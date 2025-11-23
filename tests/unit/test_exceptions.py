"""Tests for exception hierarchy."""

import pytest
from distiller_sdk.exceptions import (
    DistillerError,
    HardwareError,
    AudioError,
    DisplayError,
    CameraError,
    LEDError,
    AIError,
    ParakeetError,
    PiperError,
    WhisperError,
    ConfigurationError,
    ResourceError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_distiller_error_base(self) -> None:
        """Test that DistillerError is the base exception."""
        error = DistillerError("Base error")
        assert isinstance(error, Exception)
        assert str(error) == "Base error"

    def test_hardware_error_inheritance(self) -> None:
        """Test HardwareError inherits from DistillerError."""
        error = HardwareError("Hardware error")
        assert isinstance(error, DistillerError)
        assert isinstance(error, Exception)
        assert str(error) == "Hardware error"

    def test_audio_error_inheritance(self) -> None:
        """Test AudioError inherits from HardwareError."""
        error = AudioError("Audio error")
        assert isinstance(error, HardwareError)
        assert isinstance(error, DistillerError)
        assert isinstance(error, Exception)

    def test_display_error_inheritance(self) -> None:
        """Test DisplayError inherits from HardwareError."""
        error = DisplayError("Display error")
        assert isinstance(error, HardwareError)
        assert isinstance(error, DistillerError)

    def test_camera_error_inheritance(self) -> None:
        """Test CameraError inherits from HardwareError."""
        error = CameraError("Camera error")
        assert isinstance(error, HardwareError)
        assert isinstance(error, DistillerError)

    def test_led_error_inheritance(self) -> None:
        """Test LEDError inherits from HardwareError."""
        error = LEDError("LED error")
        assert isinstance(error, HardwareError)
        assert isinstance(error, DistillerError)

    def test_ai_error_inheritance(self) -> None:
        """Test AIError inherits from DistillerError."""
        error = AIError("AI error")
        assert isinstance(error, DistillerError)
        assert isinstance(error, Exception)

    def test_parakeet_error_inheritance(self) -> None:
        """Test ParakeetError inherits from AIError."""
        error = ParakeetError("Parakeet error")
        assert isinstance(error, AIError)
        assert isinstance(error, DistillerError)

    def test_piper_error_inheritance(self) -> None:
        """Test PiperError inherits from AIError."""
        error = PiperError("Piper error")
        assert isinstance(error, AIError)
        assert isinstance(error, DistillerError)

    def test_whisper_error_inheritance(self) -> None:
        """Test WhisperError inherits from AIError."""
        error = WhisperError("Whisper error")
        assert isinstance(error, AIError)
        assert isinstance(error, DistillerError)

    def test_configuration_error_inheritance(self) -> None:
        """Test ConfigurationError inherits from DistillerError."""
        error = ConfigurationError("Config error")
        assert isinstance(error, DistillerError)
        assert isinstance(error, Exception)

    def test_resource_error_inheritance(self) -> None:
        """Test ResourceError inherits from DistillerError."""
        error = ResourceError("Resource error")
        assert isinstance(error, DistillerError)
        assert isinstance(error, Exception)


class TestExceptionCatching:
    """Tests for exception catching patterns."""

    def test_catch_specific_audio_error(self) -> None:
        """Test catching specific AudioError."""
        with pytest.raises(AudioError) as exc_info:
            raise AudioError("Audio hardware failure")

        assert "Audio hardware failure" in str(exc_info.value)

    def test_catch_audio_as_hardware_error(self) -> None:
        """Test catching AudioError as HardwareError."""
        with pytest.raises(HardwareError):
            raise AudioError("Audio hardware failure")

    def test_catch_audio_as_distiller_error(self) -> None:
        """Test catching AudioError as DistillerError."""
        with pytest.raises(DistillerError):
            raise AudioError("Audio hardware failure")

    def test_catch_all_hardware_errors(self) -> None:
        """Test catching all hardware errors with base class."""
        hardware_errors = [
            AudioError("Audio"),
            DisplayError("Display"),
            CameraError("Camera"),
            LEDError("LED"),
        ]

        for error in hardware_errors:
            with pytest.raises(HardwareError):
                raise error

    def test_catch_all_ai_errors(self) -> None:
        """Test catching all AI errors with base class."""
        ai_errors = [
            ParakeetError("Parakeet"),
            PiperError("Piper"),
            WhisperError("Whisper"),
        ]

        for error in ai_errors:
            with pytest.raises(AIError):
                raise error

    def test_catch_all_distiller_errors(self) -> None:
        """Test catching any Distiller error."""
        all_errors = [
            AudioError("Audio"),
            DisplayError("Display"),
            ParakeetError("Parakeet"),
            ConfigurationError("Config"),
            ResourceError("Resource"),
        ]

        for error in all_errors:
            with pytest.raises(DistillerError):
                raise error

    def test_distinguish_hardware_from_ai_errors(self) -> None:
        """Test distinguishing between hardware and AI errors."""
        try:
            raise AudioError("Audio failure")
        except HardwareError:
            # Should catch hardware errors
            pass
        except AIError:
            pytest.fail("Should not catch as AIError")

        try:
            raise ParakeetError("Parakeet failure")
        except AIError:
            # Should catch AI errors
            pass
        except HardwareError:
            pytest.fail("Should not catch as HardwareError")


class TestExceptionMessages:
    """Tests for exception message handling."""

    def test_exception_with_message(self) -> None:
        """Test exception with custom message."""
        error = AudioError("No audio device found")
        assert str(error) == "No audio device found"

    def test_exception_with_empty_message(self) -> None:
        """Test exception with empty message."""
        error = AudioError("")
        assert str(error) == ""

    def test_exception_with_multiline_message(self) -> None:
        """Test exception with multiline message."""
        message = "Audio error:\n- Device not found\n- Check connections"
        error = AudioError(message)
        assert str(error) == message

    def test_exception_repr(self) -> None:
        """Test exception repr."""
        error = AudioError("Test error")
        repr_str = repr(error)
        assert "AudioError" in repr_str
        assert "Test error" in repr_str


class TestExceptionRaising:
    """Tests for raising exceptions in various scenarios."""

    def test_raise_with_cause(self) -> None:
        """Test raising exception with cause."""
        original = ValueError("Original error")

        with pytest.raises(AudioError) as exc_info:
            try:
                raise original
            except ValueError as e:
                raise AudioError("Audio failed") from e

        assert exc_info.value.__cause__ == original

    def test_raise_without_cause(self) -> None:
        """Test raising exception without cause."""
        with pytest.raises(AudioError) as exc_info:
            raise AudioError("Audio failed")

        assert exc_info.value.__cause__ is None

    def test_exception_traceback_preserved(self) -> None:
        """Test that exception traceback is preserved."""

        def inner_function() -> None:
            raise AudioError("Inner error")

        def outer_function() -> None:
            inner_function()

        with pytest.raises(AudioError) as exc_info:
            outer_function()

        # Traceback should include both functions
        tb = exc_info.traceback
        assert tb is not None


class TestExceptionDocstrings:
    """Tests for exception class docstrings."""

    def test_base_exceptions_have_docstrings(self) -> None:
        """Test that base exception classes have docstrings."""
        assert DistillerError.__doc__ is not None
        assert HardwareError.__doc__ is not None
        assert AIError.__doc__ is not None

    def test_specific_exceptions_have_docstrings(self) -> None:
        """Test that specific exception classes have docstrings."""
        assert AudioError.__doc__ is not None
        assert DisplayError.__doc__ is not None
        assert ParakeetError.__doc__ is not None
        assert PiperError.__doc__ is not None
