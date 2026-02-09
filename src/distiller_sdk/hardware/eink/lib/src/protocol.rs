//! E-ink communication protocol implementation for sending commands and data to
//! the display.

use crate::{
    error::DisplayError,
    firmware::{Command, CommandSequence, DisplayFirmware},
    hardware::{GpioController, HardwareInterface, SpiController, delay_ms, delay_us},
};

/// Display refresh modes
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub enum DisplayMode {
    /// Full refresh (slow, high quality)
    Full = 0,
    /// Partial refresh (fast, good quality)
    Partial = 1,
    /// Fast refresh (~1.5s) - temperature register override at 100°C
    Fast = 2,
    /// Turbo refresh (~1s) - temperature register override at 90°C + dual RAM
    Turbo = 3,
    /// 4-level grayscale (requires `display_image_auto`, not
    /// `display_image_raw`)
    Grayscale4 = 4,
}

/// E-ink display protocol trait
pub trait EinkProtocol {
    /// Initialize the display hardware
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if initialization fails
    fn init_hardware(&mut self) -> Result<(), DisplayError>;
    /// Initialize partial update mode
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if initialization fails
    fn init_partial(&mut self) -> Result<(), DisplayError>;
    /// Write a command byte to the display
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if the write fails
    fn write_cmd(&mut self, cmd: u8) -> Result<(), DisplayError>;
    /// Write a data byte to the display
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if the write fails
    fn write_data(&mut self, data: u8) -> Result<(), DisplayError>;
    /// Write image data to the display
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if the write fails
    fn write_image_data(&mut self, data: &[u8]) -> Result<(), DisplayError>;
    /// Check the display status and wait until ready
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Timeout` if the display doesn't become ready
    fn check_status(&mut self) -> Result<(), DisplayError>;
    /// Update the display with the current buffer
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if the update fails
    fn update_display(&mut self, mode: DisplayMode) -> Result<(), DisplayError>;
    /// Initialize fast refresh mode with a temperature override
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if initialization fails
    fn init_fast(&mut self, temp_value: u8) -> Result<(), DisplayError>;
    /// Write data to the secondary RAM buffer (0x26)
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if write fails
    fn write_secondary_ram(&mut self, data: &[u8]) -> Result<(), DisplayError>;
    /// Put the display into sleep mode
    ///
    /// # Errors
    ///
    /// Returns `DisplayError` if the sleep command fails
    fn sleep(&mut self) -> Result<(), DisplayError>;
    /// Display 4-gray image using dual RAM buffers
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Config` if firmware doesn't support 4-gray,
    /// or other `DisplayError` variants if hardware operations fail
    fn display_4gray(&mut self, ram_24: &[u8], ram_26: &[u8]) -> Result<(), DisplayError>;
    /// Get the display specifications
    fn get_spec(&self) -> &crate::firmware::DisplaySpec;
    /// Get the write RAM command byte
    fn get_write_ram_command(&self) -> u8;
}

/// Generic E-ink protocol implementation using firmware abstraction
pub struct GenericEinkProtocol<G: GpioController, S: SpiController, F: DisplayFirmware> {
    hardware: HardwareInterface<G, S>,
    firmware: F,
}

impl<G: GpioController, S: SpiController, F: DisplayFirmware> GenericEinkProtocol<G, S, F> {
    /// Create a new generic e-ink protocol with the given hardware and firmware
    #[must_use]
    pub const fn new(hardware: HardwareInterface<G, S>, firmware: F) -> Self {
        Self { hardware, firmware }
    }

    /// Execute a command sequence
    fn execute_sequence(&mut self, sequence: CommandSequence) -> Result<(), DisplayError> {
        for command in sequence.commands {
            match command {
                Command::WriteCommand(cmd) => self.write_cmd(cmd)?,
                Command::WriteData(data) => self.write_data(data)?,
                Command::WriteDataBulk(ref data) => {
                    delay_us(10);
                    self.hardware.write_dc(true)?;
                    self.hardware.spi_write_all(data)?;
                },
                Command::Delay(ms) => delay_ms(ms),
                Command::CheckStatus => self.check_status()?,
                Command::Reset => {
                    self.hardware.write_rst(false)?;
                    delay_ms(10);
                    self.hardware.write_rst(true)?;
                    delay_ms(10);
                },
            }
        }
        Ok(())
    }
}

