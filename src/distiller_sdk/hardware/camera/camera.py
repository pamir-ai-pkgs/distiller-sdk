#!/usr/bin/env python3
"""
Camera module for Raspberry Pi Camera integration.
Part of the CM5 SDK for controlling and interacting with Raspberry Pi Camera.

This module uses rpicam-apps (modern CLI tools for Raspberry Pi OS Bookworm+)
for reliable camera operations on Raspberry Pi hardware.
"""

import os
import time
import subprocess
import threading
import cv2  # type: ignore
import numpy as np
import tempfile
import shutil
import logging
from typing import Optional, Tuple, Union, List, Callable

from distiller_sdk.exceptions import CameraError
from distiller_sdk.hardware_status import HardwareStatus, HardwareState

# Set up logging
logger = logging.getLogger(__name__)


class Camera:
    """
    Camera class for interacting with Raspberry Pi camera using rpicam-apps.

    This class provides functionality to:
    - Stream video from the camera
    - Adjust camera settings
    - Capture images
    - Check camera configuration

    The class uses rpicam-apps (rpicam-still) for camera operations.
    """

    def __init__(
        self,
        resolution: Tuple[int, int] = (640, 480),
        framerate: int = 30,
        rotation: int = 0,
        format: str = "bgr",
        auto_check_config: bool = True,
    ):
        """
        Initialize the Camera object.

        Args:
            resolution: Tuple of (width, height) for the camera resolution
            framerate: Frames per second for video capture
            rotation: Camera rotation in degrees (0, 90, 180, or 270)
            format: Output format ('bgr', 'rgb', 'gray')
            auto_check_config: Whether to automatically check system configuration

        Raises:
            CameraError: If camera configuration is invalid or camera can't be initialized
        """
        self.resolution = resolution
        self.framerate = framerate
        self.rotation = rotation
        self.format = format.lower()
        self._camera = None
        self._is_streaming = False
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._frame = None
        self._frame_lock = threading.Lock()

        # Supported formats
        self._supported_formats = ["bgr", "rgb", "gray"]
        if self.format not in self._supported_formats:
            raise CameraError(
                f"Unsupported format: {self.format}. Must be one of {self._supported_formats}"
            )

        # Camera device ID
        self._camera_id = 0

        # Check for rpicam-apps availability
        if not shutil.which("rpicam-still"):
            raise CameraError("rpicam-still not found. Please install rpicam-apps package.")

        logger.info("Using rpicam-apps for camera operations")

        # Check system configuration
        if auto_check_config:
            self.check_system_config()

        # Try to initialize the camera
        try:
            self._init_camera()
        except Exception as e:
            raise CameraError(f"Failed to initialize camera: {str(e)}")

    @staticmethod
    def get_status() -> HardwareStatus:
        """Get detailed camera hardware status without initializing.

        This method probes camera hardware availability and capabilities without
        creating a Camera instance or modifying system state. It never raises
        exceptions - all errors are captured in the returned status.

        Returns:
            HardwareStatus: Detailed hardware status including state, capabilities,
                          diagnostics, and error information

        Example:
            >>> status = Camera.get_status()
            >>> if status.available:
            ...     camera = Camera()
            >>> else:
            ...     print(f"Camera unavailable: {status.message}")
        """
        capabilities = {}
        diagnostic_info = {}

        try:
            # Check for rpicam-still availability
            if not shutil.which("rpicam-still"):
                return HardwareStatus(
                    state=HardwareState.UNAVAILABLE,
                    available=False,
                    capabilities={},
                    error=FileNotFoundError("rpicam-still not found"),
                    diagnostic_info={},
                    message="rpicam-still not found - install rpicam-apps package",
                )

            capabilities["rpicam_available"] = True

            # Check for OpenCV availability (optional, for some features)
            try:
                import cv2  # noqa: F401

                capabilities["opencv_available"] = True
            except ImportError:
                capabilities["opencv_available"] = False

            # List cameras using rpicam-still
            try:
                result = subprocess.run(
                    ["rpicam-still", "--list-cameras"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=5,
                )

                if result.returncode == 0:
                    diagnostic_info["rpicam_output"] = result.stdout

                    # Check if cameras were detected
                    if "Available cameras" in result.stdout:
                        # Parse camera count from output
                        lines = result.stdout.split("\n")
                        camera_count = 0
                        camera_list = []

                        for line in lines:
                            # Camera lines typically start with a number followed by colon
                            # Example: "0 : imx219 [3280 x 2464] ..."
                            stripped = line.strip()
                            if stripped and stripped[0].isdigit() and ":" in stripped:
                                camera_count += 1
                                # Extract camera info
                                camera_info = (
                                    stripped.split(":", 1)[1].strip()
                                    if ":" in stripped
                                    else stripped
                                )
                                camera_list.append(camera_info)

                        if camera_count > 0:
                            capabilities["camera_count"] = camera_count
                            diagnostic_info["cameras_detected"] = camera_list

                            # All checks passed
                            return HardwareStatus(
                                state=HardwareState.AVAILABLE,
                                available=True,
                                capabilities=capabilities,
                                error=None,
                                diagnostic_info=diagnostic_info,
                                message=f"Camera hardware available ({camera_count} camera(s) detected)",
                            )
                        else:
                            return HardwareStatus(
                                state=HardwareState.UNAVAILABLE,
                                available=False,
                                capabilities=capabilities,
                                error=FileNotFoundError("No cameras detected"),
                                diagnostic_info=diagnostic_info,
                                message="No cameras detected by rpicam-still",
                            )
                    else:
                        return HardwareStatus(
                            state=HardwareState.UNAVAILABLE,
                            available=False,
                            capabilities=capabilities,
                            error=FileNotFoundError("No cameras detected"),
                            diagnostic_info=diagnostic_info,
                            message="No cameras detected by rpicam-still",
                        )
                else:
                    # rpicam-still command failed
                    diagnostic_info["rpicam_stderr"] = result.stderr
                    return HardwareStatus(
                        state=HardwareState.UNAVAILABLE,
                        available=False,
                        capabilities=capabilities,
                        error=subprocess.CalledProcessError(
                            result.returncode, result.args, result.stdout, result.stderr
                        ),
                        diagnostic_info=diagnostic_info,
                        message=f"rpicam-still failed: {result.stderr}",
                    )

            except subprocess.TimeoutExpired as e:
                return HardwareStatus(
                    state=HardwareState.UNAVAILABLE,
                    available=False,
                    capabilities=capabilities,
                    error=e,
                    diagnostic_info=diagnostic_info,
                    message="Timeout detecting camera hardware",
                )

        except PermissionError as e:
            return HardwareStatus(
                state=HardwareState.PERMISSION_DENIED,
                available=False,
                capabilities={},
                error=e,
                diagnostic_info=diagnostic_info,
                message=f"Permission denied accessing camera: {str(e)}",
            )
        except FileNotFoundError as e:
            return HardwareStatus(
                state=HardwareState.UNAVAILABLE,
                available=False,
                capabilities={},
                error=e,
                diagnostic_info=diagnostic_info,
                message=f"Camera tools not found: {str(e)}",
            )
        except Exception as e:
            return HardwareStatus(
                state=HardwareState.UNAVAILABLE,
                available=False,
                capabilities={},
                error=e,
                diagnostic_info=diagnostic_info,
                message=f"Error detecting camera hardware: {str(e)}",
            )

    @staticmethod
    def is_available() -> bool:
        """Quick check if camera hardware is available.

        This is a convenience method that returns the available flag from get_status().
        Use get_status() for detailed information about capabilities and errors.

        Returns:
            bool: True if camera hardware is available and accessible

        Example:
            >>> if Camera.is_available():
            ...     camera = Camera()
            ... else:
            ...     print("Camera hardware not available")
        """
        return Camera.get_status().available

    def check_system_config(self) -> bool:
        """
        Check if the Raspberry Pi is properly configured for camera use.

        Returns:
            bool: True if configuration is valid

        Raises:
            CameraError: If configuration is invalid
        """
        # Check if rpicam-still can list cameras
        try:
            result = subprocess.run(
                ["rpicam-still", "--list-cameras"], capture_output=True, text=True, check=False
            )
            if "Available cameras" not in result.stdout:
                raise CameraError("No cameras detected by rpicam-still")
        except FileNotFoundError:
            raise CameraError("rpicam-still not found. Please install rpicam-apps package.")

        # Check for camera configuration in config.txt
        config_path = "/boot/firmware/config.txt"

        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_content = f.read()

            # Check for camera configuration in config.txt
            camera_overlay_found = False

            # Different camera modules might use different dtoverlays
            camera_overlays = [
                "dtoverlay=imx219",  # Camera Module V2
                "dtoverlay=imx477",  # High Quality Camera
                "dtoverlay=imx500",  # AI Camera
                "dtoverlay=ov5647",  # Camera Module V1
                "dtoverlay=arducam",
                "dtoverlay=camera",
            ]

            for overlay in camera_overlays:
                if overlay in config_content:
                    camera_overlay_found = True
                    break

            if not camera_overlay_found:
                logger.warning(
                    "Camera dtoverlay not found in /boot/firmware/config.txt. "
                    "Camera may not work properly."
                )

        return True

    def _init_camera(self):
        """Initialize camera using rpicam CLI tools."""
        # For OpenCV fallback (not primary capture method but used for setting adjustments)
        self._camera = cv2.VideoCapture(0)

        # Test camera using rpicam-still
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as temp_file:
                cmd = [
                    "rpicam-still",
                    "-n",  # No preview
                    "-t",
                    "1",  # Timeout 1ms
                    "-o",
                    temp_file.name,  # Output file
                    "--width",
                    str(self.resolution[0]),
                    "--height",
                    str(self.resolution[1]),
                ]

                # Add rotation if specified
                if self.rotation != 0:
                    cmd.extend(["--rotation", str(self.rotation)])

                result = subprocess.run(cmd, capture_output=True, text=True, check=False)

                if result.returncode != 0:
                    raise CameraError(
                        f"Failed to initialize camera with rpicam-still: {result.stderr}"
                    )

                logger.info("Camera initialized using rpicam-still")

        except Exception as e:
            raise CameraError(f"Failed to initialize camera: {str(e)}")

    def start_stream(self, callback: Optional[Callable] = None) -> None:
        """
        Start streaming video from the camera.

        Args:
            callback: Optional callback function that will be called with each new frame

        Raises:
            CameraError: If streaming cannot be started
        """
        if self._is_streaming:
            return

        self._stop_event.clear()
        self._is_streaming = True

        # Use rpicam-still streaming
        def stream_thread_func():
            while not self._stop_event.is_set():
                try:
                    # Capture using rpicam-still
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as temp_file:
                        cmd = [
                            "rpicam-still",
                            "-n",  # No preview
                            "-t",
                            "1",  # Timeout 1ms
                            "--immediate",  # Capture immediately
                            "-o",
                            temp_file.name,  # Output file
                            "--width",
                            str(self.resolution[0]),
                            "--height",
                            str(self.resolution[1]),
                        ]

                        # Add rotation if specified
                        if self.rotation != 0:
                            cmd.extend(["--rotation", str(self.rotation)])

                        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

                        if result.returncode != 0:
                            logger.warning(f"Failed to capture frame: {result.stderr}")
                            continue

                        # Read the image with OpenCV
                        frame = cv2.imread(temp_file.name)

                        if frame is None:
                            continue

                        # Apply format conversion if needed
                        if self.format == "rgb":
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        elif self.format == "gray":
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                        # Update the current frame with thread safety
                        with self._frame_lock:
                            self._frame = frame

                        # Call the callback if provided
                        if callback:
                            callback(frame)

                except Exception as e:
                    logger.error(f"Stream error: {str(e)}")

                # Limit CPU usage - adjust sleep time based on framerate
                time.sleep(1.0 / self.framerate)

        self._stream_thread = threading.Thread(target=stream_thread_func)
        self._stream_thread.daemon = True
        self._stream_thread.start()
        logger.info("Camera streaming started")

    def stop_stream(self) -> None:
        """Stop the camera stream."""
        if not self._is_streaming:
            return

        self._stop_event.set()
        if self._stream_thread:
            self._stream_thread.join(timeout=1.0)

        self._is_streaming = False
        logger.info("Camera streaming stopped")

    def get_frame(self) -> np.ndarray:
        """
        Get the latest frame from the camera.

        Returns:
            np.ndarray: The latest camera frame

        Raises:
            CameraError: If no frame is available
        """
        # For direct capture without streaming
        if not self._is_streaming:
            # Capture a frame directly using rpicam-still
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as temp_file:
                cmd = [
                    "rpicam-still",
                    "-n",  # No preview
                    "-t",
                    "500",  # Timeout 500ms
                    "--immediate",  # Capture immediately
                    "-o",
                    temp_file.name,  # Output file
                    "--width",
                    str(self.resolution[0]),
                    "--height",
                    str(self.resolution[1]),
                ]

                # Add rotation if specified
                if self.rotation != 0:
                    cmd.extend(["--rotation", str(self.rotation)])

                result = subprocess.run(cmd, capture_output=True, text=True, check=False)

                if result.returncode != 0:
                    raise CameraError(f"Failed to capture frame: {result.stderr}")

                # Read the image with OpenCV
                frame = cv2.imread(temp_file.name)

                if frame is None:
                    raise CameraError("Failed to read captured image")

                # Apply format conversion if needed
                if self.format == "rgb":
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                elif self.format == "gray":
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Update the current frame with thread safety
                with self._frame_lock:
                    self._frame = frame

                return frame

        # Get the latest frame from the stream
        with self._frame_lock:
            if self._frame is None:
                raise CameraError("No frame available")
            return self._frame.copy()

    def capture_image(self, filepath: Optional[str] = None) -> np.ndarray:
        """
        Capture a still image from the camera.

        Args:
            filepath: Optional path to save the image

        Returns:
            np.ndarray: The captured image

        Raises:
            CameraError: If image cannot be captured
        """
        # If filepath is provided, capture directly to that file using rpicam-still
        if filepath:
            cmd = [
                "rpicam-still",
                "-n",  # No preview
                "-t",
                "1000",  # Timeout 1000ms
                "-o",
                filepath,  # Output file
                "--width",
                str(self.resolution[0]),
                "--height",
                str(self.resolution[1]),
            ]

            # Add rotation if specified
            if self.rotation != 0:
                cmd.extend(["--rotation", str(self.rotation)])

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                raise CameraError(f"Failed to capture image: {result.stderr}")

            # Read the image with OpenCV
            frame = cv2.imread(filepath)

            if frame is None:
                raise CameraError(f"Failed to read captured image from {filepath}")

            # Apply format conversion if needed
            if self.format == "rgb":
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            elif self.format == "gray":
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            return frame
        else:
            # If no filepath is provided, use get_frame
            return self.get_frame()

    def adjust_setting(self, setting: str, value: Union[int, float, bool]) -> bool:
        """
        Adjust a camera setting.

        Note: Settings adjustment through OpenCV has limited effect when using
        rpicam-still for capture. For best results, configure camera settings
        at initialization time.

        Args:
            setting: Name of the setting to adjust
            value: New value for the setting

        Returns:
            bool: True if successful (though effect may be limited)

        Raises:
            CameraError: If setting cannot be adjusted
        """
        if not self._camera or not self._camera.isOpened():
            raise CameraError("Camera is not initialized")

        setting_mapping = {
            "brightness": cv2.CAP_PROP_BRIGHTNESS,
            "contrast": cv2.CAP_PROP_CONTRAST,
            "saturation": cv2.CAP_PROP_SATURATION,
            "hue": cv2.CAP_PROP_HUE,
            "gain": cv2.CAP_PROP_GAIN,
            "exposure": cv2.CAP_PROP_EXPOSURE,
            "white_balance": cv2.CAP_PROP_WHITE_BALANCE_RED_V,
            "focus": cv2.CAP_PROP_FOCUS,
            "zoom": cv2.CAP_PROP_ZOOM,
            "auto_exposure": cv2.CAP_PROP_AUTO_EXPOSURE,
            "auto_wb": cv2.CAP_PROP_AUTO_WB,
            "sharpness": cv2.CAP_PROP_SHARPNESS,
        }

        if setting.lower() not in setting_mapping:
            raise CameraError(f"Unknown setting: {setting}")

        prop_id = setting_mapping[setting.lower()]
        success = self._camera.set(prop_id, value)

        if not success:
            logger.warning(f"Setting {setting} may not have effect with rpicam-still capture")

        return success

    def get_setting(self, setting: str) -> Union[int, float]:
        """
        Get the current value of a camera setting.

        Note: These values come from OpenCV and may not reflect actual
        rpicam-still capture settings.

        Args:
            setting: Name of the setting to get

        Returns:
            Union[int, float]: Current value of the setting

        Raises:
            CameraError: If setting cannot be retrieved
        """
        if not self._camera or not self._camera.isOpened():
            raise CameraError("Camera is not initialized")

        setting_mapping = {
            "brightness": cv2.CAP_PROP_BRIGHTNESS,
            "contrast": cv2.CAP_PROP_CONTRAST,
            "saturation": cv2.CAP_PROP_SATURATION,
            "hue": cv2.CAP_PROP_HUE,
            "gain": cv2.CAP_PROP_GAIN,
            "exposure": cv2.CAP_PROP_EXPOSURE,
            "white_balance": cv2.CAP_PROP_WHITE_BALANCE_RED_V,
            "focus": cv2.CAP_PROP_FOCUS,
            "zoom": cv2.CAP_PROP_ZOOM,
            "auto_exposure": cv2.CAP_PROP_AUTO_EXPOSURE,
            "auto_wb": cv2.CAP_PROP_AUTO_WB,
            "sharpness": cv2.CAP_PROP_SHARPNESS,
        }

        if setting.lower() not in setting_mapping:
            raise CameraError(f"Unknown setting: {setting}")

        prop_id = setting_mapping[setting.lower()]
        value = self._camera.get(prop_id)

        return value

    def get_available_settings(self) -> List[str]:
        """
        Get a list of available camera settings that can be adjusted.

        Note: These settings have limited effect with rpicam-still.

        Returns:
            List[str]: List of available setting names
        """
        return [
            "brightness",
            "contrast",
            "saturation",
            "hue",
            "gain",
            "exposure",
            "white_balance",
            "focus",
            "zoom",
            "auto_exposure",
            "auto_wb",
            "sharpness",
        ]

    def close(self):
        """Release camera resources."""
        if self._is_streaming:
            self.stop_stream()

        if self._camera and self._camera.isOpened():
            self._camera.release()
            self._camera = None

        logger.info("Camera closed")

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and cleanup resources."""
        self.close()
        return False
