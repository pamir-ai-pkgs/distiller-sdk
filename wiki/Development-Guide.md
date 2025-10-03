# Development Guide

This guide covers contributing to and developing with the Distiller SDK.

## Development Environment Setup

### Prerequisites

```bash
# Install development tools
sudo apt-get install -y \
    build-essential \
    python3.11-dev \
    git \
    curl \
    libasound2-dev \
    libcamera-dev

# Clone repository
git clone https://github.com/Pamir-AI/distiller-sdk.git
cd distiller-sdk
```

### Environment Activation

```bash
# Always activate the SDK environment first
source /opt/distiller-sdk/activate.sh

# OR if developing locally
cd distiller-sdk
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Package Management with uv

The SDK uses `uv` for modern Python package management.

### Adding Dependencies

```bash
cd /opt/distiller-sdk
source activate.sh

# Add a new package
uv add numpy  # Production dependency
uv add --dev pytest  # Development dependency

# Update lock file
uv sync
```

### Updating Dependencies

```bash
# Update all packages
uv sync

# Update specific package
uv add package-name@latest

# View dependency tree
uv tree
```

### Managing Virtual Environment

```bash
# The virtual environment is managed by uv at .venv/
ls -la .venv/

# Recreate environment
rm -rf .venv
uv venv
uv sync
```

## Code Structure

```
distiller-sdk/
├── src/distiller_sdk/
│   ├── hardware/           # Hardware interfaces
│   │   ├── audio/         # Audio recording/playback
│   │   ├── camera/        # Camera control
│   │   ├── eink/          # E-ink display driver
│   │   │   └── lib/       # Native C library
│   │   └── sam/           # LED control
│   ├── parakeet/          # ASR with VAD
│   ├── piper/             # TTS engine
│   └── whisper/           # Whisper ASR (optional)
├── tests/                  # Test files
├── build.sh               # Model download script
├── build-deb.sh           # Debian package builder
└── pyproject.toml         # Project configuration
```

## Adding New Hardware Support

### 1. Create Module Structure

```bash
mkdir -p src/distiller_sdk/hardware/new_device
touch src/distiller_sdk/hardware/new_device/__init__.py
touch src/distiller_sdk/hardware/new_device/_new_device_test.py
```

### 2. Implement Hardware Interface

```python
# src/distiller_sdk/hardware/new_device/__init__.py

