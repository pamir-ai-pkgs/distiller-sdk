# AI Modules

The Distiller CM5 SDK includes pre-trained AI models for automatic speech recognition (ASR) and
text-to-speech (TTS) synthesis. These models are optimized for edge deployment on ARM64 platforms.

## Parakeet ASR

Parakeet provides real-time automatic speech recognition with integrated Voice Activity Detection
(VAD) using Sherpa-ONNX models.

### Features

- Real-time streaming ASR
- Voice Activity Detection (VAD)
- Push-to-talk and automatic recording modes
- Low latency transcription
- Optimized for ARM64

### Basic Usage

```python
from distiller_cm5_sdk.parakeet import Parakeet

# Initialize
asr = Parakeet()

# Push-to-talk mode
print("Press Enter to start recording, press again to stop...")
for text in asr.record_and_transcribe_ptt():
    print(f"Transcribed: {text}")

# Cleanup
asr.cleanup()
```

### Automatic Recording with VAD

```python
# Automatically detect speech and transcribe
print("Speak when ready (VAD enabled)...")
for text in asr.auto_record_and_transcribe():
    print(f"You said: {text}")
    if "stop" in text.lower():
        break
```

### Manual Recording Control

```python
# Start recording
asr.start_recording()
print("Recording... speak now")

# Let user speak for a few seconds
import time
time.sleep(5)

# Stop and get audio data
audio_data = asr.stop_recording()
print(f"Recorded {len(audio_data)} bytes")

# Transcribe the buffer
for text in asr.transcribe_buffer(audio_data):
    print(f"Transcription: {text}")
```

### Advanced Configuration

```python
# Custom VAD parameters (if needed)
asr = Parakeet(
    vad_threshold=0.5,  # Adjust sensitivity
    min_speech_duration=0.3,  # Minimum speech length
    max_silence_duration=0.5  # Maximum pause in speech
)
```

### Integration Example

```python
from distiller_cm5_sdk.parakeet import Parakeet
from distiller_cm5_sdk.hardware.eink import Display

asr = Parakeet()
display = Display()

# Display transcriptions on E-ink
for text in asr.auto_record_and_transcribe():
    # Clear and show text
    display.clear()
    buffer = display.render_text(text, x=5, y=10, scale=1)
    display.display_image(buffer)

    # Check for exit command
    if "exit" in text.lower():
        break

display.clear()
asr.cleanup()
```

## Piper TTS

Piper provides high-quality text-to-speech synthesis with streaming audio output.

### Features

- Natural sounding voices
- Streaming audio synthesis
- Volume control
- Direct speaker output
- WAV file generation

### Basic Usage

```python
from distiller_cm5_sdk.piper import Piper

# Initialize
tts = Piper()

# Speak text directly to speakers
tts.speak_stream("Hello, world!", volume=50)

# Custom sound card (if needed)
tts.speak_stream(
    "Testing audio output",
    volume=75,
    sound_card_name="snd_pamir_ai_soundcard"
)
```

### Generate WAV Files

```python
# Generate and save WAV file
text = "This is a test of text to speech synthesis"
wav_path = tts.get_wav_file_path(text)
print(f"WAV file saved to: {wav_path}")

# Play the generated file
from distiller_cm5_sdk.hardware.audio import Audio
audio = Audio()
audio.play(wav_path)
```

### Voice Management

```python
# List available voices
voices = tts.list_voices()
for voice in voices:
    print(f"Voice: {voice['name']}")
    print(f"Language: {voice['language']}")
    print(f"Quality: {voice['quality']}")

# Note: Currently, only 'en_US-amy-medium' is included
```

### Integration with ASR

```python
from distiller_cm5_sdk.parakeet import Parakeet
from distiller_cm5_sdk.piper import Piper

asr = Parakeet()
tts = Piper()

# Echo back what user says
print("Say something...")
for text in asr.auto_record_and_transcribe():
    print(f"You said: {text}")

    # Speak it back
    response = f"I heard you say: {text}"
    tts.speak_stream(response, volume=60)

    if "goodbye" in text.lower():
        tts.speak_stream("Goodbye!", volume=70)
        break

asr.cleanup()
```

## Whisper ASR (Optional)

Whisper provides advanced speech recognition with support for multiple languages and translation.
Note: Whisper models are not included by default due to their size.

### Installation

```bash
# Build SDK with Whisper models
./build.sh --whisper
./build-deb.sh whisper
```

### Features

- Multi-language support
- Translation capabilities
- Higher accuracy than Parakeet
- Larger model sizes
- Higher resource usage

### Basic Usage

```python
from distiller_cm5_sdk.whisper import Whisper

# Initialize with model size
whisper = Whisper(model_size="base")  # tiny, base, small, medium

# Transcribe audio file
text = whisper.transcribe_file("audio.wav")
print(f"Transcription: {text}")

# With language detection
result = whisper.transcribe_file(
    "audio.wav",
    language=None  # Auto-detect
)
print(f"Detected language: {result['language']}")
print(f"Text: {result['text']}")
```

### Translation

```python
# Translate to English
result = whisper.transcribe_file(
    "spanish_audio.wav",
    language="es",
    task="translate"  # Translates to English
)
print(f"Translation: {result}")
```

### Real-Time Processing

