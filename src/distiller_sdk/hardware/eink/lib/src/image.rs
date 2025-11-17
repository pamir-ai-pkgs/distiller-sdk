//! Image processing utilities for converting images to e-ink display format.

use image::Pixel;

use crate::{config, error::DisplayError, firmware::DisplaySpec};

/// Convert any supported image format to 1-bit format for a specific display
/// spec
///
/// # Errors
///
/// Returns `DisplayError::Png` if the file cannot be read or conversion fails
pub fn convert_image_to_1bit_with_spec(
    filename: &str,
    spec: &DisplaySpec,
) -> Result<Vec<u8>, DisplayError> {
    // Load image using the image crate (supports multiple formats)
    let img = image::open(filename)
        .map_err(|e| DisplayError::Png(format!("Failed to load image: {e}")))?;

    // Check dimensions
    if img.width() != spec.width || img.height() != spec.height {
        return Err(DisplayError::Png(format!(
            "Invalid image size: {}x{}, expected {}x{}",
            img.width(),
            img.height(),
            spec.width,
            spec.height
        )));
    }

    let mut output = vec![0u8; spec.array_size()];

    // Convert to RGBA and process
    let rgba = img.to_rgba8();

    for y in 0..spec.height {
        for x in 0..spec.width {
            let pixel = rgba.get_pixel(x, y);
            let channels = pixel.channels();

            // Convert RGBA to grayscale
            let gray =
                (u16::from(channels[0]) + u16::from(channels[1]) + u16::from(channels[2])) / 3;

            // Convert to 1-bit (threshold at 128)
            let bit_value = u8::from(gray > 128);

            // Pack into output buffer
            let byte_idx = (y * spec.width + x) / 8;
            let bit_idx = (y * spec.width + x) % 8;

            if bit_value == 1 {
                output[byte_idx as usize] |= 1 << (7 - bit_idx);
            }
        }
    }

    Ok(output)
}

/// Convert a PNG image to 1-bit format for a specific display spec (legacy
/// compatibility)
///
/// # Errors
///
/// Returns `DisplayError::Png` if the file cannot be read or conversion fails
pub fn convert_png_to_1bit_with_spec(
    filename: &str,
    spec: &DisplaySpec,
) -> Result<Vec<u8>, DisplayError> {
    // Just use the generic image converter
    convert_image_to_1bit_with_spec(filename, spec)
}

/// Convert any supported image format to 1-bit format using the default
/// firmware spec
///
/// # Errors
///
/// Returns `DisplayError` if the file cannot be read or conversion fails
pub fn convert_image_to_1bit(filename: &str) -> Result<Vec<u8>, DisplayError> {
    let spec = config::get_default_spec()?;
    convert_image_to_1bit_with_spec(filename, &spec)
}

/// Convert a PNG image to 1-bit format using the default firmware spec (legacy
/// compatibility)
///
/// # Errors
///
/// Returns `DisplayError` if the file cannot be read or conversion fails
pub fn convert_png_to_1bit(filename: &str) -> Result<Vec<u8>, DisplayError> {
    convert_image_to_1bit(filename)
}

/// Get display dimensions from a display spec
#[must_use]
pub const fn get_dimensions_from_spec(spec: &DisplaySpec) -> (u32, u32) {
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
