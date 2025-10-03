# Troubleshooting

This guide covers common issues and solutions for the Distiller SDK.

## Installation Issues

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'distiller_sdk'`

**Solution**:

```bash
# Set Python path
export PYTHONPATH="/opt/distiller-sdk:$PYTHONPATH"
source /opt/distiller-sdk/activate.sh

# Verify installation
python -c "import distiller_sdk; print('OK')"
```

### Library Loading Errors

**Problem**: `Error while loading shared libraries: libdistiller_display_sdk_shared.so`

**Solution**:

```bash
# Update library cache
sudo ldconfig

# Set library path
export LD_LIBRARY_PATH="/opt/distiller-sdk/lib:$LD_LIBRARY_PATH"

# Check library dependencies
ldd /opt/distiller-sdk/lib/libdistiller_display_sdk_shared.so
```

### Permission Denied

**Problem**: `Permission denied` when accessing hardware

**Solution**:

```bash
# Add user to required groups
sudo usermod -a -G audio,video,spi,gpio,i2c $USER

# Log out and log in for changes to take effect
# OR use newgrp temporarily
newgrp audio
newgrp video
```

## Audio Issues

### No Sound Output

**Problem**: No audio from speakers

**Solution**:

```bash
# Check audio devices
aplay -l

# Test speakers
speaker-test -t wav -c 2

# Set volume
amixer sset 'Speaker' 80%

# In Python
from distiller_sdk.hardware.audio import Audio
Audio.set_speaker_volume_static(80)
```

### Recording Silent

**Problem**: Audio recording produces silent files

**Solution**:

```bash
# Check recording devices
arecord -l

# Test microphone
arecord -d 5 test.wav && aplay test.wav

# Adjust gain
amixer sset 'Mic' 90%

# In Python
from distiller_sdk.hardware.audio import Audio
Audio.set_mic_gain_static(90)
```

### ALSA Errors

**Problem**: `ALSA lib pcm.c:8545:(snd_pcm_open) Unknown PCM`

**Solution**:

```bash
# List available PCMs
aplay -L
arecord -L

# Check ALSA configuration
cat /proc/asound/cards
cat /proc/asound/pcm
```

## Camera Issues

### Camera Not Found

**Problem**: `RuntimeError: Camera initialization failed`

**Solution**:

```bash
# Check camera detection
v4l2-ctl --list-devices
ls -la /dev/video*

# Enable camera in config
sudo raspi-config
# Navigate to Interface Options > Camera > Enable

# Check camera module connection
vcgencmd get_camera
```

### rpicam-apps Missing

**Problem**: `rpicam-still: command not found`

**Solution**:

```bash
# Install rpicam-apps
sudo apt-get update
sudo apt-get install -y rpicam-apps

# Test camera
rpicam-still -o test.jpg
```

### Permission Denied on /dev/video

**Problem**: Cannot access camera device

**Solution**:

```bash
# Add to video group
sudo usermod -a -G video $USER
logout  # Then log in again

# Check permissions
ls -la /dev/video*
```

## E-ink Display Issues

### Display Not Responding

**Problem**: E-ink display shows nothing

**Solution**:

```bash
# Check SPI is enabled
ls -la /dev/spi*
lsmod | grep spi

# Enable SPI
sudo raspi-config
# Navigate to Interface Options > SPI > Enable

# Test with Python
from distiller_sdk.hardware.eink import Display
with Display() as d:
    d.clear()
```

### Wrong Display Dimensions

**Problem**: The image appears distorted or cropped

**Solution**:

```python
from distiller_sdk.hardware.eink import set_default_firmware, FirmwareType

# For 250×128 display
set_default_firmware(FirmwareType.EPD128x250)

# For 240×416 display
set_default_firmware(FirmwareType.EPD240x416)

# Verify setting
from distiller_sdk.hardware.eink import get_default_firmware
print(get_default_firmware())
```

### Ghosting on Display

**Problem**: The previous image is visible after update

**Solution**:

```python
from distiller_sdk.hardware.eink import Display, DisplayMode

