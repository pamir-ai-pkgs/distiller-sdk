# Whisper ASR Module

The Whisper module provides robust Automatic Speech Recognition (ASR) using OpenAI's Whisper models
through the Faster Whisper implementation. It offers high-accuracy transcription with support for
multiple languages and is optimized for the Raspberry Pi CM5 platform.

## Overview

Whisper is an advanced ASR engine that:

- Uses OpenAI's Whisper models optimized with CTranslate2
- Supports multiple languages with automatic detection
- Provides word-level timestamps
- Optimized for CPU inference on ARM64
- Works with various audio formats and sample rates

## Prerequisites

- Python 3.11+
- Faster Whisper library
- PyAudio for audio capture
- Whisper model files (downloaded separately)
- Properly configured audio hardware

## Installation

The Whisper module is included in the Distiller CM5 SDK. Ensure the SDK is properly installed:

```bash
sudo dpkg -i distiller-cm5-sdk_*_arm64.deb
source /opt/distiller-cm5-sdk/activate.sh
```

Download Whisper models (optional, not included by default):

```bash
cd /opt/distiller-cm5-sdk
./build.sh --whisper
```

Model options:

- `faster-distil-whisper-small.en` - English-only, fastest
- `faster-whisper-base` - Multilingual, balanced
- `faster-whisper-small` - Multilingual, higher accuracy

## Quick Start

### Basic Transcription from File

```python
from distiller_cm5_sdk.whisper import Whisper

# Initialize Whisper with default model
whisper = Whisper()

# Transcribe an audio file
for text in whisper.transcribe("audio.wav"):
    print(f"Transcribed: {text}")

# Clean up resources
whisper.cleanup()
```

### Push-to-Talk Recording

```python
from distiller_cm5_sdk.whisper import Whisper

whisper = Whisper()

# Interactive push-to-talk
for text in whisper.record_and_transcribe_ptt():
    print(f"You said: {text}")

whisper.cleanup()
```

### Custom Configuration

```python
from distiller_cm5_sdk.whisper import Whisper

# Configure model and audio settings
whisper = Whisper(
    model_config={
        "model_size": "faster-whisper-base",
        "device": "cpu",
        "compute_type": "int8",
        "language": "en"
    },
    audio_config={
        "rate": 48000,
        "channels": 1
    }
)

# Use the configured instance
audio_data = whisper.stop_recording()
for text in whisper.transcribe_buffer(audio_data):
    print(text)
```

## API Reference

### Class: Whisper

#### `__init__(model_config=None, audio_config=None)`

Initialize the Whisper ASR engine.

**Parameters:**

- `model_config` (dict, optional): Model configuration options
  - `model_hub_path` (str): Path to model directory (default: auto-detected)
  - `model_size` (str): Model name (default: "faster-distil-whisper-small.en")
  - `device` (str): Device for inference ("cpu" or "cuda", default: "cpu")
  - `compute_type` (str): Computation type ("int8", "float16", "float32", default: "int8")
  - `beam_size` (int): Beam search width (default: 5)
  - `language` (str): Target language code (default: "en", use None for auto-detection)
- `audio_config` (dict, optional): Audio configuration options
  - `channels` (int): Number of channels (default: 1 for mono)
  - `rate` (int): Sample rate in Hz (default: 48000)
  - `chunk` (int): Audio chunk size (default: 1024)
  - `record_secs` (int): Default recording duration (default: 3)
  - `device` (int/str): Audio device index or name (default: None for system default)
  - `format` (pyaudio constant): Audio format (default: pyaudio.paInt16)

**Raises:**

- `ValueError`: If model files are not found

**Example:**

```python
# English-only model for faster processing
whisper = Whisper(
    model_config={"model_size": "faster-distil-whisper-small.en"}
)

# Multilingual model with auto language detection
whisper = Whisper(
    model_config={
        "model_size": "faster-whisper-base",
        "language": None  # Auto-detect
    }
)
```

#### `transcribe(audio_path: str) -> Generator[str, None, None]`

