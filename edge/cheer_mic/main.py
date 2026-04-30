"""Entry point wiring the cheer detector to the sender.

Supports both real USB microphone input and pseudo data mode for testing.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

from .cheer_detector import CheerDetector, AudioConfig
from .sender import Sender, HttpTransport


def create_progress_bar(level: float, width: int = 50) -> str:
    """Create a visual progress bar for audio level.

    Args:
        level: Audio level (0.0-1.0)
        width: Width of progress bar in characters

    Returns:
        Progress bar string with filled and empty characters
    """
    filled_width = int(level * width)
    bar = "█" * filled_width + "░" * (width - filled_width)
    return bar


def main(
    team: str = "A",
    backend_url: str = "http://127.0.0.1:8000/api/cheer/trigger",
    device_index: Optional[int] = None,
    debug: bool = False,
    trigger_threshold: float = 0.65,
) -> None:
    """Run the cheer detection system.

    Args:
        team: Team identifier ('A' or 'B')
        backend_url: Backend server URL for cheer events
        device_index: Optional audio device index (None = default device)
        debug: If True, use pseudo data instead of real microphone
        trigger_threshold: Level threshold for triggering cheer events
    """
    # Print startup information
    print("=" * 70)
    print("Cheer Detection System")
    print("=" * 70)
    print(f"Team: {team}")
    print(f"Backend: {backend_url}")
    print(f"Mode: {'DEBUG (Pseudo Data)' if debug else 'PRODUCTION (USB Microphone)'}")
    print(f"Trigger Threshold: {trigger_threshold}")

    if not debug and device_index is not None:
        print(f"Audio Device: {device_index}")
    elif not debug:
        print("Audio Device: Default")

    print("=" * 70)
    print()

    # Create audio configuration for real microphone mode
    audio_config = None
    if not debug:
        audio_config = AudioConfig(device_index=device_index)

    # Initialize detector
    detector: Optional[CheerDetector] = None

    try:
        # Create detector with appropriate mode
        if debug:
            print("Initializing detector in DEBUG mode (pseudo data)...")
            detector = CheerDetector(trigger_threshold=trigger_threshold)
        else:
            print("Initializing detector in PRODUCTION mode (USB microphone)...")
            try:
                detector = CheerDetector(
                    use_real_mic=True,
                    mic_config=audio_config,
                    trigger_threshold=trigger_threshold,
                )
            except RuntimeError as e:
                print(f"\n✗ Failed to initialize USB microphone: {e}")
                print("\nTip: Run with --debug flag to use pseudo data for testing")
                sys.exit(1)

        print("✓ Detector initialized\n")

        # Create sender
        transport = HttpTransport(backend_url)
        sender = Sender(team=team, transport=transport)
        print("✓ Sender initialized\n")

        # Main detection loop
        print("Starting detection... (Press Ctrl+C to stop)\n")

        if debug:
            # In debug mode, add delay to simulate real-time
            delay = 0.1
        else:
            # In real mic mode, no delay needed (blocking on audio read)
            delay = 0.0

        while True:
            # Poll for level and events
            level, event = detector.poll()

            # Display real-time level with progress bar
            bar = create_progress_bar(level, width=50)
            print(f"\rLevel: {level:.3f} |{bar}|", end="", flush=True)

            # Handle cheer event
            if event:
                # Print event on new line
                print(
                    f"\n🎉 CHEER DETECTED! Level: {event.level:.3f} at {event.timestamp:.2f}s"
                )

                # Send event to backend
                try:
                    sender.emit(event)
                    print("   ✓ Event sent to backend")
                except Exception as e:
                    print(f"   ✗ Failed to send event: {e}")

                # Continue level display on next line
                print()

            # Sleep in debug mode to avoid tight loop
            if delay > 0:
                time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user (Ctrl+C)")
        print("Shutting down gracefully...")

    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        # Clean up resources
        if detector is not None:
            detector.close()
            print("✓ Detector resources released")

        print("\nShutdown complete.")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Cheer Detection System for Muscle Chair",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Debug mode with pseudo data (Team A)
  python -m edge.cheer_mic.main --team A --debug

  # Production mode with real microphone (auto-detect device)
  python -m edge.cheer_mic.main --team A

  # Production mode with specific audio device (Team B)
  python -m edge.cheer_mic.main --team B --device 1

  # Custom backend URL
  python -m edge.cheer_mic.main --team A --backend http://xxx.xxx.xxx.xxx:8000/api/cheer/trigger

  # List available audio devices
  python -m edge.cheer_mic.usb_mic_detector
        """,
    )

    parser.add_argument(
        "--team",
        type=str,
        choices=["A", "B"],
        default="A",
        help="Team identifier (default: A)",
    )

    parser.add_argument(
        "--backend",
        type=str,
        default="http://127.0.0.1:8000/api/cheer/trigger",
        help="Backend server URL for cheer events (default: http://127.0.0.1:8000/api/cheer/trigger)",
    )

    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Audio device index (use 'python -m edge.cheer_mic.usb_mic_detector' to list devices)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Use pseudo data instead of real microphone (for testing without hardware)",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.65,
        help="Cheer trigger threshold (0.0-1.0, default: 0.65)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    main(
        team=args.team,
        backend_url=args.backend,
        device_index=args.device,
        debug=args.debug,
        trigger_threshold=args.threshold,
    )
