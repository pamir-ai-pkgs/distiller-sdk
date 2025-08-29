//! Image processing utilities for converting images to e-ink display format.

use crate::{config, error::DisplayError, firmware::DisplaySpec};

/// Convert a PNG image to 1-bit format for a specific display spec
///
/// # Errors
///
/// Returns `DisplayError::Png` if the file cannot be read or conversion fails
pub fn convert_png_to_1bit_with_spec(
    filename: &str,
    spec: &DisplaySpec,
) -> Result<Vec<u8>, DisplayError> {
    let image = lodepng::decode32_file(filename)
        .map_err(|e| DisplayError::Png(format!("Failed to decode PNG: {e}")))?;

    if image.width != spec.width as usize || image.height != spec.height as usize {
        return Err(DisplayError::Png(format!(
            "Invalid image size: {}x{}, expected {}x{}",
            image.width, image.height, spec.width, spec.height
        )));
    }

    let mut output = vec![0u8; spec.array_size()];

    for y in 0..image.height {
        for x in 0..image.width {
            let pixel_idx = y * image.width + x;
            let pixel = image.buffer[pixel_idx];

            // Convert RGBA to grayscale
            let gray = (u16::from(pixel.r) + u16::from(pixel.g) + u16::from(pixel.b)) / 3;

            // Convert to 1-bit (threshold at 128)
            let bit_value = u8::from(gray > 128);

            // Pack into output buffer
            let byte_idx = (y * image.width + x) / 8;
            let bit_idx = (y * image.width + x) % 8;

            if bit_value == 1 {
                output[byte_idx] |= 1 << (7 - bit_idx);
            }
        }
    }

    Ok(output)
}

/// Convert a PNG image to 1-bit format using the default firmware spec
///
/// # Errors
///
/// Returns `DisplayError` if the file cannot be read or conversion fails
pub fn convert_png_to_1bit(filename: &str) -> Result<Vec<u8>, DisplayError> {
    let spec = config::get_default_spec()?;
    convert_png_to_1bit_with_spec(filename, &spec)
}

/// Get display dimensions from a display spec
#[must_use]
pub fn get_dimensions_from_spec(spec: &DisplaySpec) -> (u32, u32) {
    (spec.width, spec.height)
}

/// Get display dimensions using the default firmware
#[must_use]
pub fn get_dimensions() -> (u32, u32) {
    match config::get_default_spec() {
        Ok(spec) => get_dimensions_from_spec(&spec),
        Err(e) => {
            // Return default values but log the error properly
            log::error!(
                "Failed to get default firmware spec: {e}. Using EPD128x250 dimensions as default"
            );
            (128, 250) // Default dimensions for compatibility
        },
    }
}

/// Create a white image for a specific display spec
#[must_use]
pub fn create_white_image_with_spec(spec: &DisplaySpec) -> Vec<u8> {
    vec![0xFF; spec.array_size()]
}

/// Create a black image for a specific display spec
#[must_use]
pub fn create_black_image_with_spec(spec: &DisplaySpec) -> Vec<u8> {
    vec![0x00; spec.array_size()]
}

/// Create a white image using the default firmware spec
#[must_use]
pub fn create_white_image() -> Vec<u8> {
    match config::get_default_spec() {
        Ok(spec) => create_white_image_with_spec(&spec),
        Err(e) => {
            log::error!(
                "Failed to get default firmware spec: {e}. Using EPD128x250 size as default"
            );
            vec![0xFF; (128 * 250) / 8] // Default size for compatibility
        },
    }
}

/// Create a black image using the default firmware spec
#[must_use]
pub fn create_black_image() -> Vec<u8> {
    match config::get_default_spec() {
        Ok(spec) => create_black_image_with_spec(&spec),
        Err(e) => {
            log::error!(
                "Failed to get default firmware spec: {e}. Using EPD128x250 size as default"
            );
            vec![0x00; (128 * 250) / 8] // Default size for compatibility
        },
    }
}
