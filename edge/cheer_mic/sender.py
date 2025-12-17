"""Event sender stub for Raspberry Pi Zero cheer mic pipeline."""
from __future__ import annotations

from typing import Protocol

from .cheer_detector import CheerEvent


class Transport(Protocol):
    def send(self, payload: dict) -> None:  # pragma: no cover - interface only
        ...


class LogTransport:
    """Simple transport that prints payloads for debugging."""

    def send(self, payload: dict) -> None:
        print(f"[CHEER EVENT] {payload}")


class Sender:
    """Formats cheer events for downstream transports."""

    def __init__(self, transport: Transport | None = None) -> None:
        self._transport = transport or LogTransport()

    def _format(self, event: CheerEvent) -> dict:
        return {
            "type": event.label,
            "level": round(event.level, 3),
            "timestamp": event.timestamp,
        }

    def emit(self, event: CheerEvent) -> None:
        payload = self._format(event)
        self._transport.send(payload)

