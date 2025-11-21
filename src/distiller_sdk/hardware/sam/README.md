# LED Module

## Overview

The LED module provides **comprehensive RGB LED control** for the CM5 device through the Linux sysfs
interface. It supports multiple LEDs with individual control of RGB colors, brightness settings,
kernel-based animation modes, and Linux LED triggers.

Key features:

- **RGB Color Control**: Full 0-255 color control per channel
- **Animation Modes**: Static, blink, fade, rainbow (kernel-looped for efficiency)
- **Timing Control**: 100ms, 200ms, 500ms, 1000ms intervals
- **LED Triggers**: Heartbeat, breathing, rainbow, and all standard Linux triggers
- **Multi-LED Support**: Independent control of multiple LEDs simultaneously
- **Brightness Control**: Global brightness with preserved RGB ratios

The module wraps the SAM driver's sysfs interface located at `/sys/class/leds/pamir:led*` and
provides both a high-level Python API and legacy compatibility with the previous interface.

## Prerequisites

- The SAM driver must be loaded and create LED devices at `/sys/class/leds/pamir:led*`
- **Root privileges required**: LED control requires write access to sysfs files
- Python 3.6+ with pathlib and subprocess support

### Permission Requirements

The LED sysfs interface requires root privileges for write operations. You have several options:

1. **Use sudo mode** (recommended): Initialize with `LED(use_sudo=True)`
2. **Run as root**: Use `sudo python your_script.py`
3. **Configure udev rules**: Set up permissions for your user (advanced)

## Installation

The LED module is part of the CM5 Linux SDK and can be imported from:

```python
from distiller_sdk.hardware.sam.led import LED, LEDError, create_led_with_sudo
```

## Quick Start

### Hardware Detection

```python
from distiller_sdk.hardware_status import HardwareStatus
from distiller_sdk.hardware.sam import LED

# Check LED availability before initialization
status = HardwareStatus()

if status.led_available:
    with LED(use_sudo=True) as led:
        # Set LED 0 to red
        led.set_rgb_color(0, 255, 0, 0)
else:
    print("LED controller not available")
    # Graceful degradation
```

### Basic Usage

```python
from distiller_sdk.hardware.sam.led import LED

# Use context manager for automatic cleanup
with LED(use_sudo=True) as led:
    # Get available LEDs
    available_leds = led.get_available_leds()
    print(f"Available LEDs: {available_leds}")

    # Set LED 0 to red (static)
    led.set_rgb_color(0, 255, 0, 0)

    # Set brightness
    led.set_brightness(0, 128)

    # Make it blink at 500ms intervals
    led.blink_led(0, 255, 0, 0, timing=500)

    # Use fade animation at 1000ms intervals
    led.fade_led(0, 0, 255, 0, timing=1000)

    # Rainbow animation
    led.rainbow_led(0, timing=1000)

    # Or use Linux LED triggers
    led.set_trigger(0, "heartbeat-rgb")
# Automatic cleanup - LEDs turned off
```

### Alternative: Running as Root

```python
# If running the entire script as root (sudo python script.py)
led = LED(use_sudo=False)  # No need for internal sudo
```

### Quick Setup Function

```python
from distiller_sdk.hardware.sam.led import create_led_with_sudo

# Convenient function that creates LED with sudo enabled
led = create_led_with_sudo()
```

## Interactive Demo

For a comprehensive demonstration of all LED features, run the interactive demo:

```bash
python led_interactive_demo.py
```

This interactive demo includes:

- LED discovery and initialization
- RGB color control (primary and secondary colors)
- Brightness control (multiple levels)
- Animation modes (blink, fade, rainbow)
- LED triggers (heartbeat, breathing, rainbow)
- Timing control demonstration
- Multi-LED control (different animations on each LED)
- Convenience methods and bulk operations
- Error handling and validation
- Sudo mode management

The demo waits for you to press Enter between each section, so you can see each feature in action.

## Class: LED

### Initialization

```python
led = LED(base_path="/sys/class/leds", use_sudo=False)
```

Parameters:

