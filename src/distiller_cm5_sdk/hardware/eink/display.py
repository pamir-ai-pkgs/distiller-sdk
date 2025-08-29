#!/usr/bin/env python3
"""
Display module for CM5 SDK.
Provides functionality for e-ink display control and image display.
"""

import os
import ctypes
from ctypes import c_bool, c_char_p, c_uint32, c_int, c_float, POINTER
from enum import IntEnum
from typing import Optional, Tuple, Union


class DisplayError(Exception):
    """Custom exception for Display-related errors."""

    pass


class DisplayMode(IntEnum):
    """Display refresh modes."""

    FULL = 0  # Full refresh - slow but high quality
    PARTIAL = 1  # Partial refresh - fast updates


class FirmwareType:
    """Supported e-ink display firmware types."""

    EPD128x250 = "EPD128x250"
    EPD240x416 = "EPD240x416"


class ScalingMethod(IntEnum):
    """Image scaling methods for auto-conversion."""

    LETTERBOX = 0  # Maintain aspect ratio, add black borders
    CROP_CENTER = 1  # Center crop to fill display
    STRETCH = 2  # Stretch to fill display (may distort)


class TransformType(IntEnum):
    """Image transformation types."""

    NONE = 0
    ROTATE_90 = 1
    ROTATE_180 = 2
    ROTATE_270 = 3
    FLIP_HORIZONTAL = 4
    FLIP_VERTICAL = 5


class DitheringMethod(IntEnum):
    """Dithering methods for 1-bit conversion."""

    THRESHOLD = 0  # Fast threshold conversion
    FLOYD_STEINBERG = 1  # High quality dithering
    ORDERED = 2  # Ordered dithering


