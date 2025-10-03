# Audio Module

The Audio module provides a comprehensive interface for interacting with the CM5 audio system. It
supports:

- Recording audio to files with configurable duration
- Real-time audio recording via streams with callbacks
- Audio playback from files
- Audio playback from streams (bytes or file objects)
- Adjusting microphone gain/volume (instance and static methods)
- Adjusting speaker volume (instance and static methods)
- System configuration checking
- Recording and playback status monitoring

## Overview

The Audio class provides both instance and static methods for audio control. Static methods are
particularly useful when you need to adjust audio settings without creating an Audio instance, such
as when integrating with other modules like Parakeet ASR or Piper TTS.

## Prerequisites

- Python 3.11+
- ALSA utilities (aplay, arecord)
- Proper device paths for volume control (for CM5 hardware)
- PyAudio (for advanced features)
- NumPy (for audio processing)

## Installation

The audio module is part of the Distiller SDK. Ensure the SDK is properly installed:

```bash
sudo dpkg -i distiller-sdk_*_arm64.deb
source /opt/distiller-sdk/activate.sh
```

Required system packages:

```bash
sudo apt-get install alsa-utils portaudio19-dev
```

## Quick Start

### Basic Audio Operations

```python
from distiller_sdk.hardware.audio import Audio

# Initialize audio
audio = Audio()

# Record 5 seconds of audio
audio.record("recording.wav", duration=5)

# Play the recording
audio.play("recording.wav")

# Adjust volume
audio.set_speaker_volume(50)
audio.set_mic_gain(75)

# Clean up
audio.close()
```

### Using Static Methods (No Instance Required)

```python
from distiller_sdk.hardware.audio import Audio

# Set audio levels without creating an instance
Audio.set_mic_gain_static(85)
Audio.set_speaker_volume_static(50)

# Get current levels
mic_level = Audio.get_mic_gain_static()
speaker_level = Audio.get_speaker_volume_static()

print(f"Mic: {mic_level}%, Speaker: {speaker_level}%")
```

## API Reference

### Class: Audio

#### `__init__(sample_rate=48000, channels=2, format_type="S16_LE", input_device="hw:0,0", output_device="plughw:0", auto_check_config=True)`

Initialize the Audio object.

**Parameters:**

- `sample_rate` (int): Sample rate in Hz (default: 48000)
- `channels` (int): Number of audio channels (1=mono, 2=stereo, default: 2)
- `format_type` (str): Audio format type (default: "S16_LE")
  - Common formats: "S16_LE", "S24_LE", "S32_LE"
- `input_device` (str): Audio input device (default: "hw:0,0")
- `output_device` (str): Audio output device (default: "plughw:0")
- `auto_check_config` (bool): Whether to automatically check system configuration (default: True)

**Example:**

```python
# High-quality audio setup
audio = Audio(
    sample_rate=96000,
    channels=2,
    format_type="S24_LE"
)
```

#### `check_system_config() -> bool`

Check if the system is properly configured for audio use.

**Returns:**

- bool: True if configuration is valid

**Raises:**

- `AudioError`: If configuration is invalid

**Example:**

```python
audio = Audio(auto_check_config=False)
if audio.check_system_config():
    print("Audio system ready")
```

#### `record(filepath: str, duration: Optional[float] = None) -> str`

Record audio to a file.

**Parameters:**

- `filepath` (str): Path where the audio file will be saved
- `duration` (float, optional): Recording duration in seconds. If None, records until
  `stop_recording()` is called

**Returns:**

- str: Path to the recorded file

**Example:**

```python
# Record with fixed duration
filepath = audio.record("recording.wav", duration=5)

# Record until manually stopped
audio.record("recording.wav")
time.sleep(10)
audio.stop_recording()
```

#### `stop_recording()`

Stop an ongoing recording.

**Example:**

```python
audio.record("long_recording.wav")
# ... do other things ...
audio.stop_recording()
```

#### `stream_record(callback: Callable[[bytes], None], buffer_size: int = 4096, stop_event: Optional[threading.Event] = None) -> threading.Thread`

Record audio with real-time streaming to a callback function.

**Parameters:**

- `callback` (Callable): Function to process audio chunks
- `buffer_size` (int): Size of audio buffer in bytes (default: 4096)
- `stop_event` (threading.Event, optional): Event to signal recording stop

**Returns:**

- threading.Thread: The recording thread

**Example:**

