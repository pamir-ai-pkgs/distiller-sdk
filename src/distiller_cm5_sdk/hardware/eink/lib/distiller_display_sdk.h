#ifndef DISTILLER_DISPLAY_SDK_H
#define DISTILLER_DISPLAY_SDK_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// Display dimensions for e-ink display
#define EPD_WIDTH   128
#define EPD_HEIGHT  250
#define EPD_ARRAY   ((EPD_WIDTH * EPD_HEIGHT) / 8)  // 4000 bytes for 1-bit

// GPIO pins for e-ink display
#define DC_PIN    7   // Data/Command control
#define RST_PIN   13  // Reset
#define BUSY_PIN  9   // Busy status
#define CS_PIN    8   // Chip select

// Display modes
typedef enum {
    DISPLAY_MODE_FULL,     // Full refresh (slow, high quality)
    DISPLAY_MODE_PARTIAL   // Partial refresh (fast, good quality)
} display_mode_t;

// Image format
typedef enum {
    IMAGE_FORMAT_RAW,      // Raw 1-bit packed data
    IMAGE_FORMAT_PNG       // PNG file (will be converted to 1-bit)
} image_format_t;

/**
 * Initialize the display SDK
 * @return true on success, false on failure
 */
bool display_init(void);

/**
 * Display an image from raw 1-bit packed data
 * @param data Pointer to 1-bit packed image data (EPD_ARRAY bytes)
 * @param mode Display mode (full or partial refresh)
 * @return true on success, false on failure
 */
bool display_image_raw(const uint8_t* data, display_mode_t mode);

/**
 * Display an image from PNG file
 * @param filename Path to PNG file
 * @param mode Display mode (full or partial refresh)
 * @return true on success, false on failure
 */
bool display_image_png(const char* filename, display_mode_t mode);

/**
 * Clear the display (set to white)
 * @return true on success, false on failure
 */
bool display_clear(void);

/**
 * Put display to sleep (power saving)
 */
void display_sleep(void);

/**
 * Cleanup and shutdown display
 */
void display_cleanup(void);

/**
 * Get display dimensions
 * @param width Pointer to store width
 * @param height Pointer to store height
 */
void display_get_dimensions(uint32_t* width, uint32_t* height);

/**
 * Convert PNG to 1-bit packed data
 * @param filename Path to PNG file
 * @param output_data Pointer to buffer for output data (must be EPD_ARRAY bytes)
 * @return true on success, false on failure
 */
bool convert_png_to_1bit(const char* filename, uint8_t* output_data);

#endif // DISTILLER_DISPLAY_SDK_H 