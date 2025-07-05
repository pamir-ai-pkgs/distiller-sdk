#!/usr/bin/env python3
"""
Display module for CM5 SDK.
Provides functionality for e-ink display control and image display.
"""

import os
import ctypes
from ctypes import c_bool, c_char_p, c_uint32, POINTER
from enum import IntEnum
from typing import Optional, Tuple, Union
import tempfile


class DisplayError(Exception):
    """Custom exception for Display-related errors."""
    pass


class DisplayMode(IntEnum):
    """Display refresh modes."""
    FULL = 0      # Full refresh - slow but high quality
    PARTIAL = 1   # Partial refresh - fast updates


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
    
    # Display constants
    WIDTH = 128
    HEIGHT = 250
    ARRAY_SIZE = (WIDTH * HEIGHT) // 8  # 4000 bytes for 1-bit data
    
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
            f"Could not find libdistiller_display_sdk_shared.so in any of these locations:\n" +
            "\n".join(f"  - {path}" for path in search_paths)
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
    
    def initialize(self) -> None:
        """
        Initialize the display hardware.
        
        Raises:
            DisplayError: If initialization fails
        """
        if self._initialized:
            return
        
        success = self._lib.display_init()
        if not success:
            raise DisplayError("Failed to initialize display hardware")
        
        self._initialized = True
    
    def display_image(self, image: Union[str, bytes], mode: DisplayMode = DisplayMode.FULL, rotate: bool = False, flip_horizontal: bool = False, invert_colors: bool = False, src_width: int = None, src_height: int = None) -> None:
        """
        Display an image on the e-ink screen.
        
        Args:
            image: Either a PNG file path (string) or raw 1-bit image data (bytes)
            mode: Display refresh mode
            rotate: If True, rotate landscape data (250x128) to portrait (128x250) 
            flip_horizontal: If True, mirror the image horizontally (left-right)
            invert_colors: If True, invert colors (black↔white)
            src_width: Source width in pixels (required when transforming raw data)
            src_height: Source height in pixels (required when transforming raw data)
            
        Raises:
            DisplayError: If display operation fails
        """
        if not self._initialized:
            raise DisplayError("Display not initialized. Call initialize() first.")
        
        if isinstance(image, str):
            # PNG file path
            self._display_png(image, mode, rotate, flip_horizontal, invert_colors)
        elif isinstance(image, (bytes, bytearray)):
            # Raw image data
            raw_data = bytes(image)
            
            if flip_horizontal or rotate or invert_colors:
                if src_width is None or src_height is None:
                    raise DisplayError("src_width and src_height are required when transforming raw data")
                
                # Apply transformations in DistillerGUI order: flip, rotate, then invert colors
                if flip_horizontal:
                    raw_data = flip_bitpacked_horizontal(raw_data, src_width, src_height)
                
                if rotate:
                    # If we flipped, dimensions stay the same for rotation
                    raw_data = rotate_bitpacked_ccw_90(raw_data, src_width, src_height)
                
                if invert_colors:
                    raw_data = invert_bitpacked_colors(raw_data)
            
            self._display_raw(raw_data, mode)
        else:
            raise DisplayError(f"Invalid image type: {type(image)}. Expected str or bytes.")
    
    def _display_png(self, filename: str, mode: DisplayMode, rotate: bool = False, flip_horizontal: bool = False, invert_colors: bool = False) -> None:
        """Display a PNG image file."""
        if not os.path.exists(filename):
            raise DisplayError(f"PNG file not found: {filename}")
        
        if rotate or flip_horizontal or invert_colors:
            # For PNG transformations, convert to raw data first
            raw_data = self.convert_png_to_raw(filename)
            # Assume PNG is 250x128 landscape format when transforming
            
            # Apply transformations in DistillerGUI order: flip, rotate, then invert colors
            if flip_horizontal:
                raw_data = flip_bitpacked_horizontal(raw_data, 250, 128)
                
            if rotate:
                raw_data = rotate_bitpacked_ccw_90(raw_data, 250, 128)
                
            if invert_colors:
                raw_data = invert_bitpacked_colors(raw_data)
                
            self._display_raw(raw_data, mode)
        else:
            # Direct PNG display (must be 128x250)
            filename_bytes = filename.encode('utf-8')
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
    
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get display dimensions.
        
        Returns:
            Tuple of (width, height) in pixels
        """
        width = c_uint32()
        height = c_uint32()
        self._lib.display_get_dimensions(ctypes.byref(width), ctypes.byref(height))
        return (width.value, height.value)
    
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
        filename_bytes = filename.encode('utf-8')
        
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
    
    def __enter__(self):
        """Context manager entry."""
        if not self._initialized:
            self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions for simple usage (following SDK pattern)
def display_png(filename: str, mode: DisplayMode = DisplayMode.FULL, rotate: bool = False) -> None:
    """
    Convenience function to display a PNG image.
    
    Args:
        filename: Path to PNG file 
        mode: Display refresh mode
        rotate: If True, rotate landscape PNG (250x128) to portrait (128x250)
    """
    with Display() as display:
        display.display_image(filename, mode, rotate)


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
        "type": "e-ink"
    }


def rotate_bitpacked_ccw_90(src_data: bytes, src_width: int, src_height: int) -> bytes:
    """
    Rotate 1-bit packed bitmap data 90 degrees counter-clockwise.
    
    This function converts landscape data (e.g., 250x128) to portrait data (e.g., 128x250)
    for display on portrait-oriented e-ink screens.
    
    Args:
        src_data: Source 1-bit packed image data
        src_width: Source image width in pixels  
        src_height: Source image height in pixels
        
    Returns:
        Rotated 1-bit packed data with dimensions (src_height x src_width)
        
    Raises:
        ValueError: If data size doesn't match expected size
    """
    # Validate input data size
    expected_bytes = (src_width * src_height + 7) // 8
    if len(src_data) < expected_bytes:
        raise ValueError(f"Input data too small. Expected {expected_bytes} bytes, got {len(src_data)}")
    
    # Calculate destination dimensions and buffer size
    dst_width = src_height
    dst_height = src_width  
    dst_bytes = (dst_width * dst_height + 7) // 8
    
    # Initialize destination buffer (all zeros = white)
    dst_data = bytearray(dst_bytes)
    
    # For each pixel in source
    for src_y in range(src_height):
        for src_x in range(src_width):
            # Get bit from source - MSB first
            src_bit_idx = src_y * src_width + src_x
            src_byte_idx = src_bit_idx // 8
            src_bit_pos = 7 - (src_bit_idx % 8)  # MSB first
            src_bit = (src_data[src_byte_idx] >> src_bit_pos) & 1
            
            # Calculate destination coordinates (counter-clockwise rotation)
            dst_x = src_y
            dst_y = src_width - 1 - src_x
            
            # Set bit in destination - MSB first
            dst_bit_idx = dst_y * dst_width + dst_x  
            dst_byte_idx = dst_bit_idx // 8
            dst_bit_pos = 7 - (dst_bit_idx % 8)  # MSB first
            
            if src_bit:
                dst_data[dst_byte_idx] |= (1 << dst_bit_pos)
    
    return bytes(dst_data)


def flip_bitpacked_horizontal(src_data: bytes, src_width: int, src_height: int) -> bytes:
    """
    Flip 1-bit packed bitmap data horizontally (left-right mirror).
    
    This function mirrors the image horizontally, which is useful for correcting
    display orientation issues or mirrored content.
    
    Args:
        src_data: Source 1-bit packed image data
        src_width: Source image width in pixels  
        src_height: Source image height in pixels
        
    Returns:
        Horizontally flipped 1-bit packed data with same dimensions
        
    Raises:
        ValueError: If data size doesn't match expected size
    """
    # Validate input data size
    expected_bytes = (src_width * src_height + 7) // 8
    if len(src_data) < expected_bytes:
        raise ValueError(f"Input data too small. Expected {expected_bytes} bytes, got {len(src_data)}")
    
    # Initialize destination buffer (same size as source)
    dst_data = bytearray(expected_bytes)
    
    # Flip horizontally: for each row, reverse the column order
    for y in range(src_height):
        for x in range(src_width):
            # Get bit from source position
            src_bit_idx = y * src_width + x
            src_byte_idx = src_bit_idx // 8
            src_bit_pos = 7 - (src_bit_idx % 8)  # MSB first
            src_bit = (src_data[src_byte_idx] >> src_bit_pos) & 1
            
            # Calculate flipped x position (mirror horizontally)
            flipped_x = src_width - 1 - x
            
            # Set bit in flipped position
            dst_bit_idx = y * src_width + flipped_x
            dst_byte_idx = dst_bit_idx // 8
            dst_bit_pos = 7 - (dst_bit_idx % 8)  # MSB first
            
            if src_bit:
                dst_data[dst_byte_idx] |= (1 << dst_bit_pos)
    
    return bytes(dst_data)


def invert_bitpacked_colors(src_data: bytes) -> bytes:
    """
    Invert colors in 1-bit packed bitmap data (black↔white).
    
    This function flips all bits to invert the colors, which is needed
    for some e-ink displays that have inverted color interpretation.
    
    Args:
        src_data: Source 1-bit packed image data
        
    Returns:
        Color-inverted 1-bit packed data (same size as input)
    """
    # Invert all bits in the data (flip white<->black)
    return bytes(~byte & 0xFF for byte in src_data) 