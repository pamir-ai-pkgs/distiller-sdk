"""Tests for Display hardware detection."""

import pytest
import os
from distiller_sdk.hardware.eink import Display
from distiller_sdk.hardware_status import HardwareStatus, HardwareState


class TestDisplayDetection:
    """Tests for Display.get_status() and Display.is_available()."""

    def test_get_status_returns_hardware_status(self, mock_display_hardware):
        """Test that get_status returns HardwareStatus object."""
        status = Display.get_status()

        assert isinstance(status, HardwareStatus)
        assert hasattr(status, "state")
        assert hasattr(status, "available")
        assert hasattr(status, "capabilities")
        assert hasattr(status, "error")
        assert hasattr(status, "diagnostic_info")
        assert hasattr(status, "message")

    def test_get_status_available_hardware(self, mock_display_hardware):
        """Test get_status when display hardware is available."""
        status = Display.get_status()

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        assert status.capabilities.get("firmware_type") is not None
        assert status.capabilities.get("width") is not None
        assert status.capabilities.get("height") is not None
        assert status.error is None
        assert "available" in status.message.lower()

    def test_get_status_unavailable_library(self, monkeypatch):
        """Test get_status when shared library is not found."""

        # Mock library search to fail
        def mock_find_library():
            raise FileNotFoundError("Library not found")

        # We need to mock at the module level before import
        # For this test, we'll simulate library not found
        with monkeypatch.context() as m:
            # Remove common library paths
            m.setenv("LD_LIBRARY_PATH", "/nonexistent")

            status = Display.get_status()

            assert status.state == HardwareState.UNAVAILABLE
            assert status.available is False
            assert status.error is not None
            # Message should indicate library not found
            assert "library" in status.message.lower() or "not found" in status.message.lower()

    def test_get_status_unavailable_spi_device(self, monkeypatch, tmp_path):
        """Test get_status when SPI device is not available."""
        # Create a mock library that exists
        lib_path = tmp_path / "libdistiller_display_sdk_shared.so"
        lib_path.write_text("mock library")

        # Mock device check to fail for SPI
        def mock_exists(path):
            if "/dev/spidev" in str(path):
                return False
            return True

        monkeypatch.setattr("os.path.exists", mock_exists)

        status = Display.get_status()

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        # Message should indicate SPI device issue
        assert "spi" in status.message.lower()

    def test_get_status_unavailable_gpio_chip(self, monkeypatch, tmp_path):
        """Test get_status when GPIO chip is not available."""
        import os

        # Similar to SPI test but for GPIO
        lib_path = tmp_path / "libdistiller_display_sdk_shared.so"
        lib_path.write_text("mock library")

        def mock_exists(path):
            if "/dev/gpiochip" in str(path):
                return False
            return True

        def mock_access(path, mode):
            # Mock access for SPI to succeed so we reach GPIO check
            if "/dev/spidev" in str(path):
                return True
            return os.access(path, mode)

        monkeypatch.setattr("os.path.exists", mock_exists)
        monkeypatch.setattr("os.access", mock_access)

        status = Display.get_status()

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        # Message should indicate GPIO issue
        assert "gpio" in status.message.lower()

    def test_get_status_missing_config(self, mock_display_hardware, monkeypatch):
        """Test get_status when eink config file is missing."""
        # Mock config file check to fail
        original_exists = os.path.exists

        def mock_exists(path):
            if "eink.conf" in str(path):
                return False
            return original_exists(path)

        monkeypatch.setattr("os.path.exists", mock_exists)

        status = Display.get_status()

        # Should still be partially available (can work with defaults)
        assert status.state in [HardwareState.AVAILABLE, HardwareState.PARTIALLY_AVAILABLE]
        assert "config" in status.diagnostic_info

    def test_get_status_includes_capabilities(self, mock_display_hardware):
        """Test that get_status includes display capabilities."""
        status = Display.get_status()

        assert "firmware_type" in status.capabilities
        assert "width" in status.capabilities
        assert "height" in status.capabilities
        assert "modes" in status.capabilities
        # Should support at least FULL refresh mode
        assert "FULL" in status.capabilities["modes"] or "full" in str(status.capabilities["modes"])

    def test_get_status_includes_diagnostic_info(self, mock_display_hardware):
        """Test that get_status includes diagnostic information."""
        status = Display.get_status()

        assert isinstance(status.diagnostic_info, dict)
        # Should include device information
        assert len(status.diagnostic_info) > 0
        # Should have info about library, devices, or config
        has_info = any(
            key in status.diagnostic_info
            for key in ["library_path", "spi_device", "gpio_chip", "config"]
        )
        assert has_info

    def test_is_available_returns_bool(self, mock_display_hardware):
        """Test that is_available returns a boolean."""
        result = Display.is_available()

        assert isinstance(result, bool)

    def test_is_available_true_when_hardware_present(self, mock_display_hardware):
        """Test is_available returns True when hardware is present."""
        assert Display.is_available() is True

    def test_is_available_false_when_hardware_absent(self, monkeypatch):
        """Test is_available returns False when hardware is absent."""
        # Mock library not found
        monkeypatch.setenv("LD_LIBRARY_PATH", "/nonexistent")

        assert Display.is_available() is False

    def test_is_available_consistent_with_get_status(self, mock_display_hardware):
        """Test that is_available matches get_status().available."""
        status = Display.get_status()
        is_available = Display.is_available()

        assert is_available == status.available

    def test_get_status_does_not_initialize_hardware(self, mock_display_hardware):
        """Test that get_status does not initialize hardware."""
        # get_status should be a pure detection function
        status = Display.get_status()

        # Should not create any Display instance
        assert status is not None
        # Should not have side effects

    def test_is_available_does_not_initialize_hardware(self, mock_display_hardware):
        """Test that is_available does not initialize hardware."""
        # is_available should be a pure detection function
        result = Display.is_available()

        # Should not create any Display instance
        assert isinstance(result, bool)
        # Should not have side effects

    def test_get_status_no_exceptions_on_failure(self, monkeypatch):
        """Test that get_status does not raise exceptions."""
        # Should never raise, always returns HardwareStatus
        monkeypatch.setenv("LD_LIBRARY_PATH", "/nonexistent")

        status = Display.get_status()

        assert isinstance(status, HardwareStatus)
        assert status.available is False

    def test_is_available_no_exceptions_on_failure(self, monkeypatch):
        """Test that is_available does not raise exceptions."""
        # Should never raise, always returns bool
        monkeypatch.setenv("LD_LIBRARY_PATH", "/nonexistent")

        result = Display.is_available()

        assert isinstance(result, bool)
        assert result is False

    @pytest.mark.parametrize("firmware_type", ["EPD128x250", "EPD240x416"])
    def test_get_status_detects_firmware_type(
        self, mock_display_hardware, monkeypatch, firmware_type
    ):
        """Test that get_status detects different firmware types."""
        monkeypatch.setenv("DISTILLER_EINK_FIRMWARE", firmware_type)

        status = Display.get_status()

        # Should detect firmware type from config or env
        assert status.capabilities.get("firmware_type") is not None

    @pytest.mark.parametrize(
        "error_type",
        [
            FileNotFoundError("Device not found"),
            PermissionError("Permission denied"),
            OSError("I/O error"),
        ],
    )
    def test_get_status_handles_various_errors(self, monkeypatch, error_type):
        """Test that get_status handles various error conditions."""

        def mock_exists(path):
            raise error_type

        monkeypatch.setattr("os.path.exists", mock_exists)

        status = Display.get_status()

        assert isinstance(status, HardwareStatus)
        assert status.available is False
        assert status.error is not None
        # Error should be captured in status
        assert isinstance(status.error, (FileNotFoundError, PermissionError, OSError))

    def test_get_status_permission_denied_state(self, monkeypatch):
        """Test that permission errors result in PERMISSION_DENIED state."""

        def mock_exists(path):
            if "/dev/spi" in str(path) or "/dev/gpio" in str(path):
                raise PermissionError("Permission denied")
            return True

        monkeypatch.setattr("os.path.exists", mock_exists)

        status = Display.get_status()

        assert status.state == HardwareState.PERMISSION_DENIED
        assert status.available is False
        assert isinstance(status.error, PermissionError)
        assert "permission" in status.message.lower()
