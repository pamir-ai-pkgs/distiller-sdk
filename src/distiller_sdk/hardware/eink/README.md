# E-ink Display Module

E-ink display control module for the Distiller SDK. Provides a high-level Python interface
for the 250x128 landscape e-ink display with intelligent image conversion.

## Features

- **250x128 Landscape Display**: Native landscape orientation, no manual rotation needed
- **Multi-Format Image Support**: Display PNG, JPEG, GIF, BMP, TIFF, WebP and more
- **Intelligent Auto-Conversion**: Display any image regardless of size or format
- **Smart Scaling**: Letterbox, crop, or stretch with aspect ratio handling
- **Advanced Dithering**: Floyd-Steinberg and threshold dithering for optimal 1-bit conversion
- **Text Rendering**: Built-in bitmap font with scalable text display
- **Display Modes**: Full refresh (high quality) and partial refresh (fast updates)
- **Context Manager**: Automatic resource cleanup

## Quick Start

```python
from distiller_sdk.hardware.eink import Display, DisplayMode

with Display() as display:
    # Display any image - automatically scaled and dithered
    display.display_image_auto("photo.jpg")

    # Display text
    display.display_text("Hello!", x=10, y=10, scale=3)

    # Clear the display
    display.clear()
```

## Display Specifications

- **Resolution**: 250 x 128 pixels
- **Orientation**: Landscape (width > height)
- **Color Depth**: 1-bit monochrome (black/white)
- **Refresh Modes**: Full (slow, high quality) and Partial (fast updates)

## API Reference

### Display Class

#### Constructor

```python
Display(library_path=None, auto_init=True)
```

- `library_path`: Optional path to shared library
- `auto_init`: Auto-initialize hardware (default: True)

#### display_image_auto(image, mode, scaling, dithering, invert_colors)

Display any image with automatic scaling and dithering. **This is the primary display method.**

```python
display.display_image_auto(
    image,                                    # File path (str) or raw 1-bit data (bytes)
    mode=DisplayMode.FULL,                    # FULL or PARTIAL refresh
    scaling=ScalingMethod.LETTERBOX,          # LETTERBOX, CROP_CENTER, or STRETCH
    dithering=DitheringMethod.FLOYD_STEINBERG,# FLOYD_STEINBERG or THRESHOLD
    invert_colors=False,                      # Swap black/white
)
```

#### display_image(image, mode, scaling, dithering, invert_colors, **kwargs)

Backward-compatible alias for `display_image_auto()`. Accepts and silently ignores
legacy keyword arguments (`rotate`, `flip_horizontal`, `flip_vertical`, `src_width`, `src_height`).

#### display_png_auto(image, mode, scaling, dithering, invert_colors, **kwargs)

Backward-compatible alias for `display_image_auto()`. Accepts and silently ignores
legacy keyword arguments (`rotate`, `flip_horizontal`, `flip_vertical`, `crop_x`, `crop_y`).

#### display_text(text, x, y, scale, invert, mode)

Display text using the built-in bitmap font.

```python
display.display_text(
    text,                    # Text to display
    x=0, y=0,               # Position (0,0 = top-left)
    scale=1,                 # Scale factor (1=6x8, 2=12x16, etc.)
    invert=False,            # True = white text on black
    mode=DisplayMode.FULL,   # Refresh mode
)
```

#### render_text(text, x, y, scale, invert) -> bytes

Render text to a raw 1-bit buffer without sending to display.

#### overlay_text(buffer, text, x, y, scale, invert) -> bytes

Overlay text onto an existing 1-bit image buffer.

#### draw_rect(buffer, x, y, width, height, filled, value) -> bytes

Draw a rectangle on a 1-bit image buffer.

```python
buf = display.render_text("", 0, 0, 1)   # Create blank buffer
buf = display.draw_rect(
    buf,                     # 1-bit image buffer
    x, y,                    # Top-left corner
    width, height,           # Rectangle size
    filled=True,             # Filled or outline only
    value=True,              # True=white, False=black
)
display.display_image_auto(buf)
```

#### clear()

Clear the display (set to white).

#### sleep()

Put display into low-power sleep mode.

#### close()

Release display hardware resources.

#### get_dimensions() -> Tuple[int, int]

Returns display dimensions as `(width, height)` -- `(250, 128)`.

#### convert_png_to_raw(filename) -> bytes

Convert a PNG file to raw 1-bit packed data.

#### is_initialized() -> bool

Check if display hardware is initialized.

### Enums

```python
from distiller_sdk.hardware.eink import DisplayMode, ScalingMethod, DitheringMethod

# Display refresh modes
DisplayMode.FULL           # Slow, high quality
DisplayMode.PARTIAL        # Fast updates

# Scaling methods
ScalingMethod.LETTERBOX    # Maintain aspect ratio, black borders (default)
ScalingMethod.CROP_CENTER  # Fill display, center crop
ScalingMethod.STRETCH      # Stretch to fill (may distort)

# Dithering methods
DitheringMethod.FLOYD_STEINBERG  # High quality (default)
DitheringMethod.THRESHOLD        # Fast binary threshold
```

### Exceptions

```python
from distiller_sdk.hardware.eink import DisplayError

try:
    display.display_image_auto("missing.png")
except DisplayError as e:
    print(f"Display error: {e}")
```

## Examples

### Display an Image

```python
from distiller_sdk.hardware.eink import Display, ScalingMethod

with Display() as display:
    # Any image, any size - auto-scaled to 250x128
    display.display_image_auto("photo.jpg")

    # Crop to fill the display
    display.display_image_auto("banner.png", scaling=ScalingMethod.CROP_CENTER)

    # Invert colors
    display.display_image_auto("logo.png", invert_colors=True)
```

### Text and Drawing

```python
from distiller_sdk.hardware.eink import Display, DisplayMode

with Display() as display:
    # Display text
    display.display_text("Hello CM5!", x=20, y=50, scale=3)

    # Draw shapes on a buffer
    buf = display.render_text("", 0, 0, 1)                    # Blank buffer
    buf = display.draw_rect(buf, 10, 10, 50, 30, filled=True, value=False)   # Black filled
    buf = display.draw_rect(buf, 70, 10, 50, 30, filled=False, value=False)  # Black outline
    display.display_image_auto(buf)
```

### Raw Data

```python
import numpy as np
from distiller_sdk.hardware.eink import Display

width, height = 250, 128
pattern = np.random.randint(0, 2, (height, width), dtype=np.uint8)
packed = np.packbits(pattern, axis=1).tobytes()

with Display() as display:
    display.display_image_auto(packed)
```

## Composer Module

The `composer` submodule provides image processing utilities for building display content:

- **dithering**: Floyd-Steinberg and ordered dithering algorithms
- **image_ops**: Image scaling, cropping, and format conversion
- **text**: Text rendering with font support
- **template_renderer**: Template-based layout rendering

## Testing

```bash
# Unit tests (no hardware required)
python -m distiller_sdk.hardware.eink._display_test

# Interactive hardware diagnostic
python -m distiller_sdk.hardware.eink._diagnostic_test
```

## Notes

- Display initialization may require sudo for GPIO/SPI access
- The display retains images when powered off (e-ink persistence)
- Partial refresh is faster but may show ghosting artifacts
- Full refresh provides the cleanest image quality