```python
import threading

def process_audio(audio_data):
    print(f"Received {len(audio_data)} bytes")

stop_event = threading.Event()
thread = audio.stream_record(process_audio, buffer_size=4096, stop_event=stop_event)

# Stop after 10 seconds
time.sleep(10)
stop_event.set()
thread.join()
```

#### `play(filepath: str)`

Play an audio file.

**Parameters:**

- `filepath` (str): Path to the audio file to play

**Example:**

```python
audio.play("sound.wav")
# Playback happens in background thread
```

#### `stop_playback()`

Stop ongoing audio playback.

**Example:**

```python
audio.play("long_audio.wav")
time.sleep(2)
audio.stop_playback()  # Stop early
```

#### `stream_play(audio_data: Union[bytes, BinaryIO], format_type: Optional[str] = None, sample_rate: Optional[int] = None, channels: Optional[int] = None)`

Play audio from bytes or a file-like object.

**Parameters:**

- `audio_data` (bytes or BinaryIO): Audio data or file object
- `format_type` (str, optional): Override format type
- `sample_rate` (int, optional): Override sample rate
- `channels` (int, optional): Override channel count

**Example:**

```python
# Play from bytes
with open("audio.wav", "rb") as f:
    audio_data = f.read()
audio.stream_play(audio_data)

# Play from file object
with open("audio.wav", "rb") as f:
    audio.stream_play(f)
```

#### `set_mic_gain(gain: int)`

Set the microphone gain/volume.

**Parameters:**

- `gain` (int): Gain value (0-100)

**Example:**

```python
audio.set_mic_gain(75)
```

#### `get_mic_gain() -> int`

Get the current microphone gain.

**Returns:**

- int: Current gain value (0-100)

**Example:**

```python
gain = audio.get_mic_gain()
print(f"Microphone gain: {gain}%")
```

#### `set_mic_gain_static(gain: int) -> int` (Static Method)

Set microphone gain without creating an Audio instance.

**Parameters:**

- `gain` (int): Gain value (0-100)

**Returns:**

- int: The set gain value

**Example:**

```python
from distiller_sdk.hardware.audio import Audio
Audio.set_mic_gain_static(85)
```

#### `get_mic_gain_static() -> int` (Static Method)

Get microphone gain without creating an Audio instance.

**Returns:**

- int: Current gain value (0-100)

**Example:**

```python
from distiller_sdk.hardware.audio import Audio
gain = Audio.get_mic_gain_static()
```

#### `set_speaker_volume(volume: int)`

Set the speaker volume.

**Parameters:**

- `volume` (int): Volume level (0-100)

**Example:**

```python
audio.set_speaker_volume(60)
```

#### `get_speaker_volume() -> int`

Get the current speaker volume.

**Returns:**

- int: Current volume level (0-100)

**Example:**

```python
volume = audio.get_speaker_volume()
print(f"Speaker volume: {volume}%")
```

#### `set_speaker_volume_static(volume: int) -> int` (Static Method)

Set speaker volume without creating an Audio instance.

**Parameters:**

- `volume` (int): Volume level (0-100)

**Returns:**

- int: The set volume value

**Example:**

```python
from distiller_sdk.hardware.audio import Audio
Audio.set_speaker_volume_static(50)
```

#### `get_speaker_volume_static() -> int` (Static Method)

Get speaker volume without creating an Audio instance.

**Returns:**

- int: Current volume level (0-100)

**Example:**

```python
from distiller_sdk.hardware.audio import Audio
volume = Audio.get_speaker_volume_static()
```

#### `is_recording() -> bool`

Check if audio is currently being recorded.

**Returns:**

- bool: True if recording is in progress

**Example:**

```python
if audio.is_recording():
    print("Recording in progress")
    audio.stop_recording()
```

#### `is_playing() -> bool`

Check if audio is currently playing.

**Returns:**

- bool: True if playback is in progress

**Example:**

```python
if audio.is_playing():
    print("Playback in progress")
    audio.stop_playback()
```

#### `close()`

Clean up audio resources.

**Example:**

```python
audio.close()
```

### Static Helper Methods

#### `is_raspberry_pi() -> bool` (Static Method)

Check if the current system is a Raspberry Pi.

**Returns:**

- bool: True if running on Raspberry Pi

**Example:**

```python
if Audio.is_raspberry_pi():
    print("Running on Raspberry Pi")
```

