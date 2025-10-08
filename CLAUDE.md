# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Distiller SDK - Python SDK for the Distiller platform providing hardware control for e-ink displays, audio I/O, camera, LED control, and AI capabilities (ASR/TTS) using uv package management. Built as a Debian package targeting ARM64 Linux systems (Raspberry Pi CM5, Radxa Zero 3/3W, ArmSom CM5 IO).

## Build Commands

```bash
# Download AI models (Parakeet ASR, Piper TTS)
./build.sh                    # Standard models (~200MB)
./build.sh --whisper          # Include Whisper models (~500MB+)
./build.sh --skip-rust        # Skip Rust library build

# Build Debian package using Justfile
just build                    # Standard build (arm64 default)
just build amd64              # Cross-build for amd64
just clean                    # Clean all build artifacts
just prepare whisper          # Download models including Whisper

# Install locally for testing
sudo dpkg -i dist/distiller-sdk_*_arm64.deb
sudo apt-get install -f       # Fix dependencies

# Verify installation
source /opt/distiller-sdk/activate.sh
python -c "import distiller_sdk; print('SDK imported successfully!')"
```

## Development Setup

```bash
# Local development with uv
uv sync                       # Install dependencies (creates .venv)
source .venv/bin/activate     # Activate virtual environment

# Set up Python path for imports (when not using installed package)
export PYTHONPATH="/opt/distiller-sdk:$PYTHONPATH"
export LD_LIBRARY_PATH="/opt/distiller-sdk/lib:$LD_LIBRARY_PATH"
source /opt/distiller-sdk/activate.sh

# Code quality checks
just lint                     # Run ruff check + format check + mypy
just fix                      # Auto-fix formatting issues
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

# Verify installed package (after dpkg -i)
source /opt/distiller-sdk/activate.sh
python -c "import distiller_sdk; print('SDK imported successfully!')"
```

## Package Inspection & Debugging