- `base_path`: Base path for LED sysfs interface (default: `/sys/class/leds`)
- `use_sudo`: Whether to use sudo for write operations (default: `False`)

Raises:

- `LEDError`: If the sysfs interface is not available or no compatible LEDs are found

### Permission Management

#### `set_sudo_mode(use_sudo: bool) -> None`

Enable or disable sudo mode for write operations.

```python
led = LED()  # Start without sudo
led.set_sudo_mode(True)  # Enable sudo mode
# Now all write operations will use sudo
```

### LED Discovery

#### `get_available_leds() -> List[int]`

Get list of available LED IDs.

Returns:

- List of LED numbers (e.g., `[0, 1, 2]` for led0, led1, led2)

Example:

```python
leds = led.get_available_leds()
print(f"Found LEDs: {leds}")  # Output: Found LEDs: [0, 1, 2]
```

### RGB Color Control

#### `set_rgb_color(led_id: int, red: int, green: int, blue: int) -> None`

Set RGB color for a specific LED.

Parameters:

- `led_id`: LED number (0, 1, 2, etc.)
- `red`: Red component (0-255)
- `green`: Green component (0-255)
- `blue`: Blue component (0-255)

Raises:

- `LEDError`: If LED ID is invalid or color values are out of range

#### `get_rgb_color(led_id: int) -> Tuple[int, int, int]`

Get current RGB color for a specific LED.

Returns:

- Tuple of (red, green, blue) values (0-255)

Example:

```python
# Set LED 0 to purple
led.set_rgb_color(0, 128, 0, 255)

# Read back the color
r, g, b = led.get_rgb_color(0)
print(f"Current color: R={r}, G={g}, B={b}")
```

### Animation Modes

#### `set_animation_mode(led_id: int, mode: str, timing: Optional[int] = None) -> None`

Set animation mode with kernel-based looping for efficient animation without userspace overhead.

Parameters:

- `led_id`: LED number (0, 1, 2, etc.)
- `mode`: Animation mode - one of `"static"`, `"blink"`, `"fade"`, `"rainbow"`
- `timing`: Animation timing in milliseconds (100, 200, 500, 1000). Optional for static mode.

Supported animation modes:

- **static**: No animation, static color
- **blink**: On/off blinking at specified timing
- **fade**: Smooth fade in/out at specified timing
- **rainbow**: Cycle through rainbow colors at specified timing

The animation is executed by the kernel driver, ensuring smooth operation without Python overhead.

Raises:

- `LEDError`: If LED ID is invalid, mode is unsupported, or timing is invalid

Example:

```python
# Set LED 0 to blink at 500ms intervals
led.set_animation_mode(0, "blink", timing=500)

# Set LED 1 to fade at 1000ms intervals
led.set_animation_mode(1, "fade", timing=1000)

# Set LED 2 to rainbow cycle at 200ms intervals (fast)
led.set_animation_mode(2, "rainbow", timing=200)

# Return LED 0 to static mode
led.set_animation_mode(0, "static")
```

#### `get_animation_mode(led_id: int) -> Tuple[str, int]`

Get current animation mode and timing for a specific LED.

Returns:

- Tuple of (mode, timing) where mode is the animation mode string and timing is in milliseconds

Example:

```python
mode, timing = led.get_animation_mode(0)
print(f"LED 0: mode={mode}, timing={timing}ms")
# Output: LED 0: mode=blink, timing=500ms
```

### LED Triggers

LED triggers allow LEDs to be controlled by kernel events and patterns. The module supports both
custom RGB triggers (heartbeat-rgb, breathing-rgb, rainbow-rgb) and all standard Linux LED triggers.

#### `set_trigger(led_id: int, trigger: str) -> None`

Set Linux LED trigger for kernel-based LED control patterns.

Parameters:

- `led_id`: LED number (0, 1, 2, etc.)
- `trigger`: Trigger name (e.g., "none", "heartbeat-rgb", "breathing-rgb", "rainbow-rgb")

Custom RGB triggers provided by the SAM driver:

- **none**: No trigger (manual control)
- **heartbeat-rgb**: Heartbeat pattern with RGB color
- **breathing-rgb**: Smooth breathing pattern with RGB color
- **rainbow-rgb**: Rainbow color cycling pattern

