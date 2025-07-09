use crate::error::DisplayError;
use crate::image;
use crate::protocol::{DisplayMode, EinkProtocol, create_default_protocol};
use std::sync::Mutex;

// Display driver trait for different e-ink variants
pub trait DisplayDriver {
    fn init(&mut self) -> Result<(), DisplayError>;
    fn display_image_raw(&mut self, data: &[u8], mode: DisplayMode) -> Result<(), DisplayError>;
    fn display_image_png(&mut self, filename: &str, mode: DisplayMode) -> Result<(), DisplayError>;
    fn clear(&mut self) -> Result<(), DisplayError>;
    fn sleep(&mut self) -> Result<(), DisplayError>;
    fn cleanup(&mut self) -> Result<(), DisplayError>;
    fn get_spec(&self) -> &crate::firmware::DisplaySpec;
}

// Generic display implementation
pub struct GenericDisplay<P: EinkProtocol> {
    protocol: P,
    initialized: bool,
}

impl<P: EinkProtocol> GenericDisplay<P> {
    pub fn new(protocol: P) -> Self {
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
            DisplayMode::Full => {} // Full mode uses default initialization
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

// Default display driver type
pub type DefaultDisplay = GenericDisplay<crate::protocol::DefaultProtocol>;

// Global state for C FFI compatibility
struct GlobalDisplayState {
    display: Option<DefaultDisplay>,
}

static GLOBAL_STATE: Mutex<GlobalDisplayState> = Mutex::new(GlobalDisplayState { display: None });

// Public Rust API functions
pub fn display_init() -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE.lock().unwrap();

    if state.display.is_none() {
        let protocol = create_default_protocol()?;
        let mut display = DefaultDisplay::new(protocol);
        display.init()?;
        state.display = Some(display);
    }

    Ok(())
}

pub fn display_image_raw(data: &[u8], mode: DisplayMode) -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE.lock().unwrap();

    if let Some(display) = &mut state.display {
        display.display_image_raw(data, mode)
    } else {
        Err(DisplayError::NotInitialized)
    }
}

pub fn display_image_png(filename: &str, mode: DisplayMode) -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE.lock().unwrap();

    if let Some(display) = &mut state.display {
        display.display_image_png(filename, mode)
    } else {
        Err(DisplayError::NotInitialized)
    }
}

pub fn display_clear() -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE.lock().unwrap();

    if let Some(display) = &mut state.display {
        display.clear()
    } else {
        Err(DisplayError::NotInitialized)
    }
}

pub fn display_sleep() -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE.lock().unwrap();

    if let Some(display) = &mut state.display {
        display.sleep()
    } else {
        Err(DisplayError::NotInitialized)
    }
}

pub fn display_cleanup() -> Result<(), DisplayError> {
    let mut state = GLOBAL_STATE.lock().unwrap();

    if let Some(display) = &mut state.display {
        display.cleanup()?;
        state.display = None;
    }

    Ok(())
}

pub fn display_get_dimensions() -> (u32, u32) {
    // For backwards compatibility, use default firmware
    image::get_dimensions()
}

pub fn convert_png_to_1bit(filename: &str) -> Result<Vec<u8>, DisplayError> {
    // For backwards compatibility, use default firmware
    image::convert_png_to_1bit(filename)
}

// Advanced API functions for custom firmware
pub fn display_init_with_firmware<F: crate::firmware::DisplayFirmware + 'static>(
    firmware: F,
) -> Result<(), DisplayError> {
    let state = GLOBAL_STATE.lock().unwrap();

    if state.display.is_none() {
        let protocol = crate::protocol::create_protocol_with_firmware(firmware)?;
        let mut display = GenericDisplay::new(protocol);
        display.init()?;
        // Note: This won't work directly due to type system constraints
        // You'd need to use a trait object or enum for runtime firmware selection
        // For now, this is a design template
    }

    Ok(())
}

