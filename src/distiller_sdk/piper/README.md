# Piper TTS Module

The Piper module implements Text-to-Speech (TTS) synthesis using ONNX models. It
uses ONNX Runtime for ARM64, with typical 50-100ms first-synthesis latency.

## Overview

Piper TTS features:

- Uses ONNX models for voice synthesis
- Real-time audio streaming to speakers
- Supports multiple voice configurations
- Uses ONNX Runtime ARM64 backend
- No internet connection required

## Prerequisites

- Python 3.11+
- Pre-compiled Piper binary for ARM64
- ALSA audio system
- Properly configured audio hardware
- ONNX voice models

## Installation

The Piper module is included in the Distiller SDK. Ensure the SDK is properly installed:

```bash
sudo dpkg -i distiller-sdk_*_arm64.deb
source /opt/distiller-sdk/activate.sh
```

Required files downloaded during SDK build:

- `piper` - ARM64 binary executable
- `en_US-amy-medium.onnx` - Voice model
- `en_US-amy-medium.onnx.json` - Voice configuration

## Quick Start

### Basic Text-to-Speech

```python
from distiller_sdk.piper import Piper

# Use context manager for automatic cleanup
with Piper() as piper:
    # Speak text through speakers
    piper.speak_stream("Hello, this is a test of the Piper TTS system.", volume=50)
# Automatic cleanup
```

### Generate WAV File

```python
from distiller_sdk.piper import Piper

with Piper() as piper:
    # Generate speech as WAV file
    text = "This text will be saved as a WAV file."
    output_path = piper.get_wav_file_path(text)
    print(f"Audio saved to: {output_path}")
# Automatic cleanup
```

### List Available Voices

```python
from distiller_sdk.piper import Piper

with Piper() as piper:
    # Get available voices
    voices = piper.list_voices()
    for voice in voices:
        print(f"Voice: {voice['name']}")
        print(f"  Language: {voice['language']}")
        print(f"  Quality: {voice['quality']}")
```

## API Reference

### Class: Piper

#### `__init__(model_path=None, piper_path=None)`

Initialize the Piper TTS engine.

**Parameters:**

- `model_path` (str, optional): Path to voice model directory (default: auto-detected from SDK)
- `piper_path` (str, optional): Path to Piper binary directory (default: auto-detected from SDK)

**Raises:**

- `ValueError`: If required model files or Piper binary are not found

**Example:**

```python
# Use default paths with context manager
with Piper() as piper:
    piper.speak_stream("Hello world")

# Use custom paths
with Piper(
    model_path="/custom/path/to/models",
    piper_path="/custom/path/to/piper"
) as piper:
    piper.speak_stream("Hello world")
```

#### `list_voices() -> List[Dict]`

List available voices for TTS.

**Returns:**

- List[Dict]: List of voice information dictionaries containing:
  - `name` (str): Voice identifier
  - `language` (str): Language and locale
  - `quality` (str): Voice quality level
  - `model_path` (str): Path to ONNX model
  - `config_path` (str): Path to configuration file

**Example:**

```python
with Piper() as piper:
    voices = piper.list_voices()
    for voice in voices:
        print(f"{voice['name']}: {voice['language']} ({voice['quality']})")
```

#### `get_wav_file_path(text: str) -> str`

Generate speech and save to WAV file.

**Parameters:**

- `text` (str): Text to synthesize

**Returns:**

- str: Path to generated WAV file

**Raises:**

- `ValueError`: If Piper command fails

**Example:**

```python
import subprocess

with Piper() as piper:
    output_file = piper.get_wav_file_path("Hello world")
    print(f"Generated: {output_file}")

    # Play the generated file
    subprocess.run(["aplay", output_file])
```

#### `speak_stream(text: str, volume: int = 50, sound_card_name: str = None)`

Stream synthesized speech directly to speakers.

**Parameters:**

- `text` (str): Text to synthesize and speak
- `volume` (int, optional): Speaker volume level (0-100, default: 50)
- `sound_card_name` (str, optional): Name of sound card to use (default: system default)

**Raises:**

- `ValueError`: If volume is out of range or streaming fails

**Example:**

```python
with Piper() as piper:
    # Simple usage with default settings
    piper.speak_stream("Hello, world!")

    # With custom volume
    piper.speak_stream("This is louder.", volume=75)

    # With specific sound card
    piper.speak_stream(
        "Using specific audio device.",
        volume=50,
        sound_card_name="snd_rpi_pamir_ai_soundcard"
    )
```

#### `__enter__()`

Enter context manager.

**Returns:**

- Piper instance for context manager usage

**Example:**

```python
with Piper() as piper:
    # Use piper
    pass
```

#### `__exit__(exc_type, exc_val, exc_tb)`

Exit context manager and automatically cleanup resources.

**Parameters:**

- `exc_type`: Exception type (if any)
- `exc_val`: Exception value (if any)
- `exc_tb`: Exception traceback (if any)

**Returns:**

- False (does not suppress exceptions)

**Note:** Currently no specific cleanup needed, but implemented for consistency and future extensibility.

## Exception Handling

The Piper module uses specific exceptions for better error handling:

