# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Distiller SDK - Python SDK for the Distiller platform providing hardware control for e-ink displays, audio I/O, camera, LED control, and AI capabilities (ASR/TTS) using uv package management. Built as a Debian package targeting ARM64 Linux systems (Raspberry Pi CM5, Radxa Zero 3/3W, ArmSom CM5 IO).

**Important Context**: This is a sub-project within a larger Google Repo-based multi-repository structure (parent: `/home/utsav/dev/pamir-ai/`). Git operations work normally within this directory, but the `.git` is a symlink to `.repo/projects/distiller-sdk.git`. See parent repo's CLAUDE.md for multi-repo commands.

## Quick Reference

```bash
# Most common development commands
just setup                    # Install dependencies (first time setup)
just lint                     # Check code quality
just fix                      # Auto-fix formatting
./build.sh                    # Download models and build Rust library
just build                    # Build Debian package
just verify                   # Verify installed package works

# Testing individual modules (requires hardware)
python -m distiller_sdk.hardware.audio._audio_test
python -m distiller_sdk.hardware.camera._camera_unit_test
python -m distiller_sdk.hardware.eink._display_test

# Quick sanity checks
python -c "import distiller_sdk; print('SDK imported successfully!')"
source /opt/distiller-sdk/activate.sh  # After dpkg -i installation
```

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

### Build Process Flow
Understanding what happens during the build:

1. **`./build.sh`** (Preparation phase):
   - Downloads Parakeet ASR models from HuggingFace (~150MB)
   - Downloads Piper TTS models and binary from GitHub releases (~50MB)
   - Optionally downloads Whisper models if `--whisper` flag used (~300-500MB)
   - Builds Rust e-ink library (`libdistiller_display_sdk_shared.so`) for ARM64
   - Places models in `src/distiller_sdk/parakeet/models/`, `src/distiller_sdk/piper/models/`, etc.

2. **`just build`** (Package creation phase):
   - Calls `./build.sh` automatically (via `prepare` recipe)
   - Runs `debuild` to create Debian package
   - Copies all Python source, models, and Rust library into package
   - Runs lintian checks for Debian policy compliance
   - Outputs `.deb` package to `dist/` directory

3. **`sudo dpkg -i`** (Installation phase):
   - Extracts package to `/opt/distiller-sdk/`
   - Runs `debian/postinst` script which:
     - Detects platform (CM5, Radxa, etc.)
     - Creates uv virtual environment at `/opt/distiller-sdk/.venv`
     - Installs Python dependencies via `uv sync`
     - Sets up platform-specific e-ink config
     - Verifies hardware devices are present
     - Generates `activate.sh` script

**Key insight**: Models and Rust library are downloaded/built ONCE during `./build.sh`, then packaged into the `.deb`. The installed package at `/opt/distiller-sdk` is self-contained with its own venv.

## Development Setup

There are two modes of development:
1. **Local development** - Using local `.venv` for quick iteration on Python code
2. **Package testing** - Testing the installed Debian package at `/opt/distiller-sdk`

### Local Development (Recommended for Python changes)
```bash
# Initial setup (creates .venv via uv sync)
just setup
source .venv/bin/activate     # Activate virtual environment

# Code quality checks
just lint                     # Run ruff check + format check + mypy
just fix                      # Auto-fix formatting issues

# Development workflow for quick iteration
# 1. Edit Python code in src/distiller_sdk/
# 2. Test immediately (no rebuild needed - changes take effect immediately)
python -m distiller_sdk.hardware.eink._display_test
python -m distiller_sdk.hardware.audio._audio_test

# When done with changes
just lint                     # Check code quality before building
just build                    # Build Debian package
```

### Testing Installed Package
```bash
# After installing with: sudo dpkg -i dist/distiller-sdk_*_arm64.deb
source /opt/distiller-sdk/activate.sh

# Or set up Python path manually
export PYTHONPATH="/opt/distiller-sdk:$PYTHONPATH"
export LD_LIBRARY_PATH="/opt/distiller-sdk/lib:$LD_LIBRARY_PATH"

# Verify installation
just verify                   # Quick import check
python -c "import distiller_sdk; print('SDK imported successfully!')"
```

## Testing

