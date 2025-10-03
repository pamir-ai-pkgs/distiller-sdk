//! Error types for the e-ink display library.

use thiserror::Error;

/// Error type for display operations.
#[derive(Error, Debug)]
pub enum DisplayError {
    /// GPIO hardware error
    #[error("GPIO error: {0}")]
    Gpio(String),
    /// SPI communication error
    #[error("SPI error: {0}")]
    Spi(String),
    /// PNG processing error
    #[error("PNG error: {0}")]
    Png(String),
    /// Display has not been initialized
    #[error("Display not initialized")]
    NotInitialized,
    /// Invalid data size for display
    #[error("Invalid data size: expected {expected}, got {actual}")]
    InvalidDataSize {
        /// Expected data size in bytes
        expected: usize,
        /// Actual data size in bytes
        actual: usize,
    },
    /// Timeout waiting for display ready signal
    #[error("Timeout waiting for display")]
    Timeout,
    /// I/O operation error
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    /// Configuration error
    #[error("Configuration error: {0}")]
    Config(String),
}
