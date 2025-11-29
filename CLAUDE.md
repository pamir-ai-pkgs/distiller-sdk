# CLAUDE.md - Distiller SDK

Python SDK for Distiller hardware: e-ink display, audio I/O, camera, LED control, ASR/TTS.
**Version**: 3.2.0 | **Platform**: ARM64 Linux | **Python**: 3.11+ | **Install**: `/opt/distiller-sdk/`

## Commands

| Task | Command |
|------|---------|
| Setup | `just setup` |
| Lint | `just lint` |
| Fix | `just fix` |
| Build | `./build.sh && just build` |
| Build (whisper) | `./build.sh --whisper && just build` |
| Clean | `just clean` |
| Verify install | `just verify` |
| Pre-commit hooks | `just setup-hooks` |

## Integration & Usage

### Using SDK in Dependent Projects

When integrating distiller-sdk into services or applications:

```bash
# Method 1: Activate script (recommended)
source /opt/distiller-sdk/activate.sh

# Method 2: Manual environment setup
export PYTHONPATH="/opt/distiller-sdk:$PYTHONPATH"
export LD_LIBRARY_PATH="/opt/distiller-sdk/lib:$LD_LIBRARY_PATH"
source /opt/distiller-sdk/.venv/bin/activate
```

### Utility Functions

```python
from distiller_sdk import get_model_path, get_library_path

# Get model path for AI modules
parakeet_models = get_model_path("parakeet")  # /opt/distiller-sdk/src/distiller_sdk/parakeet/models
piper_models = get_model_path("piper")
whisper_models = get_model_path("whisper")

# Get native library path
lib_path = get_library_path()  # /opt/distiller-sdk/lib (or lib/ in dev)
```

**Auto-detection**: Functions check for Debian package installation (`/opt/distiller-sdk`) first, then fall back to development paths.

### Verify Installation

```bash
# Import test
source /opt/distiller-sdk/activate.sh
python -c "import distiller_sdk; print('SDK OK')"

# Check version
python -c "import distiller_sdk; print(distiller_sdk.__version__)"

# Platform detection
/opt/distiller-sdk/platform-detect.sh
```

## Structure

```
src/distiller_sdk/
├── __init__.py                 # Version, get_model_path(), get_library_path()
├── exceptions.py               # Exception hierarchy (see Patterns section)
├── hardware_status.py          # HardwareStatus, HardwareState enums
├── hardware/
│   ├── audio/audio.py          # Audio class (ALSA)
│   ├── camera/camera.py        # Camera class (V4L2/OpenCV)
│   ├── eink/display.py         # Display class (Rust ctypes)
│   ├── eink/lib/               # Rust library source
│   └── sam/led.py              # LED class (sysfs)
├── parakeet/parakeet.py        # Parakeet ASR (sherpa-onnx)
├── piper/piper.py              # Piper TTS
└── whisper/fast_whisper.py     # Whisper ASR (optional)

configs/                        # Platform hardware configs
├── cm5.conf
└── myd-lr3576.conf

debian/
├── platform-detect.sh          # Platform detection helper
├── postinst                    # Installation script
└── control                     # Package metadata
```

## Hardware Modules

### Audio (`hardware/audio/audio.py`)

| Method | Description |
|--------|-------------|
| `record_to_file(path, duration)` | Record to WAV file |
| `play_file(path)` | Play audio file via aplay |
| `start_stream_recording(callback)` | Streaming record with callback |
| `stop_stream_recording()` | Stop streaming |
| `set_mic_gain(gain)` | Set mic gain 0-100 |
| `set_speaker_volume(vol)` | Set speaker volume 0-100 |
| `get_status()` | Returns HardwareStatus |

**Paths**: `/sys/devices/platform/axi/.../input_gain`, `/volume_level`
**Permissions**: Requires `audio` group

### Camera (`hardware/camera/camera.py`)

| Method | Description |
|--------|-------------|
| `capture_frame()` | Single frame capture |
| `start_streaming(callback)` | Continuous streaming |
| `stop_streaming()` | Stop streaming |
| `get_status()` | Returns HardwareStatus |

**Backend**: OpenCV (V4L2). **Recommends**: rpicam-apps on CM5

