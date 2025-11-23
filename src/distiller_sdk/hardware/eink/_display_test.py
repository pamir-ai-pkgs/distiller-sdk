#!/usr/bin/env python3
"""
Display module unit tests for CM5 SDK.

Logging Configuration:
    This test demonstrates logging configuration for the display module.
    Configure logging to see debug output:

    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    For Rust-level logging, set RUST_LOG environment variable:
        export RUST_LOG=debug
        python -m distiller_sdk.hardware.eink._display_test
"""

import unittest
import os
import tempfile
from typing import Any
from unittest.mock import Mock, patch

from distiller_sdk.hardware.eink import (
    Display,
    DisplayMode,
    get_display_info,
    FirmwareType,
    set_default_firmware,
    get_default_firmware,
)

# Configure logging for tests (comment out to reduce noise)
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )


class TestDisplay(unittest.TestCase):
    """Test cases for Display class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock the library loading to avoid hardware dependencies
        # Note: FFI functions now return error codes (1=success, negative=error)
        self.mock_lib = Mock()
        self.mock_lib.display_init.return_value = 1  # SUCCESS
        self.mock_lib.display_clear.return_value = 1  # SUCCESS
        self.mock_lib.display_image_png.return_value = 1  # SUCCESS
        self.mock_lib.display_image_raw.return_value = 1  # SUCCESS
        self.mock_lib.display_image_file.return_value = 1  # SUCCESS
        self.mock_lib.display_image_auto.return_value = 1  # SUCCESS
        self.mock_lib.convert_png_to_1bit.return_value = 1  # SUCCESS
        self.mock_lib.display_initialize_config.return_value = 1  # SUCCESS
        self.mock_lib.display_cleanup.return_value = None
        self.mock_lib.display_sleep.return_value = None
        self.mock_lib.display_init_logger.return_value = None

        # Mock dimensions - return void, but we'll override the method
        self.mock_lib.display_get_dimensions.return_value = None

        # Store original firmware setting to restore after tests
        self.original_firmware = get_default_firmware()

    def tearDown(self) -> None:
        """Clean up after tests."""
        # Restore original firmware setting
        set_default_firmware(self.original_firmware)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_initialization(self, mock_exists: Any, mock_cdll: Any) -> None:
        """Test display initialization."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        display = Display(auto_init=True)

        self.assertTrue(display.is_initialized())
        self.mock_lib.display_init.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_clear(self, mock_exists: Any, mock_cdll: Any) -> None:
        """Test display clear functionality."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        display = Display(auto_init=True)
        display.clear()

        self.mock_lib.display_clear.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_png(self, mock_exists: Any, mock_cdll: Any) -> None:
        """Test PNG display functionality."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        # Create a temporary PNG file path
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            display = Display(auto_init=True)
            display.display_image(tmp_path, DisplayMode.FULL)

            self.mock_lib.display_image_png.assert_called_once()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_raw_data_epd128x250(self, mock_exists: Any, mock_cdll: Any) -> None:
        """Test raw data display functionality with EPD128x250."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        # Set firmware to EPD128x250
        set_default_firmware(FirmwareType.EPD128x250)

        # Mock dimensions for EPD128x250
        def mock_get_dimensions_128x250(width_ref: Any, height_ref: Any) -> None:
            width_ref._obj.value = 128
            height_ref._obj.value = 250

        self.mock_lib.display_get_dimensions.side_effect = mock_get_dimensions_128x250

        display = Display(auto_init=True)

        # Create test data of correct size for 128x250 (4000 bytes)
        array_size = (128 * 250) // 8
        test_data = bytes([0xFF] * array_size)
        display.display_image(test_data, DisplayMode.PARTIAL)

        self.mock_lib.display_image_raw.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_raw_data_epd240x416(self, mock_exists: Any, mock_cdll: Any) -> None:
        """Test raw data display functionality with EPD240x416."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        # Set firmware to EPD240x416
        set_default_firmware(FirmwareType.EPD240x416)

        # Mock dimensions for EPD240x416
        def mock_get_dimensions_240x416(width_ref: Any, height_ref: Any) -> None:
            width_ref._obj.value = 240
            height_ref._obj.value = 416

        self.mock_lib.display_get_dimensions.side_effect = mock_get_dimensions_240x416

        display = Display(auto_init=True)

        # Create test data of correct size for 240x416 (12480 bytes)
        array_size = (240 * 416) // 8
        test_data = bytes([0xFF] * array_size)
        display.display_image(test_data, DisplayMode.PARTIAL)

        self.mock_lib.display_image_raw.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_context_manager(self, mock_exists: Any, mock_cdll: Any) -> None:
        """Test context manager functionality."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        with Display(auto_init=False) as display:
            self.assertTrue(display.is_initialized())

        self.mock_lib.display_cleanup.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_get_dimensions_epd128x250(self, mock_exists: Any, mock_cdll: Any) -> None:
        """Test getting display dimensions for EPD128x250."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        # Set firmware to EPD128x250
        set_default_firmware(FirmwareType.EPD128x250)

        # Mock the get_dimensions function with proper ctypes behavior
        def mock_get_dimensions(width_ref: Any, height_ref: Any) -> None:
            width_ref._obj.value = 128
            height_ref._obj.value = 250

        self.mock_lib.display_get_dimensions.side_effect = mock_get_dimensions

        display = Display(auto_init=True)
        width, height = display.get_dimensions()

        self.assertEqual(width, 128)
        self.assertEqual(height, 250)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_get_dimensions_epd240x416(self, mock_exists: Any, mock_cdll: Any) -> None:
        """Test getting display dimensions for EPD240x416."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        # Set firmware to EPD240x416
        set_default_firmware(FirmwareType.EPD240x416)

        # Mock the get_dimensions function with proper ctypes behavior
        def mock_get_dimensions(width_ref: Any, height_ref: Any) -> None:
            width_ref._obj.value = 240
            height_ref._obj.value = 416

        self.mock_lib.display_get_dimensions.side_effect = mock_get_dimensions

        display = Display(auto_init=True)
        width, height = display.get_dimensions()

        self.assertEqual(width, 240)
        self.assertEqual(height, 416)

    def test_firmware_configuration(self) -> None:
        """Test firmware configuration system."""
        # Test setting and getting firmware
        original = get_default_firmware()

        # Test setting to EPD240x416
        set_default_firmware(FirmwareType.EPD240x416)
        current = get_default_firmware()
        self.assertEqual(current, FirmwareType.EPD240x416)

        # Test setting back to EPD128x250
        set_default_firmware(FirmwareType.EPD128x250)
        current = get_default_firmware()
        self.assertEqual(current, FirmwareType.EPD128x250)

        # Restore original
        set_default_firmware(original)

    def test_display_modes(self) -> None:
        """Test display mode enum."""
        self.assertEqual(DisplayMode.FULL, 0)
        self.assertEqual(DisplayMode.PARTIAL, 1)

    def test_convenience_functions(self) -> None:
        """Test convenience functions with current firmware."""
        # Test with EPD128x250
        set_default_firmware(FirmwareType.EPD128x250)
        info = get_display_info()

        self.assertIn("width", info)
        self.assertIn("height", info)
        self.assertIn("data_size", info)

        # Values should reflect current firmware configuration
        self.assertIsInstance(info["width"], int)
        self.assertIsInstance(info["height"], int)
        self.assertIsInstance(info["data_size"], int)
        self.assertGreater(info["width"], 0)
        self.assertGreater(info["height"], 0)
        self.assertGreater(info["data_size"], 0)


def run_display_tests() -> None:
    """Main function to run display tests."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_display_tests()
