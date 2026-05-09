from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache

from aiortc import RTCConfiguration, RTCIceServer


DEFAULT_DEV_CORS_ALLOW_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)


@dataclass(frozen=True)
class IceServerSettings:
    urls: tuple[str, ...]
    username: str | None = None
    credential: str | None = None


@dataclass(frozen=True)
class BackendSettings:
    host: str
    port: int
    reload: bool
    log_level: str
    cors_allow_origins: tuple[str, ...]
    ice_gather_timeout: float
    ice_servers: tuple[IceServerSettings, ...]

    def build_rtc_configuration(self) -> RTCConfiguration:
        ice_servers = [
            RTCIceServer(
                urls=list(server.urls),
                username=server.username,
                credential=server.credential,
            )
            for server in self.ice_servers
        ]
        return RTCConfiguration(iceServers=ice_servers)


def _parse_bool(raw_value: str | None, *, default: bool = False) -> bool:
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv(raw_value: str | None) -> tuple[str, ...]:
    if raw_value is None:
        return ()
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


def _parse_ice_servers(raw_value: str | None) -> tuple[IceServerSettings, ...]:
    if raw_value is None or not raw_value.strip():
        return ()

    raw_value = raw_value.strip()
    if raw_value.startswith("["):
        return _parse_ice_servers_json(raw_value)

    return tuple(IceServerSettings(urls=(url,)) for url in _parse_csv(raw_value))


def _parse_ice_servers_json(raw_value: str) -> tuple[IceServerSettings, ...]:
    payload = json.loads(raw_value)
    if not isinstance(payload, list):
        raise ValueError("BACKEND_ICE_SERVERS must be a JSON array")

    ice_servers: list[IceServerSettings] = []
    for item in payload:
        if isinstance(item, str):
            ice_servers.append(IceServerSettings(urls=(item,)))
            continue

        if not isinstance(item, dict):
            raise ValueError("BACKEND_ICE_SERVERS entries must be strings or objects")

        urls_value = item.get("urls")
        if isinstance(urls_value, str):
            urls = (urls_value,)
        elif isinstance(urls_value, list) and all(isinstance(url, str) for url in urls_value):
            urls = tuple(urls_value)
        else:
            raise ValueError("BACKEND_ICE_SERVERS entries must include a string or string[] urls field")

        ice_servers.append(
            IceServerSettings(
                urls=urls,
                username=item.get("username"),
                credential=item.get("credential"),
            )
        )

    return tuple(ice_servers)


@lru_cache(maxsize=1)
def get_backend_settings() -> BackendSettings:
    cors_allow_origins = _parse_csv(os.getenv("BACKEND_CORS_ALLOW_ORIGINS"))

    return BackendSettings(
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=_parse_bool(os.getenv("BACKEND_RELOAD")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        cors_allow_origins=cors_allow_origins or DEFAULT_DEV_CORS_ALLOW_ORIGINS,
        ice_gather_timeout=float(os.getenv("ICE_GATHERING_TIMEOUT", "5")),
        ice_servers=_parse_ice_servers(os.getenv("BACKEND_ICE_SERVERS")),
    )