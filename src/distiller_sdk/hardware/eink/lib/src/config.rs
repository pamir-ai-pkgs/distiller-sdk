//! Configuration management for e-ink display firmware selection and settings.

use std::{
    fs,
    path::Path,
    str::FromStr,
    sync::{Mutex, OnceLock},
};

use crate::{
    error::DisplayError,
    firmware::{DisplayFirmware, DisplaySpec, EPD128x250Firmware, EPD240x416Firmware},
};

/// Supported firmware types
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FirmwareType {
    /// 128x250 pixel e-ink display firmware
    EPD128x250,
    /// 240x416 pixel e-ink display firmware
    EPD240x416,
}

impl FirmwareType {
    /// Create a firmware instance for this type
    #[must_use]
    pub fn create_firmware(&self) -> Box<dyn DisplayFirmware> {
        match self {
            FirmwareType::EPD128x250 => Box::new(EPD128x250Firmware::new()),
            FirmwareType::EPD240x416 => Box::new(EPD240x416Firmware::new()),
        }
    }

    /// Get the display spec for this firmware type
    #[must_use]
    pub fn get_spec(&self) -> DisplaySpec {
        self.create_firmware().get_spec().clone()
    }

    /// Parse firmware type from string (use `FromStr` trait implementation
    /// instead)
    ///
    /// # Errors
    ///
    /// Returns `DisplayError::Config` if the firmware type is not recognized
    pub fn parse(s: &str) -> Result<Self, DisplayError> {
        match s.to_lowercase().as_str() {
            "epd128x250" | "128x250" => Ok(FirmwareType::EPD128x250),
            "epd240x416" | "240x416" => Ok(FirmwareType::EPD240x416),
            _ => Err(DisplayError::Config(format!(
                "Unknown firmware type: {s}. Supported types: EPD128x250, EPD240x416"
            ))),
        }
    }

    /// Get string representation
    #[must_use]
    pub fn as_str(&self) -> &'static str {
        match self {
            FirmwareType::EPD128x250 => "EPD128x250",
            FirmwareType::EPD240x416 => "EPD240x416",
        }
    }
}

impl std::fmt::Display for FirmwareType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.as_str())
    }
}

impl FromStr for FirmwareType {
    type Err = DisplayError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::parse(s)
    }
}

/// Hardware configuration for GPIO and SPI
#[derive(Debug, Clone)]
pub struct HardwareConfig {
    /// Platform identifier (cm5, radxa-zero3, etc)
    pub platform: String,
    /// SPI device path
    pub spi_device: String,
    /// GPIO chip device path
    pub gpio_chip: String,
    /// Data/Command GPIO pin offset
    pub dc_pin: u32,
    /// Reset GPIO pin offset
    pub rst_pin: u32,
    /// Busy GPIO pin offset
    pub busy_pin: u32,
}

impl Default for HardwareConfig {
    fn default() -> Self {
        // CM5 defaults for backward compatibility
        Self {
            platform: "cm5".to_string(),
            spi_device: "/dev/spidev0.0".to_string(),
            gpio_chip: "/dev/gpiochip0".to_string(),
            dc_pin: 7,
            rst_pin: 13,
            busy_pin: 9,
        }
    }
}

/// Global configuration for the display system
#[derive(Debug, Clone)]
pub struct DisplayConfig {
    /// Default firmware type for the display
    pub default_firmware: FirmwareType,
    /// Hardware configuration
    pub hardware: HardwareConfig,
}

impl Default for DisplayConfig {
    fn default() -> Self {
        Self {
            default_firmware: FirmwareType::EPD128x250, // Keep existing default
            hardware: HardwareConfig::default(),
        }
    }
}

/// Global configuration instance
static CONFIG: OnceLock<Mutex<DisplayConfig>> = OnceLock::new();

/// Initialize the global configuration
pub fn init_config() -> &'static Mutex<DisplayConfig> {
    CONFIG.get_or_init(|| Mutex::new(DisplayConfig::default()))
}