```python
from distiller_sdk.piper import Piper, PiperError

try:
    with Piper() as piper:
        piper.speak_stream("Hello world", volume=50)
except PiperError as e:
    print(f"Piper error: {e}")
    # Handle Piper-specific errors (binary not found, model missing, etc.)
except ValueError as e:
    print(f"Invalid value: {e}")
    # Handle invalid parameters (volume out of range, etc.)
except FileNotFoundError as e:
    print(f"File not found: {e}")
    # Handle missing files or binaries
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
# Automatic cleanup via context manager
```

### Common PiperError Scenarios

```python
from distiller_sdk.piper import Piper, PiperError

try:
    with Piper() as piper:
        # This may raise PiperError if models or binary are missing
        piper.speak_stream("Test message")
except PiperError as e:
    if "binary" in str(e).lower():
        print("Piper binary not found - run ./build.sh to download")
    elif "model" in str(e).lower():
        print("Voice model not found - run ./build.sh to download models")
    else:
        print(f"Piper error: {e}")
```

## Thread Safety

All Piper module operations are thread-safe. Multiple threads can use the same Piper instance concurrently:

```python
import threading
from distiller_sdk.piper import Piper

with Piper() as piper:
    def speak_task(text):
        """Speak text in background thread"""
        piper.speak_stream(text, volume=50)

    # Multiple speech tasks can run concurrently
    threads = []
    texts = ["First message", "Second message", "Third message"]

    for text in texts:
        t = threading.Thread(target=speak_task, args=(text,))
        threads.append(t)
        t.start()

    # Wait for all speech to complete
    for t in threads:
        t.join()
```

## Advanced Usage

### Custom Voice Models

While the SDK includes a default voice, you can add additional Piper-compatible voices:

```python
import os
from distiller_sdk.piper import Piper

# Download a new voice model (example)
# wget https://github.com/rhasspy/piper/releases/download/v1.0.0/voice-en_US-ryan-high.tar.gz
# tar -xzf voice-en_US-ryan-high.tar.gz -C /path/to/voices/

# Initialize with custom model path
custom_model_path = "/path/to/voices"
with Piper(model_path=custom_model_path) as piper:
    # The module will use the first .onnx file found in the directory
    piper.speak_stream("Using custom voice model")
```

### Batch Processing Multiple Texts

```python
from distiller_sdk.piper import Piper
import time

texts = [
    "First announcement.",
    "Second announcement.",
    "Third announcement."
]

with Piper() as piper:
    for i, text in enumerate(texts, 1):
        print(f"Speaking text {i}...")
        piper.speak_stream(text, volume=50)
        time.sleep(1)  # Pause between announcements
# Automatic cleanup
```

### Dynamic Volume Control

```python
from distiller_sdk.piper import Piper
import time

with Piper() as piper:
    # Gradually increase volume
    for volume in range(20, 81, 10):
        text = f"Volume level is {volume} percent."
        piper.speak_stream(text, volume=volume)
        time.sleep(0.5)
```

### Text Processing and Speech

```python
from distiller_sdk.piper import Piper
import re

piper = Piper()

def clean_text_for_speech(text):
    """Prepare text for better TTS output"""
    # Expand abbreviations
    text = text.replace("Dr.", "Doctor")
    text = text.replace("Mr.", "Mister")
    text = text.replace("Mrs.", "Missus")

    # Handle numbers
    text = re.sub(r'\b(\d+)\b', lambda m: num_to_words(int(m.group(1))), text)

    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s.,!?-]', '', text)

    return text

def num_to_words(n):
    """Simple number to words converter (for small numbers)"""
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
             "sixteen", "seventeen", "eighteen", "nineteen"]

    if n < 10:
        return ones[n]
    elif n < 20:
        return teens[n-10]
    elif n < 100:
        return tens[n//10] + (" " + ones[n%10] if n%10 != 0 else "")
    else:
        return str(n)  # Fallback for larger numbers

# Example usage
raw_text = "Dr. Smith has 3 appointments at 2:30 PM."
clean_text = clean_text_for_speech(raw_text)

with Piper() as piper:
    piper.speak_stream(clean_text)
```

### Save Multiple Formats

```python
from distiller_sdk.piper import Piper
import subprocess
import os

text = "This audio will be saved in multiple formats."

with Piper() as piper:
    # Generate WAV
    wav_path = piper.get_wav_file_path(text)

# Convert to MP3 (requires ffmpeg)
mp3_path = wav_path.replace('.wav', '.mp3')
subprocess.run([
    "ffmpeg", "-i", wav_path,
    "-acodec", "mp3", "-ab", "128k",
    mp3_path
], capture_output=True)

# Convert to OGG
ogg_path = wav_path.replace('.wav', '.ogg')
subprocess.run([
    "ffmpeg", "-i", wav_path,
    "-acodec", "libvorbis", "-ab", "128k",
    ogg_path
], capture_output=True)

print(f"Generated files:")
print(f"  WAV: {wav_path}")
print(f"  MP3: {mp3_path}")
print(f"  OGG: {ogg_path}")
```

## Integration Examples

### With Parakeet ASR for Voice Assistant

