# API Reference

Complete API documentation for the Distiller SDK modules.

## Hardware APIs

### Audio Class

```python
from distiller_sdk.hardware.audio import Audio

class Audio:
    def __init__(self):
        """Initialize audio system."""

    # Recording Methods
    def record(self, filepath: str, duration: float = None) -> None:
        """Record audio to file."""

    def stream_record(self, callback: Callable, buffer_size: int = 4096) -> Thread:
        """Stream recording with callback."""

    def start_recording(self) -> None:
        """Start recording (manual control)."""

    def stop_recording(self) -> bytes:
        """Stop recording and return audio data."""

    # Playback Methods
    def play(self, filepath: str) -> None:
        """Play audio file."""

    def stream_play(self, data: bytes, format_type: str = "S16_LE",
                   sample_rate: int = 16000, channels: int = 1) -> None:
        """Stream audio playback."""

    # Volume Control
    @staticmethod
    def set_mic_gain_static(gain: int) -> None:
        """Set microphone gain (0-100)."""

    @staticmethod
    def set_speaker_volume_static(volume: int) -> None:
        """Set speaker volume (0-100)."""

    # Status Methods
    def is_recording(self) -> bool:
        """Check if currently recording."""

    def is_playing(self) -> bool:
        """Check if currently playing."""

    def close(self) -> None:
        """Release audio resources."""
```

### Display Class

```python
from distiller_sdk.hardware.eink import Display, DisplayMode

class Display:
    ARRAY_SIZE: int  # Total bytes for display buffer

    def __init__(self, library_path: str = None, auto_init: bool = True):
        """Initialize display hardware."""

    # Primary display method
    def display_image_auto(self, image: Union[str, bytes],
                          mode: DisplayMode = DisplayMode.FULL,
                          scaling: ScalingMethod = ScalingMethod.LETTERBOX,
                          dithering: DitheringMethod = DitheringMethod.FLOYD_STEINBERG,
                          invert_colors: bool = False) -> None:
        """Display any image with auto-scaling and dithering."""

    # Backward-compatible aliases
    def display_image(self, image: Union[str, bytes], *,
                      mode=DisplayMode.FULL, scaling=ScalingMethod.LETTERBOX,
                      dithering=DitheringMethod.FLOYD_STEINBERG,
                      invert_colors=False, **kwargs) -> None:
        """Alias for display_image_auto(). Ignores legacy kwargs."""

    def display_png_auto(self, image: Union[str, bytes], *,
                         mode=DisplayMode.FULL, scaling=ScalingMethod.LETTERBOX,
                         dithering=DitheringMethod.FLOYD_STEINBERG,
                         invert_colors=False, **kwargs) -> None:
        """Alias for display_image_auto(). Ignores legacy kwargs."""

    def display_text(self, text: str, x: int = 0, y: int = 0,
                    scale: int = 1, invert: bool = False,
                    mode: DisplayMode = DisplayMode.FULL) -> None:
        """Render and display text in a single call."""

    def clear(self) -> None:
        """Clear display to white."""

    def sleep(self) -> None:
        """Put display into low-power sleep mode."""

    def close(self) -> None:
        """Release display hardware resources."""

    def get_dimensions(self) -> Tuple[int, int]:
        """Returns (width, height) — (250, 128)."""

    def is_initialized(self) -> bool:
        """Check if display hardware is initialized."""

    def convert_png_to_raw(self, filepath: str) -> bytes:
        """Convert PNG to raw 1-bit packed data."""

    # Text Rendering
    def render_text(self, text: str, x: int, y: int,
                   scale: int = 1, invert: bool = False) -> bytes:
        """Render text to buffer."""

    def overlay_text(self, buffer: bytes, text: str,
                    x: int, y: int, scale: int = 1,
                    invert: bool = False) -> bytes:
        """Overlay text on existing buffer."""

    # Shape Drawing
    def draw_rect(self, buffer: bytes, x: int, y: int,
                 width: int, height: int, filled: bool = False,
                 value: bool = True) -> bytes:
        """Draw rectangle on buffer."""

    # Partial Refresh Base Map
    def set_partial_base_map(self, image: Union[str, bytes]) -> None:
        """Set base map for partial refresh (writes to both RAM buffers to prevent ghosting)."""

    # Grayscale Display
    def display_grayscale(self, filename: str,
                         scaling: str = "letterbox",
                         invert: bool = False) -> None:
        """Display image with 4-level grayscale. scaling takes strings: 'letterbox', 'crop', 'stretch'."""
```

### Camera Class

```python
from distiller_sdk.hardware.camera import Camera

class Camera:
    def __init__(self):
        """Initialize camera system."""

    def capture_image(self, filepath: str = None) -> np.ndarray:
        """Capture single image."""

    def get_frame(self) -> np.ndarray:
        """Get single frame as numpy array."""

    def start_stream(self, callback: Callable) -> None:
        """Start video stream with callback."""

    def stop_stream(self) -> None:
        """Stop video stream."""

    def adjust_setting(self, setting: str, value: int) -> None:
        """Adjust camera setting."""

    def get_setting(self, setting: str) -> int:
        """Get current setting value."""

    def get_available_settings(self) -> List[str]:
        """List available settings."""

    def close(self) -> None:
        """Release camera resources."""
```

