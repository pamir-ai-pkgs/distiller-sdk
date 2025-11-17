//! Comprehensive image processing module for e-ink display
//!
//! This module provides a complete set of image processing operations optimized
//! for 1-bit e-ink displays, including transformations, scaling, dithering,
//! text rendering, and shape drawing.

#![allow(clippy::cast_precision_loss)] // Expected for image scaling and coordinate calculations

use image::{DynamicImage, GrayImage, Luma};

use crate::{error::DisplayError, firmware::DisplaySpec};

// Include the font data directly
include!("font_6x8.rs");

// Font dimensions
const FONT_WIDTH: u32 = 6;
const FONT_HEIGHT: u32 = 8;

/// Image transformation operations
#[derive(Debug, Clone, Copy)]
pub enum Transform {
    /// Rotate 90 degrees clockwise
    Rotate90,
    /// Rotate 180 degrees
    Rotate180,
    /// Rotate 270 degrees clockwise (90 degrees counter-clockwise)
    Rotate270,
    /// Flip horizontally (mirror)
    FlipHorizontal,
    /// Flip vertically
    FlipVertical,
}

/// Scaling modes for image resizing
#[derive(Debug, Clone, Copy)]
pub enum ScaleMode {
    /// Maintain aspect ratio with black borders
    Letterbox,
    /// Crop center to fill display
    CropCenter,
    /// Stretch to fit (may distort image)
    Stretch,
}

/// Dithering algorithms for converting grayscale to 1-bit
#[derive(Debug, Clone, Copy)]
pub enum DitherMode {
    /// Simple threshold at 128
    Threshold,
    /// Floyd-Steinberg error diffusion dithering
    FloydSteinberg,
    /// Ordered dithering with Bayer matrix
    Ordered,
}

/// Image processor for e-ink display operations
pub struct ImageProcessor {
    spec: DisplaySpec,
}

impl ImageProcessor {
    /// Create a new image processor for the given display specification
    #[must_use]
    pub const fn new(spec: DisplaySpec) -> Self {
        Self { spec }
    }

    /// Load image from file
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Png` if the image cannot be loaded
    pub fn load_image(&self, path: &str) -> Result<DynamicImage, DisplayError> {
        image::open(path).map_err(|e| DisplayError::Png(format!("Failed to load image: {e}")))
    }

    /// Load image from memory buffer
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Png` if the image cannot be decoded
    pub fn load_image_from_memory(&self, data: &[u8]) -> Result<DynamicImage, DisplayError> {
        image::load_from_memory(data)
            .map_err(|e| DisplayError::Png(format!("Failed to decode image: {e}")))
    }

    /// Apply transformation to an image
    #[must_use]
    pub fn transform(&self, img: &DynamicImage, transform: Transform) -> DynamicImage {
        match transform {
            Transform::Rotate90 => img.rotate90(),
            Transform::Rotate180 => img.rotate180(),
            Transform::Rotate270 => img.rotate270(),
            Transform::FlipHorizontal => img.fliph(),
            Transform::FlipVertical => img.flipv(),
        }
    }

    /// Scale image to display dimensions using the specified mode
    #[must_use]
    pub fn scale(&self, img: &DynamicImage, mode: ScaleMode) -> DynamicImage {
        let (img_width, img_height) = (img.width(), img.height());
        let (disp_width, disp_height) = (self.spec.width, self.spec.height);

        match mode {
            ScaleMode::Stretch => {
                // Simply resize to exact display dimensions
                img.resize_exact(
                    disp_width,
                    disp_height,
                    image::imageops::FilterType::Lanczos3,
                )
            },
            ScaleMode::Letterbox => {
                // Calculate scale to fit within display while maintaining aspect ratio
                let scale_x = disp_width as f32 / img_width as f32;
                let scale_y = disp_height as f32 / img_height as f32;
                let scale = scale_x.min(scale_y);

                let new_width = (img_width as f32 * scale) as u32;
                let new_height = (img_height as f32 * scale) as u32;

                // Resize image
                let resized =
                    img.resize_exact(new_width, new_height, image::imageops::FilterType::Lanczos3);

                // Create black background and paste resized image centered
                let mut output = DynamicImage::new_luma8(disp_width, disp_height);
                let x_offset = (disp_width - new_width) / 2;
                let y_offset = (disp_height - new_height) / 2;

                image::imageops::overlay(&mut output, &resized, x_offset.into(), y_offset.into());
                output
            },
            ScaleMode::CropCenter => {
                // Calculate scale to fill display (may crop)
                let scale_x = disp_width as f32 / img_width as f32;
                let scale_y = disp_height as f32 / img_height as f32;
                let scale = scale_x.max(scale_y);

                let new_width = (img_width as f32 * scale) as u32;
                let new_height = (img_height as f32 * scale) as u32;

                // Resize image
                let resized =
                    img.resize_exact(new_width, new_height, image::imageops::FilterType::Lanczos3);

                // Crop center
                let x_offset = (new_width.saturating_sub(disp_width)) / 2;
                let y_offset = (new_height.saturating_sub(disp_height)) / 2;

                resized.crop_imm(x_offset, y_offset, disp_width, disp_height)
            },
        }
    }

