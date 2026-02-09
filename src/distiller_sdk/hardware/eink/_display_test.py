#!/usr/bin/env python3
"""
Display module unit tests for Distiller SDK.

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
        self.mock_lib.display_set_partial_base_map.return_value = 1  # SUCCESS

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

    def test_display_modes_fast_turbo(self):
        """Test Fast and Turbo display mode enum values."""
        self.assertEqual(DisplayMode.FAST, 2)
        self.assertEqual(DisplayMode.TURBO, 3)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_set_partial_base_map(self, mock_exists, mock_cdll):
        """Test set_partial_base_map with raw data."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions
        self.mock_lib.display_set_partial_base_map.return_value = 1  # SUCCESS

        display = Display(auto_init=True)

        array_size = (250 * 128) // 8
        test_data = bytes([0xFF] * array_size)
        display.set_partial_base_map(test_data)

        self.mock_lib.display_set_partial_base_map.assert_called_once()

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_grayscale_lifecycle(self, mock_exists, mock_cdll):
        """Test display_grayscale routes through Rust display_image_auto with GRAYSCALE_4."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        display = Display(auto_init=True)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            display.display_grayscale(tmp_path)

            # Verify Rust FFI was called with mode=4 (GRAYSCALE_4)
            call_args = self.mock_lib.display_image_auto.call_args
            self.assertEqual(call_args[0][1], 4)  # mode=GRAYSCALE_4
            # Verify no cleanup/reinit cycle (Rust handled it natively)
            self.mock_lib.display_cleanup.assert_not_called()
            self.assertTrue(display.is_initialized())
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_image_auto_with_fast_mode(self, mock_exists, mock_cdll):
        """Test display_image_auto passes FAST mode (2) to FFI."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            display = Display(auto_init=True)
            display.display_image_auto(tmp_path, DisplayMode.FAST)

            call_args = self.mock_lib.display_image_auto.call_args
            # mode is the second argument (index 1) - verify it's FAST (2)
            self.assertEqual(call_args[0][1], 2)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_image_auto_with_turbo_mode(self, mock_exists, mock_cdll):
        """Test display_image_auto passes TURBO mode (3) to FFI."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            display = Display(auto_init=True)
            display.display_image_auto(tmp_path, DisplayMode.TURBO)

            call_args = self.mock_lib.display_image_auto.call_args
            # mode is the second argument (index 1) - verify it's TURBO (3)
            self.assertEqual(call_args[0][1], 3)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_display_mode_grayscale4(self):
        """Test GRAYSCALE_4 display mode enum value."""
        self.assertEqual(DisplayMode.GRAYSCALE_4, 4)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_image_auto_grayscale4(self, mock_exists, mock_cdll):
        """Test display_image_auto passes GRAYSCALE_4 mode (4) to FFI."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            display = Display(auto_init=True)
            display.display_image_auto(tmp_path, DisplayMode.GRAYSCALE_4)

            call_args = self.mock_lib.display_image_auto.call_args
            # mode=4 (GRAYSCALE_4), invert=0 (default)
            self.assertEqual(call_args[0][1], 4)
            self.assertEqual(call_args[0][4], 0)  # invert=False
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_image_auto_grayscale4_with_invert(self, mock_exists, mock_cdll):
        """Test display_image_auto passes invert=1 to FFI when invert_colors=True."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            display = Display(auto_init=True)
            display.display_image_auto(
                tmp_path, DisplayMode.GRAYSCALE_4, invert_colors=True
            )

            call_args = self.mock_lib.display_image_auto.call_args
            self.assertEqual(call_args[0][1], 4)  # mode=GRAYSCALE_4
            self.assertEqual(call_args[0][4], 1)  # invert=True
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_image_auto_grayscale4_raw_bytes_error(self, mock_exists, mock_cdll):
        """Test display_image_auto rejects raw bytes for GRAYSCALE_4 mode."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        display = Display(auto_init=True)

        from distiller_sdk.hardware.eink.display import DisplayError

        array_size = (250 * 128) // 8
        test_data = bytes([0xFF] * array_size)

        with self.assertRaises(DisplayError) as ctx:
            display.display_image_auto(test_data, DisplayMode.GRAYSCALE_4)

        self.assertIn("file path", str(ctx.exception))

    @patch("ctypes.CDLL")
    @patch("os.path.exists")
    def test_display_grayscale_wrapper_scaling(self, mock_exists, mock_cdll):
        """Test display_grayscale maps string scaling to enum and delegates."""
        mock_exists.return_value = True
        mock_cdll.return_value = self.mock_lib
        self.mock_lib.display_get_dimensions.side_effect = self._mock_dimensions

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            display = Display(auto_init=True)

            # Test "crop" maps to ScalingMethod.CROP_CENTER (1)
            display.display_grayscale(tmp_path, scaling="crop")

            call_args = self.mock_lib.display_image_auto.call_args
            self.assertEqual(call_args[0][1], 4)  # mode=GRAYSCALE_4
            self.assertEqual(call_args[0][2], 1)  # scaling=CROP_CENTER
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


def run_display_tests():
    """Main function to run display tests."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_display_tests()
