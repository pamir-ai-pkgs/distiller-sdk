import numpy as np
import cv2
from typing import List, Dict, Optional, Literal, Any
from dataclasses import dataclass, field

from .dithering import floyd_steinberg_dither, threshold_dither, pack_bits
from .image_ops import resize_image, flip_horizontal, rotate_ccw_90, invert_colors
from .text import render_text, measure_text


@dataclass
class Layer:
    """Base layer class."""

    id: str
    type: str
    visible: bool = True
    x: int = 0
    y: int = 0


@dataclass
class ImageLayer(Layer):
    """Image layer with processing options."""

    type: str = field(default="image", init=False)
    image_path: Optional[str] = None
    image_data: Optional[np.ndarray[Any, Any]] = None
    resize_mode: Literal["stretch", "fit", "crop"] = "fit"
    dither_mode: Literal["floyd-steinberg", "threshold", "none"] = "floyd-steinberg"
    brightness: float = 1.0
    contrast: float = 0.0
    rotate: int = 0  # Rotation in degrees (0, 90, 180, 270)
    flip_h: bool = False  # Horizontal flip
    flip_v: bool = False  # Vertical flip
    crop_x: Optional[int] = None  # X position for crop (None = center)
    crop_y: Optional[int] = None  # Y position for crop (None = center)
    width: Optional[int] = None  # Custom width (None = auto-calculate from canvas)
    height: Optional[int] = None  # Custom height (None = auto-calculate from canvas)


@dataclass
class TextLayer(Layer):
    """Text layer."""

    type: str = field(default="text", init=False)
    text: str = ""
    color: int = 0  # 0=black, 255=white
    rotate: int = 0  # Rotation in degrees (0, 90, 180, 270)
    flip_h: bool = False  # Horizontal flip
    flip_v: bool = False  # Vertical flip
    font_size: int = 1  # Font scale factor (1=normal, 2=double, etc.)
    background: bool = False  # Whether to draw white background
    padding: int = 2  # Padding around text background


@dataclass
class RectangleLayer(Layer):
    """Rectangle layer."""

    type: str = field(default="rectangle", init=False)
    width: int = 10
    height: int = 10
    filled: bool = True
    color: int = 0