#### `has_audio_controls() -> bool` (Static Method)

Check if the system has PamirAI soundcard controls.

**Returns:**

- bool: True if hardware controls are available

**Example:**

```python
if Audio.has_audio_controls():
    print("Hardware volume controls available")
else:
    print("Using software volume control")
```

## Advanced Usage

### Working with Different Audio Formats

```python
# Initialize with custom parameters
audio = Audio(
    sample_rate=96000,  # 96kHz high-resolution audio
    channels=2,         # stereo
    format_type="S32_LE"  # 32-bit signed little-endian
)

# Record high-quality audio
audio.record("/path/to/high_quality.wav", duration=10)
```

### Real-time Audio Processing

```python
import numpy as np
import threading

class AudioProcessor:
    def __init__(self, audio):
        self.audio = audio
        self.recording = False

    def process_audio_chunk(self, audio_data):
        """Process audio data in real-time"""
        # Convert to numpy array (S16_LE format)
        samples = np.frombuffer(audio_data, dtype=np.int16)

        # Calculate RMS level
        rms = np.sqrt(np.mean(samples.astype(np.float32)**2))

        # Simple voice activity detection
        if rms > 5000:
            print(f"Voice detected! Level: {rms:.0f}")

        # You could also:
        # - Apply filters
        # - Detect specific frequencies
        # - Save chunks to file
        # - Send to speech recognition

    def start_monitoring(self, duration=None):
        """Start audio monitoring"""
        stop_event = threading.Event()

        thread = self.audio.stream_record(
            self.process_audio_chunk,
            buffer_size=2048,
            stop_event=stop_event
        )

        if duration:
            time.sleep(duration)
            stop_event.set()
            thread.join()

        return thread, stop_event

# Usage
audio = Audio()
processor = AudioProcessor(audio)
thread, stop_event = processor.start_monitoring(duration=10)
```

### Volume Normalization

```python
from distiller_sdk.hardware.audio import Audio

class VolumeController:
    """Automatic volume control based on environment"""

    def __init__(self):
        self.audio = Audio()
        self.target_level = 50

    def normalize_mic_for_environment(self):
        """Adjust mic gain based on ambient noise"""
        # Record a sample
        self.audio.record("ambient_sample.wav", duration=2)

        # Analyze the sample (simplified)
        # In practice, you'd analyze the audio data

        # Adjust mic gain accordingly
        if self.is_noisy_environment():
            Audio.set_mic_gain_static(85)
            print("Noisy environment - increased mic gain")
        else:
            Audio.set_mic_gain_static(60)
            print("Quiet environment - normal mic gain")

    def is_noisy_environment(self):
        # Implement noise detection logic
        return False  # Placeholder

controller = VolumeController()
controller.normalize_mic_for_environment()
```

### Audio Format Conversion

```python
import wave
import subprocess

def convert_audio_format(input_file, output_file, target_rate=16000, target_channels=1):
    """Convert audio file to different format using ffmpeg"""

    cmd = [
        "ffmpeg", "-i", input_file,
        "-ar", str(target_rate),  # Sample rate
        "-ac", str(target_channels),  # Channels
        "-f", "wav",  # Output format
        output_file
    ]

    subprocess.run(cmd, capture_output=True)
    print(f"Converted {input_file} to {output_file}")
    print(f"  Rate: {target_rate}Hz, Channels: {target_channels}")

# Record in high quality
audio = Audio(sample_rate=48000, channels=2)
audio.record("high_quality.wav", duration=5)

# Convert for speech recognition (typically needs 16kHz mono)
convert_audio_format("high_quality.wav", "speech_ready.wav", 16000, 1)
```

## Integration Examples

### With ASR Modules

```python
from distiller_sdk.hardware.audio import Audio
from distiller_sdk.parakeet import Parakeet

# Set optimal audio levels for speech recognition
Audio.set_mic_gain_static(85)

# Record audio
audio = Audio()
audio.record("speech.wav", duration=5)

# Transcribe
parakeet = Parakeet()
for text in parakeet.transcribe("speech.wav"):
    print(f"Transcribed: {text}")

audio.close()
parakeet.cleanup()
```

### With TTS Module

```python
from distiller_sdk.hardware.audio import Audio
from distiller_sdk.piper import Piper

# Set speaker volume for TTS
Audio.set_speaker_volume_static(60)

# Initialize TTS
piper = Piper()

# Speak with controlled volume
piper.speak_stream("Hello from the audio system!", volume=50)
```

