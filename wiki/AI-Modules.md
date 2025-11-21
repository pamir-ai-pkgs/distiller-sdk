# AI Modules

The Distiller SDK includes pre-trained AI models for automatic speech recognition (ASR) and
text-to-speech (TTS) synthesis. These models use CTranslate2 quantization and ONNX Runtime for ARM64.

## Parakeet ASR

Parakeet implements real-time automatic speech recognition with integrated Voice Activity Detection
(VAD) using Sherpa-ONNX models.

### Features

- Real-time streaming ASR
- Voice Activity Detection (VAD)
- Push-to-talk and automatic recording modes
- Low latency transcription
- Uses ARM64 NEON SIMD instructions

### Basic Usage

```python
from distiller_sdk.parakeet import Parakeet

# Use context manager for automatic cleanup
with Parakeet() as asr:
    # Push-to-talk mode
    print("Press Enter to start recording, press again to stop...")
    for text in asr.record_and_transcribe_ptt():
        print(f"Transcribed: {text}")
# Automatic cleanup on exit
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
import time
from distiller_sdk.parakeet import Parakeet

with Parakeet() as asr:
    # Start recording
    asr.start_recording()
    print("Recording... speak now")

    # Let user speak for a few seconds
    time.sleep(5)

    # Stop and get audio data
    audio_data = asr.stop_recording()
    print(f"Recorded {len(audio_data)} bytes")

    # Transcribe the buffer
    for text in asr.transcribe_buffer(audio_data):
        print(f"Transcription: {text}")
# Automatic cleanup
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
from distiller_sdk.parakeet import Parakeet
from distiller_sdk.hardware.eink import Display, DisplayMode

# Use context managers for both ASR and display
with Parakeet() as asr, Display() as display:
    # Display transcriptions on E-ink
    for text in asr.auto_record_and_transcribe():
        # Clear and show text
        display.clear()
        buffer = display.render_text(text, x=5, y=10, scale=1)
        display.display_image(buffer, mode=DisplayMode.FULL)

        # Check for exit command
        if "exit" in text.lower():
            break

    display.clear()
# Automatic cleanup
```

## Piper TTS

Piper implements text-to-speech synthesis with streaming audio output.

### Features

- Natural sounding voices
- Streaming audio synthesis
- Volume control
- Direct speaker output
- WAV file generation

### Basic Usage

```python
from distiller_sdk.piper import Piper

# Use context manager for automatic cleanup
with Piper() as tts:
    # Speak text directly to speakers
    tts.speak_stream("Hello, world!", volume=50)

    # Custom sound card (if needed)
    tts.speak_stream(
        "Testing audio output",
        volume=75,
        sound_card_name="snd_pamir_ai_soundcard"
    )
# Automatic cleanup
```

### Generate WAV Files

```python
from distiller_sdk.piper import Piper
from distiller_sdk.hardware.audio import Audio

with Piper() as tts:
    # Generate and save WAV file
    text = "This is a test of text to speech synthesis"
    wav_path = tts.get_wav_file_path(text)
    print(f"WAV file saved to: {wav_path}")

# Play the generated file
with Audio() as audio:
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
from distiller_sdk.parakeet import Parakeet
from distiller_sdk.piper import Piper

# Use context managers for both ASR and TTS
with Parakeet() as asr, Piper() as tts:
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
# Automatic cleanup
```

## Whisper ASR (Optional)

Whisper implements advanced speech recognition with support for multiple languages and translation.
Note: Whisper models are not included by default due to their size.

### Installation

```bash
# Build SDK with Whisper models
./build.sh --whisper
just build
```

### Features

- Multi-language support
- Translation capabilities
- Higher accuracy than Parakeet
- Larger model sizes
- Higher resource usage

### Basic Usage

```python
from distiller_sdk.whisper import Whisper

# Use context manager for automatic cleanup
with Whisper(model_size="base") as whisper:  # tiny, base, small, medium
    # Transcribe audio file
    for text in whisper.transcribe("audio.wav"):
        print(f"Transcription: {text}")
# Automatic cleanup
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
from distiller_sdk.hardware.audio import Audio
from distiller_sdk.whisper import Whisper

# Use context managers for both audio and Whisper
with Audio() as audio, Whisper(model_size="base") as whisper:
    # Record and transcribe
    audio.record("/tmp/recording.wav", duration=10)

    for text in whisper.transcribe("/tmp/recording.wav"):
        print(f"You said: {text}")
# Automatic cleanup
```

## Combined AI Pipeline

Create sophisticated voice interaction systems using HardwareStatus and context managers:

```python
from distiller_sdk.hardware_status import HardwareStatus
from distiller_sdk.parakeet import Parakeet
from distiller_sdk.piper import Piper
from distiller_sdk.hardware.eink import Display, DisplayMode
from distiller_sdk.hardware.sam import LED
import time

class VoiceAssistant:
    """Voice assistant with automatic hardware detection and resource management."""

    def __init__(self):
        # Check hardware availability
        self.status = HardwareStatus()

        if not self.status.audio_available:
            raise RuntimeError("Audio hardware required for voice assistant")

    def show_status(self, display, led, text, led_color=(0, 0, 255)):
        """Update display and LED status."""
        # Update display (if available)
        if display:
            display.clear()
            buffer = display.render_text(text, x=5, y=10, scale=1)
            display.display_image(buffer, mode=DisplayMode.PARTIAL)

        # Update LED (if available)
        if led:
            r, g, b = led_color
            led.set_rgb_color(0, r, g, b)

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
        """Main assistant loop with context managers."""
        # Use context managers for all resources
        with Parakeet() as asr, \
             Piper() as tts, \
             Display() as display if self.status.eink_available else None, \
             LED(use_sudo=True) as led if self.status.led_available else None:

            self.show_status(display, led, "Ready", (0, 255, 0))  # Green
            tts.speak_stream("Voice assistant ready", volume=50)

            print("Listening... (say 'goodbye' to exit)")

            for text in asr.auto_record_and_transcribe():
                # Show listening status
                self.show_status(display, led, "Processing...", (255, 255, 0))  # Yellow

                # Process command
                response, should_exit = self.process_command(text)

                # Show response
                self.show_status(display, led, response[:30], (0, 0, 255))  # Blue
                tts.speak_stream(response, volume=60)

                if should_exit:
                    break

                # Ready for next command
                self.show_status(display, led, "Listening...", (0, 255, 0))  # Green

            # Final cleanup
            self.show_status(display, led, "OFF", (0, 0, 0))
            if display:
                display.clear()
        # All resources automatically cleaned up

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
/opt/distiller-sdk/
├── src/distiller_sdk/
│   ├── parakeet/models/
│   │   ├── silero_vad.onnx
│   │   ├── encoder-epoch-99-avg-1.onnx
│   │   ├── decoder-epoch-99-avg-1.onnx
│   │   └── joiner-epoch-99-avg-1.onnx
│   ├── piper/models/
│   │   └── en_US-amy-medium.onnx
│   └── whisper/models/  # Optional
│       └── faster-distil-whisper-small.en/
│           ├── model.bin
│           ├── config.json
│           ├── preprocessor_config.json
│           ├── tokenizer.json
│           └── vocabulary.json
```

## Troubleshooting AI Models

### Parakeet Issues

**No transcription output**:

```python
# Check microphone
from distiller_sdk.hardware.audio import Audio
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
ls -la /opt/distiller-sdk/src/distiller_sdk/whisper/models/
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
