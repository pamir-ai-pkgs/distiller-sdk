# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Distiller SDK - Python SDK for the Distiller platform providing hardware control for e-ink displays, audio I/O, camera, and LED control using uv package management. Built as a Debian package targeting ARM64 Linux systems (Raspberry Pi CM5, Radxa Zero 3/3W, ArmSom CM5 IO).

**Important Context**: This is a sub-project within a larger Google Repo-based multi-repository structure (parent: `/home/utsav/dev/pamir-ai/`). Git operations work normally within this directory, but the `.git` is a symlink to `.repo/projects/distiller-sdk.git`. See parent repo's CLAUDE.md for multi-repo commands.

## Quick Reference

```bash
# Setup and quality
just setup                    # Install dependencies (creates .venv via uv sync)
just lint                     # Run ruff check + format check + mypy
just fix                      # Auto-fix formatting issues

# Build pipeline (run in order)
./build.sh                    # Build Rust e-ink library
./build.sh --skip-rust        # Skip Rust library build
just build                    # Build Debian package (calls ./build.sh, then debuild)
just build amd64              # Cross-build for amd64
just clean                    # Clean all build artifacts

# Install and verify
sudo dpkg -i dist/distiller-sdk_*_arm64.deb
source /opt/distiller-sdk/activate.sh
just verify                   # Quick import check

# Hardware module tests (require physical hardware)
python -m distiller_sdk.hardware.audio._audio_test
python -m distiller_sdk.hardware.camera._camera_unit_test
python -m distiller_sdk.hardware.eink._display_test
python -m distiller_sdk.hardware.eink._diagnostic_test
python -m distiller_sdk.hardware.eink._interactive_mode_test
python -m distiller_sdk.hardware.sam.led_interactive_demo
python -m distiller_sdk.hardware.eink.composer.cli  # E-ink composition CLI

# Comprehensive test suite (separate repo)
cd ../distiller-test-harness && just setup && just test-quick
```

### Build Process Flow

1. **`./build.sh`** (Preparation): Builds Rust e-ink library (`libdistiller_display_sdk_shared.so`) for ARM64.

2. **`just build`** (Packaging): Calls `./build.sh` via `prepare` recipe, runs `debuild` with lintian checks, outputs `.deb` to `dist/`.

3. **`sudo dpkg -i`** (Installation): Extracts to `/opt/distiller-sdk/`, runs `debian/postinst` which detects platform, creates uv venv, installs Python deps, sets up e-ink config, verifies hardware, and generates `activate.sh`.

**Key insight**: Rust library is built ONCE during `./build.sh`, then packaged into the `.deb`. The installed package is self-contained.

## Development Setup

Two modes of development:
1. **Local development** - Using local `.venv` for quick iteration (no rebuild needed for Python changes)
2. **Package testing** - Testing the installed Debian package at `/opt/distiller-sdk`

```bash
# Local development (recommended for Python changes)
just setup && source .venv/bin/activate
# Edit code in src/distiller_sdk/, test immediately, then:
just lint && just build

# Testing installed package
source /opt/distiller-sdk/activate.sh
# Or manually: export PYTHONPATH="/opt/distiller-sdk:$PYTHONPATH"
#              export LD_LIBRARY_PATH="/opt/distiller-sdk/lib:$LD_LIBRARY_PATH"

# Rust library changes (only needed when modifying Rust code)
cd src/distiller_sdk/hardware/eink/lib
make -f Makefile.rust build       # Rebuild library
cd ../../../..                    # Back to SDK root, then test
```

### Dependency Notes
- Python deps in `pyproject.toml`, system-level deps in `debian/control`
- `numpy>=1.26` required for grayscale image processing and ordered dithering
- Some deps require system libraries (e.g., pyaudio needs portaudio19-dev)
- After modifying Python deps, update `debian/control` if system-level deps change

## Architecture

### Path Resolution Strategy

The SDK's `__init__.py` provides dual-mode path resolution via one helper function:

- **`get_library_path()`**: Checks `/opt/distiller-sdk/lib` first, falls back to `hardware/eink/lib/` relative path. Used to locate the Rust shared library.

This means the same code works both during local development and after Debian package installation without any configuration.

### Public API Exports

```
distiller_sdk                    # get_library_path(), __version__
distiller_sdk.hardware           # (no __init__.py — import submodules directly)
distiller_sdk.hardware.eink      # Display, DisplayError, DisplayErrorCode, DisplayMode, ScalingMethod, DitheringMethod
distiller_sdk.hardware.audio     # Audio
distiller_sdk.hardware.camera    # Camera, CameraError
distiller_sdk.hardware.sam       # LED, LEDError, create_led_with_sudo
```

