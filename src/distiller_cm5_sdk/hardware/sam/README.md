# SAM Module SDK Documentation

## Overview

The SAM (Sensor and Actuator Module) provides an interface to interact with the hardware components on the CM5 device, specifically focusing on button input and RGB LED control. It communicates with the RP2040 microcontroller via UART.

## Prerequisites

- The UART2 interface must be enabled in the device's config.txt by adding:
  ```
  dtoverlay=uart2,pin_tx=4,pin_rx=5
  ```
- The device must be rebooted after making this change.
- The UART device `/dev/ttyAMA2` must be accessible.

## Installation

The SAM module is part of the CM5 Linux SDK and can be imported from:

```python
from simpleSDK.hardware.sam.sam import SAM, ButtonType
```

## Class: SAM

### Initialization

```python
sam = SAM(timeout=1.0)
```

Parameters:
- `timeout` (float, optional): Serial timeout in seconds. Default: 1.0

Raises:
- `RuntimeError`: If the UART device `/dev/ttyAMA2` does not exist

### Connection Management

#### `connect() -> bool`

Establishes the connection to the SAM module.

Returns:
- `bool`: True if connection successful, False otherwise

Example:
```python
sam = SAM()
if not sam.connect():
    print("Failed to connect to SAM module")
    # Handle connection failure
```

#### `disconnect() -> None`

Closes the connection to the SAM module and stops the background thread.

Example:
```python
# When done with SAM
sam.disconnect()
```

### Button Interaction

The module supports four button types, defined in the `ButtonType` enum:
- `ButtonType.UP`: Up button
- `ButtonType.DOWN`: Down button
- `ButtonType.SELECT`: Select button
- `ButtonType.SHUTDOWN`: Shutdown signal

#### `register_button_callback(button: ButtonType, callback: Callable) -> None`

Registers a callback function for a specific button.

Parameters:
- `button` (ButtonType): The button type to register for
- `callback` (Callable): Function to call when button is pressed

Example:
```python
def button_up_handler():
    print("UP button pressed!")
    # Perform actions when UP button is pressed

sam.register_button_callback(ButtonType.UP, button_up_handler)
```

#### `unregister_button_callback(button: ButtonType, callback: Callable) -> bool`

Removes a previously registered callback function for a specific button.

Parameters:
- `button` (ButtonType): The button type to unregister from
- `callback` (Callable): Function to remove from callbacks

Returns:
- `bool`: True if callback was removed, False if not found

Example:
```python
sam.unregister_button_callback(ButtonType.UP, button_up_handler)
```

### LED Control

The SAM module provides methods to control the RGB LED on the device.

#### `set_led_color(r: int, g: int, b: int, brightness: float = 0.5, delay: float = 0.0, wait_for_completion: bool = False, timeout: float = None) -> bool`

Sets the RGB LED to a specific color.

Parameters:
- `r` (int): Red component (0-255)
- `g` (int): Green component (0-255)
- `b` (int): Blue component (0-255)
- `brightness` (float, optional): LED brightness (0.0-1.0). Default: 0.5
- `delay` (float, optional): Delay before next color change (seconds). Default: 0.0
- `wait_for_completion` (bool, optional): Whether to wait for task completion. Default: False
- `timeout` (float, optional): Maximum time to wait if wait_for_completion is True. Default: None

Returns:
- `bool`: True if command was sent successfully, False otherwise

Example:
```python
# Set LED to red
sam.set_led_color(255, 0, 0)

# Set LED to blue with custom brightness and wait for completion
sam.set_led_color(0, 0, 255, brightness=0.7, wait_for_completion=True, timeout=2.0)
```

#### `set_led_sequence(colors: List[Dict[str, Union[int, float]]], wait_for_completion: bool = False, timeout: float = None) -> bool`

Sets a sequence of colors for the RGB LED.

Parameters:
- `colors` (List[Dict]): List of color dictionaries with keys:
  - `r`, `g`, `b`: RGB values (0-255)
  - `brightness`: LED brightness (0.0-1.0)
  - `delay`: Delay before next color (seconds)
- `wait_for_completion` (bool, optional): Whether to wait for task completion. Default: False
- `timeout` (float, optional): Maximum time to wait if wait_for_completion is True. Default: None

Returns:
- `bool`: True if command was sent successfully, False otherwise

Example:
```python
sequence = [
    {"r": 255, "g": 0, "b": 0, "brightness": 0.5, "delay": 0.5},     # Red
    {"r": 0, "g": 255, "b": 0, "brightness": 0.5, "delay": 0.5},     # Green
    {"r": 0, "g": 0, "b": 255, "brightness": 0.5, "delay": 0.5},     # Blue
]
sam.set_led_sequence(sequence, wait_for_completion=True, timeout=5.0)
```

#### `blink_led(r: int, g: int, b: int, count: int = 3, on_time: float = 0.5, off_time: float = 0.5, brightness: float = 0.5, wait_for_completion: bool = False, timeout: float = None) -> bool`

Blinks the RGB LED with the specified color.

Parameters:
- `r` (int): Red component (0-255)
- `g` (int): Green component (0-255)
- `b` (int): Blue component (0-255)
- `count` (int, optional): Number of blinks. Default: 3
- `on_time` (float, optional): Time LED is on for each blink (seconds). Default: 0.5
- `off_time` (float, optional): Time LED is off for each blink (seconds). Default: 0.5
- `brightness` (float, optional): LED brightness (0.0-1.0). Default: 0.5
- `wait_for_completion` (bool, optional): Whether to wait for task completion. Default: False
- `timeout` (float, optional): Maximum time to wait if wait_for_completion is True. Default: None

