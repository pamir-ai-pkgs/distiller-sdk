#!/usr/bin/env python3
"""
Diagnostic test for e-ink display orientation and rendering.

Runs through each display pipeline with asymmetric test images (letter "F")
to verify correct display output.

Usage:
    python -m distiller_sdk.hardware.eink._diagnostic_test

Requires physical e-ink hardware connected.
"""

import sys
import tempfile
import os

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

from distiller_sdk.hardware.eink import Display, DisplayMode


def create_f_image(width: int, height: int, label: str = "") -> Image.Image:
    """
    Create a 1-bit image with an asymmetric letter 'F' that reveals
    orientation issues in any direction.

    The F is drawn in the top-left quadrant with:
    - Horizontal bar at top
    - Shorter horizontal bar in middle
    - Vertical bar on left side

    A small dot in the top-right corner serves as an additional orientation marker.
    """
    img = Image.new("1", (width, height), 1)  # White background (paper)
    draw = ImageDraw.Draw(img)

    # Scale F proportionally to image size
    margin_x = width // 8
    margin_y = height // 8
    f_width = width // 2
    f_height = height * 3 // 4
    bar_thickness = max(height // 12, 4)

    # Vertical stroke (left side of F)
    draw.rectangle(
        [margin_x, margin_y, margin_x + bar_thickness, margin_y + f_height],
        fill=0,
    )
    # Top horizontal stroke (full width)
    draw.rectangle(
        [margin_x, margin_y, margin_x + f_width, margin_y + bar_thickness],
        fill=0,
    )
    # Middle horizontal stroke (shorter)
    draw.rectangle(
        [margin_x, margin_y + f_height // 3,
         margin_x + f_width * 2 // 3, margin_y + f_height // 3 + bar_thickness],
        fill=0,
    )

    # Orientation dot in top-right corner
    dot_size = max(width // 16, 3)
    draw.ellipse(
        [width - margin_x - dot_size, margin_y,
         width - margin_x, margin_y + dot_size],
        fill=0,
    )

    # Label text at bottom if provided
    if label:
        try:
            draw.text((margin_x, height - margin_y - 10), label, fill=0)
        except Exception:
            pass  # Skip if font issues

    return img


def run_test(display, test_id: str, description: str, action_fn, question: str):
    """Run a single diagnostic test with user feedback."""
    print(f"\n{'='*60}")
    print(f"TEST {test_id}: {description}")
    print(f"{'='*60}")

    input("  Press Enter to run this test...")

    try:
        display.clear()
        action_fn()
    except Exception as e:
        print(f"  ERROR: {e}")
        return f"ERROR: {e}"

    print(f"\n  Question: {question}")
    result = input("  Your answer (or press Enter to skip): ").strip()
    return result if result else "skipped"


def main():
    print("=" * 60)
    print("E-INK DISPLAY DIAGNOSTIC TEST")
    print("=" * 60)
    print()
    print("This script tests each display pipeline to verify")
    print("correct rendering on the 250x128 landscape display.")
    print()
    print("For each test, look at the physical display and answer")
    print("what you see. The letter 'F' is used because it's")
    print("asymmetric - you can detect orientation issues by how")
    print("it appears.")
    print()
    print("Correct orientation: F should look like a normal letter F")
    print("  - Vertical bar on LEFT")
    print("  - Top bar extends RIGHT")
    print("  - Middle bar extends RIGHT (shorter than top)")
    print("  - Small dot in TOP-RIGHT corner")
    print()

    input("Press Enter to initialize display hardware...")

    try:
        display = Display()
    except Exception as e:
        print(f"Failed to initialize display: {e}")
        sys.exit(1)

    width, height = display.get_dimensions()
    print(f"Display dimensions: {width}x{height}")

    results = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test images
        landscape_path = os.path.join(tmpdir, "landscape_f.png")

        # Landscape image: matches display dimensions (250x128)
        landscape_img = create_f_image(width, height, f"{width}x{height}")
        landscape_img.save(landscape_path)

        # ---- Test 1a: display_image_auto with landscape image ----
        results["1a"] = run_test(
            display, "1a",
            f"display_image_auto(landscape_{width}x{height}.png)",
            lambda: display.display_image_auto(landscape_path),
            "Is the F upright and correctly oriented? (yes/no/describe)",
        )

        # ---- Test 1b: display_image_auto with inverted colors ----
        results["1b"] = run_test(
            display, "1b",
            "display_image_auto(landscape.png, invert_colors=True)",
            lambda: display.display_image_auto(landscape_path, invert_colors=True),
            "Is the F upright with inverted colors (white F on black background)? (yes/no/describe)",
        )

        # ---- Test 1c: display_image_auto with partial refresh ----
        results["1c"] = run_test(
            display, "1c",
            "display_image_auto(landscape.png, mode=PARTIAL)",
            lambda: display.display_image_auto(landscape_path, mode=DisplayMode.PARTIAL),
            "Is the F displayed correctly with partial refresh? (yes/no/describe)",
        )

        # ---- Test 2a: display_text at origin ----
        results["2a"] = run_test(
            display, "2a",
            "display_text('TOP-LEFT', x=0, y=0, scale=2)",
            lambda: display.display_text("TOP-LEFT", x=0, y=0, scale=2),
            "Is the text at top-left and readable left-to-right? (yes/no/describe)",
        )

        # ---- Test 2b: display_text centered ----
        results["2b"] = run_test(
            display, "2b",
            "display_text('HELLO', x=50, y=50, scale=3)",
            lambda: display.display_text("HELLO", x=50, y=50, scale=3),
            "Is the text readable left-to-right? (yes/no/describe)",
        )

        # ---- Test 2c: display_text at top-right ----
        results["2c"] = run_test(
            display, "2c",
            "display_text('TR', x=220, y=0, scale=2)",
            lambda: display.display_text("TR", x=220, y=0, scale=2),
            "Is 'TR' at the top-right corner? (yes/no/describe)",
        )

        # ---- Test 2d: display_text at bottom-left ----
        results["2d"] = run_test(
            display, "2d",
            "display_text('BL', x=0, y=96, scale=2)",
            lambda: display.display_text("BL", x=0, y=96, scale=2),
            "Is 'BL' at the bottom-left corner? (yes/no/describe)",
        )

        # ---- Test 2e: display_text at bottom-right ----
        results["2e"] = run_test(
            display, "2e",
            "display_text('BR', x=220, y=96, scale=2)",
            lambda: display.display_text("BR", x=220, y=96, scale=2),
            "Is 'BR' at the bottom-right corner? (yes/no/describe)",
        )

        # ---- Test 2f: display_text centered ----
        results["2f"] = run_test(
            display, "2f",
            "display_text('CENTER', x=90, y=56, scale=2)",
            lambda: display.display_text("CENTER", x=90, y=56, scale=2),
            "Is 'CENTER' roughly centered on the display? (yes/no/describe)",
        )

    # ---- Summary ----
    print("\n" + "=" * 60)
    print("DIAGNOSTIC RESULTS SUMMARY")
    print("=" * 60)

    for test_id, result in results.items():
        print(f"  Test {test_id}: {result}")

    print()
    print("Key findings to report:")
    print("  1. Does display_image_auto show F correctly? (Test 1a)")
    print("  2. Does invert_colors work? (Test 1b)")
    print("  3. Does partial refresh work? (Test 1c)")
    print("  4. Is display_text readable at origin? (Test 2a)")
    print("  5. Is display_text readable at offset position? (Test 2b)")
    print("  6. Is display_text correct at top-right? (Test 2c)")
    print("  7. Is display_text correct at bottom-left? (Test 2d)")
    print("  8. Is display_text correct at bottom-right? (Test 2e)")
    print("  9. Is display_text centered correctly? (Test 2f)")

    # Clean up
    display.clear()
    display.close()
    print("\nDiagnostic complete. Display cleared.")


if __name__ == "__main__":
    main()
