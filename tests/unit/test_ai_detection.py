"""Tests for AI module detection (Parakeet, Piper, Whisper)."""

from pathlib import Path
from typing import Any

from distiller_sdk.hardware_status import HardwareStatus, HardwareState


class TestParakeetDetection:
    """Tests for Parakeet.get_status() and Parakeet.is_available()."""

    def test_get_status_returns_hardware_status(self, mock_parakeet_models: Path) -> None:
        """Test that get_status returns HardwareStatus object."""
        from distiller_sdk.parakeet import Parakeet

        status = Parakeet.get_status(model_path=str(mock_parakeet_models))

        assert isinstance(status, HardwareStatus)
        assert hasattr(status, "state")
        assert hasattr(status, "available")
        assert hasattr(status, "capabilities")
        assert hasattr(status, "error")
        assert hasattr(status, "diagnostic_info")
        assert hasattr(status, "message")

    def test_get_status_available_models(self, mock_parakeet_models: Path) -> None:
        """Test get_status when Parakeet models are available."""
        from distiller_sdk.parakeet import Parakeet

        status = Parakeet.get_status(model_path=str(mock_parakeet_models))

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        assert status.capabilities.get("asr_available") is True
        assert status.error is None
        assert "available" in status.message.lower()

    def test_get_status_missing_models(self, tmp_path: Any) -> None:
        """Test get_status when model files are missing."""
        from distiller_sdk.parakeet import Parakeet

        # Empty directory with no models
        status = Parakeet.get_status(model_path=str(tmp_path))

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        assert status.error is not None
        # Message should indicate missing models
        assert "model" in status.message.lower() or "not found" in status.message.lower()

    def test_get_status_includes_capabilities(self, mock_parakeet_models: Path) -> None:
        """Test that get_status includes Parakeet capabilities."""
        from distiller_sdk.parakeet import Parakeet

        status = Parakeet.get_status(model_path=str(mock_parakeet_models))

        assert "asr_available" in status.capabilities
        assert "vad_available" in status.capabilities
        assert "model_type" in status.capabilities

    def test_get_status_includes_diagnostic_info(self, mock_parakeet_models: Path) -> None:
        """Test that get_status includes diagnostic information."""
        from distiller_sdk.parakeet import Parakeet

        status = Parakeet.get_status(model_path=str(mock_parakeet_models))

        assert isinstance(status.diagnostic_info, dict)
        assert len(status.diagnostic_info) > 0
        # Should have info about model files
        has_info = any(
            key in status.diagnostic_info for key in ["model_path", "model_files", "required_files"]
        )
        assert has_info

    def test_is_available_returns_bool(self, mock_parakeet_models: Path) -> None:
        """Test that is_available returns a boolean."""
        from distiller_sdk.parakeet import Parakeet

        result = Parakeet.is_available(model_path=str(mock_parakeet_models))

        assert isinstance(result, bool)

    def test_is_available_true_when_models_present(self, mock_parakeet_models: Path) -> None:
        """Test is_available returns True when models are present."""
        from distiller_sdk.parakeet import Parakeet

        assert Parakeet.is_available(model_path=str(mock_parakeet_models)) is True

    def test_is_available_false_when_models_absent(self, tmp_path: Any) -> None:
        """Test is_available returns False when models are absent."""
        from distiller_sdk.parakeet import Parakeet

        assert Parakeet.is_available(model_path=str(tmp_path)) is False

    def test_get_status_detects_vad_model(self, mock_parakeet_models: Path) -> None:
        """Test that get_status detects VAD model availability."""
        from distiller_sdk.parakeet import Parakeet

        # Add VAD model file
        (mock_parakeet_models / "silero_vad.onnx").write_bytes(b"fake vad model")

        status = Parakeet.get_status(model_path=str(mock_parakeet_models))

        assert status.state == HardwareState.AVAILABLE
        assert status.capabilities.get("vad_available") is True


