"""
SAM (System and Microcontroller) Hardware Module

This module provides interfaces to control SAM hardware components including:
- RGB LED control with per-LED color and brightness management
- Non-blocking animation modes (blink, fade, rainbow) with configurable timing
- Linux LED trigger support (heartbeat-rgb, breathing-rgb, and more)
- Thread-safe multi-LED control

The module wraps the Linux sysfs interface for the SAM driver.
"""

from .led import LED, LEDError, create_led_with_sudo

__all__ = ["LED", "LEDError", "create_led_with_sudo"]

# Version information
__version__ = "3.0.0"

# Module metadata
__author__ = "Distiller SDK Team"
__description__ = "SAM hardware control module with sysfs-based RGB LED support"
