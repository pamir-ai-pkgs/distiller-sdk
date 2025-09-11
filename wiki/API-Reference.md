# API Reference

Complete API documentation for the Distiller CM5 SDK modules.

## Hardware APIs

### Audio Class

```python
from distiller_cm5_sdk.hardware.audio import Audio

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
from distiller_cm5_sdk.hardware.eink import Display, DisplayMode

class Display:
    ARRAY_SIZE: int  # Total bytes for display buffer

    def __init__(self, firmware: FirmwareType = None):
        """Initialize display with optional firmware type."""

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
from distiller_cm5_sdk.hardware.camera import Camera

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
from distiller_cm5_sdk.hardware.sam import LED

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
```

## AI APIs

### Parakeet Class

```python
from distiller_cm5_sdk.parakeet import Parakeet

class Parakeet:
    def __init__(self, vad_threshold: float = 0.5,
                min_speech_duration: float = 0.3,
                max_silence_duration: float = 0.5):
        """Initialize ASR with VAD."""

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
from distiller_cm5_sdk.piper import Piper

class Piper:
    def __init__(self):
        """Initialize TTS engine."""

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
from distiller_cm5_sdk.whisper import Whisper

class Whisper:
    def __init__(self, model_size: str = "base"):
        """Initialize Whisper ASR."""

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
class FirmwareType(Enum):
    EPD128x250 = "EPD128x250"  # 250×128 display
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

All SDK methods may raise the following exceptions:

```python
# Hardware errors
RuntimeError  # Hardware initialization failed
IOError      # Device I/O error
ValueError   # Invalid parameter

# File errors
FileNotFoundError  # File doesn't exist
PermissionError   # Insufficient permissions

# AI model errors
ModelNotFoundError  # Model files missing
TranscriptionError  # ASR failed
SynthesisError     # TTS failed
```

Example error handling:

```python
from distiller_cm5_sdk.hardware.audio import Audio

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