impl<G: GpioController, S: SpiController, F: DisplayFirmware> EinkProtocol
    for GenericEinkProtocol<G, S, F>
{
    fn init_hardware(&mut self) -> Result<(), DisplayError> {
        // Execute reset sequence first
        let reset_sequence = self.firmware.get_reset_sequence();
        self.execute_sequence(reset_sequence)?;

        // Execute main initialization sequence
        let init_sequence = self.firmware.get_init_sequence();
        self.execute_sequence(init_sequence)?;

        Ok(())
    }

    fn init_partial(&mut self) -> Result<(), DisplayError> {
        let partial_sequence = self.firmware.get_partial_init_sequence();
        self.execute_sequence(partial_sequence)?;
        Ok(())
    }

    fn write_cmd(&mut self, cmd: u8) -> Result<(), DisplayError> {
        delay_us(10);
        self.hardware.write_dc(false)?;
        self.hardware.spi_write_all(&[cmd])?;
        Ok(())
    }

    fn write_data(&mut self, data: u8) -> Result<(), DisplayError> {
        delay_us(10);
        self.hardware.write_dc(true)?;
        self.hardware.spi_write_all(&[data])?;
        Ok(())
    }

    fn write_image_data(&mut self, data: &[u8]) -> Result<(), DisplayError> {
        // Validate image size using firmware
        self.firmware.validate_image_size(data)?;

        self.hardware.write_dc(true)?;
        self.hardware.spi_write_all(data)?;
        Ok(())
    }

    fn check_status(&mut self) -> Result<(), DisplayError> {
        // 3000 iterations × 10ms = 30s timeout (safe for all modes including 4-gray
        // ~5s)
        let mut watchdog_counter = 0;
        while self.hardware.read_busy()? && watchdog_counter < 3000 {
            delay_ms(10);
            watchdog_counter += 1;
        }

        if watchdog_counter >= 3000 {
            log::warn!("Display busy timeout");
            return Err(DisplayError::Timeout);
        }

        Ok(())
    }

    fn update_display(&mut self, mode: DisplayMode) -> Result<(), DisplayError> {
        let update_sequence = self.firmware.get_update_sequence(mode);
        self.execute_sequence(update_sequence)?;
        Ok(())
    }

    fn init_fast(&mut self, temp_value: u8) -> Result<(), DisplayError> {
        let fast_sequence = self.firmware.get_fast_init_sequence(temp_value);
        self.execute_sequence(fast_sequence)?;
        Ok(())
    }

    fn write_secondary_ram(&mut self, data: &[u8]) -> Result<(), DisplayError> {
        let secondary_cmd = self.firmware.get_secondary_ram_command();
        self.write_cmd(secondary_cmd)?;
        self.hardware.write_dc(true)?;
        self.hardware.spi_write_all(data)?;
        Ok(())
    }

    fn sleep(&mut self) -> Result<(), DisplayError> {
        let sleep_sequence = self.firmware.get_sleep_sequence();
        self.execute_sequence(sleep_sequence)?;
        Ok(())
    }

    fn display_4gray(&mut self, ram_24: &[u8], ram_26: &[u8]) -> Result<(), DisplayError> {
        let init_seq = self.firmware.get_4g_init_sequence().ok_or_else(|| {
            DisplayError::Config("4-gray mode not supported by this display firmware".into())
        })?;

        // 2. Hardware reset + 4-gray init (includes LUT, voltages, mode 0x01)
        let reset_seq = self.firmware.get_reset_sequence();
        self.execute_sequence(reset_seq)?;
        self.execute_sequence(init_seq)?;

        // 3. Clear both RAM buffers (prevent stale data artifacts)
        self.write_cmd(0x24)?;
        self.hardware.write_dc(true)?;
        self.hardware.spi_write_all(&vec![0x00u8; ram_24.len()])?;
        self.write_cmd(0x26)?;
        self.hardware.write_dc(true)?;
        self.hardware.spi_write_all(&vec![0x00u8; ram_26.len()])?;

        // 4. Re-set RAM window + counters (clear consumed the address counter) Re-run
        //    the 4-gray init to restore window/counter state
        self.execute_sequence(
            self.firmware
                .get_4g_init_sequence()
                .expect("already checked"),
        )?;

        // 5. Write image data: RAM 0x26 first, then 0x24
        self.write_cmd(0x26)?;
        self.hardware.write_dc(true)?;
        self.hardware.spi_write_all(ram_26)?;
        self.write_cmd(0x24)?;
        self.hardware.write_dc(true)?;
        self.hardware.spi_write_all(ram_24)?;

        // 6. Trigger 4-gray update (0xC7) + wait busy
        let update_seq = self
            .firmware
            .get_4g_update_sequence()
            .ok_or_else(|| DisplayError::Config("4-gray update sequence not available".into()))?;
        self.execute_sequence(update_seq)?;

        let sleep_seq = self.firmware.get_sleep_sequence();
        self.execute_sequence(sleep_seq)?;

        // 8. Re-initialize for normal 1-bit mode (restores mode 0x03)
        self.init_hardware()?;

        Ok(())
    }

    fn get_spec(&self) -> &crate::firmware::DisplaySpec {
        self.firmware.get_spec()
    }

    fn get_write_ram_command(&self) -> u8 {
        self.firmware.get_write_ram_command()
    }
}

