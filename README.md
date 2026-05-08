# WebRTC Video Streaming with Python

## Introduction

This repository contains the source code for streaming video frames in real time from one machine to another using WebRTC and Python. The project demonstrates setting up a WebRTC connection and capturing video with OpenCV from either a webcam or a video file.

## Features

- Real-time video streaming
- Peer-to-peer communication using WebRTC
- Simple signaling server setup
- Python implementation using aiortc and OpenCV
- Video-file fallback for environments without webcam access

## Additional Documentation

- See `technical_concepts.md` for the WebRTC concepts used in this repository, the offer/answer handshake flow, and where the implementation lives in the code.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10 to 3.12 is recommended
- Pip (Python package manager)

Notes:

- `aiortc` may not have ready-to-install wheels for the newest Python releases.
- If you want local preview windows via `cv2.imshow`, install `opencv-python` instead of `opencv-python-headless`.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/Bawan-Wang/WebRTC-and-Python.git
    cd WebRTC-and-Python
    ```

2. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

   If you need OpenCV GUI preview locally, replace the headless package with:

    ```bash
    pip install opencv-python
    ```

## Usage

### Start FastAPI Backend for Browser Publisher

The new browser-to-Python flow uses FastAPI as the signaling and receiver backend.

From the repository root, start the backend with:

```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Useful backend environment variables:

- `BACKEND_HOST`: backend bind host when launching through `backend.app`. Default: `0.0.0.0`.
- `BACKEND_PORT`: backend bind port when launching through `backend.app`. Default: `8000`.
- `BACKEND_RELOAD`: set to `1` to enable reload when launching through `backend.app`.
- `SAVE_FRAMES`: set to `1` if you want the backend processor to save received frames. Default: `0`.
- `FRAME_OUTPUT_DIR`: output directory used when `SAVE_FRAMES=1`. Default: `imgs`.
- `DRAW_TIMESTAMP`: set to `0` to disable drawing timestamps onto received frames.

### Backend Smoke Test

After the backend is running, verify the minimum FastAPI surface from another terminal:

```bash
python scripts/smoke_test_backend.py
```

This smoke test checks:

- `GET /health` returns `200`
- `GET /openapi.json` includes `/health` and `/api/webrtc/offer`
- `POST /api/webrtc/offer` rejects an invalid payload with `422`

If your backend is not running on `127.0.0.1:8000`, pass a custom base URL:

```bash
python scripts/smoke_test_backend.py --base-url http://127.0.0.1:9000
```

### Start `sender.py` on Remote Server:

```bash
python sender.py
```

Useful sender environment variables:

- `CAMERA_ID`: select a specific camera device index.
- `VIDEO_SOURCE`: stream from a video file instead of a webcam.
- `SIGNALING_BIND_HOST`: bind address for the TCP signaling listener. Default: `0.0.0.0`.
- `SIGNALING_PORT`: TCP signaling port. Default: `9999`.

#### Use webcam input

Example:

```bash
CAMERA_ID=0 SIGNALING_BIND_HOST=0.0.0.0 SIGNALING_PORT=9999 python sender.py
```

#### Use video-file input

If Linux does not expose any webcam device, you can validate the full WebRTC pipeline with a local video file instead of a camera.

When `VIDEO_SOURCE` is set:

- `sender.py` reads frames from the file instead of opening `CAMERA_ID`.
- `CAMERA_ID` is ignored.
- The file is rewound and replayed when it reaches the end, so the sender can keep streaming during testing.

Example:

```bash
VIDEO_SOURCE=/path/to/video.mp4 SIGNALING_BIND_HOST=0.0.0.0 SIGNALING_PORT=9999 python sender.py
```

This mode is useful in WSL2, containers, CI, or headless Linux environments where `/dev/video*` is unavailable.

### Start `receiver.py` on Local Machine:

```bash
python receiver.py
```

Useful receiver environment variables:

- `SIGNALING_HOST`: sender IP or hostname. Default: `127.0.0.1`.
- `SIGNALING_PORT`: TCP signaling port. Default: `9999`.
- `SHOW_PREVIEW`: set to `0` to disable OpenCV preview windows.
- `SAVE_FRAMES`: set to `0` to avoid writing every received frame to disk.
- `FRAME_OUTPUT_DIR`: directory used when `SAVE_FRAMES=1`. Default: `imgs`.

Example for connecting to another machine:

```bash
SIGNALING_HOST=192.168.1.10 SIGNALING_PORT=9999 SHOW_PREVIEW=0 SAVE_FRAMES=1 python receiver.py
```

Example for saving frames while testing with a sender video file on the same machine:

```bash
SIGNALING_HOST=127.0.0.1 SIGNALING_PORT=9999 SHOW_PREVIEW=0 SAVE_FRAMES=1 FRAME_OUTPUT_DIR=imgs python receiver.py
```

## Troubleshooting

- If `python -m uvicorn backend.app:app ...` fails, make sure you run it from the repository root so Python can import the `backend` package correctly.
- If the smoke test fails on `/health`, verify that the FastAPI process is still running and listening on the expected host and port.
- If the smoke test reports missing OpenAPI paths, confirm that you are running the new FastAPI backend instead of the older TCP signaling demo.
- If `sender.py` reports `Unable to open camera index ... Available video devices: none`, the Linux environment does not currently expose a webcam as `/dev/video*`.
- In WSL2, this usually means the camera is only visible to Windows, not to the Linux guest. In that case, run the sender on native Windows/Linux with direct camera access, or attach a USB camera device into WSL before retrying.
- If a camera is available, verify the device list with `ls -l /dev/video*` and then set the correct `CAMERA_ID`.
- If no webcam is available, set `VIDEO_SOURCE` to a local video file to validate the WebRTC path without camera hardware.
- If the receiver is running on a different machine, set `SIGNALING_HOST` to the sender's reachable IP address. `127.0.0.1` only works for same-host testing.
- The default dependency uses `opencv-python-headless`, so preview windows may be unavailable. Use `SHOW_PREVIEW=0` in headless environments, or install `opencv-python` if you need GUI preview locally.
## Contributing

Contributions are welcome. Please open an issue or submit a pull request in this repository for bug fixes, documentation updates, or feature improvements.

## Support

If you run into issues, open an issue in this repository and include:

- your OS and Python version
- whether you are using `CAMERA_ID` or `VIDEO_SOURCE`
- the sender and receiver command lines you ran
- the relevant console output from both sides
