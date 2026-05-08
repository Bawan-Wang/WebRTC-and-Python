from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class WebRTCOffer(BaseModel):
    sdp: str
    type: Literal["offer"]


class WebRTCAnswer(BaseModel):
    sdp: str
    type: Literal["answer"] = "answer"