Standard Linux triggers (if available in kernel):

- **heartbeat**: Standard heartbeat pattern
- **timer**: Configurable timer-based blinking
- **oneshot**: Single pulse
- **default-on**: Always on
- And more depending on kernel configuration

Raises:

- `LEDError`: If LED ID is invalid or trigger is not available

Example:

```python
# Set heartbeat trigger on LED 0
led.set_trigger(0, "heartbeat-rgb")

# Set breathing pattern on LED 1
led.set_trigger(1, "breathing-rgb")

# Set rainbow pattern on LED 2
led.set_trigger(2, "rainbow-rgb")

# Disable triggers and return to manual control
led.set_trigger(0, "none")
```

#### `get_trigger(led_id: int) -> str`

Get currently active trigger for a specific LED.

Returns:

- Trigger name string (e.g., "none", "heartbeat-rgb")

Example:

```python
trigger = led.get_trigger(0)
print(f"LED 0 trigger: {trigger}")
# Output: LED 0 trigger: heartbeat-rgb
```

#### `get_available_triggers(led_id: int) -> List[str]`

Get list of available triggers for a specific LED.

Returns:

- List of trigger names supported by the kernel and driver

Example:

```python
triggers = led.get_available_triggers(0)
print(f"Available triggers: {triggers}")
# Output: Available triggers: ['none', 'heartbeat-rgb', 'breathing-rgb', 'rainbow-rgb', 'heartbeat', 'timer', ...]
```

### Brightness Control

#### `set_brightness(led_id: int, brightness: int) -> None`

Set overall brightness for a specific LED (preserves RGB ratios).

Parameters:

- `led_id`: LED number (0, 1, 2, etc.)
- `brightness`: Brightness value (0-255)

#### `get_brightness(led_id: int) -> int`

Get current brightness for a specific LED.

Example:

```python
# Set LED to half brightness
led.set_brightness(0, 128)

# Set multiple LEDs to different brightness levels
led.set_brightness(0, 255)  # Full brightness
led.set_brightness(1, 128)  # Half brightness
led.set_brightness(2, 64)   # Quarter brightness
```

## Convenience Methods

### Individual LED Control

#### `static_led(led_id: int, red: int, green: int, blue: int) -> None`

Set LED to static color. (Equivalent to `set_rgb_color()`)

#### `blink_led(led_id: int, red: int, green: int, blue: int, timing: int = 500) -> None`

Set LED to blink animation with specified color and timing.

Parameters:

- `led_id`: LED number
- `red`, `green`, `blue`: RGB color components (0-255)
- `timing`: Blink interval in milliseconds (100, 200, 500, 1000)

Example:

```python
# Blink red at 500ms intervals
led.blink_led(0, 255, 0, 0, timing=500)

# Blink green at 200ms intervals (fast)
led.blink_led(1, 0, 255, 0, timing=200)
```

#### `fade_led(led_id: int, red: int, green: int, blue: int, timing: int = 1000) -> None`

Set LED to fade animation with specified color and timing.

Parameters:

- `led_id`: LED number
- `red`, `green`, `blue`: RGB color components (0-255)
- `timing`: Fade interval in milliseconds (100, 200, 500, 1000)

Example:

```python
# Fade blue at 1000ms intervals
led.fade_led(0, 0, 0, 255, timing=1000)

# Fade purple at 500ms intervals
led.fade_led(1, 128, 0, 255, timing=500)
```

#### `rainbow_led(led_id: int, timing: int = 1000) -> None`

Set LED to rainbow animation cycling through colors.

Parameters:

- `led_id`: LED number
- `timing`: Color cycle interval in milliseconds (100, 200, 500, 1000)

Example:

```python
# Rainbow at normal speed (1000ms)
led.rainbow_led(0, timing=1000)

# Rainbow at fast speed (200ms)
led.rainbow_led(1, timing=200)
```

#### `turn_off(led_id: int) -> None`

Turn off a specific LED.

### Bulk Operations

