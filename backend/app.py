from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request

from backend.webrtc.models import WebRTCAnswer, WebRTCOffer
from backend.webrtc.peer_manager import PeerManager


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


peer_manager = PeerManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    app.state.peer_manager = peer_manager
    try:
        yield
    finally:
        await peer_manager.close_all()


app = FastAPI(
    title="WebRTC Python Backend",
    description="FastAPI + aiortc backend that receives browser camera streams.",
    lifespan=lifespan,
)


@app.get("/health")
async def health(request: Request) -> dict[str, int | str]:
    manager: PeerManager = request.app.state.peer_manager
    return {
        "status": "ok",
        "activePeers": manager.active_peer_count,
    }


@app.post("/api/webrtc/offer", response_model=WebRTCAnswer)
async def create_answer(offer: WebRTCOffer, request: Request) -> WebRTCAnswer:
    manager: PeerManager = request.app.state.peer_manager

    try:
        return await manager.handle_offer(offer)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # pragma: no cover - defensive fallback for runtime failures
        logging.getLogger(__name__).exception("Failed to create WebRTC answer")
        raise HTTPException(
            status_code=500,
            detail="Failed to create WebRTC answer",
        ) from error


if __name__ == "__main__":
    uvicorn.run(
        "backend.app:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=os.getenv("BACKEND_RELOAD", "0") == "1",
    )
