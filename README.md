# Real-Time Video Streaming with WebRTC and Python

## Introduction

This repository contains the source code for streaming camera frames in real-time from one machine to another using WebRTC and Python. The project demonstrates setting up a WebRTC connection and capturing video frames with OpenCV.

## Features

- Real-time video streaming
- Peer-to-peer communication using WebRTC
- Simple signaling server setup
- Python implementation using aiortc and OpenCV

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.x
- Pip (Python package manager)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/eknathmali/Real-Time-Video-Streaming-with-WebRTC-and-Python.git
    cd Real-Time-Video-Streaming-with-WebRTC-and-Python
    ```

2. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Start `sender.py` on Remote Server:

```bash
python sender.py
```

If you need a specific camera device, set `CAMERA_ID` before starting the sender:

```bash
CAMERA_ID=0 python sender.py
```

### Start `receiver.py` on Local Machine:

```bash
python receiver.py
```

## Troubleshooting

- If `sender.py` reports `Unable to open camera index ... Available video devices: none`, the Linux environment does not currently expose a webcam as `/dev/video*`.
- In WSL2, this usually means the camera is only visible to Windows, not to the Linux guest. In that case, run the sender on native Windows/Linux with direct camera access, or attach a USB camera device into WSL before retrying.
- If a camera is available, verify the device list with `ls -l /dev/video*` and then set the correct `CAMERA_ID`.
## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or additions.

## Contact
For questions or suggestions, please contact
 - Email: malieknath135@gmail.com 
 - LinkedIn: [Link](https://www.linkedin.com/in/eknath-mali-5544121b9/)
