from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from av import VideoFrame


logger = logging.getLogger(__name__)


class VideoFrameProcessor:
    def __init__(
        self,
        session_id: str,
        save_frames: bool | None = None,
        output_dir: str | None = None,
        draw_timestamp: bool | None = None,
    ) -> None:
        self.session_id = session_id
        self.frame_count = 0
        self.finished = asyncio.Event()
        self.save_frames = save_frames if save_frames is not None else os.getenv("SAVE_FRAMES", "0") == "1"
        self.draw_timestamp = draw_timestamp if draw_timestamp is not None else os.getenv("DRAW_TIMESTAMP", "1") != "0"
        base_output_dir = output_dir or os.getenv("FRAME_OUTPUT_DIR", "imgs")
        self.output_dir = Path(base_output_dir) / session_id

        if self.save_frames:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    async def consume(self, track) -> None:
        try:
            while not self.finished.is_set():
                try:
                    frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.debug("Timeout waiting for frame for session %s", self.session_id)
                    continue
                except Exception as error:
                    logger.info("Stopping frame consumer for session %s: %s", self.session_id, error)
                    break

                if frame is None:
                    logger.info("Track ended for session %s", self.session_id)
                    break

                image = self._frame_to_bgr(frame)
                if image is None:
                    continue

                self.frame_count += 1
                self._annotate_frame(image)

                if self.save_frames:
                    frame_path = self.output_dir / f"received_frame_{self.frame_count:06d}.jpg"
                    if not cv2.imwrite(str(frame_path), image):
                        logger.warning("Failed to save frame %s for session %s", self.frame_count, self.session_id)

                if self.frame_count == 1 or self.frame_count % 30 == 0:
                    logger.info("Processed %s frames for session %s", self.frame_count, self.session_id)
        finally:
            self.finished.set()

    def close(self) -> None:
        self.finished.set()

    def _annotate_frame(self, frame: np.ndarray) -> None:
        if not self.draw_timestamp:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        cv2.putText(
            frame,
            timestamp,
            (10, frame.shape[0] - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    def _frame_to_bgr(self, frame) -> np.ndarray | None:
        if isinstance(frame, VideoFrame):
            return frame.to_ndarray(format="bgr24")

        if isinstance(frame, np.ndarray):
            return frame

        logger.warning("Unexpected frame type for session %s: %s", self.session_id, type(frame))
        return None
