# Camera Module for CM5 SDK

## Overview

The `camera.py` module provides a comprehensive interface for interacting with Raspberry Pi cameras
in the CM5 SDK. It uses the modern rpicam-apps stack introduced in Raspberry Pi OS Bookworm,
providing reliable camera operations on Raspberry Pi hardware.

## Architecture

The module is built around the `Camera` class, which uses rpicam-apps (modern CLI tools for
Raspberry Pi OS Bookworm+) for all camera operations.

## Key Components

### CameraError Class

- Custom exception class for camera-related errors
- Used to provide descriptive error messages specific to camera operations

### Camera Class

Primary class that provides all camera functionality:

#### Initialization Parameters

- `resolution`: Tuple of width and height (default: 640x480)
- `framerate`: Frames per second for video capture (default: 30)
- `rotation`: Camera rotation in degrees (0, 90, 180, or 270) (default: 0)
- `format`: Output format ('bgr', 'rgb', 'gray') (default: 'bgr')
- `auto_check_config`: Whether to automatically check system configuration (default: True)

#### Internal Attributes

- `_camera`: OpenCV VideoCapture object (for settings adjustment)
- `_is_streaming`: Boolean tracking if stream is active
- `_stream_thread`: Thread object for asynchronous streaming
- `_stop_event`: Threading event for signaling stream termination
- `_frame`: Current frame buffer
- `_frame_lock`: Thread lock for synchronized frame access

#### Methods

##### Configuration and Setup

- `check_system_config()`: Verifies camera configuration in system
  - Checks for rpicam-still availability
  - Verifies camera dtoverlay configuration in config.txt
  - Returns True if configuration is valid, raises CameraError otherwise

- `_init_camera()`: Initializes camera hardware
  - Tests rpicam-still availability
  - Verifies camera can capture images

##### Core Functionality

- `start_stream(callback=None)`: Starts streaming video
  - Creates a background thread capturing frames continuously
  - Optionally accepts a callback function executed for each frame
  - Uses rpicam-still for frame capture

- `stop_stream()`: Stops active streaming
  - Signals thread termination and cleans up resources

- `get_frame()`: Gets latest frame from camera
  - Returns frame from active stream or captures a new frame
  - Uses rpicam-still for capture
  - Applies format conversion according to configured format
  - Returns numpy.ndarray representing the image

- `capture_image(filepath=None)`: Captures still image
  - Captures image using rpicam-still
  - Saves to filepath if provided
  - Returns captured image as numpy.ndarray

##### Camera Settings

- `adjust_setting(setting, value)`: Adjusts camera settings
  - Limited control through OpenCV (may not affect rpicam capture)
  - Returns True if successful, raises CameraError otherwise

- `get_setting(setting)`: Gets current value of a setting
  - Retrieves setting value from OpenCV (may not reflect actual rpicam settings)
  - Returns current value of the setting
  - Raises CameraError if setting is unknown

- `get_available_settings()`: Lists available camera settings
  - Returns list of setting names that can be adjusted
  - Note: Settings have limited effect with rpicam-still

- `close()`: Releases camera resources (automatically called by context manager)
  - Stops active stream
  - Releases camera objects

- `__enter__()`: Enter context manager
  - Returns self for context manager usage
  - Enables automatic resource cleanup

- `__exit__(exc_type, exc_val, exc_tb)`: Exit context manager
  - Automatically calls `close()` to release resources
  - Ensures cleanup even if exceptions occur
  - Returns False (does not suppress exceptions)

## Implementation Details

### rpicam-apps Backend

The module uses rpicam-apps (modern CLI tools) for all camera operations:

- Uses rpicam-still (replacement for libcamera-still)
- Subprocess-based capture with temporary files
- Reliable and well-tested on Raspberry Pi OS Bookworm+

### Threading Model

The streaming functionality uses Python's threading to provide non-blocking camera access:

1. `start_stream()` creates a daemon thread
2. Thread continuously captures frames in background
3. Thread-safe access to current frame using locks
4. Stream can be cleanly terminated with `stop_stream()`

### Image Processing

Image format conversion happens after capture:

- BGR is the default format (native to OpenCV)
- RGB conversion uses cv2.COLOR_BGR2RGB
- Grayscale conversion uses cv2.COLOR_BGR2GRAY

### Error Handling

The module uses custom CameraError exceptions with descriptive messages for:

- Configuration errors
- Initialization failures
- Capture failures
- Setting adjustment errors

## Usage Examples

### Basic Usage

```python
from distiller_sdk.hardware.camera import Camera

# Use context manager for automatic cleanup
with Camera() as camera:
    # Capture an image and save it
    image = camera.capture_image("image.jpg")
# Automatic cleanup
```

### Hardware Detection

```python
from distiller_sdk.hardware_status import HardwareStatus
from distiller_sdk.hardware.camera import Camera

# Check camera availability before initialization
status = HardwareStatus()

if status.camera_available:
    with Camera() as camera:
        image = camera.capture_image("image.jpg")
else:
    print("Camera not available")
    # Graceful degradation
```

### Custom Configuration

```python
from distiller_sdk.hardware.camera import Camera

# Use context manager with custom settings
with Camera(
    resolution=(1920, 1080),
    framerate=30,
    rotation=180,
    format='rgb'
) as camera:
    # Use the camera
    image = camera.capture_image("high_res.jpg")
# Automatic cleanup
```

### Streaming with Callback