class TestPiperDetection:
    """Tests for Piper.get_status() and Piper.is_available()."""

    def test_get_status_returns_hardware_status(self, mock_piper_models: dict[str, Path]) -> None:
        """Test that get_status returns HardwareStatus object."""
        from distiller_sdk.piper import Piper

        status = Piper.get_status(
            model_path=str(mock_piper_models["models"]),
            piper_path=str(mock_piper_models["binary"].parent),
        )

        assert isinstance(status, HardwareStatus)
        assert hasattr(status, "state")
        assert hasattr(status, "available")
        assert hasattr(status, "capabilities")
        assert hasattr(status, "error")
        assert hasattr(status, "diagnostic_info")
        assert hasattr(status, "message")

    def test_get_status_available_models(self, mock_piper_models: dict[str, Path]) -> None:
        """Test get_status when Piper models and binary are available."""
        from distiller_sdk.piper import Piper

        status = Piper.get_status(
            model_path=str(mock_piper_models["models"]),
            piper_path=str(mock_piper_models["binary"].parent),
        )

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        assert status.capabilities.get("tts_available") is True
        assert status.error is None
        assert "available" in status.message.lower()

    def test_get_status_missing_models(self, tmp_path: Any) -> None:
        """Test get_status when model files are missing."""
        from distiller_sdk.piper import Piper

        # Empty directory with no models
        status = Piper.get_status(model_path=str(tmp_path))

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        assert status.error is not None
        # Message should indicate missing models
        assert "model" in status.message.lower() or "not found" in status.message.lower()

    def test_get_status_missing_binary(
        self, mock_piper_models: dict[str, Path], tmp_path: Any
    ) -> None:
        """Test get_status when piper binary is missing."""
        from distiller_sdk.piper import Piper

        # Create empty piper directory without binary
        empty_piper_dir = tmp_path / "empty_piper"
        empty_piper_dir.mkdir()

        # Models exist but no binary
        status = Piper.get_status(
            model_path=str(mock_piper_models["models"]), piper_path=str(empty_piper_dir)
        )

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        # Message should indicate missing binary
        assert "binary" in status.message.lower() or "piper" in status.message.lower()

    def test_get_status_includes_capabilities(self, mock_piper_models: dict[str, Path]) -> None:
        """Test that get_status includes Piper capabilities."""
        from distiller_sdk.piper import Piper

        status = Piper.get_status(
            model_path=str(mock_piper_models["models"]),
            piper_path=str(mock_piper_models["binary"].parent),
        )

        assert "tts_available" in status.capabilities
        assert "voice" in status.capabilities

    def test_get_status_includes_diagnostic_info(self, mock_piper_models: dict[str, Path]) -> None:
        """Test that get_status includes diagnostic information."""
        from distiller_sdk.piper import Piper

        status = Piper.get_status(
            model_path=str(mock_piper_models["models"]),
            piper_path=str(mock_piper_models["binary"].parent),
        )

        assert isinstance(status.diagnostic_info, dict)
        assert len(status.diagnostic_info) > 0
        # Should have info about model and binary
        has_info = any(
            key in status.diagnostic_info for key in ["model_path", "piper_binary", "voice_model"]
        )
        assert has_info

    def test_is_available_returns_bool(self, mock_piper_models: dict[str, Path]) -> None:
        """Test that is_available returns a boolean."""
        from distiller_sdk.piper import Piper

        result = Piper.is_available(
            model_path=str(mock_piper_models["models"]),
            piper_path=str(mock_piper_models["binary"].parent),
        )

        assert isinstance(result, bool)

    def test_is_available_true_when_models_present(
        self, mock_piper_models: dict[str, Path]
    ) -> None:
        """Test is_available returns True when models and binary are present."""
        from distiller_sdk.piper import Piper

        assert (
            Piper.is_available(
                model_path=str(mock_piper_models["models"]),
                piper_path=str(mock_piper_models["binary"].parent),
            )
            is True
        )

    def test_is_available_false_when_models_absent(self, tmp_path: Any) -> None:
        """Test is_available returns False when models are absent."""
        from distiller_sdk.piper import Piper

        assert Piper.is_available(model_path=str(tmp_path)) is False


