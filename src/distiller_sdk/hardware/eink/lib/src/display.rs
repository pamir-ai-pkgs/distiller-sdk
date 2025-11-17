//! Display module providing high-level e-ink display control.

use std::sync::Mutex;

use crate::{
    error::DisplayError,
    image,
    image_processing::Transform,
    protocol::{DisplayMode, EinkProtocol, create_default_protocol},
};

/// Display driver trait for different e-ink variants
pub trait DisplayDriver {
    /// Initialize the display hardware
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if hardware initialization fails
    fn init(&mut self) -> Result<(), DisplayError>;
    /// Display a raw 1-bit image
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if image data is invalid or display fails
    fn display_image_raw(&mut self, data: &[u8], mode: DisplayMode) -> Result<(), DisplayError>;
    /// Display a PNG image
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if file cannot be read or display fails
    fn display_image_png(&mut self, filename: &str, mode: DisplayMode) -> Result<(), DisplayError>;
    /// Display any supported image file format
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if file cannot be read or display fails
    fn display_image_file(&mut self, filename: &str, mode: DisplayMode)
    -> Result<(), DisplayError>;
    /// Display image with automatic processing
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if processing or display fails
    fn display_image_auto(
        &mut self,
        filename: &str,
        mode: DisplayMode,
        scale_mode: crate::image_processing::ScaleMode,
        dither_mode: crate::image_processing::DitherMode,
        transform: Option<Transform>,
    ) -> Result<(), DisplayError>;
    /// Clear the display to white
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if clearing fails
    fn clear(&mut self) -> Result<(), DisplayError>;
    /// Put the display into sleep mode
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if sleep command fails
    fn sleep(&mut self) -> Result<(), DisplayError>;
    /// Clean up display resources
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if cleanup fails
    fn cleanup(&mut self) -> Result<(), DisplayError>;
    /// Get the display specifications
    fn get_spec(&self) -> &crate::firmware::DisplaySpec;
}

/// Generic display implementation
pub struct GenericDisplay<P: EinkProtocol> {
    protocol: P,
    initialized: bool,
}

impl<P: EinkProtocol> GenericDisplay<P> {
    /// Create a new generic display with the given protocol
    #[must_use]
    pub const fn new(protocol: P) -> Self {
        Self {
            protocol,
            initialized: false,
        }
    }
}

impl<P: EinkProtocol> DisplayDriver for GenericDisplay<P> {
    fn init(&mut self) -> Result<(), DisplayError> {
        if self.initialized {
            return Ok(());
        }

        self.protocol.init_hardware()?;
        self.initialized = true;

        log::info!("Display SDK initialized successfully");
        Ok(())
    }

    fn display_image_raw(&mut self, data: &[u8], mode: DisplayMode) -> Result<(), DisplayError> {
        if !self.initialized {
            return Err(DisplayError::NotInitialized);
        }

        let spec = self.protocol.get_spec();
        if data.len() != spec.array_size() {
            return Err(DisplayError::InvalidDataSize {
                expected: spec.array_size(),
                actual: data.len(),
            });
        }

        match mode {
            DisplayMode::Partial => self.protocol.init_partial()?,
            DisplayMode::Full => {}, // Full mode uses default initialization
        }

        let write_ram_cmd = self.protocol.get_write_ram_command();
        self.protocol.write_cmd(write_ram_cmd)?;
        self.protocol.write_image_data(data)?;
        self.protocol.update_display(mode)?;

        Ok(())
    }

    fn display_image_png(&mut self, filename: &str, mode: DisplayMode) -> Result<(), DisplayError> {
        let spec = self.protocol.get_spec();
        let raw_data = image::convert_png_to_1bit_with_spec(filename, spec)?;
        self.display_image_raw(&raw_data, mode)
    }

    fn display_image_file(
        &mut self,
        filename: &str,
        mode: DisplayMode,
    ) -> Result<(), DisplayError> {
        let spec = self.protocol.get_spec();
        let raw_data = image::convert_image_to_1bit_with_spec(filename, spec)?;
        self.display_image_raw(&raw_data, mode)
    }

    fn display_image_auto(
        &mut self,
        filename: &str,
        mode: DisplayMode,
        scale_mode: crate::image_processing::ScaleMode,
        dither_mode: crate::image_processing::DitherMode,
        transform: Option<Transform>,
    ) -> Result<(), DisplayError> {
        let spec = self.protocol.get_spec();
        let processor = crate::image_processing::ImageProcessor::new(spec.clone());

        // Process the image with scaling and dithering
        let raw_data = processor.process_image(
            filename,
            scale_mode,
            dither_mode,
            None, // brightness
            None, // contrast
            transform,
            false, // invert
        )?;

        self.display_image_raw(&raw_data, mode)
    }

    fn clear(&mut self) -> Result<(), DisplayError> {
        let spec = self.protocol.get_spec();
        let white_data = image::create_white_image_with_spec(spec);
        self.display_image_raw(&white_data, DisplayMode::Full)
    }

