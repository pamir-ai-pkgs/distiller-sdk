# distiller-cm5-sdk

## Download the Project

cd distiller-cm5-sdk

## Before Packing
Download [model.bin](https://drive.google.com/file/d/1g3ab4ezOehtajecpRaHjy_uBlh6zNJN0/view?usp=sharing) to `distiller-cm5-sdk/whisper/models/base/`

Download [Executable file of Piper](https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz) to `distiller-cm5-sdk/piper/`

Download [Voice model file of Piper](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true) to `distiller-cm5-sdk/piper/models/`

Download [Voice config file of Piper](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true) to `distiller-cm5-sdk/piper/models/`

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
from  distiller-cm5-sdk import whisper
whisper = whisper.Whisper()
for i in whisper.transcribe(r"H:\projects\distiller-cm5-sdk-devs\speech.wav"):
    print(i)
```

### tts
```python
from distiller-cm5-sdk import piper
piper = piper.Piper()
text = "How are you"
# Just get wav file path
wav_file_path = piper.get_wav_file_path(text)

# Directly output streaming audio 
piper.speak_stream(text, volume=30)
```
