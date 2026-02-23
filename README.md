# Distiller SDK

Python SDK for the Distiller platform (Raspberry Pi CM5, Radxa Zero 3/3W, ArmSom CM5 IO), providing hardware control,
audio processing, computer vision, and AI capabilities using **uv** package management.

> **Breaking change in 4.0.0**: Speech processing (Parakeet ASR, Piper TTS, Whisper) has been removed from the SDK.
> Speech is now available as Claude Code skills in `distiller-cc >= 6.0.0`.
> Run `/ai-speech-recognition` or `/ai-text-to-speech` in Claude Code to set up and use speech features.

## Quick Start

### Prerequisites

- **Python 3.11+** (automatically installed with package)
- **ARM64 Linux system** (Raspberry Pi CM5, Radxa Zero 3/3W, ArmSom CM5 IO [Experimental - E-ink incomplete])
- **uv package manager** (auto-installed during setup)

### Installation

```bash
# Clone and build
git clone https://github.com/pamir-ai-pkgs/distiller-sdk.git
cd distiller-sdk
chmod +x build.sh

# Build Rust library and package
./build.sh                    # Build Rust e-ink library
just build                    # Build Debian package

# Install
sudo dpkg -i dist/distiller-sdk_*_arm64.deb
sudo apt-get install -f       # Install missing dependencies

# Verify
source /opt/distiller-sdk/activate.sh
python -c "import distiller_sdk; print('SDK imported successfully!')"
```

## Package Structure

```text
/opt/distiller-sdk/
├── src/distiller_sdk/    # Python SDK modules
│   └── hardware/         # Hardware control (audio, camera, e-ink, LED)
├── lib/                  # Native libraries (e-ink display)
├── .venv/                # Virtual environment (uv-managed)
└── activate.sh           # Environment activation
```

## Integration

For dependent projects and services, integrate the SDK by setting up the environment properly:

```bash
# Method 1: Environment Variables
export PYTHONPATH="/opt/distiller-sdk:$PYTHONPATH"
export LD_LIBRARY_PATH="/opt/distiller-sdk/lib:$LD_LIBRARY_PATH"
source /opt/distiller-sdk/.venv/bin/activate

# Method 2: In Python
import sys
sys.path.insert(0, '/opt/distiller-sdk')
```

## Development

### Package Management with uv

```bash
cd /opt/distiller-sdk
source activate.sh

# Package operations
uv add <package>         # Add new package
uv remove <package>      # Remove package
uv sync                  # Update packages
uv tree                  # Show dependencies
```

### Build from Source

```bash
# Build Rust library
./build.sh

# Build Debian package
just build
just clean               # Clean artifacts
```

## SDK Modules

### Audio System

```python
from distiller_sdk.hardware.audio import Audio

# Initialize
audio = Audio()

# Configure system-wide settings
Audio.set_mic_gain_static(80)      # 0-100
Audio.set_speaker_volume_static(70) # 0-100

# Recording to file
audio.record("output.wav", duration=5.0)  # Record for 5 seconds
# OR without duration (manual stop required)
audio.record("output.wav")
audio.stop_recording()

# Streaming recording with callback
def audio_callback(data):
    print(f"Received {len(data)} bytes")

thread = audio.stream_record(callback=audio_callback, buffer_size=4096)
# ... do something ...
audio.stop_recording()

# Playback from file
audio.play("sound.wav")

# Stream playback
audio_data = b'...'  # Your audio data
audio.stream_play(audio_data,
      format_type="S16_LE",
      sample_rate=16000,
      channels=1)

# Volume control
audio.set_mic_gain(85)  # Instance method
audio.set_speaker_volume(60)
gain = audio.get_mic_gain()
volume = audio.get_speaker_volume()

# Status checks
is_recording = audio.is_recording()
is_playing = audio.is_playing()

# Cleanup
audio.close()
```

### E-ink Display

250×128 landscape e-ink display with intelligent image conversion. Supports PNG, JPEG, GIF, BMP, TIFF, and WebP.

