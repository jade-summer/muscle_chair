# Skeleton Camera Module

Real-time skeleton detection system using Raspberry Pi Camera and MediaPipe.

## Overview

This module captures video from a Raspberry Pi Camera (Picamera2), performs pose estimation with MediaPipe, and streams the annotated video with joint angle data to a PC client via WebSocket. The PC client counts exercise reps and reports scores to the backend server.

## Architecture

The system consists of two main components:

1. **WebSocket Server** (`server.py`) - Runs on Raspberry Pi; captures video, detects skeleton, streams data
2. **OpenCV Client** (`client.py`) - Runs on PC; receives stream, displays video, counts reps, reports points

```
[Raspberry Pi]                    [PC]                      [Backend]
  Picamera2                         |                           |
     ↓                              |                           |
  MediaPipe Pose                    |                           |
     ↓                              |                           |
  server.py  ---WebSocket(8765)--→ client.py ---HTTP POST--→ /add_point
             ←--- mode command ----
```

## Hardware Requirements

- **Camera**: Raspberry Pi Camera Module (any generation)
- **Platform**: Raspberry Pi (tested on Zero 2 W)
- **PC**: Any machine capable of running OpenCV

## Software Dependencies

### Raspberry Pi

```bash
# System packages
sudo apt install python3-picamera2 python3-opencv python3-numpy

# Python packages
pip install websockets mediapipe
```

### PC

```bash
pip install websockets opencv-python numpy requests
```

## Usage

### 1. Start the server on Raspberry Pi

```bash
python3 -m edge.skeleton_cam.server
```

### 2. Update the IP address in client.py

```python
# client.py
WEBSOCKET_URI = "ws://<Raspberry Pi IP>:8765"
```

### 3. Start the client on PC

```bash
python3 -m edge.skeleton_cam.client
```

### 4. Operation

| State | Action |
|-------|--------|
| START screen | Click **START** button |
| Mode selection | Click **Squat** or **Push Up** |
| Training | Exercise in front of camera; reps are counted automatically |
| Quit | Press `q` |

## Supported Exercise Modes

| Mode | Key Joints | Down threshold | Up threshold |
|------|-----------|---------------|-------------|
| Squat | Hip(24) → Knee(26) → Ankle(28) | angle < 100° | angle > 160° |
| Push-up | Shoulder(12) → Elbow(14) → Wrist(16) | angle < 100° | angle > 160° |

## Backend Integration

On each rep completion, the client sends a POST request to the backend:

```json
POST /add_point
{
  "source": "pushup_sensor",
  "value": 1,
  "team": "a"
}
```

To change the team or backend URL, edit the constants at the top of `client.py`:

```python
WEBSOCKET_URI = "ws://xxx.xxx.xxx.xxx:8765"
BACKEND_URL = "http://127.0.0.1:8000/add_point"
TEAM = "a"
```

