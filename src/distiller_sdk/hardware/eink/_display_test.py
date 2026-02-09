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
from unittest.mock import Mock, patch

from distiller_sdk.hardware.eink import (
    Display,
    DisplayMode,
)

# Configure logging for tests (comment out to reduce noise)
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )


class TestDisplay(unittest.TestCase):
    """Test cases for Display class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the library loading to avoid hardware dependencies
        # Note: FFI functions now return error codes (1=success, negative=error)
        self.mock_lib = Mock()
        self.mock_lib.display_init.return_value = 1  # SUCCESS
        self.mock_lib.display_clear.return_value = 1  # SUCCESS
        self.mock_lib.display_image_auto.return_value = 1  # SUCCESS
        self.mock_lib.display_image_raw.return_value = 1  # SUCCESS
        self.mock_lib.convert_png_to_1bit.return_value = 1  # SUCCESS
        self.mock_lib.display_initialize_config.return_value = 1  # SUCCESS
        self.mock_lib.display_cleanup.return_value = None
        self.mock_lib.display_sleep.return_value = None
        self.mock_lib.display_init_logger.return_value = None

        self.mock_lib.display_get_dimensions.return_value = None

    def _mock_dimensions(self, width_ref, height_ref):
        """Helper to mock display dimensions (250x128 landscape)."""
        width_ref.contents.value = 250
        height_ref.contents.value = 128

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_initialization(self, mock_exists, mock_cdll):
        """Test display initialization."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        display = Display(auto_init=True)

        self.assertTrue(display.is_initialized())
        self.mock_lib.display_init.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_clear(self, mock_exists, mock_cdll):
        """Test display clear functionality."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        display = Display(auto_init=True)
        display.clear()

        self.mock_lib.display_clear.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_image_auto_with_file(self, mock_exists, mock_cdll):
        """Test display_image_auto with a file path."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            display = Display(auto_init=True)
            display.display_image_auto(tmp_path, DisplayMode.FULL)

            self.mock_lib.display_image_auto.assert_called_once()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_image_auto_with_raw_data(self, mock_exists, mock_cdll):
        """Test display_image_auto with raw 1-bit data."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        display = Display(auto_init=True)

        array_size = (250 * 128) // 8
        test_data = bytes([0xFF] * array_size)
        display.display_image_auto(test_data, DisplayMode.PARTIAL)

        # Raw bytes go through _display_raw -> display_image_raw, not display_image_auto
        self.mock_lib.display_image_raw.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_context_manager(self, mock_exists, mock_cdll):
        """Test context manager functionality."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        with Display(auto_init=False) as display:
            self.assertTrue(display.is_initialized())

        self.mock_lib.display_cleanup.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_get_dimensions(self, mock_exists, mock_cdll):
        """Test getting display dimensions (250x128 landscape)."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        display = Display(auto_init=True)
        width, height = display.get_dimensions()

        self.assertEqual(width, 250)
        self.assertEqual(height, 128)

    def test_display_modes(self):
        """Test display mode enum."""
        self.assertEqual(DisplayMode.FULL, 0)
        self.assertEqual(DisplayMode.PARTIAL, 1)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_image_auto_not_initialized(self, mock_exists, mock_cdll):
        """Test display_image_auto raises error when not initialized."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_init.return_value = -5  # NOT_INITIALIZED error

        from distiller_sdk.hardware.eink.display import DisplayError

        with self.assertRaises(DisplayError):
            Display(auto_init=True)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_image_auto_file_not_found(self, mock_exists, mock_cdll):
        """Test display_image_auto raises error for missing file."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        display = Display(auto_init=True)

        from distiller_sdk.hardware.eink.display import DisplayError

        # os.path.exists is mocked to True globally, so override for file check
        with patch("os.path.exists", side_effect=lambda p: p != "/nonexistent.png"):
            with self.assertRaises(DisplayError):
                display.display_image_auto("/nonexistent.png")

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_sleep(self, mock_exists, mock_cdll):
        """Test display sleep."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib

        display = Display(auto_init=True)
        display.sleep()

        self.mock_lib.display_sleep.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_text(self, mock_exists, mock_cdll):
        """Test display_text method."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_text.return_value = 1  # SUCCESS

        display = Display(auto_init=True)
        display.display_text("Hello", x=0, y=0, scale=2)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_get_dimensions_returns_landscape(self, mock_exists, mock_cdll):
        """Test get_dimensions returns landscape (250x128) dimensions."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        display = Display(auto_init=True)
        width, height = display.get_dimensions()

        self.assertEqual(width, 250)
        self.assertEqual(height, 128)
        self.assertGreater(width, height, "Width should be greater than height (landscape)")


def run_display_tests():
    """Main function to run display tests."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_display_tests()
