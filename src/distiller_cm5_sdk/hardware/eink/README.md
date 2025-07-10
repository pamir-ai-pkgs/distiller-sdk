# E-ink Display Module - distiller_cm5_sdk.hardware.eink

E-ink display control module for the Distiller CM5 SDK. Provides high-level Python interface for multiple e-ink display types with intelligent image conversion capabilities.

## Features

- **Multi-Display Support**: Supports EPD128x250 and EPD240x416 displays with automatic detection
- **Intelligent PNG Auto-Conversion**: Display any PNG image regardless of size or format
- **Smart Scaling**: Multiple scaling algorithms (letterbox, crop, stretch) with aspect ratio handling
- **Advanced Dithering**: Floyd-Steinberg and simple threshold dithering for optimal 1-bit conversion
- **Display Class**: Object-oriented interface for display control
- **PNG Image Display**: Direct PNG file display with automatic conversion
- **Raw Data Display**: Display raw 1-bit image data
- **Display Modes**: Full refresh (high quality) and partial refresh (fast updates)
- **Context Manager**: Automatic resource management
- **Hardware Abstraction**: Clean Python API over C library implementation

## Quick Start

### Auto-Conversion (Recommended)

```python
from distiller_cm5_sdk.hardware.eink import display_png_auto, ScalingMethod

# Display ANY PNG image - automatically converted to fit your display
display_png_auto("large_photo.jpg")  # Works with any size!
display_png_auto("wide_banner.png", scaling=ScalingMethod.CROP_CENTER)
display_png_auto("portrait.png", scaling=ScalingMethod.LETTERBOX)

# Enhanced display_png with auto-conversion
display_png("any_image.png", auto_convert=True)
```

### Basic Usage

```python
from distiller_cm5_sdk.hardware.eink import Display, DisplayMode

# Display a PNG image (exact display size required)
with Display() as display:
    display.display_image("my_image.png", DisplayMode.FULL)
    
# Display any PNG with auto-conversion
with Display() as display:
    display.display_png_auto("any_image.png", DisplayMode.FULL)
    
# Clear the display
with Display() as display:
    display.clear()
```

### Convenience Functions

```python
from distiller_cm5_sdk.hardware.eink import display_png, clear_display

# Quick PNG display (exact size required)
display_png("my_image.png")

# Quick PNG display with auto-conversion
display_png("any_image.png", auto_convert=True)

# Quick clear
clear_display()
```

### Display Class Usage

```python
from distiller_cm5_sdk.hardware.eink import Display, DisplayMode, DisplayError

try:
    # Initialize display
    display = Display()
    
    # Display PNG with full refresh
    display.display_image("image.png", DisplayMode.FULL)
    
    # Display raw 1-bit data with partial refresh
    raw_data = bytes([0xFF] * 4000)  # 4000 bytes for 128x250 pixels
    display.display_image(raw_data, DisplayMode.PARTIAL)
    
    # Get display info
    width, height = display.get_dimensions()
    print(f"Display: {width}x{height}")
    
    # Clear and sleep
    display.clear()
    display.sleep()
    
except DisplayError as e:
    print(f"Display error: {e}")
finally:
    display.close()
```

## Auto-Conversion System

The intelligent auto-conversion system allows you to display **any PNG image** regardless of size, format, or color depth. The system automatically:

- **Detects your display type** (EPD128x250 or EPD240x416)
- **Scales images intelligently** using multiple algorithms
- **Converts color formats** (RGB, RGBA, grayscale, palette → 1-bit)
- **Applies optimal dithering** for best visual quality

### Scaling Methods

```python
from distiller_cm5_sdk.hardware.eink import ScalingMethod

ScalingMethod.LETTERBOX     # Maintain aspect ratio, add black borders (default)
ScalingMethod.CROP_CENTER   # Scale to fill display completely, center crop
ScalingMethod.STRETCH       # Stretch to fill display (may distort image)
```

### Dithering Methods

```python
from distiller_cm5_sdk.hardware.eink import DitheringMethod

DitheringMethod.FLOYD_STEINBERG  # High quality dithering (default)
DitheringMethod.SIMPLE           # Fast threshold conversion
```

### Auto-Conversion Examples

```python
from distiller_cm5_sdk.hardware.eink import display_png_auto, ScalingMethod, DitheringMethod

# Display a large photo with letterboxing (maintains aspect ratio)
display_png_auto("vacation_photo_4000x3000.png")

# Display a wide banner with center cropping (fills display)
display_png_auto("banner_1920x400.png", scaling=ScalingMethod.CROP_CENTER)

# Display with simple dithering for faster processing
display_png_auto("image.png", dithering=DitheringMethod.SIMPLE)

# Combine scaling and dithering options
display_png_auto("portrait.png", 
                scaling=ScalingMethod.LETTERBOX,
                dithering=DitheringMethod.FLOYD_STEINBERG)
```

## Display Specifications

### Supported Display Types
- **EPD128x250**: 128 × 250 pixels (16:25 aspect ratio)
- **EPD240x416**: 240 × 416 pixels (15:26 aspect ratio)
- **Auto-Detection**: Firmware automatically detected at runtime

### Display Properties
- **Color Depth**: 1-bit monochrome (black/white)
- **Refresh Modes**: Full (slow, high quality) and Partial (fast updates)
- **Auto-Conversion**: Supports PNG images of any size and format

### Image Requirements

#### Auto-Conversion (Recommended)
- **Any PNG size**: From 64×64 to 4000×4000+ pixels
- **Any color format**: RGB, RGBA, grayscale, palette, 1-bit
- **Automatic processing**: No manual resizing or conversion needed