    /// Adjust brightness of an image (-100 to +100)
    #[must_use]
    pub fn adjust_brightness(&self, img: &DynamicImage, brightness: i32) -> DynamicImage {
        let brightness = brightness.clamp(-100, 100);
        img.brighten(brightness)
    }

    /// Adjust contrast of an image (-100 to +100)
    #[must_use]
    pub fn adjust_contrast(&self, img: &DynamicImage, contrast: f32) -> DynamicImage {
        let contrast = contrast.clamp(-100.0, 100.0);
        img.adjust_contrast(contrast)
    }

    /// Convert image to grayscale
    #[must_use]
    pub fn to_grayscale(&self, img: &DynamicImage) -> GrayImage {
        img.to_luma8()
    }

    /// Apply dithering to convert grayscale to 1-bit
    #[must_use]
    pub fn dither(&self, gray: &GrayImage, mode: DitherMode) -> Vec<u8> {
        match mode {
            DitherMode::Threshold => Self::threshold_dither(gray, 128),
            DitherMode::FloydSteinberg => Self::floyd_steinberg_dither(gray),
            DitherMode::Ordered => Self::ordered_dither(gray),
        }
    }

    /// Simple threshold dithering
    fn threshold_dither(gray: &GrayImage, threshold: u8) -> Vec<u8> {
        let (width, height) = gray.dimensions();
        let mut output = vec![0u8; ((width * height) / 8) as usize];

        for (y, row) in gray.rows().enumerate() {
            for (x, pixel) in row.enumerate() {
                let gray_value = pixel[0];
                let bit_value = u8::from(gray_value > threshold);

                let pixel_idx = y * width as usize + x;
                let byte_idx = pixel_idx / 8;
                let bit_idx = pixel_idx % 8;

                if bit_value == 1 {
                    output[byte_idx] |= 1 << (7 - bit_idx);
                }
            }
        }

        output
    }

    /// Floyd-Steinberg error diffusion dithering
    fn floyd_steinberg_dither(gray: &GrayImage) -> Vec<u8> {
        let (width, height) = gray.dimensions();
        let mut work_image = gray.clone();
        let mut output = vec![0u8; ((width * height) / 8) as usize];

        for y in 0..height {
            for x in 0..width {
                let old_pixel = i32::from(work_image.get_pixel(x, y)[0]);
                let new_pixel = if old_pixel > 128 { 255 } else { 0 };
                let error = old_pixel - new_pixel;

                // Set the output bit
                if new_pixel == 255 {
                    let pixel_idx = (y * width + x) as usize;
                    let byte_idx = pixel_idx / 8;
                    let bit_idx = pixel_idx % 8;
                    output[byte_idx] |= 1 << (7 - bit_idx);
                }

                // Distribute error to neighboring pixels
                // Right: 7/16
                if x + 1 < width {
                    let pixel = i32::from(work_image.get_pixel(x + 1, y)[0]);
                    let new_val = (pixel + error * 7 / 16).clamp(0, 255) as u8;
                    work_image.put_pixel(x + 1, y, Luma([new_val]));
                }

                // Bottom-left: 3/16
                if y + 1 < height && x > 0 {
                    let pixel = i32::from(work_image.get_pixel(x - 1, y + 1)[0]);
                    let new_val = (pixel + error * 3 / 16).clamp(0, 255) as u8;
                    work_image.put_pixel(x - 1, y + 1, Luma([new_val]));
                }

                // Bottom: 5/16
                if y + 1 < height {
                    let pixel = i32::from(work_image.get_pixel(x, y + 1)[0]);
                    let new_val = (pixel + error * 5 / 16).clamp(0, 255) as u8;
                    work_image.put_pixel(x, y + 1, Luma([new_val]));
                }

                // Bottom-right: 1/16
                if y + 1 < height && x + 1 < width {
                    let pixel = i32::from(work_image.get_pixel(x + 1, y + 1)[0]);
                    let new_val = (pixel + error / 16).clamp(0, 255) as u8;
                    work_image.put_pixel(x + 1, y + 1, Luma([new_val]));
                }
            }
        }

        output
    }

