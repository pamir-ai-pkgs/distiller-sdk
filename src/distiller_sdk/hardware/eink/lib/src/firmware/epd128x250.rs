//! Firmware implementation for 128x250 e-ink displays.

use crate::firmware::{CommandSequence, DisplayFirmware, DisplaySpec};

/// Firmware configuration for 128x250 E-ink display
/// This is the current display variant - you can duplicate this file and modify
/// register values for different display variants of the same controller family
pub struct EPD128x250Firmware {
    spec: DisplaySpec,
}

impl EPD128x250Firmware {
    /// Create a new `EPD128x250` firmware instance
    #[must_use]
    pub fn new() -> Self {
        Self {
            spec: DisplaySpec {
                width: 128,
                height: 250,
                name: "EPD128x250".to_string(),
                description: "128x250 E-ink display".to_string(),
            },
        }
    }
}

impl DisplayFirmware for EPD128x250Firmware {
    fn get_spec(&self) -> &DisplaySpec {
        &self.spec
    }

    fn get_init_sequence(&self) -> CommandSequence {
        let height = self.spec.height;
        let width = self.spec.width;

        CommandSequence::new()
            // Software reset
            .cmd(0x12)
            .check_status()
            // Driver output control
            .cmd(0x01)
            .data(((height - 1) % 256) as u8)
            .data(((height - 1) / 256) as u8)
            .data(0x00)
            // Data entry mode
            .cmd(0x11)
            .data(0x01) // Normal mode
            // Set Ram-X address start/end position
            .cmd(0x44)
            .data(0x00)
            .data((width / 8 - 1) as u8)
            // Set Ram-Y address start/end position
            .cmd(0x45)
            .data(((height - 1) % 256) as u8)
            .data(((height - 1) / 256) as u8)
            .data(0x00)
            .data(0x00)
            // BorderWavefrom
            .cmd(0x3C)
            .data(0x05)
            // Display update control
            .cmd(0x21)
            .data(0x00)
            .data(0x80)
            // Read built-in temperature sensor
            .cmd(0x18)
            .data(0x80)
            // Set RAM x address count
            .cmd(0x4E)
            .data(0x00)
            // Set RAM y address count
            .cmd(0x4F)
            .data(((height - 1) % 256) as u8)
            .data(((height - 1) / 256) as u8)
            .check_status()
    }

    fn get_partial_init_sequence(&self) -> CommandSequence {
        CommandSequence::new()
            // BorderWavefrom for partial refresh
            .cmd(0x3C)
            .data(0x80) // Partial refresh border setting
    }

    fn get_update_sequence(&self, is_partial: bool) -> CommandSequence {
        if is_partial {
            CommandSequence::new()
                .cmd(0x22) // Display Update Control
                .data(0xFF)
                .cmd(0x20) // Activate Display Update Sequence
                .check_status()
        } else {
            CommandSequence::new()
                .cmd(0x22) // Display Update Control
                .data(0xF7)
                .cmd(0x20) // Activate Display Update Sequence
                .check_status()
        }
    }

    fn get_sleep_sequence(&self) -> CommandSequence {
        CommandSequence::new()
            .cmd(0x10) // Deep sleep mode
            .data(0x01)
            .delay(100)
    }

    fn get_write_ram_command(&self) -> u8 {
        0x24 // Write RAM command
    }
}

impl Default for EPD128x250Firmware {
    fn default() -> Self {
        Self::new()
    }
}