```python
from distiller_sdk.hardware.eink import Display, DisplayMode, ScalingMethod, DitheringMethod

with Display() as display:
    # Display any image — automatically scaled, dithered, and oriented
    display.display_image_auto("photo.jpg")

    # Display text
    display.display_text("Hello!", x=10, y=10, scale=3)

    # Clear the display
    display.clear()

    # Fast refresh for status updates
    display.display_image_auto("status.png", mode=DisplayMode.FAST)

    # 4-level grayscale (EPD128x250 only)
    display.display_grayscale("photo.jpg")
```

#### display_image_auto() — Primary Display Method

```python
display.display_image_auto(
    image,                                    # File path (str) or raw 1-bit data (bytes)
    mode=DisplayMode.FULL,                    # FULL, PARTIAL, FAST, TURBO, or GRAYSCALE_4
    scaling=ScalingMethod.LETTERBOX,          # LETTERBOX, CROP_CENTER, or STRETCH
    dithering=DitheringMethod.FLOYD_STEINBERG,# FLOYD_STEINBERG, THRESHOLD, or ORDERED
    invert_colors=False,                      # Swap black/white
)
```

| Parameter | Options | Description |
|-----------|---------|-------------|
| `image` | `str` or `bytes` | File path (any supported format) or raw 1-bit packed data |
| `mode` | `FULL` / `PARTIAL` / `FAST` / `TURBO` / `GRAYSCALE_4` | Refresh mode — FULL (quality), PARTIAL (fast), FAST (~1.5s), TURBO (~1s), GRAYSCALE_4 (4-level gray, EPD128x250 only) |
| `scaling` | `LETTERBOX` / `CROP_CENTER` / `STRETCH` | How to fit image to display dimensions |
| `dithering` | `FLOYD_STEINBERG` / `THRESHOLD` / `ORDERED` | Dithering algorithm for 1-bit conversion |
| `invert_colors` | `bool` | Swap black and white |

#### Text Rendering

```python
with Display() as display:
    # High-level: render and display text in one call
    display.display_text("Hello World", x=10, y=10, scale=2)

    # Low-level: compose multiple elements into a buffer
    buffer = display.render_text("Title", x=10, y=10, scale=2)
    buffer = display.overlay_text(buffer, "Subtitle", x=10, y=30, scale=1)
    buffer = display.draw_rect(buffer, x=5, y=5, width=240, height=50, filled=False, value=False)
    display.display_image_auto(buffer)
```

#### Other Methods

- `clear()` — Clear display to white
- `sleep()` — Low-power sleep mode
- `close()` — Release hardware resources
- `get_dimensions()` — Returns `(250, 128)` (width, height)
- `convert_png_to_raw(filepath)` — Convert PNG to raw 1-bit packed data
- `is_initialized()` — Check if hardware is ready
- `set_partial_base_map(image)` — Set base map for partial refresh (prevents ghosting by writing to both RAM buffers)
- `display_grayscale(filename, scaling, invert)` — Display with 4-level grayscale (`scaling` takes strings: `"letterbox"`, `"crop"`, `"stretch"`)

#### Enums

```python
from distiller_sdk.hardware.eink import DisplayMode, ScalingMethod, DitheringMethod

DisplayMode.FULL              # Slow, high quality refresh
DisplayMode.PARTIAL           # Fast updates, possible ghosting
DisplayMode.FAST              # Fast refresh (~1.5s), temperature override
DisplayMode.TURBO             # Turbo refresh (~1s), fastest
DisplayMode.GRAYSCALE_4       # 4-level grayscale (EPD128x250 only)

ScalingMethod.LETTERBOX       # Maintain aspect ratio, black borders (default)
ScalingMethod.CROP_CENTER     # Fill display, center crop
ScalingMethod.STRETCH         # Stretch to fill (may distort)

DitheringMethod.FLOYD_STEINBERG  # High quality (default)
DitheringMethod.THRESHOLD        # Fast binary threshold
DitheringMethod.ORDERED          # Ordered dithering
```

#### Composer Module

The `composer` submodule provides image processing utilities:

