#!/usr/bin/env python3
import argparse
import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from .composer import EinkComposer

# Try to import hardware display support
try:
    sys.path.insert(0, '/opt/distiller-cm5-sdk/src')
    from distiller_cm5_sdk.hardware.eink import Display, DisplayMode, ScalingMethod, DitheringMethod
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    Display = None
    DisplayMode = None
    ScalingMethod = None
    DitheringMethod = None


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="E-ink display image composer - Create layered templates for e-ink displays",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # IMPORTANT: Always create a composition first!
  # Standard e-ink display is 128x250 (width x height)
  
  # Working example for e-ink hardware:
  eink-compose create --size 128x250
  eink-compose add-text hello "HELLO E-INK" --x 20 --y 120
  eink-compose add-rect border --width 128 --height 250 --filled false
  eink-compose display
  
  # More detailed example:
  eink-compose create --size 128x250
  eink-compose add-rect bg --width 128 --height 250 --filled true --color 255
  eink-compose add-text title "E-INK DISPLAY" --x 15 --y 50
  eink-compose add-text info "128 x 250 px" --x 25 --y 70
  eink-compose add-rect frame --x 10 --y 100 --width 108 --height 50 --filled false
  eink-compose display --save-preview preview.png
  
  # Render to file
  eink-compose render --output display.png --format png
  eink-compose render --output display.bin --format binary --dither floyd-steinberg
  
  # Display options
  eink-compose display                    # Full refresh
  eink-compose display --partial          # Fast refresh (may ghost)
  eink-compose display --rotate --flip-h  # With transformations
  
  # Save/load compositions
  eink-compose save my_template.json
  eink-compose load my_template.json
  eink-compose load my_template.json --render --output final.png
  
  # Session management
  eink-compose reset                   # Clear session, create new 128x250
  eink-compose reset --size 240x416    # Clear session, create custom size
  
  # Hardware control
  eink-compose hardware info   # Show display info
  eink-compose hardware clear  # Clear display
  eink-compose hardware sleep  # Power save mode
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create command
    create_cmd = subparsers.add_parser('create', help='Create new composition')
    create_cmd.add_argument('--size', default='128x250', help='Display size WIDTHxHEIGHT (default: 128x250)')
    create_cmd.add_argument('--output', help='Output file')
    create_cmd.add_argument('--bg-color', type=int, default=255, choices=[0, 255],
                           help='Background color: 0=black, 255=white (default: 255)')
    
    # Add image command
    add_img_cmd = subparsers.add_parser('add-image', help='Add image layer')
    add_img_cmd.add_argument('layer_id', help='Layer ID')
    add_img_cmd.add_argument('image_path', help='Path to image file')
    add_img_cmd.add_argument('--x', type=int, default=0, help='X position (default: 0)')
    add_img_cmd.add_argument('--y', type=int, default=0, help='Y position (default: 0)')
    add_img_cmd.add_argument('--resize-mode', choices=['stretch', 'fit', 'crop'], default='fit',
                            help='Resize mode (default: fit)')
    add_img_cmd.add_argument('--dither', choices=['floyd-steinberg', 'threshold', 'none'],
                            default='floyd-steinberg', help='Dithering mode (default: floyd-steinberg)')
    add_img_cmd.add_argument('--brightness', type=float, default=1.0, help='Brightness (default: 1.0)')
    add_img_cmd.add_argument('--contrast', type=float, default=0.0, help='Contrast (default: 0.0)')
    add_img_cmd.add_argument('--rotate', type=int, default=0,
                            help='Rotation in degrees (default: 0)')
    add_img_cmd.add_argument('--flip-h', action='store_true', help='Flip horizontally')
    add_img_cmd.add_argument('--flip-v', action='store_true', help='Flip vertically')
    add_img_cmd.add_argument('--crop-x', type=int, help='X position for crop (for crop mode)')
    add_img_cmd.add_argument('--crop-y', type=int, help='Y position for crop (for crop mode)')
    add_img_cmd.add_argument('--width', type=int, help='Custom width for the image')
    add_img_cmd.add_argument('--height', type=int, help='Custom height for the image')
    
    # Add text command
    add_txt_cmd = subparsers.add_parser('add-text', help='Add text layer')
    add_txt_cmd.add_argument('layer_id', help='Layer ID')
    add_txt_cmd.add_argument('text', help='Text to display')
    add_txt_cmd.add_argument('--x', type=int, default=0, help='X position (default: 0)')
    add_txt_cmd.add_argument('--y', type=int, default=0, help='Y position (default: 0)')
    add_txt_cmd.add_argument('--color', type=int, default=0, choices=[0, 255],
                            help='Text color: 0=black, 255=white (default: 0)')
    add_txt_cmd.add_argument('--rotate', type=int, default=0,
                            help='Rotation in degrees (default: 0)')
    add_txt_cmd.add_argument('--flip-h', action='store_true',
                            help='Flip text horizontally')
    add_txt_cmd.add_argument('--flip-v', action='store_true',
                            help='Flip text vertically')
    add_txt_cmd.add_argument('--font-size', type=int, default=1,
                            help='Font scale factor: 1=normal, 2=double, etc. (default: 1)')
    add_txt_cmd.add_argument('--background', action='store_true',
                            help='Add white background behind text')
    add_txt_cmd.add_argument('--padding', type=int, default=2,
                            help='Padding around background in pixels (default: 2)')
    
    # Add rectangle command
    add_rect_cmd = subparsers.add_parser('add-rect', help='Add rectangle layer')
    add_rect_cmd.add_argument('layer_id', help='Layer ID')
    add_rect_cmd.add_argument('--x', type=int, default=0, help='X position (default: 0)')
    add_rect_cmd.add_argument('--y', type=int, default=0, help='Y position (default: 0)')
    add_rect_cmd.add_argument('--width', type=int, default=10, help='Width (default: 10)')
    add_rect_cmd.add_argument('--height', type=int, default=10, help='Height (default: 10)')
    add_rect_cmd.add_argument('--filled', action='store_true', help='Fill rectangle')
    add_rect_cmd.add_argument('--color', type=int, default=0, choices=[0, 255],
                            help='Rectangle color: 0=black, 255=white (default: 0)')
    
    # Remove layer command
    remove_cmd = subparsers.add_parser('remove', help='Remove layer')
    remove_cmd.add_argument('layer_id', help='Layer ID to remove')
    
    # Toggle layer command
    toggle_cmd = subparsers.add_parser('toggle', help='Toggle layer visibility')
    toggle_cmd.add_argument('layer_id', help='Layer ID to toggle')
    
    # Reset session command
    reset_cmd = subparsers.add_parser('reset', help='Reset/clear the current session')
    reset_cmd.add_argument('--size', default='128x250', help='Display size for new session (default: 128x250)')
    
    # List layers command
    list_cmd = subparsers.add_parser('list', help='List all layers')
    
    # Render command
    render_cmd = subparsers.add_parser('render', help='Render composition')
    render_cmd.add_argument('--output', required=True, help='Output file')
    render_cmd.add_argument('--format', choices=['png', 'binary', 'bmp'], default='png',
                           help='Output format (default: png)')
    render_cmd.add_argument('--dither', choices=['floyd-steinberg', 'threshold', 'none'],
                           help='Final dithering pass')
    render_cmd.add_argument('--transform', action='append',
                           choices=['flip-h', 'flip-v', 'rotate-90', 'invert'],
                           help='Apply transformations (can be used multiple times)')
    render_cmd.add_argument('--bg-color', type=int, default=255, choices=[0, 255],
                           help='Background color: 0=black, 255=white (default: 255)')
    
    # Save composition command
    save_cmd = subparsers.add_parser('save', help='Save composition to JSON')
    save_cmd.add_argument('filename', help='Output JSON file')
    
    # Load composition command
    load_cmd = subparsers.add_parser('load', help='Load composition from JSON')
    load_cmd.add_argument('filename', help='Input JSON file')
    load_cmd.add_argument('--render', action='store_true', help='Render after loading')
    load_cmd.add_argument('--output', help='Output file (if rendering)')
    load_cmd.add_argument('--format', choices=['png', 'binary', 'bmp'], default='png',
                         help='Output format (default: png)')
    
    # Display command (hardware)
    if HARDWARE_AVAILABLE:
        display_cmd = subparsers.add_parser('display', help='Display composition on e-ink hardware')
        display_cmd.add_argument('--partial', action='store_true', 
                               help='Use partial refresh (faster but may ghost)')
        display_cmd.add_argument('--rotate', action='store_true',
                               help='Rotate image 90° counter-clockwise')
        display_cmd.add_argument('--flip-h', action='store_true',
                               help='Flip image horizontally')
        display_cmd.add_argument('--clear', action='store_true',
                               help='Clear display before showing')
        display_cmd.add_argument('--save-preview', help='Save preview PNG to file')
    
    # Hardware control commands
    if HARDWARE_AVAILABLE:
        hw_group = subparsers.add_parser('hardware', help='Hardware control commands')
        hw_subparsers = hw_group.add_subparsers(dest='hw_command', help='Hardware commands')
        
        hw_clear = hw_subparsers.add_parser('clear', help='Clear the e-ink display')
        hw_sleep = hw_subparsers.add_parser('sleep', help='Put display to sleep mode')
        hw_info = hw_subparsers.add_parser('info', help='Show display information')
    
    return parser