```python
from distiller_sdk.hardware.camera import Camera
import cv2
import time

def process_frame(frame):
    # Process each frame
    # e.g., detect objects, apply filters
    cv2.imshow("Stream", frame)
    cv2.waitKey(1)

with Camera(resolution=(1280, 720)) as camera:
    # Start streaming with callback
    camera.start_stream(callback=process_frame)

    # Do other work while streaming continues
    time.sleep(10)

    # Stop streaming
    camera.stop_stream()
# Automatic cleanup
```

### Adjusting Camera Settings

```python
from distiller_sdk.hardware.camera import Camera

with Camera() as camera:
    # Get available settings
    settings = camera.get_available_settings()
    print(f"Available settings: {settings}")

    # Get current brightness
    brightness = camera.get_setting('brightness')
    print(f"Current brightness: {brightness}")

    # Adjust brightness (limited effect with rpicam)
    camera.adjust_setting('brightness', 70)
# Automatic cleanup
```

## Exception Handling

The Camera module uses specific exceptions for better error handling:

```python
from distiller_sdk.hardware.camera import Camera, CameraError

try:
    with Camera() as camera:
        image = camera.capture_image("photo.jpg")
        camera.adjust_setting('brightness', 70)
except CameraError as e:
    print(f"Camera error: {e}")
    # Handle camera-specific errors (device not found, capture failure, etc.)
except PermissionError:
    print("Permission denied - add user to 'video' group")
    # Handle permission issues
except FileNotFoundError as e:
    print(f"File or device not found: {e}")
    # Handle missing devices or files
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
# Automatic cleanup via context manager
```

### Common CameraError Scenarios

```python
from distiller_sdk.hardware_status import HardwareStatus
from distiller_sdk.hardware.camera import Camera, CameraError

# Check availability before initialization
status = HardwareStatus()

if not status.camera_available:
    print("Camera hardware not available")
    # Graceful degradation
else:
    try:
        with Camera(resolution=(1920, 1080)) as camera:
            image = camera.capture_image("photo.jpg")
    except CameraError as e:
        print(f"Camera operation failed: {e}")
        # Handle camera errors
```

## Thread Safety

All Camera module operations are thread-safe. The streaming functionality uses thread locks to protect shared resources:

```python
import threading
from distiller_sdk.hardware.camera import Camera

with Camera() as camera:
    def capture_task():
        """Capture images in background thread"""
        for i in range(10):
            camera.capture_image(f"photo_{i}.jpg")

    def stream_task():
        """Stream video in background thread"""
        def process_frame(frame):
            # Process frame
            pass

        camera.start_stream(callback=process_frame)

    # Both operations are thread-safe
    t1 = threading.Thread(target=capture_task)
    t2 = threading.Thread(target=stream_task)
    t1.start()
    t2.start()
    t1.join()
    camera.stop_stream()
    t2.join()
```

## System Requirements

### Hardware

- Raspberry Pi computer (tested on CM5)
- Compatible camera module (e.g., Camera Module V2/V3, High Quality Camera, AI Camera)
- Proper camera connection to CSI port

### Software

- Raspberry Pi OS Bookworm or later (recommended)
- rpicam-apps package (installed by default on Bookworm)
- OpenCV Python library (opencv-Python)
- Properly configured `/boot/firmware/config.txt` with camera dtoverlay

### Camera Configuration

The camera requires proper configuration in the Raspberry Pi's `config.txt`, which may include:

- `dtoverlay=ov5647` (Camera Module V1)
- `dtoverlay=imx219` (Camera Module V2)
- `dtoverlay=imx477` (High Quality Camera)
- `dtoverlay=imx500` (AI Camera)
- Other camera-specific overlays

## Migration from libcamera-apps

If you're migrating from the older libcamera-apps:

1. **Command Changes**: libcamera-still → rpicam-still
2. **Package Changes**: libcamera-apps → rpicam-apps
3. **API Compatibility**: All command-line parameters remain the same

## Limitations and Known Issues

### Rotations with Transpose

Some rotation values (90, 270) may require transpose operations which may show errors.

### Camera Settings

- rpicam backend has limited setting control through OpenCV
- Not all settings may be available or effective depending on camera model
- For best camera control, configure settings at initialization time

### Performance Considerations

- Streaming through rpicam-still involves subprocess execution and file I/O
- Higher resolutions will impact performance
- Consider frame rate and resolution trade-offs for real-time applications

## Future Improvements

Potential future enhancements for the camera module:

1. Hardware-accelerated image processing
2. Support for multiple cameras
3. Video recording capabilities
4. Extended format support (JPEG, PNG, RAW, etc.)
5. Integration with ML frameworks for on-device inference
6. Advanced camera controls (HDR, exposure bracketing)
7. Support for the new AI Camera (IMX500) features

## Implementation Notes for AI

### Design Patterns

- Facade Pattern: Camera class provides simplified interface to complex functionality
- Observer Pattern: Streaming callback mechanism

### Thread Safety

- Thread locks protect access to shared resources (frames)
- Thread events control thread lifecycle
- Daemon threads ensure clean application exit

### Resource Management

The module ensures proper resource cleanup through:

- Thread termination in `stop_stream()`
- Camera release in `close()`
- Temporary file cleanup for rpicam operations

### Error Handling Strategy

- Custom exception hierarchy for domain-specific errors
- Descriptive error messages to aid debugging
- Conservative approach with explicit verification of operations
- Graceful degradation when features unavailable

### Code Structure

- Modular design with clear separation of concerns:
  - Configuration and validation
  - Hardware interaction
  - Image processing
  - Threading and synchronization

This module provides reliable camera operations using the modern rpicam-apps stack, ensuring
compatibility across Raspberry Pi systems running Bookworm or later.