    /// Ordered dithering using Bayer matrix
    fn ordered_dither(gray: &GrayImage) -> Vec<u8> {
        // 4x4 Bayer matrix
        const BAYER_MATRIX: [[u8; 4]; 4] =
            [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];

        let (width, height) = gray.dimensions();
        let mut output = vec![0u8; ((width * height) / 8) as usize];

        for y in 0..height {
            for x in 0..width {
                let gray_value = gray.get_pixel(x, y)[0];
                let threshold = BAYER_MATRIX[(y % 4) as usize][(x % 4) as usize] * 16;
                let bit_value = u8::from(gray_value > threshold);

                if bit_value == 1 {
                    let pixel_idx = (y * width + x) as usize;
                    let byte_idx = pixel_idx / 8;
                    let bit_idx = pixel_idx % 8;
                    output[byte_idx] |= 1 << (7 - bit_idx);
                }
            }
        }

        output
    }

    /// Invert a 1-bit image (swap black and white)
    #[must_use]
    pub fn invert_1bit(&self, data: &[u8]) -> Vec<u8> {
        data.iter().map(|&byte| !byte).collect()
    }

    /// Rotate 1-bit packed data by 90 degrees clockwise
    #[must_use]
    pub fn rotate_1bit_90(&self, data: &[u8], width: u32, height: u32) -> Vec<u8> {
        let new_width = height;
        let new_height = width;
        let mut output = vec![0u8; ((new_width * new_height) / 8) as usize];

        for y in 0..height {
            for x in 0..width {
                // Get source bit
                let src_idx = (y * width + x) as usize;
                let src_byte_idx = src_idx / 8;
                let src_bit_idx = src_idx % 8;
                let bit_value = (data[src_byte_idx] >> (7 - src_bit_idx)) & 1;

                // Calculate destination position (90 degree rotation)
                let dst_x = height - 1 - y;
                let dst_y = x;
                let dst_idx = (dst_y * new_width + dst_x) as usize;
                let dst_byte_idx = dst_idx / 8;
                let dst_bit_idx = dst_idx % 8;

                if bit_value == 1 {
                    output[dst_byte_idx] |= 1 << (7 - dst_bit_idx);
                }
            }
        }

        output
    }

    /// Flip 1-bit image horizontally (mirror left-right)
    #[must_use]
    pub fn flip_horizontal_1bit(&self, data: &[u8], width: u32, height: u32) -> Vec<u8> {
        let mut output = vec![0u8; ((width * height) / 8) as usize];

        for y in 0..height {
            for x in 0..width {
                // Get source bit
                let src_idx = (y * width + x) as usize;
                let src_byte_idx = src_idx / 8;
                let src_bit_idx = src_idx % 8;
                let bit_value = (data[src_byte_idx] >> (7 - src_bit_idx)) & 1;

                // Calculate flipped position (mirror horizontally)
                let dst_x = width - 1 - x;
                let dst_idx = (y * width + dst_x) as usize;
                let dst_byte_idx = dst_idx / 8;
                let dst_bit_idx = dst_idx % 8;

                if bit_value == 1 {
                    output[dst_byte_idx] |= 1 << (7 - dst_bit_idx);
                }
            }
        }

        output
    }

    /// Flip 1-bit image vertically (mirror top-bottom)
    #[must_use]
    pub fn flip_vertical_1bit(&self, data: &[u8], width: u32, height: u32) -> Vec<u8> {
        let mut output = vec![0u8; ((width * height) / 8) as usize];

        for y in 0..height {
            for x in 0..width {
                // Get source bit
                let src_idx = (y * width + x) as usize;
                let src_byte_idx = src_idx / 8;
                let src_bit_idx = src_idx % 8;
                let bit_value = (data[src_byte_idx] >> (7 - src_bit_idx)) & 1;

                // Calculate flipped position (mirror vertically)
                let dst_y = height - 1 - y;
                let dst_idx = (dst_y * width + x) as usize;
                let dst_byte_idx = dst_idx / 8;
                let dst_bit_idx = dst_idx % 8;

                if bit_value == 1 {
                    output[dst_byte_idx] |= 1 << (7 - dst_bit_idx);
                }
            }
        }

        output
    }