class ComposerSession:
    """Manage composer state between commands."""
    
    def __init__(self):
        self.composer = None
        self.session_file = Path.home() / '.eink_composer_session.json'
        self.load_session()
    
    def ensure_composer(self, default_width=128, default_height=250):
        """Ensure a composer exists, creating a default one if needed."""
        if not self.composer:
            print(f"No active composition found. Creating default {default_width}x{default_height} composition...")
            self.composer = EinkComposer(default_width, default_height)
            self.save_session()
            print(f"✓ Created default {default_width}x{default_height} composition")
    
    def load_session(self):
        """Load session from file."""
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    data = json.load(f)
                    self.composer = EinkComposer(data['width'], data['height'])
                    # Restore layers
                    for layer_data in data.get('layers', []):
                        self._restore_layer(layer_data)
            except Exception as e:
                print(f"Warning: Could not load session: {e}", file=sys.stderr)
                self.composer = None
    
    def save_session(self):
        """Save session to file."""
        if self.composer:
            data = {
                'width': self.composer.width,
                'height': self.composer.height,
                'layers': self.composer.get_layer_info()
            }
            with open(self.session_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def _restore_layer(self, layer_data: Dict[str, Any]):
        """Restore a layer from saved data."""
        layer_type = layer_data['type']
        layer_id = layer_data['id']
        
        if layer_type == 'image':
            self.composer.add_image_layer(
                layer_id=layer_id,
                image_path=layer_data.get('image_path', ''),
                x=layer_data['x'],
                y=layer_data['y'],
                resize_mode=layer_data.get('resize_mode', 'fit'),
                dither_mode=layer_data.get('dither_mode', 'floyd-steinberg'),
                brightness=layer_data.get('brightness', 1.0),
                contrast=layer_data.get('contrast', 0.0),
                rotate=layer_data.get('rotate', 0),
                flip_h=layer_data.get('flip_h', False),
                flip_v=layer_data.get('flip_v', False),
                crop_x=layer_data.get('crop_x', None),
                crop_y=layer_data.get('crop_y', None),
                width=layer_data.get('width', None),
                height=layer_data.get('height', None)
            )
        elif layer_type == 'text':
            self.composer.add_text_layer(
                layer_id=layer_id,
                text=layer_data.get('text', ''),
                x=layer_data['x'],
                y=layer_data['y'],
                color=layer_data.get('color', 0),
                rotate=layer_data.get('rotate', 0),
                flip_h=layer_data.get('flip_h', False),
                flip_v=layer_data.get('flip_v', False),
                font_size=layer_data.get('font_size', 1),
                background=layer_data.get('background', False),
                padding=layer_data.get('padding', 2)
            )
        elif layer_type == 'rectangle':
            self.composer.add_rectangle_layer(
                layer_id=layer_id,
                x=layer_data['x'],
                y=layer_data['y'],
                width=layer_data.get('width', 10),
                height=layer_data.get('height', 10),
                filled=layer_data.get('filled', True),
                color=layer_data.get('color', 0)
            )
        
        if not layer_data.get('visible', True):
            self.composer.toggle_layer(layer_id)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    session = ComposerSession()
    
    # Handle commands
    if args.command == 'create':
        # Parse size
        try:
            width, height = map(int, args.size.split('x'))
        except ValueError:
            print(f"Error: Invalid size format '{args.size}'. Use WIDTHxHEIGHT", file=sys.stderr)
            sys.exit(1)
        
        session.composer = EinkComposer(width, height)
        session.save_session()
        print(f"Created new {width}x{height} composition")
        
        if args.output:
            session.composer.save(args.output)
            print(f"Saved to {args.output}")
    
    elif args.command == 'add-image':
        session.ensure_composer()
        
        session.composer.add_image_layer(
            layer_id=args.layer_id,
            image_path=args.image_path,
            x=args.x, y=args.y,
            resize_mode=args.resize_mode,
            dither_mode=args.dither,
            brightness=args.brightness,
            contrast=args.contrast,
            rotate=args.rotate,
            flip_h=args.flip_h,
            flip_v=args.flip_v,
            crop_x=args.crop_x,
            crop_y=args.crop_y,
            width=args.width,
            height=args.height
        )
        session.save_session()
        print(f"Added image layer '{args.layer_id}'")
    
    elif args.command == 'add-text':
        session.ensure_composer()
        
        session.composer.add_text_layer(
            layer_id=args.layer_id,
            text=args.text,
            x=args.x, y=args.y,
            color=args.color,
            rotate=args.rotate,
            flip_h=args.flip_h,
            flip_v=args.flip_v,
            font_size=args.font_size,
            background=args.background,
            padding=args.padding
        )
        session.save_session()
        print(f"Added text layer '{args.layer_id}'")
    
    elif args.command == 'add-rect':
        session.ensure_composer()
        
        session.composer.add_rectangle_layer(
            layer_id=args.layer_id,
            x=args.x, y=args.y,
            width=args.width, height=args.height,
            filled=args.filled,
            color=args.color
        )
        session.save_session()
        print(f"Added rectangle layer '{args.layer_id}'")
    
    elif args.command == 'remove':
        session.ensure_composer()
        
        session.composer.remove_layer(args.layer_id)
        session.save_session()
        print(f"Removed layer '{args.layer_id}'")
    
    elif args.command == 'toggle':
        session.ensure_composer()
        
        session.composer.toggle_layer(args.layer_id)
        session.save_session()
        print(f"Toggled visibility of layer '{args.layer_id}'")
    
    elif args.command == 'reset':
        # Parse size
        try:
            width, height = map(int, args.size.split('x'))
        except ValueError:
            print(f"Error: Invalid size format '{args.size}'. Use WIDTHxHEIGHT", file=sys.stderr)
            sys.exit(1)
        
        # Delete existing session file if it exists
        if session.session_file.exists():
            session.session_file.unlink()
            print("✓ Cleared existing session")
        
        # Create new session
        session.composer = EinkComposer(width, height)
        session.save_session()
        print(f"✓ Created new {width}x{height} composition")
        print("Session reset complete")
    
    elif args.command == 'list':
        session.ensure_composer()
        
        layers = session.composer.get_layer_info()
        if not layers:
            print("No layers")
        else:
            print(f"Composition: {session.composer.width}x{session.composer.height}")
            print("\nLayers:")
            for layer in layers:
                visibility = "✓" if layer['visible'] else "✗"
                print(f"  [{visibility}] {layer['id']:15} {layer['type']:10} @ ({layer['x']},{layer['y']})")
                
                if layer['type'] == 'text':
                    print(f"      Text: '{layer['text']}'")
                elif layer['type'] == 'image':
                    print(f"      Image: {layer['image_path']}")
                elif layer['type'] == 'rectangle':
                    print(f"      Size: {layer['width']}x{layer['height']}")
    
    elif args.command == 'render':
        session.ensure_composer()
        
        render_kwargs = {
            'background_color': args.bg_color,
            'final_dither': args.dither if args.dither != 'none' else None,
            'transformations': args.transform
        }
        
        session.composer.save(args.output, format=args.format, **render_kwargs)
        print(f"Rendered to {args.output}")
    
    elif args.command == 'save':
        session.ensure_composer()
        
        data = {
            'width': session.composer.width,
            'height': session.composer.height,
            'layers': session.composer.get_layer_info()
        }
        
        with open(args.filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved composition to {args.filename}")
    
    elif args.command == 'load':
        try:
            with open(args.filename) as f:
                data = json.load(f)
            
            session.composer = EinkComposer(data['width'], data['height'])
            
            # Restore layers
            for layer_data in data.get('layers', []):
                session._restore_layer(layer_data)
            
            session.save_session()
            print(f"Loaded composition from {args.filename}")
            
            if args.render and args.output:
                session.composer.save(args.output, format=args.format)
                print(f"Rendered to {args.output}")
        
        except Exception as e:
            print(f"Error loading composition: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'display':
        if not HARDWARE_AVAILABLE:
            print("Error: Hardware display not available. SDK not found.", file=sys.stderr)
            print("Run: source /opt/distiller-cm5-sdk/activate.sh", file=sys.stderr)
            sys.exit(1)
        
        session.ensure_composer()
        
        try:
            # Initialize display
            display = Display()
            
            # Clear first if requested
            if args.clear:
                display.clear()
                print("✓ Display cleared")
            
            # Save to temporary file
            temp_file = "/tmp/eink_compose_display.png"
            session.composer.save(temp_file, format='png')
            
            # Save preview if requested
            if args.save_preview:
                session.composer.save(args.save_preview, format='png')
                print(f"✓ Preview saved to {args.save_preview}")
            
            # Display on hardware
            mode = DisplayMode.PARTIAL if args.partial else DisplayMode.FULL
            
            # Use display_image method
            display.display_image(
                temp_file,
                mode=mode,
                rotate=args.rotate,
                flip_horizontal=args.flip_h
            )
            
            # Clean up temp file
            os.remove(temp_file)
            
            print("✓ Displayed on e-ink hardware")
            if args.partial:
                print("  - Used partial refresh")
            if args.rotate:
                print("  - Rotated 90° CCW")
            if args.flip_h:
                print("  - Flipped horizontally")
                
        except Exception as e:
            print(f"Error displaying on hardware: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            
            # Check if the temp file exists
            if os.path.exists(temp_file):
                print(f"Temp file exists: {temp_file}", file=sys.stderr)
                print(f"File size: {os.path.getsize(temp_file)} bytes", file=sys.stderr)
            else:
                print(f"Temp file NOT found: {temp_file}", file=sys.stderr)
            
            sys.exit(1)
    
    elif args.command == 'hardware':
        if not HARDWARE_AVAILABLE:
            print("Error: Hardware control not available. SDK not found.", file=sys.stderr)
            sys.exit(1)
        
        try:
            display = Display()
            
            if args.hw_command == 'clear':
                display.clear()
                print("✓ Display cleared")
            
            elif args.hw_command == 'sleep':
                display.sleep()
                print("✓ Display in sleep mode")
            
            elif args.hw_command == 'info':
                try:
                    from distiller_cm5_sdk.hardware.eink import get_default_firmware, FirmwareType
                    firmware = get_default_firmware()
                    if firmware == FirmwareType.EPD240x416:
                        size = "240x416 (large)"
                    else:
                        size = "128x250 (standard)"
                    print(f"Display type: {size}")
                except:
                    print("Display type: 128x250 (default)")
                print("Hardware: E-ink display connected")
            
            else:
                print("Error: Unknown hardware command", file=sys.stderr)
                sys.exit(1)
                
        except Exception as e:
            print(f"Error with hardware control: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()