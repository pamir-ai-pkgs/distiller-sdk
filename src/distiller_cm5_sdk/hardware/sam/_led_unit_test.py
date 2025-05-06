#!/usr/bin/env python3
"""
Test script for the LED module SDK.
This demonstrates initialization and sending LED commands (fire and forget).
"""

import time
import sys
import signal
from led import LED
from typing import Optional

def main():
    """Main test function to demonstrate LED module functionality."""
    print("LED Module Test Script (Fire and Forget)")
    print("-----------------------------------------")
    print("This script will send LED commands without waiting for completion.")
    print("Observe the LED for visual confirmation.")
    print("Press Ctrl+C to exit the test.\n")

    led_instance: Optional[LED] = None
    try:
        print("Initializing LED module...")
        led_instance = LED()
        print("LED module initialized successfully!")
    except RuntimeError as e:
        print(f"Failed to initialize LED module: {e}")
        return 1

    led = led_instance # For type hinting below if needed, though not strictly necessary

    # Connect is a placeholder, but call for completeness
    print("Connecting to LED module (placeholder)...")
    led.connect()
    print("Connected to LED module successfully!")

    # Test Sending LED Commands
    print("Testing Sending LED Commands...")

    # Test 1: Single color
    print("Test 1: Setting LED to red (delay 0.5s)")
    led.set_led_color(255, 0, 0, brightness=0.5, delay=0.5)
    print("  - Command sent. Sleeping briefly to allow execution...")
    time.sleep(0.7) # Sleep longer than the command delay

    # Test 2: Blinking
    print("Test 2: Blinking LED in green (3 times, 0.3s on/off)")
    blink_duration = 3 * (0.3 + 0.3)
    led.blink_led(0, 255, 0, count=3, on_time=0.3, off_time=0.3, brightness=0.5)
    print(f"  - Command sent. Sleeping for estimated duration: {blink_duration:.1f}s...")
    time.sleep(blink_duration + 0.2) # Sleep for the blink duration + buffer


    # Test 3: Custom sequence
    print("Test 3: Running custom color sequence")
    sequence = [
        {"r": 255, "g": 0, "b": 0, "brightness": 0.5, "delay": 0.4},     # Red
        {"r": 0, "g": 255, "b": 0, "brightness": 0.5, "delay": 0.4},     # Green
        {"r": 0, "g": 0, "b": 255, "brightness": 0.5, "delay": 0.4},     # Blue
        {"r": 255, "g": 255, "b": 0, "brightness": 0.5, "delay": 0.4},   # Yellow
    ]
    sequence_duration = sum(item["delay"] for item in sequence)
    led.set_led_sequence(sequence)
    print(f"  - Command sent. Sleeping for estimated duration: {sequence_duration:.1f}s...")
    time.sleep(sequence_duration + 0.2) # Sleep for the sequence duration + buffer

    # Test 4: Fade (Removed)
    # print("Test 4: Fading LED to magenta")
    # fade_duration = 4.0
    # # Reduce steps to test sequence length limitation
    # led.fade_led(255, 0, 255, steps=15, duration=fade_duration, final_brightness=0.8)
    # print(f"  - Command sent. Sleeping for estimated duration: {fade_duration:.1f}s...")
    # time.sleep(fade_duration + 0.2)


    # Turn off the LED
    print("Test 5: Turning off LED")
    led.set_led_color(0, 0, 0, brightness=0, delay=0.1)

    print("  - Off command sent and slept briefly.")
    # Keep this outer sleep too, just in case
    time.sleep(0.2)


    # Setup clean exit
    def signal_handler(sig, frame):
        print("\nExiting test script by signal...")
        if led_instance: # Check if initialization was successful
             print("Attempting to turn off LED on exit...")
             # Use final_sleep to pause before file handle closes
             success = led_instance.set_led_color(0, 0, 0, brightness=0, delay=0.1)
             if success:
                 print("  - Off command sent successfully.")
             else:
                 print("  - Failed to send off command.")
             # Short pause after function returns
             time.sleep(0.2)
             led_instance.disconnect() # Placeholder call
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("\nTest commands sent. Observe LED behavior.")
    print("Press Ctrl+C to exit (or wait for script end).")

    # Keep script alive for a short time to observe final state if needed
    # Or just exit after turning off
    # time.sleep(2)

    # Cleanup is now primarily turning the LED off (already done in Test 5)
    # and the signal handler attempts it too.
    # We don't need the complex finally block checking is_running anymore.

    print("\nScript finished.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
