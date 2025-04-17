#!/usr/bin/env python3
"""
Test script for the SAM module SDK.
This demonstrates initialization, button callbacks, and LED control with task completion.
"""

import time
import sys
import signal
from sam import SAM, ButtonType

def main():
    """Main test function to demonstrate SAM module functionality."""
    print("SAM Module Test Script")
    print("---------------------")
    print("This script will test the basic functionality of the SAM module.")
    print("Press Ctrl+C to exit the test.\n")
    
    # Initialize the SAM module
    try:
        print("Initializing SAM module...")
        sam = SAM()
        print("SAM module initialized successfully!")
    except RuntimeError as e:
        print(f"Failed to initialize SAM module: {e}")
        return 1
    
    # Connect to the SAM module
    print("Connecting to SAM module...")
    if not sam.connect():
        print("Failed to connect to SAM module.")
        return 1
    print("Connected to SAM module successfully!")
    
    # Setup button callbacks
    def button_up_handler():
        print("UP button pressed!")
        # Light up blue when UP is pressed - wait for any running task to complete
        if sam.is_led_task_running():
            print("Waiting for previous LED task to complete...")
            sam.wait_for_led_task_completion(timeout=5.0)
        sam.set_led_color(0, 0, 255, brightness=0.5)
        
    def button_down_handler():
        print("DOWN button pressed!")
        # Light up green when DOWN is pressed - wait for any running task to complete
        if sam.is_led_task_running():
            print("Waiting for previous LED task to complete...")
            sam.wait_for_led_task_completion(timeout=5.0)
        sam.set_led_color(0, 255, 0, brightness=0.5)
        
    def button_select_handler():
        print("SELECT button pressed!")
        # Light up red when SELECT is pressed - wait for any running task to complete
        if sam.is_led_task_running():
            print("Waiting for previous LED task to complete...")
            sam.wait_for_led_task_completion(timeout=5.0)
        sam.set_led_color(255, 0, 0, brightness=0.5)
        
    def button_shutdown_handler():
        print("SHUTDOWN signal received!")
        # Fade to white - wait for any running task to complete
        if sam.is_led_task_running():
            print("Waiting for previous LED task to complete...")
            sam.wait_for_led_task_completion(timeout=5.0)
        sam.fade_led(255, 255, 255, steps=10, duration=2.0)
    
    # Register button callbacks
    print("Registering button callbacks...")
    sam.register_button_callback(ButtonType.UP, button_up_handler)
    sam.register_button_callback(ButtonType.DOWN, button_down_handler)
    sam.register_button_callback(ButtonType.SELECT, button_select_handler)
    sam.register_button_callback(ButtonType.SHUTDOWN, button_shutdown_handler)
    
    # Test LED sequence with task completion handling
    print("Testing LED sequences with task completion handling...")
    
    # Test 1: Single color with wait_for_completion
    print("Test 1: Setting LED to red")
    if sam.set_led_color(255, 0, 0, brightness=0.5, wait_for_completion=True, timeout=2.0):
        print("  - LED color set successfully")
    else:
        print("  - Failed to set LED color within timeout")
    
    # Test 2: Blinking with wait_for_completion
    print("Test 2: Blinking LED in green")
    if sam.blink_led(0, 255, 0, count=3, on_time=0.5, off_time=0.5, 
                    brightness=0.5, wait_for_completion=True, timeout=5.0):
        print("  - Blinking completed successfully")
    else:
        print("  - Blinking did not complete within timeout")
    
    
    # Test 3: Custom sequence with wait_for_completion
    print("Test 4: Running custom color sequence")
    sequence = [
        {"r": 255, "g": 0, "b": 0, "brightness": 0.5, "delay": 0.5},     # Red
        {"r": 0, "g": 255, "b": 0, "brightness": 0.5, "delay": 0.5},     # Green
        {"r": 0, "g": 0, "b": 255, "brightness": 0.5, "delay": 0.5},     # Blue
        {"r": 255, "g": 255, "b": 0, "brightness": 0.5, "delay": 0.5},   # Yellow
        {"r": 255, "g": 0, "b": 255, "brightness": 0.5, "delay": 0.5},   # Magenta
        {"r": 0, "g": 255, "b": 255, "brightness": 0.5, "delay": 0.5},   # Cyan
        {"r": 255, "g": 255, "b": 255, "brightness": 0.5, "delay": 0.5}  # White
    ]
    if sam.set_led_sequence(sequence, wait_for_completion=True, timeout=8.0):
        print("  - Color sequence completed successfully")
    else:
        print("  - Color sequence did not complete within timeout")
    
    # Test 4: Task queuing test
    print("Test 4: Testing task rejection when already running")
    # Start a long sequence
    sam.fade_led(255, 0, 0, steps=5, duration=2.5, wait_for_completion=False)
    
    # Try to start another sequence while the first is running
    print("  - Attempting to send a second command while first is running...")
    time.sleep(0.5)  # Give time for the first command to start
    
    if sam.is_led_task_running():
        print("  - Task is running as expected")
        result = sam.set_led_color(0, 255, 0, brightness=0.5, wait_for_completion=False)
        if not result:
            print("  - Second command correctly rejected while task running")
        else:
            print("  - Unexpected: Second command accepted while task running")
    else:
        print("  - Unexpected: Task not reported as running")
    
    # Wait for the first task to complete
    print("  - Waiting for task to complete...")
    sam.wait_for_led_task_completion(timeout=5.0)
    print("  - Task completed")
    
    # Turn off the LED
    print("Test 5: Turning off LED")
    sam.set_led_color(0, 0, 0, brightness=0, wait_for_completion=True)
    
    # Setup clean exit
    def signal_handler(sig, frame):
        print("\nExiting test script...")
        # Wait for any ongoing task before turning off LED
        if sam.is_led_task_running():
            print("Waiting for LED task to complete before exit...")
            sam.wait_for_led_task_completion(timeout=2.0)
        sam.set_led_color(0, 0, 0, brightness=0, wait_for_completion=True, timeout=1.0)
        sam.disconnect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Wait for button presses
    print("\nTest completed. Now waiting for button presses...")
    print("Press UP, DOWN, or SELECT buttons on your device to see callbacks in action.")
    print("Press Ctrl+C to exit.")
    
    try:
        # Keep the main thread alive to continue receiving button events
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        print("\nCleaning up...")
        if sam.is_led_task_running():
            print("Waiting for LED task to complete before exit...")
            sam.wait_for_led_task_completion(timeout=2.0)
        sam.set_led_color(0, 0, 0, brightness=0, wait_for_completion=True, timeout=1.0)
        sam.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
