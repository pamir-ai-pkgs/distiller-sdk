# distiller-cm5-sdk

## Download the Project

cd distiller-cm5-sdk

## Before Packing
Download [model.bin](https://drive.google.com/file/d/1g3ab4ezOehtajecpRaHjy_uBlh6zNJN0/view?usp=sharing) to `src/distiller_cm5_sdk/whisper/models/base/`

Download [Parakeet encoder model file](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/encoder.onnx) to `src/distiller_cm5_sdk/parakeet/models/`
Download [Parakeet decoder model file](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/decoder.onnx) to `src/distiller_cm5_sdk/parakeet/models/`
Download [Parakeet joiner model file](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/joiner.onnx) to `src/distiller_cm5_sdk/parakeet/models/`
Download [Parakeet tokens model file](https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/tokens.txt) to `src/distiller_cm5_sdk/parakeet/models/`

Download [Vad model file](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx) to `src/distiller_cm5_sdk/parakeet/models/`    

Download [Executable file of Piper](https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz) to `src/distiller_cm5_sdk/piper/`

Download [Voice model file of Piper](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true) to `src/distiller_cm5_sdk/piper/models/`

Download [Voice config file of Piper](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true) to `src/distiller_cm5_sdk/piper/models/`

tar -xvf piper_arm64.tar.gz

rm piper_arm64.tar.gz

## Build
python -m build

## Install
pip install ./dist/distiller-cm5-sdk-0.1.0-py3-none-any.whl

note sudo apt install portaudio19-dev need to be installed to use pyaudio

## Usage
### asr
```python
from  distiller_cm5_sdk import whisper
whisper = whisper.Whisper()
for i in whisper.transcribe(r"H:\projects\distiller-cm5-sdk-devs\speech.wav"):
    print(i)
```

### vad+asr
```python
from  distiller_cm5_sdk import parakeet
parakeet_instance = parakeet.Parakeet(vad_silence_duration=0.5)
for text in parakeet_instance.auto_record_and_transcribe():
    print(f"Transcribed: {text}")
```

### tts
```python
from distiller_cm5_sdk import piper
piper = piper.Piper()
text = "How are you"
# Just get wav file path
wav_file_path = piper.get_wav_file_path(text)

# Directly output streaming audio 
piper.speak_stream(text, volume=30)
```
