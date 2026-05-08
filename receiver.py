import asyncio
import cv2
import numpy as np
import os
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
from datetime import datetime

class VideoReceiver:
    def __init__(self):
        self.track = None
        self.preview_enabled = os.getenv("SHOW_PREVIEW", "1") != "0"
        self.save_frames = os.getenv("SAVE_FRAMES", "1") != "0"
        self.output_dir = os.getenv("FRAME_OUTPUT_DIR", "imgs")
        self.finished = asyncio.Event()
        if self.save_frames:
            os.makedirs(self.output_dir, exist_ok=True)

    def show_frame(self, frame):
        if not self.preview_enabled:
            return False

        try:
            cv2.imshow("Frame", frame)
            return cv2.waitKey(1) & 0xFF == ord('q')
        except cv2.error as error:
            print(f"Preview disabled: {error}")
            self.preview_enabled = False
            return False

    async def handle_track(self, track):
        print("Inside handle track")
        self.track = track
        frame_count = 0
        try:
            while not self.finished.is_set():
                try:
                    print("Waiting for frame...")
                    frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                    if frame is None:
                        print("Track ended")
                        break

                    frame_count += 1
                    print(f"Received frame {frame_count}")

                    if isinstance(frame, VideoFrame):
                        print(f"Frame type: VideoFrame, pts: {frame.pts}, time_base: {frame.time_base}")
                        frame = frame.to_ndarray(format="bgr24")
                    elif isinstance(frame, np.ndarray):
                        print("Frame type: numpy array")
                    else:
                        print(f"Unexpected frame type: {type(frame)}")
                        continue

                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    cv2.putText(frame, timestamp, (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                    if self.save_frames:
                        frame_path = os.path.join(self.output_dir, f"received_frame_{frame_count:06d}.jpg")
                        cv2.imwrite(frame_path, frame)
                        print(f"Saved frame {frame_count} to {frame_path}")

                    if self.show_frame(frame):
                        print("Stopping receiver preview on user request")
                        break
                except asyncio.TimeoutError:
                    print("Timeout waiting for frame, continuing...")
                except Exception as error:
                    print(f"Error in handle_track: {error}")
                    break
        finally:
            self.finished.set()
        print("Exiting handle_track")

    def close(self):
        self.finished.set()
        if self.preview_enabled:
            try:
                cv2.destroyAllWindows()
            except cv2.error as error:
                print(f"Preview cleanup skipped: {error}")


async def run(pc, signaling, video_receiver):
    await signaling.connect()
    track_task = None

    @pc.on("track")
    def on_track(track):
        nonlocal track_task
        if track.kind != "video":
            print(f"Ignoring {track.kind} track")
            return

        print(f"Receiving {track.kind} track")
        track_task = asyncio.create_task(video_receiver.handle_track(track))

    @pc.on("datachannel")
    def on_datachannel(channel):
        print(f"Data channel established: {channel.label}")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "connected":
            print("WebRTC connection established successfully")
        elif pc.connectionState in {"failed", "closed", "disconnected"}:
            video_receiver.finished.set()

    print("Waiting for offer from sender...")
    offer = await signaling.receive()
    if not isinstance(offer, RTCSessionDescription):
        raise RuntimeError(f"Expected RTCSessionDescription offer, got {type(offer)}")
    print("Offer received")
    await pc.setRemoteDescription(offer)
    print("Remote description set")

    answer = await pc.createAnswer()
    print("Answer created")
    await pc.setLocalDescription(answer)
    print("Local description set")

    await signaling.send(pc.localDescription)
    print("Answer sent to sender")

    print("Waiting for connection to be established...")
    while pc.connectionState not in {"connected", "failed", "closed"}:
        await asyncio.sleep(0.1)

    if pc.connectionState != "connected":
        raise RuntimeError(f"WebRTC connection failed with state {pc.connectionState}")

    print("Connection established, waiting for frames...")
    await video_receiver.finished.wait()

    if track_task is not None:
        await track_task

    print("Closing connection")

async def main():
    signaling_host = os.getenv("SIGNALING_HOST", "127.0.0.1")
    signaling_port = int(os.getenv("SIGNALING_PORT", "9999"))
    signaling = TcpSocketSignaling(signaling_host, signaling_port)
    pc = RTCPeerConnection()
    
    global video_receiver
    video_receiver = VideoReceiver()

    try:
        await run(pc, signaling, video_receiver)
    except Exception as e:
        print(f"Error in main: {str(e)}")
    finally:
        print("Closing peer connection")
        video_receiver.close()
        await pc.close()

if __name__ == "__main__":
    asyncio.run(main())
    

# Learn how to stream camera frames in real-time from one machine to another using WebRTC and Python. This repo walks you through setting up WebRTC with Python, capturing video with OpenCV, and establishing peer-to-peer connections