### E-ink Display (`hardware/eink/display.py`)

| Method | Description |
|--------|-------------|
| `display_image(path, mode)` | Display image (FULL/PARTIAL) |
| `display_buffer(data, width, height)` | Display raw buffer |
| `clear()` | Clear display |
| `get_status()` | Returns HardwareStatus |

**Firmware types**: EPD128x250 (default), EPD240x416
**Config priority**: `DISTILLER_EINK_FIRMWARE` env → config file → default
**Rust library**: `src/distiller_sdk/hardware/eink/lib/libdistiller_display_sdk_shared.so`

**CRITICAL - EPD128x250 dimensions**:
- Physical: 250×128 landscape (mounted orientation)
- Vendor expects: 128×250 portrait data
- SDK auto-transforms landscape → portrait
- Sending 250×128 directly causes byte alignment errors

### LED (`hardware/sam/led.py`)

| Method | Description |
|--------|-------------|
| `set_rgb_color(led_id, r, g, b)` | Set LED color |
| `blink_led(led_id, r, g, b, timing)` | Blink animation |
| `fade_led(led_id, r, g, b, timing)` | Fade animation |
| `rainbow_led(led_id, timing)` | Rainbow animation |
| `set_trigger(led_id, trigger)` | Linux LED trigger |
| `turn_off_all()` | Turn off all LEDs |
| `get_status()` | Returns HardwareStatus |

**Animation timing**: 100, 200, 500, 1000ms (kernel-driven, no Python threads)
**Triggers**: heartbeat-rgb, breathing-rgb, rainbow-rgb
**Path**: `/sys/class/leds/pamir:led*/`

## AI Modules

### Parakeet ASR (`parakeet/parakeet.py`)

| Method | Description |
|--------|-------------|
| `transcribe(audio_path)` | Transcribe file |
| `transcribe_buffer(data)` | Transcribe buffer |
| `start_recording()` | Push-to-talk start |
| `stop_recording()` | Push-to-talk stop → WAV bytes |
| `auto_record_and_transcribe()` | VAD-based auto-record |
| `get_status()` | Returns HardwareStatus |

**Backend**: sherpa-onnx | **Sample rate**: 16kHz mono | **Models**: `parakeet/models/`

### Piper TTS (`piper/piper.py`)

| Method | Description |
|--------|-------------|
| `get_wav_file_path(text)` | Generate WAV file |
| `speak_stream(text, volume)` | Stream playback (requires sudo) |
| `list_voices()` | List available voices |
| `get_status()` | Returns HardwareStatus |

**Voice**: en_US-amy-medium | **Binary**: `piper/piper/` | **Models**: `piper/models/`

### Whisper ASR (`whisper/fast_whisper.py`) - Optional

| Method | Description |
|--------|-------------|
| `transcribe(audio_path)` | Transcribe file |
| `transcribe_buffer(data)` | Transcribe buffer |
| `start_recording()` | Push-to-talk start |
| `stop_recording()` | Push-to-talk stop → WAV bytes |
| `get_status()` | Returns HardwareStatus |

**Backend**: faster-whisper | **Sample rate**: 48kHz mono | **Models**: `whisper/models/`
**Install**: `./build.sh --whisper` (adds ~300-500MB)

## Platform Support

| Platform | SPI Device | GPIO Chip | GPIO Pins (dc/rst/busy) | Config | Status |
|----------|------------|-----------|-------------------------|--------|--------|
| Raspberry Pi CM5 | `/dev/spidev0.0` | gpiochip0 | 7/13/9 | cm5.conf | ✓ Production |
| MYIR MYD-LR3576 | `/dev/spidev3.0` | gpiochip4 | TBD | myd-lr3576.conf | ⚠️ Hardware bringup |

**Detection priority**: `DISTILLER_PLATFORM` env → MYIR model string → device tree → "unknown"
**Override**: `export DISTILLER_PLATFORM=cm5|myd-lr3576`

**Platform detection script**: `/opt/distiller-sdk/platform-detect.sh`

Functions available:
- `detect_platform()` - Returns: cm5, myd-lr3576, unknown
- `get_spi_device(platform)` - Returns SPI device path
- `get_gpio_chip(platform)` - Returns GPIO chip path
- `get_gpio_pins(platform)` - Returns GPIO pin assignments
- `get_config_file(platform)` - Returns platform config path
- `get_platform_description(platform)` - Returns human-readable name

