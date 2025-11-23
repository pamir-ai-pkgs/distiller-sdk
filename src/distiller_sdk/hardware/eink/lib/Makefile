# Makefile for e-ink display library and tests
CARGO = cargo
RUST_TARGET = aarch64-unknown-linux-gnu

# Default target
.PHONY: all
all: build

# Build the library
.PHONY: build
build:
	$(CARGO) build --release

# Build the test binary
.PHONY: build-test
build-test:
	$(CARGO) build --release --bin test_display

# Run Rust tests
.PHONY: test
test:
	$(CARGO) test

# Run the display test binary
.PHONY: run-test
run-test: build-test
	./target/release/test_display

# Run the display test binary with environment override
.PHONY: run-test-240x416
run-test-240x416: build-test
	DISTILLER_EINK_FIRMWARE=EPD240x416 ./target/release/test_display

# Clean build artifacts
.PHONY: clean
clean:
	$(CARGO) clean
	rm -f *.so

# Install cross-compilation target
.PHONY: install-target
install-target:
	rustup target add $(RUST_TARGET)

# Cross-compile for ARM64
.PHONY: cross-build
cross-build:
	$(CARGO) build --release --target $(RUST_TARGET)

# Show build info
.PHONY: info
info:
	@echo "Rust version:"
	@rustc --version
	@echo "Cargo version:"
	@cargo --version
	@echo "Available targets:"
	@rustup target list --installed
	@echo "Library will be built as: libdistiller_display_sdk_shared.so"

# Help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build         - Build the library"
	@echo "  build-test    - Build the test binary"
	@echo "  test          - Run Rust unit tests"
	@echo "  run-test      - Run the display test binary"
	@echo "  run-test-240x416 - Run test with EPD240x416 firmware"
	@echo "  clean         - Clean build artifacts"
	@echo "  install-target - Install cross-compilation target"
	@echo "  cross-build   - Cross-compile for ARM64"
	@echo "  info          - Show build environment info"
	@echo "  help          - Show this help message"
