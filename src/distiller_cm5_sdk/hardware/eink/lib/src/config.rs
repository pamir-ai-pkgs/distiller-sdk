//! Configuration management for e-ink display firmware selection and settings.

use std::{
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

/// Global configuration for the display system
#[derive(Debug, Clone)]
pub struct DisplayConfig {
    /// Default firmware type for the display
    pub default_firmware: FirmwareType,
}

impl Default for DisplayConfig {
    fn default() -> Self {
        Self {
            default_firmware: FirmwareType::EPD128x250, // Keep existing default
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

/// Configuration from file (if it exists)
///
/// # Errors
///
/// Returns `DisplayError::Config` if the firmware type is invalid or lock
/// cannot be acquired
pub fn init_from_file(config_path: &str) -> Result<(), DisplayError> {
    if let Ok(content) = std::fs::read_to_string(config_path) {
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
    // Initialize with defaults first
    init_config();

    // Try to load from config file if it exists
    let mut config_paths = vec![
        "/opt/distiller-cm5-sdk/eink.conf".to_string(),
        "./eink.conf".to_string(),
    ];

    // Add home directory config path if HOME is set
    if let Ok(home) = std::env::var("HOME") {
        config_paths.push(format!("{home}/.distiller/eink.conf"));
    }

    for path in &config_paths {
        if let Err(e) = init_from_file(path) {
            log::debug!("Could not load config from {path}: {e}");
        }
    }

    // Environment variables override file settings
    init_from_env()?;

    let firmware_type = get_default_firmware()?;
    log::info!("Display configuration initialized with firmware: {firmware_type}");

    Ok(())
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