## Build System

### `./build.sh` (Preparation)
1. Downloads Parakeet ONNX models from HuggingFace (~150MB)
2. Downloads Piper binary + voice model (~50MB)
3. Optional: Downloads Whisper models with `--whisper` (~300-500MB)
4. Builds Rust e-ink library for ARM64

**Options**:
- `--whisper`: Include Whisper model downloads
- `--skip-rust`: Skip Rust library build (if already built)

### `just build` (Packaging)
1. Runs `./build.sh` via `prepare` recipe
2. Runs `debuild` to create Debian package
3. Outputs `.deb` to `dist/`

### Installation (`dpkg -i`)
1. Extracts to `/opt/distiller-sdk/`
2. Detects platform via `debian/platform-detect.sh`
3. Creates uv venv at `/opt/distiller-sdk/.venv`
4. Runs `uv sync --frozen --no-editable --compile-bytecode`
5. Generates `activate.sh`
6. Sets permissions (755 for dirs/binaries, 644 for .py files)
7. Sets ownership to `distiller:distiller`
8. Verifies Python and SDK imports
9. Checks platform-specific devices (SPI, GPIO)

### Dependencies & Integration

**Packages depending on distiller-sdk >= 3.0.0**:
- `distiller-services` - WiFi provisioning service
- `distiller-telemetry` - Device registration/telemetry
- `distiller-test-harness` - Test suite for SDK
- `distiller-agent-sdk` - Claude Agent SDK wrapper
- `device-diagnostics` - Health monitoring service

**Impact of SDK changes**: When modifying SDK APIs or exceptions, rebuild and test dependent packages:
```bash
cd distiller-sdk && just build
sudo dpkg -i dist/distiller-sdk_*.deb

cd ../distiller-services && just build
cd ../distiller-telemetry && just build
# Test that dependent packages still work
```

## Verification Commands

```bash
# SDK installation check
source /opt/distiller-sdk/activate.sh
python -c "import distiller_sdk; print('SDK OK')"

# Hardware availability check
python -c "
from distiller_sdk.hardware_status import HardwareStatus
s = HardwareStatus()
print(f'E-ink: {s.eink_available}')
print(f'Camera: {s.camera_available}')
print(f'LED: {s.led_available}')
print(f'Audio: {s.audio_available}')
"

# Platform detection
/opt/distiller-sdk/platform-detect.sh

# Check models
ls -la /opt/distiller-sdk/src/distiller_sdk/parakeet/models
ls -la /opt/distiller-sdk/src/distiller_sdk/piper/models
ls -la /opt/distiller-sdk/src/distiller_sdk/whisper/models  # If --whisper used

# Verify native library
ls -la /opt/distiller-sdk/lib/libdistiller_display_sdk_shared.so
ldd /opt/distiller-sdk/lib/libdistiller_display_sdk_shared.so

# Check device nodes
ls -la /dev/spidev*    # E-ink display (should show spidev)
ls -la /dev/gpiochip*  # GPIO (should show gpiochip)
ls -la /dev/video*     # Camera (should show video devices)

# Test audio devices
aplay -l               # Playback devices
arecord -l             # Capture devices
```

## Development Workflow

### Pre-commit Hooks Setup

Install pre-commit hooks to enforce code quality automatically:

```bash
just setup-hooks
```

**Hooks run on `git commit`**:
- Code formatting (ruff format)
- Linting (ruff check --fix)
- Type checking (mypy)
- File hygiene (trailing whitespace, EOF, YAML/JSON syntax)

**Manual validation**:
```bash
# Run all hooks on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff-format --all-files
uv run pre-commit run mypy --all-files
```

**Bypass hooks** (emergencies only): `git commit --no-verify`

### Local Development Cycle