class Display:
    """
    Display class for interacting with the CM5 e-ink display system.

    This class provides functionality to:
    - Display PNG images on the e-ink screen
    - Display raw 1-bit image data
    - Clear the display
    - Control display refresh modes
    - Manage display power states
    """

    # Display constants (will be updated dynamically)
    WIDTH = 128  # Default, will be updated after initialization
    HEIGHT = 250  # Default, will be updated after initialization
    ARRAY_SIZE = (128 * 250) // 8  # Default, will be updated after initialization

    def __init__(self, library_path: Optional[str] = None, auto_init: bool = True):
        """
        Initialize the Display object.

        Args:
            library_path: Optional path to the shared library. If None, searches common locations.
            auto_init: Whether to automatically initialize the display hardware

        Raises:
            DisplayError: If library can't be loaded or display can't be initialized
        """
        self._lib = None
        self._initialized = False

        # Find and load the shared library
        if library_path is None:
            library_path = self._find_library()

        if not os.path.exists(library_path):
            raise DisplayError(f"Display library not found: {library_path}")

        try:
            self._lib = ctypes.CDLL(library_path)
        except OSError as e:
            raise DisplayError(f"Failed to load display library: {e}")

        # Set up function signatures
        self._setup_function_signatures()

        if auto_init:
            self.initialize()

    def _find_library(self) -> str:
        """Find the shared library in common locations."""
        # Get the directory of this Python file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Common search paths
        search_paths = [
            # Debian package location
            "/opt/distiller-cm5-sdk/lib/libdistiller_display_sdk_shared.so",
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

        # display_image_png(const char* filename, display_mode_t mode) -> bool
        self._lib.display_image_png.restype = c_bool
        self._lib.display_image_png.argtypes = [c_char_p, ctypes.c_int]

        # display_clear() -> bool
        self._lib.display_clear.restype = c_bool
        self._lib.display_clear.argtypes = []

        # display_sleep() -> void
        self._lib.display_sleep.restype = None
        self._lib.display_sleep.argtypes = []

        # display_cleanup() -> void
        self._lib.display_cleanup.restype = None
        self._lib.display_cleanup.argtypes = []

        # display_get_dimensions(uint32_t* width, uint32_t* height) -> void
        self._lib.display_get_dimensions.restype = None
        self._lib.display_get_dimensions.argtypes = [POINTER(c_uint32), POINTER(c_uint32)]

        # convert_png_to_1bit(const char* filename, uint8_t* output_data) -> bool
        self._lib.convert_png_to_1bit.restype = c_bool
        self._lib.convert_png_to_1bit.argtypes = [c_char_p, ctypes.POINTER(ctypes.c_ubyte)]

        # Image processing functions
        # image_rotate_1bit(const uint8_t* data, uint32_t width, uint32_t height, int rotation, uint8_t* output) -> bool
        self._lib.image_rotate_1bit.restype = c_bool
        self._lib.image_rotate_1bit.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            c_uint32,
            c_uint32,
            c_int,
            ctypes.POINTER(ctypes.c_ubyte),
        ]

        # image_invert_1bit(const uint8_t* data, uint32_t size, uint8_t* output) -> bool
        self._lib.image_invert_1bit.restype = c_bool
        self._lib.image_invert_1bit.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            c_uint32,
            ctypes.POINTER(ctypes.c_ubyte),
        ]

        # image_flip_horizontal_1bit(const uint8_t* data, uint32_t width, uint32_t height, uint8_t* output) -> bool
        self._lib.image_flip_horizontal_1bit.restype = c_bool
        self._lib.image_flip_horizontal_1bit.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            c_uint32,
            c_uint32,
            ctypes.POINTER(ctypes.c_ubyte),
        ]

        # image_flip_vertical_1bit(const uint8_t* data, uint32_t width, uint32_t height, uint8_t* output) -> bool
        self._lib.image_flip_vertical_1bit.restype = c_bool
        self._lib.image_flip_vertical_1bit.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            c_uint32,
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
        #               int transform, int invert, uint8_t* output) -> bool
        self._lib.image_process.restype = c_bool
        self._lib.image_process.argtypes = [
            c_char_p,
            c_int,
            c_int,
            c_int,
            c_float,
            c_int,
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

        # Configuration functions (optional - may not exist in older libraries)
        try:
            # display_set_firmware(const char* firmware_str) -> bool
            self._lib.display_set_firmware.restype = c_bool
            self._lib.display_set_firmware.argtypes = [c_char_p]

            # display_get_firmware(char* firmware_str, uint32_t max_len) -> bool
            self._lib.display_get_firmware.restype = c_bool
            self._lib.display_get_firmware.argtypes = [ctypes.c_char_p, c_uint32]

            # display_initialize_config() -> bool
            self._lib.display_initialize_config.restype = c_bool
            self._lib.display_initialize_config.argtypes = []

            self._config_available = True
        except AttributeError:
            # Configuration functions not available in this library version
            self._config_available = False

    def initialize(self) -> None:
        """
        Initialize the display hardware.

        Raises:
            DisplayError: If initialization fails
        """
        if self._initialized:
            return

        # Initialize configuration system first (if available)
        if hasattr(self, "_config_available") and self._config_available:
            try:
                config_success = self._lib.display_initialize_config()
                if not config_success:
                    # Config initialization failed, but continue with defaults
                    print("Warning: Failed to initialize config system, using defaults")
            except Exception as e:
                print(f"Warning: Config system error: {e}")

        success = self._lib.display_init()
        if not success:
            raise DisplayError("Failed to initialize display hardware")

        # Update dimensions based on current firmware
        self._update_dimensions()

        self._initialized = True

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

        except Exception as e:
            print(f"Warning: Could not get dimensions from library: {e}")
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

    def display_image(
        self,
        image: Union[str, bytes],
        mode: DisplayMode = DisplayMode.FULL,
        rotate: Union[bool, int] = False,
        flip_horizontal: bool = False,
        flip_vertical: bool = False,
        invert_colors: bool = False,
        src_width: int = None,
        src_height: int = None,
    ) -> None:
        """
        Display an image on the e-ink screen.

        Args:
            image: Either a PNG file path (string) or raw 1-bit image data (bytes)
            mode: Display refresh mode
            rotate: Rotation angle in degrees (0, 90, 180, 270) or bool for backward compatibility
                   If True, rotate 90 degrees CCW (landscape 250x128 to portrait 128x250)
                   If False or 0, no rotation
            flip_horizontal: If True, mirror the image horizontally (left-right)
            flip_vertical: If True, mirror the image vertically (top-bottom)
            invert_colors: If True, invert colors (black↔white)
            src_width: Source width in pixels (required when transforming raw data)
            src_height: Source height in pixels (required when transforming raw data)

        Raises:
            DisplayError: If display operation fails
        """
        if not self._initialized:
            raise DisplayError("Display not initialized. Call initialize() first.")

        # Handle backward compatibility for boolean rotate parameter
        if isinstance(rotate, bool):
            rotation_degrees = 90 if rotate else 0
        else:
            rotation_degrees = rotate

        if isinstance(image, str):
            # PNG file path
            self._display_png(
                image, mode, rotation_degrees, flip_horizontal, flip_vertical, invert_colors
            )
        elif isinstance(image, (bytes, bytearray)):
            # Raw image data
            raw_data = bytes(image)

            if flip_horizontal or flip_vertical or rotation_degrees != 0 or invert_colors:
                if src_width is None or src_height is None:
                    raise DisplayError(
                        "src_width and src_height are required when transforming raw data"
                    )

                # Apply transformations using Rust FFI functions
                if flip_horizontal:
                    raw_data = self._flip_horizontal_1bit(raw_data, src_width, src_height)

                if flip_vertical:
                    raw_data = self._flip_vertical_1bit(raw_data, src_width, src_height)

                if rotation_degrees != 0:
                    raw_data = self._rotate_1bit(raw_data, src_width, src_height, rotation_degrees)

                if invert_colors:
                    raw_data = self._invert_1bit(raw_data)

            self._display_raw(raw_data, mode)
        else:
            raise DisplayError(f"Invalid image type: {type(image)}. Expected str or bytes.")

    def _display_png(
        self,
        filename: str,
        mode: DisplayMode,
        rotate: Union[bool, int] = False,
        flip_horizontal: bool = False,
        flip_vertical: bool = False,
        invert_colors: bool = False,
    ) -> None:
        """Display a PNG image file."""
        if not os.path.exists(filename):
            raise DisplayError(f"PNG file not found: {filename}")

        # Handle backward compatibility for boolean rotate parameter
        if isinstance(rotate, bool):
            rotation_degrees = 90 if rotate else 0
        else:
            rotation_degrees = rotate

        if rotation_degrees != 0 or flip_horizontal or flip_vertical or invert_colors:
            # For PNG transformations, convert to raw data first
            raw_data = self.convert_png_to_raw(filename)
            # Assume PNG is 250x128 landscape format when transforming

            # Apply transformations using Rust FFI functions
            if flip_horizontal:
                raw_data = self._flip_horizontal_1bit(raw_data, 250, 128)

            if flip_vertical:
                raw_data = self._flip_vertical_1bit(raw_data, 250, 128)

            if rotation_degrees != 0:
                raw_data = self._rotate_1bit(raw_data, 250, 128, rotation_degrees)

            if invert_colors:
                raw_data = self._invert_1bit(raw_data)

            self._display_raw(raw_data, mode)
        else:
            # Direct PNG display (must be 128x250)
            filename_bytes = filename.encode("utf-8")
            success = self._lib.display_image_png(filename_bytes, int(mode))
            if not success:
                raise DisplayError(f"Failed to display PNG image: {filename}")

    def _display_raw(self, data: bytes, mode: DisplayMode) -> None:
        """Display raw 1-bit image data."""
        if len(data) != self.ARRAY_SIZE:
            raise DisplayError(f"Data must be exactly {self.ARRAY_SIZE} bytes, got {len(data)}")

        # Convert bytes to ctypes array
        data_array = (ctypes.c_ubyte * len(data))(*data)

        success = self._lib.display_image_raw(data_array, int(mode))
        if not success:
            raise DisplayError("Failed to display raw image data")

    def clear(self) -> None:
        """
        Clear the display (set to white).

        Raises:
            DisplayError: If clear operation fails
        """
        if not self._initialized:
            raise DisplayError("Display not initialized. Call initialize() first.")

        success = self._lib.display_clear()
        if not success:
            raise DisplayError("Failed to clear display")

    def sleep(self) -> None:
        """Put display to sleep for power saving."""
        if self._initialized:
            self._lib.display_sleep()

    def convert_png_to_raw(self, filename: str) -> bytes:
        """
        Convert PNG file to raw 1-bit data.

        Args:
            filename: Path to PNG file (must be exactly 128x250 pixels)

        Returns:
            Raw 1-bit packed image data (4000 bytes)

        Raises:
            DisplayError: If conversion fails
        """
        if not os.path.exists(filename):
            raise DisplayError(f"PNG file not found: {filename}")

        # Create output buffer
        output_data = (ctypes.c_ubyte * self.ARRAY_SIZE)()
        filename_bytes = filename.encode("utf-8")

        success = self._lib.convert_png_to_1bit(filename_bytes, output_data)
        if not success:
            raise DisplayError(f"Failed to convert PNG: {filename}")

        # Convert ctypes array to bytes
        return bytes(output_data)

    def is_initialized(self) -> bool:
        """Check if display is initialized."""
        return self._initialized

    def close(self) -> None:
        """Cleanup display resources."""
        if self._initialized:
            self._lib.display_cleanup()
            self._initialized = False

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
            filled: Whether to fill the rectangle
            value: Fill/line value (True=white, False=black)

        Returns:
            Modified 1-bit packed image data with rectangle

        Raises:
            DisplayError: If drawing fails
        """
        if len(buffer) != self.ARRAY_SIZE:
            raise DisplayError(f"Buffer must be exactly {self.ARRAY_SIZE} bytes, got {len(buffer)}")

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

    def set_firmware(self, firmware_type: str) -> None:
        """
        Set the default firmware type for the display.

        Args:
            firmware_type: Firmware type string (e.g., "EPD128x250", "EPD240x416")

        Raises:
            DisplayError: If firmware type is invalid or setting fails
        """
        if not (hasattr(self, "_config_available") and self._config_available):
            raise DisplayError(
                "Configuration system not available. Please rebuild the Rust library."
            )

        firmware_bytes = firmware_type.encode("utf-8")
        success = self._lib.display_set_firmware(firmware_bytes)
        if not success:
            raise DisplayError(f"Failed to set firmware type: {firmware_type}")

    def get_firmware(self) -> str:
        """
        Get the current default firmware type.

        Returns:
            Current firmware type string

        Raises:
            DisplayError: If getting firmware fails
        """
        if not (hasattr(self, "_config_available") and self._config_available):
            raise DisplayError(
                "Configuration system not available. Please rebuild the Rust library."
            )

        buffer = ctypes.create_string_buffer(64)  # Should be enough for firmware names
        success = self._lib.display_get_firmware(buffer, 64)
        if not success:
            raise DisplayError("Failed to get current firmware type")
        return buffer.value.decode("utf-8")

    def initialize_config(self) -> None:
        """
        Initialize the configuration system.
        This loads configuration from environment variables and config files.

        Raises:
            DisplayError: If configuration initialization fails
        """
        if not (hasattr(self, "_config_available") and self._config_available):
            raise DisplayError(
                "Configuration system not available. Please rebuild the Rust library."
            )

        success = self._lib.display_initialize_config()
        if not success:
            raise DisplayError("Failed to initialize configuration system")

    def __enter__(self):
        """Context manager entry."""
        if not self._initialized:
            self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

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
        rotate: Union[bool, int] = False,
        flop: bool = False,
        flip: bool = False,
        crop_x: Optional[int] = None,
        crop_y: Optional[int] = None,
    ) -> bytes:
        """
        Convert any PNG to display-compatible 1-bit raw data using Rust FFI.

        Args:
            image_path: Path to source PNG file
            scaling: How to scale the image to fit display
            dithering: Dithering method for 1-bit conversion
            rotate: Rotation angle in degrees (0, 90, 180, 270) or bool for backward compatibility
                   If True, rotate 90 degrees counter-clockwise
                   If False or 0, no rotation
            flop: If True, flip image horizontally (left-right mirror)
            flip: If True, flip image vertically (top-bottom mirror)
            crop_x: X position for crop when using CROP_CENTER (None = center)
            crop_y: Y position for crop when using CROP_CENTER (None = center)

        Returns:
            Raw 1-bit image data

        Raises:
            DisplayError: If conversion fails
        """
        if not os.path.exists(image_path):
            raise DisplayError(f"PNG file not found: {image_path}")

        # Convert boolean rotate to degrees for backward compatibility
        if isinstance(rotate, bool):
            rotation_degrees = 90 if rotate else 0
        else:
            rotation_degrees = rotate % 360

        # Map rotation to transform type
        # Note: Rust FFI only supports one transform at a time
        # If multiple transforms are needed, we'll apply them sequentially
        transform = TransformType.NONE
        needs_additional_transforms = False

        # Determine primary transform
        if rotation_degrees == 90:
            transform = TransformType.ROTATE_90
        elif rotation_degrees == 180:
            transform = TransformType.ROTATE_180
        elif rotation_degrees == 270:
            transform = TransformType.ROTATE_270
        elif flop:
            transform = TransformType.FLIP_HORIZONTAL
        elif flip:
            transform = TransformType.FLIP_VERTICAL

        # Check if we need additional transforms
        if (flop and transform != TransformType.FLIP_HORIZONTAL) or (
            flip and transform != TransformType.FLIP_VERTICAL
        ):
            needs_additional_transforms = True

        # Use Rust image_process function
        output_data = (ctypes.c_ubyte * self.ARRAY_SIZE)()
        image_path_bytes = image_path.encode("utf-8")

        # No brightness/contrast adjustment (-999 means no adjustment)
        brightness = -999
        contrast = -999.0

        success = self._lib.image_process(
            image_path_bytes,
            int(scaling),
            int(dithering),
            brightness,
            contrast,
            int(transform),
            0,  # Don't invert colors here
            output_data,
        )

        if not success:
            raise DisplayError(f"Failed to process image: {image_path}")

        result = bytes(output_data)

        # Apply additional transforms if needed
        if needs_additional_transforms:
            # Apply horizontal flip if needed and not already applied
            if flop and transform != TransformType.FLIP_HORIZONTAL:
                result = self._flip_horizontal_1bit(result, self.WIDTH, self.HEIGHT)
            # Apply vertical flip if needed and not already applied
            if flip and transform != TransformType.FLIP_VERTICAL:
                result = self._flip_vertical_1bit(result, self.WIDTH, self.HEIGHT)

        return result

    def _rotate_1bit(self, data: bytes, width: int, height: int, degrees: int) -> bytes:
        """
        Rotate 1-bit image data using Rust FFI.

        Args:
            data: Input 1-bit packed image data
            width: Image width in pixels
            height: Image height in pixels
            degrees: Rotation angle (0, 90, 180, 270)

        Returns:
            Rotated 1-bit packed data
        """
        # Map degrees to Rust rotation enum
        rotation_map = {
            0: -1,  # No rotation
            90: 0,  # 90 degrees
            180: 1,  # 180 degrees
            270: 2,  # 270 degrees
        }

        normalized_degrees = degrees % 360
        if normalized_degrees not in rotation_map:
            # Find closest valid rotation
            closest = min(rotation_map.keys(), key=lambda x: abs(x - normalized_degrees))
            normalized_degrees = closest

        rotation = rotation_map[normalized_degrees]
        if rotation == -1:
            return data  # No rotation needed

        # Calculate output size
        if normalized_degrees in (90, 270):
            out_width, out_height = height, width
        else:
            out_width, out_height = width, height

        out_size = (out_width * out_height + 7) // 8

        # Prepare buffers
        input_array = (ctypes.c_ubyte * len(data))(*data)
        output_array = (ctypes.c_ubyte * out_size)()

        success = self._lib.image_rotate_1bit(
            input_array, c_uint32(width), c_uint32(height), c_int(rotation), output_array
        )

        if not success:
            raise DisplayError(f"Failed to rotate image by {degrees} degrees")

        return bytes(output_array)

    def _flip_horizontal_1bit(self, data: bytes, width: int, height: int) -> bytes:
        """
        Flip 1-bit image horizontally using Rust FFI.

        Args:
            data: Input 1-bit packed image data
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Flipped 1-bit packed data
        """
        expected_bytes = (width * height + 7) // 8
        if len(data) < expected_bytes:
            raise ValueError(
                f"Input data too small. Expected {expected_bytes} bytes, got {len(data)}"
            )

        # Prepare buffers
        input_array = (ctypes.c_ubyte * len(data))(*data)
        output_array = (ctypes.c_ubyte * expected_bytes)()

        success = self._lib.image_flip_horizontal_1bit(
            input_array, c_uint32(width), c_uint32(height), output_array
        )

        if not success:
            raise DisplayError("Failed to flip image horizontally")

        return bytes(output_array)

    def _flip_vertical_1bit(self, data: bytes, width: int, height: int) -> bytes:
        """
        Flip 1-bit image vertically using Rust FFI.

        Args:
            data: Input 1-bit packed image data
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Flipped 1-bit packed data
        """
        expected_bytes = (width * height + 7) // 8
        if len(data) < expected_bytes:
            raise ValueError(
                f"Input data too small. Expected {expected_bytes} bytes, got {len(data)}"
            )

        # Prepare buffers
        input_array = (ctypes.c_ubyte * len(data))(*data)
        output_array = (ctypes.c_ubyte * expected_bytes)()

        success = self._lib.image_flip_vertical_1bit(
            input_array, c_uint32(width), c_uint32(height), output_array
        )

        if not success:
            raise DisplayError("Failed to flip image vertically")

        return bytes(output_array)

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

    def display_png_auto(
        self,
        image_path: str,
        mode: DisplayMode = DisplayMode.FULL,
        scaling: ScalingMethod = ScalingMethod.LETTERBOX,
        dithering: DitheringMethod = DitheringMethod.FLOYD_STEINBERG,
        rotate: Union[bool, int] = False,
        flop: bool = False,
        flip: bool = False,
        crop_x: Optional[int] = None,
        crop_y: Optional[int] = None,
        cleanup_temp: bool = True,
    ) -> bool:
        """
        Display any PNG image with automatic conversion to display specifications.

        Args:
            image_path: Path to source PNG file
            mode: Display refresh mode
            scaling: How to scale the image to fit display
            dithering: Dithering method for 1-bit conversion
            rotate: Rotation angle in degrees (0, 90, 180, 270) or bool for backward compatibility
                   If True, rotate 90 degrees counter-clockwise
                   If False or 0, no rotation
            flop: If True, flip image horizontally (left-right mirror)
            flip: If True, flip image vertically (top-bottom mirror)
            crop_x: X position for crop when using CROP_CENTER (None = center)
            crop_y: Y position for crop when using CROP_CENTER (None = center)
            cleanup_temp: Whether to cleanup temporary files (unused, kept for API compatibility)

        Returns:
            True if successful, False otherwise

        Raises:
            DisplayError: If display operation fails
        """
        try:
            # Convert image to raw 1-bit data
            raw_data = self._convert_png_auto(
                image_path, scaling, dithering, rotate, flop, flip, crop_x, crop_y
            )

            # Display the raw data
            self._display_raw(raw_data, mode)
            return True

        except Exception as e:
            raise DisplayError(f"Failed to auto-display PNG: {e}")


# Convenience functions for simple usage (following SDK pattern)
def display_png(
    filename: str,
    mode: DisplayMode = DisplayMode.FULL,
    rotate: Union[bool, int] = False,
    auto_convert: bool = False,
    scaling: ScalingMethod = ScalingMethod.LETTERBOX,
    dithering: DitheringMethod = DitheringMethod.FLOYD_STEINBERG,
    flop: bool = False,
    flip: bool = False,
    crop_x: Optional[int] = None,
    crop_y: Optional[int] = None,
) -> None:
    """
    Convenience function to display a PNG image.

    Args:
        filename: Path to PNG file
        mode: Display refresh mode
        rotate: Rotation angle in degrees (0, 90, 180, 270) or bool for backward compatibility
               If True, rotate 90 degrees CCW (landscape 250x128 to portrait 128x250)
               If False or 0, no rotation
        auto_convert: If True, automatically convert any PNG to display format
        scaling: How to scale the image to fit display (only used with auto_convert)
        dithering: Dithering method for 1-bit conversion (only used with auto_convert)
        flop: If True, flip image horizontally (only used with auto_convert)
        flip: If True, flip image vertically (only used with auto_convert)
        crop_x: X position for crop when using CROP_CENTER with auto_convert (None = center)
        crop_y: Y position for crop when using CROP_CENTER with auto_convert (None = center)
    """
    with Display() as display:
        if auto_convert:
            display.display_png_auto(
                filename, mode, scaling, dithering, rotate, flop, flip, crop_x, crop_y
            )
        else:
            display.display_image(filename, mode, rotate)


def display_png_auto(
    filename: str,
    mode: DisplayMode = DisplayMode.FULL,
    scaling: ScalingMethod = ScalingMethod.LETTERBOX,
    dithering: DitheringMethod = DitheringMethod.FLOYD_STEINBERG,
    rotate: Union[bool, int] = False,
    flop: bool = False,
    flip: bool = False,
    crop_x: Optional[int] = None,
    crop_y: Optional[int] = None,
) -> None:
    """
    Convenience function to display any PNG image with automatic conversion.

    Args:
        filename: Path to PNG file (any size, any format)
        mode: Display refresh mode
        scaling: How to scale the image to fit display
        dithering: Dithering method for 1-bit conversion
        rotate: Rotation angle in degrees (0, 90, 180, 270) or bool for backward compatibility
               If True, rotate 90 degrees counter-clockwise
               If False or 0, no rotation
        flop: If True, flip image horizontally (left-right mirror)
        flip: If True, flip image vertically (top-bottom mirror)
        crop_x: X position for crop when using CROP_CENTER (None = center)
        crop_y: Y position for crop when using CROP_CENTER (None = center)
    """
    with Display() as display:
        display.display_png_auto(
            filename, mode, scaling, dithering, rotate, flop, flip, crop_x, crop_y
        )


def clear_display() -> None:
    """Convenience function to clear the display."""
    with Display() as display:
        display.clear()


def get_display_info() -> dict:
    """
    Get display information.

    Returns:
        Dictionary with display specs
    """
    return {
        "width": Display.WIDTH,
        "height": Display.HEIGHT,
        "data_size": Display.ARRAY_SIZE,
        "format": "1-bit monochrome",
        "type": "e-ink",
    }


# Configuration convenience functions
def set_default_firmware(firmware_type: str) -> None:
    """
    Set the default firmware type globally.

    Args:
        firmware_type: Firmware type string (e.g., FirmwareType.EPD128x250, FirmwareType.EPD240x416)

    Raises:
        DisplayError: If firmware type is invalid or setting fails

    Example:
        set_default_firmware(FirmwareType.EPD240x416)
    """
    display = Display(auto_init=False)
    display.set_firmware(firmware_type)


def get_default_firmware() -> str:
    """
    Get the current default firmware type.

    Returns:
        Current firmware type string

    Raises:
        DisplayError: If getting firmware fails

    Example:
        current_fw = get_default_firmware()
        print(f"Current firmware: {current_fw}")
    """
    display = Display(auto_init=False)
    return display.get_firmware()


def initialize_display_config() -> None:
    """
    Initialize the display configuration system.

    This loads configuration from:
    - Environment variable: DISTILLER_EINK_FIRMWARE
    - Config files: /opt/distiller-cm5-sdk/eink.conf, ./eink.conf, ~/.distiller/eink.conf
    - Falls back to EPD128x250 default

    Raises:
        DisplayError: If configuration initialization fails

    Example:
        # Set via environment variable
        import os
        os.environ['DISTILLER_EINK_FIRMWARE'] = 'EPD240x416'
        initialize_display_config()

        # Or via config file
        # echo "firmware=EPD240x416" > /opt/distiller-cm5-sdk/eink.conf
        initialize_display_config()
    """
    display = Display(auto_init=False)
    display.initialize_config()


def rotate_bitpacked(data: bytes, angle: int, width: int, height: int) -> bytes:
    """
    Rotate 1-bit packed image data by the specified angle.

    Args:
        data: 1-bit packed image data as bytes
        angle: Rotation angle (0, 90, 180, 270 degrees)
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Rotated 1-bit packed image data

    Raises:
        DisplayError: If rotation fails or invalid angle
    """
    if angle not in [0, 90, 180, 270]:
        raise DisplayError(f"Invalid rotation angle: {angle}. Must be 0, 90, 180, or 270")

    display = Display(auto_init=False)

    # Convert angle to rotation value expected by C function
    # Note: The C function has a non-intuitive mapping:
    # 0 = rotate 90 degrees
    # 1 = rotate 180 degrees
    # 2 = rotate 270 degrees
    # For angle 0 (no rotation), we just return the original data
    if angle == 0:
        return data

    rotation_map = {90: 0, 180: 1, 270: 2}
    rotation = rotation_map[angle]

    # Calculate output dimensions
    if angle in [90, 270]:
        out_width, out_height = height, width
    else:
        out_width, out_height = width, height

    # Calculate output size
    output_size = (out_width * out_height + 7) // 8

    # Create output buffer
    output = (ctypes.c_ubyte * output_size)()

    # Create input array from bytes
    input_array = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)

    # Call C function
    success = display._lib.image_rotate_1bit(input_array, width, height, rotation, output)

    if not success:
        raise DisplayError(f"Failed to rotate image by {angle} degrees")

    return bytes(output)


def rotate_bitpacked_ccw_90(data: bytes, width: int, height: int) -> bytes:
    """
    Rotate 1-bit packed image data 90 degrees counter-clockwise.

    Args:
        data: 1-bit packed image data as bytes
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Rotated 1-bit packed image data
    """
    return rotate_bitpacked(data, 90, width, height)


def rotate_bitpacked_cw_90(data: bytes, width: int, height: int) -> bytes:
    """
    Rotate 1-bit packed image data 90 degrees clockwise.

    Args:
        data: 1-bit packed image data as bytes
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Rotated 1-bit packed image data
    """
    return rotate_bitpacked(data, 270, width, height)


def rotate_bitpacked_180(data: bytes, width: int, height: int) -> bytes:
    """
    Rotate 1-bit packed image data 180 degrees.

    Args:
        data: 1-bit packed image data as bytes
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Rotated 1-bit packed image data
    """
    return rotate_bitpacked(data, 180, width, height)


def flip_bitpacked_horizontal(data: bytes, width: int, height: int) -> bytes:
    """
    Flip 1-bit packed image data horizontally (mirror).

    Args:
        data: 1-bit packed image data as bytes
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Horizontally flipped 1-bit packed image data

    Raises:
        DisplayError: If flip operation fails
    """
    display = Display(auto_init=False)

    # Calculate buffer size
    buffer_size = (width * height + 7) // 8

    # Create output buffer
    output = (ctypes.c_ubyte * buffer_size)()

    # Create input array from bytes
    input_array = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)

    # Call C function
    success = display._lib.image_flip_horizontal_1bit(input_array, width, height, output)

    if not success:
        raise DisplayError("Failed to flip image horizontally")

    return bytes(output)


def flip_bitpacked_vertical(data: bytes, width: int, height: int) -> bytes:
    """
    Flip 1-bit packed image data vertically.

    Args:
        data: 1-bit packed image data as bytes
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Vertically flipped 1-bit packed image data

    Raises:
        DisplayError: If flip operation fails
    """
    display = Display(auto_init=False)

    # Calculate buffer size
    buffer_size = (width * height + 7) // 8

    # Create output buffer
    output = (ctypes.c_ubyte * buffer_size)()

    # Create input array from bytes
    input_array = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)

    # Call C function
    success = display._lib.image_flip_vertical_1bit(input_array, width, height, output)

    if not success:
        raise DisplayError("Failed to flip image vertically")

    return bytes(output)


def invert_bitpacked_colors(data: bytes) -> bytes:
    """
    Invert the colors in 1-bit packed image data (black to white, white to black).

    Args:
        data: 1-bit packed image data as bytes

    Returns:
        Inverted 1-bit packed image data

    Raises:
        DisplayError: If invert operation fails
    """
    display = Display(auto_init=False)

    # Create output buffer same size as input
    output = (ctypes.c_ubyte * len(data))()

    # Create input array from bytes
    input_array = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)

    # Call C function
    success = display._lib.image_invert_1bit(input_array, len(data), output)

    if not success:
        raise DisplayError("Failed to invert image colors")

    return bytes(output)
