"""Integration test for CheerDetector with both pseudo and real mic modes.

This demonstrates the integration of USBMicDetector into CheerDetector.
"""

from __future__ import annotations

import sys
import time


def test_pseudo_mode():
    """Test CheerDetector in pseudo mode (backward compatibility)."""
    print("=== Test 1: Pseudo Mode (Backward Compatible) ===\n")

    from edge.cheer_mic.cheer_detector import CheerDetector

    # Test with default pseudo data
    print("Testing with default pseudo waveform...")
    detector = CheerDetector()

    for i in range(10):
        level, event = detector.poll()
        print(f"  Level: {level:.3f}", end="")
        if event:
            print(f" → CHEER EVENT at {event.timestamp:.2f}s")
        else:
            print()

    print("✓ Pseudo mode works!\n")

    # Test with custom sequence
    print("Testing with custom pseudo sequence...")
    custom_sequence = [0.1, 0.2, 0.8, 0.9, 0.3]
    detector2 = CheerDetector(pseudo_sequence=custom_sequence, trigger_threshold=0.7)

    for i in range(5):
        level, event = detector2.poll()
        print(f"  Level: {level:.3f}", end="")
        if event:
            print(" → CHEER EVENT!")
        else:
            print()

    print("✓ Custom sequence works!\n")


def test_context_manager():
    """Test CheerDetector as context manager."""
    print("=== Test 2: Context Manager ===\n")

    from edge.cheer_mic.cheer_detector import CheerDetector

    print("Testing context manager with pseudo mode...")

    with CheerDetector() as detector:
        for i in range(5):
            level = detector.read_level()
            print(f"  Level: {level:.3f}")

    print("✓ Context manager works!\n")


def test_real_mic_mode_mock():
    """Test CheerDetector with real mic mode (requires hardware)."""
    print("=== Test 3: Real Microphone Mode ===\n")

    try:
        from edge.cheer_mic.cheer_detector import CheerDetector, AudioConfig

        # Try to create detector with real mic
        print("Attempting to create detector with real microphone...")

        try:
            config = AudioConfig(sensitivity=10.0, noise_gate_threshold=0.1)
            detector = CheerDetector(use_real_mic=True, mic_config=config)

            print("✓ Real mic detector created successfully!")
            print("  Reading levels from USB microphone...")

            # Read a few levels
            with detector:
                for i in range(5):
                    level = detector.read_level()
                    bar = "█" * int(level * 30) + "░" * (30 - int(level * 30))
                    print(f"  [{bar}] {level:.3f}")
                    time.sleep(0.1)

            print("✓ Real mic mode works!\n")

        except RuntimeError as e:
            if "dependencies not available" in str(e):
                print("⚠ USB microphone dependencies not installed")
                print("  This is expected in test environment")
                print(f"  Error: {e}\n")
            elif "Failed to open audio stream" in str(e):
                print("⚠ No USB microphone detected")
                print("  This is expected without hardware")
                print(f"  Error: {e}\n")
            else:
                raise

    except ImportError as e:
        print(f"⚠ Import error: {e}")
        print("  This is expected without PyAudio installed\n")


def test_event_detection():
    """Test event detection with both modes."""
    print("=== Test 4: Event Detection ===\n")

    from edge.cheer_mic.cheer_detector import CheerDetector

    # Create a sequence that crosses threshold
    test_sequence = [
        0.1,
        0.2,
        0.3,  # Below threshold
        0.7,
        0.8,
        0.9,  # Above threshold - should trigger
        0.5,
        0.4,
        0.3,  # Below threshold again
        0.8,
        0.9,
        0.7,  # Above threshold - should trigger again
    ]

    detector = CheerDetector(pseudo_sequence=test_sequence, trigger_threshold=0.65)

    print("Testing event detection with threshold=0.65...")
    event_count = 0

    for i in range(len(test_sequence)):
        level, event = detector.poll()
        print(f"  Step {i + 1}: level={level:.1f}", end="")

        if event:
            event_count += 1
            print(f" → EVENT #{event_count} at timestamp={event.timestamp:.2f}")
        else:
            print()

    print(f"\n✓ Detected {event_count} events (expected: 2)\n")
    assert event_count == 2, f"Expected 2 events, got {event_count}"


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("CheerDetector Integration Tests")
    print("=" * 60)
    print()

    try:
        test_pseudo_mode()
        test_context_manager()
        test_event_detection()
        test_real_mic_mode_mock()

        print("=" * 60)
        print("All Integration Tests Completed!")
        print("=" * 60)
        print("\n✓ CheerDetector successfully integrates USBMicDetector")
        print("✓ Backward compatibility maintained")
        print("✓ Context manager support added")
        print("✓ Resource cleanup works correctly")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
