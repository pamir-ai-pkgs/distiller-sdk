#!/usr/bin/env python3
"""
Template Renderer for EinkComposer
Renders templates with dynamic data using the EinkComposer for proven compatibility.
"""

import json
import os
import tempfile
from typing import Optional
import qrcode
from PIL import Image

from . import EinkComposer


class TemplateRenderer:
    """Renders templates with dynamic data using EinkComposer for proven compatibility."""
    
    def __init__(self, template_path: str):
        """
        Initialize renderer with template file.
        
        Args:
            template_path: Path to the JSON template file
        """
        self.template_path = template_path
        self.template = self._load_template()
        
    def _load_template(self) -> dict:
        """Load template from JSON file."""
        try:
            with open(self.template_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load template {self.template_path}: {e}")
    
    def _generate_qr_code_file(self, data: str, output_path: str, size: tuple, error_correction: str = 'M') -> str:
        """
        Generate QR code and save to file for use with EinkComposer.
        
        Args:
            data: Data to encode in QR code
            output_path: Path to save QR code image
            size: (width, height) tuple for QR code size
            error_correction: Error correction level (L, M, Q, H)
            
        Returns:
            Path to saved QR code file
        """
        # Map error correction levels
        correction_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M, 
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=correction_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
            box_size=max(1, min(size) // 25),  # Adjust box size based on target size
            border=1,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Generate and save PIL image
        pil_img = qr.make_image(fill_color="black", back_color="white")
        pil_img = pil_img.resize(size, Image.NEAREST)
        pil_img.save(output_path)
        
        return output_path
    
    def render(self, ip_address: str, tunnel_url: str) -> EinkComposer:
        """
        Render template with dynamic data using EinkComposer.
        
        Args:
            ip_address: IP address to display
            tunnel_url: URL for QR code generation
            
        Returns:
            EinkComposer instance with rendered composition
        """
        # Get template dimensions
        width = self.template.get('width', 128)
        height = self.template.get('height', 250)
        
        # Create composer with template dimensions
        composer = EinkComposer(width, height)
        
        # Process each layer from the template
        for layer_data in self.template.get('layers', []):
            if not layer_data.get('visible', True):
                continue
                
            if layer_data.get('placeholder_type') == 'ip':
                self._add_ip_layer(composer, layer_data, ip_address)
            elif layer_data.get('placeholder_type') == 'qr':
                self._add_qr_layer(composer, layer_data, tunnel_url)
            else:
                self._add_regular_layer(composer, layer_data)
        
        return composer
    
    def _add_ip_layer(self, composer: EinkComposer, layer_data: dict, ip_address: str):
        """Add IP address text layer using EinkComposer."""
        composer.add_text_layer(
            layer_id=layer_data['id'],
            text=ip_address,
            x=layer_data.get('x', 0),
            y=layer_data.get('y', 0),
            color=layer_data.get('color', 0),
            font_size=layer_data.get('font_size', 1),
            background=layer_data.get('background', False),
            rotate=layer_data.get('rotate', 0),
            flip_h=layer_data.get('flip_h', False),
            flip_v=layer_data.get('flip_v', False),
            padding=layer_data.get('padding', 2)
        )
    
    def _add_qr_layer(self, composer: EinkComposer, layer_data: dict, tunnel_url: str):
        """Add QR code layer using EinkComposer."""
        # Generate QR code to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
            
        width = layer_data.get('width', 70)
        height = layer_data.get('height', 70)
        error_correction = layer_data.get('error_correction', 'M')
        
        # Generate QR code file
        self._generate_qr_code_file(tunnel_url, temp_path, (width, height), error_correction)
        
        # Add as image layer to composer
        composer.add_image_layer(
            layer_id=layer_data['id'],
            image_path=temp_path,
            x=layer_data.get('x', 0),
            y=layer_data.get('y', 0),
            width=width,
            height=height
        )
        
        # Store temp file for cleanup
        if not hasattr(composer, '_temp_files'):
            composer._temp_files = []
        composer._temp_files.append(temp_path)
    
    def _add_regular_layer(self, composer: EinkComposer, layer_data: dict):
        """Add regular (non-placeholder) layer using EinkComposer."""
        layer_type = layer_data['type']
        
        if layer_type == 'text':
            composer.add_text_layer(
                layer_id=layer_data['id'],
                text=layer_data.get('text', ''),
                x=layer_data.get('x', 0),
                y=layer_data.get('y', 0),
                color=layer_data.get('color', 0),
                font_size=layer_data.get('font_size', 1),
                background=layer_data.get('background', False),
                rotate=layer_data.get('rotate', 0),
                flip_h=layer_data.get('flip_h', False),
                flip_v=layer_data.get('flip_v', False),
                padding=layer_data.get('padding', 2)
            )
        elif layer_type == 'rectangle':
            composer.add_rectangle_layer(
                layer_id=layer_data['id'],
                x=layer_data.get('x', 0),
                y=layer_data.get('y', 0),
                width=layer_data.get('width', 10),
                height=layer_data.get('height', 10),
                filled=layer_data.get('filled', True),
                color=layer_data.get('color', 0)
            )
        elif layer_type == 'image' and layer_data.get('image_path'):
            # Resolve relative paths
            image_path = layer_data['image_path']
            if image_path.startswith('./'):
                # Convert relative path to absolute path
                template_dir = os.path.dirname(self.template_path)
                image_path = os.path.join(template_dir, image_path[2:])
            
            composer.add_image_layer(
                layer_id=layer_data['id'],
                image_path=image_path,
                x=layer_data.get('x', 0),
                y=layer_data.get('y', 0),
                resize_mode=layer_data.get('resize_mode', 'fit'),
                dither_mode=layer_data.get('dither_mode', 'floyd-steinberg'),
                brightness=layer_data.get('brightness', 1.0),
                contrast=layer_data.get('contrast', 0.0),
                rotate=layer_data.get('rotate', 0),
                flip_h=layer_data.get('flip_h', False),
                flip_v=layer_data.get('flip_v', False),
                crop_x=layer_data.get('crop_x'),
                crop_y=layer_data.get('crop_y'),
                width=layer_data.get('width'),
                height=layer_data.get('height')
            )
    
    def _cleanup_temp_files(self, composer: EinkComposer):
        """Clean up temporary files created during rendering."""
        if hasattr(composer, '_temp_files'):
            for temp_file in composer._temp_files:
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
            composer._temp_files.clear()
    
    def render_and_save(self, ip_address: str, tunnel_url: str, output_path: str) -> str:
        """
        Render template and save to file.
        
        Args:
            ip_address: IP address to display
            tunnel_url: URL for QR code generation
            output_path: Path to save rendered image
            
        Returns:
            Output file path
        """
        composer = self.render(ip_address, tunnel_url)
        composer.save(output_path, format='png')
        self._cleanup_temp_files(composer)
        return output_path
    
    def render_and_display(self, ip_address: str, tunnel_url: str):
        """
        Render template and display on e-ink hardware.
        
        Args:
            ip_address: IP address to display
            tunnel_url: URL for QR code generation
            
        Returns:
            True if successful
        """
        temp_path = None
        composer = None
        
        try:
            from distiller_cm5_sdk.hardware.eink import Display, DisplayMode
            
            composer = self.render(ip_address, tunnel_url)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                
            # Use EXACT same logic as working web UI
            import numpy as np
            from PIL import Image
            
            # Get the image and transform it for hardware orientation (same as web UI)
            img_array = composer.render()  # Get numpy array
            
            # Apply flip vertical (same as web UI)
            img_array = np.flipud(img_array)  # Flip up-down
            
            # Rotate 90° counterclockwise (same as web UI)
            rotated_array = np.rot90(img_array, k=1)  # k=1 means 90° counterclockwise
            
            # Save rotated image (same as web UI)
            pil_img = Image.fromarray(rotated_array, mode='L')
            pil_img.save(temp_path)
            
            # Display on hardware - match web UI method exactly
            display = Display(auto_init=False)
            display.initialize()
            
            # Convert PNG to raw data and display (same as web UI)
            raw_data = display.convert_png_to_raw(temp_path)
            display._display_raw(raw_data, DisplayMode.FULL)
            
            return True
            
        except ImportError:
            raise Exception("E-ink hardware SDK not available")
        except Exception as e:
            raise Exception(f"Failed to display on hardware: {e}")
        finally:
            # Clean up resources
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            if composer:
                self._cleanup_temp_files(composer)
            display.close()


def create_template_from_dict(template_dict: dict, output_path: str) -> str:
    """
    Helper function to create template file from dictionary.
    
    Args:
        template_dict: Template data as dictionary
        output_path: Path to save template JSON file
        
    Returns:
        Path to created template file
    """
    with open(output_path, 'w') as f:
        json.dump(template_dict, f, indent=2)
    return output_path