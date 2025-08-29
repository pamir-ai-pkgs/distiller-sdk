//! Hardware abstraction layer for e-ink display control via SPI and GPIO.

use std::{num::NonZeroU32, thread, time::Duration};

use gpiod::{Chip, Input, Lines, Options, Output};
use spidev::{SpiModeFlags, Spidev, SpidevOptions};

use crate::error::DisplayError;

// GPIO pin definitions - these could be made configurable per variant
/// Data/Command control pin
pub const DC_PIN: NonZeroU32 = NonZeroU32::new(7).unwrap();
/// Reset pin
pub const RST_PIN: NonZeroU32 = NonZeroU32::new(13).unwrap();
/// Busy status pin  
pub const BUSY_PIN: NonZeroU32 = NonZeroU32::new(9).unwrap();

/// GPIO Controller trait for different hardware variants
pub trait GpioController {
    /// Create a new GPIO controller instance
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Gpio` if GPIO initialization fails
    fn new() -> Result<Self, DisplayError>
    where
        Self: Sized;
    /// Set the Data/Command pin state
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Gpio` if the operation fails
    fn write_dc(&self, value: bool) -> Result<(), DisplayError>;
    /// Set the Reset pin state
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Gpio` if the operation fails
    fn write_rst(&self, value: bool) -> Result<(), DisplayError>;
    /// Read the Busy pin state
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Gpio` if the operation fails
    fn read_busy(&self) -> Result<bool, DisplayError>;
}

/// Default GPIO controller implementation using gpiod
pub struct DefaultGpioController {
    dc: Lines<Output>,
    rst: Lines<Output>,
    busy: Lines<Input>,
}

impl GpioController for DefaultGpioController {
    fn new() -> Result<Self, DisplayError> {
        let chip = Chip::new("/dev/gpiochip0")
            .map_err(|e| DisplayError::Gpio(format!("Failed to open GPIO chip: {e}")))?;

        // Configure DC pin as output (initially low)
        let dc_opts = Options::output([DC_PIN.get()])
            .values([false])
            .consumer("distiller-display-dc");
        let dc_lines = chip
            .request_lines(dc_opts)
            .map_err(|e| DisplayError::Gpio(format!("Failed to request DC line: {e}")))?;

        // Configure RST pin as output (initially high)
        let rst_opts = Options::output([RST_PIN.get()])
            .values([true])
            .consumer("distiller-display-rst");
        let rst_lines = chip
            .request_lines(rst_opts)
            .map_err(|e| DisplayError::Gpio(format!("Failed to request RST line: {e}")))?;

        // Configure BUSY pin as input
        let busy_opts = Options::input([BUSY_PIN.get()]).consumer("distiller-display-busy");
        let busy_lines = chip
            .request_lines(busy_opts)
            .map_err(|e| DisplayError::Gpio(format!("Failed to request BUSY line: {e}")))?;

        Ok(Self {
            dc: dc_lines,
            rst: rst_lines,
            busy: busy_lines,
        })
    }

    fn write_dc(&self, value: bool) -> Result<(), DisplayError> {
        self.dc
            .set_values([value])
            .map_err(|e| DisplayError::Gpio(format!("Failed to set DC pin: {e}")))
    }

    fn write_rst(&self, value: bool) -> Result<(), DisplayError> {
        self.rst
            .set_values([value])
            .map_err(|e| DisplayError::Gpio(format!("Failed to set RST pin: {e}")))
    }

    fn read_busy(&self) -> Result<bool, DisplayError> {
        let values = self
            .busy
            .get_values([false])
            .map_err(|e| DisplayError::Gpio(format!("Failed to read BUSY pin: {e}")))?;
        Ok(values[0])
    }
}

/// SPI Controller trait for different hardware variants
pub trait SpiController {
    /// Create a new SPI controller instance
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Spi` if SPI initialization fails
    fn new() -> Result<Self, DisplayError>
    where
        Self: Sized;
    /// Write data to the SPI bus
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Spi` if the write operation fails
    fn write_all(&mut self, data: &[u8]) -> Result<(), DisplayError>;
}

/// Default SPI controller implementation using spidev
pub struct DefaultSpiController {
    spi: Spidev,
}

impl SpiController for DefaultSpiController {
    fn new() -> Result<Self, DisplayError> {
        let mut spi = Spidev::open("/dev/spidev0.0")
            .map_err(|e| DisplayError::Spi(format!("Failed to open SPI device: {e}")))?;

        let options = SpidevOptions::new()
            .bits_per_word(8)
            .max_speed_hz(40_000_000)
            .mode(SpiModeFlags::SPI_MODE_0)
            .build();

        spi.configure(&options)
            .map_err(|e| DisplayError::Spi(format!("Failed to configure SPI: {e}")))?;

        Ok(Self { spi })
    }

    fn write_all(&mut self, data: &[u8]) -> Result<(), DisplayError> {
        use std::io::Write;

        // Linux SPI drivers typically have transfer size limits around 4KB
        // Split large transfers into smaller chunks to avoid "Message too long" errors
        const MAX_CHUNK_SIZE: usize = 4096;

        if data.len() <= MAX_CHUNK_SIZE {
            // Small transfer, send directly
            self.spi
                .write_all(data)
                .map_err(|e| DisplayError::Spi(format!("Failed to write data: {e}")))
        } else {
            // Large transfer, send in chunks
            for chunk in data.chunks(MAX_CHUNK_SIZE) {
                self.spi
                    .write_all(chunk)
                    .map_err(|e| DisplayError::Spi(format!("Failed to write data chunk: {e}")))?;

                // Small delay between chunks to avoid overwhelming the SPI bus
                std::thread::sleep(std::time::Duration::from_micros(100));
            }
            Ok(())
        }
    }
}

/// Hardware abstraction layer combining GPIO and SPI controllers
pub struct HardwareInterface<G: GpioController, S: SpiController> {
    gpio: G,
    spi: S,
}

impl<G: GpioController, S: SpiController> HardwareInterface<G, S> {
    /// Create a new hardware interface
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if GPIO or SPI initialization fails
    pub fn new() -> Result<Self, DisplayError> {
        let gpio = G::new()?;
        let spi = S::new()?;
        Ok(Self { gpio, spi })
    }

    /// Set the Data/Command pin state
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Gpio` if the operation fails
    pub fn write_dc(&self, value: bool) -> Result<(), DisplayError> {
        self.gpio.write_dc(value)
    }

    /// Set the Reset pin state
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Gpio` if the operation fails
    pub fn write_rst(&self, value: bool) -> Result<(), DisplayError> {
        self.gpio.write_rst(value)
    }

    /// Read the Busy pin state
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Gpio` if the operation fails
    pub fn read_busy(&self) -> Result<bool, DisplayError> {
        self.gpio.read_busy()
    }

    /// Write data to the SPI bus
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Spi` if the write operation fails
    pub fn spi_write_all(&mut self, data: &[u8]) -> Result<(), DisplayError> {
        self.spi.write_all(data)
    }
}

/// Delay for the specified number of milliseconds
pub fn delay_ms(ms: u64) {
    thread::sleep(Duration::from_millis(ms));
}

/// Delay for the specified number of microseconds
pub fn delay_us(us: u64) {
    thread::sleep(Duration::from_micros(us));
}

/// Default hardware interface type using default GPIO and SPI controllers
pub type DefaultHardwareInterface = HardwareInterface<DefaultGpioController, DefaultSpiController>;
