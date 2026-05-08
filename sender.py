import asyncio
import glob
import cv2
import os
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
import fractions
from datetime import datetime

class CustomVideoStreamTrack(VideoStreamTrack):
    def __init__(self, source):
        super().__init__()
        self.source = source
        self.using_camera = isinstance(source, int)
        backend = cv2.CAP_V4L2 if self.using_camera and os.name == "posix" and hasattr(cv2, "CAP_V4L2") else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(source, backend)
        if self.using_camera and backend == cv2.CAP_V4L2:
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
        available_devices = sorted(glob.glob("/dev/video*"))
        if not self.cap.isOpened():
            if self.using_camera:
                devices_text = ", ".join(available_devices) if available_devices else "none"
                raise RuntimeError(
                    f"Unable to open camera index {source}. "
                    f"Available video devices: {devices_text}. "
                    "If you are running inside WSL or a headless environment, the webcam may not be exposed to Linux. "
                    "Set CAMERA_ID to a valid device index when a camera is available, or set VIDEO_SOURCE to a video file path."
                )
            raise RuntimeError(f"Unable to open video source: {source}")
        self.frame_count = 0

    async def recv(self):
        ret, frame = self.cap.read()
        if not ret:
            if not self.using_camera:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
            if not ret:
                raise RuntimeError("Failed to read frame from video source")
        if self.using_camera and frame is None:
            raise RuntimeError("Failed to read frame from camera")
        if frame is None:
            raise RuntimeError("Failed to read frame from video source")

        self.frame_count += 1
        print(f"Sending frame {self.frame_count}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Current time with milliseconds
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(rgb_frame, format="rgb24")
        video_frame.pts = self.frame_count
        video_frame.time_base = fractions.Fraction(1, 30)
        return video_frame

    def stop(self):
        if self.cap.isOpened():
            self.cap.release()
        super().stop()

async def setup_webrtc_and_run(ip_address, port, source):
    signaling = TcpSocketSignaling(ip_address, port)
    pc = RTCPeerConnection()
    video_sender = CustomVideoStreamTrack(source)
    pc.addTrack(video_sender)

    try:
        await signaling.connect()

        @pc.on("datachannel")
        def on_datachannel(channel):
            print(f"Data channel established: {channel.label}")

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"Connection state is {pc.connectionState}")
            if pc.connectionState == "connected":
                print("WebRTC connection established successfully")

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await signaling.send(pc.localDescription)

        while True:
            obj = await signaling.receive()
            if isinstance(obj, RTCSessionDescription):
                await pc.setRemoteDescription(obj)
                print("Remote description set")
            elif obj is None:
                print("Signaling ended")
                break
        print("Closing connection")
    finally:
        video_sender.stop()
        await pc.close()

async def main():
    ip_address = os.getenv("SIGNALING_BIND_HOST", "0.0.0.0")
    port = int(os.getenv("SIGNALING_PORT", "9999"))
    video_source = os.getenv("VIDEO_SOURCE")
    source = video_source if video_source else int(os.getenv("CAMERA_ID", "0"))
    await setup_webrtc_and_run(ip_address, port, source)

if __name__ == "__main__":
    asyncio.run(main())