### Quick Import Tests (No hardware required)
```bash
# Sanity check - verify imports work
python -c "import distiller_sdk; print('SDK imported successfully!')"

# Test all major module imports
python -c "from distiller_sdk.hardware.audio import Audio; from distiller_sdk.hardware.camera import Camera; from distiller_sdk.hardware.eink import Display; from distiller_sdk.parakeet import Parakeet; from distiller_sdk.piper import Piper; print('All imports successful!')"

# After dpkg installation
source /opt/distiller-sdk/activate.sh
just verify  # Convenience command for import check
```

### Hardware Module Tests (Requires physical hardware)
```bash
# These tests require actual Distiller hardware
python -m distiller_sdk.hardware.audio._audio_test      # Audio I/O test
python -m distiller_sdk.hardware.camera._camera_unit_test  # Camera test
python -m distiller_sdk.hardware.eink._display_test     # E-ink display test
python -m distiller_sdk.hardware.sam.led_interactive_demo  # LED control demo

# Note: These tests will fail gracefully with error messages if hardware is not present
```

### Comprehensive Test Suite
For the full test suite with 66+ test cases, use the `distiller-test-harness` repository:
```bash
cd ../distiller-test-harness
just setup                             # Install test dependencies
just test                              # Run all tests (verbose)
just test-quick                        # Skip slow and hardware tests
uv run pytest -m hardware              # Hardware-only tests
uv run pytest sdk_tests/test_audio.py  # Specific module tests
```

## Dependency Management

### Adding/Removing Python Dependencies
```bash
# Add a new dependency (updates pyproject.toml and uv.lock)
uv add <package-name>

# Add development dependency
uv add --dev <package-name>

# Remove a dependency
uv remove <package-name>

# Update dependencies to latest compatible versions
uv sync

# Show dependency tree
uv tree

# After modifying dependencies, update Debian control file if needed
# Edit debian/control to add system-level dependencies
```

### Important Dependency Notes
- Python dependencies are managed in `pyproject.toml`
- System-level dependencies (ALSA, V4L2, etc.) are in `debian/control`
- The SDK installation creates a uv-managed venv at `/opt/distiller-sdk/.venv`
- Some dependencies require system libraries (e.g., pyaudio needs portaudio19-dev)

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
│   │   ├── audio.py             # Main Audio class (ALSA interface)
│   │   └── _audio_test.py       # Hardware test script
│   ├── camera/        # V4L2 camera capture (OpenCV)
│   │   ├── camera.py            # Main Camera class (V4L2 interface)
│   │   └── _camera_unit_test.py # Hardware test script
│   ├── eink/          # E-ink display control via ctypes to Rust library
│   │   ├── display.py           # Main Display class (ctypes bindings)
│   │   ├── _display_test.py     # Hardware test script
│   │   ├── lib/                 # Rust library source
│   │   │   ├── src/             # Rust source code
│   │   │   ├── Cargo.toml       # Rust dependencies
│   │   │   ├── Makefile.rust    # Rust build system
│   │   │   └── libdistiller_display_sdk_shared.so  # Built library
│   │   └── composer/            # Image processing utilities
│   │       ├── dithering.py     # Floyd-Steinberg, ordered dithering
│   │       ├── image_ops.py     # Image scaling, cropping
│   │       ├── text.py          # Text rendering on e-ink
│   │       └── template_renderer.py  # Template-based rendering
│   └── sam/           # LED control via sysfs GPIO
│       ├── led.py               # Main LED class (sysfs interface with animations)
│       └── led_interactive_demo.py  # Interactive demo
├── parakeet/          # ASR engine (sherpa-onnx) with VAD
│   ├── parakeet.py              # Main Parakeet class
│   └── models/                  # ONNX models (downloaded by build.sh)
├── piper/             # TTS engine (Piper)
│   ├── piper.py                 # Main Piper class
│   ├── models/                  # Voice models (downloaded by build.sh)
│   └── piper/                   # Piper binary and libs
└── whisper/           # Optional Whisper ASR (faster-whisper)
    ├── whisper.py               # Main Whisper class
    └── models/                  # Whisper models (optional download)

configs/                # Platform-specific hardware configs
├── cm5.conf                     # Raspberry Pi CM5 settings
├── radxa-zero3.conf            # Radxa Zero 3/3W settings
└── armsom-rk3576.conf          # ArmSom CM5 IO settings

