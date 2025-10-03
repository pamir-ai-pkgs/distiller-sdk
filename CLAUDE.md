# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Distiller SDK - Python SDK for the Distiller CM5 platform providing hardware control for e-ink displays, audio I/O, camera, LED control, and AI capabilities (ASR/TTS) using uv package management. Built as a Debian package targeting ARM64 Linux systems (Raspberry Pi CM5, Radxa Zero 3/3W).

## Build Commands

```bash
# Download AI models (Parakeet ASR, Piper TTS)
./build.sh                    # Standard models (~200MB)
./build.sh --whisper          # Include Whisper models (~500MB+)
./build.sh --skip-rust        # Skip Rust library build

# Build Debian package
./build-deb.sh                # Standard build
./build-deb.sh clean          # Clean rebuild
./build-deb.sh whisper        # Include Whisper models

# Install locally for testing
sudo dpkg -i dist/distiller-sdk_*_arm64.deb
sudo apt-get install -f       # Fix dependencies
```

## Development Setup

```bash
# Install with uv (for local development)
uv venv --system-site-packages
source .venv/bin/activate
uv sync

# Set up Python path for imports
export PYTHONPATH="/opt/distiller-sdk:$PYTHONPATH"
export LD_LIBRARY_PATH="/opt/distiller-sdk/lib:$LD_LIBRARY_PATH"
```

## Testing

```bash
# Test hardware modules (requires actual hardware)
python -m distiller_sdk.hardware.audio._audio_test
python -m distiller_sdk.hardware.camera._camera_unit_test
python -m distiller_sdk.hardware.eink._display_test

# Verify SDK imports
python -c "import distiller_sdk; print('SDK imported successfully!')"
python -c "from distiller_sdk.hardware.audio import Audio; from distiller_sdk.hardware.camera import Camera; from distiller_sdk.hardware.eink import Display; from distiller_sdk.parakeet import Parakeet; from distiller_sdk.piper import Piper; print('All imports successful!')"
```

## Architecture

### Module Structure
```
src/distiller_sdk/
├── hardware/           # Hardware abstraction layer
│   ├── audio/         # ALSA-based audio I/O with streaming
│   ├── camera/        # V4L2 camera capture (OpenCV)
│   ├── eink/          # E-ink display control via ctypes to C library
│   │   └── composer/  # Image processing, text rendering, transformations
│   └── sam/           # LED control via sysfs GPIO
├── parakeet/          # ASR engine (sherpa-onnx) with VAD
├── piper/             # TTS engine (Piper)
└── whisper/           # Optional Whisper ASR (faster-whisper)
```

### Platform Detection System
Multi-platform support via `platform-detect.sh` helper script:
- **Raspberry Pi CM5** (BCM2712): `/dev/spidev0.0`, `/dev/gpiochip0`
- **Radxa Zero 3/3W** (RK3566): `/dev/spidev3.0`, `/dev/gpiochip3`
- **Armbian** builds: Kernel pattern detection during build
- Override with `DISTILLER_PLATFORM` environment variable

Platform-specific configurations in `configs/`:
- `cm5.conf` - Raspberry Pi CM5 hardware settings
- `radxa-zero3.conf` - Radxa Zero 3/3W hardware settings

### E-ink Display Architecture
The display system uses ctypes bindings to a C shared library (`libdistiller_display_sdk_shared.so`):
- **Firmware types**: EPD128x250 (250×128), EPD240x416 (240×416)
- **Configuration priority**: 1) `DISTILLER_EINK_FIRMWARE` env var, 2) config files, 3) default EPD128x250
- **Image processing**: Supports PNG/JPEG/GIF/BMP/TIFF/WebP with auto-scaling, dithering, and transformations
- **Bitpacking**: 1-bit packed data with standalone transformation functions for rotation/flipping
- **Composer submodule**: Template rendering, text overlay, shape drawing

### Audio System
ALSA-based audio with both file and streaming operations:
- **Static vs instance methods**: `set_mic_gain_static()` for system-wide, `set_mic_gain()` for instance
- **Recording modes**: File recording, streaming with callback
- **Playback**: Direct file playback or stream playback with format control
- Thread-safe recording state management

### Camera System
V4L2 camera interface via OpenCV:
- Single frame capture or continuous streaming
- Configurable camera settings (brightness, contrast, etc.)
- Frame callback mechanism for processing

### AI Integration
- **Parakeet**: Streaming ASR with VAD (Voice Activity Detection) using sherpa-onnx
- **Piper**: TTS with direct audio output or WAV file generation
- **Whisper** (optional): High-quality ASR alternative

## Debian Packaging

### Package Build System
Universal `build-deb.sh` script with:
- Auto-detection of project type (python-uv, python, nodejs, dkms, systemd)
- Target architecture override: `TARGET_ARCH=arm64 ./build-deb.sh`
- Platform-agnostic single package (replaces old per-platform packages)

### Post-installation Flow (`debian/postinst`)
1. Detect platform using `platform-detect.sh`
2. Copy platform-specific config to `/opt/distiller-sdk/eink.conf`
3. Create uv virtual environment with system-site-packages
4. Run `uv sync` to install dependencies
5. Verify Python environment and SDK imports
6. Generate `activate.sh` script for environment setup
7. Check for required devices (SPI, GPIO) and warn if missing
8. Update `ldconfig` cache for shared libraries

### Installation Location
All files install to `/opt/distiller-sdk/`:
- Python source in `src/distiller_sdk/`
- AI models in `models/`, `parakeet/models/`, `piper/models/`
- Native libraries in `lib/`
- Virtual environment in `.venv/`
- Activation script: `activate.sh`

## Important Patterns

### Hardware Manager Pattern
When coordinating multiple hardware components, use a manager class to initialize, coordinate, and cleanup resources. See README.md Hardware Manager Pattern example.

### Context Manager Usage
Display class supports context manager for automatic cleanup:
```python
with Display() as display:
    display.display_image("image.png", mode=DisplayMode.FULL)
# Automatically cleaned up
```

### Error Handling
All hardware modules raise custom exceptions (`DisplayError`, etc.) for error conditions. Always handle hardware initialization failures gracefully as devices may not be present.

### Transformation Chaining
For e-ink display transformations, note that dimensions swap after 90/270° rotations:
```python
# Original: 250x128, after 90° rotation: 128x250
result = flip_bitpacked_vertical(
    rotate_bitpacked_ccw_90(data, 250, 128),
    128, 250  # Swapped dimensions
)
```

## Development Notes

- **Target platform**: ARM64 only, but builds can run on x86_64 for Debian package creation
- **Python version**: 3.11+ required (managed by uv)
- **Ruff config**: Line length 100, target Python 3.11
- **Hardware access**: May require sudo or user groups (audio, video, spi, gpio, i2c)
- **Model downloads**: Hugging Face for Parakeet/Whisper, GitHub releases for Piper
- **Native dependencies**: C library for e-ink display lives in `src/distiller_sdk/hardware/eink/lib/`

## Common Pitfalls

1. **Display firmware mismatch**: EPD128x250 firmware name represents 250×128 display (width×height), not 128×250
2. **Platform detection during build**: Armbian builds must detect platform via kernel patterns before `/etc/armbian-release` exists
3. **uv installation**: `postinst` script must handle multiple uv installation paths (root, user, system)
4. **Audio permissions**: Recording/playback requires user in `audio` group
5. **SPI/GPIO access**: E-ink display requires SPI enabled in device tree and proper GPIO permissions