class EinkComposer:
    """
    E-ink display composer for creating layered templates.
    """

    def __init__(
        self, width: int = 250, height: int = 128
    ):  # Default: 250×128 landscape (physical mounting, users create in landscape)
        """
        Initialize composer with display dimensions.

        Args:
            width: Display width in pixels
            height: Display height in pixels
        """
        self.width = width
        self.height = height
        self.layers: List[Layer] = []
        self.canvas = np.full((height, width), 255, dtype=np.uint8)  # White background

    def add_image_layer(
        self,
        layer_id: str,
        image_path: str,
        x: int = 0,
        y: int = 0,
        resize_mode: Literal["stretch", "fit", "crop"] = "fit",
        dither_mode: Literal["floyd-steinberg", "threshold", "none"] = "floyd-steinberg",
        brightness: float = 1.0,
        contrast: float = 0.0,
        rotate: int = 0,
        flip_h: bool = False,
        flip_v: bool = False,
        crop_x: Optional[int] = None,
        crop_y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> str:
        """
        Add an image layer.

        Args:
            layer_id: Unique layer identifier
            image_path: Path to image file
            x, y: Position on canvas
            resize_mode: How to resize image
            dither_mode: Dithering algorithm to use
            brightness: Brightness adjustment
            contrast: Contrast adjustment
            rotate: Rotation in degrees (0, 90, 180, 270)
            flip_h: Horizontal flip
            flip_v: Vertical flip
            crop_x: X position for crop when resize_mode='crop' (None = center)
            crop_y: Y position for crop when resize_mode='crop' (None = center)
            width: Custom width for the image (None = auto-calculate from canvas)
            height: Custom height for the image (None = auto-calculate from canvas)

        Returns:
            Layer ID
        """
        layer = ImageLayer(
            id=layer_id,
            x=x,
            y=y,
            image_path=image_path,
            resize_mode=resize_mode,
            dither_mode=dither_mode,
            brightness=brightness,
            contrast=contrast,
            rotate=rotate,
            flip_h=flip_h,
            flip_v=flip_v,
            crop_x=crop_x,
            crop_y=crop_y,
            width=width,
            height=height,
        )
        self.layers.append(layer)
        return layer_id

    def add_text_layer(
        self,
        layer_id: str,
        text: str,
        x: int = 0,
        y: int = 0,
        color: int = 0,
        rotate: int = 0,
        flip_h: bool = False,
        flip_v: bool = False,
        font_size: int = 1,
        background: bool = False,
        padding: int = 2,
    ) -> str:
        """
        Add a text layer.

        Args:
            layer_id: Unique layer identifier
            text: Text to render
            x, y: Position on canvas
            color: Text color (0=black, 255=white)
            rotate: Rotation in degrees (0, 90, 180, 270)
            flip_h: Horizontal flip
            flip_v: Vertical flip
            font_size: Font scale factor (1=normal, 2=double, etc.)
            background: Whether to draw white background behind text
            padding: Padding around text background in pixels

        Returns:
            Layer ID
        """
        layer = TextLayer(
            id=layer_id,
            text=text,
            x=x,
            y=y,
            color=color,
            rotate=rotate,
            flip_h=flip_h,
            flip_v=flip_v,
            font_size=font_size,
            background=background,
            padding=padding,
        )
        self.layers.append(layer)
        return layer_id

    def add_rectangle_layer(
        self,
        layer_id: str,
        x: int = 0,
        y: int = 0,
        width: int = 10,
        height: int = 10,
        filled: bool = True,
        color: int = 0,
    ) -> str:
        """
        Add a rectangle layer.

        Args:
            layer_id: Unique layer identifier
            x, y: Top-left position
            width, height: Rectangle dimensions
            filled: Whether to fill the rectangle
            color: Rectangle color (0=black, 255=white)

        Returns:
            Layer ID
        """
        layer = RectangleLayer(
            id=layer_id, x=x, y=y, width=width, height=height, filled=filled, color=color
        )
        self.layers.append(layer)
        return layer_id

    def remove_layer(self, layer_id: str) -> bool:
        """Remove a layer by ID."""
        self.layers = [layer for layer in self.layers if layer.id != layer_id]
        return True

    def update_layer(self, layer_id: str, **kwargs: Any) -> bool:
        """Update layer properties."""
        for layer in self.layers:
            if layer.id == layer_id:
                # Check if this is a QR placeholder and if dimensions are changing
                is_qr_placeholder = (
                    hasattr(layer, "placeholder_type") and layer.placeholder_type == "qr"
                )
                dimensions_changing = is_qr_placeholder and (
                    "width" in kwargs or "height" in kwargs
                )

                # Update properties
                for key, value in kwargs.items():
                    if hasattr(layer, key):
                        setattr(layer, key, value)

                # Regenerate QR placeholder image if dimensions changed
                if dimensions_changing and isinstance(layer, ImageLayer):
                    import numpy as np

                    width = layer.width or 70  # Default width if None
                    height = layer.height or 70  # Default height if None

                    # Create a new placeholder pattern for preview
                    placeholder_img = np.full(
                        (height, width), 255, dtype=np.uint8
                    )  # White background
                    # Add a simple border and "QR" text pattern
                    placeholder_img[0:2, :] = 0  # Top border
                    placeholder_img[-2:, :] = 0  # Bottom border
                    placeholder_img[:, 0:2] = 0  # Left border
                    placeholder_img[:, -2:] = 0  # Right border

                    # Add "QR" text in center (simplified)
                    center_y, center_x = height // 2, width // 2
                    if height > 10 and width > 20:  # Only if big enough
                        placeholder_img[
                            max(0, center_y - 5) : min(height, center_y + 5),
                            max(0, center_x - 10) : min(width, center_x + 10),
                        ] = 0

                    # Update the layer's image data
                    layer.image_data = placeholder_img

                return True
        return False

    def toggle_layer(self, layer_id: str) -> bool:
        """Toggle layer visibility."""
        for layer in self.layers:
            if layer.id == layer_id:
                layer.visible = not layer.visible
                return True
        return False

    def move_layer(self, layer_id: str, new_index: int) -> bool:
        """Move a layer to a new position in the layer stack."""
        # Find the layer
        layer_to_move = None
        old_index = -1

        for i, layer in enumerate(self.layers):
            if layer.id == layer_id:
                layer_to_move = layer
                old_index = i
                break

        if layer_to_move is None or old_index == -1:
            return False

        # Clamp new_index to valid range
        new_index = max(0, min(new_index, len(self.layers) - 1))

        # Remove from old position
        self.layers.pop(old_index)

        # Insert at new position
        self.layers.insert(new_index, layer_to_move)

        return True

    def _render_image_layer(self, layer: ImageLayer) -> None:
        """Render an image layer to canvas."""
        if not layer.visible:
            return

        # Load image
        img: np.ndarray[Any, Any]
        if layer.image_data is not None:
            img = layer.image_data
        elif layer.image_path:
            # Use OpenCV to load image in grayscale
            img_loaded = cv2.imread(layer.image_path, cv2.IMREAD_GRAYSCALE)
            if img_loaded is None:
                return  # Failed to load image
            img = img_loaded
        else:
            return

        # Apply transformations first (before resizing)
        if layer.flip_h:
            img = flip_horizontal(img)
        if layer.flip_v:
            from .image_ops import flip_vertical

            img = flip_vertical(img)

        # Apply rotation
        if layer.rotate != 0:
            # Normalize rotation to 0, 90, 180, 270
            rotations = (layer.rotate % 360) // 90
            for _ in range(rotations):
                img = rotate_ccw_90(img)

        # Calculate target size based on custom dimensions or canvas size
        # After rotation, dimensions might have changed
        if layer.width is not None and layer.height is not None:
            target_width = layer.width
            target_height = layer.height
        else:
            target_width = self.width - layer.x
            target_height = self.height - layer.y

        # Resize after transformations
        if img.shape != (target_height, target_width):
            img = resize_image(
                img,
                target_width,
                target_height,
                mode=layer.resize_mode,
                crop_x=layer.crop_x,
                crop_y=layer.crop_y,
            )

        # Apply brightness/contrast
        if layer.brightness != 1.0 or layer.contrast != 0:
            from .image_ops import adjust_brightness_contrast

            img = adjust_brightness_contrast(img, layer.brightness, layer.contrast)

        # Apply dithering
        if layer.dither_mode == "floyd-steinberg":
            img = floyd_steinberg_dither(img)
        elif layer.dither_mode == "threshold":
            img = threshold_dither(img)

        # Composite onto canvas
        h, w = img.shape
        y_end = int(min(layer.y + h, self.height))
        x_end = int(min(layer.x + w, self.width))

        if int(layer.y) < self.height and int(layer.x) < self.width:
            self.canvas[int(layer.y) : y_end, int(layer.x) : x_end] = img[
                : y_end - int(layer.y), : x_end - int(layer.x)
            ]

    def _render_text_layer(self, layer: TextLayer) -> None:
        """Render a text layer to canvas."""
        if not layer.visible or not layer.text:
            return

        # Import text functions
        from .image_ops import rotate_ccw_90, flip_horizontal

        # Measure text dimensions
        text_width, text_height = measure_text(layer.text, layer.font_size)

        # Calculate background dimensions if needed
        if layer.background:
            bg_width = text_width + 2 * layer.padding
            bg_height = text_height + 2 * layer.padding
        else:
            bg_width = text_width
            bg_height = text_height

        # Create a temporary canvas for text + background
        temp_canvas: np.ndarray[Any, Any] = np.full(
            (bg_height, bg_width), 255, dtype=np.uint8
        )  # White background

        # Render background if enabled
        if layer.background:
            # Background is already white, so just render text with offset
            text_x = layer.padding
            text_y = layer.padding
        else:
            # No background, render text directly
            text_x = 0
            text_y = 0

        # Render text on temporary canvas
        render_text(layer.text, text_x, text_y, temp_canvas, layer.color, layer.font_size)

        # Apply flipping if needed
        if layer.flip_h:
            temp_canvas = flip_horizontal(temp_canvas)
        if layer.flip_v:
            temp_canvas = np.flipud(temp_canvas).astype(np.uint8)  # Vertical flip using numpy

        # Apply rotation if needed
        if layer.rotate != 0:
            # Normalize rotation to 0, 90, 180, 270
            rotations = (layer.rotate % 360) // 90
            for _ in range(rotations):
                temp_canvas = rotate_ccw_90(temp_canvas)

        # Composite onto main canvas
        h, w = temp_canvas.shape
        y_end = int(min(layer.y + h, self.height))
        x_end = int(min(layer.x + w, self.width))

        if int(layer.y) < self.height and int(layer.x) < self.width:
            # Only composite non-white pixels if no background, otherwise composite everything
            if layer.background:
                self.canvas[int(layer.y) : y_end, int(layer.x) : x_end] = temp_canvas[
                    : y_end - int(layer.y), : x_end - int(layer.x)
                ]
            else:
                # For no background, only composite non-white pixels (text only)
                mask = temp_canvas[: y_end - int(layer.y), : x_end - int(layer.x)] < 255
                self.canvas[int(layer.y) : y_end, int(layer.x) : x_end][mask] = temp_canvas[
                    : y_end - int(layer.y), : x_end - int(layer.x)
                ][mask]

    def _render_rectangle_layer(self, layer: RectangleLayer) -> None:
        """Render a rectangle layer to canvas."""
        if not layer.visible:
            return

        x1 = int(max(0, layer.x))
        y1 = int(max(0, layer.y))
        x2 = int(min(self.width, layer.x + layer.width))
        y2 = int(min(self.height, layer.y + layer.height))

        if x1 >= x2 or y1 >= y2:
            return

        if layer.filled:
            self.canvas[y1:y2, x1:x2] = layer.color
        else:
            # Draw outline
            self.canvas[y1, x1:x2] = layer.color  # Top
            self.canvas[y2 - 1, x1:x2] = layer.color  # Bottom
            self.canvas[y1:y2, x1] = layer.color  # Left
            self.canvas[y1:y2, x2 - 1] = layer.color  # Right

    def render(
        self,
        background_color: int = 255,
        final_dither: Optional[Literal["floyd-steinberg", "threshold"]] = None,
        transformations: Optional[List[Literal["flip-h", "flip-v", "rotate-90", "invert"]]] = None,
    ) -> np.ndarray[Any, Any]:
        """
        Render all layers to create final image.

        Args:
            background_color: Background color (0=black, 255=white)
            final_dither: Optional final dithering pass
            transformations: List of transformations to apply

        Returns:
            Rendered grayscale image
        """
        # Clear canvas
        self.canvas.fill(background_color)

        # Render each layer
        for layer in self.layers:
            if isinstance(layer, ImageLayer):
                self._render_image_layer(layer)
            elif isinstance(layer, TextLayer):
                self._render_text_layer(layer)
            elif isinstance(layer, RectangleLayer):
                self._render_rectangle_layer(layer)

        result = self.canvas.copy()

        # Apply final dithering if requested
        if final_dither == "floyd-steinberg":
            result = floyd_steinberg_dither(result)
        elif final_dither == "threshold":
            result = threshold_dither(result)

        # Apply transformations
        if transformations:
            for transform in transformations:
                if transform == "flip-h":
                    result = flip_horizontal(result)
                elif transform == "flip-v":
                    from .image_ops import flip_vertical

                    result = flip_vertical(result)
                elif transform == "rotate-90":
                    result = rotate_ccw_90(result)
                elif transform == "invert":
                    result = invert_colors(result)

        return result

    def render_binary(self, **kwargs: Any) -> bytes:
        """
        Render and return as packed binary data.

        Returns:
            Packed binary data (8 pixels per byte)
        """
        img = self.render(**kwargs)
        return pack_bits(img)

    def save(
        self, filename: str, format: Literal["png", "binary", "bmp"] = "png", **render_kwargs: Any
    ) -> None:
        """
        Save rendered image to file.

        Args:
            filename: Output filename
            format: Output format
            **render_kwargs: Arguments passed to render()
        """
        if format == "binary":
            data = self.render_binary(**render_kwargs)
            with open(filename, "wb") as f:
                f.write(data)
        else:
            img = self.render(**render_kwargs)

            if format == "bmp":
                # Convert to 1-bit for true monochrome BMP
                _, binary_img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
                cv2.imwrite(filename, binary_img)
            else:
                # Save as PNG or other format
                cv2.imwrite(filename, img)

    def get_layer_info(self) -> List[Dict[str, Any]]:
        """Get information about all layers."""
        info = []
        for layer in self.layers:
            layer_info = {
                "id": layer.id,
                "type": layer.type,
                "visible": layer.visible,
                "x": layer.x,
                "y": layer.y,
            }

            if isinstance(layer, ImageLayer):
                layer_info.update(
                    {
                        "image_path": layer.image_path,
                        "resize_mode": layer.resize_mode,
                        "dither_mode": layer.dither_mode,
                        "brightness": layer.brightness,
                        "contrast": layer.contrast,
                        "rotate": layer.rotate,
                        "flip_h": layer.flip_h,
                        "flip_v": layer.flip_v,
                        "crop_x": layer.crop_x,
                        "crop_y": layer.crop_y,
                        "width": layer.width,
                        "height": layer.height,
                    }
                )
                # Include placeholder_type if it exists (for QR codes, etc.)
                if hasattr(layer, "placeholder_type"):
                    layer_info["placeholder_type"] = layer.placeholder_type
                if hasattr(layer, "error_correction"):
                    layer_info["error_correction"] = layer.error_correction
            elif isinstance(layer, TextLayer):
                layer_info.update(
                    {
                        "text": layer.text,
                        "color": layer.color,
                        "rotate": layer.rotate,
                        "flip_h": layer.flip_h,
                        "flip_v": layer.flip_v,
                        "font_size": layer.font_size,
                        "background": layer.background,
                        "padding": layer.padding,
                    }
                )
                # Include placeholder_type if it exists (for IP placeholders, etc.)
                if hasattr(layer, "placeholder_type"):
                    layer_info["placeholder_type"] = layer.placeholder_type
            elif isinstance(layer, RectangleLayer):
                layer_info.update(
                    {
                        "width": layer.width,
                        "height": layer.height,
                        "filled": layer.filled,
                        "color": layer.color,
                    }
                )

            info.append(layer_info)

        return info


__all__ = [
    "Layer",
    "ImageLayer",
    "TextLayer",
    "RectangleLayer",
    "EinkComposer",
]
