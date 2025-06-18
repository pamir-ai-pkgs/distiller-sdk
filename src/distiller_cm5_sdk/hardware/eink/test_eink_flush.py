#!/usr/bin/env python3
"""
Quick E-ink Display Flush Test
Tests basic e-ink display functionality without mocking.
"""

import sys
import time
from eink import EinkDriver

def test_eink_flush():
    """Test if we can initialize and flush the e-ink display."""
    print("E-ink Display Flush Test")
    print("=" * 30)
    
    display = None
    try:
        # Initialize display
        print("1. Initializing e-ink display...")
        display = EinkDriver()
        
        if not display.initialize():
            print("❌ Failed to initialize e-ink display")
            return False
        
        print("✅ E-ink display initialized successfully")
        
        # Test clearing/flushing the display
        print("2. Clearing/flushing display...")
        display.clear_display()
        print("✅ Display cleared successfully")
        
        # Wait a moment to see the effect
        print("3. Waiting 2 seconds...")
        time.sleep(2)
        
        print("✅ E-ink flush test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during e-ink test: {e}")
        print(f"Error type: {type(e).__name__}")
        return False
        
    finally:
        # Cleanup
        if display:
            print("4. Cleaning up...")
            display.cleanup()
            print("✅ Cleanup completed")

def main():
    """Main test function."""
    print("Starting e-ink display hardware test...")
    print()
    
    success = test_eink_flush()
    
    print()
    if success:
        print("🎉 E-ink display test PASSED!")
        sys.exit(0)
    else:
        print("💥 E-ink display test FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main() 