- **dithering**: Floyd-Steinberg and ordered dithering algorithms
- **image_ops**: Image scaling, cropping, and format conversion
- **text**: Text rendering with font support
- **template_renderer**: Template-based layout rendering

### Camera

rpicam-apps-based image capture with OpenCV processing for Raspberry Pi OS Bookworm and later.

```python
from distiller_sdk.hardware.camera import Camera

camera = Camera()

# Capture image (saves to file if filepath provided)
image = camera.capture_image("photo.jpg")
# OR without filepath (returns numpy array only)
image = camera.capture_image()

# Get single frame
frame = camera.get_frame()

# Stream processing with callback
def frame_callback(frame):
    print(f"Frame shape: {frame.shape}")
    # Process frame

camera.start_stream(callback=frame_callback)
# ... do something ...
camera.stop_stream()

# Adjust settings
camera.adjust_setting("brightness", 50)
setting_value = camera.get_setting("brightness")
available = camera.get_available_settings()

# Cleanup
camera.close()
```

### LED Control

Full RGB LED control with animation modes, Linux LED triggers, and timing control.

```python
from distiller_sdk.hardware.sam import LED
import time

led = LED(use_sudo=True)  # May need sudo for sysfs access

# Basic control (per-LED)
led.set_rgb_color(led_id=0, red=255, green=0, blue=0)  # Red
led.set_brightness(led_id=0, brightness=128)  # 0-255
led.turn_off(led_id=0)

# Get current state
red, green, blue = led.get_rgb_color(led_id=0)
brightness = led.get_brightness(led_id=0)

# Control all LEDs
led.set_color_all(red=0, green=255, blue=0)  # All green
led.set_brightness_all(200)  # 0-255
led.turn_off_all()

# Animation modes (kernel-based looping, hardware-accelerated)
led.blink_led(led_id=0, red=255, green=0, blue=0, timing=500)  # Blink red at 500ms
led.fade_led(led_id=0, red=0, green=255, blue=0, timing=1000)  # Fade green at 1000ms
led.rainbow_led(led_id=0, timing=800)  # Rainbow cycle at 800ms

# Stop animation by returning to static mode
led.set_rgb_color(led_id=0, red=0, green=0, blue=0)  # Returns to static mode
led.turn_off(led_id=0)  # Or turn off completely

# Linux LED triggers (hardware-accelerated effects)
led.set_trigger(0, "heartbeat-rgb")    # Heartbeat pattern
led.set_trigger(0, "breathing-rgb")    # Breathing effect
led.set_trigger(0, "none")             # Disable trigger

# Get available triggers
triggers = led.get_available_triggers(0)
current_trigger = led.get_trigger(0)

# Custom animation timing control
led.blink_led(led_id=0, red=255, green=255, blue=0, timing=200)  # Fast yellow blink
led.fade_led(led_id=1, red=0, green=0, blue=255, timing=2000)    # Slow blue fade

# Get available LEDs
available = led.get_available_leds()  # Returns list of LED IDs
```

### Hardware Manager Pattern

```python
from distiller_sdk.hardware.audio import Audio
from distiller_sdk.hardware.camera import Camera
from distiller_sdk.hardware.eink import Display, DisplayMode
from distiller_sdk.hardware.sam import LED

class HardwareManager:
    """Coordinate multiple hardware components."""

    def __init__(self):
        self.audio = None
        self.camera = None
        self.display = None
        self.led = None

    def initialize(self):
        """Initialize available hardware."""
        try:
            self.display = Display()
            self.camera = Camera()
            self.audio = Audio()
            self.led = LED(use_sudo=True)  # May need sudo for sysfs access
            return True
        except Exception as e:
            print(f"Hardware init failed: {e}")
            return False

    def capture_and_display(self):
        """Capture image and show on display."""
        if self.camera and self.display:
            if self.led:
                # Blink blue during capture
                self.led.blink_led(led_id=0, red=0, green=0, blue=255, timing=300)

            # Capture and save image
            image = self.camera.capture_image("/tmp/capture.png")
            # Display on e-ink using auto-conversion
            self.display.display_image_auto("/tmp/capture.png", mode=DisplayMode.FULL)

            if self.led:
                # Return to static mode and show solid green for success
                self.led.set_rgb_color(led_id=0, red=0, green=255, blue=0)

    def cleanup(self):
        """Clean up resources."""
        if self.display:
            self.display.clear()
        if self.led:
            self.led.turn_off_all()  # Turn off all LEDs
        if self.camera:
            self.camera.close()
        if self.audio:
            self.audio.close()

# Usage
manager = HardwareManager()
if manager.initialize():
    manager.capture_and_display()
    manager.cleanup()
```

