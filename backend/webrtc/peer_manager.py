from __future__ import annotations

import asyncio
import logging
import os
import uuid
from contextlib import suppress
from dataclasses import dataclass, field

from aiortc import RTCPeerConnection, RTCSessionDescription

from backend.webrtc.models import WebRTCAnswer, WebRTCOffer
from backend.webrtc.processor import VideoFrameProcessor


logger = logging.getLogger(__name__)


@dataclass
class PeerSession:
    session_id: str
    pc: RTCPeerConnection
    processor: VideoFrameProcessor
    track_tasks: set[asyncio.Task] = field(default_factory=set)


class PeerManager:
    def __init__(self) -> None:
        self._sessions: dict[str, PeerSession] = {}
        self._ice_gather_timeout = float(os.getenv("ICE_GATHERING_TIMEOUT", "5"))

    @property
    def active_peer_count(self) -> int:
        return len(self._sessions)

    async def handle_offer(self, offer: WebRTCOffer) -> WebRTCAnswer:
        session_id = uuid.uuid4().hex
        pc = RTCPeerConnection()
        processor = VideoFrameProcessor(session_id=session_id)
        session = PeerSession(session_id=session_id, pc=pc, processor=processor)
        self._sessions[session_id] = session

        self._register_handlers(session)

        try:
            await pc.setRemoteDescription(RTCSessionDescription(sdp=offer.sdp, type=offer.type))
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            await self._wait_for_ice_gathering(pc)

            if pc.localDescription is None:
                raise RuntimeError("Peer connection did not produce a local description")

            return WebRTCAnswer(sdp=pc.localDescription.sdp)
        except Exception:
            await self._close_session(session_id)
            raise

    async def close_all(self) -> None:
        for session_id in list(self._sessions):
            await self._close_session(session_id)

    def _register_handlers(self, session: PeerSession) -> None:
        pc = session.pc
        session_id = session.session_id

        @pc.on("track")
        def on_track(track) -> None:
            if track.kind != "video":
                logger.info("Ignoring %s track for session %s", track.kind, session_id)
                return

            logger.info("Receiving %s track for session %s", track.kind, session_id)
            task = asyncio.create_task(
                self._consume_track(session, track),
                name=f"consume-track-{session_id}",
            )
            session.track_tasks.add(task)
            task.add_done_callback(lambda completed_task, tasks=session.track_tasks: tasks.discard(completed_task))

        @pc.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            logger.info("Peer %s connection state is %s", session_id, pc.connectionState)
            if pc.connectionState in {"failed", "closed", "disconnected"}:
                await self._close_session(session_id)

    async def _consume_track(self, session: PeerSession, track) -> None:
        try:
            await session.processor.consume(track)
        except Exception as error:  # pragma: no cover - defensive fallback around track consumption
            logger.exception("Track consumer failed for session %s: %s", session.session_id, error)

    async def _close_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session is None:
            return

        session.processor.close()

        for task in list(session.track_tasks):
            task.cancel()

        for task in list(session.track_tasks):
            with suppress(asyncio.CancelledError):
                await task

        await session.pc.close()
        logger.info("Closed peer session %s", session_id)

    async def _wait_for_ice_gathering(self, pc: RTCPeerConnection) -> None:
        if pc.iceGatheringState == "complete":
            return

        deadline = asyncio.get_running_loop().time() + self._ice_gather_timeout
        while pc.iceGatheringState != "complete":
            if asyncio.get_running_loop().time() >= deadline:
                logger.warning("Timed out waiting for ICE gathering to complete")
                return
            await asyncio.sleep(0.1)