```bash
# 1. Make changes to SDK code
vim src/distiller_sdk/hardware/audio/audio.py

# 2. Run code quality checks
just lint                    # ruff + mypy
just fix                     # Auto-fix formatting

# 3. Test changes locally
# Run module-specific tests:
python -m distiller_sdk.hardware.audio._audio_test
python -m distiller_sdk.hardware.camera._camera_unit_test
python -m distiller_sdk.hardware.eink._display_test
python -m distiller_sdk.hardware.sam.led_interactive_demo

# 4. Build and install locally
just build
sudo dpkg -i dist/distiller-sdk_*.deb

# 5. Test in dependent projects
cd ../distiller-services
just run  # Verify services still work

# 6. Commit changes (triggers pre-commit hooks)
git add .
git commit -m "feat: add new audio feature"
```

### Testing Strategy

```bash
# Individual module tests (in SDK repo)
python -m distiller_sdk.hardware.audio._audio_test
python -m distiller_sdk.hardware.camera._camera_unit_test
python -m distiller_sdk.hardware.eink._display_test
python -m distiller_sdk.hardware.sam.led_interactive_demo

# Full test suite (separate repo: distiller-test-harness)
cd ../distiller-test-harness && just test
cd ../distiller-test-harness && just test-quick  # Skip slow tests
```

## Patterns

### Context Manager Usage

**Always use context managers** for automatic cleanup:

```python
with Display() as display:
    display.display_image("image.png", mode=DisplayMode.FULL)
# Display automatically cleaned up

with Audio() as audio:
    audio.record("output.wav", duration=5)
# Audio resources released

with LED(use_sudo=True) as led:
    led.set_rgb_color(0, 255, 0, 0)
# LEDs turned off on exit
```

### Hardware Status Checking

Check hardware availability before use to avoid exceptions:

```python
from distiller_sdk.hardware_status import HardwareStatus

status = HardwareStatus()

# Quick boolean checks
if status.eink_available:
    from distiller_sdk.hardware.eink import Display
    with Display() as display:
        display.clear()
else:
    print("E-ink display not available")

# Detailed status information
from distiller_sdk.hardware.audio import Audio
audio_status = Audio.get_status()
if audio_status.available:
    print(f"Audio ready: {audio_status.message}")
    print(f"Capabilities: {audio_status.capabilities}")
else:
    print(f"Audio unavailable: {audio_status.message}")
    if audio_status.error:
        print(f"Error: {audio_status.error}")
```

**HardwareStatus attributes**:
- `state: HardwareState` - AVAILABLE, UNAVAILABLE, PERMISSION_DENIED, PARTIALLY_AVAILABLE
- `available: bool` - Quick check
- `capabilities: Dict[str, Any]` - Feature availability
- `error: Optional[Exception]` - Exception if detection failed
- `diagnostic_info: Dict[str, Any]` - Additional diagnostics
- `message: str` - Human-readable status

### Exception Handling

**Exception hierarchy**:
```
DistillerError (base)
├── HardwareError
│   ├── AudioError
│   ├── DisplayError
│   ├── CameraError
│   └── LEDError
├── AIError
│   ├── ParakeetError
│   ├── PiperError
│   └── WhisperError
├── ConfigurationError
└── ResourceError
```

**Pattern 1: Specific exception handling**
```python
from distiller_sdk.hardware.eink import Display, DisplayMode
from distiller_sdk.exceptions import DisplayError

try:
    with Display() as display:
        display.display_image("image.png", mode=DisplayMode.FULL)
except DisplayError as e:
    print(f"Display error: {e}")
except FileNotFoundError:
    print("Image file not found")
```

**Pattern 2: Hierarchical exception handling**
```python
from distiller_sdk.exceptions import HardwareError, AudioError, DistillerError

try:
    with Audio() as audio:
        audio.record("output.wav", duration=5)
except AudioError as e:
    print(f"Audio-specific error: {e}")
except HardwareError as e:
    print(f"Generic hardware error: {e}")
except DistillerError as e:
    print(f"SDK error: {e}")
```

**Pattern 3: Multi-module error handling**
```python
from distiller_sdk.parakeet import Parakeet
from distiller_sdk.piper import Piper
from distiller_sdk.exceptions import ParakeetError, PiperError, AIError

try:
    with Parakeet() as asr:
        for text in asr.transcribe("audio.wav"):
            print(f"Transcribed: {text}")
except ParakeetError as e:
    print(f"ASR error: {e}")

try:
    with Piper() as tts:
        tts.speak_stream("Hello world", volume=50)
except PiperError as e:
    print(f"TTS error: {e}")
```

