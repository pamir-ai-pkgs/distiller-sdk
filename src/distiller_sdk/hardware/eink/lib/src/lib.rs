//! Rust SDK for controlling e-ink displays via SPI interface on ARM64 Linux
//! systems.
//!
//! This library provides a comprehensive interface for e-ink display control
//! including hardware abstraction, firmware variants, image processing, and
//! configuration management.

#![warn(clippy::all)]
#![warn(clippy::pedantic)]
#![warn(missing_docs)]
#![allow(clippy::module_name_repetitions)]
#![allow(clippy::cast_possible_truncation)]
#![allow(clippy::cast_sign_loss)]

pub mod config;
pub mod display;
pub mod error;
/// FFI bindings for C interoperability
pub mod ffi;
/// FFI bindings for image processing functions
pub mod ffi_image_processing;
pub mod firmware;
pub mod hardware;
pub mod image;
pub mod image_processing;
pub mod protocol;

// Re-export public API
pub use config::{
    FirmwareType,
    get_default_firmware,
    initialize_config,
    set_default_firmware,
    set_default_firmware_from_str,
};
pub use display::{DefaultDisplay, DisplayDriver, GenericDisplay};
// Re-export the main functions for backwards compatibility
pub use display::{
    display_cleanup,
    display_clear,
    display_get_dimensions,
    display_image_auto,
    display_image_file,
    display_image_png,
    display_image_raw,
    display_init,
    display_sleep,
};
pub use error::DisplayError;
pub use firmware::{Command, CommandSequence, DisplayFirmware, DisplaySpec};
pub use hardware::{DefaultHardwareInterface, GpioController, HardwareInterface, SpiController};
pub use image::{
    convert_image_to_1bit,
    convert_image_to_1bit_with_spec,
    convert_png_to_1bit,
    create_black_image,
    create_white_image,
    get_dimensions,
};
pub use image_processing::{
    DitherMode,
    ImageProcessor,
    ScaleMode,
    ShapeDrawer,
    TextRenderer,
    Transform,
};
pub use protocol::{DisplayMode, EinkProtocol};

// C FFI is automatically available through the ffi module