Returns:
- `bool`: True if command was sent successfully, False otherwise

Example:
```python
# Blink red LED 5 times
sam.blink_led(255, 0, 0, count=5, on_time=0.3, off_time=0.2)
```

#### `fade_led(r: int, g: int, b: int, steps: int = 10, duration: float = 1.0, final_brightness: float = 1.0, wait_for_completion: bool = False, timeout: float = None) -> bool`

Fades in the RGB LED to the specified color.

Parameters:
- `r` (int): Red component (0-255)
- `g` (int): Green component (0-255)
- `b` (int): Blue component (0-255)
- `steps` (int, optional): Number of brightness steps. Default: 10
- `duration` (float, optional): Total fade duration (seconds). Default: 1.0
- `final_brightness` (float, optional): Final brightness value (0.0-1.0). Default: 1.0
- `wait_for_completion` (bool, optional): Whether to wait for task completion. Default: False
- `timeout` (float, optional): Maximum time to wait if wait_for_completion is True. Default: None

Returns:
- `bool`: True if command was sent successfully, False otherwise

Example:
```python
# Fade to blue over 2 seconds
sam.fade_led(0, 0, 255, duration=2.0, final_brightness=0.8)
```

### Task Management

LED commands are processed as tasks by the SAM module, and only one task can run at a time. The SDK provides methods to manage these tasks.

#### `wait_for_led_task_completion(timeout: float = None) -> bool`

Waits for any ongoing LED task to complete.

Parameters:
- `timeout` (float, optional): Maximum time to wait in seconds. Default: None (wait indefinitely)

Returns:
- `bool`: True if task completed, False if timeout occurred

Example:
```python
# Wait for any running LED task to complete with a 5-second timeout
if not sam.wait_for_led_task_completion(timeout=5.0):
    print("Timeout waiting for LED task")
```

#### `is_led_task_running() -> bool`

Checks if an LED task is currently running.

Returns:
- `bool`: True if a task is running, False otherwise

Example:
```python
if sam.is_led_task_running():
    print("Cannot start new LED task while one is already running")
else:
    sam.set_led_color(0, 255, 0)  # Green
```

## Task Execution Model

The SAM module follows these rules for LED task execution:

1. Only one LED task can run at a time
2. New tasks will be rejected if another task is already running
3. Tasks can be waited on with an optional timeout
4. Tasks send a completion notification when finished

## Best Practices

1. **Check for Running Tasks**: Always check if a task is running before starting a new one:
```python
if not sam.is_led_task_running():
    sam.set_led_color(0, 255, 0)
```

2. **Wait for Task Completion**: For time-critical sequences, wait for tasks to complete:
```python
if sam.set_led_color(255, 0, 0, wait_for_completion=True, timeout=2.0):
    # LED is now red, continue with next task
    sam.set_led_color(0, 255, 0)
```

3. **Cleanup on Exit**: Always turn off the LED and disconnect before exiting:
```python
# Turn off LED
sam.set_led_color(0, 0, 0, brightness=0, wait_for_completion=True)
# Disconnect
sam.disconnect()
```

4. **Handle Potential Failures**: Always check return values to confirm operations succeeded:
```python
if not sam.connect():
    print("Failed to connect to SAM module")
    # Handle connection failure
```

## Error Handling

The SAM module may raise the following exceptions:
- `RuntimeError`: When the required UART device is not available
- `serial.SerialException`: When there are issues with the serial connection

Always handle these potential exceptions in your code:

```python
try:
    sam = SAM()
    sam.connect()
    # Use SAM module
except RuntimeError as e:
    print(f"SAM module initialization error: {e}")
    # Handle error
except serial.SerialException as e:
    print(f"Serial connection error: {e}")
    # Handle error
finally:
    # Cleanup code
    if 'sam' in locals():
        sam.disconnect()
```

## Threading Considerations

The SAM module spawns a background daemon thread to read from the serial port. Button callbacks are executed in this thread context. Keep callback functions short and thread-safe. For long-running operations, consider using a thread-safe queue or another thread.

## Complete Example

```python
import time
import signal
import sys
from simpleSDK.hardware.sam.sam import SAM, ButtonType

# Initialize SAM
sam = SAM()
if not sam.connect():
    print("Failed to connect to SAM module")
    sys.exit(1)

# Define button callbacks
def button_up_handler():
    print("UP button pressed!")
    if not sam.is_led_task_running():
        sam.set_led_color(0, 0, 255)  # Blue

def button_down_handler():
    print("DOWN button pressed!")
    if not sam.is_led_task_running():
        sam.set_led_color(0, 255, 0)  # Green

def button_select_handler():
    print("SELECT button pressed!")
    if not sam.is_led_task_running():
        sam.set_led_color(255, 0, 0)  # Red

# Register callbacks
sam.register_button_callback(ButtonType.UP, button_up_handler)
sam.register_button_callback(ButtonType.DOWN, button_down_handler)
sam.register_button_callback(ButtonType.SELECT, button_select_handler)

# Handle clean exit
def signal_handler(sig, frame):
    print("\nExiting...")
    if sam.is_led_task_running():
        sam.wait_for_led_task_completion(timeout=2.0)
    sam.set_led_color(0, 0, 0, brightness=0, wait_for_completion=True)
    sam.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Main loop
print("Waiting for button presses. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    # Cleanup
    if sam.is_led_task_running():
        sam.wait_for_led_task_completion(timeout=2.0)
    sam.set_led_color(0, 0, 0, brightness=0, wait_for_completion=True)
    sam.disconnect()
``` 