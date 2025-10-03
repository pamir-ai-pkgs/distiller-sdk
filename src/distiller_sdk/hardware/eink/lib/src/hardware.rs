//! Hardware abstraction layer for e-ink display control via SPI and GPIO.

use std::{thread, time::Duration};

use gpiod::{Chip, Input, Lines, Options, Output};
use spidev::{SpiModeFlags, Spidev, SpidevOptions};

use crate::{config::get_hardware_config, error::DisplayError};

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
        let hw_config = get_hardware_config().map_err(|e| {
            log::error!("Failed to get hardware config: {e}");
            e
        })?;

        let chip = Chip::new(&hw_config.gpio_chip).map_err(|e| {
            let err_msg = format!("Failed to open GPIO chip {}: {}", hw_config.gpio_chip, e);
            log::error!("{err_msg}");
            DisplayError::Gpio(err_msg)
        })?;

        // Configure DC pin as output (initially low)
        let dc_opts = Options::output([hw_config.dc_pin])
            .values([false])
            .consumer("distiller-display-dc");
        let dc_lines = chip.request_lines(dc_opts).map_err(|e| {
            let err_msg = format!(
                "Failed to request DC pin {} on {}: {}",
                hw_config.dc_pin, hw_config.gpio_chip, e
            );
            log::error!("{err_msg}");
            DisplayError::Gpio(err_msg)
        })?;

        // Configure RST pin as output (initially high)
        let rst_opts = Options::output([hw_config.rst_pin])
            .values([true])
            .consumer("distiller-display-rst");
        let rst_lines = chip.request_lines(rst_opts).map_err(|e| {
            let err_msg = format!(
                "Failed to request RST pin {} on {}: {}",
                hw_config.rst_pin, hw_config.gpio_chip, e
            );
            log::error!("{err_msg}");
            DisplayError::Gpio(err_msg)
        })?;

        // Configure BUSY pin as input
        let busy_opts = Options::input([hw_config.busy_pin]).consumer("distiller-display-busy");
        let busy_lines = chip.request_lines(busy_opts).map_err(|e| {
            let err_msg = format!(
                "Failed to request BUSY pin {} on {}: {}",
                hw_config.busy_pin, hw_config.gpio_chip, e
            );
            log::error!("{err_msg}");
            DisplayError::Gpio(err_msg)
        })?;

        log::info!(
            "GPIO initialized on {} with pins DC={}, RST={}, BUSY={}",
            hw_config.gpio_chip,
            hw_config.dc_pin,
            hw_config.rst_pin,
            hw_config.busy_pin
        );

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
        let hw_config = get_hardware_config().map_err(|e| {
            log::error!("Failed to get hardware config: {e}");
            e
        })?;

        let mut spi = Spidev::open(&hw_config.spi_device).map_err(|e| {
            let err_msg = format!("Failed to open SPI device {}: {}", hw_config.spi_device, e);
            log::error!("{err_msg}");
            DisplayError::Spi(err_msg)
        })?;

        let options = SpidevOptions::new()
            .bits_per_word(8)
            .max_speed_hz(40_000_000)
            .mode(SpiModeFlags::SPI_MODE_0)
            .build();

        spi.configure(&options).map_err(|e| {
            let err_msg = format!("Failed to configure SPI {}: {}", hw_config.spi_device, e);
            log::error!("{err_msg}");
            DisplayError::Spi(err_msg)
        })?;

        log::info!("SPI initialized on {}", hw_config.spi_device);

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
