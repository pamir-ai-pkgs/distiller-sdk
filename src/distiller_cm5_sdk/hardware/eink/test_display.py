#!/usr/bin/env python3
"""
Test script for e-ink display with configurable firmware.
"""

import sys
import os
from distiller_cm5_sdk.hardware.eink import (
    Display, DisplayMode, DisplayError, FirmwareType,
    set_default_firmware, get_default_firmware, initialize_display_config
)

def test_configuration():
    """Test configuration system."""
    print("=== Testing Configuration System ===")
    
    try:
        # Initialize config from environment/files
        print("1. Initializing configuration...")
        initialize_display_config()
        
        # Get current firmware
        current = get_default_firmware()
        print(f"Current firmware: {current}")
        
        # Test setting firmware
        print("2. Testing firmware setting...")
        if current == FirmwareType.EPD128x250:
            test_firmware = FirmwareType.EPD240x416
        else:
            test_firmware = FirmwareType.EPD128x250
        
        print(f"Setting firmware to: {test_firmware}")
        set_default_firmware(test_firmware)
        
        # Verify change
        updated = get_default_firmware()
        print(f"Updated firmware: {updated}")
        
        # Reset to original
        set_default_firmware(current)
        final = get_default_firmware()
        print(f"Reset to: {final}")
        
        return True
        
    except Exception as e:
        print(f"Configuration test failed: {e}")
        return False

def test_display_basic():
    """Test basic display operations."""
    print("\n=== Testing Basic Display Operations ===")
    
    try:
        # Create display without auto-initialization
        display = Display(auto_init=False)
        
        # Check if config is available
        if hasattr(display, '_config_available'):
            print(f"Config system available: {display._config_available}")
        
        # Initialize manually
        print("1. Initializing display...")
        display.initialize()
        
        # Get dimensions
        width, height = display.get_dimensions()
        print(f"Display dimensions: {width}x{height}")
        
        # Calculate correct data size
        array_size = (width * height) // 8
        print(f"Required data size: {array_size} bytes")
        
        # Test with correct data size
        print("2. Testing with correct data size...")
        
        # Create white image
        white_data = bytes([0xFF] * array_size)
        print(f"White image data: {len(white_data)} bytes")
        
        # Create black image
        black_data = bytes([0x00] * array_size)
        print(f"Black image data: {len(black_data)} bytes")
        
        # Display white image
        print("3. Displaying white image...")
        display.display_image(white_data, DisplayMode.FULL)
        print("✓ White image displayed")
        
        # Wait a bit
        import time
        time.sleep(2)
        
        # Display black image
        print("4. Displaying black image...")
        display.display_image(black_data, DisplayMode.FULL)
        print("✓ Black image displayed")
        
        time.sleep(2)
        
        # Clear display
        print("5. Clearing display...")
        display.clear()
        print("✓ Display cleared")
        
        # Sleep display
        print("6. Putting display to sleep...")
        display.sleep()
        print("✓ Display sleeping")
        
        # Cleanup
        display.close()
        print("✓ Display closed")
        
        return True
        
    except DisplayError as e:
        print(f"Display error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def test_firmware_switch():
    """Test switching between firmware types."""
    print("\n=== Testing Firmware Switching ===")
    
    try:
        # Test with EPD128x250
        print("1. Testing with EPD128x250...")
        set_default_firmware(FirmwareType.EPD128x250)
        
        display = Display(auto_init=False)
        display.initialize()
        
        width, height = display.get_dimensions()
        print(f"EPD128x250 dimensions: {width}x{height}")
        
        expected_size = (width * height) // 8
        test_data = bytes([0xFF] * expected_size)
        
        # This should work
        display.display_image(test_data, DisplayMode.FULL)
        print(f"✓ EPD128x250 test passed ({expected_size} bytes)")
        
        display.close()
        
        # Test with EPD240x416 (if available)
        print("2. Testing with EPD240x416...")
        try:
            set_default_firmware(FirmwareType.EPD240x416)
            
            display = Display(auto_init=False)
            display.initialize()
            
            width, height = display.get_dimensions()
            print(f"EPD240x416 dimensions: {width}x{height}")
            
            expected_size = (width * height) // 8
            test_data = bytes([0xFF] * expected_size)
            
            # This should work too
            display.display_image(test_data, DisplayMode.FULL)
            print(f"✓ EPD240x416 test passed ({expected_size} bytes)")
            
            display.close()
            
        except Exception as e:
            print(f"EPD240x416 test failed (may not be available): {e}")
        
        return True
        
    except Exception as e:
        print(f"Firmware switch test failed: {e}")
        return False

def main():
    """Main test function."""
    print("E-ink Display Test Suite")
    print("=" * 50)
    
    success = True
    
    # Test configuration first
    if test_configuration():
        print("✓ Configuration test passed")
    else:
        print("✗ Configuration test failed")
        success = False
    
    # Test basic display operations
    if test_display_basic():
        print("✓ Basic display test passed")
    else:
        print("✗ Basic display test failed")
        success = False
    
    # Test firmware switching
    if test_firmware_switch():
        print("✓ Firmware switch test passed")
    else:
        print("✗ Firmware switch test failed")
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())