debian/                 # Debian packaging files
├── platform-detect.sh          # Multi-platform detection helper
├── postinst                    # Post-installation script
├── control                     # Package metadata and dependencies
├── rules                       # debuild build rules
└── changelog                   # Version history
```

**Key Files to Know**:
- `build.sh`: Downloads AI models and builds Rust library
- `Justfile`: Build automation (setup, build, lint, clean, changelog)
- `pyproject.toml`: Python package metadata, dependencies, version
- `debian/platform-detect.sh`: Platform detection logic (sourced by postinst)
- `debian/postinst`: Critical installation script that sets up uv venv and platform config

### Platform Detection System
Multi-platform support via `platform-detect.sh` helper script:
- **Raspberry Pi CM5** (BCM2712): `/dev/spidev0.0`, `/dev/gpiochip0`, GPIO pins: dc=7, rst=13, busy=9
- **Radxa Zero 3/3W** (RK3566): `/dev/spidev3.0`, `/dev/gpiochip3`, GPIO pins: dc=8, rst=2, busy=1
- **ArmSom CM5 IO** (RK3576) [Experimental - E-ink incomplete]: `/dev/spidev3.0`, `/dev/gpiochip4`, GPIO pins: TBD (dc/rst/busy pins not configured)
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
- **Firmware types**:
  - **EPD128x250**: Physical 250×128 landscape (default mounting), vendor controller expects 128×250 portrait data; SDK transforms landscape → portrait for vendor
  - **EPD240x416**: 240×416 (dimensions match physical orientation)
- **Critical**: EPD128x250 vendor controller requires 128×250 portrait data despite physical 250×128 landscape mounting; sending 250×128 directly causes byte alignment issues
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

### LED System
sysfs-based RGB LED control with kernel-driven animations:
- **Basic control**: Per-LED RGB color setting, brightness control (0-255)
- **Animation modes**: Kernel-based looping animations (static, blink, fade, rainbow) with timing control (100/200/500/1000ms)
- **Linux LED triggers**: Hardware-accelerated system-driven effects (heartbeat-rgb, breathing-rgb, rainbow-rgb)
- **Multi-LED support**: Control individual LEDs or all LEDs simultaneously
- **Hardware-accelerated**: Animations loop continuously in kernel driver, no Python threading

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

### Package Dependencies
**This package is the foundation dependency** for other Distiller packages:
- `distiller-services` (WiFi provisioning) depends on `distiller-sdk >= 3.0.0`
- `distiller-telemetry` (device registration) depends on `distiller-sdk >= 3.0.0`
- `distiller-test-harness` (test suite) depends on `distiller-sdk >= 3.0.0`

**Important**: When bumping SDK version, dependent packages may need updates to their Debian control files if the API changes. The `>= 3.0.0` constraint allows for compatible minor/patch updates.

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
All hardware modules raise custom exceptions (`DisplayError`, `LEDError`, etc.) for error conditions. Always handle hardware initialization failures gracefully as devices may not be present.

### LED Animation Management
LED animations use kernel-based looping (hardware-accelerated, no Python threading):
```python
# Set animation mode (loops continuously in kernel driver)
led.blink_led(led_id=0, red=255, green=0, blue=0, timing=500)
led.fade_led(led_id=1, red=0, green=255, blue=0, timing=1000)
led.rainbow_led(led_id=2, timing=1000)

# Or use animation mode directly
led.set_animation_mode(led_id=0, mode="blink", timing=500)  # Modes: static, blink, fade, rainbow

# Use Linux LED triggers for system-driven effects
led.set_trigger(led_id=0, trigger="heartbeat-rgb")  # Triggers: heartbeat-rgb, breathing-rgb, rainbow-rgb

# Stop animation by setting to static mode
led.set_rgb_color(led_id=0, red=0, green=0, blue=0)  # Returns to static mode

