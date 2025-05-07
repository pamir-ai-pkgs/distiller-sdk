import threading
import json
import time
import os
import sys
from enum import Enum
from typing import Callable, Dict, Optional, Union, List, Tuple


class LED:
    """
    SDK interface for the RGB LED controlled via the RP2040 microcontroller.
    Provides functionality to control the RGB LED by writing JSON commands
    to /dev/pamir-uart. This SDK uses a 'fire and forget' approach;
    it does not track command completion.
    """

    def __init__(self):
        """
        Initialize the LED module interface.

        Raises:
            RuntimeError: If the device /dev/pamir-uart does not exist
                          or is not writable.
        """
        self._device_path = "/dev/pamir-uart"

        # Check if the required device exists and is writable
        if not os.path.exists(self._device_path):
            error_msg = (
                f"ERROR: {self._device_path} does not exist.\n"
                "Please ensure the necessary driver is loaded and the device is present."
            )
            print(error_msg, file=sys.stderr)
            raise RuntimeError(error_msg)
        if not os.access(self._device_path, os.W_OK):
             error_msg = (
                f"ERROR: {self._device_path} is not writable.\n"
                "Please check permissions."
            )
             print(error_msg, file=sys.stderr)
             raise RuntimeError(error_msg)

    def connect(self) -> bool:
        """
        Placeholder for connection logic. Currently does nothing as communication
        is done by direct writes to the device file.

        Returns:
            bool: Always True.
        """
        # Connection is implicit with file writes, check done in __init__
        return True

    def disconnect(self) -> None:
        """
        Placeholder for disconnection logic. Currently does nothing.
        """
        # No persistent connection to close
        pass

    def set_led_color(self, r: int, g: int, b: int, brightness: float = 0.5, delay: float = 0.0) -> bool:
        """
        Set the RGB LED color (fire and forget).

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
            brightness: LED brightness (0.0-1.0)
            delay: Duration this color should be shown (seconds).

        Returns:
            bool: True if command was written successfully, False otherwise.
        """
        return self.set_led_sequence(
            [{
                "r": r,
                "g": g,
                "b": b,
                "brightness": float(brightness),
                "delay": float(delay)
            }]
        )

    def set_led_sequence(self, colors: List[Dict[str, Union[int, float]]]) -> bool:
        """
        Set a sequence of colors for the RGB LED by writing a JSON command
        to /dev/pamir-uart (fire and forget).

        Args:
            colors: List of color dictionaries with keys:
                   r, g, b: RGB values (0-255)
                   brightness: LED brightness (0.0-1.0)
                   delay: Duration for this color step (seconds)

        Returns:
            bool: True if the command was written successfully, False otherwise.
                  Note: True only indicates the command was sent, not that
                  the hardware executed it successfully or finished.
        """
        # TODO: This is fire-and-forget. We don't know when the hardware
        #       actually finishes executing the sequence. Need a feedback
        #       mechanism from the driver/hardware for proper completion tracking.

        # Prepare the command
        sequence = {}
        for i, color in enumerate(colors):
            sequence[str(i)] = [
                color.get("r", 0),
                color.get("g", 0),
                color.get("b", 0),
                float(color.get("brightness", 0.5)),
                float(color.get("delay", 0.0))
            ]

        command = {
            "Function": "NeoPixel",
            "colors": sequence
        }
        # Ensure command ends with a newline for the driver
        cmd_string = "\n" + json.dumps(command) + "\n"
        print(f"Writing command: {cmd_string}")
        # Write the command to the device file
        try:
            with open(self._device_path, 'w') as f:
                f.write(cmd_string)
                f.flush() # Ensure it's written immediately
            return True # Command sent successfully
        except IOError as e:
            print(f"Error writing to {self._device_path}: {e}")
            return False
        except Exception as e: # Catch other potential errors
             print(f"Unexpected error sending LED command: {e}")
             return False


    def blink_led(self, r: int, g: int, b: int, count: int = 3,
                 on_time: float = 0.5, off_time: float = 0.5,
                 brightness: float = 0.5) -> bool:
        """
        Blink the RGB LED (fire and forget).

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
            count: Number of blinks
            on_time: Time LED is on for each blink (seconds)
            off_time: Time LED is off for each blink (seconds)
            brightness: LED brightness (0.0-1.0)

        Returns:
            bool: True if command was sent successfully, False otherwise.
        """
        sequence = []
        for _ in range(count):
            # On state
            sequence.append({
                "r": r,
                "g": g,
                "b": b,
                "brightness": brightness,
                "delay": on_time
            })
            # Off state
            sequence.append({
                "r": 0,
                "g": 0,
                "b": 0,
                "brightness": 0.0,
                "delay": off_time
            })

        return self.set_led_sequence(sequence)

