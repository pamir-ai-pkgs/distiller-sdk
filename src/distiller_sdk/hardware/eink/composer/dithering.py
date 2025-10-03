import numpy as np


def floyd_steinberg_dither(image: np.ndarray) -> np.ndarray:
    """
    Apply Floyd-Steinberg dithering to convert grayscale image to 1-bit monochrome.

    Args:
        image: Input grayscale image as numpy array (0-255 values)

    Returns:
        Binary image (0 or 255 values)
    """
    # Ensure we're working with a float copy
    img = image.astype(np.float32).copy()
    height, width = img.shape

    # Process each pixel
    for y in range(height):
        for x in range(width):
            old_pixel = img[y, x]
            new_pixel = 255 if old_pixel > 128 else 0
            img[y, x] = new_pixel

            # Calculate and distribute error
            error = old_pixel - new_pixel

            # Distribute error to neighboring pixels
            if x + 1 < width:
                img[y, x + 1] += error * 7 / 16
            if y + 1 < height:
                if x > 0:
                    img[y + 1, x - 1] += error * 3 / 16
                img[y + 1, x] += error * 5 / 16
                if x + 1 < width:
                    img[y + 1, x + 1] += error * 1 / 16

    return img.astype(np.uint8)


def threshold_dither(image: np.ndarray, threshold: int = 128) -> np.ndarray:
    """
    Simple threshold-based dithering (no error diffusion).

    Args:
        image: Input grayscale image as numpy array (0-255 values)
        threshold: Threshold value (default: 128)

    Returns:
        Binary image (0 or 255 values)
    """
    return np.where(image > threshold, 255, 0).astype(np.uint8)


def pack_bits(image: np.ndarray) -> bytes:
    """
    Pack a binary image (0/255 values) into bit-packed format.
    8 pixels per byte, MSB first.

    Args:
        image: Binary image array (0 or 255 values)

    Returns:
        Packed bytes
    """
    height, width = image.shape
    packed_width = (width + 7) // 8
    packed = bytearray(packed_width * height)

    for y in range(height):
        for x in range(width):
            if image[y, x] > 128:  # White pixel
                byte_idx = y * packed_width + x // 8
                bit_idx = 7 - (x % 8)
                packed[byte_idx] |= 1 << bit_idx

    return bytes(packed)


def unpack_bits(data: bytes, width: int, height: int) -> np.ndarray:
    """
    Unpack bit-packed data into a binary image array.

    Args:
        data: Packed bytes
        width: Image width
        height: Image height

    Returns:
        Binary image array (0 or 255 values)
    """
    packed_width = (width + 7) // 8
    image = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            byte_idx = y * packed_width + x // 8
            bit_idx = 7 - (x % 8)
            if data[byte_idx] & (1 << bit_idx):
                image[y, x] = 255

    return image