Note: `hardware/` has no `__init__.py` — you must import from specific submodules (e.g., `from distiller_sdk.hardware.eink import Display`).

### Module Structure
```
src/distiller_sdk/
├── __init__.py        # get_library_path(), __version__
├── hardware/          # Hardware abstraction layer (no __init__.py)
│   ├── audio/         # ALSA-based audio I/O with streaming
│   │   ├── audio.py             # Main Audio class (ALSA interface)
│   │   └── _audio_test.py       # Hardware test script
│   ├── camera/        # Camera capture via rpicam-apps CLI (rpicam-still)
│   │   ├── camera.py            # Main Camera class (subprocess to rpicam-still)
│   │   └── _camera_unit_test.py # Hardware test script
│   ├── eink/          # E-ink display control via ctypes to Rust library
│   │   ├── display.py           # Main Display class (ctypes FFI bindings)
│   │   ├── _display_test.py     # Hardware test script
│   │   ├── _diagnostic_test.py  # Interactive orientation diagnostics
│   │   ├── _interactive_mode_test.py  # Interactive demo for all display modes
│   │   ├── lib/                 # Rust library source
│   │   │   ├── src/             # Rust source code
│   │   │   ├── Cargo.toml       # Rust dependencies
│   │   │   ├── Makefile.rust    # Rust build system
│   │   │   └── libdistiller_display_sdk_shared.so  # Built library
│   │   └── composer/            # Image processing utilities
│   │       ├── cli.py           # eink-compose CLI tool
│   │       ├── dithering.py     # Floyd-Steinberg, ordered dithering
│   │       ├── image_ops.py     # Image scaling, cropping
│   │       ├── text.py          # Text rendering on e-ink
│   │       └── template_renderer.py  # Template-based rendering
│   └── sam/           # LED control via sysfs GPIO
│       ├── led.py               # Main LED class (sysfs interface with animations)
│       └── led_interactive_demo.py  # Interactive demo

configs/                # Platform-specific hardware configs
├── cm5.conf                     # Raspberry Pi CM5 settings
├── radxa-zero3.conf            # Radxa Zero 3/3W settings
└── armsom-rk3576.conf          # ArmSom CM5 IO settings
```

**Key Files to Know**:
- `build.sh`: Builds Rust e-ink library
- `Justfile`: Build automation (setup, build, lint, clean, changelog)
- `pyproject.toml`: Python package metadata, dependencies, version
- `debian/platform-detect.sh`: Platform detection logic (sourced by postinst)
- `debian/postinst`: Critical installation script that sets up uv venv and platform config

### Platform Detection System
Multi-platform support via `platform-detect.sh` helper script:
- **Raspberry Pi CM5** (BCM2712): `/dev/spidev0.0`, `/dev/gpiochip0`, GPIO pins: dc=7, rst=13, busy=9
- **Radxa Zero 3/3W** (RK3566): `/dev/spidev3.0`, `/dev/gpiochip3`, GPIO pins: dc=8, rst=2, busy=1
- **ArmSom CM5 IO** (RK3576) [Experimental]: `/dev/spidev3.0`, `/dev/gpiochip4`, GPIO pins: TBD (incomplete)
- **Armbian** builds: Kernel pattern detection via `/lib/modules/` patterns
- Override with `DISTILLER_PLATFORM=cm5|radxa|armsom-rk3576|armbian` environment variable

Detection priority: 1) `DISTILLER_PLATFORM` env var → 2) Armbian detection (`/etc/armbian-release`, kernel patterns) → 3) Device tree (`/proc/device-tree/compatible`) → 4) "unknown"

To add a new platform: create `configs/<platform>.conf`, update `debian/platform-detect.sh` (add to `validate_platform()`, `detect_platform()`, `get_config_file()`, and hardware description functions), then update docs.

### E-ink Display Architecture
The display system uses ctypes bindings to a Rust-compiled shared library (`libdistiller_display_sdk_shared.so`):
- **Firmware types**:
  - **EPD128x250**: Physical 250x128 landscape (default mounting), vendor controller expects 128x250 portrait data; SDK transforms landscape to portrait for vendor
  - **EPD240x416**: 240x416 (dimensions match physical orientation)
