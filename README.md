# Distiller CM5 SDK

A comprehensive Python SDK for the Distiller CM5 platform, providing hardware control, audio processing, computer vision, and AI capabilities.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- ARM64 Linux system (or cross-compilation setup)
- Required system packages (see Installation section)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Pamir-AI/distiller-cm5-sdk.git
   cd distiller-cm5-sdk
   ```

2. **Download models and build:**
   ```bash
   chmod +x build.sh
   ./build.sh                    # Download models (excluding Whisper)
   ./build.sh --whisper          # Download models including Whisper
   ```

3. **Build Debian package:**
   ```bash
   chmod +x build-deb.sh
   ./build-deb.sh                # Build Debian package
   ./build-deb.sh --whisper      # Build with Whisper model included
   ./build-deb.sh --clean        # Clean build
   ```

4. **Install the package:**
   ```bash
   sudo dpkg -i dist/distiller-cm5-sdk_*_arm64.deb
   sudo apt-get install -f       # Install any missing dependencies
   ```

5. **Activate the SDK environment:**
   ```bash
   source /opt/distiller-cm5-sdk/activate.sh
   ```

## 📦 What's Included

The SDK provides:

- **Hardware Control**: E-ink display, camera, audio, LEDs
- **AI Models**: Whisper (ASR), Parakeet (ASR + VAD), Piper (TTS)
- **Audio Processing**: Real-time audio capture and playback
- **Computer Vision**: OpenCV-based camera operations
- **Native Libraries**: ARM64-optimized Rust library for e-ink display

## 🛠️ Build Process

The build process includes:

1. **Model Download**: Downloads required AI models (Whisper, Parakeet, Piper)
2. **Rust Library Build**: Cross-compiles ARM64 shared library for e-ink display
3. **Debian Package**: Creates a self-contained Debian package

### Build Scripts

- `build.sh`: Downloads model files
- `build-deb.sh`: Builds the complete Debian package

### Manual Model Download

If you prefer manual control, download the following models:

#### 🔉 Whisper Model (Optional)

Place all files in:
`src/distiller_cm5_sdk/whisper/models/faster-distil-whisper-small.en/`

* [model.bin](https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/model.bin?download=true)
* [config.json](https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/config.json?download=true)
* [preprocessor_config.json](https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/preprocessor_config.json?download=true)
* [tokenizer.json](https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/tokenizer.json?download=true)
* [vocabulary.json](https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/vocabulary.json?download=true)

#### 🧠 Parakeet Model (ASR + VAD)

Place all files in:
`src/distiller_cm5_sdk/parakeet/models/`

* [encoder.onnx](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/encoder.onnx)
* [decoder.onnx](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/decoder.onnx)
* [joiner.onnx](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/joiner.onnx)
* [tokens.txt](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/tokens.txt)
* [silero_vad.onnx](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx)

#### 🗣️ Piper Model (TTS)

##### 1. Executable

Download to:
`src/distiller_cm5_sdk/piper/`

* [piper_arm64.tar.gz](https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz)

Then extract and clean up:

```bash
cd src/distiller_cm5_sdk/piper
tar -xvf piper_arm64.tar.gz
rm piper_arm64.tar.gz
```

##### 2. Voice Model Files

Place in:
`src/distiller_cm5_sdk/piper/models/`

* [en_US-amy-medium.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true)
* [en_US-amy-medium.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true)

> 🔧 Make sure `portaudio19-dev` is installed for `pyaudio` support:
>
> ```bash
> sudo apt install portaudio19-dev
> ```

## 📥 Installation

### Debian Package Installation (Recommended)

The Debian package installs everything to `/opt/distiller-cm5-sdk` as a self-contained environment:

```bash
# Build the Debian package
./build-deb.sh

# Install the package
sudo dpkg -i dist/distiller-cm5-sdk_*_arm64.deb
sudo apt-get install -f  # Install any missing dependencies

# Activate the SDK environment
source /opt/distiller-cm5-sdk/activate.sh
```

> ✅ You should now be able to import and use `distiller_cm5_sdk` in your Python code.

## 📦 Package Management

### Removing the Package

```bash
# Remove the package (keeps configuration files)
sudo apt remove distiller-cm5-sdk

# Completely remove the package and all files
sudo apt purge distiller-cm5-sdk

# Clean up any remaining dependencies
sudo apt autoremove
```

### Updating the Package

```bash
# Update the package
sudo apt update
sudo apt upgrade distiller-cm5-sdk
```

### Package Information

```bash
# View package information
dpkg -l | grep distiller-cm5-sdk

# View package contents
dpkg -L distiller-cm5-sdk

# View package status
dpkg -s distiller-cm5-sdk
```

## 🚀 Usage Examples

### 🔊 ASR with Whisper

```python
from distiller_cm5_sdk import whisper

whisper_instance = whisper.Whisper()
for text in whisper_instance.transcribe("speech.wav"):
    print(text)
```

### 🧠 ASR + VAD with Parakeet

```python
from distiller_cm5_sdk import parakeet

parakeet_instance = parakeet.Parakeet(vad_silence_duration=0.5)
for text in parakeet_instance.auto_record_and_transcribe():
    print(f"Transcribed: {text}")
```

### 🗣️ TTS with Piper

```python
from distiller_cm5_sdk import piper

piper_instance = piper.Piper()
text = "How are you?"

# Option 1: Get path to generated WAV file
wav_path = piper_instance.get_wav_file_path(text)
```

---

### 📺 E-Ink Display

```python
from distiller_cm5_sdk.hardware.eink import EinkDriver, load_and_convert_image

# Initialize the e-ink display
display = EinkDriver()
display.initialize()

# Display an image
image_data = load_and_convert_image("path/to/image.jpg", threshold=128, dither=True)
display.display_image(image_data)

# Clear the display
display.clear_display()

# Clean up resources
display.cleanup()
```

---

## 📎 Notes

* Whisper model is optional and will only be downloaded if `--whisper` is passed to `build.sh`.

