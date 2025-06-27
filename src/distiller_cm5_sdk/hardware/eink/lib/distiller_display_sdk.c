#include "distiller_display_sdk.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>
#include <gpiod.h>

// Include lodepng for PNG support
#include "lodepng.h"

// Private variables
static int spi_fd = -1;
static struct gpiod_chip *chip = NULL;
static struct gpiod_line *dc_line = NULL;
static struct gpiod_line *rst_line = NULL;
static struct gpiod_line *busy_line = NULL;
static bool initialized = false;

// Private function declarations
static void delay_ms(int ms);
static void gpio_write(int pin, int value);
static int gpio_read(int pin);
static void spi_delay(void);
static void epd_w21_write_cmd(uint8_t cmd);
static void epd_w21_write_data(uint8_t data);
static void lcd_chkstatus(void);
static void epd_init_hardware(void);
static void epd_init_partial(void);
static void epd_update(void);
static void epd_update_partial(void);

// Implementation
static void delay_ms(int ms) {
    usleep(ms * 1000);
}

static void gpio_write(int pin, int value) {
    struct gpiod_line *line = NULL;
    
    if (pin == DC_PIN) {
        line = dc_line;
    } else if (pin == RST_PIN) {
        line = rst_line;
    }
    
    if (line) {
        if (gpiod_line_set_value(line, value) < 0) {
            printf("Error: Failed to set GPIO %d to %d\n", pin, value);
        }
    }
}

static int gpio_read(int pin) {
    if (pin == BUSY_PIN && busy_line) {
        return gpiod_line_get_value(busy_line);
    }
    return -1;
}

static void spi_delay(void) {
    usleep(10);  // 10 microseconds delay
}

static void lcd_chkstatus(void) {
    int watchdog_counter = 0;
    while (gpio_read(BUSY_PIN) == 1 && watchdog_counter < 1000) {  // =1 BUSY
        delay_ms(10);
        watchdog_counter++;
    }
    if (watchdog_counter >= 1000) {
        printf("Warning: Display busy timeout\n");
    }
}

static void epd_w21_write_cmd(uint8_t cmd) {
    if (spi_fd < 0) return;
    
    spi_delay();
    gpio_write(DC_PIN, 0);
    
    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)&cmd,
        .rx_buf = 0,
        .len = 1,
        .speed_hz = 40000000,
        .bits_per_word = 8,
        .delay_usecs = 0,
        .cs_change = 1,
    };
    
    if (ioctl(spi_fd, SPI_IOC_MESSAGE(1), &tr) < 0) {
        perror("Error in SPI command transfer");
    }
}

static void epd_w21_write_data(uint8_t data) {
    if (spi_fd < 0) return;
    
    spi_delay();
    gpio_write(DC_PIN, 1);
    
    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)&data,
        .rx_buf = 0,
        .len = 1,
        .speed_hz = 40000000,
        .bits_per_word = 8,
        .delay_usecs = 0,
        .cs_change = 1,
    };
    
    if (ioctl(spi_fd, SPI_IOC_MESSAGE(1), &tr) < 0) {
        perror("Error in SPI data transfer");
    }
}

