#!/usr/bin/env python3
"""
Interactive LED Demo and Test Suite

This demo showcases comprehensive LED functionality in an interactive way.
Press Enter to continue between each demo section.
Run as: python led_interactive_demo.py

Features demonstrated:
- LED discovery and initialization
- RGB color control
- Brightness control
- Animation modes (blink, fade, rainbow)
- LED triggers (heartbeat-rgb, breathing-rgb, rainbow-rgb)
- Dynamic timing control
- Multi-LED control with animations
- Convenience methods
- Error handling
"""

import time
import sys
import signal
from distiller_sdk.hardware.sam import LEDError, create_led_with_sudo


class InteractiveLEDDemo:
    """Interactive LED demonstration class."""

    def __init__(self):
        """Initialize the demo."""
        self.led = None
        self.available_leds = []

    def wait_for_enter(self, message="Press Enter to continue..."):
        """Wait for user to press Enter."""
        try:
            input(f"\n💡 {message}")
        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def print_section(self, title, description=""):
        """Print a formatted section header."""
        print(f"\n{'=' * 60}")
        print(f"🎯 {title}")
        print(f"{'=' * 60}")
        if description:
            print(f"📝 {description}")

    def demo_initialization(self):
        """Demo 1: LED initialization and discovery."""
        self.print_section(
            "Demo 1: LED Initialization", "Discovering available LEDs and setting up sudo mode"
        )

        print("🔧 Initializing LED module with sudo mode...")
        self.led = create_led_with_sudo()
        print("✅ LED module initialized successfully!")

        self.available_leds = self.led.get_available_leds()
        print(f"🔍 Discovered LEDs: {self.available_leds}")
        print(f"📊 Total LEDs found: {len(self.available_leds)}")

        if not self.available_leds:
            raise LEDError("❌ No LEDs found! Check if the SAM driver is loaded.")

        self.wait_for_enter("Ready to test RGB colors?")

    def demo_rgb_colors(self):
        """Demo 2: RGB color control."""
        self.print_section(
            "Demo 2: RGB Color Control", "Testing primary and secondary colors on LED 0"
        )

        led_id = self.available_leds[0]
        print(f"🎨 Testing RGB colors on LED {led_id}...")

        colors = [
            (255, 0, 0, "🔴 Red"),
            (0, 255, 0, "🟢 Green"),
            (0, 0, 255, "🔵 Blue"),
            (255, 255, 0, "🟡 Yellow"),
            (255, 0, 255, "🟣 Magenta"),
            (0, 255, 255, "🩵 Cyan"),
            (255, 128, 0, "🟠 Orange"),
            (255, 255, 255, "⚪ White"),
            (128, 64, 0, "🤎 Brown"),
            (0, 128, 64, "🟢 Forest Green"),
        ]

        for red, green, blue, name in colors:
            print(f"Setting {name} - RGB({red}, {green}, {blue})")
            self.led.set_rgb_color(led_id, red, green, blue)
            self.led.set_brightness(led_id, 200)

            # Verify the color was set
            current = self.led.get_rgb_color(led_id)
            print(f"  ✓ Verified: RGB{current}")
            time.sleep(0.8)

        self.wait_for_enter("Ready to test brightness control?")

    def demo_brightness_control(self):
        """Demo 3: Brightness control."""
        self.print_section(
            "Demo 3: Brightness Control",
            "Demonstrating brightness levels while preserving color ratios",
        )

        led_id = self.available_leds[0]
        print(f"💡 Testing brightness control on LED {led_id}...")

        # Set a nice purple color
        self.led.set_rgb_color(led_id, 128, 0, 255)
        print("🟣 Set base color: Purple RGB(128, 0, 255)")

        brightness_levels = [
            (255, "🌟 Maximum (100%)"),
            (192, "☀️ High (75%)"),
            (128, "🌤️ Medium (50%)"),
            (64, "🌙 Low (25%)"),
            (16, "🌑 Very Low (6%)"),
            (0, "⚫ Off (0%)"),
            (128, "🌤️ Back to Medium"),
        ]

        for brightness, description in brightness_levels:
            print(f"Setting brightness: {description} - {brightness}/255")
            self.led.set_brightness(led_id, brightness)

            # Verify brightness was set
            current = self.led.get_brightness(led_id)
            print(f"  ✓ Verified: {current}/255")
            time.sleep(1.2)

        self.wait_for_enter("Ready to test multi-LED static control?")

    def demo_multi_led_control(self):
        """Demo 4: Multi-LED control with animations."""
        self.print_section(
            "Demo 4: Multi-LED Control with Animations",
            "Setting different animations on multiple LEDs simultaneously",
        )

        if len(self.available_leds) == 1:
            print("Single LED system - demonstrating different animations sequentially")
            led_id = self.available_leds[0]

            animations = [
                ("Blinking red", lambda: self.led.blink_led(led_id, 255, 0, 0, 400)),
                ("Fading green", lambda: self.led.fade_led(led_id, 0, 255, 0, 600)),
                ("Rainbow cycle", lambda: self.led.rainbow_led(led_id, 800)),
                ("Static blue", lambda: self.led.static_led(led_id, 0, 0, 255)),
            ]

            for description, action in animations:
                print(f"LED {led_id}: {description}")
                action()
                self.led.set_brightness(led_id, 200)
                time.sleep(3)

        else:
            print(
                f"Setting different animations on {len(self.available_leds)} LEDs simultaneously..."
            )

            # Define animations for multiple LEDs
            animations = [
                (0, "Blinking red", lambda id: self.led.blink_led(id, 255, 0, 0, 400)),
                (1, "Fading green", lambda id: self.led.fade_led(id, 0, 255, 0, 600)),
                (2, "Rainbow cycle", lambda id: self.led.rainbow_led(id, 800)),
                (3, "Blinking yellow", lambda id: self.led.blink_led(id, 255, 255, 0, 300)),
                (4, "Fading magenta", lambda id: self.led.fade_led(id, 255, 0, 255, 700)),
                (5, "Static cyan", lambda id: self.led.static_led(id, 0, 255, 255)),
                (6, "Blinking orange", lambda id: self.led.blink_led(id, 255, 128, 0, 500)),
                (7, "Rainbow cycle", lambda id: self.led.rainbow_led(id, 1000)),
            ]

            for idx, led_id in enumerate(self.available_leds):
                if idx < len(animations):
                    anim_idx, description, action = animations[idx]
                    print(f"LED {led_id}: {description}")
                    action(led_id)
                    self.led.set_brightness(led_id, 180)
                    time.sleep(0.2)

            print(f"\nAll {len(self.available_leds)} LEDs now running different animations!")
            print("Watch them animate independently for 5 seconds...")
            time.sleep(5)

            # Stop animations by setting static colors
            print("\nStopping animations by setting static colors...")
            self.led.turn_off_all()
            time.sleep(1)

        self.wait_for_enter("Ready to test animation modes?")

    def demo_animation_modes(self):
        """Demo 5: Animation modes with kernel-based looping."""
        self.print_section(
            "Demo 5: Animation Modes",
            "Testing blink, fade, and rainbow modes with different timings",
        )

        led_id = self.available_leds[0]
        print(f"Testing animation modes on LED {led_id}...")
        print("Note: Animations loop continuously in the kernel driver\n")

        # Blink mode tests
        print("--- Blink Animation ---")
        print("Setting red blink at 500ms timing...")
        self.led.blink_led(led_id, 255, 0, 0, 500)
        self.led.set_brightness(led_id, 200)
        print("Watch the LED blink continuously for 3 seconds...")
        time.sleep(3)

        print("\nChanging to faster blink (200ms)...")
        self.led.blink_led(led_id, 255, 0, 0, 200)
        print("Notice the faster blinking rate...")
        time.sleep(3)

        print("\nChanging to slower blink (1000ms)...")
        self.led.blink_led(led_id, 255, 0, 0, 1000)
        print("Notice the slower blinking rate...")
        time.sleep(3)

        print("\nChanging color to green while still blinking at 1000ms...")
        self.led.blink_led(led_id, 0, 255, 0, 1000)
        time.sleep(3)

        self.wait_for_enter("Ready to test fade animation?")

        # Fade mode tests
        print("\n--- Fade Animation ---")
        print("Setting purple fade at 1000ms timing...")
        self.led.fade_led(led_id, 128, 0, 255, 1000)
        self.led.set_brightness(led_id, 200)
        print("Watch the LED smoothly fade in and out...")
        time.sleep(4)

        print("\nChanging to faster fade (400ms)...")
        self.led.fade_led(led_id, 128, 0, 255, 400)
        print("Notice the faster fading speed...")
        time.sleep(3)

        print("\nChanging color to cyan while fading at 400ms...")
        self.led.fade_led(led_id, 0, 255, 255, 400)
        time.sleep(3)

        print("\nChanging to slow fade (1000ms) with orange...")
        self.led.fade_led(led_id, 255, 128, 0, 1000)
        time.sleep(4)

        self.wait_for_enter("Ready to test rainbow animation?")

        # Rainbow mode tests
        print("\n--- Rainbow Animation ---")
        print("Setting rainbow cycle at 1000ms timing...")
        self.led.rainbow_led(led_id, 1000)
        self.led.set_brightness(led_id, 200)
        print("Watch the LED cycle through rainbow colors...")
        time.sleep(5)

        print("\nChanging to faster rainbow (300ms)...")
        self.led.rainbow_led(led_id, 300)
        print("Notice the faster color cycling...")
        time.sleep(4)

        print("\nChanging to slower rainbow (1500ms)...")
        self.led.rainbow_led(led_id, 1500)
        print("Notice the slower color transitions...")
        time.sleep(6)

        # Test switching between animation modes
        print("\n--- Animation Mode Switching ---")
        print("Switching from rainbow to blink...")
        self.led.blink_led(led_id, 255, 255, 0, 500)
        time.sleep(3)

        print("Switching from blink to fade...")
        self.led.fade_led(led_id, 255, 0, 255, 600)
        time.sleep(3)

        print("Switching from fade to rainbow...")
        self.led.rainbow_led(led_id, 800)
        time.sleep(4)

        print("Stopping animation with static color...")
        self.led.static_led(led_id, 0, 255, 0)
        self.led.set_brightness(led_id, 150)
        time.sleep(2)

        print("\nAnimation modes demonstration complete!")
        print("Key points:")
        print("  - Animations loop continuously in kernel")
        print("  - Timing can be changed dynamically (100-1000ms)")
        print("  - Animations can be switched without stopping")
        print("  - Static color stops animation")

        self.wait_for_enter("Ready to test LED triggers?")

    def demo_led_triggers(self):
        """Demo 6: Linux LED triggers."""
        self.print_section(
            "Demo 6: LED Triggers", "Testing heartbeat-rgb, breathing-rgb, and rainbow-rgb triggers"
        )

        led_id = self.available_leds[0]
        print(f"Testing LED triggers on LED {led_id}...")
        print("Note: Triggers are managed by the Linux LED subsystem\n")

        # Get available triggers
        print("--- Available Triggers ---")
        try:
            triggers = self.led.get_available_triggers(led_id)
            print(f"Available triggers: {', '.join(triggers)}")
        except Exception as e:
            print(f"Could not read available triggers: {e}")

        # Test heartbeat trigger
        print("\n--- Heartbeat Trigger ---")
        print("Setting heartbeat-rgb trigger...")
        self.led.set_trigger(led_id, "heartbeat-rgb")
        current_trigger = self.led.get_trigger(led_id)
        print(f"Current trigger: {current_trigger}")
        print("Watch the LED pulse like a heartbeat...")
        time.sleep(5)

        self.wait_for_enter("Ready to test breathing trigger?")

        # Test breathing trigger
        print("\n--- Breathing Trigger ---")
        print("Setting breathing-rgb trigger...")
        self.led.set_trigger(led_id, "breathing-rgb")
        current_trigger = self.led.get_trigger(led_id)
        print(f"Current trigger: {current_trigger}")
        print("Watch the LED breathe in and out smoothly...")
        time.sleep(5)

        self.wait_for_enter("Ready to test rainbow trigger?")

        # Test rainbow trigger
        print("\n--- Rainbow Trigger ---")
        print("Setting rainbow-rgb trigger...")
        self.led.set_trigger(led_id, "rainbow-rgb")
        current_trigger = self.led.get_trigger(led_id)
        print(f"Current trigger: {current_trigger}")
        print("Watch the LED cycle through rainbow colors...")
        time.sleep(6)

        # Test trigger switching
        print("\n--- Trigger Switching ---")
        print("Switching between triggers...")

        print("Heartbeat...")
        self.led.set_trigger(led_id, "heartbeat-rgb")
        time.sleep(3)

        print("Breathing...")
        self.led.set_trigger(led_id, "breathing-rgb")
        time.sleep(3)

        print("Rainbow...")
        self.led.set_trigger(led_id, "rainbow-rgb")
        time.sleep(3)

        # Disable trigger
        print("\n--- Disabling Trigger ---")
        print("Setting trigger to 'none' to disable automatic control...")
        self.led.set_trigger(led_id, "none")
        current_trigger = self.led.get_trigger(led_id)
        print(f"Current trigger: {current_trigger}")

        print("Setting manual static color (blue)...")
        self.led.static_led(led_id, 0, 0, 255)
        self.led.set_brightness(led_id, 150)
        time.sleep(2)

        print("\nLED triggers demonstration complete!")
        print("Key points:")
        print("  - Triggers are kernel-based LED effects")
        print("  - Multiple trigger types available")
        print("  - Use 'none' trigger to regain manual control")
        print("  - Triggers can be switched dynamically")

        self.wait_for_enter("Ready to test timing control?")

    def demo_timing_control(self):
        """Demo 7: Dynamic timing changes."""
        self.print_section(
            "Demo 7: Dynamic Timing Control", "Changing animation timing while running"
        )

        led_id = self.available_leds[0]
        print(f"Testing dynamic timing control on LED {led_id}...")
        print("Note: Timing changes apply immediately\n")

        # Start with blink at medium speed
        print("--- Blink Timing Control ---")
        print("Starting with 500ms blink (medium speed)...")
        self.led.blink_led(led_id, 255, 0, 0, 500)
        self.led.set_brightness(led_id, 200)
        time.sleep(3)

        print("Changing to 100ms (very fast blink)...")
        self.led.blink_led(led_id, 255, 0, 0, 100)
        print("Notice the immediate timing change...")
        time.sleep(3)

        print("Changing to 1000ms (slow blink)...")
        self.led.blink_led(led_id, 255, 0, 0, 1000)
        print("Notice the slower timing...")
        time.sleep(4)

        print("Changing back to 300ms (fast blink)...")
        self.led.blink_led(led_id, 255, 0, 0, 300)
        time.sleep(3)

        self.wait_for_enter("Ready to test fade timing control?")

        # Fade timing control
        print("\n--- Fade Timing Control ---")
        print("Starting with 800ms fade...")
        self.led.fade_led(led_id, 0, 255, 0, 800)
        time.sleep(3)

        print("Changing to 200ms (rapid fade)...")
        self.led.fade_led(led_id, 0, 255, 0, 200)
        print("Notice the faster fading...")
        time.sleep(3)

        print("Changing to 1000ms (slow fade)...")
        self.led.fade_led(led_id, 0, 255, 0, 1000)
        print("Notice the slower fading...")
        time.sleep(4)

        self.wait_for_enter("Ready to test rainbow timing control?")

        # Rainbow timing control
        print("\n--- Rainbow Timing Control ---")
        print("Starting with 600ms rainbow cycle...")
        self.led.rainbow_led(led_id, 600)
        time.sleep(4)

        print("Changing to 150ms (fast rainbow)...")
        self.led.rainbow_led(led_id, 150)
        print("Notice the rapid color changes...")
        time.sleep(3)

        print("Changing to 1000ms (slow rainbow)...")
        self.led.rainbow_led(led_id, 1000)
        print("Notice the smooth color transitions...")
        time.sleep(4)

        # Stop animation
        print("\nStopping animation with static color...")
        self.led.static_led(led_id, 255, 255, 255)
        self.led.set_brightness(led_id, 100)
        time.sleep(1)

        print("\nTiming control demonstration complete!")
        print("Key points:")
        print("  - Timing range: 100-1000ms")
        print("  - Changes apply immediately")
        print("  - Works with blink, fade, and rainbow modes")
        print("  - Kernel-based timing for precision")

        self.wait_for_enter("Ready to test convenience methods?")

    def demo_convenience_methods(self):
        """Demo 8: Convenience methods."""
        self.print_section(
            "Demo 8: Convenience Methods", "Testing bulk operations and helper functions"
        )

        if len(self.available_leds) > 1:
            print(f"🎯 Testing bulk operations on {len(self.available_leds)} LEDs...")

            print("🌟 Using set_color_all() - All LEDs to white")
            self.led.set_color_all(255, 255, 255)
            time.sleep(1.5)

            print("🔅 Using set_brightness_all() - All LEDs to 30%")
            self.led.set_brightness_all(76)
            time.sleep(1.5)

            print("🎨 Setting different colors individually...")
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
            for i, led_id in enumerate(self.available_leds[:4]):
                if i < len(colors):
                    r, g, b = colors[i]
                    self.led.set_rgb_color(led_id, r, g, b)
                    print(f"  LED {led_id}: RGB({r}, {g}, {b})")
            time.sleep(2)

            print("⚫ Using turn_off_all() - All LEDs off")
            self.led.turn_off_all()
            time.sleep(1)
        else:
            print("ℹ️ Single LED system - testing individual convenience methods...")
            led_id = self.available_leds[0]

            print(f"🔸 static_led() - Static purple on LED {led_id}")
            self.led.static_led(led_id, 128, 0, 255)
            time.sleep(1.5)

            print(f"⚫ turn_off() - Turn off LED {led_id}")
            self.led.turn_off(led_id)
            time.sleep(1)

        self.wait_for_enter("Ready to test error handling?")

    def demo_error_handling(self):
        """Demo 9: Error handling."""
        self.print_section("Demo 9: Error Handling", "Testing input validation and error messages")

        valid_led = self.available_leds[0]
        print("Testing error handling and validation...")

        test_cases = [
            ("Invalid LED ID", lambda: self.led.set_rgb_color(999, 255, 0, 0)),
            ("Invalid RGB value (>255)", lambda: self.led.set_rgb_color(valid_led, 300, 0, 0)),
            ("Invalid RGB value (<0)", lambda: self.led.set_rgb_color(valid_led, -10, 0, 0)),
            ("Invalid brightness (>255)", lambda: self.led.set_brightness(valid_led, 300)),
            ("Invalid brightness (<0)", lambda: self.led.set_brightness(valid_led, -50)),
            (
                "Invalid animation mode",
                lambda: self.led.set_animation_mode(valid_led, "invalid_mode"),
            ),
            ("Invalid trigger", lambda: self.led.set_trigger(valid_led, "invalid-trigger")),
        ]

        for description, test_func in test_cases:
            try:
                test_func()
                print(f"FAIL: {description}: Should have raised an error!")
            except LEDError as e:
                print(f"PASS: {description}: Correctly caught - {str(e)[:60]}...")
            except Exception as e:
                print(f"WARN: {description}: Unexpected error type - {type(e).__name__}: {e}")

        self.wait_for_enter("Ready to test sudo mode switching?")

    def demo_sudo_mode(self):
        """Demo 10: Sudo mode switching."""
        self.print_section(
            "Demo 10: Sudo Mode Management", "Testing sudo mode switching functionality"
        )

        print("🔐 Testing sudo mode switching...")

        original_mode = self.led.use_sudo
        print(f"📊 Current sudo mode: {original_mode}")

        # Switch mode
        new_mode = not original_mode
        print(f"🔄 Switching to sudo mode: {new_mode}")
        self.led.set_sudo_mode(new_mode)

        if self.led.use_sudo == new_mode:
            print("✅ Sudo mode successfully changed")
        else:
            print("❌ Failed to change sudo mode")

        # Switch back
        print(f"🔄 Restoring original sudo mode: {original_mode}")
        self.led.set_sudo_mode(original_mode)
        print(f"📊 Final sudo mode: {self.led.use_sudo}")

        self.wait_for_enter("Ready for the final cleanup demo?")

    def demo_cleanup(self):
        """Demo 11: Cleanup and summary."""
        self.print_section("Demo 11: Cleanup & Summary", "Proper cleanup and demonstration summary")

        print("🧹 Performing comprehensive cleanup...")

        # Turn off all LEDs
        print(f"⚫ Turning off all {len(self.available_leds)} LEDs...")
        self.led.turn_off_all()

        print("\nDemo Summary:")
        print(f"  LED count: {len(self.available_leds)}")
        print("  RGB colors: Primary and secondary colors")
        print("  Brightness: Multiple levels (0-255)")
        print("  Animations: Blink, fade, rainbow modes")
        print("  LED triggers: Heartbeat, breathing, rainbow")
        print("  Timing control: Dynamic timing changes (100-1000ms)")
        print("  Multi-LED: Individual and bulk operations")
        print("  Convenience: Helper functions")
        print("  Error handling: Input validation")
        print("  Sudo mode: Permission management")
        print("  Cleanup: Proper resource cleanup")

        print("\nAll LED functionality demonstrated successfully!")

    def run_full_demo(self):
        """Run the complete interactive demo."""
        print("Interactive LED Demo and Test Suite")
        print("=" * 60)
        print("This demo walks you through comprehensive LED functionality")
        print("Press Enter between sections to continue")
        print("Press Ctrl+C anytime to exit safely")

        try:
            self.wait_for_enter("Ready to start the LED demo?")

            # Run all demo sections
            self.demo_initialization()  # Demo 1
            self.demo_rgb_colors()  # Demo 2
            self.demo_brightness_control()  # Demo 3
            self.demo_multi_led_control()  # Demo 4 - Updated with animations
            self.demo_animation_modes()  # Demo 5 - NEW
            self.demo_led_triggers()  # Demo 6 - NEW
            self.demo_timing_control()  # Demo 7 - NEW
            self.demo_convenience_methods()  # Demo 8
            self.demo_error_handling()  # Demo 9
            self.demo_sudo_mode()  # Demo 10
            self.demo_cleanup()  # Demo 11

            print("\nDemo completed successfully!")
            print("Thank you for trying the LED module!")

        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
            self.cleanup_on_exit()
        except LEDError as e:
            print(f"\nLED Error: {e}")
            if "Permission denied" in str(e):
                print("Tip: Run with proper sudo permissions")
            self.cleanup_on_exit()
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            self.cleanup_on_exit()

    def cleanup_on_exit(self):
        """Cleanup when exiting unexpectedly."""
        if self.led and self.available_leds:
            print("🧹 Emergency cleanup...")
            try:
                self.led.turn_off_all()
                print("✅ Cleanup completed")
            except Exception:
                print("⚠️ Cleanup failed - LEDs may still be active")


def main():
    """Main function."""

    # Set up signal handler for clean exit
    def signal_handler(sig, frame):
        print("\n🛑 Received exit signal...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the demo
    demo = InteractiveLEDDemo()
    demo.run_full_demo()

    return 0


if __name__ == "__main__":
    sys.exit(main())