with Display() as display:
    # Use full refresh to clear ghosting
    display.display_image("image.png", mode=DisplayMode.FULL)

    # Clear display completely
    display.clear()
```

## LED Issues

### LEDs Not Lighting

**Problem**: LED commands have no effect

**Solution**:

```bash
# Check LED sysfs
ls -la /sys/class/leds/

# Test with sudo
sudo python3 -c "
from distiller_sdk.hardware.sam import LED
led = LED(use_sudo=True)
led.set_rgb_color(0, 255, 0, 0)
"

# Fix permissions (alternative to sudo)
sudo chmod 666 /sys/class/leds/*/brightness
sudo chmod 666 /sys/class/leds/*/multi_intensity
```

### LED Permission Denied

**Problem**: `PermissionError` accessing LED sysfs

**Solution**:

```python
# Use sudo flag
from distiller_sdk.hardware.sam import LED
led = LED(use_sudo=True)

# OR setup udev rules for permanent fix
# Create /etc/udev/rules.d/99-leds.rules:
# SUBSYSTEM=="leds", MODE="0666"
# Then reload: sudo udevadm control --reload-rules
```

## AI Model Issues

### Parakeet Not Transcribing

**Problem**: No transcription output from Parakeet

**Solution**:

```python
# Check audio input
from distiller_sdk.hardware.audio import Audio
audio = Audio()
audio.record("test.wav", duration=3)
audio.play("test.wav")  # Verify recording

# Adjust VAD sensitivity
from distiller_sdk.parakeet import Parakeet
asr = Parakeet(vad_threshold=0.3)  # More sensitive
```

### Piper No Audio Output

**Problem**: TTS produces no sound

**Solution**:

```python
# Test with different volume
from distiller_sdk.piper import Piper
tts = Piper()
tts.speak_stream("Test", volume=80)

# Specify sound card
tts.speak_stream("Test", sound_card_name="snd_pamir_ai_soundcard")

# Generate WAV file to test
wav_path = tts.get_wav_file_path("Test")
print(f"WAV file: {wav_path}")
```

### Whisper Model Not Found

**Problem**: `FileNotFoundError` for Whisper models

**Solution**:

```bash
# Download Whisper models
cd /path/to/distiller-sdk
./build.sh --whisper

# Rebuild package with Whisper
./build-deb.sh whisper

# Verify models exist
ls -la /opt/distiller-sdk/src/distiller_sdk/whisper/models/
```

### Out of Memory

**Problem**: `MemoryError` or system freeze when using AI models

**Solution**:

```python
# Use smaller models
from distiller_sdk.whisper import Whisper
whisper = Whisper(model_size="tiny")  # Smallest model

# Free memory after use
asr.cleanup()
del asr

# Monitor memory
import psutil
print(f"Available RAM: {psutil.virtual_memory().available / 1024**3:.1f} GB")
```

## General Debugging

### Check SDK Installation

```bash
# Verify package installation
dpkg -l | grep distiller-sdk
dpkg -L distiller-sdk | head -20

# Check Python environment
which python
python --version
pip list | grep distiller
```

### Test Individual Components

```bash
# Test each hardware module
python -m distiller_sdk.hardware.audio._audio_test
python -m distiller_sdk.hardware.camera._camera_unit_test
python -m distiller_sdk.hardware.eink._display_test
```

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now SDK calls will show debug output
from distiller_sdk.hardware.audio import Audio
audio = Audio()  # Will show debug messages
```

### System Information

```bash
# Check system details
uname -a
cat /etc/os-release
free -h
df -h

# Check Python paths
python -c "import sys; print('\n'.join(sys.path))"

# Check environment
env | grep -E "(PYTHON|LD_LIBRARY|DISTILLER)"
```

## Getting Help

If issues persist:

1. Check [GitHub Issues](https://github.com/Pamir-AI/distiller-sdk/issues)
2. Provide system information:

   ```bash
   uname -a
   python --version
   dpkg -l | grep distiller-sdk
   ```

3. Include error messages and traceback
4. Describe the steps to reproduce the issue

## Next Steps

- [Development Guide](Development-Guide) - Contributing to SDK
- [API Reference](API-Reference) - Complete API documentation
