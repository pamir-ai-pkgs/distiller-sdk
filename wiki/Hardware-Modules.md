# Hardware Modules

The Distiller SDK includes Python interfaces for controlling hardware components
on the Distiller platform (Raspberry Pi CM5, Radxa Zero 3/3W). All hardware modules follow
consistent patterns with context manager support and proper resource cleanup.

## Audio System

The audio module implements ALSA-based recording and playback with hardware volume control.

### Features

- Recording to file or streaming with callbacks
- Playback from files or raw audio streams
- Hardware volume and gain control
- Thread-safe operations
- Support for various audio formats

### Basic Usage

```python
from distiller_sdk.hardware.audio import Audio

# Configure system-wide settings
Audio.set_mic_gain_static(80)      # 0-100
Audio.set_speaker_volume_static(70) # 0-100

# Use context manager for automatic cleanup
with Audio() as audio:
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
# Automatic cleanup on exit
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

The E-ink module supports EPD128x250 (native: 128×250 portrait, mounted: 250×128 landscape) and
EPD240x416 displays with comprehensive image processing.

### Features

- Full and partial refresh modes
- Multiple image format support (PNG, JPEG, GIF, BMP, TIFF, WebP)
- Automatic scaling and dithering
- Text rendering and overlay
- Shape drawing primitives
- Hardware transformations (rotate, flip, invert)

### Display Configuration

```python
from distiller_sdk.hardware.eink import (
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
from distiller_sdk.hardware.eink import (
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
from distiller_sdk.hardware.camera import Camera

# Use context manager for automatic cleanup
with Camera() as camera:
    # Capture image
    image = camera.capture_image("photo.jpg")  # Saves and returns array
    # OR
    image = camera.capture_image()  # Returns array only

    # Get single frame
    frame = camera.get_frame()
    print(f"Frame shape: {frame.shape}")
# Automatic cleanup on exit
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
- Kernel-based animation modes (static, blink, fade, rainbow)
- Linux LED triggers (heartbeat-rgb, breathing-rgb, rainbow-rgb)
- Hardware-accelerated continuous looping
- State queries

### Basic Usage

```python
from distiller_sdk.hardware.sam import LED

# Use context manager for automatic LED turn-off
with LED(use_sudo=True) as led:
    # Control individual LED
    led.set_rgb_color(led_id=0, red=255, green=0, blue=0)  # Red
    led.set_brightness(led_id=0, brightness=128)  # 50% brightness
    led.turn_off(led_id=0)

    # Control all LEDs
    led.set_color_all(red=0, green=255, blue=0)  # All green
    led.set_brightness_all(200)
    led.turn_off_all()
# All LEDs automatically turned off on exit
```

### LED Animation Modes

Kernel-based animations loop continuously in hardware (no Python threads):

```python
# Animation modes (hardware-accelerated, continuous looping)
led.blink_led(led_id=0, red=255, green=0, blue=0, timing=500)   # Blink red
led.fade_led(led_id=1, red=0, green=255, blue=0, timing=1000)   # Fade green
led.rainbow_led(led_id=2, timing=800)                           # Rainbow cycle

# Or set animation mode directly
led.set_animation_mode(led_id=0, mode="blink", timing=500)
# Available modes: "static", "blink", "fade", "rainbow"
# Available timings: 100, 200, 500, 1000 (milliseconds)

# Note: Invalid timing values will raise LEDError
# led.blink_led(led_id=0, red=255, green=0, blue=0, timing=300)  # ERROR: Invalid timing

# Use Linux LED triggers for system-driven effects
led.set_trigger(led_id=0, trigger="heartbeat-rgb")  # Heartbeat pattern
led.set_trigger(led_id=1, trigger="breathing-rgb")  # Breathing effect
led.set_trigger(led_id=2, trigger="rainbow-rgb")    # Rainbow effect

# Return to static mode
led.set_rgb_color(led_id=0, red=255, green=255, blue=0)  # Yellow, static
led.turn_off(led_id=0)  # Or turn off
```

### Platform-Specific Notes

**ArmSom CM5 IO (RK3576)**:
- LED control fully supported via sysfs
- All animation modes and triggers work
- E-ink display GPIO pins incomplete (experimental platform)

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

Coordinate multiple hardware components efficiently using HardwareStatus and context managers:

```python
from distiller_sdk.hardware_status import HardwareStatus
from distiller_sdk.hardware.audio import Audio
from distiller_sdk.hardware.camera import Camera
from distiller_sdk.hardware.eink import Display, DisplayMode, ScalingMethod
from distiller_sdk.hardware.sam import LED

class HardwareManager:
    """Coordinate multiple hardware components with automatic detection and cleanup."""

    def __init__(self):
        # Check hardware availability
        self.status = HardwareStatus()

        if not self.status.audio_available:
            print("Warning: Audio hardware not available")

    def capture_and_display(self):
        """Capture photo and show on E-ink display."""
        # Use context managers for automatic cleanup
        with Camera() as camera if self.status.camera_available else None, \
             Display() as display if self.status.eink_available else None, \
             LED(use_sudo=True) as led if self.status.led_available else None:

            if camera and display:
                # Capture
                image = camera.capture_image("/tmp/photo.png")

                # Display with auto-conversion
                display.display_png_auto(
                    "/tmp/photo.png",
                    mode=DisplayMode.FULL,
                    scaling=ScalingMethod.LETTERBOX
                )

                # Success indicator
                if led:
                    led.set_rgb_color(0, 0, 255, 0)  # Green
            elif not camera:
                print("Camera not available")
            elif not display:
                print("Display not available")
        # All resources automatically cleaned up

    def record_and_show_status(self, duration=5):
        """Record audio and show status on display."""
        if not self.status.audio_available:
            print("Audio hardware not available")
            return

        with Audio() as audio, \
             Display() as display if self.status.eink_available else None:

            # Show recording status
            if display:
                display.clear()
                text = display.render_text("Recording...", 10, 10, 2)
                display.display_image(text, DisplayMode.FULL)

            # Record
            audio.record("/tmp/recording.wav", duration)

            # Show complete
            if display:
                display.clear()
                text = display.render_text("Complete!", 10, 10, 2)
                display.display_image(text, DisplayMode.FULL)
        # All resources automatically cleaned up

# Usage
manager = HardwareManager()
manager.capture_and_display()
manager.record_and_show_status()
```

## Hardware Testing

Test individual hardware components:

```bash
# Audio test
python -m distiller_sdk.hardware.audio._audio_test

# Camera test
python -m distiller_sdk.hardware.camera._camera_unit_test

# E-ink display test
python -m distiller_sdk.hardware.eink._display_test
```

## Thread Safety

All hardware modules in v3.0 are thread-safe and can be used concurrently:

```python
import threading
from distiller_sdk.hardware.audio import Audio
from distiller_sdk.hardware.sam import LED

# Safe concurrent operations
with Audio() as audio, LED(use_sudo=True) as led:
    def record_task():
        audio.record("recording.wav", duration=5)

    def led_animation():
        led.blink_led(led_id=0, red=255, green=0, blue=0, timing=500)

    # Both operations are thread-safe
    t1 = threading.Thread(target=record_task)
    t2 = threading.Thread(target=led_animation)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
# Automatic cleanup
```

**Thread Safety Guarantees:**
- All public methods use internal locking for thread safety
- Multiple threads can safely call methods on the same instance
- No external synchronization required for concurrent operations
- Context managers properly handle cleanup in multi-threaded code

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
