"""
4-Gray Grayscale Display Driver for GDEY0213B74 (SSD1680 controller).

This module implements 4-level grayscale display using direct SPI/GPIO access,
bypassing the Rust library which only supports 1-bit modes. The SSD1680 controller
supports 4 gray levels by combining two 1-bit RAM buffers (0x24 and 0x26) with
a custom Look-Up Table (LUT) waveform.

Gray level encoding (after inversion for transfer):
    RAM 0x26 bit | RAM 0x24 bit | Display
    -------------|--------------|--------
    0            | 0            | Black
    0            | 1            | Dark Gray
    1            | 0            | Light Gray
    1            | 1            | White

LUT and init sequence from GxEPD2_4G library (GxEPD2_213_GDEY0213B74.cpp)
by Jean-Marc Zingg, based on Good Display reference code.

Usage:
    from distiller_sdk.hardware.eink.grayscale_4g import display_4gray

    # Display any image with 4-level grayscale
    display_4gray("/path/to/image.png")

    # Or with options
    display_4gray("/path/to/image.png", rotate=90, scaling="letterbox")
"""

import time
import struct
import logging
from typing import Optional, Tuple, Union

import spidev
import gpiod
from PIL import Image

logger = logging.getLogger(__name__)

# Display dimensions (portrait orientation as required by controller)
WIDTH = 128
HEIGHT = 250
BUFFER_SIZE = WIDTH * HEIGHT // 8  # 4000 bytes per RAM buffer

# GPIO pin assignments (from eink.conf)
DC_PIN = 7
RST_PIN = 13
BUSY_PIN = 9

# SPI settings
SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED_HZ = 10_000_000  # 10 MHz

# 4-Gray LUT waveform data (159 bytes total, 153 loaded via command 0x32)
# From GxEPD2_213_GDEY0213B74.cpp
LUT_4GRAY = bytes([
    # Voltage Source levels (VS) - 5 groups of 12 bytes = 60 bytes
    0x40, 0x48, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # VS L0: white
    0x08, 0x48, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # VS L1: light grey
    0x02, 0x48, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # VS L2: dark grey
    0x20, 0x48, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # VS L3: black
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # VS L4: VCOM

    # Timing/Phase groups (TP) - 12 groups of 7 bytes = 84 bytes
    0x0A, 0x19, 0x00, 0x03, 0x08, 0x00, 0x00,  # TP0 RP0
    0x14, 0x01, 0x00, 0x14, 0x01, 0x00, 0x03,  # TP1 RP1
    0x0A, 0x03, 0x00, 0x08, 0x19, 0x00, 0x00,  # TP2 RP2
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01,  # TP3 RP3
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # TP4
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # TP5
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # TP6
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # TP7
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # TP8
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # TP9
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # TP10
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # TP11

    # Gate/Source voltage settings (9 bytes)
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x00, 0x00, 0x00,  # @144

    # Additional voltage params extracted separately for init commands:
    # These are at positions [153..158] in the full LUT array
    # 0x22 = EOPQ, 0x17 = VGH, 0x41 = VSH1, 0x00 = VSH2, 0x32 = VSL, 0x1C = VCOM
])

# Voltage parameters from the end of the LUT array (used in init commands)
EOPQ_VAL = 0x22
VGH_VAL = 0x17
VSH1_VAL = 0x41
VSH2_VAL = 0x00
VSL_VAL = 0x32
VCOM_VAL = 0x1C


