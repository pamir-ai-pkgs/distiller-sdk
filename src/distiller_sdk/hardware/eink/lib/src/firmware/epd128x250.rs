//! Firmware implementation for `EPD128x250` e-ink displays.
//!
//! # Orientation & Conversion
//!
//! Spec dimensions are landscape (width=250, height=128) matching the physical
//! mounted orientation seen by end users. The vendor controller, however, expects
//! portrait data (128×250). `display_image_raw()` in `display.rs` bridges this
//! gap with a single CW 90° rotation — users work in landscape, the conversion
//! is transparent.
//!
//! Buffer size is 4000 bytes either way: (250×128)/8 = (128×250)/8 = 4000.

use crate::firmware::{CommandSequence, DisplayFirmware, DisplaySpec};

/// Firmware configuration for `EPD128x250` E-ink display.
///
/// Duplicate this file and modify register values for different display variants
/// of the same controller family.
pub struct EPD128x250Firmware {
    spec: DisplaySpec,
}

impl EPD128x250Firmware {
    /// Create a new `EPD128x250` firmware instance.
    #[must_use]
    pub fn new() -> Self {
        Self {
            spec: DisplaySpec {
                width: 250,
                height: 128,
                name: "EPD128x250".to_string(),
                description: "EPD128x250 E-ink display (landscape: 250x128 as mounted)"
                    .to_string(),
            },
        }
    }
}

impl DisplayFirmware for EPD128x250Firmware {
    fn get_spec(&self) -> &DisplaySpec {
        &self.spec
    }

    fn get_init_sequence(&self) -> CommandSequence {
        // Hardware init uses vendor's native portrait dimensions (128x250)
        let vendor_width: u32 = 128;
        let vendor_height: u32 = 250;

        CommandSequence::new()
            // Software reset
            .cmd(0x12)
            .check_status()
            // Driver output control
            .cmd(0x01)
            .data(((vendor_height - 1) % 256) as u8)
            .data(((vendor_height - 1) / 256) as u8)
            .data(0x00)
            // Data entry mode (SSD1681 datasheet §8.1, CMD 0x11):
            // 0x03 = Y-increment + X-increment (bits [1:0])
            // Bit 0=1: X-address counter increments (left→right)
            // Bit 1=1: Y-address counter increments (top→bottom)
            // Y-increment ensures buffer row 0 → physical top when display
            // is landscape-mounted. Changed from 0x01 (Y-decrement) to fix
            // inverted image orientation after rotate=90 transform.
            .cmd(0x11)
            .data(0x03)
            // Set Ram-X address start/end position
            .cmd(0x44)
            .data(0x00)
            .data((vendor_width / 8 - 1) as u8)
            // Set RAM Y address start/end position (SSD1681 §8.1, CMD 0x45):
            // Y-increment mode: start=0, end=height-1 (top→bottom scan)
            // Matches data entry mode 0x03 above.
            .cmd(0x45)
            .data(0x00)
            .data(0x00)
            .data(((vendor_height - 1) % 256) as u8)
            .data(((vendor_height - 1) / 256) as u8)
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
            // Set RAM Y address count (SSD1681 §8.1, CMD 0x4F):
            // Start at 0 to match Y-increment mode (data entry 0x03).
            .cmd(0x4F)
            .data(0x00)
            .data(0x00)
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