### Multi-Hardware Coordination

Combine multiple hardware modules safely:

```python
from distiller_sdk.hardware_status import HardwareStatus
from distiller_sdk.hardware.camera import Camera
from distiller_sdk.hardware.eink import Display, DisplayMode
from distiller_sdk.hardware.sam import LED
from distiller_sdk.parakeet import Parakeet
from distiller_sdk.piper import Piper
from distiller_sdk.exceptions import HardwareError, AIError

# Check availability first
status = HardwareStatus()
if not (status.camera_available and status.eink_available):
    print("Required hardware not available")
    exit(1)

# Use context managers for all hardware
try:
    with Camera() as camera, \
         Display() as display, \
         LED(use_sudo=True) as led, \
         Parakeet() as asr, \
         Piper() as tts:

        # LED indicates activity
        led.blink_led(0, red=0, green=0, blue=255, timing=300)

        # Capture image
        image = camera.capture_image("/tmp/capture.png")

        # Display on e-ink
        display.display_png_auto("/tmp/capture.png", mode=DisplayMode.FULL)

        # Voice interaction
        tts.speak_stream("Say something", volume=50)
        for text in asr.record_and_transcribe_ptt():
            print(f"You said: {text}")
            tts.speak_stream(f"You said: {text}", volume=50)

        # Success indicator
        led.set_rgb_color(0, red=0, green=255, blue=0)

except HardwareError as e:
    print(f"Hardware error: {e}")
except AIError as e:
    print(f"AI module error: {e}")
# All resources automatically cleaned up
```

### LED Animations

Animations are kernel-driven (no Python threads). Set animation and it loops until changed:

```python
# Start animation (loops continuously)
led.blink_led(led_id=0, red=255, green=0, blue=0, timing=500)

# Animation runs in background...

# Stop animation by setting static color
led.set_rgb_color(led_id=0, red=0, green=0, blue=0)  # Returns to static mode

# Or turn off completely
led.turn_off(led_id=0)
```

**Thread safety**: All modules are thread-safe. Multiple instances can run concurrently without locking issues.

## Troubleshooting

### Environment Setup Issues

**Import errors**: `ModuleNotFoundError: No module named 'distiller_sdk'`
```bash
# Check PYTHONPATH
echo $PYTHONPATH  # Should include /opt/distiller-sdk

# Fix: Source activate script
source /opt/distiller-sdk/activate.sh

# Or set manually
export PYTHONPATH="/opt/distiller-sdk:$PYTHONPATH"
source /opt/distiller-sdk/.venv/bin/activate
```

**Library loading errors**: `OSError: libdistiller_display_sdk_shared.so: cannot open shared object file`
```bash
# Check LD_LIBRARY_PATH
echo $LD_LIBRARY_PATH  # Should include /opt/distiller-sdk/lib

# Fix: Update library path
export LD_LIBRARY_PATH="/opt/distiller-sdk/lib:$LD_LIBRARY_PATH"

# Or update system cache
sudo ldconfig

# Verify library
ldd /opt/distiller-sdk/lib/libdistiller_display_sdk_shared.so
```

**Permission denied**: `PermissionError: [Errno 13] Permission denied`
```bash
# Add user to required groups
sudo usermod -aG audio,video,spi,gpio,i2c $USER

# Logout and login for groups to take effect
# Verify group membership
groups
```

### Hardware Issues

**E-ink display not responding**:
```bash
# 1. Check SPI device
ls -la /dev/spidev*
# Expected: /dev/spidev0.0 (CM5) or /dev/spidev3.0 (MYD-LR3576)

# 2. Verify platform detection
/opt/distiller-sdk/platform-detect.sh
# Should return: cm5 or myd-lr3576

# 3. Check firmware configuration
python -c "from distiller_sdk.hardware.eink import get_default_firmware; print(get_default_firmware())"
# Should return: EPD128x250 or EPD240x416

# 4. Override firmware if needed
export DISTILLER_EINK_FIRMWARE=EPD128x250

# 5. Test display
python -m distiller_sdk.hardware.eink._display_test
```

