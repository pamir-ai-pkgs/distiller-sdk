//! FFI exports for image processing functions
//!
//! This module provides C-compatible functions for all image processing
//! operations.

use std::{
    ffi::CStr,
    os::raw::{c_char, c_float, c_int, c_uint},
    ptr,
    slice,
};

use crate::{
    config,
    image_processing::{
        DitherMode,
        ImageProcessor,
        ScaleMode,
        ShapeDrawer,
        TextRenderer,
        Transform,
    },
};

// Transform operations

/// Apply rotation transformation to 1-bit image data
///
/// # Safety
///
/// The caller must ensure:
/// - `data` is a valid pointer to at least `(width * height) / 8` bytes
/// - `output` is a valid pointer to at least `(new_width * new_height) / 8`
///   bytes
/// - All pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `data`: Input 1-bit image data
/// - `width`: Image width in pixels
/// - `height`: Image height in pixels
/// - `rotation`: Rotation angle (0=90°, 1=180°, 2=270°)
/// - `output`: Output buffer for transformed data
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn image_rotate_1bit(
    data: *const u8,
    width: c_uint,
    height: c_uint,
    rotation: c_int,
    output: *mut u8,
) -> c_int {
    if data.is_null() || output.is_null() {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let processor = ImageProcessor::new(spec);
    let data_size = ((width * height) / 8) as usize;
    let data_slice = unsafe { slice::from_raw_parts(data, data_size) };

    let result = match rotation {
        0 => processor.rotate_1bit_90(data_slice, width, height),
        1 => {
            // Rotate 180 = rotate 90 twice
            let temp = processor.rotate_1bit_90(data_slice, width, height);
            processor.rotate_1bit_90(&temp, height, width)
        },
        2 => {
            // Rotate 270 = rotate 90 three times
            let temp1 = processor.rotate_1bit_90(data_slice, width, height);
            let temp2 = processor.rotate_1bit_90(&temp1, height, width);
            processor.rotate_1bit_90(&temp2, width, height)
        },
        _ => return 0,
    };

    let output_size = result.len();
    unsafe {
        ptr::copy_nonoverlapping(result.as_ptr(), output, output_size);
    }
    1
}

/// Invert a 1-bit image (swap black and white)
///
/// # Safety
///
/// The caller must ensure:
/// - `data` is a valid pointer to at least `size` bytes
/// - `output` is a valid pointer to at least `size` bytes
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `data`: Input 1-bit image data
/// - `size`: Size of data in bytes
/// - `output`: Output buffer for inverted data
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn image_invert_1bit(
    data: *const u8,
    size: c_uint,
    output: *mut u8,
) -> c_int {
    if data.is_null() || output.is_null() || size == 0 {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let processor = ImageProcessor::new(spec);
    let data_slice = unsafe { slice::from_raw_parts(data, size as usize) };
    let inverted = processor.invert_1bit(data_slice);

    unsafe {
        ptr::copy_nonoverlapping(inverted.as_ptr(), output, size as usize);
    }
    1
}

/// Flip a 1-bit image horizontally (mirror left-right)
///
/// # Safety
///
/// The caller must ensure:
/// - `data` is a valid pointer to at least `(width * height) / 8` bytes
/// - `output` is a valid pointer to at least `(width * height) / 8` bytes
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `data`: Input 1-bit image data
/// - `width`: Image width in pixels
/// - `height`: Image height in pixels
/// - `output`: Output buffer for flipped data
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn image_flip_horizontal_1bit(
    data: *const u8,
    width: c_uint,
    height: c_uint,
    output: *mut u8,
) -> c_int {
    if data.is_null() || output.is_null() || width == 0 || height == 0 {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let processor = ImageProcessor::new(spec);
    let data_size = ((width * height) / 8) as usize;
    let data_slice = unsafe { slice::from_raw_parts(data, data_size) };
    let flipped = processor.flip_horizontal_1bit(data_slice, width, height);

    unsafe {
        ptr::copy_nonoverlapping(flipped.as_ptr(), output, data_size);
    }
    1
}

/// Flip a 1-bit image vertically (mirror top-bottom)
///
/// # Safety
///
/// The caller must ensure:
/// - `data` is a valid pointer to at least `(width * height) / 8` bytes
/// - `output` is a valid pointer to at least `(width * height) / 8` bytes
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `data`: Input 1-bit image data
/// - `width`: Image width in pixels
/// - `height`: Image height in pixels
/// - `output`: Output buffer for flipped data
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn image_flip_vertical_1bit(
    data: *const u8,
    width: c_uint,
    height: c_uint,
    output: *mut u8,
) -> c_int {
    if data.is_null() || output.is_null() || width == 0 || height == 0 {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let processor = ImageProcessor::new(spec);
    let data_size = ((width * height) / 8) as usize;
    let data_slice = unsafe { slice::from_raw_parts(data, data_size) };
    let flipped = processor.flip_vertical_1bit(data_slice, width, height);

    unsafe {
        ptr::copy_nonoverlapping(flipped.as_ptr(), output, data_size);
    }
    1
}

// Dithering operations

/// Apply dithering to grayscale image data
///
/// # Safety
///
/// The caller must ensure:
/// - `gray_data` is a valid pointer to at least `width * height` bytes
/// - `output` is a valid pointer to at least `(width * height) / 8` bytes
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `gray_data`: Input grayscale image data (one byte per pixel)
/// - `width`: Image width in pixels
/// - `height`: Image height in pixels
/// - `mode`: Dithering mode (0=Threshold, 1=FloydSteinberg, 2=Ordered)
/// - `output`: Output buffer for 1-bit dithered data
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn image_dither(
    gray_data: *const u8,
    width: c_uint,
    height: c_uint,
    mode: c_int,
    output: *mut u8,
) -> c_int {
    if gray_data.is_null() || output.is_null() {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let processor = ImageProcessor::new(spec);
    let data_size = (width * height) as usize;
    let data_slice = unsafe { slice::from_raw_parts(gray_data, data_size) };

    // Create GrayImage from raw data
    let Some(gray_image) = image::GrayImage::from_raw(width, height, data_slice.to_vec()) else {
        return 0;
    };

    let dither_mode = match mode {
        0 => DitherMode::Threshold,
        1 => DitherMode::FloydSteinberg,
        2 => DitherMode::Ordered,
        _ => return 0,
    };

    let dithered = processor.dither(&gray_image, dither_mode);
    let output_size = dithered.len();

    unsafe {
        ptr::copy_nonoverlapping(dithered.as_ptr(), output, output_size);
    }
    1
}

// Image processing pipeline

/// Process an image file with comprehensive transformations
///
/// # Safety
///
/// The caller must ensure:
/// - `path` is a valid pointer to a null-terminated C string
/// - `output` is a valid pointer to at least `array_size` bytes
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `path`: Path to input image file
/// - `scale_mode`: Scaling mode (0=Letterbox, 1=CropCenter, 2=Stretch)
/// - `dither_mode`: Dithering mode (0=Threshold, 1=FloydSteinberg, 2=Ordered)
/// - `brightness`: Brightness adjustment (-100 to +100, or -999 for none)
/// - `contrast`: Contrast adjustment (-100 to +100, or -999 for none)
/// - `transform`: Transformation (0=None, 1=Rotate90, 2=Rotate180, 3=Rotate270,
///   4=FlipH, 5=FlipV)
/// - `invert`: Whether to invert the image (0=false, 1=true)
/// - `output`: Output buffer for processed 1-bit data
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn image_process(
    path: *const c_char,
    scale_mode: c_int,
    dither_mode: c_int,
    brightness: c_int,
    contrast: c_float,
    transform: c_int,
    invert: c_int,
    output: *mut u8,
) -> c_int {
    if path.is_null() || output.is_null() {
        return 0;
    }

    let path_str = unsafe {
        match CStr::from_ptr(path).to_str() {
            Ok(s) => s,
            Err(_) => return 0,
        }
    };

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let processor = ImageProcessor::new(spec);

    let scale = match scale_mode {
        0 => ScaleMode::Letterbox,
        1 => ScaleMode::CropCenter,
        2 => ScaleMode::Stretch,
        _ => return 0,
    };

    let dither = match dither_mode {
        0 => DitherMode::Threshold,
        1 => DitherMode::FloydSteinberg,
        2 => DitherMode::Ordered,
        _ => return 0,
    };

    let transform_opt = match transform {
        0 => None,
        1 => Some(Transform::Rotate90),
        2 => Some(Transform::Rotate180),
        3 => Some(Transform::Rotate270),
        4 => Some(Transform::FlipHorizontal),
        5 => Some(Transform::FlipVertical),
        _ => return 0,
    };

    let brightness_opt = if brightness == -999 {
        None
    } else {
        Some(brightness)
    };

    let contrast_opt = if contrast < -900.0 {
        None
    } else {
        Some(contrast)
    };

    match processor.process_image(
        path_str,
        scale,
        dither,
        brightness_opt,
        contrast_opt,
        transform_opt,
        invert != 0,
    ) {
        Ok(data) => {
            unsafe {
                ptr::copy_nonoverlapping(data.as_ptr(), output, data.len());
            }
            1
        },
        Err(_) => 0,
    }
}

// Text rendering

/// Render text to a 1-bit image buffer
///
/// # Safety
///
/// The caller must ensure:
/// - `text` is a valid pointer to a null-terminated C string
/// - `output` is a valid pointer to at least `array_size` bytes
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `text`: Text string to render
/// - `x`: X position for text
/// - `y`: Y position for text
/// - `scale`: Text scale factor (1=normal, 2=double, etc.)
/// - `invert`: Whether to invert text (0=false, 1=true)
/// - `output`: Output buffer for 1-bit image data
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn text_render(
    text: *const c_char,
    x: c_uint,
    y: c_uint,
    scale: c_uint,
    invert: c_int,
    output: *mut u8,
) -> c_int {
    if text.is_null() || output.is_null() {
        return 0;
    }

    let text_str = unsafe {
        match CStr::from_ptr(text).to_str() {
            Ok(s) => s,
            Err(_) => return 0,
        }
    };

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let renderer = TextRenderer::new(spec.width, spec.height);
    let scale = if scale == 0 { 1 } else { scale };
    let buffer = renderer.render_text(text_str, x, y, scale, invert != 0);

    unsafe {
        ptr::copy_nonoverlapping(buffer.as_ptr(), output, buffer.len());
    }
    1
}

/// Overlay text on an existing 1-bit image buffer
///
/// # Safety
///
/// The caller must ensure:
/// - `buffer` is a valid pointer to at least `array_size` bytes of writable
///   memory
/// - `text` is a valid pointer to a null-terminated C string
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `buffer`: Existing 1-bit image buffer to modify
/// - `text`: Text string to overlay
/// - `x`: X position for text
/// - `y`: Y position for text
/// - `scale`: Text scale factor (1=normal, 2=double, etc.)
/// - `invert`: Whether to invert text (0=false, 1=true)
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn text_overlay(
    buffer: *mut u8,
    text: *const c_char,
    x: c_uint,
    y: c_uint,
    scale: c_uint,
    invert: c_int,
) -> c_int {
    if buffer.is_null() || text.is_null() {
        return 0;
    }

    let text_str = unsafe {
        match CStr::from_ptr(text).to_str() {
            Ok(s) => s,
            Err(_) => return 0,
        }
    };

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let renderer = TextRenderer::new(spec.width, spec.height);
    let buffer_size = spec.array_size();
    let buffer_slice = unsafe { slice::from_raw_parts_mut(buffer, buffer_size) };

    let scale = if scale == 0 { 1 } else { scale };
    renderer.overlay_text(buffer_slice, text_str, x, y, scale, invert != 0);
    1
}

// Shape drawing

/// Draw a filled rectangle on a 1-bit image buffer
///
/// # Safety
///
/// The caller must ensure:
/// - `buffer` is a valid pointer to at least `array_size` bytes of writable
///   memory
/// - The pointer remains valid for the duration of this call
///
/// # Parameters
///
/// - `buffer`: 1-bit image buffer to modify
/// - `x`: X position of rectangle
/// - `y`: Y position of rectangle
/// - `width`: Rectangle width
/// - `height`: Rectangle height
/// - `value`: Fill value (0=black, 1=white)
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn shape_draw_rect_filled(
    buffer: *mut u8,
    x: c_uint,
    y: c_uint,
    width: c_uint,
    height: c_uint,
    value: c_int,
) -> c_int {
    if buffer.is_null() {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let drawer = ShapeDrawer::new(spec.width, spec.height);
    let buffer_size = spec.array_size();
    let buffer_slice = unsafe { slice::from_raw_parts_mut(buffer, buffer_size) };

    drawer.draw_rect_filled(buffer_slice, x, y, width, height, value != 0);
    1
}

/// Draw a rectangle outline on a 1-bit image buffer
///
/// # Safety
///
/// The caller must ensure:
/// - `buffer` is a valid pointer to at least `array_size` bytes of writable
///   memory
/// - The pointer remains valid for the duration of this call
///
/// # Parameters
///
/// - `buffer`: 1-bit image buffer to modify
/// - `x`: X position of rectangle
/// - `y`: Y position of rectangle
/// - `width`: Rectangle width
/// - `height`: Rectangle height
/// - `thickness`: Outline thickness in pixels
/// - `value`: Line value (0=black, 1=white)
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn shape_draw_rect_outline(
    buffer: *mut u8,
    x: c_uint,
    y: c_uint,
    width: c_uint,
    height: c_uint,
    thickness: c_uint,
    value: c_int,
) -> c_int {
    if buffer.is_null() {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let drawer = ShapeDrawer::new(spec.width, spec.height);
    let buffer_size = spec.array_size();
    let buffer_slice = unsafe { slice::from_raw_parts_mut(buffer, buffer_size) };

    drawer.draw_rect_outline(buffer_slice, x, y, width, height, thickness, value != 0);
    1
}

/// Draw a horizontal line on a 1-bit image buffer
///
/// # Safety
///
/// The caller must ensure:
/// - `buffer` is a valid pointer to at least `array_size` bytes of writable
///   memory
/// - The pointer remains valid for the duration of this call
///
/// # Parameters
///
/// - `buffer`: 1-bit image buffer to modify
/// - `x`: X position of line start
/// - `y`: Y position of line
/// - `length`: Line length in pixels
/// - `value`: Line value (0=black, 1=white)
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn shape_draw_line_horizontal(
    buffer: *mut u8,
    x: c_uint,
    y: c_uint,
    length: c_uint,
    value: c_int,
) -> c_int {
    if buffer.is_null() {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let drawer = ShapeDrawer::new(spec.width, spec.height);
    let buffer_size = spec.array_size();
    let buffer_slice = unsafe { slice::from_raw_parts_mut(buffer, buffer_size) };

    drawer.draw_line_horizontal(buffer_slice, x, y, length, value != 0);
    1
}

/// Draw a vertical line on a 1-bit image buffer
///
/// # Safety
///
/// The caller must ensure:
/// - `buffer` is a valid pointer to at least `array_size` bytes of writable
///   memory
/// - The pointer remains valid for the duration of this call
///
/// # Parameters
///
/// - `buffer`: 1-bit image buffer to modify
/// - `x`: X position of line
/// - `y`: Y position of line start
/// - `length`: Line length in pixels
/// - `value`: Line value (0=black, 1=white)
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn shape_draw_line_vertical(
    buffer: *mut u8,
    x: c_uint,
    y: c_uint,
    length: c_uint,
    value: c_int,
) -> c_int {
    if buffer.is_null() {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let drawer = ShapeDrawer::new(spec.width, spec.height);
    let buffer_size = spec.array_size();
    let buffer_slice = unsafe { slice::from_raw_parts_mut(buffer, buffer_size) };

    drawer.draw_line_vertical(buffer_slice, x, y, length, value != 0);
    1
}

// Bit manipulation utilities

/// Pack grayscale bytes into 1-bit format
///
/// # Safety
///
/// The caller must ensure:
/// - `gray_data` is a valid pointer to at least `size` bytes
/// - `output` is a valid pointer to at least `(size + 7) / 8` bytes
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `gray_data`: Input grayscale data (one byte per pixel)
/// - `size`: Number of pixels
/// - `output`: Output buffer for packed 1-bit data
///
/// # Returns
///
/// Number of bytes written to output, or 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn image_pack_1bit(
    gray_data: *const u8,
    size: c_uint,
    output: *mut u8,
) -> c_uint {
    if gray_data.is_null() || output.is_null() || size == 0 {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let processor = ImageProcessor::new(spec);
    let data_slice = unsafe { slice::from_raw_parts(gray_data, size as usize) };
    let packed = processor.pack_1bit(data_slice);

    unsafe {
        ptr::copy_nonoverlapping(packed.as_ptr(), output, packed.len());
    }
    packed.len() as c_uint
}

/// Unpack 1-bit data to grayscale bytes
///
/// # Safety
///
/// The caller must ensure:
/// - `packed_data` is a valid pointer to at least `size` bytes
/// - `output` is a valid pointer to at least `size * 8` bytes
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `packed_data`: Input packed 1-bit data
/// - `size`: Size of packed data in bytes
/// - `output`: Output buffer for grayscale data
///
/// # Returns
///
/// Number of pixels written to output, or 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn image_unpack_1bit(
    packed_data: *const u8,
    size: c_uint,
    output: *mut u8,
) -> c_uint {
    if packed_data.is_null() || output.is_null() || size == 0 {
        return 0;
    }

    let Ok(spec) = config::get_default_spec() else {
        return 0;
    };

    let processor = ImageProcessor::new(spec);
    let data_slice = unsafe { slice::from_raw_parts(packed_data, size as usize) };
    let unpacked = processor.unpack_1bit(data_slice);

    unsafe {
        ptr::copy_nonoverlapping(unpacked.as_ptr(), output, unpacked.len());
    }
    unpacked.len() as c_uint
}
