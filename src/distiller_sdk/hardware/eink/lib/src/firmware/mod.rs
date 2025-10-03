//! Display firmware module containing hardware-specific implementations for
//! various e-ink displays.

use crate::error::DisplayError;

pub mod epd128x250;
pub mod epd240x416;

pub use epd128x250::EPD128x250Firmware;
pub use epd240x416::EPD240x416Firmware;

/// Display specifications
#[derive(Debug, Clone)]
pub struct DisplaySpec {
    /// Display width in pixels
    pub width: u32,
    /// Display height in pixels
    pub height: u32,
    /// Display model name
    pub name: String,
    /// Display description
    pub description: String,
}

impl DisplaySpec {
    /// Calculate the required array size in bytes for 1-bit image data
    #[must_use]
    pub fn array_size(&self) -> usize {
        ((self.width * self.height) / 8) as usize
    }
}

/// Command sequence for display operations
#[derive(Debug, Clone, Default)]
pub struct CommandSequence {
    /// List of commands to execute
    pub commands: Vec<Command>,
}

/// Display command types
#[derive(Debug, Clone)]
pub enum Command {
    /// Write a command byte to the display
    WriteCommand(u8),
    /// Write a data byte to the display
    WriteData(u8),
    /// Delay for specified milliseconds
    Delay(u64),
    /// Check the display busy status
    CheckStatus,
    /// Reset the display hardware
    Reset,
}

impl CommandSequence {
    /// Create a new empty command sequence
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a command byte to the sequence
    #[must_use]
    pub fn cmd(mut self, command: u8) -> Self {
        self.commands.push(Command::WriteCommand(command));
        self
    }

    /// Add a data byte to the sequence
    #[must_use]
    pub fn data(mut self, data: u8) -> Self {
        self.commands.push(Command::WriteData(data));
        self
    }

    /// Add a delay to the sequence
    #[must_use]
    pub fn delay(mut self, ms: u64) -> Self {
        self.commands.push(Command::Delay(ms));
        self
    }

    /// Add a status check to the sequence
    #[must_use]
    pub fn check_status(mut self) -> Self {
        self.commands.push(Command::CheckStatus);
        self
    }

    /// Add a reset command to the sequence
    #[must_use]
    pub fn reset(mut self) -> Self {
        self.commands.push(Command::Reset);
        self
    }
}

/// Firmware interface trait - implement this for different display variants
pub trait DisplayFirmware {
    /// Get the display specifications
    fn get_spec(&self) -> &DisplaySpec;
    /// Get the initialization command sequence
    fn get_init_sequence(&self) -> CommandSequence;
    /// Get the partial update initialization sequence
    fn get_partial_init_sequence(&self) -> CommandSequence;
    /// Get the display update sequence
    fn get_update_sequence(&self, is_partial: bool) -> CommandSequence;
    /// Get the sleep mode sequence
    fn get_sleep_sequence(&self) -> CommandSequence;
    /// Get the write RAM command byte
    fn get_write_ram_command(&self) -> u8;

    /// Get the hardware reset sequence
    fn get_reset_sequence(&self) -> CommandSequence {
        CommandSequence::new().reset().delay(10)
    }

    /// Validate that image data is the correct size
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::InvalidDataSize` if the data size doesn't match
    fn validate_image_size(&self, data: &[u8]) -> Result<(), DisplayError> {
        let expected_size = self.get_spec().array_size();
        if data.len() != expected_size {
            return Err(DisplayError::InvalidDataSize {
                expected: expected_size,
                actual: data.len(),
            });
        }
        Ok(())
    }
}