### Audio Monitoring System

```python
from distiller_sdk.hardware.audio import Audio
import threading
import time

class AudioMonitor:
    def __init__(self):
        self.audio = Audio()
        self.alert_threshold = 10000
        self.monitoring = False

    def audio_callback(self, data):
        """Process audio and detect events"""
        import numpy as np
        samples = np.frombuffer(data, dtype=np.int16)
        level = np.max(np.abs(samples))

        if level > self.alert_threshold:
            print(f"ALERT: Loud sound detected! Level: {level}")
            # Could trigger notifications, logging, etc.

    def start(self):
        """Start monitoring"""
        self.monitoring = True
        self.stop_event = threading.Event()

        self.thread = self.audio.stream_record(
            self.audio_callback,
            buffer_size=4096,
            stop_event=self.stop_event
        )

        print("Audio monitoring started...")

    def stop(self):
        """Stop monitoring"""
        if self.monitoring:
            self.stop_event.set()
            self.thread.join()
            self.monitoring = False
            print("Audio monitoring stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
        self.audio.close()

# Use as context manager
with AudioMonitor() as monitor:
    print("Monitoring for 10 seconds...")
    time.sleep(10)
```

## Troubleshooting

### No Audio Devices Found

If you encounter "No audio input devices detected":

1. List available devices:

```bash
arecord -l
aplay -l
```

2. Check ALSA configuration:

```bash
cat /proc/asound/cards
```

3. Verify audio permissions:

```bash
groups | grep audio
# If not in audio group:
sudo usermod -a -G audio $USER
# Log out and back in
```

### Volume Control Not Working

If volume control methods don't work:

1. Check if hardware controls exist:

```python
from distiller_sdk.hardware.audio import Audio

if Audio.has_audio_controls():
    print("Hardware controls available")
else:
    print("No hardware controls - using software volume")
```

2. Verify control paths (CM5 hardware only):

```bash
ls -la /sys/devices/platform/axi/1000120000.pcie/1f00074000.i2c/i2c-1/1-0018/
```

3. Try using ALSA mixer:

```bash
alsamixer
```

### Recording Issues

If recording fails or produces no sound:

1. Test recording manually:

```bash
arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 5 test.wav
aplay test.wav
```

2. Check microphone gain:

```python
from distiller_sdk.hardware.audio import Audio
print(f"Current mic gain: {Audio.get_mic_gain_static()}%")
Audio.set_mic_gain_static(85)  # Increase gain
```

3. Verify input device:

```python
audio = Audio(input_device="hw:0,0")  # Try different devices
```

### Playback Issues

If audio playback doesn't work:

1. Test speakers:

```bash
speaker-test -t sine -f 440 -l 1
```

2. Check volume level:

```python
from distiller_sdk.hardware.audio import Audio
Audio.set_speaker_volume_static(70)
```

3. Try different output device:

```python
audio = Audio(output_device="plughw:0")  # or "hw:0,0"
```

### Performance Issues

For better performance:

1. Use appropriate buffer sizes:

```python
# Smaller buffer = lower latency but more CPU
audio.stream_record(callback, buffer_size=2048)

# Larger buffer = higher latency but less CPU
audio.stream_record(callback, buffer_size=8192)
```

2. Choose appropriate sample rates:

```python
# Lower sample rate for speech
audio = Audio(sample_rate=16000)  # Good for speech

# Higher sample rate for music
audio = Audio(sample_rate=48000)  # Good for music
```

## Performance Considerations

- **CPU Usage**: Audio recording/playback typically uses 1-5% CPU
- **Memory**: Minimal memory usage (~10MB for typical operations)
- **Latency**: Stream recording has ~50ms latency with default buffer size
- **Sample Rates**: Higher rates increase CPU usage and file sizes

## Best Practices

1. **Resource Management**:
   - Always call `close()` when done
   - Use context managers where possible
   - Stop recordings/playback before closing

2. **Volume Settings**:
   - Use static methods for global settings
   - Set appropriate levels for your environment
   - Consider automatic gain control for varying conditions

3. **Audio Quality**:
   - Match sample rates to your use case
   - Use appropriate formats (S16_LE for most cases)
   - Consider mono for speech, stereo for music

## License and Credits

The Audio module is part of the Distiller SDK for Raspberry Pi CM5 platform. Uses ALSA for
low-level audio operations.