static void epd_init_hardware(void) {
    // Module reset
    gpio_write(RST_PIN, 0);
    delay_ms(10);
    gpio_write(RST_PIN, 1);
    delay_ms(10);
    
    lcd_chkstatus();
    epd_w21_write_cmd(0x12);  // SWRESET
    lcd_chkstatus();
    
    epd_w21_write_cmd(0x01);  // Driver output control
    epd_w21_write_data((EPD_HEIGHT-1) % 256);
    epd_w21_write_data((EPD_HEIGHT-1) / 256);
    epd_w21_write_data(0x00);

    epd_w21_write_cmd(0x11);  // data entry mode
    epd_w21_write_data(0x01);  // Normal mode

    epd_w21_write_cmd(0x44);  // set Ram-X address start/end position
    epd_w21_write_data(0x00);
    epd_w21_write_data(EPD_WIDTH/8-1);

    epd_w21_write_cmd(0x45);  // set Ram-Y address start/end position
    epd_w21_write_data((EPD_HEIGHT-1) % 256);
    epd_w21_write_data((EPD_HEIGHT-1) / 256);
    epd_w21_write_data(0x00);
    epd_w21_write_data(0x00);

    epd_w21_write_cmd(0x3C);  // BorderWavefrom
    epd_w21_write_data(0x05);

    epd_w21_write_cmd(0x21);  // Display update control
    epd_w21_write_data(0x00);
    epd_w21_write_data(0x80);

    epd_w21_write_cmd(0x18);  // Read built-in temperature sensor
    epd_w21_write_data(0x80);

    epd_w21_write_cmd(0x4E);  // set RAM x address count
    epd_w21_write_data(0x00);
        
    epd_w21_write_cmd(0x4F);  // set RAM y address count
    epd_w21_write_data((EPD_HEIGHT-1) % 256);
    epd_w21_write_data((EPD_HEIGHT-1) / 256);
    lcd_chkstatus();
}

static void epd_init_partial(void) {
    // For partial refresh, set up partial refresh mode
    epd_w21_write_cmd(0x3C);  // BorderWavefrom
    epd_w21_write_data(0x80);  // Partial refresh border setting
}

static void epd_update(void) {
    epd_w21_write_cmd(0x22);  // Display Update Control
    epd_w21_write_data(0xF7);
    epd_w21_write_cmd(0x20);  // Activate Display Update Sequence
    lcd_chkstatus();
}

static void epd_update_partial(void) {
    epd_w21_write_cmd(0x22);  // Display Update Control
    epd_w21_write_data(0xFF);
    epd_w21_write_cmd(0x20);  // Activate Display Update Sequence
    lcd_chkstatus();
}

