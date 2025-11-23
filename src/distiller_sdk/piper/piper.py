import subprocess
import os
import logging
import re
import tempfile
from typing import Optional, List, Dict, Any, Literal

from distiller_sdk.hardware.audio.audio import Audio
from distiller_sdk import get_model_path
from distiller_sdk.hardware_status import HardwareStatus, HardwareState

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Piper")


class Piper:
    """Piper TTS engine.

    Args:
        model_path: Path to model directory (default: from get_model_path("piper"))
        piper_path: Path to piper binary directory (default: model_path/piper)
        configure_audio: Whether to set recommended audio levels (default: True)
                        If True, sets speaker volume to 30 for optimal TTS
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        piper_path: Optional[str] = None,
        configure_audio: bool = True,
    ) -> None:
        logger.info("Piper: Initializing Piper")

        # Configure audio with recommended settings if requested
        if configure_audio:
            Audio.set_speaker_volume_static(30)

        # Use provided paths or get from Debian package location
        if model_path is None:
            model_path = get_model_path("piper")
        if piper_path is None:
            piper_path = os.path.join(model_path, "piper")

        self.model_path = model_path
        self.piper_path = piper_path
        self.voice_onnx = os.path.join(self.model_path, "en_US-amy-medium.onnx")
        self.voice_json = os.path.join(self.model_path, "en_US-amy-medium.onnx.json")
        self.piper = os.path.join(self.piper_path, "piper")

        # Check if the model file exists
        if not os.path.exists(self.voice_onnx):
            logger.error(f"Piper: Model onnx file does not exist: {self.voice_onnx}")
            raise ValueError(f"Piper: Model onnx file does not exist: {self.voice_onnx}")
        if not os.path.exists(self.voice_json):
            logger.error(f"Piper: Model json file does not exist: {self.voice_json}")
            raise ValueError(f"Piper: Model json file does not exist: {self.voice_json}")
        if not os.path.exists(self.piper_path):
            logger.error(f"Piper: piper does not exist: {self.piper}")
            raise ValueError(f"Piper: piper does not exist: {self.piper}")

        logger.info("Piper: Piper initialized")

    @staticmethod
    def get_status(
        model_path: Optional[str] = None, piper_path: Optional[str] = None
    ) -> HardwareStatus:
        """Get detailed Piper TTS availability status.

        This method checks for Piper model files and binary without initializing
        the TTS engine. It never raises exceptions - all errors are captured in
        the returned status.

        Args:
            model_path: Path to model directory (default: from get_model_path("piper"))
            piper_path: Path to piper binary directory (default: model_path/piper)

        Returns:
            HardwareStatus: Detailed status including TTS availability,
                          capabilities, diagnostics, and error information

        Example:
            >>> status = Piper.get_status()
            >>> if status.available:
            ...     piper = Piper()
            >>> else:
            ...     print(f"Piper unavailable: {status.message}")
        """
        capabilities: Dict[str, Any] = {}
        diagnostic_info: Dict[str, Any] = {}

        try:
            if model_path is None:
                model_path = get_model_path("piper")
            if piper_path is None:
                piper_path = os.path.join(model_path, "piper")

            diagnostic_info["model_path"] = model_path
            diagnostic_info["piper_path"] = piper_path

            # Check if model directory exists
            if not os.path.exists(model_path):
                return HardwareStatus(
                    state=HardwareState.UNAVAILABLE,
                    available=False,
                    capabilities={},
                    error=FileNotFoundError(f"Piper model directory not found: {model_path}"),
                    diagnostic_info=diagnostic_info,
                    message=f"Piper model directory not found: {model_path}",
                )

            # Check for required model files
            voice_onnx = os.path.join(model_path, "en_US-amy-medium.onnx")
            voice_json = os.path.join(model_path, "en_US-amy-medium.onnx.json")

            missing_files = []
            if not os.path.exists(voice_onnx):
                missing_files.append("en_US-amy-medium.onnx")
            if not os.path.exists(voice_json):
                missing_files.append("en_US-amy-medium.onnx.json")

            if missing_files:
                return HardwareStatus(
                    state=HardwareState.UNAVAILABLE,
                    available=False,
                    capabilities={},
                    error=FileNotFoundError(
                        f"Piper model files missing: {', '.join(missing_files)}"
                    ),
                    diagnostic_info={
                        "model_path": model_path,
                        "missing_files": missing_files,
                    },
                    message=f"Piper model incomplete - missing files: {', '.join(missing_files)}",
                )

            diagnostic_info["voice_model"] = "en_US-amy-medium"

            # Check for piper binary
            piper_binary = os.path.join(piper_path, "piper")
            if not os.path.exists(piper_binary):
                return HardwareStatus(
                    state=HardwareState.UNAVAILABLE,
                    available=False,
                    capabilities={},
                    error=FileNotFoundError(f"Piper binary not found: {piper_binary}"),
                    diagnostic_info=diagnostic_info,
                    message=f"Piper binary not found: {piper_binary}",
                )

            # Check if binary is executable
            if not os.access(piper_binary, os.X_OK):
                return HardwareStatus(
                    state=HardwareState.PERMISSION_DENIED,
                    available=False,
                    capabilities={},
                    error=PermissionError(f"Piper binary not executable: {piper_binary}"),
                    diagnostic_info=diagnostic_info,
                    message=f"Piper binary not executable: {piper_binary}",
                )

            diagnostic_info["piper_binary"] = piper_binary

            # TTS available
            capabilities["tts_available"] = True
            capabilities["voice"] = "en_US-amy-medium"

            # All checks passed
            return HardwareStatus(
                state=HardwareState.AVAILABLE,
                available=True,
                capabilities=capabilities,
                error=None,
                diagnostic_info=diagnostic_info,
                message="Piper TTS available (en_US-amy-medium)",
            )

        except PermissionError as e:
            return HardwareStatus(
                state=HardwareState.PERMISSION_DENIED,
                available=False,
                capabilities={},
                error=e,
                diagnostic_info=diagnostic_info,
                message=f"Permission denied accessing Piper: {str(e)}",
            )
        except Exception as e:
            return HardwareStatus(
                state=HardwareState.UNAVAILABLE,
                available=False,
                capabilities={},
                error=e,
                diagnostic_info=diagnostic_info,
                message=f"Error detecting Piper: {str(e)}",
            )

    @staticmethod
    def is_available(model_path: Optional[str] = None, piper_path: Optional[str] = None) -> bool:
        """Quick check if Piper TTS is available.

        This is a convenience method that returns the available flag from get_status().
        Use get_status() for detailed information about TTS capabilities and errors.

        Args:
            model_path: Path to model directory (default: from get_model_path("piper"))
            piper_path: Path to piper binary directory (default: model_path/piper)

        Returns:
            bool: True if Piper TTS is available

        Example:
            >>> if Piper.is_available():
            ...     piper = Piper()
            ... else:
            ...     print("Piper TTS not available")
        """
        return Piper.get_status(model_path=model_path, piper_path=piper_path).available

    def list_voices(self) -> List[Dict[str, str]]:
        """
        List available voices for Piper TTS.
        Returns a list of voice information dictionaries.
        """
        voices = [
            {
                "name": "en_US-amy-medium",
                "language": "English (US)",
                "quality": "medium",
                "model_path": self.voice_onnx,
                "config_path": self.voice_json,
            }
        ]
        logger.info(f"Piper: Available voices: {[v['name'] for v in voices]}")
        return voices

    def get_wav_file_path(self, text: str, output_path: Optional[str] = None) -> str:
        """Generate WAV file from text using Piper TTS.

        Args:
            text: Text to convert to speech
            output_path: Optional path for output WAV file

        Returns:
            Path to generated WAV file

        Raises:
            ValueError: If piper command fails
        """
        if output_path is None:
            # Create unique temp file in current directory
            fd, output_path = tempfile.mkstemp(suffix=".wav", dir=os.getcwd())
            os.close(fd)  # Close the file descriptor, we just want the path

        # Build command without shell - pass text via stdin
        command = [
            self.piper,
            "--model",
            self.voice_onnx,
            "--config",
            self.voice_json,
            "--output_file",
            output_path,
        ]
        logger.info(f"Piper exec command: {' '.join(command)}")
        try:
            subprocess.run(command, input=text, text=True, capture_output=True, check=True)
            logger.info(f"Piper: Text '{text}' spoken successfully and saved to {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Piper: Error running piper command: {e.stderr}")
            raise ValueError(f"Piper: Error running piper command: {e.stderr}")

    def find_hw_by_name(self, card_name: str) -> str:
        try:
            result = subprocess.run(["aplay", "-l"], capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()

            for line in lines:
                if "card" in line and card_name in line:
                    match = re.search(r"card (\d+):", line)
                    if match:
                        card_num = match.group(1)
                        logger.info(f"Piper: Found sound card '{card_name}' with number {card_num}")
                        return card_num

            logger.warning(f"Piper: Sound card '{card_name}' not found, defaulting to card 0")
            return "0"  # Default fallback
        except Exception as e:
            logger.warning(f"Piper: Error finding sound card: {str(e)}, defaulting to card 0")
            return "0"  # Default fallback

    def speak_stream(
        self, text: str, volume: int = 50, sound_card_name: Optional[str] = None
    ) -> None:
        """Stream TTS audio directly to speaker using pipe.

        Args:
            text: Text to convert to speech
            volume: Speaker volume (0-100, default: 50)
            sound_card_name: Optional sound card name to use

        Raises:
            ValueError: If volume is out of range or streaming fails
        """
        if volume < 0 or volume > 100:
            logger.warning("Piper: The volume level is not within the range of 0-100.")
            raise ValueError("Piper: The volume level is not within the range of 0-100.")

        Audio.set_speaker_volume_static(volume)

        # Find sound card by name if provided
        hw_num = "0"  # Default
        if sound_card_name:
            hw_num = self.find_hw_by_name(sound_card_name)

        # Build commands without shell - pipe piper output to aplay
        piper_cmd = [
            "sudo",
            self.piper,
            "--model",
            self.voice_onnx,
            "--config",
            self.voice_json,
            "--output-raw",
        ]
        aplay_cmd = ["aplay", "-D", f"plughw:{hw_num}", "-r", "22050", "-f", "S16_LE", "-t", "raw"]

        logger.info(f"Piper: Executing pipeline: {' '.join(piper_cmd)} | {' '.join(aplay_cmd)}")
        try:
            # Create pipeline: text → piper → aplay
            piper_process = subprocess.Popen(
                piper_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            aplay_process = subprocess.Popen(
                aplay_cmd,
                stdin=piper_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Close piper stdout in parent to allow piper to receive SIGPIPE if aplay exits
            if piper_process.stdout is not None:
                piper_process.stdout.close()

            # Send text to piper and wait for completion
            piper_stdout, piper_stderr = piper_process.communicate(input=text)
            aplay_stdout, aplay_stderr = aplay_process.communicate()

            # Check for errors
            if piper_process.returncode != 0:
                if isinstance(piper_stderr, str):
                    piper_stderr_str = piper_stderr
                elif isinstance(piper_stderr, bytes):
                    piper_stderr_str = piper_stderr.decode()
                else:
                    piper_stderr_str = ""
                logger.error(f"Piper: Piper command failed: {piper_stderr_str}")
                raise ValueError(f"Piper: Piper command failed: {piper_stderr_str}")
            if aplay_process.returncode != 0:
                aplay_stderr_str = aplay_stderr.decode() if aplay_stderr else ""
                logger.error(f"Piper: aplay command failed: {aplay_stderr_str}")
                raise ValueError(f"Piper: aplay command failed: {aplay_stderr_str}")

            logger.info(f"Piper: Text '{text}' streamed successfully")
        except Exception as e:
            logger.error(f"Piper: Error streaming audio: {str(e)}")
            raise ValueError(f"Piper: Error streaming audio: {str(e)}")

    def __enter__(self) -> "Piper":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> Literal[False]:
        """Exit context manager. Piper has no resources to cleanup."""
        return False


__all__ = ["Piper"]

if __name__ == "__main__":
    piper = Piper()
    text_t = "Hello, this is a test."
    output_file_path_t = piper.get_wav_file_path(text_t)
    print("output_file_path:", output_file_path_t)
    # Example using the sound card by name
    piper.speak_stream(text_t, 30, "snd_rpi_pamir_ai_soundcard")
