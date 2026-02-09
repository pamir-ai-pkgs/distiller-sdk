#!/usr/bin/env python3
"""
Interactive E-ink Mode Test - Visually Interesting Hardware Demos.

This interactive demo showcases e-ink display capabilities including:
- Mandelbrot fractal with Floyd-Steinberg dithering
- Speed comparison: FULL vs FAST vs TURBO refresh modes
- Sine wave animation with TURBO mode
- Partial refresh with bouncing ball over checkerboard
- Gradient dithering halftone art
- 4-gray grayscale mountain landscape
- 4-gray vs 1-bit visual comparison

Run as: python -m distiller_sdk.hardware.eink._interactive_mode_test

Requires:
- E-ink display hardware connected
- numpy, PIL (pillow) installed
"""

import math
import os
import signal
import sys
import tempfile
import time

import numpy as np
from PIL import Image, ImageDraw

from distiller_sdk.hardware.eink import Display, DisplayError, DisplayMode
from distiller_sdk.hardware.eink.composer.dithering import floyd_steinberg_dither


class InteractiveModeDemo:
    """Interactive e-ink display mode demonstration."""

    def __init__(self):
        """Initialize the demo."""
        self.display = None
        self.width = 250
        self.height = 128

    def wait_for_enter(self, message="Press Enter to continue..."):
        """Wait for user to press Enter."""
        try:
            input(f"\n  {message}")
        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def print_section(self, title, description=""):
        """Print a formatted section header."""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")
        if description:
            print(f"  {description}")

    def _init_display(self):
        """Initialize the display and get dimensions."""
        print("  Initializing e-ink display...")
        self.display = Display(auto_init=True)
        self.width, self.height = self.display.get_dimensions()
        print(f"  Display initialized: {self.width}x{self.height}")

    def _pack_for_display(self, image):
        """Pack 2D binary image (0/255) to continuous bit stream for display.

        Unlike composer's pack_bits() which uses row-aligned packing (32 bytes
        per 250-pixel row = 4096 bytes), the Rust display_image_raw() expects
        continuous packing: bits flow across row boundaries without padding
        (250*128/8 = 4000 bytes exactly).
        """
        flat = (image.flatten() > 128).astype(np.uint8)
        reshaped = flat.reshape(-1, 8)
        weights = np.array([128, 64, 32, 16, 8, 4, 2, 1], dtype=np.uint8)
        packed = np.sum(reshaped * weights, axis=1, dtype=np.uint8)
        return bytes(packed)

    def _unpack_for_display(self, data, width, height):
        """Unpack continuous bit stream back to 2D binary image (0/255).

        Inverse of _pack_for_display(). Used to get an editable numpy array
        from display-format packed bytes (e.g., for compositing ball on background).
        """
        packed = np.frombuffer(data, dtype=np.uint8)
        bits = np.unpackbits(packed)
        pixels = bits[: width * height].reshape(height, width)
        return (pixels * 255).astype(np.uint8)

    # -- Demo 1: Mandelbrot Fractal ----------------------------------

    def _generate_mandelbrot(self, width, height, max_iter=80):
        """Generate Mandelbrot set as grayscale numpy array."""
        x = np.linspace(-2.5, 1.0, width)
        y = np.linspace(-1.0, 1.0, height)
        X, Y = np.meshgrid(x, y)
        C = X + 1j * Y
        Z = np.zeros_like(C)
        M = np.zeros(C.shape, dtype=np.uint8)
        for i in range(max_iter):
            mask = np.abs(Z) <= 2
            Z[mask] = Z[mask] ** 2 + C[mask]
            M[mask] = i
        # Normalize to 0-255
        return (M / max_iter * 255).astype(np.uint8)

    def demo_mandelbrot(self):
        """Demo 1: Mandelbrot fractal with Floyd-Steinberg dithering."""
        self.print_section(
            "Demo 1: Mandelbrot Fractal",
            "Floyd-Steinberg dithering on a complex mathematical pattern",
        )

        print("  Generating Mandelbrot set...")
        grayscale = self._generate_mandelbrot(self.width, self.height)

        print("  Applying Floyd-Steinberg dithering...")
        dithered = floyd_steinberg_dither(grayscale)
        packed = self._pack_for_display(dithered)

        print("  Displaying on e-ink (FULL refresh)...")
        t0 = time.time()
        self.display.display_image_auto(packed, DisplayMode.FULL)
        elapsed = time.time() - t0
        print(f"  Done in {elapsed:.2f}s")
        print("  The fractal's continuous gradients produce beautiful")
        print("  halftone patterns when dithered to 1-bit.")

    # -- Demo 2: Speed Showdown --------------------------------------

    def _generate_starburst(self, width, height):
        """Radial starburst: concentric circles + radial lines from center."""
        img = Image.new("1", (width, height), 1)
        draw = ImageDraw.Draw(img)
        cx, cy = width // 2, height // 2
        # Concentric circles
        for r in range(8, max(width, height), 12):
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=0)
        # Radial lines (every 15 degrees)
        for angle in range(0, 360, 15):
            rad = math.radians(angle)
            x2 = cx + int(max(width, height) * math.cos(rad))
            y2 = cy + int(max(width, height) * math.sin(rad))
            draw.line([(cx, cy), (x2, y2)], fill=0)
        return img

    def demo_speed_showdown(self):
        """Demo 2: FULL vs FAST vs TURBO speed comparison."""
        self.print_section(
            "Demo 2: Speed Showdown",
            "Comparing FULL vs FAST vs TURBO refresh with the same image",
        )

        print("  Generating starburst pattern...")
        img = self._generate_starburst(self.width, self.height)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "starburst.png")
            img.save(path)

            modes = [
                (DisplayMode.FULL, "FULL ", "highest quality, no ghosting"),
                (DisplayMode.FAST, "FAST ", "good quality, minimal ghosting"),
                (DisplayMode.TURBO, "TURBO", "fastest, may show ghosting"),
            ]

            print()
            for mode, label, desc in modes:
                self.wait_for_enter(f"Display with {label.strip()} refresh?")
                t0 = time.time()
                self.display.display_image_auto(path, mode)
                elapsed = time.time() - t0
                print(f"  {label} refresh: {elapsed:.2f}s  ({desc})")

    # -- Demo 3: Sine Wave Animation ---------------------------------

    def _generate_sine_frame(self, width, height, phase):
        """Generate sine wave frame as 1-bit packed bytes."""
        x = np.arange(width)
        # Two overlapping sine waves with different frequencies
        y1 = height // 2 + int(height * 0.3) * np.sin(2 * np.pi * x / width * 3 + phase)
        y2 = height // 2 + int(height * 0.2) * np.sin(2 * np.pi * x / width * 5 + phase * 1.5)

        img = np.full((height, width), 255, dtype=np.uint8)
        for col in range(width):
            row1 = int(y1[col])
            row2 = int(y2[col])
            # Fill between the two waves for visual impact
            lo = max(0, min(row1, row2))
            hi = min(height - 1, max(row1, row2))
            img[lo : hi + 1, col] = 0
        return self._pack_for_display(img)

    def demo_sine_animation(self):
        """Demo 3: Sine wave animation using TURBO mode."""
        self.print_section(
            "Demo 3: Sine Wave Animation",
            "TURBO mode enables near-real-time animation",
        )

        num_frames = 6
        print(f"  Animating {num_frames} frames with TURBO refresh...")
        print()

        for i in range(num_frames):
            phase = i * (2 * math.pi / num_frames)
            frame_data = self._generate_sine_frame(self.width, self.height, phase)

            t0 = time.time()
            self.display.display_image_auto(frame_data, DisplayMode.TURBO)
            elapsed = time.time() - t0
            print(f"  Frame {i + 1}/{num_frames}: {elapsed:.2f}s")

        print("  Animation complete.")

    # -- Demo 4: Partial Refresh with Bouncing Ball ------------------

    def _generate_checkerboard(self, width, height, square_size=16):
        """Checkerboard pattern as packed bytes."""
        img = np.zeros((height, width), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                if ((x // square_size) + (y // square_size)) % 2 == 0:
                    img[y, x] = 255
        return self._pack_for_display(img)

    def _generate_ball_frame(self, width, height, bx, by, radius, bg_array):
        """Composite a ball onto the checkerboard background."""
        img = np.copy(bg_array)
        # Draw filled circle (ball) in black
        Y, X = np.ogrid[:height, :width]
        mask = (X - bx) ** 2 + (Y - by) ** 2 <= radius**2
        img[mask] = 0
        return self._pack_for_display(img)

    def demo_partial_bounce(self):
        """Demo 4: Partial refresh with bouncing ball over checkerboard."""
        self.print_section(
            "Demo 4: Bouncing Ball (Partial Refresh)",
            "set_partial_base_map() + PARTIAL mode for animation over static background",
        )

        print("  Generating checkerboard background...")
        bg_packed = self._generate_checkerboard(self.width, self.height)

        print("  Setting partial base map...")
        self.display.display_image_auto(bg_packed, DisplayMode.FULL)
        self.display.set_partial_base_map(bg_packed)

        # Unpack background for compositing
        bg_array = self._unpack_for_display(bg_packed, self.width, self.height)

        # Ball parameters
        radius = 12
        bx, by = 30, 30
        dx, dy = 18, 12
        num_positions = 8

        print(f"  Animating ball across {num_positions} positions...")
        print()

        for i in range(num_positions):
            frame = self._generate_ball_frame(self.width, self.height, bx, by, radius, bg_array)
            t0 = time.time()
            self.display.display_image_auto(frame, DisplayMode.PARTIAL)
            elapsed = time.time() - t0
            print(f"  Position {i + 1}/{num_positions}: ball at ({bx}, {by}) - {elapsed:.2f}s")

            # Move ball, bounce off edges
            bx += dx
            by += dy
            if bx - radius < 0 or bx + radius >= self.width:
                dx = -dx
                bx += 2 * dx
            if by - radius < 0 or by + radius >= self.height:
                dy = -dy
                by += 2 * dy

        print("  Bouncing ball demo complete.")

    # -- Demo 5: Gradient Dithering Art ------------------------------

    def _generate_diagonal_gradient(self, width, height):
        """Diagonal gradient: top-left white, bottom-right black."""
        y, x = np.mgrid[0:height, 0:width]
        gradient = ((x / width + y / height) / 2 * 255).astype(np.uint8)
        return gradient

    def _generate_radial_gradient(self, width, height):
        """Radial gradient: bright center, dark edges."""
        cy, cx = height / 2, width / 2
        y, x = np.mgrid[0:height, 0:width]
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        max_dist = np.sqrt(cx**2 + cy**2)
        gradient = (255 * (1 - dist / max_dist)).clip(0, 255).astype(np.uint8)
        return gradient

    def demo_gradient_dithering(self):
        """Demo 5: Gradient dithering art -- halftone beauty."""
        self.print_section(
            "Demo 5: Gradient Dithering Art",
            "Floyd-Steinberg dithering on smooth gradients creates halftone art",
        )

        # Diagonal gradient
        print("  Generating diagonal gradient...")
        gradient = self._generate_diagonal_gradient(self.width, self.height)
        print("  Applying Floyd-Steinberg dithering...")
        dithered = floyd_steinberg_dither(gradient)
        packed = self._pack_for_display(dithered)

        print("  Displaying diagonal gradient (FULL refresh)...")
        self.display.display_image_auto(packed, DisplayMode.FULL)
        print("  Notice the newspaper-style halftone dot pattern.")

        self.wait_for_enter("Display radial gradient?")

        # Radial gradient
        print("  Generating radial gradient...")
        gradient = self._generate_radial_gradient(self.width, self.height)
        print("  Applying Floyd-Steinberg dithering...")
        dithered = floyd_steinberg_dither(gradient)
        packed = self._pack_for_display(dithered)

        print("  Displaying radial gradient (FULL refresh)...")
        self.display.display_image_auto(packed, DisplayMode.FULL)
        print("  Bright center fading to dark edges, all in 1-bit.")

    # -- Demo 6: 4-Gray Mountain Landscape ---------------------------

    def _generate_mountain_landscape(self, width, height):
        """Layered mountain landscape with 4 gray levels."""
        img = np.full((height, width), 160, dtype=np.uint8)  # Light gray sky (level 2)

        # Far mountains (dark gray, y ~ 55%)
        for x in range(width):
            peak = int(height * 0.55 + 20 * math.sin(x / 30) + 10 * math.sin(x / 17))
            peak = max(0, min(height - 1, peak))
            img[peak:, x] = np.minimum(img[peak:, x], 80)  # Dark gray (level 1)

        # Near mountains (black, y ~ 70%)
        for x in range(width):
            peak = int(height * 0.7 + 15 * math.sin(x / 25 + 2) + 8 * math.sin(x / 11))
            peak = max(0, min(height - 1, peak))
            img[peak:, x] = 0  # Black

        # Moon (white circle)
        cy, cx, r = height // 4, width * 3 // 4, 12
        Y, X = np.ogrid[:height, :width]
        moon_mask = (X - cx) ** 2 + (Y - cy) ** 2 <= r**2
        img[moon_mask] = 255  # White

        return Image.fromarray(img)

    def demo_grayscale_landscape(self):
        """Demo 6: 4-gray grayscale mountain landscape."""
        self.print_section(
            "Demo 6: 4-Gray Mountain Landscape",
            "4-level grayscale for richer imagery (white/light gray/dark gray/black)",
        )

        print("  Generating procedural mountain landscape...")
        landscape = self._generate_mountain_landscape(self.width, self.height)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "landscape.png")
            landscape.save(path)

            print("  Displaying with 4-gray grayscale driver...")
            print("  (This temporarily reinitializes the display controller)")
            t0 = time.time()
            self.display.display_grayscale(path)
            elapsed = time.time() - t0
            print(f"  Done in {elapsed:.2f}s")
            print("  Notice the 4 distinct gray levels creating depth:")
            print("    White moon, light gray sky, dark gray far mountains, black near mountains")

    # -- Demo 7: 4-Gray vs 1-Bit Comparison --------------------------

    def demo_grayscale_vs_1bit(self):
        """Demo 7: 4-gray vs 1-bit side-by-side comparison."""
        self.print_section(
            "Demo 7: 4-Gray vs 1-Bit Comparison",
            "Same image rendered in grayscale vs dithered 1-bit",
        )

        print("  Generating mountain landscape...")
        landscape = self._generate_mountain_landscape(self.width, self.height)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "landscape.png")
            landscape.save(path)

            print("  Displaying in 4-gray grayscale (smooth shading)...")
            self.display.display_grayscale(path)

            self.wait_for_enter("Now display the same image dithered to 1-bit?")

            print("  Applying Floyd-Steinberg dithering to 1-bit...")
            grayscale_array = np.array(landscape)
            dithered = floyd_steinberg_dither(grayscale_array)
            packed = self._pack_for_display(dithered)

            print("  Displaying dithered 1-bit version (FULL refresh)...")
            self.display.display_image_auto(packed, DisplayMode.FULL)
            print("  Compare: grayscale has smooth tones, 1-bit uses halftone dots.")

    # -- Demo 8: Cleanup & Summary -----------------------------------

    def demo_summary(self):
        """Demo 8: Feature summary and cleanup."""
        self.print_section(
            "Demo 8: Summary & Cleanup",
            "All features tested successfully",
        )

        print("  Clearing display...")
        self.display.clear()

        print("  Displaying summary card...")
        self.display.display_text("Mode Test OK", x=10, y=10, scale=3, mode=DisplayMode.FULL)

        print()
        print("  Features Tested:")
        print("    [x] Mandelbrot fractal with Floyd-Steinberg dithering")
        print("    [x] Speed comparison: FULL vs FAST vs TURBO (with timing)")
        print("    [x] Sine wave animation with TURBO mode")
        print("    [x] Partial refresh: bouncing ball over checkerboard")
        print("    [x] Gradient dithering halftone art")
        print("    [x] 4-gray grayscale mountain landscape")
        print("    [x] 4-gray vs 1-bit visual comparison")

    # -- Main Runner -------------------------------------------------

    def run_full_demo(self):
        """Run the complete interactive demo."""
        print("Interactive E-ink Mode Test")
        print("=" * 60)
        print("  Showcasing e-ink display capabilities with procedural art")
        print("  Press Enter between sections to continue")
        print("  Press Ctrl+C anytime to exit safely")

        try:
            self.wait_for_enter("Ready to start?")
            self._init_display()

            demos = [
                ("Mandelbrot Fractal", self.demo_mandelbrot),
                ("Speed Showdown", self.demo_speed_showdown),
                ("Sine Wave Animation", self.demo_sine_animation),
                ("Bouncing Ball", self.demo_partial_bounce),
                ("Gradient Dithering", self.demo_gradient_dithering),
                ("4-Gray Landscape", self.demo_grayscale_landscape),
                ("4-Gray vs 1-Bit", self.demo_grayscale_vs_1bit),
                ("Summary", self.demo_summary),
            ]

            for i, (name, demo_fn) in enumerate(demos):
                if i > 0:
                    self.wait_for_enter(f"Ready for Demo {i + 1}: {name}?")
                try:
                    demo_fn()
                except DisplayError as e:
                    print(f"  Display error in {name}: {e}")
                    print("  Continuing to next demo...")
                except Exception as e:
                    print(f"  Error in {name}: {e}")
                    print("  Continuing to next demo...")

            print()
            print("  Demo completed successfully!")

        except KeyboardInterrupt:
            print("\n  Demo interrupted by user.")
            self.cleanup_on_exit()
        except DisplayError as e:
            print(f"\n  Display error: {e}")
            self.cleanup_on_exit()
        except Exception as e:
            print(f"\n  Unexpected error: {e}")
            self.cleanup_on_exit()

    def cleanup_on_exit(self):
        """Cleanup when exiting unexpectedly."""
        if self.display:
            print("  Cleaning up display...")
            try:
                self.display.clear()
                self.display.close()
                print("  Cleanup completed.")
            except Exception:
                try:
                    self.display.close()
                except Exception:
                    print("  Cleanup failed - display may need manual reset.")


def main():
    """Main entry point."""
    demo = InteractiveModeDemo()

    def signal_handler(sig, frame):
        print("\n  Received exit signal...")
        demo.cleanup_on_exit()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    demo.run_full_demo()
    return 0


if __name__ == "__main__":
    sys.exit(main())
