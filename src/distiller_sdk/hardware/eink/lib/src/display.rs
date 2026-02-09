//! Display module providing high-level e-ink display control.

use std::sync::Mutex;

use crate::{
    error::DisplayError,
    image,
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
        invert: bool,
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
    /// Set the partial refresh base map by writing to both RAM buffers
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if write fails
    fn set_partial_base_map(&mut self, data: &[u8]) -> Result<(), DisplayError>;
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

        // EPD128x250: rotate landscape (250×128) → portrait (128×250) for vendor
        // controller
        let hw_data = if spec.width == 250 && spec.height == 128 {
            crate::image_processing::ImageProcessor::rotate_1bit_90(data, spec.width, spec.height)
        } else {
            data.to_vec()
        };

        match mode {
            DisplayMode::Grayscale4 => {
                return Err(DisplayError::Config(
                    "Grayscale4 mode requires display_image_auto, not display_image_raw".into(),
                ));
            },
            DisplayMode::Partial => self.protocol.init_partial()?,
            DisplayMode::Fast => self.protocol.init_fast(0x64)?, // 100°C
            DisplayMode::Turbo => self.protocol.init_fast(0x5A)?, // 90°C
            DisplayMode::Full => {},
        }

        let write_ram_cmd = self.protocol.get_write_ram_command();
        self.protocol.write_cmd(write_ram_cmd)?;
        self.protocol.write_image_data(&hw_data)?;

        // Turbo mode also writes zeros to secondary RAM (0x26)
        if matches!(mode, DisplayMode::Turbo) {
            let zeros = vec![0x00u8; self.protocol.get_spec().array_size()];
            self.protocol.write_secondary_ram(&zeros)?;
        }

        self.protocol.update_display(mode)?;

        Ok(())
    }

    fn display_image_png(&mut self, filename: &str, mode: DisplayMode) -> Result<(), DisplayError> {
        if matches!(mode, DisplayMode::Grayscale4) {
            return Err(DisplayError::Config(
                "Grayscale4 mode requires display_image_auto".into(),
            ));
        }
        let spec = self.protocol.get_spec();
        let raw_data = image::convert_png_to_1bit_with_spec(filename, spec)?;
        self.display_image_raw(&raw_data, mode)
    }

    fn display_image_file(
        &mut self,
        filename: &str,
        mode: DisplayMode,
    ) -> Result<(), DisplayError> {
        if matches!(mode, DisplayMode::Grayscale4) {
            return Err(DisplayError::Config(
                "Grayscale4 mode requires display_image_auto".into(),
            ));
        }
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
        invert: bool,
    ) -> Result<(), DisplayError> {
        if !self.initialized {
            return Err(DisplayError::NotInitialized);
        }

        let spec = self.protocol.get_spec();
        let processor = crate::image_processing::ImageProcessor::new(spec.clone());

        if let DisplayMode::Grayscale4 = mode {
            // 4-gray pipeline: scale to VENDOR dimensions (portrait for EPD128x250)
            let (vendor_w, vendor_h) = if spec.width == 250 && spec.height == 128 {
                (128u32, 250u32) // Portrait for SSD1680 controller
            } else {
                (spec.width, spec.height)
            };

            // EPD128x250: rotate CW 90° to convert landscape→portrait before scaling
            let rotate_cw90 = spec.width == 250 && spec.height == 128;

            let (ram_24, ram_26) = processor.process_image_4gray(
                filename,
                vendor_w,
                vendor_h,
                scale_mode,
                invert,
                rotate_cw90,
            )?;

            self.protocol.display_4gray(&ram_24, &ram_26)
        } else {
            let raw_data = processor.process_image(
                filename,
                scale_mode,
                dither_mode,
                None, // brightness
                None, // contrast
                invert,
            )?;

            self.display_image_raw(&raw_data, mode)
        }
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

    fn set_partial_base_map(&mut self, data: &[u8]) -> Result<(), DisplayError> {
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

        // EPD128x250: rotate landscape (250×128) → portrait (128×250) for vendor
        // controller
        let hw_data = if spec.width == 250 && spec.height == 128 {
            crate::image_processing::ImageProcessor::rotate_1bit_90(data, spec.width, spec.height)
        } else {
            data.to_vec()
        };

        let write_ram_cmd = self.protocol.get_write_ram_command();
        self.protocol.write_cmd(write_ram_cmd)?;
        self.protocol.write_image_data(&hw_data)?;

        self.protocol.write_secondary_ram(&hw_data)?;

        // Perform full update to establish baseline
        self.protocol.update_display(DisplayMode::Full)?;

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
    invert: bool,
) -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if let Some(display) = &mut state.display {
        display.display_image_auto(filename, mode, scale_mode, dither_mode, invert)
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

/// Set the partial refresh base map by writing image to both RAM buffers
///
/// # Errors
///
/// Returns `DisplayError` if the display is not initialized or write fails
pub fn display_set_partial_base_map(data: &[u8]) -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire state lock: {e}")))?;

    if let Some(display) = &mut state.display {
        display.set_partial_base_map(data)
    } else {
        Err(DisplayError::NotInitialized)
    }
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