#### `set_color_all(red: int, green: int, blue: int) -> None`

Set the same RGB color for all available LEDs.

#### `set_brightness_all(brightness: int) -> None`

Set the same brightness for all available LEDs.

#### `turn_off_all() -> None`

Turn off all available LEDs.

Example:

```python
# Static color control
led.static_led(0, 255, 0, 0)          # Static red on LED 0
led.set_rgb_color(1, 0, 255, 0)       # Direct green on LED 1
led.set_rgb_color(2, 0, 0, 255)       # Direct blue on LED 2

# Animation convenience methods
led.blink_led(0, 255, 0, 0, timing=500)    # Blink red at 500ms
led.fade_led(1, 0, 255, 0, timing=1000)    # Fade green at 1000ms
led.rainbow_led(2, timing=200)             # Rainbow at 200ms (fast)

# Bulk operations
led.set_color_all(255, 255, 255)      # All LEDs white
led.set_brightness_all(100)           # All LEDs dimmed
led.turn_off_all()                    # Turn off everything
```

## Legacy Compatibility

The module provides backward compatibility with the previous interface:

#### `connect() -> bool`

Legacy compatibility method (always returns True).

#### `disconnect() -> None`

Legacy compatibility method (no operation).

#### `set_led_color(r: int, g: int, b: int, brightness: float = 0.5, delay: float = 0.0, led_id: int = 0) -> bool`

Legacy method for setting LED color with 0.0-1.0 brightness scale.

Example:

```python
# Legacy usage (still supported)
result = led.set_led_color(255, 128, 0, brightness=0.7, led_id=0)
```

## Error Handling

The LED module uses custom `LEDError` exceptions for all LED-related errors:

```python
from distiller_sdk.hardware.sam.led import LED, LEDError

try:
    with LED(use_sudo=True) as led:
        led.set_rgb_color(0, 255, 0, 0)
        led.blink_led(0, 255, 0, 0, timing=500)
except LEDError as e:
    print(f"LED error: {e}")
    # Handle LED-specific errors (hardware not found, invalid values, etc.)
except PermissionError:
    print("Permission denied - try using LED(use_sudo=True)")
    # Handle permission issues
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
# Automatic cleanup via context manager
```

### Hardware Detection with Error Handling

```python
from distiller_sdk.hardware_status import HardwareStatus
from distiller_sdk.hardware.sam import LED, LEDError

# Check availability before initialization
status = HardwareStatus()

if not status.led_available:
    print("LED controller not available")
    # Graceful degradation
else:
    try:
        with LED(use_sudo=True) as led:
            led.set_rgb_color(0, 255, 0, 0)
    except LEDError as e:
        print(f"LED operation failed: {e}")
        # Handle LED errors
```

Common error scenarios:

- **Initialization**: No LEDs found, sysfs interface unavailable
- **Invalid LED ID**: Attempting to control non-existent LED
- **Invalid values**: RGB values outside 0-255 range, brightness outside 0-255 range
- **Invalid modes**: Unsupported animation modes (use: static, blink, fade, rainbow)
- **Invalid timing**: Animation timing not in [100, 200, 500, 1000] milliseconds
- **Invalid triggers**: Trigger not available in kernel (check with `get_available_triggers()`)
- **Permission errors**: Insufficient permissions to write to sysfs files

## Context Manager Support

The LED class supports context managers for automatic resource cleanup:

### `__enter__()`

Enter context manager.

- Returns: LED instance for context manager usage
- Enables automatic resource cleanup

### `__exit__(exc_type, exc_val, exc_tb)`

Exit context manager and automatically cleanup resources.

- Parameters:
  - `exc_type`: Exception type (if any)
  - `exc_val`: Exception value (if any)
  - `exc_tb`: Exception traceback (if any)
- Returns: False (does not suppress exceptions)
- Automatically calls `turn_off_all()` to turn off all LEDs

Example:

```python
with LED(use_sudo=True) as led:
    led.set_rgb_color(0, 255, 0, 0)
    led.blink_led(1, 0, 255, 0, timing=500)
# LEDs automatically turned off on exit
```

