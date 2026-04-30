"""Test for calibration tool functionality.

This demonstrates the calibration tool's core functions without requiring
interactive input or hardware.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['pyaudio'] = MagicMock()
sys.modules['numpy'] = MagicMock()

import numpy as np  # noqa: E402
np.frombuffer = lambda data, dtype: MagicMock(astype=lambda x: MagicMock(__pow__=lambda self, p: [100.0] * 1024))
np.mean = lambda x: 10000.0
np.sqrt = lambda x: 100.0
np.int16 = int
np.float32 = float

from edge.cheer_mic.calibrate import (  # noqa: E402
    CalibrationState,
    create_progress_bar,
    process_command,
    display_recommendations,
)


def test_calibration_state():
    """Test CalibrationState dataclass."""
    print("=== Test 1: CalibrationState ===\n")

    # Default state
    state = CalibrationState()
    assert state.sensitivity == 15.0
    assert state.noise_gate_threshold == 0.05
    assert state.trigger_threshold == 0.65
    assert state.device_index is None
    print("✓ Default state OK")

    # Custom state
    custom_state = CalibrationState(
        sensitivity=20.0,
        noise_gate_threshold=0.1,
        trigger_threshold=0.7,
        device_index=1,
    )
    assert custom_state.sensitivity == 20.0
    assert custom_state.device_index == 1
    print("✓ Custom state OK\n")


def test_progress_bar():
    """Test progress bar creation."""
    print("=== Test 2: Progress Bar ===\n")

    # Test various levels
    bar_0 = create_progress_bar(0.0, width=10)
    assert "░" * 10 in bar_0
    print(f"  0.0: |{bar_0}|")

    bar_half = create_progress_bar(0.5, width=10)
    assert "█" in bar_half and "░" in bar_half
    print(f"  0.5: |{bar_half}|")

    bar_full = create_progress_bar(1.0, width=10)
    assert "█" * 10 in bar_full
    print(f"  1.0: |{bar_full}|")

    print("✓ Progress bar OK\n")


def test_command_processing():
    """Test command processing logic."""
    print("=== Test 3: Command Processing ===\n")

    state = CalibrationState()

    # Test sensitivity increase
    new_state = process_command("s", state)
    assert new_state.sensitivity == 16.0
    print(f"  's' command: {state.sensitivity} → {new_state.sensitivity}")

    # Test sensitivity decrease
    new_state = process_command("S", new_state)
    assert new_state.sensitivity == 15.0
    print(f"  'S' command: {new_state.sensitivity} ← 15.0")

    # Test noise gate increase
    new_state = process_command("g", state)
    assert new_state.noise_gate_threshold == 0.10
    print(f"  'g' command: {state.noise_gate_threshold} → {new_state.noise_gate_threshold}")

    # Test noise gate decrease
    new_state = process_command("G", new_state)
    assert new_state.noise_gate_threshold == 0.05
    print(f"  'G' command: {new_state.noise_gate_threshold} ← 0.05")

    # Test trigger increase
    new_state = process_command("t", state)
    assert abs(new_state.trigger_threshold - 0.70) < 0.001
    print(f"  't' command: {state.trigger_threshold} → {new_state.trigger_threshold}")

    # Test trigger decrease
    new_state = process_command("T", new_state)
    assert abs(new_state.trigger_threshold - 0.65) < 0.001
    print(f"  'T' command: {new_state.trigger_threshold} ← 0.65")

    # Test reset
    modified_state = CalibrationState(
        sensitivity=25.0,
        noise_gate_threshold=0.2,
        trigger_threshold=0.8,
    )
    reset_state = process_command("r", modified_state)
    assert reset_state.sensitivity == 15.0
    assert reset_state.noise_gate_threshold == 0.05
    assert reset_state.trigger_threshold == 0.65
    print("  'r' command: Reset to defaults")

    print("✓ Command processing OK\n")


def test_boundary_conditions():
    """Test boundary conditions for parameter adjustments."""
    print("=== Test 4: Boundary Conditions ===\n")

    # Test minimum sensitivity
    state = CalibrationState(sensitivity=1.0)
    new_state = process_command("S", state)  # Try to decrease below minimum
    assert new_state.sensitivity >= 1.0
    print(f"  Min sensitivity: {new_state.sensitivity} >= 1.0 ✓")

    # Test maximum noise gate
    state = CalibrationState(noise_gate_threshold=1.0)
    new_state = process_command("g", state)  # Try to increase above maximum
    assert new_state.noise_gate_threshold <= 1.0
    print(f"  Max noise gate: {new_state.noise_gate_threshold} <= 1.0 ✓")

    # Test minimum noise gate
    state = CalibrationState(noise_gate_threshold=0.0)
    new_state = process_command("G", state)  # Try to decrease below minimum
    assert new_state.noise_gate_threshold >= 0.0
    print(f"  Min noise gate: {new_state.noise_gate_threshold} >= 0.0 ✓")

    # Test maximum trigger threshold
    state = CalibrationState(trigger_threshold=1.0)
    new_state = process_command("t", state)  # Try to increase above maximum
    assert new_state.trigger_threshold <= 1.0
    print(f"  Max trigger: {new_state.trigger_threshold} <= 1.0 ✓")

    # Test minimum trigger threshold
    state = CalibrationState(trigger_threshold=0.0)
    new_state = process_command("T", state)  # Try to decrease below minimum
    assert new_state.trigger_threshold >= 0.0
    print(f"  Min trigger: {new_state.trigger_threshold} >= 0.0 ✓")

    print("\n✓ Boundary conditions OK\n")


def test_recommendation_output():
    """Test recommendation display format."""
    print("=== Test 5: Recommendation Output ===\n")

    # Test with custom calibration
    state = CalibrationState(
        sensitivity=18.5,
        noise_gate_threshold=0.08,
        trigger_threshold=0.70,
        device_index=1,
    )

    print("Expected output for calibrated state:")
    print(f"  Sensitivity: {state.sensitivity}")
    print(f"  Noise Gate: {state.noise_gate_threshold}")
    print(f"  Trigger: {state.trigger_threshold}")
    print(f"  Device: {state.device_index}")
    print()

    # Display recommendations (this will print to stdout)
    display_recommendations(state)

    print("✓ Recommendation output OK\n")


def test_calibration_workflow():
    """Test a complete calibration workflow."""
    print("=== Test 6: Complete Calibration Workflow ===\n")

    # Start with default state
    state = CalibrationState()
    print("Initial state:")
    print(f"  Sensitivity: {state.sensitivity}")
    print(f"  Noise Gate: {state.noise_gate_threshold}")
    print(f"  Trigger: {state.trigger_threshold}")
    print()

    # Simulate calibration session
    print("Simulated calibration session:")

    # User increases sensitivity twice
    print("  1. User hears low audio, increases sensitivity (s)")
    state = process_command("s", state)
    print(f"     → Sensitivity: {state.sensitivity}")

    print("  2. Still too low, increase again (s)")
    state = process_command("s", state)
    print(f"     → Sensitivity: {state.sensitivity}")

    # User adjusts noise gate
    print("  3. Too much background noise, increase gate (g)")
    state = process_command("g", state)
    print(f"     → Noise Gate: {state.noise_gate_threshold}")

    # User adjusts trigger
    print("  4. Too many false triggers, increase threshold (t)")
    state = process_command("t", state)
    print(f"     → Trigger: {state.trigger_threshold}")

    print()
    print("Final calibrated state:")
    print(f"  Sensitivity: {state.sensitivity}")
    print(f"  Noise Gate: {state.noise_gate_threshold}")
    print(f"  Trigger: {state.trigger_threshold}")

    assert abs(state.sensitivity - 17.0) < 0.001
    assert abs(state.noise_gate_threshold - 0.10) < 0.001
    assert abs(state.trigger_threshold - 0.70) < 0.001

    print("\n✓ Calibration workflow OK\n")


def main():
    """Run all calibration tests."""
    print("=" * 70)
    print("CALIBRATION TOOL TESTS")
    print("=" * 70)
    print()

    try:
        test_calibration_state()
        test_progress_bar()
        test_command_processing()
        test_boundary_conditions()
        test_recommendation_output()
        test_calibration_workflow()

        print("=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        print()
        print("The calibration tool is ready to use!")
        print()
        print("To run the calibration tool with real hardware:")
        print("  1. Install dependencies:")
        print("     sudo apt install portaudio19-dev python3-pyaudio python3-numpy")
        print("  2. Run calibration:")
        print("     python -m edge.cheer_mic.calibrate")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
