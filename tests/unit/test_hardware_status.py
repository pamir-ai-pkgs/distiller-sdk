"""Tests for hardware status system."""

import pytest
from distiller_sdk.hardware_status import HardwareStatus, HardwareState


class TestHardwareState:
    """Tests for HardwareState enum."""

    def test_hardware_state_values(self) -> None:
        """Test that all hardware states are defined."""
        assert HardwareState.AVAILABLE.value == "available"
        assert HardwareState.UNAVAILABLE.value == "unavailable"
        assert HardwareState.PERMISSION_DENIED.value == "permission_denied"
        assert HardwareState.PARTIALLY_AVAILABLE.value == "partially_available"

    def test_hardware_state_enum_members(self) -> None:
        """Test that enum has expected members."""
        states = [e.name for e in HardwareState]
        assert "AVAILABLE" in states
        assert "UNAVAILABLE" in states
        assert "PERMISSION_DENIED" in states
        assert "PARTIALLY_AVAILABLE" in states


class TestHardwareStatus:
    """Tests for HardwareStatus dataclass."""

    def test_hardware_status_available(self) -> None:
        """Test creating a status for available hardware."""
        status = HardwareStatus(
            state=HardwareState.AVAILABLE,
            available=True,
            capabilities={"input": True, "output": True},
            error=None,
            diagnostic_info={"device": "/dev/audio0"},
            message="Audio hardware fully available",
        )

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        assert status.capabilities == {"input": True, "output": True}
        assert status.error is None
        assert status.diagnostic_info == {"device": "/dev/audio0"}
        assert status.message == "Audio hardware fully available"

    def test_hardware_status_unavailable(self) -> None:
        """Test creating a status for unavailable hardware."""
        error = FileNotFoundError("Hardware not found")
        status = HardwareStatus(
            state=HardwareState.UNAVAILABLE,
            available=False,
            capabilities={},
            error=error,
            diagnostic_info={},
            message="Hardware not found",
        )

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        assert status.capabilities == {}
        assert status.error == error
        assert status.message == "Hardware not found"

    def test_hardware_status_permission_denied(self) -> None:
        """Test status for permission denied scenario."""
        error = PermissionError("Access denied")
        status = HardwareStatus(
            state=HardwareState.PERMISSION_DENIED,
            available=False,
            capabilities={},
            error=error,
            diagnostic_info={"required_group": "audio"},
            message="Permission denied - add user to audio group",
        )

        assert status.state == HardwareState.PERMISSION_DENIED
        assert status.available is False
        assert status.error == error
        assert "audio" in status.diagnostic_info["required_group"]

    def test_hardware_status_partially_available(self) -> None:
        """Test status for partially available hardware."""
        status = HardwareStatus(
            state=HardwareState.PARTIALLY_AVAILABLE,
            available=True,  # Still considered available
            capabilities={"input": True, "output": False},
            error=None,
            diagnostic_info={"missing": "output device"},
            message="Input available, output unavailable",
        )

        assert status.state == HardwareState.PARTIALLY_AVAILABLE
        assert status.available is True  # Can still use input
        assert status.capabilities["input"] is True
        assert status.capabilities["output"] is False

    def test_hardware_status_dataclass_equality(self) -> None:
        """Test that two identical statuses are equal."""
        status1 = HardwareStatus(
            state=HardwareState.AVAILABLE,
            available=True,
            capabilities={},
            error=None,
            diagnostic_info={},
            message="OK",
        )
        status2 = HardwareStatus(
            state=HardwareState.AVAILABLE,
            available=True,
            capabilities={},
            error=None,
            diagnostic_info={},
            message="OK",
        )

        assert status1 == status2

    def test_hardware_status_dataclass_inequality(self) -> None:
        """Test that different statuses are not equal."""
        status1 = HardwareStatus(
            state=HardwareState.AVAILABLE,
            available=True,
            capabilities={},
            error=None,
            diagnostic_info={},
            message="OK",
        )
        status2 = HardwareStatus(
            state=HardwareState.UNAVAILABLE,
            available=False,
            capabilities={},
            error=None,
            diagnostic_info={},
            message="Not OK",
        )

        assert status1 != status2

    def test_hardware_status_repr(self) -> None:
        """Test string representation of hardware status."""
        status = HardwareStatus(
            state=HardwareState.AVAILABLE,
            available=True,
            capabilities={"test": True},
            error=None,
            diagnostic_info={"info": "data"},
            message="Test message",
        )

        repr_str = repr(status)
        assert "HardwareStatus" in repr_str
        assert "AVAILABLE" in repr_str
        assert "True" in repr_str

    def test_hardware_status_with_complex_capabilities(self) -> None:
        """Test status with complex capability dictionary."""
        capabilities = {
            "input": True,
            "output": True,
            "volume_control": True,
            "sample_rates": [16000, 44100, 48000],
            "channels": {"mono": True, "stereo": True},
        }

        status = HardwareStatus(
            state=HardwareState.AVAILABLE,
            available=True,
            capabilities=capabilities,
            error=None,
            diagnostic_info={},
            message="Full capabilities",
        )

        assert status.capabilities["input"] is True
        assert status.capabilities["volume_control"] is True
        assert 44100 in status.capabilities["sample_rates"]
        assert status.capabilities["channels"]["stereo"] is True

    def test_hardware_status_with_exception_info(self) -> None:
        """Test that exceptions are properly stored in status."""
        error = RuntimeError("Unexpected hardware error")
        status = HardwareStatus(
            state=HardwareState.UNAVAILABLE,
            available=False,
            capabilities={},
            error=error,
            diagnostic_info={"traceback": "..."},
            message="Runtime error occurred",
        )

        assert isinstance(status.error, RuntimeError)
        assert str(status.error) == "Unexpected hardware error"

    @pytest.mark.parametrize(
        "state,expected_available",
        [
            (HardwareState.AVAILABLE, True),
            (HardwareState.UNAVAILABLE, False),
            (HardwareState.PERMISSION_DENIED, False),
            (HardwareState.PARTIALLY_AVAILABLE, True),  # Typically still usable
        ],
    )
    def test_hardware_status_available_flag_consistency(
        self, state: HardwareState, expected_available: bool
    ) -> None:
        """Test that available flag is consistent with state."""
        status = HardwareStatus(
            state=state,
            available=expected_available,
            capabilities={},
            error=None,
            diagnostic_info={},
            message="Test",
        )

        assert status.available == expected_available
