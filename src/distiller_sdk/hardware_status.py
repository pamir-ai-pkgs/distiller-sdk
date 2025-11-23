"""Hardware status system for Distiller SDK.

This module provides a standardized way to represent hardware availability
and capabilities across all Distiller hardware and AI modules.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class HardwareState(Enum):
    """Represents the state of hardware availability.

    Attributes:
        AVAILABLE: Hardware is fully available and ready to use
        UNAVAILABLE: Hardware is not available (missing, not installed)
        PERMISSION_DENIED: Hardware exists but access is denied
        PARTIALLY_AVAILABLE: Some hardware features available, others not
    """

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    PERMISSION_DENIED = "permission_denied"
    PARTIALLY_AVAILABLE = "partially_available"


@dataclass
class HardwareStatus:
    """Detailed hardware status with diagnostics.

    This class provides comprehensive information about hardware availability,
    capabilities, and any errors encountered during detection.

    Attributes:
        state: Overall hardware state (enum)
        available: Quick boolean check (True if hardware is usable)
        capabilities: Dictionary of hardware capabilities (feature: bool)
        error: Exception if hardware detection failed, None otherwise
        diagnostic_info: Additional diagnostic information as dictionary
        message: Human-readable status message

    Example:
        >>> status = Audio.get_status()
        >>> if status.available:
        ...     print(f"Audio ready: {status.message}")
        ...     if status.capabilities.get("input"):
        ...         audio = Audio()
        ...         audio.record("output.wav")
        >>> else:
        ...     print(f"Audio unavailable: {status.message}")
        ...     if status.error:
        ...         print(f"Error: {status.error}")
    """

    state: HardwareState
    available: bool
    capabilities: Dict[str, Any]
    error: Optional[Exception]
    diagnostic_info: Dict[str, Any]
    message: str

    def __post_init__(self) -> None:
        """Validate hardware status after initialization."""
        # Ensure consistency between state and available flag
        if self.state == HardwareState.AVAILABLE:
            if not self.available:
                raise ValueError("State AVAILABLE requires available=True")
        elif self.state in (HardwareState.UNAVAILABLE, HardwareState.PERMISSION_DENIED):
            if self.available:
                raise ValueError(f"State {self.state.value} requires available=False")
