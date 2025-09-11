# Parakeet ASR Module

The Parakeet module provides high-performance Automatic Speech Recognition (ASR) with Voice Activity
Detection (VAD) using ONNX models. It's designed for real-time speech-to-text conversion on the
Raspberry Pi CM5 platform, offering both push-to-talk and continuous speech recognition
capabilities.

## Overview

Parakeet is a lightweight ASR engine that uses:

- NVIDIA NeMo Parakeet models (ONNX format) for speech recognition
- Silero VAD for voice activity detection
- Optimized for ARM64 processors
- Support for streaming and batch transcription

## Prerequisites

- Python 3.11+
- PyAudio for audio capture
- ONNX Runtime for model inference
- Sherpa-ONNX for ASR processing
- Sounddevice for VAD-based recording
- Properly configured audio hardware

## Installation

The Parakeet module is included in the Distiller CM5 SDK. Ensure the SDK is properly installed:

```bash
sudo dpkg -i distiller-cm5-sdk_*_arm64.deb
source /opt/distiller-cm5-sdk/activate.sh
```

Required model files are downloaded during SDK build:

- `encoder.onnx` - Encoder model
- `decoder.onnx` - Decoder model
- `joiner.onnx` - Joiner model
- `tokens.txt` - Token vocabulary
- `silero_vad.onnx` - Voice Activity Detection model

## Quick Start

### Basic Transcription from File

```python
from distiller_cm5_sdk.parakeet import Parakeet

# Initialize Parakeet
parakeet = Parakeet()

# Transcribe an audio file
for text in parakeet.transcribe("/path/to/audio.wav"):
    print(f"Transcribed: {text}")

# Clean up resources
parakeet.cleanup()
```

### Push-to-Talk Recording

```python
from distiller_cm5_sdk.parakeet import Parakeet

parakeet = Parakeet()

# Start recording
print("Press Enter to start recording...")
input()
parakeet.start_recording()

# Stop and transcribe
print("Recording... Press Enter to stop...")
input()
audio_data = parakeet.stop_recording()

# Transcribe the recorded audio
for text in parakeet.transcribe_buffer(audio_data):
    print(f"Transcribed: {text}")

parakeet.cleanup()
```

### Automatic Speech Recognition with VAD

```python
from distiller_cm5_sdk.parakeet import Parakeet

# Initialize with custom VAD silence duration
parakeet = Parakeet(vad_silence_duration=1.0)

# Start continuous recognition with VAD
print("Listening... (Press Ctrl+C to stop)")
try:
    for text in parakeet.auto_record_and_transcribe():
        if text:  # Only print non-empty transcriptions
            print(f"Detected speech: {text}")
except KeyboardInterrupt:
    print("Stopping...")
finally:
    parakeet.cleanup()
```

## API Reference

### Class: Parakeet

#### `__init__(model_config=None, audio_config=None, vad_silence_duration=1.0)`

Initialize the Parakeet ASR engine.

**Parameters:**

- `model_config` (dict, optional): Model configuration options
  - `model_path` (str): Path to model directory (default: auto-detected)
  - `device` (str): Device for inference ("cpu" or "cuda", default: "cpu")
  - `num_threads` (int): Number of threads for inference (default: 4)
- `audio_config` (dict, optional): Audio configuration options
  - `channels` (int): Number of channels (default: 1 for mono)
  - `rate` (int): Sample rate in Hz (default: 16000)
  - `chunk` (int): Audio chunk size (default: 512)
  - `record_secs` (int): Default recording duration (default: 3)
  - `device` (str): Audio device name (default: "sysdefault")
  - `format` (pyaudio constant): Audio format (default: pyaudio.paInt16)
- `vad_silence_duration` (float): Minimum silence duration in seconds for VAD (default: 1.0)

**Example:**

```python
parakeet = Parakeet(
    model_config={"num_threads": 2},
    audio_config={"rate": 16000, "channels": 1},
    vad_silence_duration=0.5
)
```

#### `transcribe(audio_path: str) -> Generator[str, None, None]`

Transcribe audio from a file.

**Parameters:**

- `audio_path` (str): Path to audio file (must be 16kHz, mono)

**Returns:**

- Generator yielding transcribed text segments

**Example:**

```python
for text in parakeet.transcribe("recording.wav"):
    print(text)
```

#### `transcribe_buffer(audio_data: bytes) -> Generator[str, None, None]`

Transcribe audio from a WAV format byte buffer.

**Parameters:**

- `audio_data` (bytes): Audio data in WAV format

**Returns:**

- Generator yielding transcribed text segments

**Example:**

```python
with open("audio.wav", "rb") as f:
    audio_data = f.read()
for text in parakeet.transcribe_buffer(audio_data):
    print(text)
```

#### `start_recording() -> bool`

Start recording audio (push-to-talk start).

**Returns:**

- bool: True if recording started successfully, False otherwise

**Example:**

```python
if parakeet.start_recording():
    print("Recording started")
```

#### `stop_recording() -> bytes`

Stop recording audio and return the recorded data.

**Returns:**

- bytes: Audio data in WAV format, or None if not recording

**Example:**

```python
audio_data = parakeet.stop_recording()
if audio_data:
    # Process the audio data
    pass
```

#### `record_and_transcribe_ptt() -> Generator[str, None, None]`

Interactive push-to-talk demo with user prompts.

**Returns:**

- Generator yielding transcribed text segments

**Example:**

```python
for text in parakeet.record_and_transcribe_ptt():
    print(f"You said: {text}")
```