**Garbled display output (EPD128x250)**:
- **Root cause**: Sending 250×128 data directly instead of letting SDK transform
- **Solution**: SDK auto-transforms landscape (250×128) → portrait (128×250) for vendor
- Don't manually rotate or transform - SDK handles it

**Audio recording/playback fails**:
```bash
# 1. Check audio devices
aplay -l    # Playback devices
arecord -l  # Capture devices

# 2. Test audio output
speaker-test -t wav -c 2

# 3. Verify user in audio group
groups | grep audio

# 4. Fix permissions
sudo usermod -aG audio $USER
# Logout and login

# 5. Check ALSA mixer
alsamixer
# Adjust volumes, ensure not muted
```

**Camera not found**:
```bash
# 1. Check camera device
ls -la /dev/video*
v4l2-ctl --list-devices

# 2. Verify user in video group
groups | grep video

# 3. Fix permissions
sudo usermod -aG video $USER

# 4. On Raspberry Pi CM5, check rpicam-apps
rpicam-still --list-cameras

# 5. Test camera
python -m distiller_sdk.hardware.camera._camera_unit_test
```

**LED control fails**:
```bash
# 1. Check LED sysfs interface
ls -la /sys/class/leds/pamir:led*

# 2. Try with sudo
python -c "
from distiller_sdk.hardware.sam import LED
with LED(use_sudo=True) as led:
    led.set_rgb_color(0, 255, 0, 0)
"

# 3. Add to sudoers (for passwordless LED control)
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/class/leds/*" | sudo tee /etc/sudoers.d/distiller-led
```

### Model & Build Issues

**Models not found**: `FileNotFoundError: [Errno 2] No such file or directory: '.../models'`
```bash
# 1. Check if models downloaded
ls -la /opt/distiller-sdk/src/distiller_sdk/parakeet/models
ls -la /opt/distiller-sdk/src/distiller_sdk/piper/models

# 2. If missing, rebuild with model download
cd distiller-sdk
./build.sh              # Standard models
./build.sh --whisper    # Include Whisper
just build
sudo dpkg -i dist/distiller-sdk_*.deb
```

**Rust library build fails**:
```bash
# 1. Check Rust toolchain
rustc --version
# If not installed:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup target add aarch64-unknown-linux-gnu

# 2. Rebuild library
cd src/distiller_sdk/hardware/eink/lib
make -f Makefile.rust build

# 3. Verify library built
ls -la libdistiller_display_sdk_shared.so
```

**Platform not detected**: Returns "unknown"
```bash
# 1. Check device tree
cat /proc/device-tree/model
cat /proc/device-tree/compatible

# 2. Override manually
export DISTILLER_PLATFORM=cm5  # or myd-lr3576

# 3. Verify override
/opt/distiller-sdk/platform-detect.sh
```

### Debugging Commands

```bash
# Check SDK package installation
dpkg -L distiller-sdk

# Verify imports
python -c "
from distiller_sdk.hardware.audio import Audio
from distiller_sdk.hardware.camera import Camera
from distiller_sdk.hardware.eink import Display
from distiller_sdk.parakeet import Parakeet
from distiller_sdk.piper import Piper
print('All imports successful!')
"

# Test hardware modules
python -m distiller_sdk.hardware.audio._audio_test
python -m distiller_sdk.hardware.camera._camera_unit_test
python -m distiller_sdk.hardware.eink._display_test
python -m distiller_sdk.hardware.sam.led_interactive_demo
```

## Rust Library Development

```bash
cd src/distiller_sdk/hardware/eink/lib
make -f Makefile.rust build    # Build for ARM64
make -f Makefile.rust clean    # Clean artifacts
```

**Target**: `aarch64-unknown-linux-gnu` | Auto-rebuilds when `.rs`, `Cargo.toml`, or `Cargo.lock` change.

**Cross-compilation setup**:
```bash
# Install ARM64 target
rustup target add aarch64-unknown-linux-gnu

# Build
cd src/distiller_sdk/hardware/eink/lib
cargo build --release --target aarch64-unknown-linux-gnu

# Output
ls -la target/aarch64-unknown-linux-gnu/release/libdistiller_display_sdk_shared.so
```