## Thread Safety

All LED module operations are thread-safe. You can safely control LEDs from multiple threads:

```python
import threading
from distiller_sdk.hardware.sam import LED

with LED(use_sudo=True) as led:
    def led_task_1():
        """Control LED 0 in background thread"""
        led.blink_led(0, 255, 0, 0, timing=500)

    def led_task_2():
        """Control LED 1 in background thread"""
        led.fade_led(1, 0, 255, 0, timing=1000)

    # Both operations are thread-safe
    t1 = threading.Thread(target=led_task_1)
    t2 = threading.Thread(target=led_task_2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
```

## Constants and Validation

### Animation Modes

Supported animation modes:

- `STATIC = "static"` - No animation
- `BLINK = "blink"` - On/off blinking
- `FADE = "fade"` - Smooth fade in/out
- `RAINBOW = "rainbow"` - Rainbow color cycling

### LED Triggers

Custom RGB triggers provided by SAM driver:

- `heartbeat-rgb` - Heartbeat pattern with RGB color
- `breathing-rgb` - Smooth breathing pattern with RGB color
- `rainbow-rgb` - Rainbow color cycling pattern
- `none` - No trigger (manual control)

Plus all standard Linux LED triggers available in the kernel.

### Timing Constraints

Animation timing values (milliseconds):

- `100` - Very fast animation
- `200` - Fast animation
- `500` - Normal animation (default for blink)
- `1000` - Slow animation (default for fade/rainbow)

### Value Ranges

- RGB components: 0-255
- Brightness: 0-255
- LED IDs: Must be in available LEDs list
- Animation timing: 100, 200, 500, 1000 milliseconds

## Multi-LED Support

The module supports multiple independent LEDs with different animations running simultaneously:

```python
# Control different LEDs independently with static colors
led.set_rgb_color(0, 255, 0, 0)      # LED 0: Static red
led.set_rgb_color(1, 0, 255, 0)      # LED 1: Static green
led.set_rgb_color(2, 0, 0, 255)      # LED 2: Static blue

# Different animation modes on each LED
led.blink_led(0, 255, 0, 0, timing=500)     # LED 0: Blinking red at 500ms
led.fade_led(1, 0, 255, 0, timing=1000)     # LED 1: Fading green at 1000ms
led.rainbow_led(2, timing=200)              # LED 2: Fast rainbow at 200ms

# Different triggers on each LED
led.set_trigger(0, "heartbeat-rgb")   # LED 0: Heartbeat pattern
led.set_trigger(1, "breathing-rgb")   # LED 1: Breathing pattern
led.set_trigger(2, "rainbow-rgb")     # LED 2: Rainbow pattern

# Mix animations and triggers
led.blink_led(0, 255, 0, 0, timing=500)     # LED 0: Blink animation
led.set_trigger(1, "breathing-rgb")         # LED 1: Breathing trigger
led.static_led(2, 128, 128, 255)            # LED 2: Static color
```

## Timing Control

Animation timing can be controlled independently for each LED:

```python
# Same animation, different speeds
led.blink_led(0, 255, 0, 0, timing=100)    # Very fast blink
led.blink_led(1, 255, 0, 0, timing=200)    # Fast blink
led.blink_led(2, 255, 0, 0, timing=500)    # Normal blink

# Change timing dynamically
led.blink_led(0, 0, 255, 0, timing=500)    # Start at 500ms
import time
time.sleep(3)
led.blink_led(0, 0, 255, 0, timing=200)    # Speed up to 200ms

# Get current timing
mode, timing = led.get_animation_mode(0)
print(f"Current timing: {timing}ms")

# Supported timing values
TIMINGS = [100, 200, 500, 1000]  # milliseconds
for timing in TIMINGS:
    led.fade_led(0, 128, 0, 255, timing=timing)
    time.sleep(3)
```

## Complete Example

