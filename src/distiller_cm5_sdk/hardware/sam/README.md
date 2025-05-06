# LED Module SDK Documentation

## Overview

The LED module provides an interface to interact with the RGB LED on the CM5 device.
It communicates with the underlying hardware driver by writing JSON commands
to the `/dev/pamir-uart` device file using a **fire and forget** approach.

**Important:** This SDK sends commands but does not track or wait for their completion on the hardware. Sequencing multiple commands requires manual timing (e.g., using `time.sleep()`) in the calling script.

## Prerequisites

- The driver responsible for creating `/dev/pamir-uart` must be loaded.
- The user running the script must have write permissions for `/dev/pamir-uart`.

## Installation

The LED module is part of the CM5 Linux SDK and can be imported from:

```python
# Adjust the import path based on your project structure
from distiller_cm5_sdk.hardware.sam.led import LED
```

## Class: LED

### Initialization

```python
led = LED()
```

Parameters:
- None

Raises:
- `RuntimeError`: If the device `/dev/pamir-uart` does not exist or is not writable.

### Connection Management

#### `connect() -> bool`

Placeholder method. Always returns `True`.

#### `disconnect() -> None`

Placeholder method. Does nothing.

### LED Control (Fire and Forget)

These methods generate JSON commands and write them to `/dev/pamir-uart`. They return immediately after writing the command successfully or raise an error if writing fails. They **do not** wait for the hardware to finish.

#### `set_led_color(r: int, g: int, b: int, brightness: float = 0.5, delay: float = 0.0) -> bool`

Sets the RGB LED to a specific color.

Parameters:
- `r`, `g`, `b`: Color components (0-255).
- `brightness`: LED brightness (0.0-1.0). Default: 0.5.
- `delay`: Duration this color should be shown (seconds). Default: 0.0.

Returns:
- `bool`: True if the command was written successfully, False otherwise.

Example:
```python
# Set LED to red for 1 second
led.set_led_color(255, 0, 0, delay=1.0)
# Script continues immediately; wait manually if needed:
time.sleep(1.0)
```

#### `set_led_sequence(colors: List[Dict[str, Union[int, float]]]) -> bool`

Sets a sequence of colors for the RGB LED.

Parameters:
- `colors`: List of color dictionaries (keys: `r`, `g`, `b`, `brightness`, `delay`).

Returns:
- `bool`: True if the command was written successfully, False otherwise.

Example:
```python
sequence = [
    {"r": 255, "g": 0, "b": 0, "brightness": 0.5, "delay": 0.5}, # Red 0.5s
    {"r": 0, "g": 255, "b": 0, "brightness": 0.5, "delay": 0.5}, # Green 0.5s
]
sequence_duration = 0.5 + 0.5
led.set_led_sequence(sequence)
# Script continues immediately; wait manually:
time.sleep(sequence_duration)
```

#### `blink_led(r: int, g: int, b: int, count: int = 3, on_time: float = 0.5, off_time: float = 0.5, brightness: float = 0.5) -> bool`

Blinks the RGB LED. (Convenience function calling `set_led_sequence`).

Parameters:
- `r`, `g`, `b`: Color components (0-255).
- `count`: Number of blinks. Default: 3.
- `on_time`, `off_time`: Blink timings (seconds). Default: 0.5.
- `brightness`: LED brightness (0.0-1.0). Default: 0.5.

Returns:
- `bool`: True if the command was written successfully, False otherwise.

Example:
```python
blink_duration = 3 * (0.5 + 0.5) # 3 * (on + off)
led.blink_led(0, 0, 255, count=3)
# Script continues immediately; wait manually:
time.sleep(blink_duration)
```

## Sequencing Commands

Since all control methods are "fire and forget", you must manually insert delays using `time.sleep()` in your script if you need to ensure one command finishes before the next begins. Calculate the duration based on the `delay`, `on_time`/`off_time`, or `duration` parameters you provide.

## Best Practices

1.  **Check Permissions**: Ensure `/dev/pamir-uart` exists and is writable before initializing `LED()`.
2.  **Manual Timing**: Use `time.sleep()` for sequencing commands based on their expected durations.
3.  **Cleanup on Exit**: Send a command to turn the LED off before your application exits.
   ```python
   # Turn off LED
   led.set_led_color(0, 0, 0, brightness=0, delay=0.1)
   time.sleep(0.1) # Brief pause for command write
   ```
4.  **Handle `RuntimeError`**: Catch potential `RuntimeError` during `LED()` initialization if the device is missing or inaccessible.

## Error Handling

The LED module may raise:
- `RuntimeError`: During `__init__` if `/dev/pamir-uart` is not found or not writable.
- `IOError` (caught internally): If writing to `/dev/pamir-uart` fails (methods return `False`).

Handle the `RuntimeError` during initialization:

```python
try:
    led = LED()
    # Use LED module
except RuntimeError as e:
    print(f"LED module initialization error: {e}")
    # Handle error (e.g., exit application)
finally:
    # Optional: Attempt to turn off LED if instance exists
    if 'led' in locals() and led is not None:
         try:
             led.set_led_color(0, 0, 0, brightness=0, delay=0.1)
         except Exception as cleanup_e:
             print(f"Error during LED cleanup: {cleanup_e}")
```

## Threading Considerations

This version of the SDK does minimal internal state management and does not use locks. If you intend to use a single `LED` instance from multiple threads concurrently, you might need to implement your own external locking mechanism around calls to the LED control methods to prevent interleaved writes to the device file, although the impact of interleaved writes depends on the driver's behavior.

## Complete Example (Fire and Forget)

```python
import time
import signal
import sys
# Adjust import path as needed
from distiller_cm5_sdk.hardware.sam.led import LED

led = None
try:
    # Initialize LED
    led = LED()
    print("LED module initialized successfully.")

    # Example: Blink green 3 times, requires manual wait
    print("Blinking green...")
    on_time = 0.3
    off_time = 0.2
    count = 3
    blink_duration = count * (on_time + off_time)
    led.blink_led(0, 255, 0, count=count, on_time=on_time, off_time=off_time)
    print(f"  - Blink command sent. Waiting {blink_duration:.1f}s...")
    time.sleep(blink_duration)
    print("  - Blink should be finished.")

    time.sleep(1)

    # Example: Fade to blue (Removed)
    # print("Fading to blue...")
    # fade_duration = 2.0
    # led.fade_led(0, 0, 255, steps=20, duration=fade_duration)
    # print(f"  - Fade command sent. Waiting {fade_duration:.1f}s...")
    # time.sleep(fade_duration)
    # print("  - Fade should be finished.")

except RuntimeError as e:
    print(f"Error initializing LED module: {e}")
    sys.exit(1)
except KeyboardInterrupt:
    print("\nExiting by user request...")
finally:
    # Cleanup: Attempt to turn off LED
    if led is not None:
        print("Turning off LED...")
        try:
            led.set_led_color(0, 0, 0, brightness=0, delay=0.1)
            time.sleep(0.1) # Short pause after sending off command
            print("LED off command sent.")
        except Exception as cleanup_e:
            print(f"Error turning off LED during cleanup: {cleanup_e}")

print("Script finished.")
``` 