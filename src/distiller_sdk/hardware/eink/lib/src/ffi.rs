use std::{
    ffi::CStr,
    os::raw::{c_char, c_int, c_uint},
    ptr,
};

use crate::{config, display, protocol::DisplayMode};

// C FFI exports

/// Initialize the display hardware.
///
/// # Safety
///
/// This function is safe to call from C code. It initializes internal state
/// and hardware resources. Should be called before any other display
/// operations.
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub extern "C" fn display_init() -> c_int {
    match display::display_init() {
        Ok(()) => 1, // true
        Err(e) => {
            log::error!("Display init failed: {e}");
            0 // false
        },
    }
}

/// Display a raw 1-bit image on the e-ink display.
///
/// # Safety
///
/// The caller must ensure:
/// - `data` is a valid pointer to at least `array_size` bytes
/// - `data` remains valid for the duration of this call
/// - The data size matches the configured display's expected array size
///
/// # Parameters
///
/// - `data`: Pointer to raw 1-bit image data
/// - `mode`: Display mode (0 = Full, 1 = Partial)
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_image_raw(data: *const u8, mode: c_int) -> c_int {
    if data.is_null() {
        return 0;
    }

    // Get the configured firmware array size
    let array_size = match config::get_default_spec() {
        Ok(spec) => spec.array_size(),
        Err(e) => {
            log::error!("Failed to get default firmware spec: {e}");
            return 0; // Return error instead of using fallback
        },
    };
    let data_slice = unsafe { std::slice::from_raw_parts(data, array_size) };
    let display_mode = match mode {
        0 => DisplayMode::Full,
        1 => DisplayMode::Partial,
        _ => return 0,
    };

    match display::display_image_raw(data_slice, display_mode) {
        Ok(()) => 1,
        Err(e) => {
            log::error!("Display image raw failed: {e}");
            0
        },
    }
}

/// Display a PNG image on the e-ink display.
///
/// # Safety
///
/// The caller must ensure:
/// - `filename` is a valid pointer to a null-terminated C string
/// - The string remains valid for the duration of this call
///
/// # Parameters
///
/// - `filename`: Path to PNG file as null-terminated C string
/// - `mode`: Display mode (0 = Full, 1 = Partial)
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_image_png(filename: *const c_char, mode: c_int) -> c_int {
    if filename.is_null() {
        return 0;
    }

    let Ok(filename_str) = unsafe { CStr::from_ptr(filename) }.to_str() else {
        return 0;
    };

    let display_mode = match mode {
        0 => DisplayMode::Full,
        1 => DisplayMode::Partial,
        _ => return 0,
    };

    match display::display_image_png(filename_str, display_mode) {
        Ok(()) => 1,
        Err(e) => {
            log::error!("Display image PNG failed: {e}");
            0
        },
    }
}

/// Display any supported image file format on the e-ink display.
///
/// # Safety
///
/// The caller must ensure:
/// - `filename` is a valid pointer to a null-terminated C string
/// - The string remains valid for the duration of this call
///
/// # Parameters
///
/// - `filename`: Path to image file as null-terminated C string
/// - `mode`: Display mode (0 = Full, 1 = Partial)
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_image_file(filename: *const c_char, mode: c_int) -> c_int {
    if filename.is_null() {
        return 0;
    }

    let Ok(filename_str) = unsafe { CStr::from_ptr(filename) }.to_str() else {
        return 0;
    };

    let display_mode = match mode {
        0 => DisplayMode::Full,
        1 => DisplayMode::Partial,
        _ => return 0,
    };

    match display::display_image_file(filename_str, display_mode) {
        Ok(()) => 1,
        Err(e) => {
            log::error!("Display image file failed: {e}");
            0
        },
    }
}

/// Display image with automatic processing (scaling and dithering).
///
/// # Safety
///
/// The caller must ensure:
/// - `filename` is a valid pointer to a null-terminated C string
/// - The string remains valid for the duration of this call
///
/// # Parameters
///
/// - `filename`: Path to image file as null-terminated C string
/// - `mode`: Display mode (0 = Full, 1 = Partial)
/// - `scale_mode`: Scale mode (0 = Letterbox, 1 = `CropCenter`, 2 = Stretch)
/// - `dither_mode`: Dither mode (0 = Threshold, 1 = `FloydSteinberg`, 2 =
///   Ordered)
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_image_auto(
    filename: *const c_char,
    mode: c_int,
    scale_mode: c_int,
    dither_mode: c_int,
) -> c_int {
    if filename.is_null() {
        return 0;
    }

    let Ok(filename_str) = unsafe { CStr::from_ptr(filename) }.to_str() else {
        return 0;
    };

    let display_mode = match mode {
        0 => DisplayMode::Full,
        1 => DisplayMode::Partial,
        _ => return 0,
    };

    let scale = match scale_mode {
        0 => crate::image_processing::ScaleMode::Letterbox,
        1 => crate::image_processing::ScaleMode::CropCenter,
        2 => crate::image_processing::ScaleMode::Stretch,
        _ => return 0,
    };

    let dither = match dither_mode {
        0 => crate::image_processing::DitherMode::Threshold,
        1 => crate::image_processing::DitherMode::FloydSteinberg,
        2 => crate::image_processing::DitherMode::Ordered,
        _ => return 0,
    };

    match display::display_image_auto(filename_str, display_mode, scale, dither) {
        Ok(()) => 1,
        Err(e) => {
            log::error!("Display image auto failed: {e}");
            0
        },
    }
}