Transcribe audio from a file.

**Parameters:**

- `audio_path` (str): Path to audio file (supports various formats)

**Returns:**

- Generator yielding transcribed text segments

**Example:**

```python
for segment in whisper.transcribe("recording.wav"):
    print(segment)
```

#### `transcribe_buffer(audio_data: bytes) -> Generator[str, None, None]`

Transcribe audio from a WAV format byte buffer.

**Parameters:**

- `audio_data` (bytes): Audio data in WAV format

**Returns:**

- Generator yielding transcribed text segments

**Example:**

```python
# Read audio data
with open("audio.wav", "rb") as f:
    audio_data = f.read()

# Transcribe
for text in whisper.transcribe_buffer(audio_data):
    print(text)
```

#### `start_recording() -> bool`

Start recording audio (push-to-talk start).

**Returns:**

- bool: True if recording started successfully, False otherwise

**Example:**

```python
if whisper.start_recording():
    print("Recording... Press Enter to stop")
    input()
    audio_data = whisper.stop_recording()
```

#### `stop_recording() -> bytes`

Stop recording and return audio data.

**Returns:**

- bytes: Audio data in WAV format, or None if not recording

**Example:**

```python
audio_data = whisper.stop_recording()
if audio_data:
    # Save or process the audio
    with open("recorded.wav", "wb") as f:
        f.write(audio_data)
```

#### `record_and_transcribe_ptt() -> Generator[str, None, None]`

Interactive push-to-talk recording and transcription.

**Returns:**

- Generator yielding transcribed text segments

**Example:**

```python
# Simple voice input
for text in whisper.record_and_transcribe_ptt():
    print(f"Transcription: {text}")
```

#### `cleanup()`

Release audio resources and clean up.

**Example:**

```python
whisper.cleanup()
```

## Advanced Usage

### Multilingual Transcription

```python
from distiller_cm5_sdk.whisper import Whisper

# Initialize with multilingual model
whisper = Whisper(
    model_config={
        "model_size": "faster-whisper-base",
        "language": None  # Auto-detect language
    }
)

# Transcribe will detect and report the language
audio_files = ["english.wav", "spanish.wav", "french.wav"]

for audio_file in audio_files:
    print(f"\nTranscribing {audio_file}:")
    for text in whisper.transcribe(audio_file):
        print(f"  {text}")

whisper.cleanup()
```

### Transcription with Timestamps

```python
from distiller_cm5_sdk.whisper import Whisper

# The model provides timestamps for each segment
whisper = Whisper()

# Note: Timestamps are logged but not returned in the generator
# Check logs for timing information
for text in whisper.transcribe("long_audio.wav"):
    # Timestamps appear in logs like:
    # [0.00s -> 3.50s] First sentence
    # [3.50s -> 7.20s] Second sentence
    print(text)
```

### Batch Processing with Progress

```python
from distiller_cm5_sdk.whisper import Whisper
import os
from pathlib import Path

whisper = Whisper()

audio_dir = Path("/path/to/audio/files")
output_dir = Path("/path/to/transcripts")
output_dir.mkdir(exist_ok=True)

audio_files = list(audio_dir.glob("*.wav"))
total_files = len(audio_files)

for i, audio_file in enumerate(audio_files, 1):
    print(f"Processing {i}/{total_files}: {audio_file.name}")

    transcript = []
    for text in whisper.transcribe(str(audio_file)):
        transcript.append(text)

    # Save transcript
    output_file = output_dir / f"{audio_file.stem}.txt"
    with open(output_file, "w") as f:
        f.write(" ".join(transcript))

    print(f"  Saved to: {output_file}")

whisper.cleanup()
print(f"Completed {total_files} transcriptions")
```

### Real-time Transcription Loop

