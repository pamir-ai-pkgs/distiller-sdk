# API Reference

Complete API documentation for the Distiller SDK modules.

## Hardware Detection

### HardwareStatus Class

```python
from distiller_sdk.hardware_status import HardwareStatus

class HardwareStatus:
    """Check hardware availability without raising exceptions."""

    @property
    def eink_available(self) -> bool:
        """Check if E-ink display is available."""

    @property
    def camera_available(self) -> bool:
        """Check if camera is available."""

    @property
    def led_available(self) -> bool:
        """Check if LED controller is available."""

    @property
    def audio_available(self) -> bool:
        """Check if audio hardware is available."""
```

**Example Usage:**
```python
status = HardwareStatus()

if status.eink_available:
    from distiller_sdk.hardware.eink import Display
    with Display() as display:
        display.clear()

if status.camera_available:
    from distiller_sdk.hardware.camera import Camera
    with Camera() as camera:
        camera.capture_image("photo.jpg")
```

## Hardware APIs

### Audio Class

```python
from distiller_sdk.hardware.audio import Audio

class Audio:
    def __init__(self):
        """Initialize audio system."""

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.close()
        return False

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

    def __init__(self, firmware: FirmwareType = None):
        """Initialize display with optional firmware type."""

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        return False

    # Basic Display
    def display_image(self, image_data: Union[str, bytes],
                     mode: DisplayMode = DisplayMode.FULL,
                     rotate: Union[int, bool] = False,
                     flip_horizontal: bool = False,
                     flip_vertical: bool = False,
                     invert_colors: bool = False,
                     src_width: int = None,
                     src_height: int = None) -> None:
        """Display image with transformations."""

    def clear(self) -> None:
        """Clear display to white."""

    # Auto-conversion
    def display_image_auto(self, filepath: str,
                          mode: DisplayMode = DisplayMode.FULL,
                          scaling: ScalingMethod = ScalingMethod.LETTERBOX,
                          dithering: DitheringMethod = DitheringMethod.FLOYD_STEINBERG) -> None:
        """Display any image with auto-conversion."""

    def display_png_auto(self, filepath: str,
                        mode: DisplayMode = DisplayMode.FULL,
                        scaling: ScalingMethod = ScalingMethod.LETTERBOX,
                        dithering: DitheringMethod = DitheringMethod.FLOYD_STEINBERG,
                        rotate: int = 0,
                        flip_horizontal: bool = False,
                        flip_vertical: bool = False,
                        crop_x: int = None,
                        crop_y: int = None) -> None:
        """Display PNG with full options."""

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
```

### Camera Class

```python
from distiller_sdk.hardware.camera import Camera

class Camera:
    def __init__(self):
        """Initialize camera system."""

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.close()
        return False

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

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic LED turn-off."""
        self.turn_off_all()
        return False

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

## AI APIs

### Parakeet Class

```python
from distiller_sdk.parakeet import Parakeet

class Parakeet:
    def __init__(self, vad_threshold: float = 0.5,
                min_speech_duration: float = 0.3,
                max_silence_duration: float = 0.5):
        """Initialize ASR with VAD."""

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.cleanup()
        return False

    def record_and_transcribe_ptt(self) -> Generator[str, None, None]:
        """Push-to-talk recording and transcription."""

    def auto_record_and_transcribe(self) -> Generator[str, None, None]:
        """Automatic VAD-based recording and transcription."""

    def start_recording(self) -> None:
        """Start manual recording."""

    def stop_recording(self) -> bytes:
        """Stop recording and return audio."""

    def transcribe_buffer(self, audio_data: bytes) -> Generator[str, None, None]:
        """Transcribe audio buffer."""

    def cleanup(self) -> None:
        """Release ASR resources."""
```

### Piper Class

```python
from distiller_sdk.piper import Piper

class Piper:
    def __init__(self):
        """Initialize TTS engine."""

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        return False

    def speak_stream(self, text: str, volume: int = 50,
                    sound_card_name: str = None) -> None:
        """Stream speech to speakers."""

    def get_wav_file_path(self, text: str) -> str:
        """Generate WAV file and return path."""

    def list_voices(self) -> List[Dict[str, str]]:
        """List available voices."""
```

### Whisper Class

```python
from distiller_sdk.whisper import Whisper

