#!/usr/bin/env python3
"""
Display module for Distiller SDK.
Provides functionality for e-ink display control and image display.

Logging:
    This module uses the logging module for debug and error messages.
    Enable detailed Rust-level logging with RUST_LOG environment variable:
        RUST_LOG=debug python script.py
"""

import ctypes
import logging
import os
from ctypes import POINTER, c_bool, c_char_p, c_float, c_int, c_uint32
from enum import IntEnum
from typing import Optional, Tuple, Union

# Set up module logger
logger = logging.getLogger(__name__)


class DisplayError(Exception):
    """Custom exception for Display-related errors."""

    pass


class DisplayErrorCode(IntEnum):
    """Error codes returned by FFI functions."""

    SUCCESS = 1
    GPIO = -1
    SPI = -2
    CONFIG = -3
    TIMEOUT = -4
    NOT_INITIALIZED = -5
    INVALID_DATA = -6
    PNG = -7
    IO = -8
    UNSUPPORTED_MODE = -10
    UNKNOWN = -99


# Error code to human-readable message mapping
ERROR_MESSAGES = {
    DisplayErrorCode.GPIO: "GPIO hardware error - check /dev/gpiochipX device exists and is accessible",
    DisplayErrorCode.SPI: "SPI device error - check /dev/spidevX.Y device exists and SPI is enabled",
    DisplayErrorCode.CONFIG: "Configuration error - check /opt/distiller-sdk/eink.conf exists and is valid",
    DisplayErrorCode.TIMEOUT: "Hardware timeout - display not responding (check connections and power)",
    DisplayErrorCode.NOT_INITIALIZED: "Display not initialized - call initialize() first",
    DisplayErrorCode.INVALID_DATA: "Invalid data - check image dimensions and data format",
    DisplayErrorCode.PNG: "PNG processing error - check file exists and is a valid PNG",
    DisplayErrorCode.IO: "I/O error - check file permissions and disk space",
    DisplayErrorCode.UNSUPPORTED_MODE: "Display mode not supported by current firmware",
    DisplayErrorCode.UNKNOWN: "Unknown error - check RUST_LOG=debug for details",
}


class DisplayMode(IntEnum):
    """Display refresh modes."""

    FULL = 0  # Full refresh - slow but high quality
    PARTIAL = 1  # Partial refresh - fast updates
    FAST = 2  # Fast refresh (~1.5s) - reduced ghosting
    TURBO = 3  # Turbo refresh (~1s) - fastest, may ghost
    GRAYSCALE_4 = 4  # 4-level grayscale


class ScalingMethod(IntEnum):
    """Image scaling methods for auto-conversion."""

    LETTERBOX = 0  # Maintain aspect ratio, add black borders
    CROP_CENTER = 1  # Center crop to fill display
    STRETCH = 2  # Stretch to fill display (may distort)


class DitheringMethod(IntEnum):
    """Dithering methods for 1-bit conversion."""

    THRESHOLD = 0  # Fast threshold conversion
    FLOYD_STEINBERG = 1  # High quality dithering
    ORDERED = 2  # Ordered dithering