    /// Pack grayscale bytes into 1-bit format (MSB first)
    #[must_use]
    pub fn pack_1bit(&self, data: &[u8]) -> Vec<u8> {
        let mut output = Vec::with_capacity(data.len().div_ceil(8));

        for chunk in data.chunks(8) {
            let mut byte = 0u8;
            for (i, &pixel) in chunk.iter().enumerate() {
                if pixel > 128 {
                    byte |= 1 << (7 - i);
                }
            }
            output.push(byte);
        }

        output
    }

    /// Unpack 1-bit data to grayscale bytes
    #[must_use]
    pub fn unpack_1bit(&self, data: &[u8]) -> Vec<u8> {
        let mut output = Vec::with_capacity(data.len() * 8);

        for &byte in data {
            for i in 0..8 {
                let bit = (byte >> (7 - i)) & 1;
                output.push(if bit == 1 { 255 } else { 0 });
            }
        }

        output
    }

    /// Complete image processing pipeline
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Png` if image processing fails
    #[allow(clippy::too_many_arguments)]
    pub fn process_image(
        &self,
        path: &str,
        scale_mode: ScaleMode,
        dither_mode: DitherMode,
        brightness: Option<i32>,
        contrast: Option<f32>,
        transform: Option<Transform>,
        invert: bool,
    ) -> Result<Vec<u8>, DisplayError> {
        // Load image
        let mut img = self.load_image(path)?;

        // Apply transformation if specified
        if let Some(t) = transform {
            img = self.transform(&img, t);
        }

        // Adjust brightness if specified
        if let Some(b) = brightness {
            img = self.adjust_brightness(&img, b);
        }

        // Adjust contrast if specified
        if let Some(c) = contrast {
            img = self.adjust_contrast(&img, c);
        }

        // Scale to display dimensions
        img = self.scale(&img, scale_mode);

        // Convert to grayscale
        let gray = self.to_grayscale(&img);

        // Apply dithering to get 1-bit data
        let mut data = self.dither(&gray, dither_mode);

        // Invert if requested
        if invert {
            data = self.invert_1bit(&data);
        }

        Ok(data)
    }
}

/// Text renderer for drawing text on 1-bit images
pub struct TextRenderer {
    width: u32,
    height: u32,
}

impl TextRenderer {
    /// Create a new text renderer for the given dimensions
    #[must_use]
    pub const fn new(width: u32, height: u32) -> Self {
        Self { width, height }
    }

    /// Draw a single character at the specified position
    fn draw_char(&self, buffer: &mut [u8], ch: char, x: u32, y: u32, scale: u32, invert: bool) {
        let char_code = ch as usize;
        if !(32..=126).contains(&char_code) {
            return; // Character not in font
        }

        let font_offset = (char_code - 32) * 6;

        for row in 0..FONT_HEIGHT {
            for col in 0..FONT_WIDTH {
                let font_byte_idx = font_offset + col as usize;
                if font_byte_idx >= FONT_6X8_DATA.len() {
                    continue;
                }

                let font_byte = FONT_6X8_DATA[font_byte_idx];
                let bit_set = (font_byte >> row) & 1 == 1;
                let pixel_value = if invert { !bit_set } else { bit_set };

                if pixel_value {
                    // Draw scaled pixel
                    for sy in 0..scale {
                        for sx in 0..scale {
                            let px = x + col * scale + sx;
                            let py = y + row * scale + sy;

                            if px < self.width && py < self.height {
                                let pixel_idx = (py * self.width + px) as usize;
                                let byte_idx = pixel_idx / 8;
                                let bit_idx = pixel_idx % 8;

                                if byte_idx < buffer.len() {
                                    buffer[byte_idx] |= 1 << (7 - bit_idx);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    /// Render text string to 1-bit buffer
    #[must_use]
    pub fn render_text(&self, text: &str, x: u32, y: u32, scale: u32, invert: bool) -> Vec<u8> {
        let buffer_size = ((self.width * self.height) / 8) as usize;
        let mut buffer = vec![0u8; buffer_size];

        let mut current_x = x;
        let char_width = FONT_WIDTH * scale;
        let char_spacing = scale; // Space between characters

        for ch in text.chars() {
            if current_x + char_width > self.width {
                break; // Stop if we run out of space
            }

            self.draw_char(&mut buffer, ch, current_x, y, scale, invert);
            current_x += char_width + char_spacing;
        }

        buffer
    }

    /// Overlay text on existing 1-bit buffer
    pub fn overlay_text(
        &self,
        buffer: &mut [u8],
        text: &str,
        x: u32,
        y: u32,
        scale: u32,
        invert: bool,
    ) {
        let mut current_x = x;
        let char_width = FONT_WIDTH * scale;
        let char_spacing = scale;

        for ch in text.chars() {
            if current_x + char_width > self.width {
                break;
            }

            self.draw_char(buffer, ch, current_x, y, scale, invert);
            current_x += char_width + char_spacing;
        }
    }
}

/// Shape drawing utilities for 1-bit images
pub struct ShapeDrawer {
    width: u32,
    height: u32,
}

impl ShapeDrawer {
    /// Create a new shape drawer for the given dimensions
    #[must_use]
    pub const fn new(width: u32, height: u32) -> Self {
        Self { width, height }
    }

    /// Set a pixel in the buffer
    fn set_pixel(&self, buffer: &mut [u8], x: u32, y: u32, value: bool) {
        if x >= self.width || y >= self.height {
            return;
        }

        let pixel_idx = (y * self.width + x) as usize;
        let byte_idx = pixel_idx / 8;
        let bit_idx = pixel_idx % 8;

        if byte_idx < buffer.len() {
            if value {
                buffer[byte_idx] |= 1 << (7 - bit_idx);
            } else {
                buffer[byte_idx] &= !(1 << (7 - bit_idx));
            }
        }
    }

    /// Draw a filled rectangle
    pub fn draw_rect_filled(
        &self,
        buffer: &mut [u8],
        x: u32,
        y: u32,
        width: u32,
        height: u32,
        value: bool,
    ) {
        let x_end = (x + width).min(self.width);
        let y_end = (y + height).min(self.height);

        for py in y..y_end {
            for px in x..x_end {
                self.set_pixel(buffer, px, py, value);
            }
        }
    }

    /// Draw a rectangle outline
    #[allow(clippy::too_many_arguments)]
    pub fn draw_rect_outline(
        &self,
        buffer: &mut [u8],
        x: u32,
        y: u32,
        width: u32,
        height: u32,
        thickness: u32,
        value: bool,
    ) {
        // Top edge
        self.draw_rect_filled(buffer, x, y, width, thickness, value);
        // Bottom edge
        if y + height > thickness {
            self.draw_rect_filled(buffer, x, y + height - thickness, width, thickness, value);
        }
        // Left edge
        self.draw_rect_filled(buffer, x, y, thickness, height, value);
        // Right edge
        if x + width > thickness {
            self.draw_rect_filled(buffer, x + width - thickness, y, thickness, height, value);
        }
    }

    /// Draw a horizontal line
    pub fn draw_line_horizontal(
        &self,
        buffer: &mut [u8],
        x: u32,
        y: u32,
        length: u32,
        value: bool,
    ) {
        let x_end = (x + length).min(self.width);
        for px in x..x_end {
            self.set_pixel(buffer, px, y, value);
        }
    }

    /// Draw a vertical line
    pub fn draw_line_vertical(&self, buffer: &mut [u8], x: u32, y: u32, length: u32, value: bool) {
        let y_end = (y + length).min(self.height);
        for py in y..y_end {
            self.set_pixel(buffer, x, py, value);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pack_unpack_1bit() {
        let spec = DisplaySpec {
            width: 128,
            height: 250,
            name: "Test".to_string(),
            description: "Test display".to_string(),
        };
        let processor = ImageProcessor::new(spec);

        let original = vec![0, 255, 0, 255, 255, 0, 255, 0];
        let packed = processor.pack_1bit(&original);
        let unpacked = processor.unpack_1bit(&packed);

        assert_eq!(original, unpacked);
    }

    #[test]
    fn test_invert_1bit() {
        let spec = DisplaySpec {
            width: 128,
            height: 250,
            name: "Test".to_string(),
            description: "Test display".to_string(),
        };
        let processor = ImageProcessor::new(spec);

        let data = vec![0b1010_1010, 0b1111_0000];
        let inverted = processor.invert_1bit(&data);

        assert_eq!(inverted, vec![0b0101_0101, 0b0000_1111]);
    }
}
