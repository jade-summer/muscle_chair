"""Event sender stub for Raspberry Pi Zero cheer mic pipeline."""
from __future__ import annotations

import json
import time
from typing import Protocol
from urllib import error, request

from .cheer_detector import CheerEvent


class Transport(Protocol):
    def send(self, payload: dict) -> None:  # pragma: no cover - interface only
        ...


class LogTransport:
    """Simple transport that prints payloads for debugging."""

    def send(self, payload: dict) -> None:
        print(f"[CHEER EVENT] {payload}")


class HttpTransport:
    """POST cheer payloads as JSON to an HTTP endpoint using stdlib only."""

    def __init__(self, endpoint_url: str, timeout: float = 5.0) -> None:
        self._endpoint_url = endpoint_url
        self._timeout = timeout

    def send(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self._endpoint_url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self._timeout) as response:
                response.read()  # drain response for reuse-safe behaviour
        except error.HTTPError as exc:
            status = exc.code
            reason = exc.reason
            body_snippet = ""
            try:
                body_snippet = exc.read(256).decode("utf-8", errors="replace")
            except Exception:  # pragma: no cover - best-effort logging
                body_snippet = "<failed to read body>"
            print(
                f"[CHEER EVENT] HTTP send failed: status={status} reason={reason} body={body_snippet!r}"
            )
        except error.URLError as exc:
            print(f"[CHEER EVENT] HTTP network failure: {exc}")


class Sender:
    """Formats cheer events for downstream transports."""

    def __init__(
        self,
        transport: Transport | None = None,
        *,
        team: str = "unknown",
    ) -> None:
        self._transport = transport or LogTransport()
        self._team = team

    @staticmethod
    def _level_percent(raw_level: float) -> float:
        """Convert a normalized 0-1 level reading to the 0-100 scale required by the backend."""
        percent = round(raw_level * 100.0, 1)
        return min(100.0, max(0.0, percent))

    def _format(self, event: CheerEvent) -> dict:
        return {
            "team": self._team,
            "event": event.label,
            "level": self._level_percent(event.level),
            "ts": int(time.time() * 1000),
        }

    def emit(self, event: CheerEvent) -> None:
        payload = self._format(event)
        self._transport.send(payload)

