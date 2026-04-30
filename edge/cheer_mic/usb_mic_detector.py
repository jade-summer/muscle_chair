"""USB microphone input module for real-time cheer detection.

This module provides real-time audio level detection using PyAudio to capture
audio from USB microphones. It calculates RMS (Root Mean Square) volume,
applies noise gating and smoothing, then normalizes to a 0.0-1.0 range.
"""

from __future__ import annotations

import sys
from collections import deque
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pyaudio


@dataclass(frozen=True)
class AudioConfig:
    """Configuration for audio capture and processing."""

    sample_rate: int = 16000  # Hz - lightweight for Raspberry Pi Zero
    chunk_size: int = 1024  # samples per buffer
    channels: int = 1  # mono audio
    sensitivity: float = 15.0  # RMS multiplier for level calculation
    noise_gate_threshold: float = 0.05  # minimum level to register
    smoothing_window_size: int = 3  # moving average window size
    device_index: Optional[int] = None  # None = default device


def list_audio_devices() -> list[dict[str, Any]]:
    """List all available audio input devices.

    Returns:
        List of device info dictionaries with keys:
        - index: device index for PyAudio
        - name: device name
        - channels: max input channels
        - sample_rate: default sample rate
    """
    audio = pyaudio.PyAudio()
    devices = []

    try:
        device_count = audio.get_device_count()
        for i in range(device_count):
            info = audio.get_device_info_by_index(i)
            # Only include devices with input channels
            if info["maxInputChannels"] > 0:
                devices.append(
                    {
                        "index": i,
                        "name": info["name"],
                        "channels": info["maxInputChannels"],
                        "sample_rate": int(info["defaultSampleRate"]),
                    }
                )
    finally:
        audio.terminate()

    return devices


class USBMicDetector:
    """Real-time audio level detector using USB microphone input.

    This class captures audio from a USB microphone, processes the audio data
    to calculate volume levels, and provides normalized cheer intensity values.
    """

    def __init__(self, config: AudioConfig = AudioConfig()) -> None:
        """Initialize the USB microphone detector.

        Args:
            config: Audio configuration parameters
        """
        self._config = config
        self._audio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._smoothing_buffer: deque[float] = deque(
            maxlen=config.smoothing_window_size
        )
        self._is_running = False

    def __enter__(self) -> USBMicDetector:
        """Context manager entry - start audio stream."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - stop audio stream."""
        self.stop()

    def start(self) -> None:
        """Start the audio input stream."""
        if self._is_running:
            return

        self._audio = pyaudio.PyAudio()

        # Open audio stream
        try:
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=self._config.channels,
                rate=self._config.sample_rate,
                input=True,
                frames_per_buffer=self._config.chunk_size,
                input_device_index=self._config.device_index,
            )
            self._is_running = True
        except Exception as e:
            # Clean up on failure
            if self._audio:
                self._audio.terminate()
                self._audio = None
            raise RuntimeError(f"Failed to open audio stream: {e}") from e

    def stop(self) -> None:
        """Stop the audio input stream and release resources."""
        if not self._is_running:
            return

        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        if self._audio:
            self._audio.terminate()
            self._audio = None

        self._is_running = False
        self._smoothing_buffer.clear()

    def _calculate_rms(self, audio_data: bytes) -> float:
        """Calculate RMS (Root Mean Square) of audio data.

        Args:
            audio_data: Raw audio bytes from PyAudio

        Returns:
            RMS value as float
        """
        # Convert bytes to numpy array of int16
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # Calculate RMS
        rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))

        return float(rms)

    def _apply_noise_gate(self, level: float) -> float:
        """Apply noise gate threshold.

        Args:
            level: Input level (0.0-1.0)

        Returns:
            Level with noise gate applied (below threshold becomes 0.0)
        """
        if level < self._config.noise_gate_threshold:
            return 0.0
        return level

    def _apply_smoothing(self, level: float) -> float:
        """Apply moving average smoothing to reduce jitter.

        Args:
            level: Current level value

        Returns:
            Smoothed level value
        """
        self._smoothing_buffer.append(level)
        return sum(self._smoothing_buffer) / len(self._smoothing_buffer)

    def read_level(self) -> float:
        """Read current audio level from microphone.

        Returns:
            Normalized audio level (0.0-1.0)

        Raises:
            RuntimeError: If stream is not running
        """
        if not self._is_running or self._stream is None:
            raise RuntimeError("Audio stream is not running. Call start() first.")

        # Read audio data from stream
        audio_data = self._stream.read(
            self._config.chunk_size, exception_on_overflow=False
        )

        # Calculate RMS volume
        rms = self._calculate_rms(audio_data)

        # Normalize RMS to 0.0-1.0 range using sensitivity
        # int16 max value is 32768, so normalize and apply sensitivity
        raw_level = (rms / 32768.0) * self._config.sensitivity

        # Clamp to 0.0-1.0 range
        raw_level = max(0.0, min(1.0, raw_level))

        # Apply noise gate
        gated_level = self._apply_noise_gate(raw_level)

        # Apply smoothing
        smoothed_level = self._apply_smoothing(gated_level)

        return smoothed_level


def main() -> None:
    """Standalone test for USB microphone detector."""
    print("=== USB Microphone Detector Test ===\n")

    # List available devices
    print("Available audio input devices:")
    devices = list_audio_devices()
    if not devices:
        print("No audio input devices found!")
        sys.exit(1)

    for device in devices:
        print(
            f"  [{device['index']}] {device['name']} "
            f"(channels: {device['channels']}, rate: {device['sample_rate']} Hz)"
        )

    # Allow user to select device (or use default)
    print("\nUsing default audio device (or specify with device_index parameter)")

    # Create detector with default configuration
    config = AudioConfig()
    print("\nConfiguration:")
    print(f"  Sample Rate: {config.sample_rate} Hz")
    print(f"  Chunk Size: {config.chunk_size} samples")
    print(f"  Channels: {config.channels}")
    print(f"  Sensitivity: {config.sensitivity}")
    print(f"  Noise Gate: {config.noise_gate_threshold}")
    print(f"  Smoothing Window: {config.smoothing_window_size}")

    # Test audio capture
    print("\n--- Starting audio level detection ---")
    print("Speak into the microphone to see levels (Ctrl+C to exit)\n")

    try:
        with USBMicDetector(config) as detector:
            while True:
                level = detector.read_level()

                # Visual level bar (50 chars wide)
                bar_length = int(level * 50)
                bar = "█" * bar_length + "░" * (50 - bar_length)

                print(f"\rLevel: {level:.3f} |{bar}|", end="", flush=True)

    except KeyboardInterrupt:
        print("\n\nTest stopped by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
