# Distiller CM5 SDK

Python SDK for the Distiller CM5 platform, providing hardware control, audio processing, computer
vision, and AI capabilities using **uv** package management.

## Quick Start

### Prerequisites

- **Python 3.11+** (automatically installed with package)
- **ARM64 Linux system** (CM5 platform)
- **uv package manager** (auto-installed during setup)

### Installation

```bash
# Clone and build
git clone https://github.com/Pamir-AI/distiller-cm5-sdk.git
cd distiller-cm5-sdk
chmod +x build.sh build-deb.sh

# Download models and build package
./build.sh                    # Download models (excluding Whisper)
./build-deb.sh               # Build Debian package

# Install
sudo dpkg -i dist/distiller-cm5-sdk_*_arm64.deb
sudo apt-get install -f       # Install missing dependencies

# Verify
source /opt/distiller-cm5-sdk/activate.sh
python -c "import distiller_cm5_sdk; print('SDK imported successfully!')"
```

## Package Structure

```text
/opt/distiller-cm5-sdk/
├── distiller_cm5_sdk/    # Python SDK modules
│   ├── hardware/         # Hardware control
│   ├── parakeet/        # ASR + VAD
│   ├── piper/           # TTS engine
│   └── whisper/         # Whisper ASR (optional)
├── models/              # AI model files
├── lib/                 # Native libraries
├── .venv/                # Virtual environment (uv-managed)
└── activate.sh          # Environment activation
```

## Integration

For dependent projects and services, integrate the SDK by setting up the environment properly:

```bash
# Method 1: Environment Variables
export PYTHONPATH="/opt/distiller-cm5-sdk:$PYTHONPATH"
export LD_LIBRARY_PATH="/opt/distiller-cm5-sdk/lib:$LD_LIBRARY_PATH"
source /opt/distiller-cm5-sdk/.venv/bin/activate

# Method 2: In Python
import sys
sys.path.insert(0, '/opt/distiller-cm5-sdk')
```

## Development

### Package Management with uv

```bash
cd /opt/distiller-cm5-sdk
source activate.sh

# Package operations
uv add <package>         # Add new package
uv remove <package>      # Remove package
uv sync                  # Update packages
uv tree                  # Show dependencies
```

### Build from Source

```bash
# Download models
./build.sh               # Standard models
./build.sh --whisper     # Include Whisper

# Build Debian package
./build-deb.sh          # Standard build
./build-deb.sh clean    # Clean rebuild
./build-deb.sh whisper  # Include Whisper
```

## SDK Modules

### Audio System

```python
from distiller_cm5_sdk.hardware.audio import Audio

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

Supports EPD128x250 (250×128 pixels) and EPD240x416 (240×416 pixels) displays with comprehensive
image processing capabilities.

**Note**: The EPD128x250 firmware name follows internal convention but actually represents a 250×128
(width×height) display.

#### Configuration

```python
from distiller_cm5_sdk.hardware.eink import (
    Display, DisplayMode, FirmwareType,
    ScalingMethod, DitheringMethod, TransformType,
    set_default_firmware, get_default_firmware
)

# Configure firmware type (persists across sessions)
set_default_firmware(FirmwareType.EPD240x416)  # 240×416 display
set_default_firmware(FirmwareType.EPD128x250)  # 250×128 display (default)
current_fw = get_default_firmware()

# Configuration priority:
# 1. Environment: DISTILLER_EINK_FIRMWARE=EPD240x416
# 2. Config files: /opt/distiller-cm5-sdk/eink.conf
# 3. Default: EPD128x250
```

#### Basic Display Operations

```python
with Display() as display:
    # Simple PNG display (must match display dimensions)
    display.display_image("image.png", mode=DisplayMode.FULL)

    # Display with transformations
    display.display_image(
        "image.png",
        mode=DisplayMode.FULL,
        rotate=90,        # Rotation: 0, 90, 180, 270 degrees (or True for 90°)
        flip_horizontal=True,   # Mirror left-right
        flip_vertical=True,     # Mirror top-bottom
        invert_colors=True      # Invert black/white
    )

    # Display various image formats (JPEG, GIF, BMP, TIFF, WebP)
    display.display_image_file("photo.jpg", mode=DisplayMode.FULL)
    display.display_image_file("animation.gif", mode=DisplayMode.FULL)

    # Raw 1-bit data display with transformations
    raw_data = bytes([0xFF] * 4000)  # White screen
    display.display_image(
        raw_data,
        mode=DisplayMode.PARTIAL,  # Fast update mode
        rotate=180,             # Rotate 180 degrees
        flip_vertical=True,     # Flip vertically
        flip_horizontal=False,  # Don't flip horizontally
        invert_colors=False,    # Don't invert colors
        src_width=250,  # Required for raw data transformations
        src_height=128  # Required for raw data transformations
    )

    # Clear display
    display.clear()