# Turn off all LEDs
led.turn_off_all()
```

### Transformation Chaining
For e-ink display transformations, note that dimensions swap after 90/270° rotations:
```python
# For EPD128x250: physical 250×128 landscape (default), vendor expects 128×250 portrait
# Users create content in landscape, SDK transforms to portrait for vendor controller
# Example showing dimension swap after rotation
result = flip_bitpacked_vertical(
    rotate_bitpacked_ccw_90(data, 128, 250),
    250, 128  # Dimensions swapped after 90° rotation
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
The e-ink display functionality is implemented in Rust and exposed to Python via ctypes.

**Important**: The Rust library is automatically built during `./build.sh` execution. You typically don't need to build it manually unless modifying the Rust code.

```bash
cd src/distiller_sdk/hardware/eink/lib

# Check if rebuild needed
make -f Makefile.rust check-rebuild

# Build library manually (if modifying Rust code)
make -f Makefile.rust build

# Clean build artifacts
make -f Makefile.rust clean

# Show target info
make -f Makefile.rust target-info

# After rebuilding Rust library, test the changes
cd ../../../..  # Back to SDK root
python -m distiller_sdk.hardware.eink._display_test
```

**Rust Library Location**: `src/distiller_sdk/hardware/eink/lib/`
- Source code: `src/` directory (Rust)
- Build output: `libdistiller_display_sdk_shared.so` (copied to package `lib/` during install)
- Python bindings: `src/distiller_sdk/hardware/eink/display.py` (ctypes interface)

## Development Workflows

### Quick Python-only Changes
For changes to Python code only (no Rust library changes):
```bash
# 1. Make changes to Python files in src/distiller_sdk/
# 2. Test immediately (no build needed)
source .venv/bin/activate
python -m distiller_sdk.hardware.audio._audio_test

# 3. When ready to package
just lint                          # Check code quality
just build                         # Build Debian package
```

### Changes Involving Rust Library
For changes to the Rust e-ink library:
```bash
# 1. Make changes to Rust code in src/distiller_sdk/hardware/eink/lib/src/
# 2. Rebuild Rust library
cd src/distiller_sdk/hardware/eink/lib
make -f Makefile.rust build
cd ../../../..

# 3. Test changes
python -m distiller_sdk.hardware.eink._display_test

# 4. When ready, rebuild full package
./build.sh                         # Downloads models and builds Rust library
just build                         # Build Debian package
```

### Adding New Hardware Platform Support
To add support for a new platform (e.g., new SBC):
```bash
# 1. Create config file
cp configs/cm5.conf configs/new-platform.conf
# Edit configs/new-platform.conf with correct SPI/GPIO settings

# 2. Update platform detection
# Edit debian/platform-detect.sh:
#   - Add new platform to validate_platform() function
#   - Add detection logic to detect_platform() function
#   - Add config mapping to get_config_file() function
#   - Add hardware descriptions to get_spi_device(), get_gpio_chip(), etc.

# 3. Test platform detection
source debian/platform-detect.sh
detect_platform
get_platform_description new-platform

# 4. Update documentation in CLAUDE.md and README.md
```

### Version Bumping and Release
```bash
# 1. Update version in pyproject.toml
# Edit version = "3.2.0" -> "3.3.0"

# 2. Update Debian changelog
just changelog                     # Opens editor with dch -i
# Add meaningful changelog entry

# 3. Build and test
just clean
./build.sh
just build
sudo dpkg -i dist/distiller-sdk_*_arm64.deb
just verify                        # Verify installation

# 4. Commit and tag (within this repo)
git add pyproject.toml debian/changelog
git commit -m "chore: bump version to 3.3.0"
git tag v3.3.0
git push && git push --tags
```

## Common Pitfalls

1. **EPD128x250 dimension specification**: The display is physically mounted as 250×128 landscape (default orientation), but the vendor controller expects 128×250 portrait data due to firmware logic. Users create content in landscape (250×128), and the SDK automatically transforms it to portrait (128×250) for the vendor. Sending 250×128 directly causes byte alignment issues and garbled output. This is a vendor controller quirk, not an error.
2. **Platform detection during build**: Armbian builds must detect platform via kernel patterns in `/lib/modules/` before `/etc/armbian-release` exists
3. **uv installation**: `postinst` script handles multiple uv installation paths via PATH export including root/user `.local/bin` and `.cargo/bin`
4. **Audio permissions**: Recording/playback requires user in `audio` group
5. **SPI/GPIO access**: E-ink display requires SPI enabled in device tree and proper GPIO permissions
6. **Rust build dependencies**: E-ink library build requires Rust toolchain with `aarch64-unknown-linux-gnu` target
7. **ArmSom RK3576 GPIO pins**: GPIO pin configuration for e-ink display is incomplete in `configs/armsom-rk3576.conf`
8. **Justfile architecture**: Default build architecture is `arm64`; specify `just build amd64` for cross-platform builds
9. **Model size**: Standard build is ~200MB; including Whisper adds ~300-500MB more via `just prepare whisper`
10. **Rust library not in Python path**: When testing locally, ensure `LD_LIBRARY_PATH` includes the Rust library location
11. **Model files not downloaded**: Run `./build.sh` before first build to download AI models from HuggingFace
