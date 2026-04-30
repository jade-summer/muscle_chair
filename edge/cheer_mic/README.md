# Cheer Detection Module

Real-time cheer detection system for Raspberry Pi Zero 2 W using USB microphones.

## Overview

This module captures audio from USB microphones, processes the audio data to detect cheer intensity, and sends events to a backend server when cheer levels exceed a threshold.

## Architecture

The system consists of three main components:

1. **USB Microphone Input** (`usb_mic_detector.py`) - Captures and processes real-time audio
2. **Cheer Detection** (`cheer_detector.py`) - Detects cheer events based on audio levels
3. **Event Transmission** (`sender.py`) - Sends cheer events to backend via HTTP

## Hardware Requirements

- **Microphone**: SANWA SUPPLY MM-MCU028K (USB Audio Class compliant)
- **Platform**: Raspberry Pi Zero 2 W
- **Connection**: USB Type-A via Micro USB OTG adapter
- **Quantity**: 2 units (Team A and Team B)

## Software Dependencies

### System Packages (Raspberry Pi)
```bash
sudo apt install portaudio19-dev python3-pyaudio python3-numpy
```

### Python Packages
```
pyaudio>=0.2.13
numpy>=1.24.0
```

## USB Microphone Detector

### Features

- **Real-time audio capture** at 16kHz (optimized for Raspberry Pi Zero)
- **RMS-based volume calculation** for cheer intensity
- **Noise gate** to filter ambient noise
- **Smoothing filter** to reduce level jitter
- **Normalized output** (0.0 - 1.0 range)
- **Context manager** support for resource management

### Configuration

```python
from edge.cheer_mic.usb_mic_detector import AudioConfig, USBMicDetector

# Create custom configuration
config = AudioConfig(
    sample_rate=16000,          # Hz - lightweight for RPi Zero
    chunk_size=1024,            # samples per buffer
    channels=1,                 # mono audio
    sensitivity=15.0,           # RMS multiplier
    noise_gate_threshold=0.05,  # minimum level to register
    smoothing_window_size=3,    # moving average window
    device_index=None           # None = default device
)

# Use the detector
with USBMicDetector(config) as detector:
    level = detector.read_level()  # Returns 0.0-1.0
    print(f"Cheer level: {level:.3f}")
```

### Audio Device Selection

List available audio devices:

```python
from edge.cheer_mic.usb_mic_detector import list_audio_devices

devices = list_audio_devices()
for device in devices:
    print(f"[{device['index']}] {device['name']}")
```

Specify device by index:

```python
config = AudioConfig(device_index=1)  # Use device #1
```

### Standalone Testing

```bash
# List devices and test audio levels
python3 -m edge.cheer_mic.usb_mic_detector
```

This will display real-time audio levels with a visual bar indicator.

## Calibration

The default configuration parameters are estimates. Use the calibration tool to determine optimal values for your specific environment:

- **Sensitivity**: Adjust RMS-to-level conversion
- **Noise Gate**: Filter ambient noise threshold
- **Cheer Trigger**: Level required to emit events

## API Reference

### AudioConfig

Dataclass for audio configuration:

```python
@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    sensitivity: float = 15.0
    noise_gate_threshold: float = 0.05
    smoothing_window_size: int = 3
    device_index: Optional[int] = None
```

### USBMicDetector

Real-time audio level detector:

```python
class USBMicDetector:
    def __init__(self, config: AudioConfig = AudioConfig()) -> None
    def start(self) -> None
    def stop(self) -> None
    def read_level(self) -> float  # Returns 0.0-1.0
```

Context manager support:
```python
with USBMicDetector(config) as detector:
    level = detector.read_level()
```

### list_audio_devices()

Utility function to list available audio input devices:

```python
def list_audio_devices() -> list[dict[str, any]]
```

Returns list of devices with:
- `index`: Device index for PyAudio
- `name`: Device name
- `channels`: Max input channels
- `sample_rate`: Default sample rate

## Development Notes

### Resource Management

The USBMicDetector properly manages PyAudio resources:
- Always use the context manager (`with` statement) for automatic cleanup
- Or manually call `start()` and `stop()` methods
- Resources are released on exit/error

### Error Handling

Common errors:
- **"Audio stream is not running"**: Call `start()` before `read_level()`
- **"Failed to open audio stream"**: Check device_index or USB connection
- **High CPU usage**: Reduce sample_rate or increase chunk_size

## Testing

### Mock Test (No Hardware Required)
```bash
python3 edge/cheer_mic/test_usb_mic_mock.py
```

### Hardware Test (Requires USB Microphone)
```bash
python3 -m edge.cheer_mic.usb_mic_detector
```

## Troubleshooting

### Raspberry Pi: No Audio Device Found

```bash
# Check USB devices
lsusb

# List audio devices
arecord -l

# Test recording
arecord -D plughw:1,0 -f cd -d 5 test.wav
aplay test.wav
```

### WSL2: No Audio Device Found

Ensure WSLg is enabled and PulseAudio is running. Check Windows microphone permissions.

### High CPU Usage

Reduce processing load:
```python
config = AudioConfig(
    sample_rate=8000,   # Lower sample rate
    chunk_size=2048,    # Larger buffer
)
```

## License

Part of the Muscle Chair project.
