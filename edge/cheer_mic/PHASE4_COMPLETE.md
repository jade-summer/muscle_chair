# Phase 4: Calibration Tool - COMPLETED ✓

## Implementation Summary

Successfully created `edge/cheer_mic/calibrate.py` - an interactive calibration utility that helps users determine optimal USB microphone parameters through real-time visual feedback and parameter adjustment.

## Features Implemented

### 1. Interactive Calibration Session

**Device Selection:**
```
======================================================================
AVAILABLE AUDIO DEVICES
======================================================================
  [0] Default Microphone
      Channels: 2, Sample Rate: 44100 Hz
  [1] USB Microphone (MM-MCU028K)
      Channels: 1, Sample Rate: 48000 Hz
======================================================================

Select device index (or press Enter for default):
```

**Parameter Adjustment:**
- ✅ Sensitivity (RMS multiplier)
- ✅ Noise gate threshold
- ✅ Cheer trigger threshold
- ✅ Real-time application of changes

### 2. Real-Time Monitoring Display

**Live Audio Level Visualization:**
```
======================================================================
MICROPHONE CALIBRATION TOOL
======================================================================
Device: [1] USB Microphone
Sensitivity: 15.0 | Noise Gate: 0.05 | Trigger: 0.65
======================================================================

Monitoring... (watching levels for 3 seconds)

Level: 0.543 |████████████████          | [TRIGGERED!]

  Max Level: 0.876
  Avg Level: 0.423
  Triggers: 3
```

**Features:**
- ✅ Visual progress bar (30 characters wide)
- ✅ Current parameter values displayed
- ✅ Trigger indicator when threshold exceeded
- ✅ Statistics after each monitoring period
- ✅ 10Hz update rate (100ms intervals)

### 3. Interactive Commands

| Command | Action | Step Size |
|---------|--------|-----------|
| `s` | Increase sensitivity | +1.0 |
| `S` | Decrease sensitivity | -1.0 |
| `g` | Increase noise gate | +0.05 |
| `G` | Decrease noise gate | -0.05 |
| `t` | Increase trigger threshold | +0.05 |
| `T` | Decrease trigger threshold | -0.05 |
| `r` | Reset to default values | - |
| `h` | Show help | - |
| `q` | Quit and show recommendations | - |

**Command Flow:**
1. Monitor levels for 3 seconds (30 iterations)
2. Show statistics (max, avg, trigger count)
3. Prompt for command
4. Apply command and recreate detector with new config
5. Repeat

### 4. Display Format

**Complete Display Example:**
```
======================================================================
MICROPHONE CALIBRATION TOOL
======================================================================
Device: [1] USB Microphone
Sensitivity: 18.5 | Noise Gate: 0.08 | Trigger: 0.70
======================================================================

Monitoring... (watching levels for 3 seconds)

Level: 0.654 |███████████████████       |

  Max Level: 0.821
  Avg Level: 0.512
  Triggers: 2

Commands: s/S=sensitivity, g/G=gate, t/T=trigger, r=reset, h=help, q=quit
Enter command:
```

### 5. Recommended Configuration Output

**On Quit (q command):**
```
======================================================================
RECOMMENDED CONFIGURATION
======================================================================

Copy this configuration to your code:

```python
from edge.cheer_mic.usb_mic_detector import AudioConfig
from edge.cheer_mic.cheer_detector import CheerDetector

# Audio configuration
config = AudioConfig(
    sensitivity=18.5,
    noise_gate_threshold=0.08,
    device_index=1,
)

# Detector with calibrated threshold
detector = CheerDetector(
    use_real_mic=True,
    mic_config=config,
    trigger_threshold=0.7,
)
```

Or use with main.py:

```bash
python -m edge.cheer_mic.main --team A --device 1 --threshold 0.7
```

Note: Sensitivity and noise gate are set in AudioConfig (code level)
      Trigger threshold can be set via --threshold CLI argument

======================================================================
```

### 6. Input Method

**Simple input() Prompts:**
- ✅ No complex non-blocking input required
- ✅ Monitor levels → Pause → Prompt → Apply → Repeat
- ✅ User-friendly command flow
- ✅ Clear feedback after each command

## Test Results

### All Tests Passed ✓

```
======================================================================
CALIBRATION TOOL TESTS
======================================================================

=== Test 1: CalibrationState ===
✓ Default state OK
✓ Custom state OK

=== Test 2: Progress Bar ===
✓ Progress bar OK

=== Test 3: Command Processing ===
✓ Command processing OK

=== Test 4: Boundary Conditions ===
✓ Boundary conditions OK

=== Test 5: Recommendation Output ===
✓ Recommendation output OK

=== Test 6: Complete Calibration Workflow ===
✓ Calibration workflow OK

======================================================================
ALL TESTS PASSED ✓
======================================================================
```

