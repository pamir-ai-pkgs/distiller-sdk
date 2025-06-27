# E-ink Display Module - distiller_cm5_sdk.hardware.eink

E-ink display control module for the Distiller CM5 SDK. Provides high-level Python interface for the 128x250 pixel monochrome e-ink display.

## Features

- **Display Class**: Object-oriented interface for display control
- **PNG Image Display**: Direct PNG file display with automatic conversion
- **Raw Data Display**: Display raw 1-bit image data
- **Display Modes**: Full refresh (high quality) and partial refresh (fast updates)
- **Context Manager**: Automatic resource management
- **Hardware Abstraction**: Clean Python API over C library implementation

## Quick Start

### Basic Usage

```python
from distiller_cm5_sdk.hardware.eink import Display, DisplayMode

# Display a PNG image
with Display() as display:
    display.display_image("my_image.png", DisplayMode.FULL)
    
# Clear the display
with Display() as display:
    display.clear()
```

### Convenience Functions

```python
from distiller_cm5_sdk.hardware.eink import display_png, clear_display

# Quick PNG display
display_png("my_image.png")

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

## Display Specifications

- **Resolution**: 128 × 250 pixels
- **Color Depth**: 1-bit monochrome (black/white)
- **Data Size**: 4000 bytes for raw data
- **Refresh Modes**: Full (slow, high quality) and Partial (fast updates)
- **Image Format**: PNG files must be exactly 128×250 pixels

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

#### display_png(filename, mode=DisplayMode.FULL)
Quick PNG display with automatic resource management.

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

## Image Requirements

### PNG Files
- **Exact Size**: 128 × 250 pixels
- **Color**: Grayscale or RGB (converted to 1-bit)
- **Threshold**: Pixels > 128 brightness = white, ≤ 128 = black

### Raw Data
- **Size**: Exactly 4000 bytes
- **Format**: 1-bit packed data (8 pixels per byte)
- **Layout**: Row-major order, left-to-right, top-to-bottom

## Examples

### Simple PNG Display
```python
from distiller_cm5_sdk.hardware.eink import display_png

# Display image with full refresh
display_png("logo.png")
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

Run the test suite:
```python
from distiller_cm5_sdk.hardware.eink._display_test import run_display_tests
run_display_tests()
```

## Notes

- Display initialization may require sudo permissions for GPIO access
- The display retains images when powered off (e-ink persistence)
- Partial refresh mode is faster but may show ghosting artifacts
- Full refresh mode provides the cleanest image quality 