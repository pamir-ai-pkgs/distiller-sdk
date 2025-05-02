# Audio Module

The Audio module provides a simple interface for interacting with the CM5 audio system. It supports:

- Recording audio to files
- Real-time audio recording via streams
- Audio playback from files
- Audio playback from streams
- Adjusting microphone gain/volume
- Adjusting speaker volume

## Installation

The audio module is part of the CM5 SDK. Make sure you have the proper hardware configuration and required system dependencies:

- ALSA utilities (aplay, arecord)
- Proper device paths for volume control

## Basic Usage

### Initialization

```python
from distiller_cm5_sdk.hardware.audio import Audio

# Initialize with default settings
audio = Audio()

# Initialize with custom settings
audio = Audio(
    sample_rate=44100,
    channels=1,  # mono
    format_type="S24_LE",
    input_device="hw:0,0",
    output_device="plughw:0"
)
```

### Recording to a File

```python
# Record with a fixed duration (5 seconds)
filepath = audio.record("/path/to/recording.wav", duration=5)

# Record until manually stopped
filepath = audio.record("/path/to/recording.wav")
# ... do something else ...
audio.stop_recording()
```

### Stream Recording (Real-time)

```python
# Define a callback function to process audio chunks in real-time
def process_audio(audio_data):
    # Process the audio chunk
    print(f"Received {len(audio_data)} bytes of audio data")

# Create a stop event to control recording
import threading
stop_event = threading.Event()

# Start recording with the callback
thread = audio.stream_record(process_audio, buffer_size=4096, stop_event=stop_event)

# Stop recording after 10 seconds
import time
time.sleep(10)
stop_event.set()
thread.join()
```

### Audio Playback

```python
# Play an audio file
audio.play("/path/to/audio.wav")

# Stop playback
audio.stop_playback()
```

### Stream Playback

```python
# Play from bytes
with open("/path/to/audio.wav", "rb") as f:
    audio_data = f.read()
audio.stream_play(audio_data)

# Play from a file-like object
with open("/path/to/audio.wav", "rb") as f:
    audio.stream_play(f)
```

### Adjusting Microphone Gain

```python
# Set microphone gain (0-100)
audio.set_mic_gain(75)

# Get current microphone gain
current_gain = audio.get_mic_gain()
print(f"Current microphone gain: {current_gain}")
```

### Adjusting Speaker Volume

```python
# Set speaker volume (0-100)
audio.set_speaker_volume(80)

# Get current speaker volume
current_volume = audio.get_speaker_volume()
print(f"Current speaker volume: {current_volume}")
```

### Clean Up

```python
# Clean up resources when done
audio.close()
```

## Advanced Usage

### Custom Sample Rate and Format

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

### Advanced Stream Processing

```python
import numpy as np

# Function to detect audio level
def detect_audio_level(audio_data):
    # Convert audio data to numpy array (assuming S16_LE format)
    # Each sample is 2 bytes (16-bit)
    samples = np.frombuffer(audio_data, dtype=np.int16)
    
    # Calculate RMS level
    rms = np.sqrt(np.mean(samples.astype(np.float32)**2))
    print(f"Audio level: {rms:.2f}")
    
    # Detect if sound is above threshold
    if rms > 10000:
        print("Loud sound detected!")

# Start recording with the processing callback
audio.stream_record(detect_audio_level)
```

## Troubleshooting

If you encounter issues with the audio module, check the following:

1. Ensure the audio hardware is properly connected
2. Verify that ALSA utilities (arecord, aplay) are installed
3. Check if the system paths for volume control exist:
   - `/sys/devices/platform/axi/1000120000.pcie/1f00074000.i2c/i2c-1/1-0018/input_gain`
   - `/sys/devices/platform/axi/1000120000.pcie/1f00074000.i2c/i2c-1/1-0018/volume_level`
4. List available audio devices: `arecord -l` and `aplay -l`
5. Test audio recording manually: `arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 5 test.wav`
6. Test audio playback manually: `aplay -Dplughw:0 test.wav` 