```python
from distiller_sdk.piper import Piper
from distiller_sdk.parakeet import Parakeet

def voice_assistant():
    """Simple voice assistant loop"""
    with Piper() as piper, Parakeet() as parakeet:
        piper.speak_stream("Voice assistant ready. Say 'exit' to quit.")

        for text in parakeet.auto_record_and_transcribe():
            if text:
                print(f"You said: {text}")

                # Check for exit command
                if "exit" in text.lower():
                    piper.speak_stream("Goodbye!")
                    break

                # Echo back what was heard
                response = f"I heard you say: {text}"
                piper.speak_stream(response, volume=50)
    # Automatic cleanup for both modules

# Run the assistant
voice_assistant()
```

### With E-ink Display for Visual Feedback

```python
from distiller_sdk.piper import Piper
from distiller_sdk.hardware.eink import Display

def speak_with_display(text):
    """Show text on display while speaking"""
    with Piper() as piper, Display() as display:
        # Display the text
        display.clear()
        display.render_text(
            text=text,
            font_size=20,
            wrap_text=True
        )

        # Speak the text
        piper.speak_stream(text, volume=50)
    # Automatic cleanup

# Example usage
speak_with_display("Hello! This text appears on the display while being spoken.")
```

### Notification System

```python
from distiller_sdk.piper import Piper
from distiller_sdk.hardware.sam import LED
import time

def notify(message, priority="normal"):
    """Send audio and visual notification"""
    with Piper() as piper, LED(use_sudo=True) as led:
        if priority == "high":
            # Red LED for high priority
            led.set_rgb_color(0, 255, 0, 0)
            volume = 75
            prefix = "Urgent: "
        elif priority == "low":
            # Blue LED for low priority
            led.set_rgb_color(0, 0, 0, 255)
            volume = 30
            prefix = "Info: "
        else:
            # Green LED for normal
            led.set_rgb_color(0, 0, 255, 0)
            volume = 50
            prefix = ""

        # Speak the notification
        full_message = prefix + message
        piper.speak_stream(full_message, volume=volume)

        # Flash LED using blink animation
        current_color = led.get_rgb_color(0)
        led.blink_led(0, current_color[0], current_color[1], current_color[2], timing=200)
        time.sleep(2)
    # Automatic cleanup - LEDs turned off

# Example notifications
notify("System startup complete", priority="low")
notify("New message received", priority="normal")
notify("Battery level critical", priority="high")
```

## Troubleshooting

### Piper Binary Not Found

If you get "piper does not exist" error:

1. Verify Piper binary exists:

```bash
ls -la /opt/distiller-sdk/models/piper/piper/piper
```

2. Check executable permissions:

```bash
chmod +x /opt/distiller-sdk/models/piper/piper/piper
```

3. Test Piper directly:

```bash
echo "test" | /opt/distiller-sdk/models/piper/piper/piper --model /opt/distiller-sdk/models/piper/en_US-amy-medium.onnx --output_file test.wav
```

### No Audio Output

If speech synthesis works but no audio is heard:

1. Check speaker volume:

```python
from distiller_sdk.hardware.audio import Audio
print(f"Current volume: {Audio.get_speaker_volume_static()}")
Audio.set_speaker_volume_static(70)
```

2. Test audio output:

```bash
speaker-test -t sine -f 440 -l 1
```

3. Verify sound card:

```bash
aplay -l
```

### Model File Errors

If model files are missing or corrupted:

1. Check model files:

```bash
ls -la /opt/distiller-sdk/models/piper/*.onnx*
```

2. Re-download models:

```bash
cd /opt/distiller-sdk
./build.sh
```

### Audio Quality Issues

For better audio quality:

1. Adjust volume levels:

```python
# Lower volume can reduce distortion
piper.speak_stream(text, volume=40)
```

2. Check audio format compatibility:

```bash
# Verify audio device capabilities
aplay -D plughw:0 --dump-hw-params
```

3. Use different audio devices:

```python
# List available devices
import subprocess
result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
print(result.stdout)

# Use specific device
piper.speak_stream(text, sound_card_name="your_device_name")
```

## Performance Considerations

- **CPU Usage**: TTS synthesis uses approximately 10-20% CPU on CM5
- **Memory**: Models require approximately 50-100MB RAM
- **Latency**: First synthesis may take 1-2 seconds for model loading, subsequent calls are faster
- **Audio Buffer**: Streaming mode has minimal buffering for real-time playback

## Speech Synthesis Best Practices

1. **Text Preparation**:
   - Remove or expand abbreviations
   - Spell out numbers when needed
   - Add punctuation for natural pauses

2. **Volume Management**:
   - Start with moderate volume (40-60%)
   - Adjust based on environment
   - Consider automatic gain control

3. **Performance Optimization**:
   - Pre-load the Piper instance at startup
   - Reuse the same instance for multiple synthesis operations
   - Consider caching frequently used phrases

## License and Credits

The Piper module uses:

- Piper TTS engine (MIT License)
- ONNX Runtime (MIT License)
- Voice models from the Piper project

Part of the Distiller SDK for Raspberry Pi CM5 platform.