```python
from distiller_cm5_sdk.whisper import Whisper
import time

whisper = Whisper(
    model_config={"beam_size": 1},  # Faster inference
    audio_config={"rate": 16000}     # Lower sample rate
)

def continuous_transcription(duration_per_chunk=5):
    """Continuously record and transcribe in chunks"""

    print(f"Starting continuous transcription ({duration_per_chunk}s chunks)")
    print("Press Ctrl+C to stop")

    try:
        while True:
            # Record for specified duration
            print(f"Recording for {duration_per_chunk} seconds...")
            whisper.start_recording()
            time.sleep(duration_per_chunk)
            audio_data = whisper.stop_recording()

            # Transcribe the chunk
            if audio_data:
                print("Transcribing...")
                for text in whisper.transcribe_buffer(audio_data):
                    if text.strip():
                        print(f"[{time.strftime('%H:%M:%S')}] {text}")

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        whisper.cleanup()

# Run continuous transcription
continuous_transcription(duration_per_chunk=3)
```

### Custom Audio Device Selection

```python
from distiller_cm5_sdk.whisper import Whisper
import pyaudio

# List available audio devices
p = pyaudio.PyAudio()
print("Available audio input devices:")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info["maxInputChannels"] > 0:
        print(f"  [{i}] {info['name']} ({info['maxInputChannels']} channels)")
p.terminate()

# Use specific device by index
whisper = Whisper(
    audio_config={"device": 2}  # Use device index 2
)

# Or by name
whisper = Whisper(
    audio_config={"device": "USB Audio Device"}
)
```

### Optimize for Speed vs Accuracy

```python
from distiller_cm5_sdk.whisper import Whisper

# Fast configuration (lower accuracy)
fast_whisper = Whisper(
    model_config={
        "model_size": "faster-distil-whisper-small.en",
        "compute_type": "int8",
        "beam_size": 1  # Greedy search
    }
)

# Accurate configuration (slower)
accurate_whisper = Whisper(
    model_config={
        "model_size": "faster-whisper-base",
        "compute_type": "float32",
        "beam_size": 10  # Wider beam search
    }
)

# Benchmark both
import time

test_audio = "test.wav"

# Fast mode
start = time.time()
fast_result = list(fast_whisper.transcribe(test_audio))
fast_time = time.time() - start

# Accurate mode
start = time.time()
accurate_result = list(accurate_whisper.transcribe(test_audio))
accurate_time = time.time() - start

print(f"Fast mode: {fast_time:.2f}s")
print(f"Accurate mode: {accurate_time:.2f}s")
```

## Integration Examples

### Voice Command System

```python
from distiller_cm5_sdk.whisper import Whisper
from distiller_cm5_sdk.piper import Piper
import re

whisper = Whisper()
piper = Piper()

# Define voice commands
commands = {
    r"turn on (?:the )?light": lambda: print("Turning on light..."),
    r"turn off (?:the )?light": lambda: print("Turning off light..."),
    r"what time is it": lambda: piper.speak_stream(f"The time is {time.strftime('%I:%M %p')}"),
    r"exit|quit|stop": lambda: "exit"
}

def process_command(text):
    """Match text against commands and execute"""
    text_lower = text.lower().strip()

    for pattern, action in commands.items():
        if re.search(pattern, text_lower):
            result = action()
            if result == "exit":
                return False
            return True

    # Unknown command
    piper.speak_stream("Sorry, I didn't understand that command")
    return True

# Main loop
piper.speak_stream("Voice command system ready. Say 'exit' to quit.")

try:
    while True:
        print("\nListening for command...")

        for text in whisper.record_and_transcribe_ptt():
            print(f"Heard: {text}")
            if not process_command(text):
                piper.speak_stream("Goodbye!")
                break
        else:
            continue
        break

finally:
    whisper.cleanup()
```

### Transcription with Confidence Filtering

