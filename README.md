# distiller-cm5-sdk

---

## 📁 Project Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/Pamir-AI/distiller-cm5-sdk.git
cd distiller-cm5-sdk
```

---

## ⚙️ Model Download & Build (Recommended)

Run the following script to automatically download all required models and build the package:

> 📝 **If you're using a virtual environment**, make sure to activate it first:
>
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> ```
>
> Then, install the required `build` module:
>
> ```bash
> pip install build
> ````


```bash
chmod +x build.sh
./build.sh                # Build without Whisper (Recommended)
./build.sh --whisper      # Build with Whisper model included
```
---

## 🛠️ Manual Model Download & Build (Optional)

If you prefer manual control, download the following models:

### 🔉 Whisper Model (Optional)

Place all files in:
`src/distiller_cm5_sdk/whisper/models/faster-distil-whisper-small.en/`

* [model.bin](https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/model.bin?download=true)
* [config.json](https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/config.json?download=true)
* [preprocessor\_config.json](https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/preprocessor_config.json?download=true)
* [tokenizer.json](https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/tokenizer.json?download=true)
* [vocabulary.json](https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/vocabulary.json?download=true)

### 🧠 Parakeet Model (ASR + VAD)

Place all files in:
`src/distiller_cm5_sdk/parakeet/models/`

* [encoder.onnx](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/encoder.onnx)
* [decoder.onnx](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/decoder.onnx)
* [joiner.onnx](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/joiner.onnx)
* [tokens.txt](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/tokens.txt)
* [silero\_vad.onnx](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx)

### 🗣️ Piper Model (TTS)

#### 1. Executable

Download to:
`src/distiller_cm5_sdk/piper/`

* [piper\_arm64.tar.gz](https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz)

Then extract and clean up:

```bash
cd src/distiller_cm5_sdk/piper
tar -xvf piper_arm64.tar.gz
rm piper_arm64.tar.gz
```

#### 2. Voice Model Files

Place in:
`src/distiller_cm5_sdk/piper/models/`

* [en\_US-amy-medium.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true)
* [en\_US-amy-medium.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true)

---

### 🔨 Build

If not using `build.sh`, manually build:

```bash
python -m build
```

> 🔧 Make sure `portaudio19-dev` is installed for `pyaudio` support:
>
> ```bash
> sudo apt install portaudio19-dev
> ```

---

## 📥 Install the Package

After building, install the generated wheel file:

```bash
pip install ./dist/distiller_cm5-sdk-0.1.0-py3-none-any.whl
```

> ✅ You should now be able to import and use `distiller_cm5_sdk` in your Python code.


## 🚀 Usage Examples

### 🔊 ASR with Whisper

```python
from distiller_cm5_sdk import whisper

whisper_instance = whisper.Whisper()
for text in whisper_instance.transcribe("speech.wav"):
    print(text)
```

---

### 🧠 ASR + VAD with Parakeet

```python
from distiller_cm5_sdk import parakeet

parakeet_instance = parakeet.Parakeet(vad_silence_duration=0.5)
for text in parakeet_instance.auto_record_and_transcribe():
    print(f"Transcribed: {text}")
```

---

### 🗣️ TTS with Piper

```python
from distiller_cm5_sdk import piper

piper_instance = piper.Piper()
text = "How are you?"

# Option 1: Get path to generated WAV file
wav_path = piper_instance.get_wav_file_path(text)

# Option 2: Directly speak with real-time streaming
piper_instance.speak_stream(text, volume=30)
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

