use std::ffi::CStr;
use std::io::Write;
use std::os::raw::{c_char, c_int, c_uint};
use std::ptr;
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use gpiod::{Chip, Input, Lines, Options, Output};
use spidev::{SpiModeFlags, Spidev, SpidevOptions};
use thiserror::Error;

// Display constants
const EPD_WIDTH: u32 = 128;
const EPD_HEIGHT: u32 = 250;
const EPD_ARRAY: usize = ((EPD_WIDTH * EPD_HEIGHT) / 8) as usize; // 4000 bytes

// GPIO pin definitions
const DC_PIN: u32 = 7; // Data/Command control
const RST_PIN: u32 = 13; // Reset
const BUSY_PIN: u32 = 9; // Busy status

// Display modes
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub enum DisplayMode {
    Full = 0,    // Full refresh (slow, high quality)
    Partial = 1, // Partial refresh (fast, good quality)
}

// Error types
#[derive(Error, Debug)]
pub enum DisplayError {
    #[error("GPIO error: {0}")]
    Gpio(String),
    #[error("SPI error: {0}")]
    Spi(String),
    #[error("PNG error: {0}")]
    Png(String),
    #[error("Display not initialized")]
    NotInitialized,
    #[error("Invalid data size: expected {expected}, got {actual}")]
    InvalidDataSize { expected: usize, actual: usize },
    #[error("Timeout waiting for display")]
    Timeout,
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

// GPIO Controller struct to manage GPIO operations
struct GpioController {
    dc_lines: Lines<Output>,  // Data/Command output
    rst_lines: Lines<Output>, // Reset output
    busy_lines: Lines<Input>, // Busy input
}

impl GpioController {
    fn new() -> Result<Self, DisplayError> {
        let chip = Chip::new("/dev/gpiochip0")
            .map_err(|e| DisplayError::Gpio(format!("Failed to open GPIO chip: {}", e)))?;

        // Configure DC pin as output (initially low)
        let dc_opts = Options::output([DC_PIN])
            .values([false])
            .consumer("distiller-display-dc");
        let dc_lines = chip
            .request_lines(dc_opts)
            .map_err(|e| DisplayError::Gpio(format!("Failed to request DC line: {}", e)))?;

        // Configure RST pin as output (initially high)
        let rst_opts = Options::output([RST_PIN])
            .values([true])
            .consumer("distiller-display-rst");
        let rst_lines = chip
            .request_lines(rst_opts)
            .map_err(|e| DisplayError::Gpio(format!("Failed to request RST line: {}", e)))?;

        // Configure BUSY pin as input
        let busy_opts = Options::input([BUSY_PIN]).consumer("distiller-display-busy");
        let busy_lines = chip
            .request_lines(busy_opts)
            .map_err(|e| DisplayError::Gpio(format!("Failed to request BUSY line: {}", e)))?;

        Ok(Self {
            dc_lines,
            rst_lines,
            busy_lines,
        })
    }

    fn write_dc(&self, value: bool) -> Result<(), DisplayError> {
        self.dc_lines
            .set_values([value])
            .map_err(|e| DisplayError::Gpio(format!("Failed to set DC pin: {}", e)))
    }

    fn write_rst(&self, value: bool) -> Result<(), DisplayError> {
        self.rst_lines
            .set_values([value])
            .map_err(|e| DisplayError::Gpio(format!("Failed to set RST pin: {}", e)))
    }

