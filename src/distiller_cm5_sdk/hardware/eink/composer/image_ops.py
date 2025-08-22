import numpy as np
from PIL import Image
from typing import Tuple, Literal, Optional


def resize_image(image: np.ndarray, target_width: int, target_height: int, 
                 mode: Literal['stretch', 'fit', 'crop'] = 'fit',
                 bg_color: int = 255,
                 crop_x: Optional[int] = None,
                 crop_y: Optional[int] = None) -> np.ndarray:
    """
    Resize image using different modes.
    
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
    pil_img = Image.fromarray(image, mode='L')
    
    if mode == 'stretch':
        # Simple resize without maintaining aspect ratio
        resized = pil_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        return np.array(resized)
    
    elif mode == 'fit':
        # Resize to fit within bounds, maintain aspect ratio
        pil_img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Create new image with background
        result = Image.new('L', (target_width, target_height), bg_color)
        
        # Center the resized image
        x = (target_width - pil_img.width) // 2
        y = (target_height - pil_img.height) // 2
        result.paste(pil_img, (x, y))
        
        return np.array(result)
    
    elif mode == 'crop':
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
        cropped = resized.crop((x, y, x + target_width, y + target_height))
        
        return np.array(cropped)


def flip_horizontal(image: np.ndarray) -> np.ndarray:
    """Flip image horizontally (mirror left-right)."""
    return np.fliplr(image)


def flip_vertical(image: np.ndarray) -> np.ndarray:
    """Flip image vertically (mirror top-bottom)."""
    return np.flipud(image)


def rotate_ccw_90(image: np.ndarray) -> np.ndarray:
    """Rotate image 90 degrees counter-clockwise."""
    return np.rot90(image, k=1)


def rotate_cw_90(image: np.ndarray) -> np.ndarray:
    """Rotate image 90 degrees clockwise."""
    return np.rot90(image, k=-1)


def rotate_180(image: np.ndarray) -> np.ndarray:
    """Rotate image 180 degrees."""
    return np.rot90(image, k=2)


def invert_colors(image: np.ndarray) -> np.ndarray:
    """Invert image colors (black to white, white to black)."""
    return 255 - image


def adjust_brightness_contrast(image: np.ndarray, brightness: float = 1.0, 
                             contrast: float = 1.0) -> np.ndarray:
    """
    Adjust image brightness and contrast.
    
    Args:
        image: Input grayscale image
        brightness: Brightness multiplier (1.0 = no change, >1 = brighter, <1 = darker)
        contrast: Contrast adjustment (-100 to 100, 0 = no change)
        
    Returns:
        Adjusted image
    """
    # Apply brightness
    img = image.astype(np.float32) * brightness
    
    # Apply contrast
    if contrast != 0:
        factor = (259 * (contrast + 255)) / (255 * (259 - contrast))
        img = 128 + factor * (img - 128)
    
    # Clip to valid range
    return np.clip(img, 0, 255).astype(np.uint8)


def crop_image(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
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
    img_h, img_w = image.shape
    
    # Clip coordinates to image bounds
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    x2 = min(x + width, img_w)
    y2 = min(y + height, img_h)
    
    return image[y:y2, x:x2]