/// Set the default firmware type globally
///
/// # Errors
///
/// Returns `DisplayError::Config` if the configuration lock cannot be acquired
pub fn set_default_firmware(firmware_type: FirmwareType) -> Result<(), DisplayError> {
    let config = init_config();
    let mut config_guard = config
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire config lock: {e}")))?;

    log::info!("Setting default firmware to: {firmware_type}");
    config_guard.default_firmware = firmware_type;
    Ok(())
}

/// Set the default firmware type from string
///
/// # Errors
///
/// Returns `DisplayError::Config` if the firmware type is not recognized or the
/// lock cannot be acquired
pub fn set_default_firmware_from_str(firmware_str: &str) -> Result<(), DisplayError> {
    let firmware_type = FirmwareType::parse(firmware_str)?;
    set_default_firmware(firmware_type)
}

/// Get the current default firmware type
///
/// # Errors
///
/// Returns `DisplayError::Config` if the configuration lock cannot be acquired
pub fn get_default_firmware() -> Result<FirmwareType, DisplayError> {
    let config = init_config();
    let config_guard = config
        .lock()
        .map_err(|e| DisplayError::Config(format!("Failed to acquire config lock: {e}")))?;
    Ok(config_guard.default_firmware)
}

/// Create a firmware instance using the default firmware type
///
/// # Errors
///
/// Returns `DisplayError::Config` if the configuration lock cannot be acquired
pub fn create_default_firmware() -> Result<Box<dyn DisplayFirmware>, DisplayError> {
    let firmware_type = get_default_firmware()?;
    Ok(firmware_type.create_firmware())
}

/// Get the display spec for the default firmware
///
/// # Errors
///
/// Returns `DisplayError::Config` if the configuration lock cannot be acquired
pub fn get_default_spec() -> Result<DisplaySpec, DisplayError> {
    let firmware_type = get_default_firmware()?;
    Ok(firmware_type.get_spec())
}

/// Configuration from environment variables
///
/// # Errors
///
/// Returns `DisplayError::Config` if the firmware type is invalid or lock
/// cannot be acquired
pub fn init_from_env() -> Result<(), DisplayError> {
    if let Ok(firmware_env) = std::env::var("DISTILLER_EINK_FIRMWARE") {
        log::info!("Setting firmware from environment: {firmware_env}");
        set_default_firmware_from_str(&firmware_env)?;
    }
    Ok(())
}

/// Parse INI-style configuration file
///
/// # Errors
///
/// Returns `DisplayError::Config` if parsing fails
pub fn parse_ini_config(content: &str) -> Result<DisplayConfig, DisplayError> {
    let mut config = DisplayConfig::default();
    let mut current_section = "";

    for line in content.lines() {
        let line = line.trim();

        // Skip comments and empty lines
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        // Section header
        if line.starts_with('[') && line.ends_with(']') {
            current_section = &line[1..line.len() - 1];
            continue;
        }

        // Key-value pairs
        if let Some(eq_pos) = line.find('=') {
            let key = line[..eq_pos].trim();
            let value = line[eq_pos + 1..].trim();

            match current_section {
                "display" => {
                    if key == "firmware" {
                        config.default_firmware = FirmwareType::parse(value)?;
                    }
                },
                "hardware" => match key {
                    "platform" => config.hardware.platform = value.to_string(),
                    "spi_device" => config.hardware.spi_device = value.to_string(),
                    "gpio_chip" => config.hardware.gpio_chip = value.to_string(),
                    _ => {},
                },
                "gpio_pins" => match key {
                    "dc_pin" => {
                        config.hardware.dc_pin = value
                            .parse()
                            .map_err(|_| DisplayError::Config(format!("Invalid dc_pin: {value}")))?
                    },
                    "rst_pin" => {
                        config.hardware.rst_pin = value.parse().map_err(|_| {
                            DisplayError::Config(format!("Invalid rst_pin: {value}"))
                        })?
                    },
                    "busy_pin" => {
                        config.hardware.busy_pin = value.parse().map_err(|_| {
                            DisplayError::Config(format!("Invalid busy_pin: {value}"))
                        })?
                    },
                    _ => {},
                },
                _ => {},
            }
        }
    }

    Ok(config)
}

