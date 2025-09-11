# Hardware Modules

The Distiller CM5 SDK provides comprehensive Python interfaces for controlling hardware components
on the CM5 platform. All hardware modules follow consistent patterns with context manager support
and proper resource cleanup.

## Audio System

The audio module provides ALSA-based recording and playback with hardware volume control.

### Features

- Recording to file or streaming with callbacks
- Playback from files or raw audio streams
- Hardware volume and gain control
- Thread-safe operations
- Support for various audio formats

### Basic Usage

```python
from distiller_cm5_sdk.hardware.audio import Audio

# Initialize
audio = Audio()

# Configure system-wide settings
Audio.set_mic_gain_static(80)      # 0-100
Audio.set_speaker_volume_static(70) # 0-100

# Record to file
audio.record("output.wav", duration=5.0)  # 5 seconds

# Playback
audio.play("sound.wav")

# Stream recording with callback
def process_audio(data):
    print(f"Received {len(data)} bytes")

thread = audio.stream_record(callback=process_audio)
# ... do processing ...
audio.stop_recording()

# Cleanup
audio.close()
```

### Advanced Features

```python
# Stream playback with custom format
audio_data = b'...'  # Your raw audio
audio.stream_play(
    audio_data,
    format_type="S16_LE",
    sample_rate=16000,
    channels=1
)

# Check status
if audio.is_recording():
    print("Currently recording")

if audio.is_playing():
    print("Currently playing")
```

## E-ink Display

The E-ink module supports EPD128x250 (250×128) and EPD240x416 displays with comprehensive image
processing.

### Features

- Full and partial refresh modes
- Multiple image format support (PNG, JPEG, GIF, BMP, TIFF, WebP)
- Automatic scaling and dithering
- Text rendering and overlay
- Shape drawing primitives
- Hardware transformations (rotate, flip, invert)

### Display Configuration

```python
from distiller_cm5_sdk.hardware.eink import (
    Display, DisplayMode, FirmwareType,
    ScalingMethod, DitheringMethod,
    set_default_firmware
)

# Configure firmware (persists across sessions)
set_default_firmware(FirmwareType.EPD128x250)  # 250×128 display
# OR
set_default_firmware(FirmwareType.EPD240x416)  # 240×416 display

# Use display
with Display() as display:
    display.clear()
```

### Image Display

```python
with Display() as display:
    # Simple image display
    display.display_image("image.png", mode=DisplayMode.FULL)

    # With transformations
    display.display_image(
        "image.png",
        mode=DisplayMode.PARTIAL,  # Fast update
        rotate=90,                 # Rotation in degrees
        flip_horizontal=True,      # Mirror horizontally
        invert_colors=True         # Invert black/white
    )

    # Auto-conversion with scaling
    display.display_image_auto(
        "large_photo.jpg",
        mode=DisplayMode.FULL,
        scaling=ScalingMethod.LETTERBOX,  # Maintain aspect ratio
        dithering=DitheringMethod.FLOYD_STEINBERG  # High quality
    )
```

### Text and Graphics

```python
with Display() as display:
    # Render text
    buffer = display.render_text(
        "Hello World",
        x=10, y=20,
        scale=2,        # 2x size
        invert=False    # Black on white
    )
    display.display_image(buffer, mode=DisplayMode.FULL)

    # Draw shapes
    buffer = bytes([0x00] * display.ARRAY_SIZE)  # Black background
    buffer = display.draw_rect(
        buffer,
        x=10, y=10,
        width=50, height=30,
        filled=True,
        value=True  # White rectangle
    )
    display.display_image(buffer, mode=DisplayMode.FULL)
```

### Raw Data Transformations

```python
from distiller_cm5_sdk.hardware.eink import (
    rotate_bitpacked, flip_bitpacked_horizontal,
    invert_bitpacked_colors
)

# Transform 1-bit packed data
data = bytes([0xFF] * 4000)  # White screen
rotated = rotate_bitpacked(data, 90, 250, 128)
flipped = flip_bitpacked_horizontal(rotated, 128, 250)
inverted = invert_bitpacked_colors(flipped)
```

## Camera

The camera module uses rpicam-apps for image and video capture.

### Features

- Single image capture
- Video streaming with callbacks
- Camera settings adjustment
- NumPy array output
- File saving support

### Basic Usage

```python
from distiller_cm5_sdk.hardware.camera import Camera

camera = Camera()

# Capture image
image = camera.capture_image("photo.jpg")  # Saves and returns array
# OR
image = camera.capture_image()  # Returns array only

# Get single frame
frame = camera.get_frame()
print(f"Frame shape: {frame.shape}")

# Cleanup
camera.close()
```

### Video Streaming

```python
def process_frame(frame):
    # Process each frame
    height, width, channels = frame.shape
    print(f"Frame: {width}x{height}")
    # Add your processing here

# Start streaming
camera.start_stream(callback=process_frame)

# Let it run...
import time
time.sleep(10)

# Stop streaming
camera.stop_stream()
```