class EinkSPI:
    """Low-level SPI/GPIO interface for the e-ink controller."""

    def __init__(self):
        self.spi = None
        self.chip = None
        self.dc_line = None
        self.rst_line = None
        self.busy_line = None

    def open(self):
        """Open SPI and GPIO devices."""
        # Open SPI
        self.spi = spidev.SpiDev()
        self.spi.open(SPI_BUS, SPI_DEVICE)
        self.spi.max_speed_hz = SPI_SPEED_HZ
        self.spi.mode = 0

        # Open GPIO
        self.chip = gpiod.Chip("/dev/gpiochip0")

        # Configure output pins (DC, RST)
        dc_settings = gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            output_value=gpiod.line.Value.ACTIVE,
        )
        rst_settings = gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            output_value=gpiod.line.Value.ACTIVE,
        )
        busy_settings = gpiod.LineSettings(
            direction=gpiod.line.Direction.INPUT,
            bias=gpiod.line.Bias.PULL_UP,
        )

        self.request = self.chip.request_lines(
            consumer="eink-4gray",
            config={
                DC_PIN: dc_settings,
                RST_PIN: rst_settings,
                BUSY_PIN: busy_settings,
            },
        )

        logger.debug("SPI and GPIO opened successfully")

    def close(self):
        """Close SPI and GPIO devices."""
        if self.request:
            self.request.release()
            self.request = None
        if self.chip:
            self.chip.close()
            self.chip = None
        if self.spi:
            self.spi.close()
            self.spi = None
        logger.debug("SPI and GPIO closed")

    def _set_dc(self, value: bool):
        """Set DC pin (False=command, True=data)."""
        self.request.set_value(
            DC_PIN,
            gpiod.line.Value.ACTIVE if value else gpiod.line.Value.INACTIVE,
        )

    def _set_rst(self, value: bool):
        """Set RST pin."""
        self.request.set_value(
            RST_PIN,
            gpiod.line.Value.ACTIVE if value else gpiod.line.Value.INACTIVE,
        )

    def _get_busy(self) -> bool:
        """Read BUSY pin (True = busy/high)."""
        return self.request.get_value(BUSY_PIN) == gpiod.line.Value.ACTIVE

    def hardware_reset(self):
        """Perform hardware reset sequence."""
        self._set_rst(True)
        time.sleep(0.01)
        self._set_rst(False)
        time.sleep(0.01)
        self._set_rst(True)
        time.sleep(0.01)
        logger.debug("Hardware reset done")

    def wait_busy(self, timeout_s: float = 30.0):
        """Wait until BUSY pin goes low (not busy)."""
        start = time.monotonic()
        while self._get_busy():
            if time.monotonic() - start > timeout_s:
                raise TimeoutError(f"E-ink BUSY timeout after {timeout_s}s")
            time.sleep(0.001)
        logger.debug(f"BUSY cleared in {time.monotonic() - start:.3f}s")

    def send_command(self, cmd: int):
        """Send a command byte (DC=low)."""
        self._set_dc(False)
        self.spi.writebytes([cmd])

    def send_data(self, data: Union[int, bytes, list]):
        """Send data byte(s) (DC=high)."""
        self._set_dc(True)
        if isinstance(data, int):
            self.spi.writebytes([data])
        elif isinstance(data, (bytes, bytearray)):
            # SPI writebytes has a 4096-byte limit per call, send in chunks
            chunk_size = 4096
            for i in range(0, len(data), chunk_size):
                self.spi.writebytes(list(data[i:i + chunk_size]))
        else:
            chunk_size = 4096
            for i in range(0, len(data), chunk_size):
                self.spi.writebytes(data[i:i + chunk_size])

    def send_command_data(self, cmd: int, *data_bytes):
        """Send a command followed by data bytes."""
        self.send_command(cmd)
        for b in data_bytes:
            self.send_data(b)


