import subprocess
import threading
from typing import List, Optional, Tuple, Dict, Any, Literal
from pathlib import Path

from distiller_sdk.exceptions import LEDError
from distiller_sdk.hardware_status import HardwareStatus, HardwareState


class LED:
    """
    SDK interface for RGB LED control via sysfs.

    This class provides comprehensive RGB LED control with support for:
    - Multiple LEDs (led0, led1, led2, etc.)
    - RGB color control (0-255 per component)
    - Animation modes (static, blink, fade, rainbow) - kernel-based looping
    - LED triggers (heartbeat-rgb, breathing-rgb, rainbow-rgb, and standard Linux triggers)
    - Brightness control (0-255)
    - Timing control for animations (100/200/500/1000ms)

    Animation modes are hardware-accelerated and loop continuously in the kernel driver.
    LED triggers provide system-driven patterns like heartbeat and breathing effects.

    Note: Most operations require root privileges. Use sudo or set use_sudo=True.
    """

    # Valid animation modes and timings supported by kernel driver
    VALID_MODES = ["static", "blink", "fade", "rainbow"]
    VALID_TIMINGS = [100, 200, 500, 1000]

    def __init__(self, base_path: str = "/sys/class/leds", use_sudo: bool = False):
        """
        Initialize the LED module interface.

        Args:
            base_path: Base path for LED sysfs interface (default: /sys/class/leds)
            use_sudo: Whether to use sudo for write operations (default: False)

        Raises:
            LEDError: If the sysfs interface is not available or accessible
        """
        self.base_path = Path(base_path)
        self.use_sudo = use_sudo

        # Thread safety lock
        self._lock = threading.Lock()

        # Check if sysfs interface exists
        if not self.base_path.exists():
            raise LEDError(f"LED sysfs interface not found at {base_path}")

        # Discover available LEDs
        self.available_leds = self._discover_leds()

        if not self.available_leds:
            raise LEDError("No compatible LEDs found (pamir:led* pattern)")

    @staticmethod
    def get_status(base_path: str = "/sys/class/leds") -> HardwareStatus:
        """Get detailed LED hardware status without initializing.

        This method probes LED hardware availability and capabilities without
        creating an LED instance or modifying system state. It never raises
        exceptions - all errors are captured in the returned status.

        Args:
            base_path: Base path for LED sysfs interface (default: /sys/class/leds)

        Returns:
            HardwareStatus: Detailed hardware status including state, capabilities,
                          diagnostics, and error information

        Example:
            >>> status = LED.get_status()
            >>> if status.available:
            ...     led = LED()
            >>> else:
            ...     print(f"LED unavailable: {status.message}")
        """
        capabilities: Dict[str, Any] = {}
        diagnostic_info: Dict[str, Any] = {}

        try:
            # Check if sysfs interface exists
            base = Path(base_path)
            if not base.exists():
                return HardwareStatus(
                    state=HardwareState.UNAVAILABLE,
                    available=False,
                    capabilities={},
                    error=FileNotFoundError(f"LED sysfs interface not found at {base_path}"),
                    diagnostic_info={"sysfs_path": base_path},
                    message=f"LED sysfs interface not found at {base_path}",
                )

            diagnostic_info["sysfs_path"] = str(base)

            # Discover available LEDs (pamir:led* pattern)
            available_leds = []
            led_details = []

            try:
                for item in base.iterdir():
                    if item.is_dir() and item.name.startswith("pamir:led"):
                        try:
                            led_num = int(item.name.replace("pamir:led", ""))
                            available_leds.append(led_num)

                            # Check for RGB support
                            has_rgb = all(
                                (item / component).exists()
                                for component in ["red", "green", "blue"]
                            )

                            # Check for animation support
                            has_animation = (item / "animation_mode").exists()

                            # Check for trigger support
                            has_trigger = (item / "trigger").exists()

                            led_details.append(
                                {
                                    "led_id": led_num,
                                    "rgb": has_rgb,
                                    "animation": has_animation,
                                    "trigger": has_trigger,
                                }
                            )

                        except ValueError:
                            continue

            except PermissionError as e:
                return HardwareStatus(
                    state=HardwareState.PERMISSION_DENIED,
                    available=False,
                    capabilities={},
                    error=e,
                    diagnostic_info=diagnostic_info,
                    message=f"Permission denied accessing LED sysfs: {str(e)}",
                )

            if not available_leds:
                return HardwareStatus(
                    state=HardwareState.UNAVAILABLE,
                    available=False,
                    capabilities={},
                    error=FileNotFoundError("No LEDs found matching pamir:led* pattern"),
                    diagnostic_info=diagnostic_info,
                    message="No compatible LEDs found (pamir:led* pattern)",
                )

            # Set capabilities
            capabilities["led_count"] = len(available_leds)
            capabilities["available_leds"] = sorted(available_leds)

            # Check if all LEDs have RGB support
            capabilities["rgb_support"] = all(led["rgb"] for led in led_details)

            # Check if any LED has animation support
            capabilities["animation_support"] = any(led["animation"] for led in led_details)

            # Check if any LED has trigger support
            capabilities["trigger_support"] = any(led["trigger"] for led in led_details)

            # Diagnostic info
            diagnostic_info["led_list"] = led_details
            diagnostic_info["leds_found"] = len(available_leds)

            # All checks passed
            return HardwareStatus(
                state=HardwareState.AVAILABLE,
                available=True,
                capabilities=capabilities,
                error=None,
                diagnostic_info=diagnostic_info,
                message=f"LED hardware available ({len(available_leds)} LED(s) detected)",
            )

        except PermissionError as e:
            return HardwareStatus(
                state=HardwareState.PERMISSION_DENIED,
                available=False,
                capabilities={},
                error=e,
                diagnostic_info=diagnostic_info,
                message=f"Permission denied accessing LED hardware: {str(e)}",
            )
        except FileNotFoundError as e:
            return HardwareStatus(
                state=HardwareState.UNAVAILABLE,
                available=False,
                capabilities={},
                error=e,
                diagnostic_info=diagnostic_info,
                message=f"LED hardware not found: {str(e)}",
            )
        except Exception as e:
            return HardwareStatus(
                state=HardwareState.UNAVAILABLE,
                available=False,
                capabilities={},
                error=e,
                diagnostic_info=diagnostic_info,
                message=f"Error detecting LED hardware: {str(e)}",
            )

    @staticmethod
    def is_available() -> bool:
        """Quick check if LED hardware is available.

        This is a convenience method that returns the available flag from get_status().
        Use get_status() for detailed information about capabilities and errors.

        Returns:
            bool: True if LED hardware is available and accessible

        Example:
            >>> if LED.is_available():
            ...     led = LED()
            ... else:
            ...     print("LED hardware not available")
        """
        return LED.get_status().available

    def _discover_leds(self) -> List[int]:
        """
        Discover available LEDs by scanning for pamir:led* directories.

        Returns:
            List of LED numbers (e.g., [0, 1, 2] for led0, led1, led2)
        """
        leds = []

        try:
            for item in self.base_path.iterdir():
                if item.is_dir() and item.name.startswith("pamir:led"):
                    try:
                        led_num = int(item.name.replace("pamir:led", ""))
                        leds.append(led_num)
                    except ValueError:
                        continue
        except (OSError, PermissionError):
            pass

        return sorted(leds)

    def _get_led_path(self, led_id: int) -> Path:
        """
        Get the sysfs path for a specific LED.

        Args:
            led_id: LED number (0, 1, 2, etc.)

        Returns:
            Path to the LED's sysfs directory

        Raises:
            LEDError: If LED ID is not available
        """
        if led_id not in self.available_leds:
            raise LEDError(f"LED {led_id} not available. Available LEDs: {self.available_leds}")

        return self.base_path / f"pamir:led{led_id}"

    def _write_sysfs_file(self, file_path: Path, value: str) -> None:
        """
        Write a value to a sysfs file.

        Args:
            file_path: Path to sysfs file
            value: Value to write

        Raises:
            LEDError: If writing fails
        """
        if self.use_sudo:
            try:
                # Use subprocess with sudo to write the value
                cmd = ["sudo", "tee", str(file_path)]
                subprocess.run(cmd, input=str(value), text=True, capture_output=True, check=True)
            except subprocess.CalledProcessError as e:
                raise LEDError(f"Failed to write '{value}' to {file_path} using sudo: {e}")
            except FileNotFoundError:
                raise LEDError("sudo command not found. Please install sudo or run as root.")
        else:
            try:
                with open(file_path, "w") as f:
                    f.write(str(value))
                    f.flush()
            except PermissionError as e:
                raise LEDError(
                    f"Permission denied writing to {file_path}. "
                    f"Try running with sudo or initialize LED(use_sudo=True). "
                    f"Original error: {e}"
                )
            except (OSError, IOError) as e:
                raise LEDError(f"Failed to write '{value}' to {file_path}: {e}")

    def _read_sysfs_file(self, file_path: Path) -> str:
        """
        Read a value from a sysfs file.

        Args:
            file_path: Path to sysfs file

        Returns:
            Content of the file (stripped)

        Raises:
            LEDError: If reading fails
        """
        try:
            with open(file_path, "r") as f:
                return f.read().strip()
        except (OSError, IOError, PermissionError) as e:
            raise LEDError(f"Failed to read from {file_path}: {e}")

    def set_sudo_mode(self, use_sudo: bool) -> None:
        """
        Enable or disable sudo mode for write operations.

        Args:
            use_sudo: Whether to use sudo for write operations
        """
        self.use_sudo = use_sudo

    def get_available_leds(self) -> List[int]:
        """
        Get list of available LED IDs.

        Returns:
            List of available LED numbers
        """
        return self.available_leds.copy()

    def set_rgb_color(self, led_id: int, red: int, green: int, blue: int) -> None:
        """
        Set RGB color for a specific LED.

        Args:
            led_id: LED number (0, 1, 2, etc.)
            red: Red component (0-255)
            green: Green component (0-255)
            blue: Blue component (0-255)

        Raises:
            LEDError: If LED ID is invalid or values are out of range

        Note:
            Each RGB component write sends a separate command to the hardware.
            Brief color transitions may be visible during updates (R → R+G → R+G+B).
        """
        # Validate color values
        for component, value in [("red", red), ("green", green), ("blue", blue)]:
            if not 0 <= value <= 255:
                raise LEDError(f"{component.capitalize()} value {value} out of range (0-255)")

        with self._lock:
            led_path = self._get_led_path(led_id)

            # Set RGB components
            self._write_sysfs_file(led_path / "red", str(red))
            self._write_sysfs_file(led_path / "green", str(green))
            self._write_sysfs_file(led_path / "blue", str(blue))

    def get_rgb_color(self, led_id: int) -> Tuple[int, int, int]:
        """
        Get current RGB color for a specific LED.

        Args:
            led_id: LED number (0, 1, 2, etc.)

        Returns:
            Tuple of (red, green, blue) values (0-255)

        Raises:
            LEDError: If LED ID is invalid or reading fails
        """
        led_path = self._get_led_path(led_id)

        try:
            red = int(self._read_sysfs_file(led_path / "red"))
            green = int(self._read_sysfs_file(led_path / "green"))
            blue = int(self._read_sysfs_file(led_path / "blue"))
            return (red, green, blue)
        except ValueError as e:
            raise LEDError(f"Failed to parse RGB values for LED {led_id}: {e}")

    def set_animation_mode(self, led_id: int, mode: str, timing: Optional[int] = None) -> None:
        """
        Set animation mode for a specific LED with kernel-based looping.

        Animations run continuously in the kernel driver without CPU intervention.

        Args:
            led_id: LED number (0, 1, 2, etc.)
            mode: Animation mode - "static", "blink", "fade", or "rainbow"
            timing: Optional timing in milliseconds. Will be rounded to nearest
                   valid value (100, 200, 500, or 1000). If not provided, current
                   timing value is preserved.

        Raises:
            LEDError: If LED ID is invalid or mode is not supported

        Examples:
            led.set_animation_mode(0, "blink", 500)  # Blink every 500ms
            led.set_animation_mode(0, "rainbow", 1000)  # Rainbow cycle, 1 second per cycle
            led.set_animation_mode(0, "static")  # Stop animation, keep current color
        """
        # Validate mode
        if mode not in self.VALID_MODES:
            raise LEDError(
                f"Invalid animation mode '{mode}'. Valid modes: {', '.join(self.VALID_MODES)}"
            )

        with self._lock:
            led_path = self._get_led_path(led_id)

            # Set timing if provided
            if timing is not None:
                # Find nearest valid timing value
                nearest_timing = min(self.VALID_TIMINGS, key=lambda x: abs(x - timing))
                self._write_sysfs_file(led_path / "timing", str(nearest_timing))

            # Set animation mode
            self._write_sysfs_file(led_path / "mode", mode)

    def get_animation_mode(self, led_id: int) -> Tuple[str, int]:
        """
        Get current animation mode and timing for a specific LED.

        Args:
            led_id: LED number (0, 1, 2, etc.)

        Returns:
            Tuple of (mode, timing_ms) where mode is one of "static", "blink",
            "fade", or "rainbow", and timing_ms is the current timing value in milliseconds

        Raises:
            LEDError: If LED ID is invalid or reading fails

        Example:
            mode, timing = led.get_animation_mode(0)
            print(f"LED 0 mode: {mode}, timing: {timing}ms")
        """
        led_path = self._get_led_path(led_id)

        try:
            mode = self._read_sysfs_file(led_path / "mode")
            timing = int(self._read_sysfs_file(led_path / "timing"))
            return (mode, timing)
        except ValueError as e:
            raise LEDError(f"Failed to parse animation mode/timing for LED {led_id}: {e}")

    def set_trigger(self, led_id: int, trigger: str) -> None:
        """
        Set LED trigger for a specific LED.

        Triggers provide system-driven LED patterns like heartbeat, breathing effects,
        and other kernel-based animations. Setting a trigger takes control of the LED
        away from manual color/mode control.

        Args:
            led_id: LED number (0, 1, 2, etc.)
            trigger: Trigger name (e.g., "heartbeat-rgb", "breathing-rgb", "rainbow-rgb",
                    "none", or any standard Linux LED trigger)

        Raises:
            LEDError: If LED ID is invalid or trigger is not available

        Examples:
            led.set_trigger(0, "heartbeat-rgb")  # System heartbeat pattern
            led.set_trigger(0, "breathing-rgb")  # Breathing effect
            led.set_trigger(0, "none")           # Disable trigger, return to manual control

        Note:
            Use get_available_triggers() to see all available triggers for a LED.
            Set trigger to "none" to return to manual color/animation control.
        """
        with self._lock:
            led_path = self._get_led_path(led_id)
            self._write_sysfs_file(led_path / "trigger", trigger)

    def get_trigger(self, led_id: int) -> str:
        """
        Get current active trigger for a specific LED.

        Args:
            led_id: LED number (0, 1, 2, etc.)

        Returns:
            Name of the currently active trigger, or "none" if no trigger is active

        Raises:
            LEDError: If LED ID is invalid or reading fails

        Example:
            trigger = led.get_trigger(0)
            print(f"Active trigger: {trigger}")
        """
        led_path = self._get_led_path(led_id)
        trigger_content = self._read_sysfs_file(led_path / "trigger")

        # Parse trigger string: "none [heartbeat-rgb] breathing-rgb ..."
        # Active trigger is enclosed in brackets
        for item in trigger_content.split():
            if item.startswith("[") and item.endswith("]"):
                return item.strip("[]")

        # If no brackets found, assume "none" is active
        return "none"

    def get_available_triggers(self, led_id: int) -> List[str]:
        """
        Get list of available triggers for a specific LED.

        Args:
            led_id: LED number (0, 1, 2, etc.)

        Returns:
            List of available trigger names

        Raises:
            LEDError: If LED ID is invalid or reading fails

        Example:
            triggers = led.get_available_triggers(0)
            print(f"Available triggers: {', '.join(triggers)}")
        """
        led_path = self._get_led_path(led_id)
        trigger_content = self._read_sysfs_file(led_path / "trigger")

        # Parse trigger string: "none [heartbeat-rgb] breathing-rgb ..."
        # Remove brackets from active trigger
        triggers = []
        for item in trigger_content.split():
            trigger_name = item.strip("[]")
            triggers.append(trigger_name)

        return triggers

    def set_brightness(self, led_id: int, brightness: int) -> None:
        """
        Set overall brightness for a specific LED.

        Args:
            led_id: LED number (0, 1, 2, etc.)
            brightness: Brightness value (0-255)

        Raises:
            LEDError: If LED ID is invalid or brightness is out of range
        """
        if not 0 <= brightness <= 255:
            raise LEDError(f"Brightness {brightness} out of range (0-255)")

        with self._lock:
            led_path = self._get_led_path(led_id)
            self._write_sysfs_file(led_path / "brightness", str(brightness))

    def get_brightness(self, led_id: int) -> int:
        """
        Get current brightness for a specific LED.

        Args:
            led_id: LED number (0, 1, 2, etc.)

        Returns:
            Current brightness value (0-255)

        Raises:
            LEDError: If LED ID is invalid or reading fails
        """
        led_path = self._get_led_path(led_id)

        try:
            return int(self._read_sysfs_file(led_path / "brightness"))
        except ValueError as e:
            raise LEDError(f"Failed to parse brightness for LED {led_id}: {e}")

    # Convenience methods for common operations

    def turn_off(self, led_id: int) -> None:
        """
        Turn off a specific LED.

        Args:
            led_id: LED number (0, 1, 2, etc.)
        """
        self.set_brightness(led_id, 0)

    def turn_off_all(self) -> None:
        """Turn off all available LEDs."""
        for led_id in self.available_leds:
            self.turn_off(led_id)

    def set_color_all(self, red: int, green: int, blue: int) -> None:
        """
        Set the same RGB color for all available LEDs.

        Args:
            red: Red component (0-255)
            green: Green component (0-255)
            blue: Blue component (0-255)
        """
        for led_id in self.available_leds:
            self.set_rgb_color(led_id, red, green, blue)

    def set_brightness_all(self, brightness: int) -> None:
        """
        Set the same brightness for all available LEDs.

        Args:
            brightness: Brightness value (0-255)
        """
        for led_id in self.available_leds:
            self.set_brightness(led_id, brightness)

    def blink_led(self, led_id: int, red: int, green: int, blue: int, timing: int = 500) -> None:
        """
        Set a LED to blink with specified color using kernel-based animation.

        This convenience method sets the RGB color and then enables blink mode.
        The blinking animation runs continuously in the kernel driver.

        Args:
            led_id: LED number (0, 1, 2, etc.)
            red: Red component (0-255)
            green: Green component (0-255)
            blue: Blue component (0-255)
            timing: Blink timing in milliseconds (default: 500)
                   Will be rounded to nearest valid value (100/200/500/1000)

        Raises:
            LEDError: If LED ID is invalid or values are out of range

        Example:
            led.blink_led(0, 255, 0, 0, 500)  # Blink red every 500ms
        """
        # Set the RGB color first
        self.set_rgb_color(led_id, red, green, blue)

        # Enable blink animation mode
        self.set_animation_mode(led_id, "blink", timing)

    def fade_led(self, led_id: int, red: int, green: int, blue: int, timing: int = 1000) -> None:
        """
        Set a LED to fade with specified color using kernel-based animation.

        This convenience method sets the RGB color and then enables fade mode.
        The fading animation runs continuously in the kernel driver.

        Args:
            led_id: LED number (0, 1, 2, etc.)
            red: Red component (0-255)
            green: Green component (0-255)
            blue: Blue component (0-255)
            timing: Fade timing in milliseconds (default: 1000)
                   Will be rounded to nearest valid value (100/200/500/1000)

        Raises:
            LEDError: If LED ID is invalid or values are out of range

        Example:
            led.fade_led(0, 0, 255, 0, 1000)  # Fade green with 1 second cycle
        """
        # Set the RGB color first
        self.set_rgb_color(led_id, red, green, blue)

        # Enable fade animation mode
        self.set_animation_mode(led_id, "fade", timing)

    def rainbow_led(self, led_id: int, timing: int = 1000) -> None:
        """
        Set a LED to rainbow cycle mode using kernel-based animation.

        Rainbow mode cycles through all colors continuously in the kernel driver.
        The RGB color settings are ignored in rainbow mode.

        Args:
            led_id: LED number (0, 1, 2, etc.)
            timing: Cycle timing in milliseconds (default: 1000)
                   Will be rounded to nearest valid value (100/200/500/1000)

        Raises:
            LEDError: If LED ID is invalid

        Example:
            led.rainbow_led(0, 1000)  # Rainbow cycle, 1 second per full cycle

        Note:
            Rainbow mode ignores the current RGB color settings and cycles through
            all colors automatically.
        """
        # Enable rainbow animation mode (RGB values are ignored in this mode)
        self.set_animation_mode(led_id, "rainbow", timing)

    def static_led(self, led_id: int, red: int, green: int, blue: int) -> None:
        """
        Set a LED to static color and stop any animation.

        Args:
            led_id: LED number (0, 1, 2, etc.)
            red: Red component (0-255)
            green: Green component (0-255)
            blue: Blue component (0-255)
        """
        self.set_rgb_color(led_id, red, green, blue)
        self.set_animation_mode(led_id, "static")

    # Legacy compatibility methods (matching old interface)

    def connect(self) -> bool:
        """
        Legacy compatibility method.

        Returns:
            bool: Always True (sysfs interface doesn't require connection)
        """
        return True

    def disconnect(self) -> None:
        """
        Legacy compatibility method.
        """
        pass

    def set_led_color(
        self, r: int, g: int, b: int, brightness: float = 0.5, delay: float = 0.0, led_id: int = 0
    ) -> bool:
        """
        Legacy compatibility method for setting LED color.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
            brightness: LED brightness (0.0-1.0)
            delay: Ignored (for compatibility)
            led_id: LED number (default: 0)

        Returns:
            bool: True if successful
        """
        try:
            # Convert brightness from 0.0-1.0 to 0-255
            brightness_int = int(brightness * 255)

            self.set_rgb_color(led_id, r, g, b)
            self.set_brightness(led_id, brightness_int)

            # Note: delay parameter is ignored in this static-only version

            return True
        except LEDError:
            return False

    def __enter__(self) -> "LED":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> Literal[False]:
        """Exit context manager and turn off all LEDs."""
        self.turn_off_all()
        return False


# Convenience function for quick LED access with sudo
def create_led_with_sudo() -> LED:
    """
    Create an LED instance with sudo enabled.

    Returns:
        LED instance configured to use sudo for write operations
    """
    return LED(use_sudo=True)


__all__ = ["LED", "LEDError", "create_led_with_sudo"]
