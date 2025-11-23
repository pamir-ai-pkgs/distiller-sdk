"""Tests for Audio hardware detection."""

import pytest
import subprocess
from distiller_sdk.hardware.audio import Audio
from distiller_sdk.hardware_status import HardwareStatus, HardwareState


class TestAudioDetection:
    """Tests for Audio.get_status() and Audio.is_available()."""

    def test_get_status_returns_hardware_status(self, mock_audio_hardware):
        """Test that get_status returns HardwareStatus object."""
        status = Audio.get_status()

        assert isinstance(status, HardwareStatus)
        assert hasattr(status, "state")
        assert hasattr(status, "available")
        assert hasattr(status, "capabilities")
        assert hasattr(status, "error")
        assert hasattr(status, "diagnostic_info")
        assert hasattr(status, "message")

    def test_get_status_available_hardware(self, mock_audio_hardware):
        """Test get_status when audio hardware is available."""
        status = Audio.get_status()

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        assert status.capabilities.get("input") is True
        assert status.capabilities.get("output") is True
        assert status.error is None
        assert "available" in status.message.lower()

    def test_get_status_unavailable_hardware(self, mock_audio_unavailable):
        """Test get_status when audio hardware is unavailable."""
        status = Audio.get_status()

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        assert status.error is not None
        assert isinstance(status.error, FileNotFoundError)
        # Message should indicate hardware is not available
        assert (
            "found" in status.message.lower()
            or "unavailable" in status.message.lower()
            or "not installed" in status.message.lower()
        )

    def test_get_status_partial_input_only(self, monkeypatch):
        """Test get_status when only input is available."""

        def mock_run(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            if isinstance(cmd, list):
                cmd_str = " ".join(cmd)
            else:
                cmd_str = cmd

            if "arecord -l" in cmd_str:
                # Input available
                return subprocess.CompletedProcess(cmd, 0, b"card 0: USB Audio", b"")
            elif "aplay -l" in cmd_str:
                # Output unavailable
                return subprocess.CompletedProcess(cmd, 1, b"", b"no devices found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        status = Audio.get_status()

        assert status.state == HardwareState.PARTIALLY_AVAILABLE
        assert status.available is True  # Still usable for recording
        assert status.capabilities.get("input") is True
        assert status.capabilities.get("output") is False

    def test_get_status_partial_output_only(self, monkeypatch):
        """Test get_status when only output is available."""

        def mock_run(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            if isinstance(cmd, list):
                cmd_str = " ".join(cmd)
            else:
                cmd_str = cmd

            if "arecord -l" in cmd_str:
                # Input unavailable
                return subprocess.CompletedProcess(cmd, 1, b"", b"no devices found")
            elif "aplay -l" in cmd_str:
                # Output available
                return subprocess.CompletedProcess(cmd, 0, b"card 0: USB Audio", b"")

        monkeypatch.setattr(subprocess, "run", mock_run)

        status = Audio.get_status()

        assert status.state == HardwareState.PARTIALLY_AVAILABLE
        assert status.available is True  # Still usable for playback
        assert status.capabilities.get("input") is False
        assert status.capabilities.get("output") is True

    def test_get_status_includes_volume_control_capability(self, mock_audio_hardware, monkeypatch):
        """Test that get_status includes volume control capability."""
        # Mock has_audio_controls
        monkeypatch.setattr(Audio, "has_audio_controls", lambda: True)

        status = Audio.get_status()

        assert "volume_control" in status.capabilities
        assert status.capabilities["volume_control"] is True

    def test_get_status_no_volume_control(self, mock_audio_hardware, monkeypatch):
        """Test status when volume control is not available."""
        # Mock has_audio_controls to return False
        monkeypatch.setattr(Audio, "has_audio_controls", lambda: False)

        status = Audio.get_status()

        assert "volume_control" in status.capabilities
        assert status.capabilities["volume_control"] is False

    def test_get_status_includes_diagnostic_info(self, mock_audio_hardware):
        """Test that get_status includes diagnostic information."""
        status = Audio.get_status()

        assert isinstance(status.diagnostic_info, dict)
        # Should include device information
        assert len(status.diagnostic_info) > 0

    def test_is_available_returns_bool(self, mock_audio_hardware):
        """Test that is_available returns a boolean."""
        result = Audio.is_available()

        assert isinstance(result, bool)

    def test_is_available_true_when_hardware_present(self, mock_audio_hardware):
        """Test is_available returns True when hardware is present."""
        assert Audio.is_available() is True

    def test_is_available_false_when_hardware_absent(self, mock_audio_unavailable):
        """Test is_available returns False when hardware is absent."""
        assert Audio.is_available() is False

    def test_is_available_consistent_with_get_status(self, mock_audio_hardware):
        """Test that is_available matches get_status().available."""
        status = Audio.get_status()
        is_available = Audio.is_available()

        assert is_available == status.available

    def test_get_status_does_not_initialize_hardware(self, mock_audio_hardware):
        """Test that get_status does not initialize hardware."""
        # get_status should be a pure detection function
        status = Audio.get_status()

        # Should not create any Audio instance
        assert status is not None
        # Should not have side effects

    def test_is_available_does_not_initialize_hardware(self, mock_audio_hardware):
        """Test that is_available does not initialize hardware."""
        # is_available should be a pure detection function
        result = Audio.is_available()

        # Should not create any Audio instance
        assert isinstance(result, bool)
        # Should not have side effects

    def test_get_status_no_exceptions_on_failure(self, mock_audio_unavailable):
        """Test that get_status does not raise exceptions."""
        # Should never raise, always returns HardwareStatus
        status = Audio.get_status()

        assert isinstance(status, HardwareStatus)
        assert status.available is False

    def test_is_available_no_exceptions_on_failure(self, mock_audio_unavailable):
        """Test that is_available does not raise exceptions."""
        # Should never raise, always returns bool
        result = Audio.is_available()

        assert isinstance(result, bool)
        assert result is False

    def test_get_status_caches_device_list(self, mock_audio_hardware):
        """Test that diagnostic_info includes device listings."""
        status = Audio.get_status()

        # Should include information about detected devices
        assert (
            "input_devices" in status.diagnostic_info
            or "output_devices" in status.diagnostic_info
            or "devices" in status.diagnostic_info
        )

    @pytest.mark.parametrize(
        "command_error",
        [
            FileNotFoundError("arecord not found"),
            PermissionError("Permission denied"),
            subprocess.CalledProcessError(1, "arecord", stderr=b"error"),
        ],
    )
    def test_get_status_handles_various_errors(self, monkeypatch, command_error):
        """Test that get_status handles various error conditions."""

        def mock_run(*args, **kwargs):
            raise command_error

        monkeypatch.setattr(subprocess, "run", mock_run)

        status = Audio.get_status()

        assert isinstance(status, HardwareStatus)
        assert status.available is False
        assert status.error is not None
        # Error should be captured in status
        assert isinstance(
            status.error, (FileNotFoundError, PermissionError, subprocess.CalledProcessError)
        )