#### `auto_record_and_transcribe() -> Generator[str, None, None]`

Automatic speech recognition with voice activity detection.

**Returns:**

- Generator yielding transcribed text segments as they are recognized

**Example:**

```python
for text in parakeet.auto_record_and_transcribe():
    if text:
        print(f"Detected: {text}")
```

#### `cleanup()`

Release audio resources and clean up.

**Example:**

```python
parakeet.cleanup()
```

## Advanced Usage

### Custom Audio Device Selection

```python
# List available audio devices
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info["maxInputChannels"] > 0:
        print(f"Device {i}: {info['name']}")
p.terminate()

# Use specific device
parakeet = Parakeet(
    audio_config={"device": "USB Audio Device"}
)
```

### Adjusting VAD Sensitivity

```python
# More aggressive VAD (shorter silence = faster response)
parakeet = Parakeet(vad_silence_duration=0.3)

# More conservative VAD (longer silence = fewer false triggers)
parakeet = Parakeet(vad_silence_duration=2.0)
```

### Batch Processing Multiple Files

```python
import os
from distiller_cm5_sdk.parakeet import Parakeet

parakeet = Parakeet()

audio_files = ["file1.wav", "file2.wav", "file3.wav"]
transcriptions = {}

for audio_file in audio_files:
    transcript = []
    for text in parakeet.transcribe(audio_file):
        transcript.append(text)
    transcriptions[audio_file] = " ".join(transcript)

parakeet.cleanup()

# Print all transcriptions
for file, text in transcriptions.items():
    print(f"{file}: {text}")
```

### Real-time Streaming with Callback

```python
from distiller_cm5_sdk.parakeet import Parakeet

def on_speech_detected(text):
    """Callback function for processing transcribed text"""
    print(f"[{time.strftime('%H:%M:%S')}] {text}")
    # Add your custom processing here
    # e.g., send to server, trigger actions, etc.

parakeet = Parakeet(vad_silence_duration=0.5)

try:
    for text in parakeet.auto_record_and_transcribe():
        if text:
            on_speech_detected(text)
except KeyboardInterrupt:
    pass
finally:
    parakeet.cleanup()
```

## Troubleshooting

### No Audio Input Devices Found

If you encounter "No audio input devices found" error:

1. Check connected microphones:

```bash
arecord -l
```

2. Verify audio permissions:

```bash
sudo usermod -a -G audio $USER
# Log out and back in for changes to take effect
```

3. Test audio recording:

```bash
arecord -d 5 test.wav
aplay test.wav
```

### Model Loading Errors

If model files are missing:

1. Verify model files exist:

```bash
ls -la /opt/distiller-cm5-sdk/models/parakeet/
```

2. Re-download models if needed:

```bash
cd /opt/distiller-cm5-sdk
./build.sh
```

### VAD Not Working

If voice activity detection isn't working:

1. Check VAD model exists:

```bash
ls -la /opt/distiller-cm5-sdk/models/parakeet/silero_vad.onnx
```

2. Adjust VAD sensitivity:

```python
# Try different silence durations
parakeet = Parakeet(vad_silence_duration=0.5)  # More sensitive
# or
parakeet = Parakeet(vad_silence_duration=2.0)  # Less sensitive
```

### Poor Transcription Quality

1. Ensure audio is clear and at proper volume:
   - Microphone gain is automatically set to 85% for optimal performance
   - Check microphone placement and ambient noise

2. Verify audio format:
   - Sample rate must be 16kHz for Parakeet
   - Audio must be mono (single channel)

3. Test with known good audio:

```python
# Record a clear test phrase
parakeet = Parakeet()
print("Say 'The quick brown fox jumps over the lazy dog'")
for text in parakeet.record_and_transcribe_ptt():
    print(f"Transcribed: {text}")
```

## Performance Considerations

- **CPU Usage**: ASR is CPU-intensive. On CM5, expect 20-40% CPU usage during active transcription
- **Memory**: Models require approximately 100-150MB RAM when loaded
- **Latency**: Typical transcription latency is 100-300ms on CM5 hardware
- **Batch vs Stream**: For pre-recorded files, batch processing is more efficient than streaming

## Integration Examples

### With Piper TTS for Voice Assistant

```python
from distiller_cm5_sdk.parakeet import Parakeet
from distiller_cm5_sdk.piper import Piper

parakeet = Parakeet()
piper = Piper()

print("Voice Assistant Ready. Say something...")
for text in parakeet.auto_record_and_transcribe():
    if text:
        print(f"You said: {text}")
        response = f"You said: {text}"
        piper.speak_stream(response, volume=50)
```

### With Hardware LED Feedback

```python
from distiller_cm5_sdk.parakeet import Parakeet
from distiller_cm5_sdk.hardware.sam import LED

parakeet = Parakeet()
led = LED()

# Visual feedback during recording
parakeet.start_recording()
led.set_color(255, 0, 0)  # Red = recording

audio_data = parakeet.stop_recording()
led.set_color(0, 255, 0)  # Green = processing

for text in parakeet.transcribe_buffer(audio_data):
    print(f"Transcribed: {text}")
led.turn_off()
```

## License and Credits

The Parakeet module uses:

- NVIDIA NeMo Parakeet models (Apache 2.0 License)
- Silero VAD (MIT License)
- Sherpa-ONNX (Apache 2.0 License)

Part of the Distiller CM5 SDK for Raspberry Pi CM5 platform.