class TestWhisperDetection:
    """Tests for Whisper.get_status() and Whisper.is_available()."""

    def test_get_status_returns_hardware_status(self, mock_whisper_models: Path) -> None:
        """Test that get_status returns HardwareStatus object."""
        from distiller_sdk.whisper import Whisper

        status = Whisper.get_status(model_path=str(mock_whisper_models))

        assert isinstance(status, HardwareStatus)
        assert hasattr(status, "state")
        assert hasattr(status, "available")
        assert hasattr(status, "capabilities")
        assert hasattr(status, "error")
        assert hasattr(status, "diagnostic_info")
        assert hasattr(status, "message")

    def test_get_status_available_models(self, mock_whisper_models: Path) -> None:
        """Test get_status when Whisper models are available."""
        from distiller_sdk.whisper import Whisper

        # Create model.bin file in the subdirectory
        model_dir = mock_whisper_models / "faster-distil-whisper-small.en"
        model_dir.mkdir(exist_ok=True)
        (model_dir / "model.bin").write_bytes(b"fake whisper model")

        status = Whisper.get_status(model_path=str(mock_whisper_models))

        assert status.state == HardwareState.AVAILABLE
        assert status.available is True
        assert status.capabilities.get("asr_available") is True
        assert status.error is None
        assert "available" in status.message.lower()

    def test_get_status_missing_models(self, tmp_path: Any) -> None:
        """Test get_status when model files are missing."""
        from distiller_sdk.whisper import Whisper

        # Empty directory with no models
        status = Whisper.get_status(model_path=str(tmp_path))

        assert status.state == HardwareState.UNAVAILABLE
        assert status.available is False
        assert status.error is not None
        # Message should indicate missing models
        assert "model" in status.message.lower() or "not found" in status.message.lower()

    def test_get_status_includes_capabilities(self, mock_whisper_models: Path) -> None:
        """Test that get_status includes Whisper capabilities."""
        from distiller_sdk.whisper import Whisper

        # Create model.bin file
        model_dir = mock_whisper_models / "faster-distil-whisper-small.en"
        model_dir.mkdir(exist_ok=True)
        (model_dir / "model.bin").write_bytes(b"fake whisper model")

        status = Whisper.get_status(model_path=str(mock_whisper_models))

        assert "asr_available" in status.capabilities
        assert "model_type" in status.capabilities

    def test_get_status_includes_diagnostic_info(self, mock_whisper_models: Path) -> None:
        """Test that get_status includes diagnostic information."""
        from distiller_sdk.whisper import Whisper

        # Create model.bin file
        model_dir = mock_whisper_models / "faster-distil-whisper-small.en"
        model_dir.mkdir(exist_ok=True)
        (model_dir / "model.bin").write_bytes(b"fake whisper model")

        status = Whisper.get_status(model_path=str(mock_whisper_models))

        assert isinstance(status.diagnostic_info, dict)
        assert len(status.diagnostic_info) > 0
        # Should have info about model files
        has_info = any(
            key in status.diagnostic_info for key in ["model_path", "model_size", "model_file"]
        )
        assert has_info

    def test_is_available_returns_bool(self, mock_whisper_models: Path) -> None:
        """Test that is_available returns a boolean."""
        from distiller_sdk.whisper import Whisper

        # Create model.bin file
        model_dir = mock_whisper_models / "faster-distil-whisper-small.en"
        model_dir.mkdir(exist_ok=True)
        (model_dir / "model.bin").write_bytes(b"fake whisper model")

        result = Whisper.is_available(model_path=str(mock_whisper_models))

        assert isinstance(result, bool)

    def test_is_available_true_when_models_present(self, mock_whisper_models: Path) -> None:
        """Test is_available returns True when models are present."""
        from distiller_sdk.whisper import Whisper

        # Create model.bin file
        model_dir = mock_whisper_models / "faster-distil-whisper-small.en"
        model_dir.mkdir(exist_ok=True)
        (model_dir / "model.bin").write_bytes(b"fake whisper model")

        assert Whisper.is_available(model_path=str(mock_whisper_models)) is True

    def test_is_available_false_when_models_absent(self, tmp_path: Any) -> None:
        """Test is_available returns False when models are absent."""
        from distiller_sdk.whisper import Whisper

        assert Whisper.is_available(model_path=str(tmp_path)) is False
