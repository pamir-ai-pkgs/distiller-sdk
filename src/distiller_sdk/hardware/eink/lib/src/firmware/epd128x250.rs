//! Firmware implementation for `EPD128x250` e-ink displays.
//!
//! # Orientation & Conversion
//!
//! Spec dimensions are landscape (width=250, height=128) matching the physical
//! mounted orientation seen by end users. The vendor controller, however,
//! expects portrait data (128×250). `display_image_raw()` in `display.rs`
//! bridges this gap with a single CW 90° rotation — users work in landscape,
//! the conversion is transparent.
//!
//! Buffer size is 4000 bytes either way: (250×128)/8 = (128×250)/8 = 4000.

use crate::firmware::{CommandSequence, DisplayFirmware, DisplaySpec};

// 4-gray LUT waveform data (153 bytes) from GxEPD2_213_GDEY0213B74.cpp
// Loaded via command 0x32 during 4-gray initialization
#[rustfmt::skip]
const LUT_4GRAY: [u8; 153] = [
    // Voltage Source levels (VS) - 5 groups of 12 bytes = 60 bytes
    0x40, 0x48, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x08, 0x48, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x02, 0x48, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x20, 0x48, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    // Timing/Phase groups (TP) - 12 groups of 7 bytes = 84 bytes
    0x0A, 0x19, 0x00, 0x03, 0x08, 0x00, 0x00,
    0x14, 0x01, 0x00, 0x14, 0x01, 0x00, 0x03,
    0x0A, 0x03, 0x00, 0x08, 0x19, 0x00, 0x00,
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    // Gate/Source voltage settings (9 bytes)
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x00, 0x00, 0x00,
];

// Voltage parameters from GxEPD2 for 4-gray mode
const EOPQ_4G: u8 = 0x22;
const VGH_4G: u8 = 0x17;
const VSH1_4G: u8 = 0x41;
const VSH2_4G: u8 = 0x00;
const VSL_4G: u8 = 0x32;
const VCOM_4G: u8 = 0x1C;