class Whisper:
    def __init__(self, model_size: str = "base"):
        """Initialize Whisper ASR."""

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.cleanup()
        return False

    def transcribe_file(self, filepath: str,
                       language: str = None,
                       task: str = "transcribe") -> Union[str, Dict]:
        """Transcribe audio file."""
```

## Enums and Constants

### DisplayMode

```python
class DisplayMode(Enum):
    FULL = "full"      # Full refresh (slower, no ghosting)
    PARTIAL = "partial"  # Partial refresh (faster, may ghost)
```

### FirmwareType

```python
class FirmwareType:
    """String constants for firmware types."""
    EPD128x250 = "EPD128x250"  # Native: 128×250, Mounted: 250×128 landscape
    EPD240x416 = "EPD240x416"  # 240×416 display
```

### ScalingMethod

```python
class ScalingMethod(Enum):
    LETTERBOX = "letterbox"    # Maintain aspect ratio
    CROP_CENTER = "crop_center"  # Center crop to fill
    STRETCH = "stretch"        # Stretch to fill
```

### DitheringMethod

```python
class DitheringMethod(Enum):
    THRESHOLD = "threshold"           # Simple threshold
    FLOYD_STEINBERG = "floyd_steinberg"  # Error diffusion
    ORDERED = "ordered"              # Ordered dithering
```

## Utility Functions

### E-ink Transformations

```python
# Rotation functions
rotate_bitpacked(data: bytes, angle: int, width: int, height: int) -> bytes
rotate_bitpacked_ccw_90(data: bytes, width: int, height: int) -> bytes
rotate_bitpacked_cw_90(data: bytes, width: int, height: int) -> bytes
rotate_bitpacked_180(data: bytes, width: int, height: int) -> bytes

# Flip functions
flip_bitpacked_horizontal(data: bytes, width: int, height: int) -> bytes
flip_bitpacked_vertical(data: bytes, width: int, height: int) -> bytes

# Color inversion
invert_bitpacked_colors(data: bytes) -> bytes
```

### E-ink Configuration

```python
set_default_firmware(firmware: FirmwareType) -> None
get_default_firmware() -> FirmwareType
```

## Error Handling

### Exception Hierarchy

All SDK modules provide specific exception types for better error handling:

```python
from distiller_sdk.exceptions import (
    DistillerException,    # Base exception for all SDK errors
    AudioError,            # Audio module errors
    CameraError,           # Camera module errors
    DisplayError,          # Display module errors
    LEDError,              # LED module errors
    ParakeetError,         # Parakeet ASR errors
    PiperError,            # Piper TTS errors
    WhisperError,          # Whisper ASR errors
)
```

### Hardware Exceptions

**AudioError**: Audio recording/playback failures
**CameraError**: Camera initialization or capture failures
**DisplayError**: E-ink display errors (includes DisplayErrorCode enum)
**LEDError**: LED control errors

### AI Module Exceptions

**ParakeetError**: Parakeet ASR transcription failures
**PiperError**: Piper TTS synthesis failures
**WhisperError**: Whisper ASR transcription failures

### Standard Python Exceptions

**FileNotFoundError**: File doesn't exist
**PermissionError**: Insufficient permissions
**ValueError**: Invalid parameter values
**RuntimeError**: General runtime failures

### Exception Handling Example

```python
from distiller_sdk.hardware.audio import Audio, AudioError

try:
    with Audio() as audio:
        audio.record("test.wav", duration=5)
except AudioError as e:
    print(f"Audio hardware error: {e}")
except PermissionError:
    print("Permission denied - add user to 'audio' group")
except FileNotFoundError:
    print("Output directory not found")
except Exception as e:
    print(f"Unexpected error: {e}")
# Automatic cleanup via context manager
```

### Display Error Codes

```python
from distiller_sdk.hardware.eink import Display, DisplayError, DisplayErrorCode

try:
    with Display() as display:
        display.display_image("image.png")
except DisplayError as e:
    if hasattr(e, 'error_code'):
        if e.error_code == DisplayErrorCode.INIT_FAILED:
            print("Display initialization failed")
        elif e.error_code == DisplayErrorCode.INVALID_IMAGE:
            print("Invalid image format")
```

## Next Steps

- [Troubleshooting](Troubleshooting) - Common issues
- [Development Guide](Development-Guide) - Contributing to SDK