```

#### Auto-Conversion with Scaling and Dithering

```python
# Display any image with automatic conversion
# supports PNG, JPEG, GIF, BMP, TIFF, WebP
display.display_image_auto(
    "large_photo.jpg",  # Any size, any supported format
    mode=DisplayMode.FULL,
    scaling=ScalingMethod.LETTERBOX,      # Maintain aspect ratio
    dithering=DitheringMethod.FLOYD_STEINBERG  # High quality
)

# PNG-specific auto-conversion with all transformation options
display.display_png_auto(
    "any_image.png",
    mode=DisplayMode.FULL,
    scaling=ScalingMethod.LETTERBOX,      # Maintain aspect ratio
    dithering=DitheringMethod.FLOYD_STEINBERG,  # High quality
    rotate=90,              # Rotation in degrees (0, 90, 180, 270)
    flip_horizontal=False,  # Horizontal flip
    flip_vertical=True,     # Vertical flip
    crop_x=None,           # Auto-center for CROP_CENTER
    crop_y=None            # Auto-center for CROP_CENTER
)

# Scaling methods:
# - LETTERBOX: Maintain aspect ratio, add borders
# - CROP_CENTER: Center crop to fill display
# - STRETCH: Stretch to fill (may distort)

# Dithering methods:
# - THRESHOLD: Fast binary conversion
# - FLOYD_STEINBERG: High quality error diffusion
# - ORDERED: Ordered dithering pattern
```

#### Text Rendering

```python
# Render text to display buffer
text_buffer = display.render_text(
    "Hello World",
    x=10, y=20,
    scale=2,        # 2x size
    invert=False    # Black text on white
)
display.display_image(text_buffer, mode=DisplayMode.FULL)

# Overlay text on existing image
image_buffer = display.convert_png_to_raw("background.png")
with_text = display.overlay_text(
    image_buffer,
    "Status: OK",
    x=5, y=5,
    scale=1,
    invert=True     # White text on image
)
display.display_image(with_text, mode=DisplayMode.FULL)
```

#### Shape Drawing

```python
# Create blank buffer
buffer = bytes([0x00] * display.ARRAY_SIZE)  # Black screen

# Draw rectangle
with_rect = display.draw_rect(
    buffer,
    x=10, y=10,
    width=50, height=30,
    filled=True,
    value=True      # White rectangle
)
display.display_image(with_rect, mode=DisplayMode.FULL)
```

#### Bitpacking Transformations (Standalone Functions)

```python
from distiller_cm5_sdk.hardware.eink import (
    rotate_bitpacked, rotate_bitpacked_ccw_90, rotate_bitpacked_cw_90,
    rotate_bitpacked_180, flip_bitpacked_horizontal, flip_bitpacked_vertical,
    invert_bitpacked_colors
)

# 1-bit packed data (250x128 display for EPD128x250)
data = bytes([0xAA] * 4000)  # Alternating pattern

# Rotation transformations
rotated_90_ccw = rotate_bitpacked(data, 90, 250, 128)  # Counter-clockwise
rotated_90_ccw = rotate_bitpacked_ccw_90(data, 250, 128)  # Same as above
rotated_90_cw = rotate_bitpacked_cw_90(data, 250, 128)  # Clockwise 90°
rotated_180 = rotate_bitpacked_180(data, 250, 128)  # 180° rotation

# Flip transformations
flipped_h = flip_bitpacked_horizontal(data, 250, 128)  # Mirror left-right
flipped_v = flip_bitpacked_vertical(data, 250, 128)  # Mirror top-bottom

# Color inversion
inverted = invert_bitpacked_colors(data)  # Swap black and white

# Chain transformations
result = flip_bitpacked_vertical(
    rotate_bitpacked_ccw_90(data, 250, 128),
    128, 250  # Note: dimensions swap after 90° rotation
)
```

### Camera

```python
from distiller_cm5_sdk.hardware.camera import Camera

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

```python
from distiller_cm5_sdk.hardware.sam import LED
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

# Breathing pattern example
for brightness in range(0, 256, 5):  # Breathing
    led.set_brightness(led_id=0, brightness=brightness)
    time.sleep(0.05)

# Get available LEDs
available = led.get_available_leds()  # Returns list of LED IDs
```

### Parakeet ASR (with VAD)

```python
from distiller_cm5_sdk.parakeet import Parakeet

# Initialize
asr = Parakeet()

# Push-to-talk recording and transcription
for text in asr.record_and_transcribe_ptt():
    print(f"Transcribed: {text}")

# Automatic recording with VAD (Voice Activity Detection)
for text in asr.auto_record_and_transcribe():
    print(f"Transcribed: {text}")

# Manual recording control
asr.start_recording()
# ... speak ...
audio_data = asr.stop_recording()

# Transcribe the recorded audio
for text in asr.transcribe_buffer(audio_data):
    print(f"Transcribed: {text}")

# Cleanup
asr.cleanup()
```

