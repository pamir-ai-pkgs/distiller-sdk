# Distiller SDK Wiki

Welcome to the Distiller SDK documentation! This SDK provides comprehensive hardware control and
AI capabilities for multiple ARM64 platforms.

## Quick Links

- [Installation Guide](Installation) - Get started with the SDK
- [Hardware Modules](Hardware-Modules) - Control hardware components
- [AI Modules](AI-Modules) - Speech modules (deprecated — see distiller-cc)
- [API Reference](API-Reference) - Complete API documentation
- [Troubleshooting](Troubleshooting) - Common issues and solutions
- [Development Guide](Development-Guide) - Development workflow

## SDK Overview

The Distiller SDK is a Python package that provides:

### Hardware Control

- **Audio** - ALSA-based recording and playback with hardware volume control
- **Camera** - rpicam-apps-based image/video capture
- **E-ink Display** - Native driver for EPD128x250 (native 128×250, mounted 250×128) and EPD240x416 displays
- **RGB LEDs** - Kernel-based animation modes with Linux LED trigger support

## Key Features

- **System-wide Installation** - Installed at `/opt/distiller-sdk/`
- **uv Package Management** - Modern Python dependency management
- **Native Libraries** - Optimized C libraries for hardware control
- **Comprehensive API** - Pythonic interfaces for all hardware

## Requirements

- **Platform**: Raspberry Pi CM5, Radxa Zero 3/3W, ArmSom CM5 IO (experimental), or compatible ARM64 system
- **OS**: ARM64 Linux (Debian/Ubuntu-based)
- **Python**: 3.11 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 2GB for full installation

## Quick Start Example

```python
from distiller_sdk.hardware.audio import Audio
from distiller_sdk.hardware.eink import Display, DisplayMode
from distiller_sdk.hardware.camera import Camera
from distiller_sdk.hardware.sam import LED

# Initialize hardware
audio = Audio()
display = Display()
camera = Camera()
led = LED(use_sudo=True)

# Capture and display image
led.set_rgb_color(0, 0, 0, 255)  # Blue — capturing
image = camera.capture_image("/tmp/photo.jpg")

display.display_image_auto("/tmp/photo.jpg", mode=DisplayMode.FULL)

led.set_rgb_color(0, 0, 255, 0)  # Green — done

# Cleanup
camera.close()
audio.close()
display.close()
led.turn_off_all()
```

## Documentation Structure

This wiki is organized into the following sections:

1. **[Installation](Installation)** - Step-by-step installation instructions
2. **[Hardware Modules](Hardware-Modules)** - Detailed hardware component documentation
3. **[AI Modules](AI-Modules)** - Speech modules (deprecated — see distiller-cc >= 6.0.0)
4. **[API Reference](API-Reference)** - Complete API documentation with examples
5. **[Troubleshooting](Troubleshooting)** - Solutions to common problems
6. **[Development Guide](Development-Guide)** - Contributing and development workflow

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/pamir-ai-pkgs/distiller-sdk/issues)
- **Source Code**: [GitHub Repository](https://github.com/pamir-ai-pkgs/distiller-sdk)
- **License**: See [LICENSE](https://github.com/pamir-ai-pkgs/distiller-sdk/blob/main/LICENSE)
