# Installation Guide

This guide covers the installation of the Distiller CM5 SDK on ARM64 Linux systems.

## Prerequisites

Before installing the SDK, ensure your system meets these requirements:

### System Requirements

- **Platform**: Raspberry Pi CM5 or compatible ARM64 system
- **OS**: ARM64 Linux (Debian/Ubuntu-based)
- **Python**: 3.11 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 2GB for full installation with models

### Required Linux Groups

Your user must be a member of these groups:

```bash
sudo usermod -a -G audio,video,spi,gpio,i2c $USER
# Log out and back in for changes to take effect
```

### Required System Packages

```bash
# Update package list
sudo apt-get update

# Install required packages
sudo apt-get install -y \
    python3.11 python3.11-venv python3.11-dev \
    libasound2-dev alsa-utils \
    libcamera-dev rpicam-apps \
    build-essential git curl
```

## Installation Methods

### Method 1: Install from Pre-built Package (Recommended)

1. **Download the latest release**:

```bash
wget https://github.com/Pamir-AI/distiller-cm5-sdk/releases/latest/download/distiller-cm5-sdk_2.0.0_arm64.deb
```

2. **Install the package**:

```bash
sudo dpkg -i distiller-cm5-sdk_2.0.0_arm64.deb
sudo apt-get install -f  # Install any missing dependencies
```

3. **Verify installation**:

```bash
source /opt/distiller-cm5-sdk/activate.sh
python -c "import distiller_cm5_sdk; print('SDK installed successfully!')"
```

### Method 2: Build from Source

1. **Clone the repository**:

```bash
git clone https://github.com/Pamir-AI/distiller-cm5-sdk.git
cd distiller-cm5-sdk
```

2. **Make build scripts executable**:

```bash
chmod +x build.sh build-deb.sh
```

3. **Download AI models**:

```bash
# Standard models (Parakeet, Piper)
./build.sh

# Include Whisper models (larger download)
./build.sh --whisper
```

4. **Build the Debian package**:

```bash
# Standard build
./build-deb.sh

# Include Whisper models
./build-deb.sh whisper

# Clean rebuild
./build-deb.sh clean
```

5. **Install the package**:

```bash
sudo dpkg -i dist/distiller-cm5-sdk_*_arm64.deb
sudo apt-get install -f
```

## Post-Installation Setup

### 1. Activate the SDK Environment

Always activate the SDK environment before use:

```bash
source /opt/distiller-cm5-sdk/activate.sh
```

Add to your shell profile for automatic activation:

```bash
echo "source /opt/distiller-cm5-sdk/activate.sh" >> ~/.bashrc
source ~/.bashrc
```

### 2. Configure E-ink Display (if applicable)

Set the display firmware type:

```bash
# For EPD128x250 (250×128 display) - default
export DISTILLER_EINK_FIRMWARE=EPD128x250

# For EPD240x416 display
export DISTILLER_EINK_FIRMWARE=EPD240x416
```

Make it persistent:

```bash
echo "export DISTILLER_EINK_FIRMWARE=EPD128x250" >> ~/.bashrc
```

### 3. Verify Hardware Access

Test each hardware component:

**Audio**:

```bash
python -m distiller_cm5_sdk.hardware.audio._audio_test
```

**Camera**:

```bash
python -m distiller_cm5_sdk.hardware.camera._camera_unit_test
```

**E-ink Display**:

```bash
python -m distiller_cm5_sdk.hardware.eink._display_test
```

### 4. Test AI Models

**Parakeet ASR**:

```python
from distiller_cm5_sdk.parakeet import Parakeet
asr = Parakeet()
print("Parakeet loaded successfully!")
```

**Piper TTS**:

```python
from distiller_cm5_sdk.piper import Piper
tts = Piper()
tts.speak_stream("Hello, world!")
```

## Integration with Other Projects

### For Python Projects

Add to your Python script:

```python
import sys
sys.path.insert(0, '/opt/distiller-cm5-sdk')

# Now import SDK modules
from distiller_cm5_sdk.hardware.audio import Audio
from distiller_cm5_sdk.parakeet import Parakeet
```

### For System Services

Create a systemd service file:

```ini
[Unit]
Description=My Distiller CM5 Service
After=network.target

[Service]
Type=simple
User=your-username
Environment="PYTHONPATH=/opt/distiller-cm5-sdk"
Environment="LD_LIBRARY_PATH=/opt/distiller-cm5-sdk/lib"
ExecStart=/opt/distiller-cm5-sdk/venv/bin/python /path/to/your/script.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM arm64v8/python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libasound2 \
    libcamera0 \
    && rm -rf /var/lib/apt/lists/*

# Copy SDK
COPY --from=host /opt/distiller-cm5-sdk /opt/distiller-cm5-sdk

# Set environment
ENV PYTHONPATH="/opt/distiller-cm5-sdk:$PYTHONPATH"
ENV LD_LIBRARY_PATH="/opt/distiller-cm5-sdk/lib:$LD_LIBRARY_PATH"

# Your application
WORKDIR /app
COPY . .

CMD ["python", "app.py"]
```

## Package Management with uv

The SDK uses `uv` for package management. After installation:

### Add a New Package

```bash
cd /opt/distiller-cm5-sdk
source activate.sh
uv add requests  # Example package
```

### Update Packages

```bash
uv sync
```

### View Dependency Tree

```bash
uv tree
```

### Remove a Package

```bash
uv remove package-name
```

## Uninstallation

To remove the SDK:

```bash
sudo apt-get remove distiller-cm5-sdk
sudo apt-get purge distiller-cm5-sdk  # Also remove config files
sudo rm -rf /opt/distiller-cm5-sdk    # Remove all files
```

## Upgrading

To upgrade to a newer version:

1. **Uninstall the old version**:

```bash
sudo apt-get remove distiller-cm5-sdk
```

2. **Install the new version**:

```bash
sudo dpkg -i distiller-cm5-sdk_NEW_VERSION_arm64.deb
sudo apt-get install -f
```

## Next Steps

- [Hardware Modules](Hardware-Modules) - Learn to control hardware components
- [AI Modules](AI-Modules) - Use speech recognition and synthesis
- [API Reference](API-Reference) - Explore the complete API
- [Troubleshooting](Troubleshooting) - Solve common issues
