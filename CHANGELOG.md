# Changelog

## [Unreleased] - 2026-02-08

### E-ink Display SDK

#### Added

- **Fast refresh mode** (`DisplayMode.FAST`): ~1.5s refresh using temperature register override (100°C). The SSD1680 controller selects faster waveforms when it believes the panel is at high temperature. Uses update command `0xC7` instead of `0xF7`.

- **Turbo refresh mode** (`DisplayMode.TURBO`): ~1s refresh using 90°C temperature override plus dual-RAM write (zeros to secondary buffer `0x26`). Note: manufacturer warns older panel revisions may not support this.

- **Partial refresh base map** (`Display.set_partial_base_map()`): Writes the base image to both primary (`0x24`) and secondary (`0x26`) RAM buffers before partial refresh. This prevents ghosting artifacts caused by undefined state in the secondary buffer, which the SSD1680 uses to diff changed pixels.

- **4-level grayscale display** (`Display.display_grayscale()`): New method for displaying images with 4 gray levels (black, dark gray, light gray, white) on the GDEY0213B74 panel. Implemented as a standalone Python driver using direct SPI/GPIO access with:
  - Custom 159-byte LUT waveform from GxEPD2 library
  - Special init sequence (analog/digital block control, VCOM, VGH, VSH/VSL voltages)
  - Dual-RAM encoding: each pixel is 2 bits split across RAM `0x24` and `0x26`
  - New file: `grayscale_4g.py`
  - New dependency: `gpiod>=2.4.0`

#### Changed

- **BT.601 grayscale conversion**: RGB-to-grayscale formula changed from simple average `(R+G+B)/3` to perceptual luminance weighting `(77*R + 150*G + 29*B) >> 8`. This matches human eye sensitivity (green ~59%, red ~30%, blue ~11%) and produces more natural grayscale from color photos. Affects all 1-bit display modes.

- **Firmware trait signature**: `DisplayFirmware::get_update_sequence()` parameter changed from `is_partial: bool` to `mode: DisplayMode` to support 4 refresh modes.

#### API Summary

```python
from distiller_sdk.hardware.eink import Display, DisplayMode

with Display() as display:
    # 1-bit modes (with dithering)
    display.display_image_auto("img.png", mode=DisplayMode.FULL, rotate=90)     # ~2s, best quality
    display.display_image_auto("img.png", mode=DisplayMode.FAST, rotate=90)     # ~1.5s
    display.display_image_auto("img.png", mode=DisplayMode.TURBO, rotate=90)    # ~1s, fastest

    # Partial refresh (set base map first)
    display.set_partial_base_map(base_image_bytes)
    display.display_image(updated_bytes, mode=DisplayMode.PARTIAL)

    # 4-level grayscale (separate method, no dithering needed)
    display.display_grayscale("img.png", rotate=90)
```

### Files Changed

**Rust library** (`src/distiller_sdk/hardware/eink/lib/src/`):
- `protocol.rs` — Added `DisplayMode::Fast` (2), `DisplayMode::Turbo` (3), `init_fast()`, `write_secondary_ram()`
- `firmware/mod.rs` — Added `get_fast_init_sequence()`, `get_fast_update_sequence()`, `get_secondary_ram_command()` default trait methods; changed `get_update_sequence` signature
- `firmware/epd128x250.rs` — Updated `get_update_sequence()` for 4 modes
- `firmware/epd240x416.rs` — Updated `get_update_sequence()` signature
- `display.rs` — Fast/Turbo init in `display_image_raw()`, added `set_partial_base_map()`
- `ffi.rs` — Mode 2/3 parsing in all FFI functions, added `display_set_partial_base_map()` export
- `image.rs` — BT.601 grayscale formula

**Python** (`src/distiller_sdk/hardware/eink/`):
- `display.py` — Added `DisplayMode.FAST/TURBO`, `set_partial_base_map()`, `display_grayscale()`, `display_grayscale()` convenience function
- `grayscale_4g.py` — New file: standalone 4-gray driver using spidev + gpiod