### Piper TTS

```python
from distiller_cm5_sdk.piper import Piper

# Initialize
tts = Piper()

# Stream speech directly to speakers
tts.speak_stream("Hello, world!", volume=50)

# Stream with specific sound card
tts.speak_stream("Hello", volume=30, sound_card_name="snd_pamir_ai_soundcard")

# Get WAV file (saves to current directory as output.wav)
wav_path = tts.get_wav_file_path("Hello, this is a test")
print(f"WAV file saved to: {wav_path}")

# List available voices
voices = tts.list_voices()
for voice in voices:
    print(f"Voice: {voice['name']}, Language: {voice['language']}")
# Note: Currently only 'en_US-amy-medium' is available
```

### Whisper ASR (Optional)

```python
from distiller_cm5_sdk.whisper import Whisper

# Initialize (requires models)
whisper = Whisper(model_size="base")

# Transcribe
text = whisper.transcribe_file("audio.wav")

# With options
result = whisper.transcribe_file(
    "audio.wav",
    language="en",
    task="transcribe"  # or "translate"
)
```

### Hardware Manager Pattern

```python
from distiller_cm5_sdk.hardware.audio import Audio
from distiller_cm5_sdk.hardware.camera import Camera
from distiller_cm5_sdk.hardware.eink import Display, DisplayMode
from distiller_cm5_sdk.hardware.sam import LED

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
            # Capture and save image
            image = self.camera.capture_image("/tmp/capture.png")
            # Display on e-ink using auto-conversion
            self.display.display_png_auto("/tmp/capture.png", DisplayMode.FULL)
            if self.led:
                # Set first LED to green for success
                self.led.set_rgb_color(led_id=0, red=0, green=255, blue=0)

    def cleanup(self):
        """Clean up resources."""
        if self.display:
            self.display.clear()
        if self.led:
            self.led.turn_off_all()
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

### Model Downloads

```bash
./build.sh              # Standard models (~200MB)
./build.sh --whisper    # Include Whisper (~500MB+)
```

### Package Build

```bash
./build-deb.sh         # Build .deb package
./build-deb.sh clean   # Clean rebuild
./build-deb.sh whisper # Include Whisper models
```

### Installation

```bash
sudo dpkg -i dist/distiller-cm5-sdk_*_arm64.deb
sudo apt-get install -f  # Fix dependencies
```

## Troubleshooting

### Common Issues

**1. Import Errors**

```bash
# Fix Python path
export PYTHONPATH="/opt/distiller-cm5-sdk:$PYTHONPATH"
source /opt/distiller-cm5-sdk/activate.sh
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
python -c "from distiller_cm5_sdk.hardware.eink import get_default_firmware; print(get_default_firmware())"

# Set firmware
export DISTILLER_EINK_FIRMWARE=EPD128x250
```

**5. Library Loading Errors**

```bash
# Update library cache
sudo ldconfig

# Check library
ldd /opt/distiller-cm5-sdk/lib/libdistiller_display_sdk_shared.so
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
dpkg -L distiller-cm5-sdk

# Verify imports
python -c "from distiller_cm5_sdk.hardware.audio import Audio; from distiller_cm5_sdk.hardware.camera import Camera; from distiller_cm5_sdk.hardware.eink import Display; from distiller_cm5_sdk.parakeet import Parakeet; from distiller_cm5_sdk.piper import Piper; print('All imports successful!')"

# Test hardware
python -m distiller_cm5_sdk.hardware.audio._audio_test
python -m distiller_cm5_sdk.hardware.camera._camera_unit_test
python -m distiller_cm5_sdk.hardware.eink._display_test
```

## System Requirements

### Hardware

- **Platform**: Raspberry Pi CM5 or compatible ARM64 system
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 2GB for full installation with models
- **Peripherals**: E-ink display (SPI), Camera (V4L2), Audio (ALSA)

### Software

- **OS**: ARM64 Linux (Debian/Ubuntu based)
- **Python**: 3.11 or higher
- **Libraries**: ALSA, V4L2, SPI support
- **Groups**: audio, video, spi, gpio, i2c

## Version Information

- **SDK Version**: 2.0.0
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

- **Documentation**: See module READMEs in `src/distiller_cm5_sdk/`
- **Issues**: [GitHub Issues](https://github.com/Pamir-AI/distiller-cm5-sdk/issues)
- **Wiki**: [GitHub Wiki](https://github.com/Pamir-AI/distiller-cm5-sdk/wiki)

## License

See LICENSE file for details.