// Public API implementation
bool display_init(void) {
    if (initialized) {
        return true;
    }
    
    // Initialize SPI
    spi_fd = open("/dev/spidev0.0", O_RDWR);
    if (spi_fd < 0) {
        perror("Error opening SPI device");
        return false;
    }
    
    // Configure SPI
    uint8_t mode = SPI_MODE_0;
    uint8_t bits = 8;
    uint32_t speed = 40000000;
    
    if (ioctl(spi_fd, SPI_IOC_WR_MODE, &mode) < 0 ||
        ioctl(spi_fd, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0 ||
        ioctl(spi_fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed) < 0) {
        perror("Error configuring SPI");
        close(spi_fd);
        spi_fd = -1;
        return false;
    }
    
    // Initialize GPIO
    chip = gpiod_chip_open_by_name("gpiochip0");
    if (!chip) {
        perror("Error opening GPIO chip");
        close(spi_fd);
        spi_fd = -1;
        return false;
    }
    
    // Configure GPIO lines
    dc_line = gpiod_chip_get_line(chip, DC_PIN);
    rst_line = gpiod_chip_get_line(chip, RST_PIN);
    busy_line = gpiod_chip_get_line(chip, BUSY_PIN);
    
    if (!dc_line || !rst_line || !busy_line) {
        printf("Error: Failed to get GPIO lines\n");
        display_cleanup();
        return false;
    }
    
    if (gpiod_line_request_output(dc_line, "dc", 0) < 0 ||
        gpiod_line_request_output(rst_line, "rst", 1) < 0 ||
        gpiod_line_request_input(busy_line, "busy") < 0) {
        printf("Error: Failed to configure GPIO lines\n");
        display_cleanup();
        return false;
    }
    
    // Initialize display hardware
    epd_init_hardware();
    
    initialized = true;
    printf("Display SDK initialized successfully\n");
    return true;
}

bool display_image_raw(const uint8_t* data, display_mode_t mode) {
    if (!initialized || !data) {
        printf("Error: Display not initialized or invalid data\n");
        return false;
    }
    
    if (mode == DISPLAY_MODE_PARTIAL) {
        epd_init_partial();
    }
    
    // Write image data to display RAM
    epd_w21_write_cmd(0x24);  // write RAM for black(0)/white (1)
    for (size_t i = 0; i < EPD_ARRAY; i++) {
        epd_w21_write_data(data[i]);
    }
    
    // Update display
    if (mode == DISPLAY_MODE_FULL) {
        epd_update();
    } else {
        epd_update_partial();
    }
    
    return true;
}

bool display_image_png(const char* filename, display_mode_t mode) {
    if (!initialized || !filename) {
        printf("Error: Display not initialized or invalid filename\n");
        return false;
    }
    
    uint8_t image_data[EPD_ARRAY];
    if (!convert_png_to_1bit(filename, image_data)) {
        printf("Error: Failed to convert PNG to 1-bit data\n");
        return false;
    }
    
    return display_image_raw(image_data, mode);
}

bool display_clear(void) {
    if (!initialized) {
        printf("Error: Display not initialized\n");
        return false;
    }
    
    // Create white image data (all bits set to 1)
    uint8_t white_data[EPD_ARRAY];
    memset(white_data, 0xFF, EPD_ARRAY);
    
    return display_image_raw(white_data, DISPLAY_MODE_FULL);
}

void display_sleep(void) {
    if (!initialized) {
        return;
    }
    
    epd_w21_write_cmd(0x10);  // Enter deep sleep
    epd_w21_write_data(0x01);
    delay_ms(100);
}

void display_cleanup(void) {
    if (spi_fd >= 0) {
        close(spi_fd);
        spi_fd = -1;
    }
    
    if (dc_line) {
        gpiod_line_release(dc_line);
        dc_line = NULL;
    }
    if (rst_line) {
        gpiod_line_release(rst_line);
        rst_line = NULL;
    }
    if (busy_line) {
        gpiod_line_release(busy_line);
        busy_line = NULL;
    }
    
    if (chip) {
        gpiod_chip_close(chip);
        chip = NULL;
    }
    
    initialized = false;
    printf("Display SDK cleaned up\n");
}

void display_get_dimensions(uint32_t* width, uint32_t* height) {
    if (width) *width = EPD_WIDTH;
    if (height) *height = EPD_HEIGHT;
}

bool convert_png_to_1bit(const char* filename, uint8_t* output_data) {
    if (!filename || !output_data) {
        return false;
    }
    
    unsigned char* image_data;
    unsigned width, height;
    
    // Load PNG
    unsigned error = lodepng_decode32_file(&image_data, &width, &height, filename);
    if (error) {
        printf("Error loading PNG: %s\n", lodepng_error_text(error));
        return false;
    }
    
    // Check dimensions
    if (width != EPD_WIDTH || height != EPD_HEIGHT) {
        printf("Error: PNG dimensions (%dx%d) don't match display (%dx%d)\n",
               width, height, EPD_WIDTH, EPD_HEIGHT);
        free(image_data);
        return false;
    }
    
    // Convert RGBA to 1-bit
    memset(output_data, 0, EPD_ARRAY);
    
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            unsigned pixel_idx = y * width + x;
            unsigned rgba_idx = pixel_idx * 4;
            
            // Convert to grayscale
            unsigned char gray = (image_data[rgba_idx] + image_data[rgba_idx + 1] + image_data[rgba_idx + 2]) / 3;
            
            // Threshold to 1-bit (0 = black, 1 = white)
            unsigned char bit = (gray > 128) ? 1 : 0;
            
            // Pack into output buffer
            unsigned bit_idx = pixel_idx;
            unsigned byte_idx = bit_idx / 8;
            unsigned bit_pos = 7 - (bit_idx % 8);  // MSB first
            
            if (bit) {
                output_data[byte_idx] |= (1 << bit_pos);
            }
        }
    }
    
    free(image_data);
    return true;
} 