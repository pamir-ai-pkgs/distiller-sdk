import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from typing import Literal, Optional, Any


def resize_image(
    image: np.ndarray[Any, Any],
    target_width: int,
    target_height: int,
    mode: Literal["stretch", "fit", "crop"] = "fit",
    bg_color: int = 255,
    crop_x: Optional[int] = None,
    crop_y: Optional[int] = None,
) -> np.ndarray[Any, Any]:
    """
    Resize image using different modes with Pillow.

    Note: The main Display class uses Rust backend for image processing,
    but these composer utilities use Pillow for compatibility and stability.

    Args:
        image: Input grayscale image as numpy array
        target_width: Target width
        target_height: Target height
        mode: Resize mode
            - 'stretch': Resize to exact dimensions (may distort)
            - 'fit': Resize to fit within bounds (maintains aspect ratio, adds background)
            - 'crop': Resize to cover area (maintains aspect ratio, crops excess)
        bg_color: Background color for 'fit' mode (default: white/255)
        crop_x: X position for crop (None = center)
        crop_y: Y position for crop (None = center)

    Returns:
        Resized grayscale image
    """
    # Convert numpy array to PIL Image
    pil_img = Image.fromarray(image, mode="L")

    if mode == "stretch":
        # Simple resize without maintaining aspect ratio
        resized = pil_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        return np.array(resized)

    elif mode == "fit":
        # Resize to fit within bounds, maintain aspect ratio
        pil_img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

        # Create new image with background
        result = Image.new("L", (target_width, target_height), bg_color)

        # Center the resized image
        x = (target_width - pil_img.width) // 2
        y = (target_height - pil_img.height) // 2
        result.paste(pil_img, (x, y))

        return np.array(result)

    elif mode == "crop":
        # Resize to cover entire area, crop excess
        img_ratio = pil_img.width / pil_img.height
        target_ratio = target_width / target_height

        if img_ratio > target_ratio:
            # Image is wider - fit to height
            new_height = target_height
            new_width = int(target_height * img_ratio)
        else:
            # Image is taller - fit to width
            new_width = target_width
            new_height = int(target_width / img_ratio)

        # Resize
        resized = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Calculate crop position
        if crop_x is None:
            x = (new_width - target_width) // 2  # Center horizontally
        else:
            x = max(0, min(crop_x, new_width - target_width))  # Clamp to valid range

        if crop_y is None:
            y = (new_height - target_height) // 2  # Center vertically
        else:
            y = max(0, min(crop_y, new_height - target_height))  # Clamp to valid range

        # Crop to target size
        cropped = resized.crop((x, y, x + target_width, y + target_height))

        return np.array(cropped)


def flip_horizontal(image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Flip image horizontally (mirror left-right)."""
    pil_img = Image.fromarray(image, mode="L")
    flipped = pil_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return np.array(flipped)


def flip_vertical(image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Flip image vertically (mirror top-bottom)."""
    pil_img = Image.fromarray(image, mode="L")
    flipped = pil_img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return np.array(flipped)


def rotate_ccw_90(image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Rotate image 90 degrees counter-clockwise."""
    pil_img = Image.fromarray(image, mode="L")
    rotated = pil_img.rotate(90, expand=True)
    return np.array(rotated)


def rotate_cw_90(image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Rotate image 90 degrees clockwise."""
    pil_img = Image.fromarray(image, mode="L")
    rotated = pil_img.rotate(-90, expand=True)
    return np.array(rotated)


def rotate_180(image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Rotate image 180 degrees."""
    pil_img = Image.fromarray(image, mode="L")
    rotated = pil_img.rotate(180, expand=True)
    return np.array(rotated)


def invert_colors(image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Invert image colors (black to white, white to black)."""
    pil_img = Image.fromarray(image, mode="L")
    inverted = ImageOps.invert(pil_img)
    return np.array(inverted)


def adjust_brightness_contrast(
    image: np.ndarray[Any, Any], brightness: float = 1.0, contrast: float = 1.0
) -> np.ndarray[Any, Any]:
    """
    Adjust image brightness and contrast.

    Args:
        image: Input grayscale image
        brightness: Brightness multiplier (1.0 = no change, >1 = brighter, <1 = darker)
        contrast: Contrast adjustment (-100 to 100, 0 = no change)

    Returns:
        Adjusted image
    """
    pil_img: Image.Image = Image.fromarray(image, mode="L")

    # Apply brightness
    if brightness != 1.0:
        brightness_enhancer = ImageEnhance.Brightness(pil_img)
        pil_img = brightness_enhancer.enhance(brightness)

    # Apply contrast
    # Convert contrast from (-100 to 100) scale to Pillow's scale
    # Pillow uses 1.0 as neutral, <1 reduces contrast, >1 increases
    if contrast != 0:
        # Map -100..100 to roughly 0..2 scale for Pillow
        contrast_factor = 1.0 + (contrast / 100.0)
        contrast_factor = max(0.0, contrast_factor)  # Ensure non-negative
        contrast_enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = contrast_enhancer.enhance(contrast_factor)

    return np.array(pil_img)


def crop_image(
    image: np.ndarray[Any, Any], x: int, y: int, width: int, height: int
) -> np.ndarray[Any, Any]:
    """
    Crop a region from the image.

    Args:
        image: Input image
        x: Top-left x coordinate
        y: Top-left y coordinate
        width: Crop width
        height: Crop height

    Returns:
        Cropped image region
    """
    pil_img = Image.fromarray(image, mode="L")
    img_w, img_h = pil_img.size

    # Clip coordinates to image bounds
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    x2 = min(x + width, img_w)
    y2 = min(y + height, img_h)

    cropped = pil_img.crop((x, y, x2, y2))
    return np.array(cropped)


__all__ = [
    "resize_image",
    "flip_horizontal",
    "flip_vertical",
    "rotate_ccw_90",
    "rotate_cw_90",
    "rotate_180",
    "invert_colors",
    "adjust_brightness_contrast",
    "crop_image",
]