    fn sleep(&mut self) -> Result<(), DisplayError> {
        self.protocol.sleep()
    }

    fn cleanup(&mut self) -> Result<(), DisplayError> {
        if self.initialized {
            self.sleep()?;
            self.initialized = false;
            log::info!("Display SDK cleaned up");
        }
        Ok(())
    }

    fn get_spec(&self) -> &crate::firmware::DisplaySpec {
        self.protocol.get_spec()
    }
}

/// Default display driver type using configurable protocol
pub type DefaultDisplay = GenericDisplay<crate::protocol::DefaultProtocol>;

// Global state for C FFI compatibility
struct GlobalDisplayState {
    display: Option<DefaultDisplay>,
}

static GLOBAL_STATE: Mutex<GlobalDisplayState> = Mutex::new(GlobalDisplayState { display: None });

/// Initialize the display hardware
///
/// # Errors
///
/// Returns `DisplayError` if hardware initialization fails
pub fn display_init() -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if state.display.is_none() {
        let protocol = create_default_protocol()?;
        let mut display = DefaultDisplay::new(protocol);
        display.init()?;
        state.display = Some(display);
    }

    Ok(())
}

/// Display a raw 1-bit image
///
/// # Errors
///
/// Returns `DisplayError` if the display is not initialized or display fails
pub fn display_image_raw(data: &[u8], mode: DisplayMode) -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if let Some(display) = &mut state.display {
        display.display_image_raw(data, mode)
    } else {
        Err(DisplayError::NotInitialized)
    }
}

/// Display a PNG image
///
/// # Errors
///
/// Returns `DisplayError` if the display is not initialized, file cannot be
/// read, or display fails
pub fn display_image_png(filename: &str, mode: DisplayMode) -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if let Some(display) = &mut state.display {
        display.display_image_png(filename, mode)
    } else {
        Err(DisplayError::NotInitialized)
    }
}

/// Display any supported image file format
///
/// # Errors
///
/// Returns `DisplayError` if the display is not initialized, file cannot be
/// read, or display fails
pub fn display_image_file(filename: &str, mode: DisplayMode) -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if let Some(display) = &mut state.display {
        display.display_image_file(filename, mode)
    } else {
        Err(DisplayError::NotInitialized)
    }
}

/// Display image with automatic processing
///
/// # Errors
///
/// Returns `DisplayError` if the display is not initialized, processing fails,
/// or display fails
pub fn display_image_auto(
    filename: &str,
    mode: DisplayMode,
    scale_mode: crate::image_processing::ScaleMode,
    dither_mode: crate::image_processing::DitherMode,
    transform: Option<Transform>,
) -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if let Some(display) = &mut state.display {
        display.display_image_auto(filename, mode, scale_mode, dither_mode, transform)
    } else {
        Err(DisplayError::NotInitialized)
    }
}

/// Clear the display to white
///
/// # Errors
///
/// Returns `DisplayError` if the display is not initialized or clearing fails
pub fn display_clear() -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if let Some(display) = &mut state.display {
        display.clear()
    } else {
        Err(DisplayError::NotInitialized)
    }
}

/// Put the display into sleep mode
///
/// # Errors
///
/// Returns `DisplayError` if the display is not initialized or sleep command
/// fails
pub fn display_sleep() -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if let Some(display) = &mut state.display {
        display.sleep()
    } else {
        Err(DisplayError::NotInitialized)
    }
}

/// Clean up display resources and put it to sleep
///
/// # Errors
///
/// Returns `DisplayError` if cleanup fails
pub fn display_cleanup() -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if let Some(display) = &mut state.display {
        display.cleanup()?;
        state.display = None;
    }

    Ok(())
}

/// Get the current display dimensions
#[must_use]
pub fn display_get_dimensions() -> (u32, u32) {
    // For backwards compatibility, use default firmware
    image::get_dimensions()
}

/// Convert a PNG image to 1-bit format suitable for the display
///
/// # Errors
///
/// Returns `DisplayError` if the file cannot be read or conversion fails
pub fn convert_png_to_1bit(filename: &str) -> Result<Vec<u8>, DisplayError> {
    // For backwards compatibility, use default firmware
    image::convert_png_to_1bit(filename)
}

/// Initialize display with custom firmware
///
/// # Errors
///
/// Returns `DisplayError` if initialization fails
pub fn display_init_with_firmware<F: crate::firmware::DisplayFirmware + 'static>(
    firmware: F,
) -> Result<(), DisplayError> {
    let state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if state.display.is_none() {
        let protocol = crate::protocol::create_protocol_with_firmware(firmware)?;
        let mut display = GenericDisplay::new(protocol);
        display.init()?;
        // Note: This won't work directly due to type system constraints
        // You'd need to use a trait object or enum for runtime firmware
        // selection For now, this is a design template
    }

    Ok(())
}
