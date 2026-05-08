# WebRTC Technical Concepts

This document explains the WebRTC concepts used in this repository, how they map to the Python implementation, and where the offer/answer handshake is implemented.

## 1. What This Repository Does

This project builds a one-way video streaming pipeline:

- `sender.py` captures frames from either a webcam or a video file.
- `receiver.py` receives the remote video track.
- The two peers exchange WebRTC session descriptions over a plain TCP signaling channel.
- After the peer connection is established, video frames flow from sender to receiver.

In short: the repository uses WebRTC for media transport, but it uses a separate TCP channel for signaling.

## 2. Core WebRTC Concepts Used Here

### RTCPeerConnection

`RTCPeerConnection` is the main WebRTC object. It owns the session, negotiates capabilities, manages connectivity, and carries media tracks.

In this repository:

- `sender.py` creates a peer connection in `setup_webrtc_and_run(...)`.
- `receiver.py` creates a peer connection in `main()` and passes it into `run(...)`.

### Signaling

Signaling is the out-of-band channel used to exchange negotiation messages. Signaling is not the media stream itself.

In this repository, signaling is implemented with:

- `aiortc.contrib.signaling.TcpSocketSignaling`

That means:

- sender and receiver exchange SDP messages over TCP
- signaling is separate from the WebRTC media path
- this is a simple demo-friendly design, not a browser-style production signaling service

### SDP Offer / Answer

WebRTC peers negotiate with SDP using the offer/answer model:

1. one side creates an offer
2. the other side receives the offer and creates an answer
3. both sides set remote descriptions
4. once negotiation completes, the peer connection can move toward `connected`

In this repository:

- the sender is the offerer
- the receiver is the answerer

### Media Track

A media track is the actual audio or video source attached to a WebRTC connection.

In this repository:

- `CustomVideoStreamTrack` in `sender.py` inherits from `VideoStreamTrack`
- each call to `recv()` returns one video frame
- the sender adds this track to the peer connection with `pc.addTrack(...)`

### ICE / Connectivity

WebRTC normally uses ICE to find a working network path between peers.

This repository keeps that part simple:

- there is no custom STUN server configuration
- there is no custom TURN server configuration
- there is no explicit trickle ICE handling in the application code
- the code exchanges `pc.localDescription` directly over signaling

This is acceptable for local testing and simple reachable-network setups, but it is not a full NAT-traversal solution.

### Data Channel

There are `datachannel` event handlers in both peers, but this repository does not create a data channel for application data.

So currently:

- video transport is the main feature
- data channel support is only partially scaffolded

## 3. How the Handshake Works in This Repository

The WebRTC handshake is split between the sender and receiver.

### Sender side

Main handshake code lives in:

- `sender.py` -> `setup_webrtc_and_run(...)`

Flow:

1. create `TcpSocketSignaling(ip_address, port)`
2. create `RTCPeerConnection()`
3. create `CustomVideoStreamTrack(source)`
4. attach the video track with `pc.addTrack(video_sender)`
5. connect signaling with `await signaling.connect()`
6. create the offer with `await pc.createOffer()`
7. apply it locally with `await pc.setLocalDescription(offer)`
8. send the local description with `await signaling.send(pc.localDescription)`
9. wait for the receiver's answer in the signaling loop
10. apply the receiver's answer with `await pc.setRemoteDescription(obj)`

Important sender-side handshake lines are conceptually these calls:

- `pc.createOffer()`
- `pc.setLocalDescription(...)`
- `signaling.send(pc.localDescription)`
- `pc.setRemoteDescription(...)`

### Receiver side

Main handshake code lives in:

- `receiver.py` -> `run(pc, signaling, video_receiver)`

Flow:

1. connect signaling with `await signaling.connect()`
2. wait for the sender offer with `offer = await signaling.receive()`
3. apply the remote offer with `await pc.setRemoteDescription(offer)`
4. create an answer with `await pc.createAnswer()`
5. apply it locally with `await pc.setLocalDescription(answer)`
6. send the answer back with `await signaling.send(pc.localDescription)`
7. wait for the peer connection state to become `connected`