```python
import time
from distiller_sdk.hardware.sam.led import LED, LEDError

try:
    # Use context manager for automatic cleanup
    with LED(use_sudo=True) as led:
        print(f"Available LEDs: {led.get_available_leds()}")

        # Demo RGB color control
        print("RGB Color Demo...")
        colors = [
            (255, 0, 0, "Red"),
            (0, 255, 0, "Green"),
            (0, 0, 255, "Blue"),
            (255, 255, 0, "Yellow"),
            (255, 0, 255, "Magenta"),
            (0, 255, 255, "Cyan"),
        ]

        for r, g, b, name in colors:
            print(f"Setting LED 0 to {name}")
            led.set_rgb_color(0, r, g, b)
            led.set_brightness(0, 200)
            time.sleep(1)

        # Demo animation modes
        print("\nAnimation Demo...")
        print("Blinking red at 500ms...")
        led.blink_led(0, 255, 0, 0, timing=500)
        time.sleep(3)

        print("Fading blue at 1000ms...")
        led.fade_led(0, 0, 0, 255, timing=1000)
        time.sleep(4)

        print("Rainbow cycle at 200ms (fast)...")
        led.rainbow_led(0, timing=200)
        time.sleep(4)

        # Demo triggers
        print("\nTrigger Demo...")
        print("Heartbeat pattern...")
        led.set_trigger(0, "heartbeat-rgb")
        time.sleep(3)

        print("Breathing pattern...")
        led.set_trigger(1, "breathing-rgb")
        time.sleep(3)

        print("Rainbow trigger...")
        led.set_trigger(2, "rainbow-rgb")
        time.sleep(3)

        # Demo timing control
        print("\nTiming Control Demo...")
        for timing in [100, 200, 500, 1000]:
            print(f"Blink at {timing}ms...")
            led.blink_led(0, 0, 255, 0, timing=timing)
            time.sleep(2)

        # Demo multi-LED with different animations
        print("\nMulti-LED Demo...")
        led.blink_led(0, 255, 0, 0, timing=500)     # LED 0: Blink red
        led.fade_led(1, 0, 255, 0, timing=1000)     # LED 1: Fade green
        led.rainbow_led(2, timing=200)              # LED 2: Rainbow
        time.sleep(5)

        # Cleanup (manual cleanup not required with context manager)
        led.set_trigger(0, "none")
        led.set_trigger(1, "none")
        led.set_trigger(2, "none")

        print("\nDemo complete!")
    # Automatic cleanup - all LEDs turned off

except LEDError as e:
    print(f"LED Error: {e}")
    print("Ensure the SAM driver is loaded and LED sysfs interface is available")
except KeyboardInterrupt:
    print("Demo interrupted")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Troubleshooting

### Driver Not Loaded

```
LEDError: LED sysfs interface not found at /sys/class/leds
```

- Ensure the SAM driver is loaded: `lsmod | grep pamir`
- Check for LED devices: `ls /sys/class/leds/pamir:led*`

### No LEDs Found

```
LEDError: No compatible LEDs found (pamir:led* pattern)
```

- Verify LED devices exist: `ls /sys/class/leds/`
- Check device naming matches `pamir:led*` pattern

### Permission Denied

```
LEDError: Permission denied writing to /sys/class/leds/pamir:led0/red. Try running with sudo or initialize LED(use_sudo=True).
```

**Solutions:**

- Use sudo mode: `led = LED(use_sudo=True)`
- Run entire script with sudo: `sudo python script.py`
- Set up udev rules for user access (advanced)

**Testing your setup:**

```python
# Test if you need sudo
try:
    led = LED(use_sudo=False)
    led.set_rgb_color(0, 255, 0, 0)  # Will fail if permissions needed
except LEDError as e:
    if "Permission denied" in str(e):
        print("Need sudo - reinitializing with sudo mode")
        led = LED(use_sudo=True)
```

### Invalid LED ID

```
LEDError: LED 5 not available. Available LEDs: [0, 1, 2]
```

- Use `get_available_leds()` to check available LED IDs
- Ensure LED ID exists before attempting control

## Performance Notes

- sysfs operations are fast but not real-time
- Multiple LED operations are independent and can be parallelized
- Animation timing is handled by the kernel driver, not userspace
- Reading sysfs values involves file I/O overhead
- For high-frequency updates, consider grouping operations
