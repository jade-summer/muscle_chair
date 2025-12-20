"""Cheer detection primitive for Raspberry Pi Zero.

This module supports both pseudo audio energy levels (for testing) and real
USB microphone input for production use.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Generator, Iterable, Iterator, Optional

try:
    from .usb_mic_detector import AudioConfig, USBMicDetector
except ImportError:
    # Allow module to be imported even without PyAudio dependencies
    AudioConfig = None  # type: ignore
    USBMicDetector = None  # type: ignore

CHEER_TRIGGER = 0.65  # Placeholder threshold until USB mic values are sampled.


@dataclass(frozen=True)
class CheerEvent:
    """Represents one CHEER_TRIGGER transition."""

    level: float
    timestamp: float
    label: str = "CHEER_TRIGGER"


class CheerDetector:
    """Generates energy levels and emits events when cheers cross a threshold.

    Supports both pseudo audio (default) and real USB microphone input.
    """

    def __init__(
        self,
        pseudo_sequence: Optional[Iterable[float]] = None,
        trigger_threshold: float = CHEER_TRIGGER,
        use_real_mic: bool = False,
        mic_config: Optional[AudioConfig] = None,
    ) -> None:
        """Initialize the cheer detector.

        Args:
            pseudo_sequence: Optional sequence of pseudo audio levels (0.0-1.0)
            trigger_threshold: Level threshold for triggering cheer events
            use_real_mic: If True, use real USB microphone input instead of pseudo data
            mic_config: Optional AudioConfig for USB microphone (uses default if None)

        Raises:
            RuntimeError: If use_real_mic=True but USB mic dependencies not available
        """
        self._trigger_threshold = trigger_threshold
        self._was_triggered = False
        self._use_real_mic = use_real_mic
        self._mic_detector: Optional[USBMicDetector] = None

        if use_real_mic:
            # Real microphone mode
            if USBMicDetector is None:
                raise RuntimeError(
                    "USB microphone dependencies not available. "
                    "Install: sudo apt install portaudio19-dev python3-pyaudio python3-numpy"
                )

            config = mic_config if mic_config is not None else AudioConfig()
            self._mic_detector = USBMicDetector(config)
            self._mic_detector.start()
            self._levels = None  # Not used in real mic mode
        else:
            # Pseudo data mode (backward compatible)
            self._levels: Optional[Iterator[float]] = iter(
                pseudo_sequence if pseudo_sequence is not None else self._default_waveform()
            )

    def __enter__(self) -> CheerDetector:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup resources."""
        self.close()

    @staticmethod
    def _default_waveform() -> Generator[float, None, None]:
        """Yield pseudo energy readings with sporadic bursts."""
        calm = [0.05, 0.1, 0.12, 0.08, 0.09]
        cheer = [0.5, 0.7, 0.9, 0.75, 0.4]
        while True:
            for value in calm:
                yield value
            for value in cheer:
                yield value

    def read_level(self) -> float:
        """Return the next energy level (pseudo or real microphone).

        Returns:
            Audio level normalized to 0.0-1.0 range

        Raises:
            RuntimeError: If real mic is enabled but not started
        """
        if self._use_real_mic:
            if self._mic_detector is None:
                raise RuntimeError("Microphone detector not initialized")
            return self._mic_detector.read_level()
        else:
            # Pseudo data mode
            if self._levels is None:
                raise RuntimeError("Pseudo data iterator not initialized")
            level = next(self._levels)
            return level

    def close(self) -> None:
        """Release resources (microphone, audio stream, etc.).

        Safe to call multiple times. Automatically called when using context manager.
        """
        if self._mic_detector is not None:
            self._mic_detector.stop()
            self._mic_detector = None

    def poll(self) -> tuple[float, Optional[CheerEvent]]:
        """Read the next level and emit an event on rising threshold crossings."""
        level = self.read_level()
        triggered = level >= self._trigger_threshold
        event = None
        if triggered and not self._was_triggered:
            event = CheerEvent(level=level, timestamp=monotonic())
        self._was_triggered = triggered
        return level, event

    def stream_events(self, limit: Optional[int] = None) -> Iterator[CheerEvent]:
        """Yield cheer events up to the optional limit."""
        count = 0
        while limit is None or count < limit:
            _, event = self.poll()
            if event is not None:
                yield event
            count += 1

