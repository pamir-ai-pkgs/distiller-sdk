"""Shared pytest fixtures for distiller-sdk tests."""

import subprocess
from pathlib import Path
from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch


# ============================================================================
# Hardware Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_audio_hardware(monkeypatch: MonkeyPatch) -> None:
    """Mock audio hardware for unit tests.

    Simulates ALSA tools (arecord, aplay) being available with audio devices.
    """

    def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        cmd = args[0] if args else kwargs.get("args", [])
        if isinstance(cmd, list):
            cmd_str = " ".join(cmd)
        else:
            cmd_str = cmd

        if "arecord -l" in cmd_str:
            return subprocess.CompletedProcess(
                cmd,
                0,
                b"**** List of CAPTURE Hardware Devices ****\ncard 0: USB [USB Audio Device], device 0: USB Audio [USB Audio]\n",
                b"",
            )
        elif "aplay -l" in cmd_str:
            return subprocess.CompletedProcess(
                cmd,
                0,
                b"**** List of PLAYBACK Hardware Devices ****\ncard 0: USB [USB Audio Device], device 0: USB Audio [USB Audio]\n",
                b"",
            )
        elif "amixer" in cmd_str:
            return subprocess.CompletedProcess(cmd, 0, b"Volume: 50", b"")
        else:
            return subprocess.CompletedProcess(cmd, 1, b"", b"Command not found")

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
def mock_audio_unavailable(monkeypatch: MonkeyPatch) -> None:
    """Mock audio hardware being unavailable."""

    def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError("arecord: command not found")

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
def mock_display_hardware(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """Mock e-ink display hardware for unit tests.

    Simulates e-ink display hardware including SPI device, GPIO chip,
    shared library, and config file being available.
    """
    import os

    # Mock os.path.exists to simulate hardware devices
    original_exists = os.path.exists

    def mock_exists(path: Any) -> bool:
        path_str = str(path)
        # Mock SPI device
        if "/dev/spidev" in path_str:
            return True
        # Mock GPIO chip
        if "/dev/gpiochip" in path_str:
            return True
        # Mock shared library
        if "libdistiller_display_sdk_shared.so" in path_str:
            return True
        # Mock config file
        if "eink.conf" in path_str:
            return True
        # Everything else use original behavior
        return original_exists(path)

    monkeypatch.setattr("os.path.exists", mock_exists)

    # Mock os.access for permission checks
    def mock_access(path: Any, mode: int) -> bool:
        path_str = str(path)
        if "/dev/spidev" in path_str or "/dev/gpiochip" in path_str:
            return True
        return os.access(path, mode)

    monkeypatch.setattr("os.access", mock_access)


@pytest.fixture
def mock_camera_hardware(monkeypatch: MonkeyPatch) -> None:
    """Mock camera hardware for unit tests.

    Simulates Raspberry Pi camera with rpicam-still available and camera detected.
    """
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

        if "rpicam-still" in cmd_str:
            if "--list-cameras" in cmd_str:
                # Simulate camera detected
                return subprocess.CompletedProcess(
                    cmd,
                    0,
                    "Available cameras\n0 : imx219 [3280 x 2464] (/base/soc/i2c0mux/i2c@1/imx219@10)\nModes: 'SRGGB10_CSI2P' : 640x480 1640x1232 3280x2464\n",
                    "",
                )
            elif "--version" in cmd_str:
                return subprocess.CompletedProcess(cmd, 0, "rpicam-still 1.0.0", "")
            else:
                # Other rpicam-still commands succeed
                return subprocess.CompletedProcess(cmd, 0, "", "")
        else:
            return subprocess.CompletedProcess(cmd, 1, "", "Command not found")

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
def mock_led_hardware(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    """Mock LED sysfs interface for unit tests.

    Simulates Pamir RGB LED hardware with sysfs interface including
    multiple LEDs with RGB control, animation modes, and triggers.
    """
    # Create mock sysfs LED directory structure
    led_base = tmp_path / "sys" / "class" / "leds"
    led_base.mkdir(parents=True, exist_ok=True)

    # Create multiple LED directories (pamir:led0, pamir:led1)
    for led_num in [0, 1]:
        led_path = led_base / f"pamir:led{led_num}"
        led_path.mkdir(parents=True, exist_ok=True)

        # Create RGB control files
        (led_path / "red").write_text("0")
        (led_path / "green").write_text("0")
        (led_path / "blue").write_text("0")
        (led_path / "brightness").write_text("255")

        # Animation support
        (led_path / "animation_mode").write_text("static")
        (led_path / "animation_timing").write_text("500")

        # Trigger support
        (led_path / "trigger").write_text("[none] heartbeat-rgb breathing-rgb")

    # Mock LED.get_status to use tmp_path
    original_get_status: Any = None
    try:
        from distiller_sdk.hardware.sam import LED

        if hasattr(LED, "get_status"):
            original_get_status = LED.get_status

            def mock_get_status(base_path: str = "/sys/class/leds") -> Any:
                # Redirect to our tmp_path if default path requested
                if base_path == "/sys/class/leds":
                    base_path = str(led_base)
                return original_get_status(base_path=base_path)

            monkeypatch.setattr(LED, "get_status", staticmethod(mock_get_status))
    except (ImportError, AttributeError):
        # LED class or get_status not yet implemented
        pass

    return led_base


# ============================================================================
# AI Model Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_parakeet_models(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    """Mock Parakeet model files."""
    models_dir = tmp_path / "parakeet" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # Create required ASR model files
    (models_dir / "encoder.onnx").write_bytes(b"fake encoder model")
    (models_dir / "decoder.onnx").write_bytes(b"fake decoder model")
    (models_dir / "joiner.onnx").write_bytes(b"fake joiner model")
    (models_dir / "tokens.txt").write_text("fake tokens")

    return models_dir


@pytest.fixture
def mock_piper_models(monkeypatch: MonkeyPatch, tmp_path: Path) -> dict[str, Path]:
    """Mock Piper model files and binary."""
    models_dir = tmp_path / "piper" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # Create required TTS model files
    (models_dir / "en_US-amy-medium.onnx").write_bytes(b"fake voice model")
    (models_dir / "en_US-amy-medium.onnx.json").write_text('{"fake": "config"}')

    # Create mock piper binary directory
    piper_dir = tmp_path / "piper" / "piper"
    piper_dir.mkdir(parents=True, exist_ok=True)

    # Create mock piper executable
    piper_bin = piper_dir / "piper"
    piper_bin.write_text("#!/bin/bash\necho 'fake piper'")
    piper_bin.chmod(0o755)

    return {"models": models_dir, "binary": piper_bin}


@pytest.fixture
def mock_whisper_models(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    """Mock Whisper model files."""
    models_dir = tmp_path / "whisper" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # Create mock model directory
    (models_dir / "base.en").mkdir()

    return models_dir


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def temp_audio_file(tmp_path: Path) -> Path:
    """Create a temporary WAV file for testing."""
    audio_file = tmp_path / "test_audio.wav"
    # Create a minimal WAV file header (44 bytes)
    wav_header = (
        b"RIFF"  # ChunkID
        b"\x24\x00\x00\x00"  # ChunkSize (36 + data size)
        b"WAVE"  # Format
        b"fmt "  # Subchunk1ID
        b"\x10\x00\x00\x00"  # Subchunk1Size (16 for PCM)
        b"\x01\x00"  # AudioFormat (1 for PCM)
        b"\x01\x00"  # NumChannels (1 = mono)
        b"\x44\xac\x00\x00"  # SampleRate (44100)
        b"\x88\x58\x01\x00"  # ByteRate
        b"\x02\x00"  # BlockAlign
        b"\x10\x00"  # BitsPerSample (16)
        b"data"  # Subchunk2ID
        b"\x00\x00\x00\x00"  # Subchunk2Size (0 = no audio data)
    )
    audio_file.write_bytes(wav_header)
    return audio_file


@pytest.fixture
def temp_image_file(tmp_path: Path) -> Path:
    """Create a temporary image file for testing."""
    image_file = tmp_path / "test_image.png"
    # Create a minimal 1x1 PNG file
    png_data = (
        b"\x89PNG\r\n\x1a\n"  # PNG signature
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"  # IHDR chunk
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n-\xb4"  # IDAT chunk (1x1 transparent pixel)
        b"\x00\x00\x00\x00IEND\xaeB`\x82"  # IEND chunk
    )
    image_file.write_bytes(png_data)
    return image_file


# ============================================================================
# Parametrize Helpers
# ============================================================================


def hardware_states() -> list[tuple[str, bool, dict[str, Any], Exception | None, str]]:
    """Provide common hardware states for parametrized tests."""
    return [
        ("available", True, {}, None, "Hardware available"),
        ("unavailable", False, {}, FileNotFoundError("Not found"), "Hardware not found"),
        ("permission_denied", False, {}, PermissionError("Access denied"), "Permission denied"),
        (
            "partially_available",
            True,
            {"input": True, "output": False},
            None,
            "Partial availability",
        ),
    ]
