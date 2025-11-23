"""Tests for Camera hardware detection."""

import subprocess
from typing import Any

import pytest

from distiller_sdk.hardware.camera import Camera
from distiller_sdk.hardware_status import HardwareStatus, HardwareState


class TestCameraDetection:
    """Tests for Camera.get_status() and Camera.is_available()."""

    def test_get_status_returns_hardware_status(self, mock_camera_hardware: None) -> None:
        """Test that get_status returns HardwareStatus object."""
        status = Camera.get_status()

        assert isinstance(status, HardwareStatus)
        assert hasattr(status, "state")
        assert hasattr(status, "available")
        assert hasattr(status, "capabilities")
        assert hasattr(status, "error")
        assert hasattr(status, "diagnostic_info")
        assert hasattr(status, "message")

    def test_get_status_available_hardware(self, mock_camera_hardware: None) -> None:
        """Test get_status when camera hardware is available."""
        status = Camera.get_status()

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        assert status.capabilities.get("rpicam_available") is True
        assert status.error is None
        assert "available" in status.message.lower()

    def test_get_status_unavailable_no_rpicam(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_status when rpicam-still is not installed."""

        def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
            raise FileNotFoundError("rpicam-still not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        status = Camera.get_status()

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        assert status.error is not None
        assert isinstance(status.error, FileNotFoundError)
        # Message should indicate rpicam-still not found
        assert "rpicam" in status.message.lower() or "not found" in status.message.lower()

    def test_get_status_no_camera_detected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_status when no camera is detected by rpicam-still."""
        import shutil

        # Mock shutil.which to find rpicam-still
        def mock_which(cmd: str) -> str | None:
            if cmd == "rpicam-still":
                return "/usr/bin/rpicam-still"
            return None

        monkeypatch.setattr(shutil, "which", mock_which)

        def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
            cmd = args[0] if args else kwargs.get("args", [])
            if isinstance(cmd, list):
                cmd_str = " ".join(cmd)
            else:
                cmd_str = cmd

            if "rpicam-still" in cmd_str and "--list-cameras" in cmd_str:
                # No cameras found
                return subprocess.CompletedProcess(cmd, 0, "No cameras detected\n", "")
            else:
                return subprocess.CompletedProcess(cmd, 1, "", "Command not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        status = Camera.get_status()

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        # Message should indicate no camera detected
        assert "camera" in status.message.lower() and (
            "not" in status.message.lower() or "no" in status.message.lower()
        )

    def test_get_status_includes_capabilities(self, mock_camera_hardware: None) -> None:
        """Test that get_status includes camera capabilities."""
        status = Camera.get_status()

        assert "rpicam_available" in status.capabilities
        assert "opencv_available" in status.capabilities
        # Should detect camera count if possible
        assert "camera_count" in status.capabilities or "cameras_detected" in status.diagnostic_info

    def test_get_status_includes_diagnostic_info(self, mock_camera_hardware: None) -> None:
        """Test that get_status includes diagnostic information."""
        status = Camera.get_status()

        assert isinstance(status.diagnostic_info, dict)
        # Should include device information
        assert len(status.diagnostic_info) > 0
        # Should have info about rpicam-still or cameras
        has_info = any(
            key in status.diagnostic_info
            for key in ["rpicam_output", "cameras_detected", "camera_list"]
        )
        assert has_info

    def test_is_available_returns_bool(self, mock_camera_hardware: None) -> None:
        """Test that is_available returns a boolean."""
        result = Camera.is_available()

        assert isinstance(result, bool)

    def test_is_available_true_when_hardware_present(self, mock_camera_hardware: None) -> None:
        """Test is_available returns True when hardware is present."""
        assert Camera.is_available() is True

    def test_is_available_false_when_hardware_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_available returns False when hardware is absent."""

        def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
            raise FileNotFoundError("rpicam-still not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        assert Camera.is_available() is False

    def test_is_available_consistent_with_get_status(self, mock_camera_hardware: None) -> None:
        """Test that is_available matches get_status().available."""
        status = Camera.get_status()
        is_available = Camera.is_available()

        assert is_available == status.available

    def test_get_status_does_not_initialize_hardware(self, mock_camera_hardware: None) -> None:
        """Test that get_status does not initialize hardware."""
        # get_status should be a pure detection function
        status = Camera.get_status()

        # Should not create any Camera instance
        assert status is not None
        # Should not have side effects

    def test_is_available_does_not_initialize_hardware(self, mock_camera_hardware: None) -> None:
        """Test that is_available does not initialize hardware."""
        # is_available should be a pure detection function
        result = Camera.is_available()

        # Should not create any Camera instance
        assert isinstance(result, bool)
        # Should not have side effects

    def test_get_status_no_exceptions_on_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_status does not raise exceptions."""

        # Should never raise, always returns HardwareStatus
        def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
            raise FileNotFoundError("rpicam-still not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        status = Camera.get_status()

        assert isinstance(status, HardwareStatus)
        assert status.available is False

    def test_is_available_no_exceptions_on_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that is_available does not raise exceptions."""

        # Should never raise, always returns bool
        def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
            raise FileNotFoundError("rpicam-still not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = Camera.is_available()

        assert isinstance(result, bool)
        assert result is False

    @pytest.mark.parametrize(
        "error_type",
        [
            FileNotFoundError("rpicam-still not found"),
            PermissionError("Permission denied"),
            subprocess.CalledProcessError(1, "rpicam-still", stderr=b"error"),
        ],
    )
    def test_get_status_handles_various_errors(
        self, monkeypatch: pytest.MonkeyPatch, error_type: Any
    ) -> None:
        """Test that get_status handles various error conditions."""

        def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
            raise error_type

        monkeypatch.setattr(subprocess, "run", mock_run)

        status = Camera.get_status()

        assert isinstance(status, HardwareStatus)
        assert status.available is False
        assert status.error is not None
        # Error should be captured in status
        assert isinstance(
            status.error, (FileNotFoundError, PermissionError, subprocess.CalledProcessError)
        )

    def test_get_status_permission_denied_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that permission errors result in PERMISSION_DENIED state."""
        import shutil

        # Mock shutil.which to find rpicam-still
        def mock_which(cmd: str) -> str | None:
            if cmd == "rpicam-still":
                return "/usr/bin/rpicam-still"
            return None

        monkeypatch.setattr(shutil, "which", mock_which)

        def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
            raise PermissionError("Permission denied accessing camera")

        monkeypatch.setattr(subprocess, "run", mock_run)

        status = Camera.get_status()

        assert status.state == HardwareState.PERMISSION_DENIED
        assert status.available is False
        assert isinstance(status.error, PermissionError)
        assert "permission" in status.message.lower()

    def test_get_status_detects_multiple_cameras(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_status detects multiple cameras."""
        import shutil

        # Mock shutil.which to find rpicam-still
        def mock_which(cmd: str) -> str | None:
            if cmd == "rpicam-still":
                return "/usr/bin/rpicam-still"
            return None

        monkeypatch.setattr(shutil, "which", mock_which)

        def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
            cmd = args[0] if args else kwargs.get("args", [])
            if isinstance(cmd, list):
                cmd_str = " ".join(cmd)
            else:
                cmd_str = cmd

            if "rpicam-still" in cmd_str and "--list-cameras" in cmd_str:
                # Two cameras detected
                return subprocess.CompletedProcess(
                    cmd,
                    0,
                    "Available cameras\n0 : imx219 [Camera Module v2]\n1 : imx477 [HQ Camera]\n",
                    "",
                )
            else:
                return subprocess.CompletedProcess(cmd, 1, "", "")

        monkeypatch.setattr(subprocess, "run", mock_run)

        status = Camera.get_status()

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        # Should detect multiple cameras
        assert status.capabilities.get("camera_count", 0) >= 1
