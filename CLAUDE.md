# AI-DLC and Spec-Driven Development

Kiro-style Spec Driven Development implementation on AI-DLC (AI Development Life Cycle)

## Project Context

### Paths
- Steering: `.kiro/steering/`
- Specs: `.kiro/specs/`

### Steering vs Specification

**Steering** (`.kiro/steering/`) - Guide AI with project-wide rules and context
**Specs** (`.kiro/specs/`) - Formalize development process for individual features

### Active Specifications
- Check `.kiro/specs/` for active specifications
- Use `/kiro:spec-status [feature-name]` to check progress

## Development Guidelines
- Think in English, generate responses in Japanese. All Markdown content written to project files (e.g., requirements.md, design.md, tasks.md, research.md, validation reports) MUST be written in the target language configured for this specification (see spec.json.language).

## Minimal Workflow
- Phase 0 (optional): `/kiro:steering`, `/kiro:steering-custom`
- Phase 1 (Specification):
  - `/kiro:spec-init "description"`
  - `/kiro:spec-requirements {feature}`
  - `/kiro:validate-gap {feature}` (optional: for existing codebase)
  - `/kiro:spec-design {feature} [-y]`
  - `/kiro:validate-design {feature}` (optional: design review)
  - `/kiro:spec-tasks {feature} [-y]`
- Phase 2 (Implementation): `/kiro:spec-impl {feature} [tasks]`
  - `/kiro:validate-impl {feature}` (optional: after implementation)
- Progress check: `/kiro:spec-status {feature}` (use anytime)

## Development Rules
- 3-phase approval workflow: Requirements → Design → Tasks → Implementation
- Human review required each phase; use `-y` only for intentional fast-track
- Keep steering current and verify alignment with `/kiro:spec-status`
- Follow the user's instructions precisely, and within that scope act autonomously: gather the necessary context and complete the requested work end-to-end in this run, asking questions only when essential information is missing or the instructions are critically ambiguous.

## Steering Configuration
- Load entire `.kiro/steering/` as project memory
- Default files: `product.md`, `tech.md`, `structure.md`
- Custom files are supported (managed via `/kiro:steering-custom`)

---

# USB Microphone Integration for Cheer Detection

## Overview
Integrate real USB microphone input (MM-MCU028K) to replace pseudo audio data in the cheer detection system. This enables real-time cheer level detection based on actual audio volume.

## Hardware Specifications
- **Microphone Model**: SANWA SUPPLY MM-MCU028K
- **Quantity**: 1 units (Team A or Team B)
- **Connection**: USB Type-A (requires Micro USB OTG adapter for Raspberry Pi Zero 2 W)
- **Driver**: USB Audio Class compliant (driverless)

## Technical Requirements

### Audio Processing
- **Detection Method**: Simple volume-based (RMS calculation)
- **Philosophy**: Sound volume = Cheer intensity
- **Sampling Rate**: 16kHz (lightweight for Raspberry Pi Zero)
- **Buffer Size**: 1024 samples
- **Update Frequency**: 10Hz (100ms interval)
- **Output Range**: 0.0 - 1.0 (normalized level)

### Feature Requirements
1. **Noise Gate**: Filter out ambient noise below threshold
2. **Smoothing**: Moving average filter to reduce jitter
3. **Sensitivity Adjustment**: Configurable RMS-to-level conversion factor
4. **Device Selection**: Support multiple USB audio devices
5. **Fallback Mode**: Maintain pseudo data mode for testing without hardware

### Development Environment
- **Primary Development**: WSL2 on Windows (using Windows microphone via WSLg)
- **Testing**: Local PC → Raspberry Pi Zero 2 W
- **Target OS**: Raspberry Pi OS (Debian-based)

## Implementation Strategy

### Phase 1: Core USB Microphone Module
Create `edge/cheer_mic/usb_mic_detector.py`:
- AudioConfig dataclass for configuration
- USBMicDetector class with real-time audio input
- Device listing utility function
- Standalone testing capability

### Phase 2: Integration with Existing System
Modify `edge/cheer_mic/cheer_detector.py`:
- Add `use_real_mic` parameter to CheerDetector
- Integrate USBMicDetector while maintaining backward compatibility
- Preserve pseudo data mode for testing

### Phase 3: CLI Enhancement
Update `edge/cheer_mic/main.py`:
- Add command-line arguments (--team, --device, --debug, --backend)
- Support both real microphone and pseudo data modes
- Add visual feedback (level bar in terminal)

