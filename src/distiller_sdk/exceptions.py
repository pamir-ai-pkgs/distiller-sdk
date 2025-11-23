"""Exception hierarchy for Distiller SDK.

This module provides a standardized exception hierarchy for all Distiller SDK
errors, making it easier to catch and handle specific types of failures.

Exception Hierarchy:
    DistillerError (base)
    ├── HardwareError
    │   ├── AudioError
    │   ├── DisplayError
    │   ├── CameraError
    │   └── LEDError
    ├── AIError
    │   ├── ParakeetError
    │   ├── PiperError
    │   └── WhisperError
    ├── ConfigurationError
    └── ResourceError

Example:
    >>> try:
    ...     audio = Audio()
    ... except AudioError as e:
    ...     print(f"Audio error: {e}")
    ... except HardwareError as e:
    ...     print(f"Hardware error: {e}")
    ... except DistillerError as e:
    ...     print(f"Distiller error: {e}")
"""


class DistillerError(Exception):
    """Base exception for all Distiller SDK errors.

    All Distiller SDK exceptions inherit from this base class, allowing
    users to catch all SDK-related errors with a single except clause.

    Example:
        >>> try:
        ...     # Any Distiller SDK operation
        ...     audio.record("output.wav")
        ... except DistillerError as e:
        ...     print(f"SDK error: {e}")
    """

    pass


class HardwareError(DistillerError):
    """Base exception for hardware-related errors.

    Raised when hardware devices (audio, display, camera, LED) fail or
    are unavailable. Use specific subclasses for targeted error handling.

    Example:
        >>> try:
        ...     display.show_image("image.png")
        ... except HardwareError as e:
        ...     print(f"Hardware unavailable: {e}")
    """

    pass


class AudioError(HardwareError):
    """Exception for audio hardware errors.

    Raised when:
    - Audio devices not found
    - Recording/playback fails
    - Audio configuration errors
    - ALSA errors

    Example:
        >>> try:
        ...     audio = Audio()
        ... except AudioError as e:
        ...     print(f"Audio error: {e}")
    """

    pass


class DisplayError(HardwareError):
    """Exception for e-ink display errors.

    Raised when:
    - Display hardware not available
    - SPI communication fails
    - Image rendering fails
    - Display initialization fails

    Example:
        >>> try:
        ...     display = Display()
        ... except DisplayError as e:
        ...     print(f"Display error: {e}")
    """

    pass


class CameraError(HardwareError):
    """Exception for camera hardware errors.

    Raised when:
    - Camera device not found
    - rpicam-still/libcamera not available
    - Photo/video capture fails
    - Camera configuration errors

    Example:
        >>> try:
        ...     camera = Camera()
        ... except CameraError as e:
        ...     print(f"Camera error: {e}")
    """

    pass


class LEDError(HardwareError):
    """Exception for LED control errors.

    Raised when:
    - LED sysfs interface not available
    - LED control fails
    - Permission denied for LED access

    Example:
        >>> try:
        ...     led = LED()
        ... except LEDError as e:
        ...     print(f"LED error: {e}")
    """

    pass


class AIError(DistillerError):
    """Base exception for AI/ML module errors.

    Raised when AI models (ASR, TTS) fail or are unavailable. Use specific
    subclasses for targeted error handling.

    Example:
        >>> try:
        ...     parakeet = Parakeet()
        ... except AIError as e:
        ...     print(f"AI module error: {e}")
    """

    pass


class ParakeetError(AIError):
    """Exception for Parakeet ASR errors.

    Raised when:
    - Parakeet models not found
    - Model loading fails
    - Transcription fails
    - Audio input errors

    Example:
        >>> try:
        ...     parakeet = Parakeet()
        ...     text = parakeet.transcribe("audio.wav")
        ... except ParakeetError as e:
        ...     print(f"Parakeet error: {e}")
    """

    pass


class PiperError(AIError):
    """Exception for Piper TTS errors.

    Raised when:
    - Piper binary not found
    - Voice models not available
    - Text synthesis fails
    - Audio output errors

    Example:
        >>> try:
        ...     piper = Piper()
        ...     piper.synthesize("Hello world")
        ... except PiperError as e:
        ...     print(f"Piper error: {e}")
    """

    pass


class WhisperError(AIError):
    """Exception for Whisper ASR errors.

    Raised when:
    - Whisper models not found
    - Model loading fails
    - Transcription fails
    - GPU/CPU allocation errors

    Example:
        >>> try:
        ...     whisper = Whisper()
        ...     text = whisper.transcribe("audio.wav")
        ... except WhisperError as e:
        ...     print(f"Whisper error: {e}")
    """

    pass


class ConfigurationError(DistillerError):
    """Exception for configuration and initialization errors.

    Raised when:
    - Invalid configuration values
    - Missing required configuration
    - Platform detection fails
    - Environment setup errors

    Example:
        >>> try:
        ...     display = Display(firmware="INVALID")
        ... except ConfigurationError as e:
        ...     print(f"Configuration error: {e}")
    """

    pass


class ResourceError(DistillerError):
    """Exception for resource management errors.

    Raised when:
    - Device already in use
    - Resource locking fails
    - Concurrent access violations
    - Cleanup failures

    Example:
        >>> try:
        ...     audio.record("output.wav")
        ... except ResourceError as e:
        ...     print(f"Resource busy: {e}")
    """

    pass