### LED Class

```python
from distiller_sdk.hardware.sam import LED

class LED:
    def __init__(self, use_sudo: bool = False):
        """Initialize LED control."""

    # Individual LED Control
    def set_rgb_color(self, led_id: int, red: int, green: int, blue: int) -> None:
        """Set RGB color (0-255 each)."""

    def set_brightness(self, led_id: int, brightness: int) -> None:
        """Set brightness (0-255)."""

    def turn_off(self, led_id: int) -> None:
        """Turn off specific LED."""

    def get_rgb_color(self, led_id: int) -> Tuple[int, int, int]:
        """Get current RGB values."""

    def get_brightness(self, led_id: int) -> int:
        """Get current brightness."""

    # Batch Control
    def set_color_all(self, red: int, green: int, blue: int) -> None:
        """Set all LEDs to same color."""

    def set_brightness_all(self, brightness: int) -> None:
        """Set all LEDs to same brightness."""

    def turn_off_all(self) -> None:
        """Turn off all LEDs."""

    def get_available_leds(self) -> List[int]:
        """List available LED IDs."""

    # Animation Control
    def set_animation_mode(self, led_id: int, mode: str, timing: Optional[int] = None) -> None:
        """Set animation mode. Modes: static, blink, fade, rainbow. Timings: 100, 200, 500, 1000ms."""

    def blink_led(self, led_id: int, red: int, green: int, blue: int, timing: int = 500) -> None:
        """Set LED to blink mode with color and timing."""

    def fade_led(self, led_id: int, red: int, green: int, blue: int, timing: int = 1000) -> None:
        """Set LED to fade mode with color and timing."""

    def rainbow_led(self, led_id: int, timing: int = 1000) -> None:
        """Set LED to rainbow cycle mode with timing."""

    # Linux LED Triggers
    def set_trigger(self, led_id: int, trigger: str) -> None:
        """Set Linux LED trigger (heartbeat-rgb, breathing-rgb, rainbow-rgb, none)."""

    def get_trigger(self, led_id: int) -> str:
        """Get current trigger."""

    def get_available_triggers(self, led_id: int) -> List[str]:
        """Get available triggers for LED."""
```

## Enums and Constants

### DisplayMode

```python
class DisplayMode(IntEnum):
    FULL = 0           # Full refresh — slow, high quality, no ghosting
    PARTIAL = 1        # Partial refresh — fast updates, may ghost
    FAST = 2           # Fast refresh (~1.5s) — temperature override, reduced ghosting
    TURBO = 3          # Turbo refresh (~1s) — fastest, may ghost
    GRAYSCALE_4 = 4    # 4-level grayscale (EPD128x250 only, file paths only)
```

### ScalingMethod

```python
class ScalingMethod(IntEnum):
    LETTERBOX = 0      # Maintain aspect ratio, add black borders
    CROP_CENTER = 1    # Center crop to fill display
    STRETCH = 2        # Stretch to fill (may distort)
```

### DitheringMethod

```python
class DitheringMethod(IntEnum):
    THRESHOLD = 0          # Fast binary threshold
    FLOYD_STEINBERG = 1    # High quality error diffusion (default)
    ORDERED = 2            # Ordered dithering
```

### DisplayErrorCode

```python
class DisplayErrorCode(IntEnum):
    SUCCESS = 1            # Operation successful
    GPIO = -1              # GPIO hardware error
    SPI = -2               # SPI device error
    CONFIG = -3            # Configuration error
    TIMEOUT = -4           # Hardware timeout
    NOT_INITIALIZED = -5   # Display not initialized
    INVALID_DATA = -6      # Invalid data format
    PNG = -7               # PNG processing error
    IO = -8                # I/O error
    UNSUPPORTED_MODE = -10 # Mode not supported by current firmware
    UNKNOWN = -99          # Unknown error
```

## Error Handling

All SDK methods may raise the following exceptions:

```python
# Hardware errors
DisplayError     # E-ink display errors (see DisplayErrorCode for codes)
LEDError         # LED control errors
CameraError      # Camera initialization/operation errors
RuntimeError     # Hardware initialization failed
IOError          # Device I/O error
ValueError       # Invalid parameter

# File errors
FileNotFoundError  # File doesn't exist
PermissionError    # Insufficient permissions
```

Example error handling:

```python
from distiller_sdk.hardware.audio import Audio

try:
    audio = Audio()
    audio.record("test.wav", duration=5)
except RuntimeError as e:
    print(f"Audio init failed: {e}")
except IOError as e:
    print(f"Recording failed: {e}")
finally:
    if audio:
        audio.close()
```

## Next Steps

- [Troubleshooting](Troubleshooting) - Common issues
- [Development Guide](Development-Guide) - Contributing to SDK