### Camera Settings

```python
# Adjust settings
camera.adjust_setting("brightness", 50)
camera.adjust_setting("contrast", 75)

# Get current value
brightness = camera.get_setting("brightness")

# List available settings
settings = camera.get_available_settings()
for setting in settings:
    print(f"Setting: {setting}")
```

## RGB LED Control

The LED module controls RGB LEDs via the sysfs interface.

### Features

- Individual LED control
- Batch control for all LEDs
- RGB color setting
- Brightness adjustment
- State queries

### Basic Usage

```python
from distiller_cm5_sdk.hardware.sam import LED

led = LED(use_sudo=True)  # May need sudo for sysfs

# Control individual LED
led.set_rgb_color(led_id=0, red=255, green=0, blue=0)  # Red
led.set_brightness(led_id=0, brightness=128)  # 50% brightness
led.turn_off(led_id=0)

# Control all LEDs
led.set_color_all(red=0, green=255, blue=0)  # All green
led.set_brightness_all(200)
led.turn_off_all()
```

### LED Patterns

```python
import time

# Breathing effect
for i in range(3):  # 3 cycles
    # Fade in
    for brightness in range(0, 256, 5):
        led.set_brightness(led_id=0, brightness=brightness)
        time.sleep(0.02)
    # Fade out
    for brightness in range(255, -1, -5):
        led.set_brightness(led_id=0, brightness=brightness)
        time.sleep(0.02)

# Color cycle
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # R, G, B
for r, g, b in colors:
    led.set_rgb_color(led_id=0, red=r, green=g, blue=b)
    time.sleep(1)
```

### Query LED State

```python
# Get current color
red, green, blue = led.get_rgb_color(led_id=0)
print(f"LED 0: RGB({red}, {green}, {blue})")

# Get brightness
brightness = led.get_brightness(led_id=0)
print(f"Brightness: {brightness}/255")

# List available LEDs
leds = led.get_available_leds()
print(f"Available LEDs: {leds}")
```

## Hardware Manager Pattern

Coordinate multiple hardware components efficiently:

```python
from distiller_cm5_sdk.hardware.audio import Audio
from distiller_cm5_sdk.hardware.camera import Camera
from distiller_cm5_sdk.hardware.eink import Display, DisplayMode
from distiller_cm5_sdk.hardware.sam import LED

class HardwareManager:
    def __init__(self):
        self.audio = None
        self.camera = None
        self.display = None
        self.led = None

    def initialize(self):
        """Initialize all hardware."""
        try:
            self.audio = Audio()
            self.camera = Camera()
            self.display = Display()
            self.led = LED(use_sudo=True)
            return True
        except Exception as e:
            print(f"Init failed: {e}")
            return False

    def capture_and_display(self):
        """Capture photo and show on E-ink display."""
        if self.camera and self.display:
            # Capture
            image = self.camera.capture_image("/tmp/photo.png")

            # Display with auto-conversion
            self.display.display_png_auto(
                "/tmp/photo.png",
                mode=DisplayMode.FULL,
                scaling=ScalingMethod.LETTERBOX
            )

            # Success indicator
            if self.led:
                self.led.set_rgb_color(0, 0, 255, 0)  # Green

    def record_and_show_status(self, duration=5):
        """Record audio and show status on display."""
        if self.audio and self.display:
            # Show recording status
            self.display.clear()
            text = self.display.render_text("Recording...", 10, 10, 2)
            self.display.display_image(text, DisplayMode.FULL)

            # Record
            self.audio.record("/tmp/recording.wav", duration)

            # Show complete
            self.display.clear()
            text = self.display.render_text("Complete!", 10, 10, 2)
            self.display.display_image(text, DisplayMode.FULL)

    def cleanup(self):
        """Clean up all resources."""
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
    try:
        manager.capture_and_display()
        manager.record_and_show_status()
    finally:
        manager.cleanup()
```

## Hardware Testing

Test individual hardware components:

```bash
# Audio test
python -m distiller_cm5_sdk.hardware.audio._audio_test

# Camera test
python -m distiller_cm5_sdk.hardware.camera._camera_unit_test

# E-ink display test
python -m distiller_cm5_sdk.hardware.eink._display_test
```

## Important Notes

### Permissions

- Ensure your user is in the required groups: `audio`, `video`, `spi`, `gpio`, `i2c`
- LED control may require sudo access unless sysfs permissions are configured

### Resource Management

- Always use context managers (`with` statements) when available
- Call `close()` or `cleanup()` methods to free resources
- Hardware resources are limited - avoid multiple simultaneous instances

### Thread Safety

- Audio recording/playback operations are thread-safe
- Camera streaming uses separate threads for callbacks
- LED operations are atomic but not locked

## Next Steps

- [AI Modules](AI-Modules) - Speech recognition and synthesis
- [API Reference](API-Reference) - Complete API documentation
- [Troubleshooting](Troubleshooting) - Common hardware issues