/// Clear the display to white.
///
/// # Safety
///
/// This function is safe to call from C code. The display must be initialized
/// before calling this function.
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub extern "C" fn display_clear() -> c_int {
    match display::display_clear() {
        Ok(()) => 1,
        Err(e) => {
            log::error!("Display clear failed: {e}");
            0
        },
    }
}

/// Put the display into sleep mode.
///
/// # Safety
///
/// This function is safe to call from C code. The display must be initialized
/// before calling this function.
#[unsafe(no_mangle)]
pub extern "C" fn display_sleep() {
    if let Err(e) = display::display_sleep() {
        log::error!("Display sleep failed: {e}");
    }
}

/// Clean up display resources and put it to sleep.
///
/// # Safety
///
/// This function is safe to call from C code. It releases hardware resources
/// and should be called when done using the display.
#[unsafe(no_mangle)]
pub extern "C" fn display_cleanup() {
    if let Err(e) = display::display_cleanup() {
        log::error!("Display cleanup failed: {e}");
    }
}

/// Get the current display dimensions.
///
/// # Safety
///
/// The caller must ensure:
/// - `width` and `height` are valid pointers to writable memory
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `width`: Output pointer for display width in pixels
/// - `height`: Output pointer for display height in pixels
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_get_dimensions(width: *mut c_uint, height: *mut c_uint) {
    if !width.is_null() && !height.is_null() {
        let (w, h) = display::display_get_dimensions();
        unsafe {
            *width = w;
            *height = h;
        }
    }
}

/// Convert a PNG image to 1-bit format suitable for the display.
///
/// # Safety
///
/// The caller must ensure:
/// - `filename` is a valid pointer to a null-terminated C string
/// - `output_data` is a valid pointer to at least `array_size` bytes of
///   writable memory
/// - Both pointers remain valid for the duration of this call
///
/// # Parameters
///
/// - `filename`: Path to PNG file as null-terminated C string
/// - `output_data`: Output buffer for converted 1-bit data
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn convert_png_to_1bit(
    filename: *const c_char,
    output_data: *mut u8,
) -> c_int {
    if filename.is_null() || output_data.is_null() {
        return 0;
    }

    let Ok(filename_str) = unsafe { CStr::from_ptr(filename) }.to_str() else {
        return 0;
    };

    match display::convert_png_to_1bit(filename_str) {
        Ok(data) => {
            // Get the configured firmware array size
            let array_size = match config::get_default_spec() {
                Ok(spec) => spec.array_size(),
                Err(e) => {
                    log::error!("Failed to get default firmware spec: {e}");
                    return 0; // Return error instead of using fallback
                },
            };
            unsafe {
                ptr::copy_nonoverlapping(data.as_ptr(), output_data, array_size);
            }
            1
        },
        Err(e) => {
            log::error!("Convert PNG to 1bit failed: {e}");
            0
        },
    }
}

// Configuration FFI functions

/// Set the display firmware type.
///
/// # Safety
///
/// The caller must ensure:
/// - `firmware_str` is a valid pointer to a null-terminated C string
/// - The string remains valid for the duration of this call
///
/// # Parameters
///
/// - `firmware_str`: Firmware type name (e.g., `"EPD128x250"`, `"EPD240x416"`)
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_set_firmware(firmware_str: *const c_char) -> c_int {
    if firmware_str.is_null() {
        return 0;
    }

    let firmware_str = unsafe {
        match CStr::from_ptr(firmware_str).to_str() {
            Ok(s) => s,
            Err(_) => return 0,
        }
    };

    match config::set_default_firmware_from_str(firmware_str) {
        Ok(()) => 1,
        Err(e) => {
            log::error!("Failed to set firmware: {e}");
            0
        },
    }
}

/// Get the current display firmware type.
///
/// # Safety
///
/// The caller must ensure:
/// - `firmware_str` is a valid pointer to at least `max_len` bytes of writable
///   memory
/// - The pointer remains valid for the duration of this call
///
/// # Parameters
///
/// - `firmware_str`: Output buffer for firmware type name
/// - `max_len`: Maximum length of the output buffer
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_get_firmware(firmware_str: *mut c_char, max_len: c_uint) -> c_int {
    if firmware_str.is_null() || max_len == 0 {
        return 0;
    }

    match config::get_default_firmware() {
        Ok(firmware_type) => {
            let firmware_name = firmware_type.as_str();
            let name_bytes = firmware_name.as_bytes();

            if name_bytes.len() + 1 > max_len as usize {
                return 0; // Buffer too small
            }

            unsafe {
                ptr::copy_nonoverlapping(
                    name_bytes.as_ptr(),
                    firmware_str.cast::<u8>(),
                    name_bytes.len(),
                );
                *firmware_str.add(name_bytes.len()) = 0; // Null terminator
            }
            1
        },
        Err(e) => {
            log::error!("Failed to get firmware: {e}");
            0
        },
    }
}

/// Initialize the display configuration system.
///
/// # Safety
///
/// This function is safe to call from C code. It loads configuration from
/// environment variables and configuration files.
///
/// # Returns
///
/// 1 on success, 0 on failure
#[unsafe(no_mangle)]
pub extern "C" fn display_initialize_config() -> c_int {
    match config::initialize_config() {
        Ok(()) => 1,
        Err(e) => {
            log::error!("Failed to initialize config: {e}");
            0
        },
    }
}