class Display:
    """
    Display class for interacting with the CM5 e-ink display system.

    This class provides functionality to:
    - Display images in various formats (PNG, JPEG, GIF, BMP, TIFF, WebP, etc.)
    - Display raw 1-bit image data
    - Automatic image scaling and dithering for any size/format
    - Clear the display
    - Control display refresh modes (Full/Partial)
    - Manage display power states
    - Color inversion
    - Text rendering and overlay capabilities
    """

    WIDTH = 250
    HEIGHT = 128
    ARRAY_SIZE = (250 * 128) // 8  # 4000

    def __init__(self, library_path: Optional[str] = None, auto_init: bool = True):
        """
        Initialize the Display object.

        Args:
            library_path: Optional path to the shared library. If None, searches common locations.
            auto_init: Whether to automatically initialize the display hardware

        Raises:
            DisplayError: If library can't be loaded or display can't be initialized
        """
        self._initialized = False
        self._library_path = library_path

        # Find and load the shared library
        if library_path is None:
            library_path = self._find_library()

        logger.debug(f"Loading display library from: {library_path}")

        if not os.path.exists(library_path):
            logger.error(f"Display library not found at: {library_path}")
            raise DisplayError(f"Display library not found: {library_path}")

        try:
            self._lib: ctypes.CDLL = ctypes.CDLL(library_path)
            logger.debug("Display library loaded successfully")
        except OSError as e:
            logger.error(f"Failed to load display library: {e}")
            raise DisplayError(f"Failed to load display library: {e}")

        # Set up function signatures
        self._setup_function_signatures()

        # Initialize Rust logger if RUST_LOG is set
        if os.environ.get("RUST_LOG"):
            logger.debug("Initializing Rust logger (RUST_LOG is set)")
            self._init_rust_logger()

        if auto_init:
            self.initialize()

    def _find_library(self) -> str:
        """Find the shared library in common locations."""
        # Get the directory of this Python file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Common search paths
        search_paths = [
            # Debian package location
            "/opt/distiller-sdk/lib/libdistiller_display_sdk_shared.so",
            # Relative to this module
            os.path.join(current_dir, "lib", "libdistiller_display_sdk_shared.so"),
            # Build directory
            os.path.join(current_dir, "build", "libdistiller_display_sdk_shared.so"),
            # System locations
            "/usr/local/lib/libdistiller_display_sdk_shared.so",
            "/usr/lib/libdistiller_display_sdk_shared.so",
        ]

        for path in search_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                return abs_path

        raise DisplayError(
            "Could not find libdistiller_display_sdk_shared.so in any of these locations:\n"
            + "\n".join(f"  - {path}" for path in search_paths)
        )

    def _setup_function_signatures(self):
        """Set up ctypes function signatures for all C functions."""

        # display_init() -> bool
        self._lib.display_init.restype = c_bool
        self._lib.display_init.argtypes = []

        # display_image_raw(const uint8_t* data, display_mode_t mode) -> bool
        self._lib.display_image_raw.restype = c_bool
        self._lib.display_image_raw.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]

        # display_image_auto(const char* filename, mode, scale_mode, dither_mode, invert) -> int
        self._lib.display_image_auto.restype = c_int
        self._lib.display_image_auto.argtypes = [c_char_p, c_int, c_int, c_int, c_int]

        # display_clear() -> bool
        self._lib.display_clear.restype = c_bool
        self._lib.display_clear.argtypes = []

        # display_sleep() -> void
        self._lib.display_sleep.restype = None
        self._lib.display_sleep.argtypes = []

        # display_cleanup() -> void
        self._lib.display_cleanup.restype = None
        self._lib.display_cleanup.argtypes = []

        # display_set_partial_base_map(const uint8_t* data) -> int
        self._lib.display_set_partial_base_map.restype = c_int
        self._lib.display_set_partial_base_map.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]

        # display_get_dimensions(uint32_t* width, uint32_t* height) -> void
        self._lib.display_get_dimensions.restype = None
        self._lib.display_get_dimensions.argtypes = [POINTER(c_uint32), POINTER(c_uint32)]

        # convert_png_to_1bit(const char* filename, uint8_t* output_data) -> bool
        self._lib.convert_png_to_1bit.restype = c_bool
        self._lib.convert_png_to_1bit.argtypes = [c_char_p, ctypes.POINTER(ctypes.c_ubyte)]

        # image_invert_1bit(const uint8_t* data, uint32_t size, uint8_t* output) -> bool
        self._lib.image_invert_1bit.restype = c_bool
        self._lib.image_invert_1bit.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            c_uint32,
            ctypes.POINTER(ctypes.c_ubyte),
        ]

        # image_dither(const uint8_t* gray_data, uint32_t width, uint32_t height, int mode, uint8_t* output) -> bool
        self._lib.image_dither.restype = c_bool
        self._lib.image_dither.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            c_uint32,
            c_uint32,
            c_int,
            ctypes.POINTER(ctypes.c_ubyte),
        ]

        # image_process(const char* path, int scale_mode, int dither_mode, int brightness, float contrast,
        #               int invert, uint8_t* output) -> bool
        self._lib.image_process.restype = c_bool
        self._lib.image_process.argtypes = [
            c_char_p,
            c_int,
            c_int,
            c_int,
            c_float,
            c_int,
            ctypes.POINTER(ctypes.c_ubyte),
        ]

        # text_render(const char* text, uint32_t x, uint32_t y, uint32_t scale, int invert, uint8_t* output) -> bool
        self._lib.text_render.restype = c_bool
        self._lib.text_render.argtypes = [
            c_char_p,
            c_uint32,
            c_uint32,
            c_uint32,
            c_int,
            ctypes.POINTER(ctypes.c_ubyte),
        ]

        # text_overlay(uint8_t* buffer, const char* text, uint32_t x, uint32_t y, uint32_t scale, int invert) -> bool
        self._lib.text_overlay.restype = c_bool
        self._lib.text_overlay.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            c_char_p,
            c_uint32,
            c_uint32,
            c_uint32,
            c_int,
        ]

        # shape_draw_rect_filled(uint8_t* buffer, uint32_t x, uint32_t y, uint32_t width, uint32_t height, int value) -> bool
        self._lib.shape_draw_rect_filled.restype = c_bool
        self._lib.shape_draw_rect_filled.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            c_uint32,
            c_uint32,
            c_uint32,
            c_uint32,
            c_int,
        ]

        # Logger initialization (optional - may not exist in older libraries)
        try:
            # display_init_logger() -> void
            self._lib.display_init_logger.restype = None
            self._lib.display_init_logger.argtypes = []
            self._logger_available = True
        except AttributeError:
            self._logger_available = False

    def _init_rust_logger(self) -> None:
        """Initialize the Rust logger if available."""
        if hasattr(self, "_logger_available") and self._logger_available:
            try:
                self._lib.display_init_logger()
                logger.debug("Rust logger initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Rust logger: {e}")

    def _check_result(self, result: int, operation: str) -> None:
        """
        Check FFI function result and raise DisplayError on failure.

        Args:
            result: Return value from FFI function (1=success, negative=error code)
            operation: Description of the operation for error message

        Raises:
            DisplayError: If result indicates an error
        """
        if result == DisplayErrorCode.SUCCESS:
            return

        try:
            error_code = DisplayErrorCode(result)
            base_msg = ERROR_MESSAGES.get(error_code, f"Unknown error (code: {error_code})")
            logger.error(f"{operation} failed: {base_msg}")
            raise DisplayError(f"{operation}: {base_msg}")
        except ValueError:
            # Invalid error code
            logger.error(f"{operation} failed with unknown error code: {result}")
            raise DisplayError(f"{operation}: Unknown error code {result}")

    def initialize(self) -> None:
        """
        Initialize the display hardware.

        Raises:
            DisplayError: If initialization fails
        """
        if self._initialized:
            logger.debug("Display already initialized, skipping")
            return

        logger.debug("Initializing display hardware...")

        result = self._lib.display_init()
        try:
            self._check_result(result, "Display initialization")
        except DisplayError:
            # Provide additional helpful hints for initialization failures
            logger.error("Common initialization issues:")
            logger.error("  - GPIO chip not accessible (check /dev/gpiochipX permissions)")
            logger.error("  - SPI device not accessible (check /dev/spidevX.Y permissions)")
            logger.error("  - Configuration file missing (/opt/distiller-sdk/eink.conf)")
            logger.error("  - Hardware not connected or powered")
            logger.error("For detailed Rust-level errors, run with: RUST_LOG=debug")
            raise

        # Update dimensions based on current firmware
        self._update_dimensions()

        self._initialized = True
        logger.info(f"Display initialized successfully ({self.WIDTH}x{self.HEIGHT})")

    def _update_dimensions(self) -> None:
        """Update display dimensions from the library."""
        try:
            width_ptr = ctypes.pointer(c_uint32())
            height_ptr = ctypes.pointer(c_uint32())
            self._lib.display_get_dimensions(width_ptr, height_ptr)

            self.WIDTH = width_ptr.contents.value
            self.HEIGHT = height_ptr.contents.value
            self.ARRAY_SIZE = (self.WIDTH * self.HEIGHT) // 8

            # Also update class-level constants for backwards compatibility
            Display.WIDTH = self.WIDTH
            Display.HEIGHT = self.HEIGHT
            Display.ARRAY_SIZE = self.ARRAY_SIZE

            logger.debug(f"Display dimensions updated: {self.WIDTH}x{self.HEIGHT}")

        except Exception as e:
            logger.warning(f"Could not get dimensions from library: {e}")
            logger.debug(f"Using default dimensions: {self.WIDTH}x{self.HEIGHT}")
            # Keep default values

    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get display dimensions.

        Returns:
            Tuple of (width, height) in pixels
        """
        if not self._initialized:
            # Try to get dimensions without initializing
            try:
                width_ptr = ctypes.pointer(c_uint32())
                height_ptr = ctypes.pointer(c_uint32())
                self._lib.display_get_dimensions(width_ptr, height_ptr)
                return (width_ptr.contents.value, height_ptr.contents.value)
            except Exception:
                return (self.WIDTH, self.HEIGHT)
        return (self.WIDTH, self.HEIGHT)

    def _display_raw(self, data: bytes, mode: DisplayMode) -> None:
        """Display raw 1-bit image data."""
        logger.debug(f"Displaying raw image data ({len(data)} bytes, mode={mode.name})")

        if len(data) != self.ARRAY_SIZE:
            logger.error(f"Invalid data size: expected {self.ARRAY_SIZE} bytes, got {len(data)}")
            raise DisplayError(f"Data must be exactly {self.ARRAY_SIZE} bytes, got {len(data)}")

        # Convert bytes to ctypes array
        data_array = (ctypes.c_ubyte * len(data))(*data)

        result = self._lib.display_image_raw(data_array, int(mode))
        self._check_result(result, "Display raw image")
        logger.debug("Raw image displayed successfully")

    def display_image_auto(
        self,
        image: Union[str, bytes],
        mode: DisplayMode = DisplayMode.FULL,
        scaling: ScalingMethod = ScalingMethod.LETTERBOX,
        dithering: DitheringMethod = DitheringMethod.FLOYD_STEINBERG,
        invert_colors: bool = False,
    ) -> None:
        """
        Display any image with automatic scaling and dithering.

        This is the primary display method. Supports file paths (any image
        format/size) and raw 1-bit packed bytes.

        Args:
            image: Image file path (str) or raw 1-bit packed data (bytes)
            mode: Display refresh mode (FULL or PARTIAL)
            scaling: How to scale the image to fit display (file paths only)
            dithering: Dithering method for 1-bit conversion (file paths only)
            invert_colors: Invert colors (black/white swap)

        Raises:
            DisplayError: If display operation fails
        """
        if not self._initialized:
            raise DisplayError(
                "Display not initialized. Call initialize() first."
            )

        if isinstance(image, str):
            # File path input — Rust handles all modes including Grayscale4
            if not os.path.exists(image):
                raise DisplayError(f"Image file not found: {image}")

            logger.debug(
                f"Auto-displaying image: {image} "
                f"(mode={mode.name}, scale={scaling.name}, dither={dithering.name}, invert={invert_colors})"
            )
            filename_bytes = image.encode("utf-8")
            result = self._lib.display_image_auto(
                filename_bytes,
                int(mode),
                int(scaling),
                int(dithering),
                1 if invert_colors else 0,
            )

            self._check_result(
                result, f"Auto-display image '{image}' (mode={mode.name})"
            )
            logger.debug("Image auto-displayed successfully")

        elif isinstance(image, (bytes, bytearray)):
            # Raw bytes input — Grayscale4 requires file path
            if mode == DisplayMode.GRAYSCALE_4:
                raise DisplayError("Grayscale4 mode requires a file path, not raw bytes")

            raw_data = bytes(image)
            if len(raw_data) != self.ARRAY_SIZE:
                raise DisplayError(
                    f"Raw data must be exactly {self.ARRAY_SIZE} bytes, "
                    f"got {len(raw_data)}"
                )

            if invert_colors:
                raw_data = self._invert_1bit(raw_data)

            self._display_raw(raw_data, mode)
        else:
            raise DisplayError(
                f"Invalid image type: {type(image)}. "
                "Expected str or bytes."
            )

    def display_image(
        self,
        image: Union[str, bytes],
        mode: DisplayMode = DisplayMode.FULL,
        scaling: ScalingMethod = ScalingMethod.LETTERBOX,
        dithering: DitheringMethod = DitheringMethod.FLOYD_STEINBERG,
        invert_colors: bool = False,
        **kwargs,
    ) -> None:
        """Alias for display_image_auto(). Accepts extra kwargs for backward compatibility."""
        self.display_image_auto(
            image, mode=mode, scaling=scaling, dithering=dithering, invert_colors=invert_colors
        )

    def display_png_auto(
        self,
        image: Union[str, bytes],
        mode: DisplayMode = DisplayMode.FULL,
        scaling: ScalingMethod = ScalingMethod.LETTERBOX,
        dithering: DitheringMethod = DitheringMethod.FLOYD_STEINBERG,
        invert_colors: bool = False,
        **kwargs,
    ) -> None:
        """Alias for display_image_auto(). Accepts extra kwargs for backward compatibility."""
        self.display_image_auto(
            image, mode=mode, scaling=scaling, dithering=dithering, invert_colors=invert_colors
        )

    def clear(self) -> None:
        """
        Clear the display (set to white).

        Raises:
            DisplayError: If clear operation fails
        """
        if not self._initialized:
            logger.error("Attempted to clear display before initialization")
            raise DisplayError("Display not initialized. Call initialize() first.")

        logger.debug("Clearing display")
        result = self._lib.display_clear()
        self._check_result(result, "Clear display")
        logger.debug("Display cleared successfully")

    def sleep(self) -> None:
        """Put display to sleep for power saving."""
        if self._initialized:
            logger.debug("Putting display to sleep")
            self._lib.display_sleep()

    def convert_png_to_raw(self, filename: str) -> bytes:
        """
        Convert PNG file to raw 1-bit data.

        Args:
            filename: Path to PNG file (must match display dimensions)

        Returns:
            Raw 1-bit packed image data (size depends on firmware)

        Raises:
            DisplayError: If conversion fails
        """
        if not os.path.exists(filename):
            raise DisplayError(f"PNG file not found: {filename}")

        logger.debug(f"Converting PNG to raw: {filename}")
        # Create output buffer
        output_data = (ctypes.c_ubyte * self.ARRAY_SIZE)()
        filename_bytes = filename.encode("utf-8")

        result = self._lib.convert_png_to_1bit(filename_bytes, output_data)
        self._check_result(result, f"Convert PNG '{filename}' to raw")

        # Convert ctypes array to bytes
        logger.debug("PNG conversion successful")
        return bytes(output_data)

    def is_initialized(self) -> bool:
        """Check if display is initialized."""
        return self._initialized

    def close(self) -> None:
        """Cleanup display resources."""
        if self._initialized:
            logger.debug("Cleaning up display resources")
            self._lib.display_cleanup()
            self._initialized = False
            logger.debug("Display closed successfully")

    def render_text(
        self, text: str, x: int = 0, y: int = 0, scale: int = 1, invert: bool = False
    ) -> bytes:
        """
        Render text to a 1-bit image buffer using Rust FFI.

        Args:
            text: Text string to render
            x: X position for text
            y: Y position for text
            scale: Text scale factor (1=normal, 2=double, etc.)
            invert: Whether to invert text colors

        Returns:
            1-bit packed image data with rendered text

        Raises:
            DisplayError: If text rendering fails
        """
        output_data = (ctypes.c_ubyte * self.ARRAY_SIZE)()
        text_bytes = text.encode("utf-8")

        success = self._lib.text_render(
            text_bytes,
            c_uint32(x),
            c_uint32(y),
            c_uint32(scale),
            c_int(1 if invert else 0),
            output_data,
        )

        if not success:
            raise DisplayError(f"Failed to render text: {text}")

        return bytes(output_data)

    def display_text(self, text, x=0, y=0, scale=1, invert=False, mode=DisplayMode.FULL):
        """
        Render and display text in a single call.

        Args:
            text: Text string to display
            x: X position for text (0 = left edge)
            y: Y position for text (0 = top edge)
            scale: Text scale factor (1=normal, 2=double, etc.)
            invert: False = black text on white background (default, like paper)
                    True = white text on black background
            mode: Display refresh mode (FULL or PARTIAL)

        Raises:
            DisplayError: If text rendering or display fails
        """
        # EPD128x250 has ~10 inactive source lines at physical top edge
        _TOP_MARGIN = 10 if (self.WIDTH == 250 and self.HEIGHT == 128) else 0
        y_render = y + _TOP_MARGIN
        buf = self.render_text(text, x, y_render, scale, invert=False)
        if not invert:
            buf = self._invert_1bit(buf)
        self._display_raw(buf, mode)

    def set_partial_base_map(self, image: Union[str, bytes]) -> None:
        """
        Set the base map for partial refresh by writing to both RAM buffers.

        This establishes the reference image for subsequent partial updates,
        preventing ghosting artifacts from accumulating.

        Args:
            image: Image file path (str) or raw 1-bit packed data (bytes).
                   If a file path, it will be converted using the default
                   scaling and dithering settings.

        Raises:
            DisplayError: If the operation fails
        """
        if not self._initialized:
            raise DisplayError("Display not initialized. Call initialize() first.")

        if isinstance(image, str):
            if not os.path.exists(image):
                raise DisplayError(f"Image file not found: {image}")
            raw_data = self.convert_png_to_raw(image)
        elif isinstance(image, (bytes, bytearray)):
            raw_data = bytes(image)
        else:
            raise DisplayError(f"Invalid image type: {type(image)}. Expected str or bytes.")

        if len(raw_data) != self.ARRAY_SIZE:
            raise DisplayError(
                f"Data must be exactly {self.ARRAY_SIZE} bytes, got {len(raw_data)}"
            )

        data_array = (ctypes.c_ubyte * len(raw_data))(*raw_data)
        result = self._lib.display_set_partial_base_map(data_array)
        self._check_result(result, "Set partial base map")
        logger.debug("Partial base map set successfully")

    def display_grayscale(
        self,
        filename: str,
        scaling: str = "letterbox",
        invert: bool = False,
    ) -> None:
        """
        Display an image with 4-level grayscale.

        Routes through display_image_auto with GRAYSCALE_4 mode, which uses
        the Rust library's native 4-gray support.

        Args:
            filename: Path to any image file (PNG, JPEG, etc.)
            scaling: "letterbox", "crop", or "stretch"
            invert: If True, invert the grayscale levels

        Raises:
            DisplayError: If display operation fails
        """
        scale_map = {
            "letterbox": ScalingMethod.LETTERBOX,
            "crop": ScalingMethod.CROP_CENTER,
            "stretch": ScalingMethod.STRETCH,
        }
        self.display_image_auto(
            filename,
            mode=DisplayMode.GRAYSCALE_4,
            scaling=scale_map.get(scaling, ScalingMethod.LETTERBOX),
            invert_colors=invert,
        )

    def overlay_text(
        self, buffer: bytes, text: str, x: int = 0, y: int = 0, scale: int = 1, invert: bool = False
    ) -> bytes:
        """
        Overlay text on an existing 1-bit image buffer using Rust FFI.

        Args:
            buffer: Existing 1-bit image buffer
            text: Text string to overlay
            x: X position for text
            y: Y position for text
            scale: Text scale factor (1=normal, 2=double, etc.)
            invert: Whether to invert text colors

        Returns:
            Modified 1-bit packed image data with overlaid text

        Raises:
            DisplayError: If text overlay fails
        """
        if len(buffer) != self.ARRAY_SIZE:
            raise DisplayError(f"Buffer must be exactly {self.ARRAY_SIZE} bytes, got {len(buffer)}")

        # Validate coordinates are within display bounds
        if x < 0 or y < 0:
            raise DisplayError(f"Text position ({x}, {y}) must be non-negative")
        if x >= self.WIDTH or y >= self.HEIGHT:
            raise DisplayError(
                f"Text position ({x}, {y}) exceeds display dimensions ({self.WIDTH}x{self.HEIGHT})"
            )

        # Create mutable copy of buffer
        buffer_array = (ctypes.c_ubyte * len(buffer))(*buffer)
        text_bytes = text.encode("utf-8")

        success = self._lib.text_overlay(
            buffer_array,
            text_bytes,
            c_uint32(x),
            c_uint32(y),
            c_uint32(scale),
            c_int(1 if invert else 0),
        )

        if not success:
            raise DisplayError(f"Failed to overlay text: {text}")

        return bytes(buffer_array)

    def draw_rect(
        self,
        buffer: bytes,
        x: int,
        y: int,
        width: int,
        height: int,
        filled: bool = True,
        value: bool = True,
    ) -> bytes:
        """
        Draw a rectangle on a 1-bit image buffer using Rust FFI.

        Args:
            buffer: 1-bit image buffer to modify
            x: X position of rectangle
            y: Y position of rectangle
            width: Rectangle width
            height: Rectangle height
            filled: Whether to fill rectangle (True) or outline only (False)
            value: Fill/line value (True=white, False=black)

        Returns:
            Modified 1-bit packed image data with rectangle

        Raises:
            DisplayError: If drawing fails
        """
        if len(buffer) != self.ARRAY_SIZE:
            raise DisplayError(f"Buffer must be exactly {self.ARRAY_SIZE} bytes, got {len(buffer)}")

        # Validate rectangle coordinates and dimensions
        if x < 0 or y < 0:
            raise DisplayError(f"Rectangle position ({x}, {y}) must be non-negative")
        if width <= 0 or height <= 0:
            raise DisplayError(f"Rectangle dimensions ({width}x{height}) must be positive")

        # Check if rectangle fits within display bounds
        if x >= self.WIDTH or y >= self.HEIGHT:
            raise DisplayError(
                f"Rectangle position ({x}, {y}) exceeds display dimensions ({self.WIDTH}x{self.HEIGHT})"
            )
        if x + width > self.WIDTH or y + height > self.HEIGHT:
            raise DisplayError(
                f"Rectangle ({width}x{height} at ({x}, {y}) exceeds display dimensions ({self.WIDTH}x{self.HEIGHT})"
            )

        # Create mutable copy of buffer
        buffer_array = (ctypes.c_ubyte * len(buffer))(*buffer)

        success = self._lib.shape_draw_rect_filled(
            buffer_array,
            c_uint32(x),
            c_uint32(y),
            c_uint32(width),
            c_uint32(height),
            c_int(1 if value else 0),
        )

        if not success:
            raise DisplayError("Failed to draw rectangle")

        return bytes(buffer_array)

    def __enter__(self):
        """Context manager entry."""
        if not self._initialized:
            self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        # Return False to propagate any exceptions that occurred
        return False

    def _get_display_dimensions(self) -> Tuple[int, int]:
        """Get current display dimensions."""
        if not self._initialized:
            self.initialize()
        return self.WIDTH, self.HEIGHT

    def _convert_png_auto(
        self,
        image_path: str,
        scaling: ScalingMethod = ScalingMethod.LETTERBOX,
        dithering: DitheringMethod = DitheringMethod.FLOYD_STEINBERG,
    ) -> bytes:
        """
        Convert any image to display-compatible 1-bit raw data using Rust FFI.

        Args:
            image_path: Path to source image file
            scaling: How to scale the image to fit display
            dithering: Dithering method for 1-bit conversion

        Returns:
            Raw 1-bit image data

        Raises:
            DisplayError: If conversion fails
        """
        if not os.path.exists(image_path):
            raise DisplayError(f"Image file not found: {image_path}")

        # Use Rust image_process function
        output_data = (ctypes.c_ubyte * self.ARRAY_SIZE)()
        image_path_bytes = image_path.encode("utf-8")

        # No brightness/contrast adjustment (-999 means no adjustment)
        brightness = -999
        contrast = -999.0

        result = self._lib.image_process(
            image_path_bytes,
            int(scaling),
            int(dithering),
            brightness,
            contrast,
            0,  # Don't invert colors here
            output_data,
        )

        self._check_result(result, f"Process image '{image_path}' with auto-conversion")

        return bytes(output_data)

    def _invert_1bit(self, data: bytes) -> bytes:
        """
        Invert colors in 1-bit image data.

        Uses a hybrid approach: Python for small data (avoiding FFI overhead),
        Rust FFI for larger data where performance gains outweigh overhead.

        Args:
            data: Input 1-bit packed image data

        Returns:
            Inverted 1-bit packed data
        """
        size = len(data)

        # For small data (<4KB), use Python to avoid FFI overhead
        # This threshold is based on benchmark results showing FFI overhead
        # dominates for small operations
        if size < 4096:
            # Simple bitwise NOT operation in Python
            return bytes(~b & 0xFF for b in data)

        # For larger data, use Rust FFI for better performance
        input_array = (ctypes.c_ubyte * size)(*data)
        output_array = (ctypes.c_ubyte * size)()

        success = self._lib.image_invert_1bit(input_array, c_uint32(size), output_array)

        if not success:
            raise DisplayError("Failed to invert image colors")

        return bytes(output_array)