### Phase 4: Calibration Tool
Create `edge/cheer_mic/calibrate.py`:
- Interactive calibration utility
- Display real-time audio levels
- Test and adjust sensitivity/threshold parameters
- Save recommended configuration

## Architecture Principles (MUST FOLLOW)
1. **Separation of Concerns**: Audio input, event detection, and transmission are separate modules
2. **Dependency Injection**: Use Protocol pattern for transport abstraction
3. **Graceful Degradation**: System works with or without real microphone
4. **Resource Management**: Proper cleanup with context managers
5. **Configurability**: All thresholds/parameters should be adjustable without code changes

## Testing Requirements
- Unit tests for audio processing functions (mock PyAudio)
- Integration test with pseudo data
- Manual testing with real USB microphone
- Performance test on Raspberry Pi Zero (CPU/memory usage)

## Dependencies
Python packages:
```txt
pyaudio>=0.2.13
numpy>=1.24.0
```

System packages (Raspberry Pi):
```bash
sudo apt install portaudio19-dev python3-pyaudio
```

## Configuration Parameters (To Be Determined by Testing)
The following values are initial estimates and MUST be calibrated with actual hardware:
```python
# Audio capture
SAMPLE_RATE = 16000          # Hz
CHUNK_SIZE = 1024            # samples
CHANNELS = 1                 # mono

# Signal processing
SENSITIVITY = 15.0           # RMS multiplier (TBD)
NOISE_GATE_THRESHOLD = 0.05  # Minimum level to register (TBD)
SMOOTHING_WINDOW_SIZE = 3    # Moving average window (TBD)

# Event detection
CHEER_TRIGGER_THRESHOLD = 0.65  # Level to trigger event (TBD)
```

**Note**: These parameters will be determined through the calibration tool testing phase.

## File Structure
```
edge/cheer_mic/
├── __init__.py
├── main.py                  # Entry point (UPDATE)
├── cheer_detector.py        # Detector with mic integration (UPDATE)
├── usb_mic_detector.py      # New USB mic input module (NEW)
├── calibrate.py             # Calibration utility (NEW)
├── sender.py                # Unchanged
└── README.md                # Documentation (NEW)
```

## Success Criteria
1. ✅ USB microphone detected and accessible in WSL2
2. ✅ Real-time audio level visualization in terminal
3. ✅ CheerEvent triggered when volume exceeds threshold
4. ✅ HTTP POST successfully sent to backend
5. ✅ CPU usage < 30% on Raspberry Pi Zero 2 W
6. ✅ Latency < 200ms (audio input → backend notification)

## Raspberry Pi Zero 2 W Hardware Notes
- **USB Connection**: Use Micro USB OTG port (NOT the Type-C power port)
- **Required Adapter**: Micro USB (male) to USB Type-A (female) OTG adapter
- **Power**: Ensure adequate power supply (2.5A+ recommended when using USB peripherals)
- **Audio Device Detection**: 
```bash
  # List USB devices
  lsusb
  
  # List audio devices
  arecord -l
  
  # Test recording
  arecord -D plughw:1,0 -f cd -d 10 test.wav
```

---

## Single Mic Cheer Detection (全国大会向け改修)

### 変更概要
ハードウェア制約により USB マイクを 2 本から 1 本に変更。
1 本のマイクで片方のチームの応援のみを検知する設計（シングルチームモード）。
コードの変更は不要で、既存の --team 引数をそのまま使用する。

### 設計方針
- **方式**: シングルチームモード
  - 1 本のマイクを応援席の近くに設置し、対象チームを --team 引数で指定する
  - 音量がしきい値を超えたら CHEER_TRIGGER イベントを HTTP POST で送信する
  - バックエンド・デバイス制御・Web UI の変更は不要（完全互換）

### 使用方法
```bash
# シングルマイク・Team A 検知（本番用）
python3 -m edge.cheer_mic.main --team A --backend http://<SERVER_IP>:8000/api/cheer/trigger

# シングルマイク・Team B 検知（本番用）
python3 -m edge.cheer_mic.main --team B --backend http://<SERVER_IP>:8000/api/cheer/trigger

# デバッグモード（マイクなし）
python3 -m edge.cheer_mic.main --team A --debug
```

### 変更ファイル
- なし（既存コードをそのまま使用）

### ドキュメント更新
- `README.md`: ハードウェア台数・構成図を更新