- **Display modes**: Full (standard), Partial (fast), Fast (~1.5s, temp override at 100C), Turbo (~1s, temp override at 90C, dual RAM), Grayscale4 (4-level gray via dual RAM LUT, EPD128x250 only)
- **Critical**: EPD128x250 vendor controller requires 128x250 portrait data despite physical 250x128 landscape mounting; sending 250x128 directly causes byte alignment issues
- **Configuration priority**: 1) `DISTILLER_EINK_FIRMWARE` env var, 2) config files, 3) default EPD128x250
- **Image processing**: Supports PNG/JPEG/GIF/BMP/TIFF/WebP with auto-scaling, dithering (Floyd-Steinberg, threshold, ordered), and transformations
- **Grayscale support**: GRAYSCALE_4 is EPD128x250 only; uses `numpy>=1.26` for ordered dithering to 4 gray levels
- **Partial refresh base map**: `set_partial_base_map()` writes to both RAM buffers to prevent ghosting accumulation
- **Bitpacking**: 1-bit packed data with standalone transformation functions for rotation/flipping
- **Composer submodule**: Template rendering, text overlay, shape drawing; CLI via `python -m distiller_sdk.hardware.eink.composer.cli`

#### FFI Binding Pattern
`display.py` uses `_setup_function_signatures()` to define ctypes interfaces to 16 Rust FFI functions. Each function gets explicit `restype` and `argtypes` for type safety:

```python
# Example pattern from _setup_function_signatures():
self._lib.display_init.restype = c_bool
self._lib.display_init.argtypes = []
self._lib.display_image_raw.restype = c_bool
self._lib.display_image_raw.argtypes = [POINTER(c_ubyte), c_int]
```

Functions covered: `display_init`, `display_image_raw`, `display_image_auto`, `display_clear`, `display_sleep`, `display_cleanup`, `display_set_partial_base_map`, `display_get_dimensions`, `convert_png_to_1bit`, `image_invert_1bit`, `image_dither`, `image_process`, `text_render`, `text_overlay`, `shape_draw_rect_filled`, `display_init_logger` (optional).

The Rust library is in `src/distiller_sdk/hardware/eink/lib/`, built via `Makefile.rust` for `aarch64-unknown-linux-gnu`, auto-rebuilt when `.rs` files, `Cargo.toml`, or `Cargo.lock` change.

### Camera System
Camera capture via `rpicam-apps` CLI tools (specifically `rpicam-still`) using subprocess calls:
- **NOT direct V4L2/OpenCV** — the Camera class invokes `rpicam-still` as a subprocess
- OpenCV (`cv2`) used only for post-capture image reading and format conversion (BGR/RGB/grayscale)
- Settings adjustment via OpenCV `CAP_PROP_*` has limited effect with rpicam-still capture
- Single frame capture or continuous streaming via repeated subprocess calls
- Requires `rpicam-still` binary (checked at init with `shutil.which`)

### Audio System
ALSA-based audio with both file and streaming operations:
- **Static vs instance methods**: `set_mic_gain_static()` for system-wide, `set_mic_gain()` for instance
- **Recording modes**: File recording, streaming with callback
- **Playback**: Direct file playback or stream playback with format control
- Thread-safe recording state management

### LED System
sysfs-based RGB LED control with kernel-driven animations:
- **Basic control**: Per-LED RGB color setting, brightness control (0-255)
- **Animation modes**: Kernel-based looping animations (static, blink, fade, rainbow) with timing control (100/200/500/1000ms)
- **Linux LED triggers**: Hardware-accelerated system-driven effects (heartbeat-rgb, breathing-rgb, rainbow-rgb)
- **Multi-LED support**: Control individual LEDs or all LEDs simultaneously
- **Hardware-accelerated**: Animations loop continuously in kernel driver, no Python threading

## Debian Packaging

### Package Build System
- Uses `debuild` with lintian profile for compliance checking
- Target architecture: `just build arm64` (default) or `just build amd64`
- Platform-agnostic single package; Provides/Replaces/Breaks `distiller-cm5-sdk` for v2.x migration
- **Foundation dependency**: `distiller-services`, `distiller-telemetry`, `distiller-test-harness` all require `distiller-sdk >= 3.0.0`

### Post-installation Flow (`debian/postinst`)
1. Remove legacy `/opt/distiller-cm5-sdk/` installation if present
2. Detect platform using `debian/platform-detect.sh` helper functions
3. Copy platform-specific config to `/opt/distiller-sdk/eink.conf`
4. Create uv virtual environment with `--system-site-packages` (fallback to regular venv)
5. Run `uv sync --frozen --no-editable --compile-bytecode` for production install
6. Set file permissions and ownership (`distiller:distiller`, readable by all, executables in `.venv/bin`)
7. Verify Python environment and SDK imports
8. Check for required devices (SPI, GPIO) and warn if missing
9. Update `ldconfig` cache for shared libraries

