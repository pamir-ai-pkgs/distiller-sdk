#!/bin/bash

# Script Name: build.sh
# Description: Builds Rust library for the Python SDK.
# Usage: Run this script inside the distiller-sdk directory.
#        Options:
#        --skip-rust     Skip Rust library build (if already built)

set -e

# Parse arguments
SKIP_RUST=false
for arg in "$@"; do
	if [ "$arg" == "--skip-rust" ]; then
		SKIP_RUST=true
	fi
done

# Build Rust library for e-ink display
if [ "$SKIP_RUST" = true ]; then
	echo "[INFO] Skipping Rust library build (--skip-rust flag provided)"
	# Still check if the library exists
	if [ -f "src/distiller_sdk/hardware/eink/lib/libdistiller_display_sdk_shared.so" ]; then
		echo "[INFO] Rust library already exists"
	else
		echo "[WARNING] Rust library not found - e-ink display support may not be available"
	fi
else
	echo "[INFO] Checking Rust library for e-ink display..."
	RUST_LIB_DIR="src/distiller_sdk/hardware/eink/lib"
	RUST_LIB_FILE="$RUST_LIB_DIR/libdistiller_display_sdk_shared.so"

	if [ -d "$RUST_LIB_DIR" ]; then
		# Check if library exists and is up-to-date
		rebuild_needed=false

		if [ ! -f "$RUST_LIB_FILE" ]; then
			echo "[INFO] Rust library not found, building..."
			rebuild_needed=true
		else
			# Check if any source file is newer than the library
			if find "$RUST_LIB_DIR/src" -name "*.rs" -newer "$RUST_LIB_FILE" 2>/dev/null | grep -q .; then
				echo "[INFO] Rust source files have changed, rebuilding..."
				rebuild_needed=true
			elif [ -f "$RUST_LIB_DIR/Cargo.toml" ] && [ "$RUST_LIB_DIR/Cargo.toml" -nt "$RUST_LIB_FILE" ]; then
				echo "[INFO] Cargo.toml has changed, rebuilding..."
				rebuild_needed=true
			else
				echo "[INFO] Rust library is up-to-date, skipping rebuild"
			fi
		fi

		if [ "$rebuild_needed" = true ]; then
			echo "[INFO] Entering $RUST_LIB_DIR"
			cd "$RUST_LIB_DIR"

			# Only clean if we're rebuilding
			echo "[INFO] Cleaning previous build artifacts..."
			make -f Makefile.rust clean || true

			# Build the Rust library for ARM64
			echo "[INFO] Building Rust library for ARM64..."
			if make -f Makefile.rust build; then
				echo "[INFO] Rust library built successfully"
				# Verify the library was built
				if [ -f "libdistiller_display_sdk_shared.so" ]; then
					echo "[INFO] Rust library available at: $RUST_LIB_DIR/libdistiller_display_sdk_shared.so"
				else
					echo "[ERROR] Rust library build completed but library file not found"
					exit 1
				fi
			else
				echo "[ERROR] Failed to build Rust library"
				exit 1
			fi

			# Clean build artifacts but keep the library
			echo "[INFO] Cleaning Rust build artifacts to reduce package size..."
			rm -rf target/ target-build
			echo "[INFO] Rust build artifacts cleaned"

			# Return to original directory
			cd - >/dev/null
		fi
	else
		echo "[WARNING] Rust library directory not found at $RUST_LIB_DIR"
		echo "[WARNING] E-ink display support may not be available"
	fi
fi

echo "[INFO] Build completed successfully."