/// Runtime firmware selection supporting multiple display types
pub enum ConfigurableProtocol {
    /// 128x250 display protocol
    EPD128x250(
        Box<
            GenericEinkProtocol<
                crate::hardware::DefaultGpioController,
                crate::hardware::DefaultSpiController,
                crate::firmware::EPD128x250Firmware,
            >,
        >,
    ),
    /// 240x416 display protocol
    EPD240x416(
        Box<
            GenericEinkProtocol<
                crate::hardware::DefaultGpioController,
                crate::hardware::DefaultSpiController,
                crate::firmware::EPD240x416Firmware,
            >,
        >,
    ),
}

impl EinkProtocol for ConfigurableProtocol {
    fn init_hardware(&mut self) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.init_hardware(),
            Self::EPD240x416(p) => p.init_hardware(),
        }
    }

    fn init_partial(&mut self) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.init_partial(),
            Self::EPD240x416(p) => p.init_partial(),
        }
    }

    fn write_cmd(&mut self, cmd: u8) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.write_cmd(cmd),
            Self::EPD240x416(p) => p.write_cmd(cmd),
        }
    }

    fn write_data(&mut self, data: u8) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.write_data(data),
            Self::EPD240x416(p) => p.write_data(data),
        }
    }

    fn write_image_data(&mut self, data: &[u8]) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.write_image_data(data),
            Self::EPD240x416(p) => p.write_image_data(data),
        }
    }

    fn check_status(&mut self) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.check_status(),
            Self::EPD240x416(p) => p.check_status(),
        }
    }

    fn update_display(&mut self, mode: DisplayMode) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.update_display(mode),
            Self::EPD240x416(p) => p.update_display(mode),
        }
    }

    fn init_fast(&mut self, temp_value: u8) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.init_fast(temp_value),
            Self::EPD240x416(p) => p.init_fast(temp_value),
        }
    }

    fn write_secondary_ram(&mut self, data: &[u8]) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.write_secondary_ram(data),
            Self::EPD240x416(p) => p.write_secondary_ram(data),
        }
    }

    fn sleep(&mut self) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.sleep(),
            Self::EPD240x416(p) => p.sleep(),
        }
    }

    fn display_4gray(&mut self, ram_24: &[u8], ram_26: &[u8]) -> Result<(), DisplayError> {
        match self {
            Self::EPD128x250(p) => p.display_4gray(ram_24, ram_26),
            Self::EPD240x416(p) => p.display_4gray(ram_24, ram_26),
        }
    }

    fn get_spec(&self) -> &crate::firmware::DisplaySpec {
        match self {
            Self::EPD128x250(p) => p.get_spec(),
            Self::EPD240x416(p) => p.get_spec(),
        }
    }

    fn get_write_ram_command(&self) -> u8 {
        match self {
            Self::EPD128x250(p) => p.get_write_ram_command(),
            Self::EPD240x416(p) => p.get_write_ram_command(),
        }
    }
}

/// Default protocol type using configurable firmware
pub type DefaultProtocol = ConfigurableProtocol;

/// Create a default protocol using the configured firmware type
///
/// # Errors
///
/// Returns `DisplayError` if hardware initialization fails
pub fn create_default_protocol() -> Result<DefaultProtocol, DisplayError> {
    let hardware = crate::hardware::DefaultHardwareInterface::new()?;

    // Get the configured firmware type and create appropriate protocol variant
    let firmware_type = crate::config::get_default_firmware().unwrap_or_else(|e| {
        log::warn!("Failed to get configured firmware: {e}, using EPD128x250");
        crate::config::FirmwareType::EPD128x250
    });

    match firmware_type {
        crate::config::FirmwareType::EPD128x250 => {
            let firmware = crate::firmware::EPD128x250Firmware::new();
            let protocol = GenericEinkProtocol::new(hardware, firmware);
            Ok(ConfigurableProtocol::EPD128x250(Box::new(protocol)))
        },
        crate::config::FirmwareType::EPD240x416 => {
            let firmware = crate::firmware::EPD240x416Firmware::new();
            let protocol = GenericEinkProtocol::new(hardware, firmware);
            Ok(ConfigurableProtocol::EPD240x416(Box::new(protocol)))
        },
    }
}

/// Create a protocol with custom firmware
///
/// # Errors
///
/// Returns `DisplayError` if hardware initialization fails
pub fn create_protocol_with_firmware<F: DisplayFirmware>(
    firmware: F,
) -> Result<
    GenericEinkProtocol<
        crate::hardware::DefaultGpioController,
        crate::hardware::DefaultSpiController,
        F,
    >,
    DisplayError,
> {
    let hardware = crate::hardware::DefaultHardwareInterface::new()?;
    Ok(GenericEinkProtocol::new(hardware, firmware))
}