### Installation Layout
All files install to `/opt/distiller-sdk/`:
- Python source in `src/distiller_sdk/`
- Native libraries in `lib/` (Rust e-ink library)
- Virtual environment in `.venv/` (created during postinst)
- Activation script: `activate.sh` (generated during postinst)
- Platform configs in `configs/`
- File ownership: `distiller:distiller` user/group

## Important Patterns

### Hardware Manager Pattern
When coordinating multiple hardware components, use a manager class to initialize, coordinate, and cleanup resources. See README.md Hardware Manager Pattern example.

### Context Manager Usage
Display class supports context manager for automatic cleanup:
```python
with Display() as display:
    display.display_image_auto("image.png", mode=DisplayMode.FULL)
# Automatically cleaned up
```

### Error Handling
All hardware modules raise custom exceptions (`DisplayError`, `LEDError`, `CameraError`, etc.) for error conditions. Always handle hardware initialization failures gracefully as devices may not be present.

### LED Animation Management
LED animations use kernel-based looping (hardware-accelerated, no Python threading):
```python
led.blink_led(led_id=0, red=255, green=0, blue=0, timing=500)
led.fade_led(led_id=1, red=0, green=255, blue=0, timing=1000)
led.rainbow_led(led_id=2, timing=1000)
led.set_animation_mode(led_id=0, mode="blink", timing=500)  # static, blink, fade, rainbow
led.set_trigger(led_id=0, trigger="heartbeat-rgb")  # heartbeat-rgb, breathing-rgb, rainbow-rgb
led.set_rgb_color(led_id=0, red=0, green=0, blue=0)  # Returns to static mode
led.turn_off_all()
```

### E-ink Display
The EPD128x250 landscape-to-portrait conversion is handled automatically by the Rust layer in `display_image_raw()`. Users pass 250x128 landscape images to `display_image_auto()` — no manual rotation needed.

## Development Notes

- **Target platform**: ARM64 only, but builds can run on x86_64 for Debian package creation
- **Python version**: 3.11+ required (managed by uv)
- **Ruff config**: Line length 100, target Python 3.11
- **Hardware access**: May require sudo or user groups (audio, video, spi, gpio, i2c)
- **Version bumping**: Edit `pyproject.toml` version, run `just changelog` (dch -i), then build and tag

## Common Pitfalls

1. **EPD128x250 dimension specification**: The display is physically mounted as 250x128 landscape, but the vendor controller expects 128x250 portrait data. Users create content in landscape (250x128), and the SDK transforms it automatically. Sending 250x128 directly causes byte alignment issues and garbled output.
2. **Platform detection during build**: Armbian builds must detect platform via kernel patterns in `/lib/modules/` before `/etc/armbian-release` exists
3. **uv installation**: `postinst` handles multiple uv installation paths via PATH export including root/user `.local/bin` and `.cargo/bin`
4. **Audio permissions**: Recording/playback requires user in `audio` group
5. **SPI/GPIO access**: E-ink display requires SPI enabled in device tree and proper GPIO permissions
6. **Rust build dependencies**: E-ink library build requires Rust toolchain with `aarch64-unknown-linux-gnu` target
7. **ArmSom RK3576 GPIO pins**: GPIO pin configuration for e-ink display is incomplete in `configs/armsom-rk3576.conf`
8. **Justfile architecture**: Default build architecture is `arm64`; specify `just build amd64` for cross-platform builds
9. **Rust library not in Python path**: When testing locally, ensure `LD_LIBRARY_PATH` includes the Rust library location
10. **GRAYSCALE_4 file-path-only**: `display_image_auto()` with `GRAYSCALE_4` mode only works with file paths, not raw bytes — raises `DisplayError` if raw bytes are passed
11. **GRAYSCALE_4 EPD128x250-only**: 4-level grayscale is only supported on the EPD128x250 firmware; EPD240x416 returns `UNSUPPORTED_MODE` error (-10)
12. **Fast/Turbo software resets**: Fast and Turbo modes use software resets with temperature overrides (100C/90C); some ghosting is expected and acceptable for the speed gain
13. **numpy dependency**: `numpy>=1.26` is now a required dependency for grayscale image processing and ordered dithering