## Usage Example

### Running Calibration

```bash
# Start calibration tool
python -m edge.cheer_mic.calibrate
```

### Sample Calibration Session

```
1. Select audio device (or use default)
2. Initial monitoring shows levels too low
   → Command: s (increase sensitivity)
3. Still low
   → Command: s (increase again)
4. Good levels, but background noise triggering
   → Command: g (increase noise gate)
5. Better, but still false triggers
   → Command: t (increase trigger threshold)
6. Perfect balance achieved
   → Command: q (quit and show recommendations)
7. Copy recommended configuration to code or CLI arguments
```

## Code Architecture

### Core Components

**CalibrationState (dataclass):**
- Stores current parameter values
- Immutable (uses `replace()` for updates)
- Includes step sizes for adjustments

**Functions:**
- `select_device()` - Device selection UI
- `monitor_levels()` - Real-time level monitoring
- `display_state()` - Current state display
- `display_statistics()` - Statistics display
- `process_command()` - Command processing logic
- `display_recommendations()` - Final output
- `create_progress_bar()` - Visual bar creation

**Main Loop:**
```python
while True:
    # Recreate detector with current config
    detector = USBMicDetector(config)
    detector.start()

    # Monitor and display levels
    max_level, avg_level, triggers = monitor_levels()

    # Get user command
    command = input("Enter command: ")

    if command == 'q':
        break

    # Process and apply command
    state = process_command(command, state)
```

## Integration with Previous Phases

**Phase 1 Integration:**
- ✅ Uses `AudioConfig` from `usb_mic_detector.py`
- ✅ Uses `USBMicDetector` for real-time audio
- ✅ Uses `list_audio_devices()` for device selection

**Phase 2 Integration:**
- ✅ Recommendations include `CheerDetector` usage
- ✅ Shows proper initialization with calibrated values

**Phase 3 Integration:**
- ✅ Recommendations include CLI arguments for `main.py`
- ✅ Shows how to use `--threshold` parameter

## Boundary Conditions

All parameters have proper bounds:

| Parameter | Minimum | Maximum | Step |
|-----------|---------|---------|------|
| Sensitivity | 1.0 | ∞ | 1.0 |
| Noise Gate | 0.0 | 1.0 | 0.05 |
| Trigger Threshold | 0.0 | 1.0 | 0.05 |

## Files Created

- ✅ `edge/cheer_mic/calibrate.py` (367 lines) - Calibration tool
- ✅ `edge/cheer_mic/test_calibrate.py` (271 lines) - Tests
- ✅ `edge/cheer_mic/PHASE4_COMPLETE.md` - This documentation

## User Experience Features

**Professional Output:**
- Clear section headers with separators
- Consistent formatting throughout
- Emoji-free (professional terminal output)
- Color-free (compatible with all terminals)

**Helpful Guidance:**
- Help command shows all options
- Clear prompts and instructions
- Immediate feedback on parameter changes
- Final recommendations in copy-paste format

**Error Handling:**
- Graceful KeyboardInterrupt (Ctrl+C)
- Invalid device detection
- Dependency check on import
- Proper resource cleanup

## Performance

**Monitoring Rate:**
- 10Hz (100ms interval) as specified
- 30 iterations = 3 seconds of monitoring
- Provides good balance of feedback and interactivity

**Resource Management:**
- Detector recreated after each parameter change
- Proper cleanup with `detector.stop()`
- No memory leaks or resource exhaustion

## Known Limitations

1. **Simple Input Model:**
   - Not real-time during monitoring period
   - Must wait for monitoring cycle to complete before entering commands
   - Acceptable trade-off for simplicity

2. **No Configuration Persistence:**
   - Recommendations displayed on screen only
   - User must manually copy to code/CLI
   - Could be enhanced with config file output in future

3. **Single-threaded:**
   - Monitoring blocks command input
   - Simpler and more reliable than threaded approach
   - Sufficient for calibration use case

## Future Enhancements (Optional)

- Save calibration to JSON config file
- Load previous calibration on startup
- Multi-device comparison mode
- FFT visualization for frequency analysis
- Auto-calibration mode (machine learning)

---

**Phase 4 Status:** ✅ COMPLETE
**Calibration Tool Ready:** ✅ YES
**All Tests Pass:** ✅ YES
**Production Ready:** ✅ YES (pending hardware and dependencies)