    fn read_busy(&self) -> Result<bool, DisplayError> {
        let values = self
            .busy_lines
            .get_values([false])
            .map_err(|e| DisplayError::Gpio(format!("Failed to read BUSY pin: {}", e)))?;
        Ok(values[0])
    }
}

// Display state
struct DisplayState {
    spi: Option<Spidev>,
    gpio: Option<GpioController>,
    initialized: bool,
}

// Global state (using Mutex for thread safety)
static DISPLAY_STATE: Mutex<DisplayState> = Mutex::new(DisplayState {
    spi: None,
    gpio: None,
    initialized: false,
});

// Helper functions
fn delay_ms(ms: u64) {
    thread::sleep(Duration::from_millis(ms));
}

fn delay_us(us: u64) {
    thread::sleep(Duration::from_micros(us));
}

fn gpio_write(pin: u32, value: bool) -> Result<(), DisplayError> {
    let state = DISPLAY_STATE.lock().unwrap();

    if let Some(gpio) = &state.gpio {
        match pin {
            DC_PIN => gpio.write_dc(value),
            RST_PIN => gpio.write_rst(value),
            _ => Err(DisplayError::Gpio(format!("Invalid output pin: {}", pin))),
        }
    } else {
        Err(DisplayError::Gpio("GPIO not initialized".to_string()))
    }
}

fn gpio_read(pin: u32) -> Result<bool, DisplayError> {
    let state = DISPLAY_STATE.lock().unwrap();

    if let Some(gpio) = &state.gpio {
        match pin {
            BUSY_PIN => gpio.read_busy(),
            _ => Err(DisplayError::Gpio(format!("Invalid input pin: {}", pin))),
        }
    } else {
        Err(DisplayError::Gpio("GPIO not initialized".to_string()))
    }
}

fn spi_delay() {
    delay_us(10);
}

fn lcd_chkstatus() -> Result<(), DisplayError> {
    let mut watchdog_counter = 0;
    while gpio_read(BUSY_PIN)? && watchdog_counter < 1000 {
        delay_ms(10);
        watchdog_counter += 1;
    }

    if watchdog_counter >= 1000 {
        log::warn!("Display busy timeout");
        return Err(DisplayError::Timeout);
    }

    Ok(())
}

fn epd_w21_write_cmd(cmd: u8) -> Result<(), DisplayError> {
    let state = DISPLAY_STATE.lock().unwrap();

    if state.spi.is_some() {
        spi_delay();
        drop(state);
        gpio_write(DC_PIN, false)?;

        let mut state = DISPLAY_STATE.lock().unwrap();
        if let Some(spi) = state.spi.as_mut() {
            spi.write_all(&[cmd])
                .map_err(|e| DisplayError::Spi(format!("Failed to write command: {}", e)))?;
        }
    }

    Ok(())
}

fn epd_w21_write_data(data: u8) -> Result<(), DisplayError> {
    let state = DISPLAY_STATE.lock().unwrap();

    if state.spi.is_some() {
        spi_delay();
        drop(state);
        gpio_write(DC_PIN, true)?;

        let mut state = DISPLAY_STATE.lock().unwrap();
        if let Some(spi) = state.spi.as_mut() {
            spi.write_all(&[data])
                .map_err(|e| DisplayError::Spi(format!("Failed to write data: {}", e)))?;
        }
    }

    Ok(())
}

fn epd_init_hardware() -> Result<(), DisplayError> {
    // Module reset
    gpio_write(RST_PIN, false)?;
    delay_ms(10);
    gpio_write(RST_PIN, true)?;
    delay_ms(10);

    lcd_chkstatus()?;
    epd_w21_write_cmd(0x12)?; // SWRESET
    lcd_chkstatus()?;

    epd_w21_write_cmd(0x01)?; // Driver output control
    epd_w21_write_data(((EPD_HEIGHT - 1) % 256) as u8)?;
    epd_w21_write_data(((EPD_HEIGHT - 1) / 256) as u8)?;
    epd_w21_write_data(0x00)?;

    epd_w21_write_cmd(0x11)?; // data entry mode
    epd_w21_write_data(0x01)?; // Normal mode

    epd_w21_write_cmd(0x44)?; // set Ram-X address start/end position
    epd_w21_write_data(0x00)?;
    epd_w21_write_data((EPD_WIDTH / 8 - 1) as u8)?;

    epd_w21_write_cmd(0x45)?; // set Ram-Y address start/end position
    epd_w21_write_data(((EPD_HEIGHT - 1) % 256) as u8)?;
    epd_w21_write_data(((EPD_HEIGHT - 1) / 256) as u8)?;
    epd_w21_write_data(0x00)?;
    epd_w21_write_data(0x00)?;

    epd_w21_write_cmd(0x3C)?; // BorderWavefrom
    epd_w21_write_data(0x05)?;

    epd_w21_write_cmd(0x21)?; // Display update control
    epd_w21_write_data(0x00)?;
    epd_w21_write_data(0x80)?;

    epd_w21_write_cmd(0x18)?; // Read built-in temperature sensor
    epd_w21_write_data(0x80)?;

    epd_w21_write_cmd(0x4E)?; // set RAM x address count
    epd_w21_write_data(0x00)?;

    epd_w21_write_cmd(0x4F)?; // set RAM y address count
    epd_w21_write_data(((EPD_HEIGHT - 1) % 256) as u8)?;
    epd_w21_write_data(((EPD_HEIGHT - 1) / 256) as u8)?;
    lcd_chkstatus()?;

    Ok(())
}

fn epd_init_partial() -> Result<(), DisplayError> {
    // For partial refresh, set up partial refresh mode
    epd_w21_write_cmd(0x3C)?; // BorderWavefrom
    epd_w21_write_data(0x80)?; // Partial refresh border setting
    Ok(())
}

fn epd_update() -> Result<(), DisplayError> {
    epd_w21_write_cmd(0x22)?; // Display Update Control
    epd_w21_write_data(0xF7)?;
    epd_w21_write_cmd(0x20)?; // Activate Display Update Sequence
    lcd_chkstatus()?;
    Ok(())
}

fn epd_update_partial() -> Result<(), DisplayError> {
    epd_w21_write_cmd(0x22)?; // Display Update Control
    epd_w21_write_data(0xFF)?;
    epd_w21_write_cmd(0x20)?; // Activate Display Update Sequence
    lcd_chkstatus()?;
    Ok(())
}

// Public Rust API
pub fn rust_display_init() -> Result<(), DisplayError> {
    let mut state = DISPLAY_STATE.lock().unwrap();

    if state.initialized {
        return Ok(());
    }

    // Initialize SPI
    let mut spi = Spidev::open("/dev/spidev0.0")
        .map_err(|e| DisplayError::Spi(format!("Failed to open SPI device: {}", e)))?;

    let options = SpidevOptions::new()
        .bits_per_word(8)
        .max_speed_hz(40_000_000)
        .mode(SpiModeFlags::SPI_MODE_0)
        .build();

    spi.configure(&options)
        .map_err(|e| DisplayError::Spi(format!("Failed to configure SPI: {}", e)))?;

    // Initialize GPIO
    let gpio = GpioController::new()?;

    state.spi = Some(spi);
    state.gpio = Some(gpio);

    drop(state); // Release the lock before calling epd_init_hardware

    epd_init_hardware()?;

    let mut state = DISPLAY_STATE.lock().unwrap();
    state.initialized = true;

    log::info!("Display SDK initialized successfully");
    Ok(())
}

pub fn rust_display_image_raw(data: &[u8], mode: DisplayMode) -> Result<(), DisplayError> {
    let state = DISPLAY_STATE.lock().unwrap();

    if !state.initialized {
        return Err(DisplayError::NotInitialized);
    }

    if data.len() != EPD_ARRAY {
        return Err(DisplayError::InvalidDataSize {
            expected: EPD_ARRAY,
            actual: data.len(),
        });
    }

    drop(state); // Release the lock

    match mode {
        DisplayMode::Partial => epd_init_partial()?,
        DisplayMode::Full => {} // Full mode uses default initialization
    }

    epd_w21_write_cmd(0x24)?; // Write RAM

    let state = DISPLAY_STATE.lock().unwrap();
    if state.spi.is_some() {
        drop(state);
        gpio_write(DC_PIN, true)?;
        let mut state = DISPLAY_STATE.lock().unwrap();
        if let Some(spi) = state.spi.as_mut() {
            spi.write_all(data)
                .map_err(|e| DisplayError::Spi(format!("Failed to write image data: {}", e)))?;
        }
    }

    match mode {
        DisplayMode::Full => epd_update()?,
        DisplayMode::Partial => epd_update_partial()?,
    }

    Ok(())
}

pub fn rust_display_image_png(filename: &str, mode: DisplayMode) -> Result<(), DisplayError> {
    let raw_data = rust_convert_png_to_1bit(filename)?;
    rust_display_image_raw(&raw_data, mode)
}

pub fn rust_display_clear() -> Result<(), DisplayError> {
    let white_data = vec![0xFF; EPD_ARRAY];
    rust_display_image_raw(&white_data, DisplayMode::Full)
}

pub fn rust_display_sleep() -> Result<(), DisplayError> {
    epd_w21_write_cmd(0x10)?; // Deep sleep mode
    epd_w21_write_data(0x01)?;
    delay_ms(100);
    Ok(())
}

pub fn rust_display_cleanup() -> Result<(), DisplayError> {
    let state = DISPLAY_STATE.lock().unwrap();

    if state.initialized {
        drop(state);
        rust_display_sleep()?;
        let mut state = DISPLAY_STATE.lock().unwrap();

        state.spi = None;
        state.gpio = None;
        state.initialized = false;

        log::info!("Display SDK cleaned up");
    }

    Ok(())
}

pub fn rust_display_get_dimensions() -> (u32, u32) {
    (EPD_WIDTH, EPD_HEIGHT)
}

pub fn rust_convert_png_to_1bit(filename: &str) -> Result<Vec<u8>, DisplayError> {
    let image = lodepng::decode32_file(filename)
        .map_err(|e| DisplayError::Png(format!("Failed to decode PNG: {}", e)))?;

    if image.width != EPD_WIDTH as usize || image.height != EPD_HEIGHT as usize {
        return Err(DisplayError::Png(format!(
            "Invalid image size: {}x{}, expected {}x{}",
            image.width, image.height, EPD_WIDTH, EPD_HEIGHT
        )));
    }

    let mut output = vec![0u8; EPD_ARRAY];

    for y in 0..image.height {
        for x in 0..image.width {
            let pixel_idx = y * image.width + x;
            let pixel = image.buffer[pixel_idx];

            // Convert RGBA to grayscale
            let gray = (pixel.r as u16 + pixel.g as u16 + pixel.b as u16) / 3;

            // Convert to 1-bit (threshold at 128)
            let bit_value = if gray > 128 { 1 } else { 0 };

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

// C FFI exports
#[no_mangle]
pub extern "C" fn display_init() -> c_int {
    match rust_display_init() {
        Ok(()) => 1, // true
        Err(e) => {
            log::error!("Display init failed: {}", e);
            0 // false
        }
    }
}

#[no_mangle]
pub extern "C" fn display_image_raw(data: *const u8, mode: c_int) -> c_int {
    if data.is_null() {
        return 0;
    }

    let data_slice = unsafe { std::slice::from_raw_parts(data, EPD_ARRAY) };
    let display_mode = match mode {
        0 => DisplayMode::Full,
        1 => DisplayMode::Partial,
        _ => return 0,
    };

    match rust_display_image_raw(data_slice, display_mode) {
        Ok(()) => 1,
        Err(e) => {
            log::error!("Display image raw failed: {}", e);
            0
        }
    }
}

#[no_mangle]
pub extern "C" fn display_image_png(filename: *const c_char, mode: c_int) -> c_int {
    if filename.is_null() {
        return 0;
    }

    let filename_str = unsafe {
        match CStr::from_ptr(filename).to_str() {
            Ok(s) => s,
            Err(_) => return 0,
        }
    };

    let display_mode = match mode {
        0 => DisplayMode::Full,
        1 => DisplayMode::Partial,
        _ => return 0,
    };

    match rust_display_image_png(filename_str, display_mode) {
        Ok(()) => 1,
        Err(e) => {
            log::error!("Display image PNG failed: {}", e);
            0
        }
    }
}

#[no_mangle]
pub extern "C" fn display_clear() -> c_int {
    match rust_display_clear() {
        Ok(()) => 1,
        Err(e) => {
            log::error!("Display clear failed: {}", e);
            0
        }
    }
}

#[no_mangle]
pub extern "C" fn display_sleep() {
    if let Err(e) = rust_display_sleep() {
        log::error!("Display sleep failed: {}", e);
    }
}

#[no_mangle]
pub extern "C" fn display_cleanup() {
    if let Err(e) = rust_display_cleanup() {
        log::error!("Display cleanup failed: {}", e);
    }
}

#[no_mangle]
pub extern "C" fn display_get_dimensions(width: *mut c_uint, height: *mut c_uint) {
    if !width.is_null() && !height.is_null() {
        let (w, h) = rust_display_get_dimensions();
        unsafe {
            *width = w;
            *height = h;
        }
    }
}

#[no_mangle]
pub extern "C" fn convert_png_to_1bit(filename: *const c_char, output_data: *mut u8) -> c_int {
    if filename.is_null() || output_data.is_null() {
        return 0;
    }

    let filename_str = unsafe {
        match CStr::from_ptr(filename).to_str() {
            Ok(s) => s,
            Err(_) => return 0,
        }
    };

    match rust_convert_png_to_1bit(filename_str) {
        Ok(data) => {
            unsafe {
                ptr::copy_nonoverlapping(data.as_ptr(), output_data, EPD_ARRAY);
            }
            1
        }
        Err(e) => {
            log::error!("Convert PNG to 1bit failed: {}", e);
            0
        }
    }
}
