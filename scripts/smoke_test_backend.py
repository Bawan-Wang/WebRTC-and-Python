from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib import error, request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test the FastAPI WebRTC backend.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the FastAPI backend, for example http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Request timeout in seconds.",
    )
    return parser.parse_args()


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 5.0,
) -> tuple[int, Any]:
    body = None
    headers: dict[str, str] = {}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=body, headers=headers, method=method)

    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
            parsed = json.loads(raw_body) if raw_body else None
            return response.status, parsed
    except error.HTTPError as http_error:
        raw_body = http_error.read().decode("utf-8")
        parsed = json.loads(raw_body) if raw_body else None
        return http_error.code, parsed


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    try:
        health_status, health_body = request_json(f"{base_url}/health", timeout=args.timeout)
        ensure(health_status == 200, f"Expected /health to return 200, got {health_status}")
        ensure(isinstance(health_body, dict), "Expected /health response body to be a JSON object")
        ensure(health_body.get("status") == "ok", f"Unexpected /health body: {health_body}")
        ensure("activePeers" in health_body, f"Missing activePeers in /health body: {health_body}")

        openapi_status, openapi_body = request_json(f"{base_url}/openapi.json", timeout=args.timeout)
        ensure(openapi_status == 200, f"Expected /openapi.json to return 200, got {openapi_status}")
        ensure(isinstance(openapi_body, dict), "Expected /openapi.json response body to be a JSON object")
        paths = openapi_body.get("paths", {})
        ensure("/health" in paths, "Expected /health to exist in OpenAPI paths")
        ensure("/api/webrtc/offer" in paths, "Expected /api/webrtc/offer to exist in OpenAPI paths")

        invalid_offer_status, invalid_offer_body = request_json(
            f"{base_url}/api/webrtc/offer",
            method="POST",
            payload={"sdp": "placeholder", "type": "answer"},
            timeout=args.timeout,
        )
        ensure(
            invalid_offer_status == 422,
            f"Expected invalid offer payload to return 422, got {invalid_offer_status}",
        )
        ensure(isinstance(invalid_offer_body, dict), "Expected invalid offer response body to be a JSON object")

        print("Smoke test passed")
        print(f"Base URL: {base_url}")
        print(f"Health response: {health_body}")
        print("Validated routes: /health, /openapi.json, /api/webrtc/offer")
        return 0
    except Exception as error_message:
        print(f"Smoke test failed: {error_message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
