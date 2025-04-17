# Camera Module for CM5 SDK

## Overview
The `camera.py` module provides a comprehensive interface for interacting with Raspberry Pi cameras in the CM5 SDK. It uses `libcamera-still` underneath for hardware access, providing reliable camera operations on Raspberry Pi hardware.

## Architecture
The module is built around the `Camera` class, which handles all camera operations through a combination of:
- `libcamera-still` for image capture via subprocess calls
- OpenCV for image processing and format conversion
- Python's threading for non-blocking camera streaming

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
- `_camera`: OpenCV VideoCapture object (used as fallback for settings)
- `_is_streaming`: Boolean tracking if stream is active
- `_stream_thread`: Thread object for asynchronous streaming
- `_stop_event`: Threading event for signaling stream termination
- `_frame`: Current frame buffer
- `_frame_lock`: Thread lock for synchronized frame access
- `_supported_formats`: List of supported image formats
- `_camera_id`: Camera device identifier

#### Methods

##### Configuration and Setup
- `check_system_config()`: Verifies camera configuration in system
  - Checks for libcamera-still availability
  - Verifies camera dtoverlay configuration in config.txt
  - Returns True if configuration is valid, raises CameraError otherwise

- `_init_camera()`: Initializes camera hardware
  - Sets up OpenCV VideoCapture as fallback
  - Tests camera using libcamera-still to ensure it's working
  - Raises CameraError if initialization fails

##### Core Functionality
- `start_stream(callback=None)`: Starts streaming video
  - Creates a background thread capturing frames continuously
  - Optionally accepts a callback function executed for each frame
  - Uses libcamera-still for reliable frame capture

- `stop_stream()`: Stops active streaming
  - Signals thread termination and cleans up resources

- `get_frame()`: Gets latest frame from camera
  - Returns frame from active stream or captures a new frame
  - Uses libcamera-still for direct capture if not streaming
  - Applies format conversion according to configured format
  - Returns numpy.ndarray representing the image

- `capture_image(filepath=None)`: Captures still image
  - Captures image directly using libcamera-still
  - Saves to filepath if provided
  - Returns captured image as numpy.ndarray
  - Directly uses libcamera-still for higher quality stills

##### Camera Settings
- `adjust_setting(setting, value)`: Adjusts camera settings
  - Maps settings to OpenCV constants
  - Note: Limited effectiveness with libcamera-based capture
  - Returns True if successful, raises CameraError otherwise

- `get_setting(setting)`: Gets current value of a setting
  - Maps setting names to OpenCV constants
  - Returns current value of the setting
  - Raises CameraError if setting is unknown

- `get_available_settings()`: Lists available camera settings
  - Returns list of setting names that can be adjusted

- `close()`: Releases camera resources
  - Stops active stream
  - Releases OpenCV camera resources

## Implementation Details

### Hardware Access
The module uses `libcamera-still` for direct hardware access, which provides better compatibility with Raspberry Pi camera modules than OpenCV's VideoCapture. The implementation:

1. Creates temporary files for image capture
2. Executes libcamera-still as a subprocess with appropriate parameters
3. Reads the captured images with OpenCV for processing

### Threading Model
The streaming functionality uses Python's threading to provide non-blocking camera access:

1. `start_stream()` creates a daemon thread running stream_thread_func
2. The thread continuously captures frames in the background
3. Thread-safe access to the current frame is ensured using thread locks
4. The stream can be cleanly terminated with `stop_stream()`

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
from camera import Camera

# Initialize with default settings
camera = Camera()

# Capture an image and save it
image = camera.capture_image("image.jpg")

# Close when done
camera.close()
```

### Custom Configuration
```python
from camera import Camera

# Initialize with custom settings
camera = Camera(
    resolution=(1920, 1080),
    framerate=30,
    rotation=180,
    format='rgb'
)

# Use the camera
# ...

# Close when done
camera.close()
```

### Streaming with Callback
```python
from camera import Camera
import cv2
import time

def process_frame(frame):
    # Process each frame
    # e.g., detect objects, apply filters
    cv2.imshow("Stream", frame)
    cv2.waitKey(1)

camera = Camera(resolution=(1280, 720))

# Start streaming with callback
camera.start_stream(callback=process_frame)

# Do other work while streaming continues
time.sleep(10)

# Stop streaming
camera.stop_stream()
camera.close()
```

### Adjusting Camera Settings
```python
from camera import Camera

camera = Camera()

# Get available settings
settings = camera.get_available_settings()
print(f"Available settings: {settings}")

# Get current brightness
brightness = camera.get_setting('brightness')
print(f"Current brightness: {brightness}")

# Adjust brightness
camera.adjust_setting('brightness', 70)

# Close when done
camera.close()
```

## System Requirements

### Hardware
- Raspberry Pi computer (tested on CM5)
- Compatible camera module (e.g., Camera Module V1/V2, High Quality Camera)
- Proper camera connection to CSI port

### Software
- Raspberry Pi OS or compatible Linux distribution
- libcamera-apps package installed
- OpenCV Python library
- Properly configured /boot/firmware/config.txt with camera dtoverlay

### Camera Configuration
The camera requires proper configuration in the Raspberry Pi's config.txt, which may include:
- `dtoverlay=ov5647` (Camera Module V1)
- `dtoverlay=imx219` (Camera Module V2)
- `dtoverlay=imx477` (High Quality Camera)
- Other camera-specific overlays

## Limitations and Known Issues

### Rotations with Transpose
Some rotation values (90, 270) may not be supported by all camera modules as they require transpose operations. The error "transforms requiring transpose not supported" may appear in these cases.

### Camera Settings
While the module supports adjustment of various camera settings through the OpenCV interface, these may have limited effect when capturing with libcamera-still. Future implementations may directly pass settings to libcamera-still.

### Performance Considerations
- Streaming through libcamera-still is not as performant as native V4L2 streaming
- Each frame capture involves subprocess execution and file I/O, which limits framerate
- Higher resolutions will further impact performance

## Future Improvements
Potential future enhancements for the camera module:

1. Direct libcamera API integration for improved performance
2. Expanded setting controls through libcamera parameters
3. Hardware-accelerated image processing
4. Support for multiple cameras
5. Video recording capabilities
6. Extended format support (JPEG, PNG, RAW, etc.)
7. Integration with ML frameworks for on-device inference

## Implementation Notes for AI

### Design Patterns
- Facade Pattern: The Camera class provides a simplified interface to complex camera functionality
- Singleton-like behavior: While not a strict singleton, typically only one camera instance should exist
- Observer Pattern: The streaming callback mechanism follows observer pattern principles

### Thread Safety
- Thread locks protect access to shared resources (frames)
- Thread events control thread lifecycle
- Daemon threads ensure clean application exit

### Resource Management
- The module ensures proper resource cleanup through:
  - Thread termination in `stop_stream()`
  - Camera release in `close()`
  - Temporary file cleanup using context managers

### Error Handling Strategy
- Custom exception hierarchy for domain-specific errors
- Descriptive error messages to aid debugging
- Conservative approach with explicit verification of operations

### Code Structure
- Modular design with clear separation of concerns:
  - Configuration and validation
  - Hardware interaction
  - Image processing
  - Threading and synchronization

This module carefully balances simplicity of interface with reliability of operation, prioritizing consistent behavior on Raspberry Pi hardware over raw performance. 