Important receiver-side handshake calls are:

- `signaling.receive()`
- `pc.setRemoteDescription(offer)`
- `pc.createAnswer()`
- `pc.setLocalDescription(answer)`
- `signaling.send(pc.localDescription)`

## 4. Handshake Sequence at a Glance

You can think about the handshake like this:

1. sender starts and creates a local video track
2. sender creates an SDP offer
3. sender sends that offer through `TcpSocketSignaling`
4. receiver gets the offer and sets it as the remote description
5. receiver creates an SDP answer
6. receiver sends the answer back through `TcpSocketSignaling`
7. sender receives the answer and sets it as the remote description
8. both peers continue connection setup internally until `pc.connectionState` becomes `connected`
9. once connected, video frames begin flowing to the receiver's `on_track` handler

## 5. Where the Media Flow Is Implemented

### Sender media pipeline

The local video source is implemented in:

- `sender.py` -> `CustomVideoStreamTrack`

Key responsibilities:

- open webcam input or `VIDEO_SOURCE`
- read frames using OpenCV
- draw a timestamp on each frame
- convert `numpy` frame data into `av.VideoFrame`
- return frames from `recv()` for WebRTC transmission

This is the key abstraction that turns OpenCV frames into a WebRTC video track.

### Receiver media pipeline

The remote video handling is implemented in:

- `receiver.py` -> `VideoReceiver.handle_track(...)`

Key responsibilities:

- wait for incoming frames from the remote track
- convert `VideoFrame` to a NumPy array when needed
- draw a local receive timestamp
- optionally save frames to disk
- optionally preview frames with OpenCV

The receiver starts consuming media from this event handler:

- `receiver.py` -> `@pc.on("track")`

That event is the moment where the remote WebRTC track becomes available to the application.

## 6. File-to-Concept Map

| Concept | Where to look | What it does |
| --- | --- | --- |
| Local peer connection creation | `sender.py` -> `setup_webrtc_and_run(...)` | Creates sender-side `RTCPeerConnection` |
| Remote peer connection creation | `receiver.py` -> `main()` | Creates receiver-side `RTCPeerConnection` |
| Signaling transport | `sender.py` and `receiver.py` with `TcpSocketSignaling` | Exchanges offer/answer messages |
| Offer creation | `sender.py` -> `pc.createOffer()` | Starts negotiation |
| Answer creation | `receiver.py` -> `pc.createAnswer()` | Completes the SDP response |
| Local video source | `sender.py` -> `CustomVideoStreamTrack` | Produces frames from camera or file |
| Attach local media | `sender.py` -> `pc.addTrack(video_sender)` | Publishes sender video |
| Remote track event | `receiver.py` -> `@pc.on("track")` | Receives the remote media track |
| Frame processing and saving | `receiver.py` -> `VideoReceiver.handle_track(...)` | Converts, timestamps, previews, and optionally saves frames |
| Connection state monitoring | `sender.py` and `receiver.py` -> `@pc.on("connectionstatechange")` | Logs connection lifecycle |

## 7. How to Trace the Handshake in Runtime Logs

If you want to verify negotiation while the programs are running, these log messages are the most useful.

### Sender logs

Look for messages such as:

- `Remote description set`
- `Connection state is connected`
- `WebRTC connection established successfully`

### Receiver logs

Look for messages such as:

- `Waiting for offer from sender...`
- `Offer received`
- `Remote description set`
- `Answer created`
- `Answer sent to sender`
- `Connection state is connected`
- `Receiving video track`

If you see the receiver reach `Receiving video track`, the offer/answer handshake has already completed and media delivery has started.

## 8. Current Architectural Limits

This repository is intentionally simple. Current limits include:

- one-way video only
- no browser client
- no full signaling server application beyond plain TCP signaling
- no explicit STUN/TURN configuration for difficult network topologies
- receiver-side frame saving can become expensive if enabled for every frame

For local testing, education, and controlled-network demos, this structure is fine. For internet-facing or production use, the next step would be a real signaling service, explicit ICE server configuration, and stronger connection lifecycle management.