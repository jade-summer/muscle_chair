"""Entry point wiring the cheer detector to the sender.

This keeps a tight loop suitable for Raspberry Pi Zero where the real implementation
will block on USB microphone data. For now it only uses pseudo input so the rest of
node graph can be validated.
"""
from __future__ import annotations

import time

from .cheer_detector import CheerDetector
from .sender import Sender, HttpTransport


def main(iterations: int = 50, delay: float = 0.1) -> None:
    detector = CheerDetector()
    transport = HttpTransport("http://127.0.0.1:8000/api/cheer/trigger")
    sender = Sender(team="A", transport=transport)
    for _ in range(iterations):
        level, event = detector.poll()
        print(f"cheer_level={level:.3f}")
        if event:
            sender.emit(event)
        time.sleep(delay)


if __name__ == "__main__":
    main()

