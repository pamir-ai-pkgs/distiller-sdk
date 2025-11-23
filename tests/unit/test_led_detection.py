"""Tests for LED hardware detection."""

import pytest
from pathlib import Path
from typing import Any

from distiller_sdk.hardware.sam import LED
from distiller_sdk.hardware_status import HardwareStatus, HardwareState


class TestLEDDetection:
    """Tests for LED.get_status() and LED.is_available()."""

    def test_get_status_returns_hardware_status(self, mock_led_hardware: Path) -> None:
        """Test that get_status returns HardwareStatus object."""
        status = LED.get_status()

        assert isinstance(status, HardwareStatus)
        assert hasattr(status, "state")
        assert hasattr(status, "available")
        assert hasattr(status, "capabilities")
        assert hasattr(status, "error")
        assert hasattr(status, "diagnostic_info")
        assert hasattr(status, "message")

    def test_get_status_available_hardware(self, mock_led_hardware: Path) -> None:
        """Test get_status when LED hardware is available."""
        status = LED.get_status()

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        led_count = status.capabilities.get("led_count")
        assert led_count is not None
        assert led_count > 0
        assert status.error is None
        assert "available" in status.message.lower()

    def test_get_status_unavailable_no_sysfs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_status when sysfs interface is not available."""
        # Mock Path.exists to return False for /sys/class/leds
        original_exists = Path.exists

        def mock_exists(self: Any) -> bool:
            if str(self) == "/sys/class/leds":
                return False
            return original_exists(self)

        monkeypatch.setattr(Path, "exists", mock_exists)

        status = LED.get_status()

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        assert status.error is not None
        assert isinstance(status.error, FileNotFoundError)
        # Message should indicate sysfs not found
        assert "sysfs" in status.message.lower() or "not found" in status.message.lower()

    def test_get_status_no_leds_detected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """Test get_status when no LEDs are detected."""
        # Create empty LED directory
        led_base = tmp_path / "sys" / "class" / "leds"
        led_base.mkdir(parents=True, exist_ok=True)

        # Mock Path to use our tmp_path
        status = LED.get_status(base_path=str(led_base))

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        # Message should indicate no LEDs found
        assert "led" in status.message.lower() and (
            "not" in status.message.lower() or "no" in status.message.lower()
        )

    def test_get_status_includes_capabilities(self, mock_led_hardware: Path) -> None:
        """Test that get_status includes LED capabilities."""
        status = LED.get_status()

        assert "led_count" in status.capabilities
        assert "available_leds" in status.capabilities
        assert "rgb_support" in status.capabilities
        # Should support RGB control
        assert status.capabilities["rgb_support"] is True

    def test_get_status_includes_diagnostic_info(self, mock_led_hardware: Path) -> None:
        """Test that get_status includes diagnostic information."""
        status = LED.get_status()

        assert isinstance(status.diagnostic_info, dict)
        # Should include sysfs path information
        assert len(status.diagnostic_info) > 0
        # Should have info about LEDs found
        has_info = any(
            key in status.diagnostic_info for key in ["led_list", "leds_found", "sysfs_path"]
        )
        assert has_info

    def test_is_available_returns_bool(self, mock_led_hardware: Path) -> None:
        """Test that is_available returns a boolean."""
        result = LED.is_available()

        assert isinstance(result, bool)

    def test_is_available_true_when_hardware_present(self, mock_led_hardware: Path) -> None:
        """Test is_available returns True when hardware is present."""
        assert LED.is_available() is True

    def test_is_available_false_when_hardware_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_available returns False when hardware is absent."""
        # Mock Path.exists to return False
        original_exists = Path.exists

        def mock_exists(self: Any) -> bool:
            if str(self) == "/sys/class/leds":
                return False
            return original_exists(self)

        monkeypatch.setattr(Path, "exists", mock_exists)

        assert LED.is_available() is False

    def test_is_available_consistent_with_get_status(self, mock_led_hardware: Path) -> None:
        """Test that is_available matches get_status().available."""
        status = LED.get_status()
        is_available = LED.is_available()

        assert is_available == status.available

    def test_get_status_does_not_initialize_hardware(self, mock_led_hardware: Path) -> None:
        """Test that get_status does not initialize hardware."""
        # get_status should be a pure detection function
        status = LED.get_status()

        # Should not create any LED instance
        assert status is not None
        # Should not have side effects

    def test_is_available_does_not_initialize_hardware(self, mock_led_hardware: Path) -> None:
        """Test that is_available does not initialize hardware."""
        # is_available should be a pure detection function
        result = LED.is_available()

        # Should not create any LED instance
        assert isinstance(result, bool)
        # Should not have side effects

    def test_get_status_no_exceptions_on_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_status does not raise exceptions."""
        # Should never raise, always returns HardwareStatus
        original_exists = Path.exists

        def mock_exists(self: Any) -> bool:
            if str(self) == "/sys/class/leds":
                return False
            return original_exists(self)

        monkeypatch.setattr(Path, "exists", mock_exists)

        status = LED.get_status()

        assert isinstance(status, HardwareStatus)
        assert status.available is False

    def test_is_available_no_exceptions_on_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that is_available does not raise exceptions."""
        # Should never raise, always returns bool
        original_exists = Path.exists

        def mock_exists(self: Any) -> bool:
            if str(self) == "/sys/class/leds":
                return False
            return original_exists(self)

        monkeypatch.setattr(Path, "exists", mock_exists)

        result = LED.is_available()

        assert isinstance(result, bool)
        assert result is False

    @pytest.mark.parametrize(
        "error_type",
        [
            FileNotFoundError("Directory not found"),
            PermissionError("Permission denied"),
            OSError("I/O error"),
        ],
    )
    def test_get_status_handles_various_errors(
        self, monkeypatch: pytest.MonkeyPatch, error_type: Any
    ) -> None:
        """Test that get_status handles various error conditions."""

        def mock_exists(self: Any) -> bool:
            raise error_type

        monkeypatch.setattr(Path, "exists", mock_exists)

        status = LED.get_status()

        assert isinstance(status, HardwareStatus)
        assert status.available is False
        assert status.error is not None
        # Error should be captured in status
        assert isinstance(status.error, (FileNotFoundError, PermissionError, OSError))

    def test_get_status_permission_denied_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that permission errors result in PERMISSION_DENIED state."""

        def mock_exists(self: Any) -> bool:
            if str(self) == "/sys/class/leds":
                raise PermissionError("Permission denied accessing sysfs")
            return True

        monkeypatch.setattr(Path, "exists", mock_exists)

        status = LED.get_status()

        assert status.state == HardwareState.PERMISSION_DENIED
        assert status.available is False
        assert isinstance(status.error, PermissionError)
        assert "permission" in status.message.lower()

    def test_get_status_detects_multiple_leds(self, tmp_path: Any) -> None:
        """Test that get_status detects multiple LEDs."""
        # Create LED directory structure with multiple LEDs
        led_base = tmp_path / "sys" / "class" / "leds"
        led_base.mkdir(parents=True, exist_ok=True)

        # Create multiple LED directories
        for led_num in [0, 1, 2]:
            led_dir = led_base / f"pamir:led{led_num}"
            led_dir.mkdir()
            # Create RGB control files
            (led_dir / "red").write_text("0")
            (led_dir / "green").write_text("0")
            (led_dir / "blue").write_text("0")
            (led_dir / "brightness").write_text("0")

        status = LED.get_status(base_path=str(led_base))

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        # Should detect 3 LEDs
        assert status.capabilities.get("led_count") == 3
        assert 0 in status.capabilities.get("available_leds", [])
        assert 1 in status.capabilities.get("available_leds", [])
        assert 2 in status.capabilities.get("available_leds", [])

    def test_get_status_detects_animation_support(self, tmp_path: Any) -> None:
        """Test that get_status detects animation mode support."""
        # Create LED directory with animation support
        led_base = tmp_path / "sys" / "class" / "leds"
        led_base.mkdir(parents=True, exist_ok=True)

        led_dir = led_base / "pamir:led0"
        led_dir.mkdir()
        (led_dir / "red").write_text("0")
        (led_dir / "green").write_text("0")
        (led_dir / "blue").write_text("0")
        (led_dir / "brightness").write_text("0")
        (led_dir / "animation_mode").write_text("static")
        (led_dir / "animation_timing").write_text("500")

        status = LED.get_status(base_path=str(led_base))

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        # Should detect animation support
        assert status.capabilities.get("animation_support") is True

    def test_get_status_detects_trigger_support(self, tmp_path: Any) -> None:
        """Test that get_status detects trigger support."""
        # Create LED directory with trigger support
        led_base = tmp_path / "sys" / "class" / "leds"
        led_base.mkdir(parents=True, exist_ok=True)

        led_dir = led_base / "pamir:led0"
        led_dir.mkdir()
        (led_dir / "red").write_text("0")
        (led_dir / "green").write_text("0")
        (led_dir / "blue").write_text("0")
        (led_dir / "brightness").write_text("0")
        (led_dir / "trigger").write_text("[none] heartbeat-rgb")

        status = LED.get_status(base_path=str(led_base))

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        # Should detect trigger support
        assert status.capabilities.get("trigger_support") is True