```python
from distiller_cm5_sdk.whisper import Whisper

whisper = Whisper()

def is_valid_transcription(text):
    """Filter out low-confidence or noise transcriptions"""
    # Filter out very short transcriptions (likely noise)
    if len(text.strip()) < 3:
        return False

    # Filter out common mis-transcriptions
    noise_patterns = [
        "thank you", "thanks for watching",  # Common YouTube artifacts
        "[music]", "[applause]", "[silence]"  # Common placeholders
    ]

    text_lower = text.lower()
    for pattern in noise_patterns:
        if pattern in text_lower and len(text_lower) < 20:
            return False

    return True

# Transcribe with filtering
for text in whisper.transcribe("noisy_audio.wav"):
    if is_valid_transcription(text):
        print(f"Valid: {text}")
    else:
        print(f"Filtered: {text}")
```

## Troubleshooting

### Model Not Found Error

If you get "Model not found" error:

1. Check if models are downloaded:

```bash
ls -la /opt/distiller-cm5-sdk/models/whisper/
```

2. Download Whisper models:

```bash
cd /opt/distiller-cm5-sdk
./build.sh --whisper
```

3. Verify model structure:

```bash
ls -la /opt/distiller-cm5-sdk/models/whisper/faster-distil-whisper-small.en/
# Should contain: model.bin, config.json, tokenizer.json, etc.
```

### Audio Hardware Issues

If audio recording fails:

1. Check audio devices:

```bash
arecord -l
```

2. Test recording:

```bash
arecord -d 5 -f S16_LE -r 48000 test.wav
aplay test.wav
```

3. Check permissions:

```bash
groups | grep audio
# If not in audio group:
sudo usermod -a -G audio $USER
# Log out and back in
```

### Poor Transcription Quality

To improve transcription accuracy:

1. Use a better model:

```python
# Upgrade from small to base model
whisper = Whisper(
    model_config={"model_size": "faster-whisper-base"}
)
```

2. Ensure good audio quality:

```python
# Check if microphone gain is appropriate
from distiller_cm5_sdk.hardware.audio import Audio
Audio.set_mic_gain_static(85)
```

3. Reduce background noise:

```python
# Record in a quiet environment
# Consider using noise reduction preprocessing
```

### Memory Issues

If running out of memory:

1. Use smaller model:

```python
whisper = Whisper(
    model_config={
        "model_size": "faster-distil-whisper-small.en",
        "compute_type": "int8"  # Lower precision
    }
)
```

2. Process shorter audio chunks:

```python
# Instead of transcribing long files at once
# Break them into smaller segments
```

3. Clean up resources:

```python
# Always call cleanup when done
whisper.cleanup()

# Use context manager pattern
class WhisperContext:
    def __enter__(self):
        self.whisper = Whisper()
        return self.whisper

    def __exit__(self, *args):
        self.whisper.cleanup()

with WhisperContext() as w:
    for text in w.transcribe("audio.wav"):
        print(text)
```

## Performance Considerations

- **Model Loading**: First initialization takes 3-5 seconds to load models
- **CPU Usage**: Transcription uses 40-60% CPU on CM5 depending on model
- **Memory Usage**: Models require 200-500MB RAM depending on size
- **Real-time Factor**: Typical RTF is 0.3-0.5 (faster than real-time)
- **Accuracy vs Speed**: Trade-off between model size and accuracy

### Performance Comparison

| Model           | Memory | Speed  | Accuracy       | Languages    |
| --------------- | ------ | ------ | -------------- | ------------ |
| distil-small.en | ~200MB | Fast   | Good (English) | English only |
| base            | ~350MB | Medium | Better         | 100+         |
| small           | ~500MB | Slower | Best           | 100+         |

## Best Practices

1. **Model Selection**:
   - Use English-only models for English content
   - Use base model for multilingual needs
   - Consider compute_type based on accuracy needs

2. **Audio Quality**:
   - Use 16kHz or higher sample rate
   - Ensure clear audio without clipping
   - Minimize background noise

3. **Resource Management**:
   - Initialize once and reuse the instance
   - Clean up resources when done
   - Monitor memory usage for long sessions

## License and Credits

The Whisper module uses:

- OpenAI Whisper models (MIT License)
- Faster Whisper implementation (MIT License)
- CTranslate2 for optimization (MIT License)

Part of the Distiller CM5 SDK for Raspberry Pi CM5 platform.
