"""Cheer detection primitive for Raspberry Pi Zero.

The module currently feeds on pseudo audio energy levels instead of real
USB microphone input, so downstream components can be exercised without
waiting on hardware integration.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Generator, Iterable, Iterator, Optional

CHEER_TRIGGER = 0.65  # Placeholder threshold until USB mic values are sampled.


@dataclass(frozen=True)
class CheerEvent:
    """Represents one CHEER_TRIGGER transition."""

    level: float
    timestamp: float
    label: str = "CHEER_TRIGGER"


class CheerDetector:
    """Generates energy levels and emits events when cheers cross a threshold."""

    def __init__(
        self,
        pseudo_sequence: Optional[Iterable[float]] = None,
        trigger_threshold: float = CHEER_TRIGGER,
    ) -> None:
        self._levels: Iterator[float] = iter(
            pseudo_sequence if pseudo_sequence is not None else self._default_waveform()
        )
        self._trigger_threshold = trigger_threshold
        self._was_triggered = False

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
        """Return the next pseudo energy level."""
        level = next(self._levels)
        return level

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