/// Configuration from file (if it exists) - legacy support
///
/// # Errors
///
/// Returns `DisplayError::Config` if the firmware type is invalid or lock
/// cannot be acquired
pub fn init_from_file(config_path: &str) -> Result<(), DisplayError> {
    if let Ok(content) = fs::read_to_string(config_path) {
        // Try new INI format first
        if let Ok(parsed_config) = parse_ini_config(&content) {
            let config = init_config();
            let mut config_guard = config
                .lock()
                .map_err(|e| DisplayError::Config(format!("Failed to acquire config lock: {e}")))?;
            *config_guard = parsed_config;
            return Ok(());
        }

        // Fall back to old format for backward compatibility
        for line in content.lines() {
            let line = line.trim();
            if line.starts_with("firmware=") || line.starts_with("FIRMWARE=") {
                let firmware_str = line.split('=').nth(1).unwrap_or("").trim();
                if !firmware_str.is_empty() {
                    log::info!("Setting firmware from config file: {firmware_str}");
                    set_default_firmware_from_str(firmware_str)?;
                    break;
                }
            }
        }
    }
    Ok(())
}

/// Initialize configuration from all sources (environment, file, defaults)
///
/// # Errors
///
/// Returns `DisplayError::Config` if initialization fails
pub fn initialize_config() -> Result<(), DisplayError> {
    let config_path = "/opt/distiller-sdk/eink.conf";

    // Config file is now mandatory
    if !Path::new(config_path).exists() {
        return Err(DisplayError::Config(format!(
            "Configuration file not found: {config_path}. Please configure your hardware platform."
        )));
    }

    let content = fs::read_to_string(config_path)
        .map_err(|e| DisplayError::Config(format!("Cannot read config: {e}")))?;

    let config = parse_ini_config(&content)?;

    // Validate hardware paths exist
    if !Path::new(&config.hardware.spi_device).exists() {
        log::warn!(
            "SPI device {} not found. Please enable SPI for your platform.",
            config.hardware.spi_device
        );
    }
    if !Path::new(&config.hardware.gpio_chip).exists() {
        return Err(DisplayError::Config(format!(
            "GPIO chip {} not found",
            config.hardware.gpio_chip
        )));
    }

    // Store configuration
    let global = init_config();
    let mut guard = global
        .lock()
        .map_err(|e| DisplayError::Config(format!("Config lock failed: {e}")))?;
    *guard = config.clone();

    log::info!(
        "Display configured for platform: {} with firmware: {}",
        config.hardware.platform,
        config.default_firmware
    );

    Ok(())
}

/// Get the hardware configuration
///
/// # Errors
///
/// Returns `DisplayError::Config` if the configuration lock cannot be acquired
pub fn get_hardware_config() -> Result<HardwareConfig, DisplayError> {
    let config = init_config();
    let guard = config
        .lock()
        .map_err(|e| DisplayError::Config(format!("Config lock failed: {e}")))?;
    Ok(guard.hardware.clone())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_firmware_type_parsing() {
        assert_eq!(
            FirmwareType::parse("EPD128x250").unwrap(),
            FirmwareType::EPD128x250
        );
        assert_eq!(
            FirmwareType::parse("128x250").unwrap(),
            FirmwareType::EPD128x250
        );
        assert_eq!(
            FirmwareType::parse("EPD240x416").unwrap(),
            FirmwareType::EPD240x416
        );
        assert_eq!(
            FirmwareType::parse("240x416").unwrap(),
            FirmwareType::EPD240x416
        );
        assert!(FirmwareType::parse("invalid").is_err());

        // Test FromStr trait implementation
        assert_eq!(
            "EPD128x250".parse::<FirmwareType>().unwrap(),
            FirmwareType::EPD128x250
        );
    }

    #[test]
    fn test_config_default() {
        let config = DisplayConfig::default();
        assert_eq!(config.default_firmware, FirmwareType::EPD128x250);
    }

    #[test]
    fn test_set_get_firmware() {
        set_default_firmware(FirmwareType::EPD240x416).unwrap();
        assert_eq!(get_default_firmware().unwrap(), FirmwareType::EPD240x416);

        // Reset to default
        set_default_firmware(FirmwareType::EPD128x250).unwrap();
        assert_eq!(get_default_firmware().unwrap(), FirmwareType::EPD128x250);
    }
}