class NewDevice:
    """Hardware interface for new device."""

    def __init__(self):
        """Initialize device."""
        self._device = None
        self._initialize()

    def _initialize(self):
        """Setup hardware connection."""
        # Hardware initialization code
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Release resources."""
        if self._device:
            # Cleanup code
            self._device = None
```

### 3. Add Test File

```python
# src/distiller_sdk/hardware/new_device/_new_device_test.py

def test_basic():
    """Test basic functionality."""
    from . import NewDevice

    device = NewDevice()
    # Test operations
    device.close()
    print("Test passed!")

if __name__ == "__main__":
    test_basic()
```

### 4. Update Hardware Imports

```python
# src/distiller_sdk/hardware/__init__.py
from .new_device import NewDevice

__all__ = [..., "NewDevice"]
```

## Building Native Libraries

### E-ink Display Library

```bash
cd src/distiller_sdk/hardware/eink/lib

# Clean build
make clean
make

# Verify library
ldd libdistiller_display_sdk_shared.so

# Test
cd ../
python _display_test.py
```

### Adding New Native Code

1. Create C source files in the appropriate module
2. Update Makefile:

```makefile
# Example Makefile
CC = gcc
CFLAGS = -fPIC -O2 -Wall
LDFLAGS = -shared

TARGET = libnew_hardware.so
SOURCES = new_hardware.c utils.c
OBJECTS = $(SOURCES:.c=.o)

$(TARGET): $(OBJECTS)
    $(CC) $(LDFLAGS) -o $@ $^

%.o: %.c
    $(CC) $(CFLAGS) -c $< -o $@

clean:
    rm -f $(OBJECTS) $(TARGET)
```

## Testing

### Running Hardware Tests

```bash
# Individual module tests
python -m distiller_sdk.hardware.audio._audio_test
python -m distiller_sdk.hardware.camera._camera_unit_test
python -m distiller_sdk.hardware.eink._display_test

# Run all tests (if using pytest)
pytest tests/
```

### Writing Tests

```python
# tests/test_hardware.py
import pytest
import os
from distiller_sdk.hardware.audio import Audio

def test_audio_initialization():
    """Test audio system initialization."""
    audio = Audio()
    assert audio is not None
    audio.close()

@pytest.mark.hardware
def test_recording():
    """Test audio recording (requires hardware)."""
    audio = Audio()
    audio.record("/tmp/test.wav", duration=1)
    # Verify file exists
    assert os.path.exists("/tmp/test.wav")
    audio.close()
```

## Code Style

### Linting with Ruff

```bash
cd /opt/distiller-sdk

# Check code
ruff check src/

# Format code
ruff format src/

# Auto-fix issues
ruff check --fix src/
```

### Configuration

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]  # Line too long
```

### Code Conventions

- Use type hints for public APIs
- Provide docstrings for all public methods
- Follow the context manager pattern for resources
- Use descriptive variable names
- Keep functions focused and small

## Building Packages

### Download Models

```bash
# Standard models
./build.sh

# Include Whisper
./build.sh --whisper

# Custom model directory
./build.sh --model-dir /custom/path
```

### Build Debian Package

```bash
# Standard build
./build-deb.sh

# Clean rebuild
./build-deb.sh clean

# Include Whisper
./build-deb.sh whisper

# Test package
sudo dpkg -i dist/distiller-sdk_*.deb
```

### Package Contents

```bash
# View package contents
dpkg -c dist/distiller-sdk_*.deb

# Extract without installing
dpkg -x dist/distiller-sdk_*.deb /tmp/extract
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# SDK will now show debug messages
from distiller_sdk.hardware.audio import Audio
audio = Audio()
```

### Using GDB for Native Code

```bash
# Debug native library
gdb python
(gdb) run -c "from distiller_sdk.hardware.eink import Display; d = Display()"
(gdb) break function_name
(gdb) continue
```

### Memory Profiling

```python
import tracemalloc
tracemalloc.start()

# Your code here
from distiller_sdk.parakeet import Parakeet
asr = Parakeet()

# Get memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024**2:.1f} MB")
print(f"Peak: {peak / 1024**2:.1f} MB")
tracemalloc.stop()
```

## Contributing

### 1. Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/distiller-sdk.git
cd distiller-sdk
git remote add upstream https://github.com/Pamir-AI/distiller-sdk.git
```

### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Follow the code style guidelines
- Add tests for new features
- Update documentation
- Test on actual hardware

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
# Create Pull Request on GitHub
```

## Release Process

### Version Bumping

```bash
# Update version in pyproject.toml
# Update debian/changelog
# Tag release
git tag -a v2.0.1 -m "Release version 2.0.1"
git push origin v2.0.1
```

### Building Release

```bash
# Clean build
./build-deb.sh clean

# Upload to releases
gh release create v2.0.1 dist/*.deb
```

## Best Practices

### Hardware Interfaces

- Always provide context manager support
- Handle resource cleanup properly
- Provide both low-level and convenience methods
- Document hardware requirements

### Error Handling

- Use descriptive error messages
- Handle hardware disconnection gracefully
- Provide fallback options where possible
- Log errors for debugging

### Performance

- Use native libraries for compute-intensive tasks
- Implement streaming for audio/video
- Cache model loading
- Profile memory usage

### Documentation

- Keep README files updated
- Provide usage examples
- Document error conditions
- Include troubleshooting tips

## Getting Help

- [GitHub Issues](https://github.com/Pamir-AI/distiller-sdk/issues)
- [Wiki](https://github.com/Pamir-AI/distiller-sdk/wiki)
- Review existing code for patterns
- Test on actual CM5 hardware

## Next Steps

- [API Reference](API-Reference) - Complete API documentation
- [Hardware Modules](Hardware-Modules) - Hardware interfaces
- [AI Modules](AI-Modules) - AI capabilities