## Build & Deployment

### Build Process

```bash
./build.sh             # Build Rust e-ink library
just build             # Build .deb package
just clean && just build  # Clean rebuild
```

### Installation

```bash
sudo dpkg -i dist/distiller-sdk_*_arm64.deb
sudo apt-get install -f  # Fix dependencies
```

## Troubleshooting

### Common Issues

**1. Import Errors**

```bash
# Fix Python path
export PYTHONPATH="/opt/distiller-sdk:$PYTHONPATH"
source /opt/distiller-sdk/activate.sh
```

**2. Audio Issues**

```bash
# Check devices
aplay -l
arecord -l

# Test audio
speaker-test -t wav -c 2

# Fix permissions
sudo usermod -a -G audio $USER
```

**3. Camera Not Found**

```bash
# Check camera
ls -la /dev/video*
v4l2-ctl --list-devices

# Fix permissions
sudo usermod -a -G video $USER
```

**4. E-ink Display Issues**

```bash
# Check SPI
ls -la /dev/spi*
lsmod | grep spi

# Test configuration
python -c "from distiller_sdk.hardware.eink import Display; d = Display(); print(f'Display OK: {d.get_dimensions()}')"

# Set firmware via environment
export DISTILLER_EINK_FIRMWARE=EPD128x250
```

**5. Library Loading Errors**

```bash
# Update library cache
sudo ldconfig

# Check library
ldd /opt/distiller-sdk/lib/libdistiller_display_sdk_shared.so
```

**6. Permission Denied**

```bash
# Add user to required groups
sudo usermod -a -G audio,video,spi,gpio,i2c $USER
# Logout and login again
```

### Debug Commands

```bash
# Check SDK installation
dpkg -L distiller-sdk

# Verify imports
python -c "from distiller_sdk.hardware.audio import Audio; from distiller_sdk.hardware.camera import Camera; from distiller_sdk.hardware.eink import Display; from distiller_sdk.hardware.sam import LED; print('All imports successful!')"

# Test hardware
python -m distiller_sdk.hardware.audio._audio_test
python -m distiller_sdk.hardware.camera._camera_unit_test
python -m distiller_sdk.hardware.eink._display_test
```

## System Requirements

### Hardware

- **Platform**: Raspberry Pi CM5, Radxa Zero 3/3W, ArmSom CM5 IO (experimental), or compatible ARM64 system
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 2GB for full installation with models
- **Peripherals**: E-ink display (SPI), Camera (V4L2), Audio (ALSA)

### Software

- **OS**: ARM64 Linux (Debian/Ubuntu based)
- **Python**: 3.11 or higher
- **Libraries**: ALSA, V4L2, SPI support
- **Groups**: audio, video, spi, gpio, i2c

## Platform Information

- **Supported Platforms**: Raspberry Pi CM5, Radxa Zero 3/3W, ArmSom CM5 IO (experimental - e-ink incomplete)
- **Python**: 3.11+
- **Package Manager**: uv (latest)
- **Architecture**: ARM64
- **License**: See LICENSE file

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature-name`
6. Create pull request

## Support

- **Documentation**: See module READMEs in `src/distiller_sdk/`
- **Issues**: [GitHub Issues](https://github.com/pamir-ai-pkgs/distiller-sdk/issues)
- **Wiki**: [GitHub Wiki](https://github.com/pamir-ai-pkgs/distiller-sdk/wiki)

## License

See LICENSE file for details.
