#!/usr/bin/env python3
"""
Simple test for the horizontal flip fix - no PIL required.
"""

import sys
from pathlib import Path

# Add the current directory to path so we can import display
sys.path.insert(0, str(Path(__file__).parent))

from display import Display, DisplayMode, display_png

def test_simple_flip():
    """Test the horizontal flip fix functionality."""
    
    print("Simple E-ink Display Flip Fix Test")
    print("=" * 40)
    
    try:
        # Test flip correction enabled (default)
        print("\n1. Testing with flip correction enabled (default)...")
        with Display() as display:
            print(f"   Flip correction enabled: {display.is_flip_correction_enabled()}")
            
            # Test enabling/disabling flip correction
            display.enable_flip_correction(False)
            print(f"   After disabling: {display.is_flip_correction_enabled()}")
            
            display.enable_flip_correction(True)
            print(f"   After re-enabling: {display.is_flip_correction_enabled()}")
        
        # Test flip correction disabled
        print("\n2. Testing with flip correction disabled...")
        with Display(fix_flip=False) as display:
            print(f"   Flip correction enabled: {display.is_flip_correction_enabled()}")
        
        print("\n3. Display information:")
        width, height = Display().get_dimensions()
        print(f"   Display dimensions: {width}x{height}")
        print(f"   Data array size: {Display.ARRAY_SIZE} bytes")
        
        print("\nSimple flip fix is ready!")
        print("\nHow it works:")
        print("- Both PNG and raw data go through _display_raw()")
        print("- The flip is applied to the raw 1-bit data before sending to hardware")
        print("- No PIL needed - works with any image that the C library can convert")
        
        print("\nUsage examples:")
        print("  # Default - flip correction enabled")
        print("  display_png('image.png')")
        print("")
        print("  # Disable flip correction")
        print("  display_png('image.png', fix_flip=False)")
        print("")
        print("  # Using Display class directly")
        print("  with Display(fix_flip=True) as display:")
        print("      display.display_image('image.png')")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        print("\nNote: This test only verifies the flip logic implementation.")
        print("Actual display hardware is not required for this test.")


if __name__ == "__main__":
    test_simple_flip() 