```python
from distiller_cm5_sdk.hardware.audio import Audio
from distiller_cm5_sdk.whisper import Whisper

audio = Audio()
whisper = Whisper(model_size="base")

# Record and transcribe
audio.record("/tmp/recording.wav", duration=10)
text = whisper.transcribe_file("/tmp/recording.wav")
print(f"You said: {text}")
```

## Combined AI Pipeline

Create sophisticated voice interaction systems:

```python
from distiller_cm5_sdk.parakeet import Parakeet
from distiller_cm5_sdk.piper import Piper
from distiller_cm5_sdk.hardware.eink import Display, DisplayMode
from distiller_cm5_sdk.hardware.sam import LED
import time

class VoiceAssistant:
    def __init__(self):
        self.asr = Parakeet()
        self.tts = Piper()
        self.display = Display()
        self.led = LED(use_sudo=True)

    def show_status(self, text, led_color=(0, 0, 255)):
        """Update display and LED status."""
        # Update display
        self.display.clear()
        buffer = self.display.render_text(text, x=5, y=10, scale=1)
        self.display.display_image(buffer, mode=DisplayMode.PARTIAL)

        # Update LED
        r, g, b = led_color
        self.led.set_rgb_color(0, r, g, b)

    def process_command(self, text):
        """Process voice commands."""
        text_lower = text.lower()

        if "time" in text_lower:
            current_time = time.strftime("%I:%M %p")
            response = f"The time is {current_time}"

        elif "date" in text_lower:
            current_date = time.strftime("%B %d, %Y")
            response = f"Today is {current_date}"

        elif "hello" in text_lower:
            response = "Hello! How can I help you?"

        elif "goodbye" in text_lower or "exit" in text_lower:
            response = "Goodbye! Have a great day!"
            return response, True  # Exit flag

        else:
            response = f"You said: {text}"

        return response, False

    def run(self):
        """Main assistant loop."""
        self.show_status("Ready", (0, 255, 0))  # Green
        self.tts.speak_stream("Voice assistant ready", volume=50)

        print("Listening... (say 'goodbye' to exit)")

        for text in self.asr.auto_record_and_transcribe():
            # Show listening status
            self.show_status("Processing...", (255, 255, 0))  # Yellow

            # Process command
            response, should_exit = self.process_command(text)

            # Show response
            self.show_status(response[:30], (0, 0, 255))  # Blue
            self.tts.speak_stream(response, volume=60)

            if should_exit:
                break

            # Ready for next command
            self.show_status("Listening...", (0, 255, 0))  # Green

        # Cleanup
        self.show_status("OFF", (0, 0, 0))
        self.display.clear()
        self.led.turn_off_all()
        self.asr.cleanup()

# Run assistant
assistant = VoiceAssistant()
assistant.run()
```

## Performance Considerations

### Parakeet

- **Latency**: ~100-200 ms for VAD, real-time transcription
- **Memory**: ~200MB RAM
- **CPU**: ~10-20% on CM5 during active transcription
- **Best for**: Real-time applications, voice commands

### Piper

- **Latency**: ~50-100 ms to start speaking
- **Memory**: ~150MB RAM
- **CPU**: ~15-25% during synthesis
- **Best for**: Natural sounding speech output

### Whisper

- **Latency**: 1-5 seconds depending on model size
- **Memory**: 500 MB - 2 GB depending on model
- **CPU**: 50-90% during transcription
- **Best for**: High accuracy, multi-language support

## Model Files

Models are located in:

```
/opt/distiller-cm5-sdk/
├── src/distiller_cm5_sdk/
│   ├── parakeet/models/
│   │   ├── silero_vad.onnx
│   │   ├── encoder-epoch-99-avg-1.onnx
│   │   ├── decoder-epoch-99-avg-1.onnx
│   │   └── joiner-epoch-99-avg-1.onnx
│   ├── piper/models/
│   │   └── en_US-amy-medium.onnx
│   └── whisper/models/  # Optional
│       ├── tiny.bin
│       ├── base.bin
│       └── small.bin
```

## Troubleshooting AI Models

### Parakeet Issues

**No transcription output**:

```python
# Check microphone
from distiller_cm5_sdk.hardware.audio import Audio
audio = Audio()
audio.record("test.wav", duration=3)
# Play back to verify recording
audio.play("test.wav")
```

**VAD not detecting speech**:

```python
# Adjust VAD sensitivity
asr = Parakeet(vad_threshold=0.3)  # Lower = more sensitive
```

### Piper Issues

**No audio output**:

```bash
# Check speaker volume
amixer sset 'Speaker' 80%
speaker-test -t wav -c 2
```

**Distorted speech**:

```python
# Reduce volume
tts.speak_stream("Test", volume=30)  # Lower volume
```

### Whisper Issues

**Model not found**:

```bash
# Ensure models are downloaded
./build.sh --whisper
ls -la /opt/distiller-cm5-sdk/src/distiller_cm5_sdk/whisper/models/
```

**Out of memory**:

```python
# Use smaller model
whisper = Whisper(model_size="tiny")  # Uses less RAM
```

## Next Steps

- [API Reference](API-Reference) - Complete API documentation
- [Hardware Modules](Hardware-Modules) - Integrate with hardware
- [Troubleshooting](Troubleshooting) - Common issues and solutions
