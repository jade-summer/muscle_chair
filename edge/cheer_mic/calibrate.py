"""Interactive calibration utility for USB microphone parameters.

This tool helps users determine optimal values for sensitivity, noise gate,
and trigger threshold by providing real-time visual feedback.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, replace
from typing import Optional

try:
    from .usb_mic_detector import AudioConfig, USBMicDetector, list_audio_devices
except ImportError:
    print("Error: USB microphone dependencies not available.")
    print("Install: sudo apt install portaudio19-dev python3-pyaudio python3-numpy")
    sys.exit(1)


@dataclass
class CalibrationState:
    """Current calibration parameters."""

    sensitivity: float = 15.0
    noise_gate_threshold: float = 0.05
    trigger_threshold: float = 0.65
    device_index: Optional[int] = None

    # Step sizes for adjustments
    sensitivity_step: float = 1.0
    threshold_step: float = 0.05


def create_progress_bar(level: float, width: int = 30) -> str:
    """Create a visual progress bar for audio level.

    Args:
        level: Audio level (0.0-1.0)
        width: Width of progress bar in characters

    Returns:
        Progress bar string
    """
    filled_width = int(level * width)
    bar = "█" * filled_width + "░" * (width - filled_width)
    return bar


def display_help() -> None:
    """Display help for calibration commands."""
    print("\n" + "=" * 70)
    print("CALIBRATION COMMANDS")
    print("=" * 70)
    print("  s - Increase sensitivity (+1.0)")
    print("  S - Decrease sensitivity (-1.0)")
    print("  g - Increase noise gate (+0.05)")
    print("  G - Decrease noise gate (-0.05)")
    print("  t - Increase trigger threshold (+0.05)")
    print("  T - Decrease trigger threshold (-0.05)")
    print("  r - Reset to default values")
    print("  h - Show this help")
    print("  q - Quit and show recommended configuration")
    print("=" * 70)
    print()


def select_device() -> Optional[int]:
    """Prompt user to select an audio device.

    Returns:
        Selected device index or None for default
    """
    print("\n" + "=" * 70)
    print("AVAILABLE AUDIO DEVICES")
    print("=" * 70)

    devices = list_audio_devices()

    if not devices:
        print("No audio input devices found!")
        return None

    for device in devices:
        print(
            f"  [{device['index']}] {device['name']}\n"
            f"      Channels: {device['channels']}, "
            f"Sample Rate: {device['sample_rate']} Hz"
        )

    print("=" * 70)
    print()

    while True:
        choice = input("Select device index (or press Enter for default): ").strip()

        if not choice:
            print("Using default device\n")
            return None

        try:
            index = int(choice)
            # Validate device exists
            if any(d["index"] == index for d in devices):
                print(f"Selected device: {index}\n")
                return index
            else:
                print(f"Invalid device index: {index}. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number or press Enter.")


def monitor_levels(
    detector: USBMicDetector,
    state: CalibrationState,
    iterations: int = 30,
) -> tuple[float, float, int]:
    """Monitor audio levels for a period and return statistics.

    Args:
        detector: USB microphone detector
        state: Current calibration state
        iterations: Number of iterations to monitor

    Returns:
        Tuple of (max_level, avg_level, trigger_count)
    """
    max_level = 0.0
    total_level = 0.0
    trigger_count = 0
    last_triggered = False

    print("\nMonitoring... (watching levels for 3 seconds)\n")

    for i in range(iterations):
        level = detector.read_level()

        # Track statistics
        max_level = max(max_level, level)
        total_level += level

        # Check for trigger
        triggered = level >= state.trigger_threshold
        if triggered and not last_triggered:
            trigger_count += 1
        last_triggered = triggered

        # Display current state
        bar = create_progress_bar(level, width=30)
        trigger_indicator = " [TRIGGERED!]" if triggered else ""

        # Clear line and display
        print(f"\rLevel: {level:.3f} |{bar}|{trigger_indicator}", end="", flush=True)

        time.sleep(0.1)  # 10Hz update rate

    print("\n")  # New line after monitoring

    avg_level = total_level / iterations if iterations > 0 else 0.0
    return max_level, avg_level, trigger_count


def display_state(state: CalibrationState, device_name: str = "Default") -> None:
    """Display current calibration state.

    Args:
        state: Current calibration state
        device_name: Name of the audio device
    """
    print("=" * 70)
    print("MICROPHONE CALIBRATION TOOL")
    print("=" * 70)
    print(f"Device: {device_name}")
    print(
        f"Sensitivity: {state.sensitivity:.1f} | "
        f"Noise Gate: {state.noise_gate_threshold:.3f} | "
        f"Trigger: {state.trigger_threshold:.2f}"
    )
    print("=" * 70)


def display_statistics(max_level: float, avg_level: float, trigger_count: int) -> None:
    """Display statistics from monitoring period.

    Args:
        max_level: Maximum level observed
        avg_level: Average level observed
        trigger_count: Number of times trigger threshold was crossed
    """
    print(f"  Max Level: {max_level:.3f}")
    print(f"  Avg Level: {avg_level:.3f}")
    print(f"  Triggers: {trigger_count}")
    print()


def process_command(command: str, state: CalibrationState) -> CalibrationState:
    """Process a calibration command and return updated state.

    Args:
        command: Single character command
        state: Current calibration state

    Returns:
        Updated calibration state
    """
    if command == "s":
        # Increase sensitivity
        new_sensitivity = state.sensitivity + state.sensitivity_step
        print(f"Increased sensitivity: {state.sensitivity:.1f} → {new_sensitivity:.1f}")
        return replace(state, sensitivity=new_sensitivity)

    elif command == "S":
        # Decrease sensitivity
        new_sensitivity = max(1.0, state.sensitivity - state.sensitivity_step)
        print(f"Decreased sensitivity: {state.sensitivity:.1f} → {new_sensitivity:.1f}")
        return replace(state, sensitivity=new_sensitivity)

    elif command == "g":
        # Increase noise gate
        new_gate = min(1.0, state.noise_gate_threshold + state.threshold_step)
        print(
            f"Increased noise gate: {state.noise_gate_threshold:.3f} → {new_gate:.3f}"
        )
        return replace(state, noise_gate_threshold=new_gate)

    elif command == "G":
        # Decrease noise gate
        new_gate = max(0.0, state.noise_gate_threshold - state.threshold_step)
        print(
            f"Decreased noise gate: {state.noise_gate_threshold:.3f} → {new_gate:.3f}"
        )
        return replace(state, noise_gate_threshold=new_gate)

    elif command == "t":
        # Increase trigger threshold
        new_trigger = min(1.0, state.trigger_threshold + state.threshold_step)
        print(
            f"Increased trigger: {state.trigger_threshold:.2f} → {new_trigger:.2f}"
        )
        return replace(state, trigger_threshold=new_trigger)

    elif command == "T":
        # Decrease trigger threshold
        new_trigger = max(0.0, state.trigger_threshold - state.threshold_step)
        print(
            f"Decreased trigger: {state.trigger_threshold:.2f} → {new_trigger:.2f}"
        )
        return replace(state, trigger_threshold=new_trigger)

    elif command == "r":
        # Reset to defaults
        print("Reset to default values")
        return CalibrationState(device_index=state.device_index)

    elif command == "h":
        # Show help
        display_help()
        return state

    else:
        print(f"Unknown command: {command}")
        return state


def display_recommendations(state: CalibrationState) -> None:
    """Display recommended configuration based on calibration.

    Args:
        state: Final calibration state
    """
    print("\n" + "=" * 70)
    print("RECOMMENDED CONFIGURATION")
    print("=" * 70)
    print()
    print("Copy this configuration to your code:")
    print()
    print("```python")
    print("from edge.cheer_mic.usb_mic_detector import AudioConfig")
    print("from edge.cheer_mic.cheer_detector import CheerDetector")
    print()
    print("# Audio configuration")
    print("config = AudioConfig(")
    print(f"    sensitivity={state.sensitivity},")
    print(f"    noise_gate_threshold={state.noise_gate_threshold},")

    if state.device_index is not None:
        print(f"    device_index={state.device_index},")

    print(")")
    print()
    print("# Detector with calibrated threshold")
    print("detector = CheerDetector(")
    print("    use_real_mic=True,")
    print("    mic_config=config,")
    print(f"    trigger_threshold={state.trigger_threshold},")
    print(")")
    print("```")
    print()
    print("Or use with main.py:")
    print()
    print("```bash")

    cmd = "python -m edge.cheer_mic.main --team A"
    if state.device_index is not None:
        cmd += f" --device {state.device_index}"
    cmd += f" --threshold {state.trigger_threshold}"

    print(cmd)
    print("```")
    print()
    print("Note: Sensitivity and noise gate are set in AudioConfig (code level)")
    print(f"      Trigger threshold can be set via --threshold CLI argument")
    print()
    print("=" * 70)


def main() -> None:
    """Run the interactive calibration session."""
    print("\n" + "=" * 70)
    print("MICROPHONE CALIBRATION UTILITY")
    print("=" * 70)
    print()
    print("This tool helps you calibrate your USB microphone for optimal")
    print("cheer detection by adjusting sensitivity, noise gate, and trigger")
    print("threshold in real-time.")
    print()

    # Select device
    device_index = select_device()

    # Initialize calibration state
    state = CalibrationState(device_index=device_index)

    # Get device name for display
    if device_index is not None:
        devices = list_audio_devices()
        device_info = next((d for d in devices if d["index"] == device_index), None)
        device_name = (
            f"[{device_index}] {device_info['name']}" if device_info else f"[{device_index}]"
        )
    else:
        device_name = "Default"

    # Create detector with initial configuration
    detector: Optional[USBMicDetector] = None

    try:
        # Show initial help
        display_help()
        input("Press Enter to start calibration...")

        while True:
            # Create/recreate detector with current configuration
            if detector is not None:
                detector.stop()

            config = AudioConfig(
                sensitivity=state.sensitivity,
                noise_gate_threshold=state.noise_gate_threshold,
                device_index=state.device_index,
            )
            detector = USBMicDetector(config)
            detector.start()

            # Display current state
            display_state(state, device_name)

            # Monitor levels
            max_level, avg_level, trigger_count = monitor_levels(detector, state)

            # Display statistics
            display_statistics(max_level, avg_level, trigger_count)

            # Prompt for command
            print("Commands: s/S=sensitivity, g/G=gate, t/T=trigger, r=reset, h=help, q=quit")
            command = input("Enter command: ").strip()

            if command == "q":
                print("\nExiting calibration...")
                break

            # Process command
            state = process_command(command, state)
            print()

    except KeyboardInterrupt:
        print("\n\nCalibration interrupted by user (Ctrl+C)")

    except Exception as e:
        print(f"\n\nError during calibration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Clean up detector
        if detector is not None:
            detector.stop()

    # Display recommendations
    display_recommendations(state)

    print("\nCalibration complete!")


if __name__ == "__main__":
    main()