#### Manual/Legacy Mode
- **Exact Size**: Must match display dimensions (128×250 or 240×416)
- **Color**: Grayscale or RGB (converted to 1-bit)
- **Threshold**: Pixels > 128 brightness = white, ≤ 128 = black

## API Reference

### Display Class

#### Constructor
```python
Display(library_path=None, auto_init=True)
```
- `library_path`: Optional path to shared library
- `auto_init`: Auto-initialize hardware (default: True)

#### Methods

##### display_image(image, mode=DisplayMode.FULL)
Display an image on the screen.
- `image`: PNG file path (str) or raw 1-bit data (bytes)
- `mode`: DisplayMode.FULL or DisplayMode.PARTIAL

##### display_png_auto(image_path, mode=DisplayMode.FULL, scaling=ScalingMethod.LETTERBOX, dithering=DitheringMethod.FLOYD_STEINBERG) -> bool
Display any PNG image with automatic conversion to display specifications.
- `image_path`: Path to PNG file (any size, any format)
- `mode`: Display refresh mode
- `scaling`: How to scale the image to fit display
- `dithering`: Dithering method for 1-bit conversion
- Returns: True if successful

##### clear()
Clear the display (set to white).

##### get_dimensions() -> Tuple[int, int]
Returns display dimensions as (width, height).

##### convert_png_to_raw(filename) -> bytes
Convert PNG file to raw 1-bit data.

##### sleep()
Put display to sleep for power saving.

##### close()
Cleanup display resources.

### Display Modes

```python
from distiller_cm5_sdk.hardware.eink import DisplayMode

DisplayMode.FULL      # Full refresh - slow, high quality
DisplayMode.PARTIAL   # Partial refresh - fast updates
```

### Convenience Functions

#### display_png(filename, mode=DisplayMode.FULL, rotate=False, auto_convert=False, scaling=ScalingMethod.LETTERBOX, dithering=DitheringMethod.FLOYD_STEINBERG)
Quick PNG display with automatic resource management.
- `filename`: Path to PNG file
- `mode`: Display refresh mode
- `rotate`: If True, rotate landscape PNG (250x128) to portrait (128x250)
- `auto_convert`: If True, automatically convert any PNG to display format
- `scaling`: How to scale the image (only used with auto_convert)
- `dithering`: Dithering method (only used with auto_convert)

#### display_png_auto(filename, mode=DisplayMode.FULL, scaling=ScalingMethod.LETTERBOX, dithering=DitheringMethod.FLOYD_STEINBERG)
Quick auto-conversion PNG display with automatic resource management.
- `filename`: Path to PNG file (any size, any format)
- `mode`: Display refresh mode
- `scaling`: How to scale the image to fit display
- `dithering`: Dithering method for 1-bit conversion

#### clear_display()
Quick display clear with automatic resource management.

#### get_display_info() -> dict
Returns display specifications dictionary.

### Exceptions

#### DisplayError
Raised for display-related errors:
- Library loading failures
- Hardware initialization failures
- Invalid image formats or sizes
- Display operation failures

### Raw Data Requirements
- **Size**: Exactly (width × height) ÷ 8 bytes
- **Format**: 1-bit packed data (8 pixels per byte)
- **Layout**: Row-major order, left-to-right, top-to-bottom

## Examples

### Auto-Conversion Examples (Recommended)

```python
from distiller_cm5_sdk.hardware.eink import display_png_auto, ScalingMethod, DitheringMethod

# Display any PNG image - fully automatic
display_png_auto("my_photo.png")

# Display with specific scaling
display_png_auto("wide_image.png", scaling=ScalingMethod.CROP_CENTER)

# Display with fast dithering
display_png_auto("image.png", dithering=DitheringMethod.SIMPLE)

# Use enhanced display_png with auto-conversion
display_png("any_image.png", auto_convert=True)
```

### Simple PNG Display (Legacy)
```python
from distiller_cm5_sdk.hardware.eink import display_png

# Display image with exact display dimensions
display_png("logo_128x250.png")
```

### Raw Data Generation
```python
import numpy as np
from distiller_cm5_sdk.hardware.eink import Display

# Create a test pattern
width, height = 128, 250
image_2d = np.random.randint(0, 2, (height, width), dtype=np.uint8)

# Pack to 1-bit format
packed_data = np.packbits(image_2d, axis=1).tobytes()

# Display
with Display() as display:
    display.display_image(packed_data)
```

### Error Handling
```python
from distiller_cm5_sdk.hardware.eink import Display, DisplayError

try:
    with Display() as display:
        display.display_image("nonexistent.png")
except DisplayError as e:
    print(f"Failed to display image: {e}")
```

## Hardware Details

The display module wraps a C library implementation that interfaces directly with:
- SPI communication for display data
- GPIO pins for control signals
- Hardware-specific display controller

The C library is automatically loaded from common locations:
- `./lib/libdistiller_display_sdk_shared.so`
- `./build/libdistiller_display_sdk_shared.so`
- System library paths

## Testing

### Auto-Conversion Test Suite
Test the new auto-conversion functionality:
```bash
# Test auto-conversion with various image formats and sizes
python src/distiller_cm5_sdk/hardware/eink/test_auto_display.py

# Comprehensive auto-conversion test
python test_auto_conversion.py
```

### Legacy Test Suite
Run the original test suite:
```python
from distiller_cm5_sdk.hardware.eink._display_test import run_display_tests
run_display_tests()
```

## Notes

- **Auto-conversion is recommended** for most use cases - no need to manually resize images
- Display initialization may require sudo permissions for GPIO access
- The display retains images when powered off (e-ink persistence)
- Partial refresh mode is faster but may show ghosting artifacts
- Full refresh mode provides the cleanest image quality
- **Backward compatibility**: All existing code continues to work unchanged
- **Multi-display support**: Automatically detects and adapts to your display type