#![allow(unused)]

use std::{
    ffi::CStr,
    os::raw::{c_char, c_int, c_uint},
    ptr,
};

use crate::{config, display, error::DisplayError, protocol::DisplayMode};

// Error code constants for FFI
const SUCCESS: c_int = 1;
const ERR_GPIO: c_int = -1;
const ERR_SPI: c_int = -2;
const ERR_CONFIG: c_int = -3;
const ERR_TIMEOUT: c_int = -4;
const ERR_NOT_INITIALIZED: c_int = -5;
const ERR_INVALID_DATA: c_int = -6;
const ERR_PNG: c_int = -7;
const ERR_IO: c_int = -8;
const ERR_UNSUPPORTED_MODE: c_int = -10;
const ERR_UNKNOWN: c_int = -99;

/// Map `DisplayError` to error code
const fn error_to_code(e: &DisplayError) -> c_int {
    match e {
        DisplayError::Gpio(_) => ERR_GPIO,
        DisplayError::Spi(_) => ERR_SPI,
        DisplayError::Png(_) => ERR_PNG,
        DisplayError::NotInitialized => ERR_NOT_INITIALIZED,
        DisplayError::InvalidDataSize { .. } => ERR_INVALID_DATA,
        DisplayError::Timeout => ERR_TIMEOUT,
        DisplayError::Io(_) => ERR_IO,
        DisplayError::Config(_) => ERR_CONFIG,
    }
}

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
/// - 1 on success
/// - Negative error code on failure (see error constants)
#[unsafe(no_mangle)]
pub extern "C" fn display_init() -> c_int {
    match display::display_init() {
        Ok(()) => SUCCESS,
        Err(e) => {
            log::error!("Display init failed: {e}");
            error_to_code(&e)
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
/// - 1 on success
/// - Negative error code on failure (see error constants)
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_image_raw(data: *const u8, mode: c_int) -> c_int {
    if data.is_null() {
        return ERR_INVALID_DATA;
    }

    // Get the configured firmware array size
    let array_size = match config::get_default_spec() {
        Ok(spec) => spec.array_size(),
        Err(e) => {
            log::error!("Failed to get default firmware spec: {e}");
            return error_to_code(&e);
        },
    };
    let data_slice = unsafe { std::slice::from_raw_parts(data, array_size) };
    let display_mode = match mode {
        0 => DisplayMode::Full,
        1 => DisplayMode::Partial,
        2 => DisplayMode::Fast,
        3 => DisplayMode::Turbo,
        _ => return ERR_INVALID_DATA,
    };

    match display::display_image_raw(data_slice, display_mode) {
        Ok(()) => SUCCESS,
        Err(e) => {
            log::error!("Display image raw failed: {e}");
            error_to_code(&e)
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
/// - 1 on success
/// - Negative error code on failure (see error constants)
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_image_png(filename: *const c_char, mode: c_int) -> c_int {
    if filename.is_null() {
        return ERR_INVALID_DATA;
    }

    let Ok(filename_str) = unsafe { CStr::from_ptr(filename) }.to_str() else {
        return ERR_INVALID_DATA;
    };

    let display_mode = match mode {
        0 => DisplayMode::Full,
        1 => DisplayMode::Partial,
        2 => DisplayMode::Fast,
        3 => DisplayMode::Turbo,
        _ => return ERR_INVALID_DATA,
    };

    match display::display_image_png(filename_str, display_mode) {
        Ok(()) => SUCCESS,
        Err(e) => {
            log::error!("Display image PNG failed: {e}");
            error_to_code(&e)
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
/// - 1 on success
/// - Negative error code on failure (see error constants)
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_image_file(filename: *const c_char, mode: c_int) -> c_int {
    if filename.is_null() {
        return ERR_INVALID_DATA;
    }

    let Ok(filename_str) = unsafe { CStr::from_ptr(filename) }.to_str() else {
        return ERR_INVALID_DATA;
    };

    let display_mode = match mode {
        0 => DisplayMode::Full,
        1 => DisplayMode::Partial,
        2 => DisplayMode::Fast,
        3 => DisplayMode::Turbo,
        _ => return ERR_INVALID_DATA,
    };

    match display::display_image_file(filename_str, display_mode) {
        Ok(()) => SUCCESS,
        Err(e) => {
            log::error!("Display image file failed: {e}");
            error_to_code(&e)
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
/// - `mode`: Display mode (0 = Full, 1 = Partial, 2 = Fast, 3 = Turbo, 4 =
///   `Grayscale4`)
/// - `scale_mode`: Scale mode (0 = Letterbox, 1 = `CropCenter`, 2 = Stretch)
/// - `dither_mode`: Dither mode (0 = Threshold, 1 = `FloydSteinberg`, 2 =
///   Ordered). Ignored when mode=4.
/// - `invert`: 0 = normal, 1 = invert colors
///
/// # Returns
///
/// - 1 on success
/// - -10 if mode is unsupported by the current firmware
/// - Negative error code on failure (see error constants)
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_image_auto(
    filename: *const c_char,
    mode: c_int,
    scale_mode: c_int,
    dither_mode: c_int,
    invert: c_int,
) -> c_int {
    if filename.is_null() {
        return ERR_INVALID_DATA;
    }

    let Ok(filename_str) = unsafe { CStr::from_ptr(filename) }.to_str() else {
        return ERR_INVALID_DATA;
    };

    let display_mode = match mode {
        0 => DisplayMode::Full,
        1 => DisplayMode::Partial,
        2 => DisplayMode::Fast,
        3 => DisplayMode::Turbo,
        4 => DisplayMode::Grayscale4,
        _ => return ERR_INVALID_DATA,
    };

    let scale = match scale_mode {
        0 => crate::image_processing::ScaleMode::Letterbox,
        1 => crate::image_processing::ScaleMode::CropCenter,
        2 => crate::image_processing::ScaleMode::Stretch,
        _ => return ERR_INVALID_DATA,
    };

    let dither = match dither_mode {
        0 => crate::image_processing::DitherMode::Threshold,
        1 => crate::image_processing::DitherMode::FloydSteinberg,
        2 => crate::image_processing::DitherMode::Ordered,
        _ => return ERR_INVALID_DATA,
    };

    let invert_bool = invert != 0;

    match display::display_image_auto(filename_str, display_mode, scale, dither, invert_bool) {
        Ok(()) => SUCCESS,
        Err(ref e @ DisplayError::Config(ref msg)) if msg.contains("not supported") => {
            log::error!("Display mode not supported: {e}");
            ERR_UNSUPPORTED_MODE
        },
        Err(e) => {
            log::error!("Display image auto failed: {e}");
            error_to_code(&e)
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
/// - 1 on success
/// - Negative error code on failure (see error constants)
#[unsafe(no_mangle)]
pub extern "C" fn display_clear() -> c_int {
    match display::display_clear() {
        Ok(()) => SUCCESS,
        Err(e) => {
            log::error!("Display clear failed: {e}");
            error_to_code(&e)
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

/// Set the partial refresh base map by writing to both RAM buffers.
///
/// # Safety
///
/// The caller must ensure:
/// - `data` is a valid pointer to at least `array_size` bytes
/// - `data` remains valid for the duration of this call
///
/// # Returns
///
/// - 1 on success
/// - Negative error code on failure
#[unsafe(no_mangle)]
pub unsafe extern "C" fn display_set_partial_base_map(data: *const u8) -> c_int {
    if data.is_null() {
        return ERR_INVALID_DATA;
    }

    let array_size = match config::get_default_spec() {
        Ok(spec) => spec.array_size(),
        Err(e) => {
            log::error!("Failed to get default firmware spec: {e}");
            return error_to_code(&e);
        },
    };
    let data_slice = unsafe { std::slice::from_raw_parts(data, array_size) };

    match display::display_set_partial_base_map(data_slice) {
        Ok(()) => SUCCESS,
        Err(e) => {
            log::error!("Set partial base map failed: {e}");
            error_to_code(&e)
        },
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
/// - 1 on success
/// - Negative error code on failure (see error constants)
#[unsafe(no_mangle)]
pub unsafe extern "C" fn convert_png_to_1bit(
    filename: *const c_char,
    output_data: *mut u8,
) -> c_int {
    if filename.is_null() || output_data.is_null() {
        return ERR_INVALID_DATA;
    }

    let Ok(filename_str) = unsafe { CStr::from_ptr(filename) }.to_str() else {
        return ERR_INVALID_DATA;
    };

    match display::convert_png_to_1bit(filename_str) {
        Ok(data) => {
            // Get the configured firmware array size
            let array_size = match config::get_default_spec() {
                Ok(spec) => spec.array_size(),
                Err(e) => {
                    log::error!("Failed to get default firmware spec: {e}");
                    return error_to_code(&e);
                },
            };
            unsafe {
                ptr::copy_nonoverlapping(data.as_ptr(), output_data, array_size);
            }
            SUCCESS
        },
        Err(e) => {
            log::error!("Convert PNG to 1bit failed: {e}");
            error_to_code(&e)
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
/// - 1 on success
/// - Negative error code on failure (see error constants)
#[unsafe(no_mangle)]
pub extern "C" fn display_initialize_config() -> c_int {
    match config::initialize_config() {
        Ok(()) => SUCCESS,
        Err(e) => {
            log::error!("Failed to initialize config: {e}");
            error_to_code(&e)
        },
    }
}

/// Initialize the Rust logger for this library.
///
/// # Safety
///
/// This function is safe to call from C code. It initializes the `env_logger`
/// for Rust code, allowing `RUST_LOG` environment variable to control logging.
/// Can be called multiple times safely (subsequent calls are no-ops).
#[unsafe(no_mangle)]
pub extern "C" fn display_init_logger() {
    let _ = env_logger::try_init();
}