/// Firmware configuration for `EPD128x250` E-ink display.
///
/// Duplicate this file and modify register values for different display
/// variants of the same controller family.
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
                description: "EPD128x250 E-ink display (landscape: 250x128 as mounted)".to_string(),
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

    fn get_update_sequence(&self, mode: crate::protocol::DisplayMode) -> CommandSequence {
        use crate::protocol::DisplayMode;
        match mode {
            DisplayMode::Full => CommandSequence::new()
                .cmd(0x22)
                .data(0xF7)
                .cmd(0x20)
                .check_status(),
            DisplayMode::Partial => CommandSequence::new()
                .cmd(0x22)
                .data(0xFF)
                .cmd(0x20)
                .check_status(),
            DisplayMode::Fast | DisplayMode::Turbo => self.get_fast_update_sequence(),
            DisplayMode::Grayscale4 => CommandSequence::new(), // handled by display_4gray()
        }
    }

    fn get_fast_init_sequence(&self, temp_value: u8) -> CommandSequence {
        // After SW reset, ALL registers revert to defaults. Re-apply critical
        // registers to maintain staging's 0x03 data entry mode (Y-inc, X-inc).
        let vendor_width: u32 = 128;
        let vendor_height: u32 = 250;

        CommandSequence::new()
            // Software reset
            .cmd(0x12)
            .check_status()
            // Re-apply driver output control
            .cmd(0x01)
            .data(((vendor_height - 1) % 256) as u8)
            .data(((vendor_height - 1) / 256) as u8)
            .data(0x00)
            // Re-apply data entry mode (CRITICAL: must be 0x03)
            .cmd(0x11)
            .data(0x03)
            // Re-apply RAM X window
            .cmd(0x44)
            .data(0x00)
            .data((vendor_width / 8 - 1) as u8)
            // Re-apply RAM Y window (Y-increment: start=0, end=height-1)
            .cmd(0x45)
            .data(0x00)
            .data(0x00)
            .data(((vendor_height - 1) % 256) as u8)
            .data(((vendor_height - 1) / 256) as u8)
            // Re-apply RAM counters
            .cmd(0x4E)
            .data(0x00)
            .cmd(0x4F)
            .data(0x00)
            .data(0x00)
            // Enable built-in temperature sensor
            .cmd(0x18)
            .data(0x80)
            // Load current temperature value
            .cmd(0x22)
            .data(0xB1)
            .cmd(0x20)
            .check_status()
            // Override temperature register
            .cmd(0x1A)
            .data(temp_value)
            .data(0x00)
            // Reload with overridden temperature
            .cmd(0x22)
            .data(0x91)
            .cmd(0x20)
            .check_status()
    }

    fn get_sleep_sequence(&self) -> CommandSequence {
        CommandSequence::new()
            .cmd(0x10) // Deep sleep mode
            .data(0x01)
            .delay(100)
    }

    fn get_write_ram_command(&self) -> u8 {
        0x24
    }

    fn get_4g_init_sequence(&self) -> Option<CommandSequence> {
        // Port of grayscale_4g.py _init_4gray() / GxEPD2 _Init_4G
        // Uses data entry mode 0x01 (Y-dec, X-inc) required by the 4-gray LUT waveform
        let vendor_width: u32 = 128;
        let vendor_height: u32 = 250;

        Some(
            CommandSequence::new()
                // Software reset
                .cmd(0x12)
                .delay(10)
                .check_status()
                // Analog block control
                .cmd(0x74)
                .data(0x54)
                // Digital block control
                .cmd(0x7E)
                .data(0x3B)
                // Driver output control (295 lines for GxEPD2 compat)
                .cmd(0x01)
                .data(0x27) // (295 - 1) & 0xFF = 0x27 (not 249; GxEPD2 uses 295)
                .data(0x01) // (295 - 1) >> 8 = 0x01
                .data(0x00)
                // Data entry mode: 0x01 = Y-dec, X-inc (CRITICAL for 4-gray LUT)
                .cmd(0x11)
                .data(0x01)
                // RAM X window: 0x00 to 0x0F (128/8 - 1 = 15)
                .cmd(0x44)
                .data(0x00)
                .data((vendor_width / 8 - 1) as u8)
                // RAM Y window: start=249, end=0 (REVERSED for Y-dec mode)
                .cmd(0x45)
                .data(((vendor_height - 1) % 256) as u8) // 249
                .data(((vendor_height - 1) / 256) as u8) // 0
                .data(0x00) // end Y low
                .data(0x00) // end Y high
                // Border waveform
                .cmd(0x3C)
                .data(0x00)
                // VCOM voltage
                .cmd(0x2C)
                .data(VCOM_4G)
                // End Option
                .cmd(0x3F)
                .data(EOPQ_4G)
                // VGH voltage
                .cmd(0x03)
                .data(VGH_4G)
                // VSH1, VSH2, VSL
                .cmd(0x04)
                .data(VSH1_4G)
                .data(VSH2_4G)
                .data(VSL_4G)
                // Display update control
                .cmd(0x21)
                .data(0x00)
                .data(0x80)
                // Load LUT (command 0x32 + 153 bytes bulk data)
                .cmd(0x32)
                .data_bulk(LUT_4GRAY.to_vec())
                // Set RAM X counter to 0
                .cmd(0x4E)
                .data(0x00)
                // Set RAM Y counter to 249 (start at top for Y-dec)
                .cmd(0x4F)
                .data(((vendor_height - 1) % 256) as u8)
                .data(((vendor_height - 1) / 256) as u8)
                .check_status(),
        )
    }

    fn get_4g_update_sequence(&self) -> Option<CommandSequence> {
        Some(
            CommandSequence::new()
                .cmd(0x22)
                .data(0xC7)
                .cmd(0x20)
                .check_status(),
        )
    }
}

impl Default for EPD128x250Firmware {
    fn default() -> Self {
        Self::new()
    }
}