class Grayscale4Display:
    """4-Gray grayscale display driver for GDEY0213B74."""

    def __init__(self):
        self.hw = EinkSPI()

    def open(self):
        self.hw.open()

    def close(self):
        self.hw.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def _set_partial_ram_area(self, x: int, y: int, w: int, h: int):
        """Set the RAM address window matching the Rust SDK convention (X inc, Y dec)."""
        # Data entry mode: X increment, Y decrement (0x01) — matches Rust SDK
        self.hw.send_command_data(0x11, 0x01)

        # RAM X start/end (low to high for X increment)
        self.hw.send_command(0x44)
        self.hw.send_data(x // 8)
        self.hw.send_data((x + w - 1) // 8)

        # RAM Y start/end (high to low for Y decrement)
        y_end = y + h - 1
        self.hw.send_command(0x45)
        self.hw.send_data(y_end % 256)
        self.hw.send_data(y_end // 256)
        self.hw.send_data(y % 256)
        self.hw.send_data(y // 256)

        # RAM address counter
        self.hw.send_command(0x4E)
        self.hw.send_data(x // 8)
        self.hw.send_command(0x4F)
        self.hw.send_data(y_end % 256)
        self.hw.send_data(y_end // 256)

    def _init_4gray(self):
        """Initialize the display for 4-gray mode (matching GxEPD2 _Init_4G)."""
        self.hw.hardware_reset()
        time.sleep(0.01)

        # Software reset
        self.hw.send_command(0x12)
        time.sleep(0.01)

        # Analog block control
        self.hw.send_command_data(0x74, 0x54)

        # Digital block control
        self.hw.send_command_data(0x7E, 0x3B)

        # Driver output control (height-1 = 0x127 = 295... wait, our display is 250)
        # GxEPD2 uses 0x27, 0x01 = 295 for this display type
        # 0x127 = 295 rows. But our display is 250 rows?
        # Looking at the code: HEIGHT = 250, but init uses 0x27,0x01 = 295
        # This matches the GxEPD2 init exactly
        self.hw.send_command(0x01)
        self.hw.send_data(0x27)  # (HEIGHT-1) low byte: actually 295 & 0xFF = 0x27
        self.hw.send_data(0x01)  # (HEIGHT-1) high byte: 295 >> 8 = 0x01
        self.hw.send_data(0x00)  # Gate scanning sequence

        # Set partial RAM area (full screen)
        self._set_partial_ram_area(0, 0, WIDTH, HEIGHT)

        # Border waveform
        self.hw.send_command_data(0x3C, 0x00)

        # VCOM voltage
        self.hw.send_command_data(0x2C, VCOM_VAL)

        # End Option (EOPQ)
        self.hw.send_command_data(0x3F, EOPQ_VAL)

        # VGH voltage
        self.hw.send_command_data(0x03, VGH_VAL)

        # VSH1, VSH2, VSL voltages
        self.hw.send_command(0x04)
        self.hw.send_data(VSH1_VAL)
        self.hw.send_data(VSH2_VAL)
        self.hw.send_data(VSL_VAL)

        # Display update control
        self.hw.send_command(0x21)
        self.hw.send_data(0x00)
        self.hw.send_data(0x80)

        # Load LUT waveform (153 bytes via command 0x32)
        self.hw.send_command(0x32)
        self.hw.send_data(LUT_4GRAY[:153])

        # Clear both RAM buffers with 0x00
        self._write_screen_buffer(0x24, 0x00)
        self._write_screen_buffer(0x26, 0x00)

        logger.debug("4-gray init complete")

    def _write_screen_buffer(self, command: int, value: int):
        """Fill an entire RAM buffer with a single byte value."""
        self.hw.send_command(command)
        self.hw.send_data(bytes([value] * BUFFER_SIZE))

    def _update_4gray(self):
        """Trigger 4-gray display update (matching GxEPD2 _Update_4G)."""
        self.hw.send_command_data(0x22, 0xC7)
        self.hw.send_command(0x20)
        self.hw.wait_busy(timeout_s=30.0)
        logger.debug("4-gray update complete")

    def _deep_sleep(self):
        """Put display into deep sleep mode."""
        self.hw.send_command_data(0x10, 0x01)
        time.sleep(0.1)

    def display_grayscale(
        self,
        image_path: str,
        rotate: int = 0,
        scaling: str = "letterbox",
        invert: bool = False,
    ):
        """
        Display an image with 4-level grayscale.

        Args:
            image_path: Path to any image file (PNG, JPEG, etc.)
            rotate: Rotation in degrees (0, 90, 180, 270)
            scaling: "letterbox" (maintain aspect, white borders),
                     "crop" (center crop to fill),
                     "stretch" (distort to fill)
            invert: If True, invert the grayscale levels
        """
        # Load and prepare the image
        img = Image.open(image_path)

        # Convert to grayscale
        img = img.convert("L")

        # Pre-flip horizontally to correct for the SSD1680's scan direction
        # mirror (same approach as the 1-bit pipeline), then rotate.
        # The flip must happen BEFORE rotation to match the 1-bit behavior.
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if rotate == 90:
            img = img.transpose(Image.Transpose.ROTATE_270)
        elif rotate == 180:
            img = img.transpose(Image.Transpose.ROTATE_180)
        elif rotate == 270:
            img = img.transpose(Image.Transpose.ROTATE_90)

        # Scale to display dimensions (WIDTH x HEIGHT = 128x250 portrait)
        target_w, target_h = WIDTH, HEIGHT
        img = self._scale_image(img, target_w, target_h, scaling)

        if invert:
            from PIL import ImageOps
            img = ImageOps.invert(img)

        # Convert to 4-gray levels and split into dual RAM buffers
        ram_24, ram_26 = self._convert_to_4gray_buffers(img)

        # Initialize 4-gray mode
        self._init_4gray()

        # Set RAM area for full screen
        self._set_partial_ram_area(0, 0, WIDTH, HEIGHT)

        # Write RAM 0x26 (previous/red buffer) first
        self.hw.send_command(0x26)
        self.hw.send_data(ram_26)

        # Write RAM 0x24 (current/BW buffer)
        self.hw.send_command(0x24)
        self.hw.send_data(ram_24)

        # Trigger update
        self._update_4gray()

        # Sleep
        self._deep_sleep()

        logger.info("4-gray grayscale display complete")

    def display_gray_test(self):
        """Display a 4-band test pattern (black, dark gray, light gray, white).

        Matches GxEPD2 drawGreyLevels() for verification.
        """
        self._init_4gray()

        quarter = BUFFER_SIZE // 4  # 1000 bytes per band

        # RAM 0x24 pattern:
        # Band 1 (black):      0x00
        # Band 2 (dark gray):  0xFF
        # Band 3 (light gray): 0x00
        # Band 4 (white):      0xFF
        ram_24 = (bytes([0x00] * quarter) +
                  bytes([0xFF] * quarter) +
                  bytes([0x00] * quarter) +
                  bytes([0xFF] * quarter))

        # RAM 0x26 pattern:
        # Band 1 (black):      0x00
        # Band 2 (dark gray):  0x00
        # Band 3 (light gray): 0xFF
        # Band 4 (white):      0xFF
        ram_26 = (bytes([0x00] * quarter) +
                  bytes([0x00] * quarter) +
                  bytes([0xFF] * quarter) +
                  bytes([0xFF] * quarter))

        self.hw.send_command(0x24)
        self.hw.send_data(ram_24)

        self.hw.send_command(0x26)
        self.hw.send_data(ram_26)

        self._update_4gray()
        self._deep_sleep()

        logger.info("Gray test pattern displayed")

    def _scale_image(
        self, img: Image.Image, target_w: int, target_h: int, method: str
    ) -> Image.Image:
        """Scale image to target dimensions using the specified method."""
        src_w, src_h = img.size

        if method == "stretch":
            return img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        elif method == "crop":
            # Scale to fill, then center crop
            scale = max(target_w / src_w, target_h / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            # Center crop
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            return img.crop((left, top, left + target_w, top + target_h))

        else:  # letterbox
            # Scale to fit, add white borders
            scale = min(target_w / src_w, target_h / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            # Create white background and paste centered
            result = Image.new("L", (target_w, target_h), 255)
            paste_x = (target_w - new_w) // 2
            paste_y = (target_h - new_h) // 2
            result.paste(img, (paste_x, paste_y))
            return result

    def _convert_to_4gray_buffers(
        self, img: Image.Image
    ) -> Tuple[bytes, bytes]:
        """
        Convert a grayscale image to dual RAM buffers for 4-gray display.

        The SSD1680 4-gray encoding uses 2 RAM buffers where each pixel
        is encoded as a bit pair across the two buffers:

            RAM 0x26 bit | RAM 0x24 bit | Result (after ~inversion)
            -------------|--------------|---------------------------
            0            | 0            | Black
            0            | 1            | Dark Gray
            1            | 0            | Light Gray
            1            | 1            | White

        Data is inverted (~) before transfer (matching GxEPD2 writeImage_4G).

        Args:
            img: PIL Image in "L" mode, already sized to WIDTH x HEIGHT

        Returns:
            Tuple of (ram_24_data, ram_26_data), each BUFFER_SIZE bytes
        """
        pixels = img.load()
        w, h = img.size

        ram_24 = bytearray(BUFFER_SIZE)
        ram_26 = bytearray(BUFFER_SIZE)

        for y in range(h):
            for x in range(w):
                gray = pixels[x, y]

                # Quantize to 4 levels with thresholds
                # Level 0: Black    (gray < 64)
                # Level 1: Dark Gray  (64 <= gray < 128)
                # Level 2: Light Gray (128 <= gray < 192)
                # Level 3: White    (gray >= 192)
                if gray < 64:
                    bit_24 = 0  # RAM 0x24 bit
                    bit_26 = 0  # RAM 0x26 bit
                elif gray < 128:
                    bit_24 = 1
                    bit_26 = 0
                elif gray < 192:
                    bit_24 = 0
                    bit_26 = 1
                else:
                    bit_24 = 1
                    bit_26 = 1

                # Calculate byte position and bit position within byte
                byte_idx = (y * w + x) // 8
                bit_idx = 7 - ((y * w + x) % 8)  # MSB first

                # Set bits in RAM buffers
                if bit_24:
                    ram_24[byte_idx] |= (1 << bit_idx)
                if bit_26:
                    ram_26[byte_idx] |= (1 << bit_idx)

        # Invert both buffers (matching GxEPD2 _transfer(~out_byte))
        ram_24 = bytes([~b & 0xFF for b in ram_24])
        ram_26 = bytes([~b & 0xFF for b in ram_26])

        return ram_24, ram_26


def display_4gray(
    image_path: str,
    rotate: int = 0,
    scaling: str = "letterbox",
    invert: bool = False,
):
    """
    Convenience function to display an image with 4-level grayscale.

    This function opens SPI/GPIO, initializes the display for 4-gray mode,
    sends the image, and closes everything. It operates independently of
    the Rust library - do NOT have a Display() instance open at the same time.

    Args:
        image_path: Path to any image file
        rotate: Rotation in degrees (0, 90, 180, 270).
                For the GDEY0213B74 mounted in landscape, use rotate=90.
        scaling: "letterbox", "crop", or "stretch"
        invert: If True, invert grayscale levels
    """
    with Grayscale4Display() as disp:
        disp.display_grayscale(image_path, rotate=rotate, scaling=scaling, invert=invert)


def display_4gray_test():
    """Display a 4-band gray test pattern (black, dark gray, light gray, white)."""
    with Grayscale4Display() as disp:
        disp.display_gray_test()