```bash
# Inspect built package contents
dpkg -c dist/distiller-sdk_*_arm64.deb

# Check package metadata
dpkg-deb -I dist/distiller-sdk_*_arm64.deb

# Run lintian checks (already runs during build)
lintian --pedantic dist/distiller-sdk_*_arm64.deb

# Check installed package files
dpkg -L distiller-sdk

# Debug platform detection
source debian/platform-detect.sh
detect_platform
get_platform_description $(detect_platform)
get_spi_device $(detect_platform)
get_gpio_chip $(detect_platform)

# Check changelog
dch -i    # Edit changelog interactively
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
- **Raspberry Pi CM5** (BCM2712): `/dev/spidev0.0`, `/dev/gpiochip0`, GPIO pins: dc=7, rst=13, busy=9
- **Radxa Zero 3/3W** (RK3566): `/dev/spidev3.0`, `/dev/gpiochip3`, GPIO pins: dc=8, rst=2, busy=1
- **ArmSom CM5 IO** (RK3576): `/dev/spidev3.0`, `/dev/gpiochip4`, GPIO pins: TBD
- **Armbian** builds: Kernel pattern detection via `/lib/modules/` patterns
- Override with `DISTILLER_PLATFORM=cm5|radxa|armsom-rk3576|armbian` environment variable

Platform-specific configurations in `configs/`:
- `cm5.conf` - Raspberry Pi CM5 hardware settings
- `radxa-zero3.conf` - Radxa Zero 3/3W hardware settings
- `armsom-rk3576.conf` - ArmSom CM5 IO hardware settings (GPIO pins incomplete)

Detection priority:
1. `DISTILLER_PLATFORM` environment variable (validated against supported platforms)
2. Armbian detection (`/etc/armbian-release`, `/boot/armbianEnv.txt`, kernel patterns)
3. Device tree compatibility (`/proc/device-tree/compatible`)
4. Defaults to "unknown"

### E-ink Display Architecture
The display system uses ctypes bindings to a Rust-compiled shared library (`libdistiller_display_sdk_shared.so`):
- **Firmware types**: EPD128x250 (250×128), EPD240x416 (240×416)
- **Configuration priority**: 1) `DISTILLER_EINK_FIRMWARE` env var, 2) config files, 3) default EPD128x250
- **Image processing**: Supports PNG/JPEG/GIF/BMP/TIFF/WebP with auto-scaling, dithering, and transformations
- **Bitpacking**: 1-bit packed data with standalone transformation functions for rotation/flipping
- **Composer submodule**: Template rendering, text overlay, shape drawing
- **Rust library**: Located in `src/distiller_sdk/hardware/eink/lib/`, built via `Makefile.rust` for ARM64 target

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
Justfile-based build system (replaces legacy `build-deb.sh`):
- Uses `debuild` with lintian profile for compliance checking
- Target architecture specified via `arch` parameter: `just build arm64` or `just build amd64`
- Platform-agnostic single package (replaces old per-platform packages)
- Provides/Replaces/Breaks `distiller-cm5-sdk` for migration from v2.x
- Build artifacts placed in `dist/` directory

### Post-installation Flow (`debian/postinst`)
1. Remove legacy `/opt/distiller-cm5-sdk/` installation if present
2. Detect platform using `debian/platform-detect.sh` helper functions
3. Copy platform-specific config to `/opt/distiller-sdk/eink.conf`
4. Create uv virtual environment with `--system-site-packages` (fallback to regular venv if needed)
5. Run `uv sync --frozen --no-editable --compile-bytecode` for production install
6. Set appropriate file permissions (readable by all, executables in .venv/bin)
7. Verify Python environment and SDK imports
8. Check for required devices (SPI, GPIO) and warn if missing with platform-specific instructions
9. Update `ldconfig` cache for shared libraries

### Installation Location
All files install to `/opt/distiller-sdk/`:
- Python source in `src/distiller_sdk/`
- AI models in `parakeet/models/`, `piper/models/`, `whisper/models/` (optional)
- Native libraries in `lib/` (Rust e-ink library)
- Virtual environment in `.venv/` (created during postinst)
- Activation script: `activate.sh` (generated during postinst)
- Platform configs in `configs/`

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
- **Rust library**: E-ink display uses Rust library in `src/distiller_sdk/hardware/eink/lib/`
  - Built with `Makefile.rust` targeting `aarch64-unknown-linux-gnu`
  - Auto-rebuilds when source files (.rs), Cargo.toml, or Cargo.lock change
  - Outputs `libdistiller_display_sdk_shared.so` used via ctypes

### Rust E-ink Library Development
```bash
cd src/distiller_sdk/hardware/eink/lib

# Check if rebuild needed
make -f Makefile.rust check-rebuild

# Build library
make -f Makefile.rust build

# Clean build artifacts
make -f Makefile.rust clean

# Show target info
make -f Makefile.rust target-info
```

## Common Pitfalls

1. **Display firmware mismatch**: EPD128x250 firmware name represents 250×128 display (width×height), not 128×250
2. **Platform detection during build**: Armbian builds must detect platform via kernel patterns in `/lib/modules/` before `/etc/armbian-release` exists
3. **uv installation**: `postinst` script handles multiple uv installation paths via PATH export including root/user `.local/bin` and `.cargo/bin`
4. **Audio permissions**: Recording/playback requires user in `audio` group
5. **SPI/GPIO access**: E-ink display requires SPI enabled in device tree and proper GPIO permissions
6. **Rust build dependencies**: E-ink library build requires Rust toolchain with `aarch64-unknown-linux-gnu` target
7. **ArmSom RK3576 GPIO pins**: GPIO pin configuration for e-ink display is incomplete in `configs/armsom-rk3576.conf`
8. **Justfile architecture**: Default build architecture is `arm64`; specify `just build amd64` for cross-platform builds
9. **Model size**: Standard build is ~200MB; including Whisper adds ~300-500MB more via `just prepare whisper`
