#!/bin/bash
# Universal Debian Package Builder
# Compatible with all Pamir AI projects
# Modern Debian packaging practices

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DIST_DIR="dist"
TARGET_ARCHITECTURE="${TARGET_ARCH:-arm64}" # Can be overridden with TARGET_ARCH env var
DEBIAN_DIR="debian"
# Platform configuration no longer needed - single universal package

# Logging functions
log_info() {
	echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
	echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
	echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
	echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Detect project type
detect_project_type() {
	local project_type="unknown"

	# Check for Python project with uv
	if [ -f "pyproject.toml" ] && grep -q "uv" "pyproject.toml" 2>/dev/null; then
		project_type="python-uv"
	elif [ -f "pyproject.toml" ]; then
		project_type="python"
	# Check for Node.js project
	elif [ -f "package.json" ]; then
		project_type="nodejs"
	# Check for DKMS project
	elif [ -f "dkms.conf" ]; then
		project_type="dkms"
	# Check for systemd service project
	elif [ -d "systemd" ] || ls *.service 2>/dev/null | grep -q service; then
		project_type="systemd"
	fi

	echo "$project_type"
}

# Get package name from control file
get_package_name() {
	if [ -f "${DEBIAN_DIR}/control" ]; then
		grep "^Package:" "${DEBIAN_DIR}/control" | awk '{print $2}' | head -1
	else
		echo ""
	fi
}

# Check build dependencies
check_build_dependencies() {
	local missing_deps=""

	# Check for dpkg-buildpackage
	if ! command -v dpkg-buildpackage >/dev/null 2>&1; then
		if ! dpkg -l dpkg-dev 2>/dev/null | grep -q "^ii"; then
			missing_deps="$missing_deps dpkg-dev"
		fi
	fi

	# Check for dch (from devscripts)
	if ! command -v dch >/dev/null 2>&1; then
		if ! dpkg -l devscripts 2>/dev/null | grep -q "^ii"; then
			missing_deps="$missing_deps devscripts"
		fi
	fi

	# Check for debhelper (check if package is installed)
	if ! dpkg -l debhelper 2>/dev/null | grep -q "^ii"; then
		missing_deps="$missing_deps debhelper"
	fi

	# Check for fakeroot
	if ! command -v fakeroot >/dev/null 2>&1; then
		if ! dpkg -l fakeroot 2>/dev/null | grep -q "^ii"; then
			missing_deps="$missing_deps fakeroot"
		fi
	fi

	# Check for device-tree-compiler (for DKMS projects)
	local project_type=$(detect_project_type)
	if [ "$project_type" = "dkms" ]; then
		if ! command -v dtc >/dev/null 2>&1; then
			if ! dpkg -l device-tree-compiler 2>/dev/null | grep -q "^ii"; then
				missing_deps="$missing_deps device-tree-compiler"
			fi
		fi
	fi

	if [ -n "$missing_deps" ]; then
		log_error "Missing build dependencies:$missing_deps"
		log_info "Install with: sudo apt-get install$missing_deps"
		return 1
	fi

	return 0
}

# Clean build artifacts
clean_build() {
	log_info "Cleaning build artifacts..."

	local package_name=$(get_package_name)
	if [ -n "$package_name" ]; then
		# Clean debian build files
		[ -d "${DEBIAN_DIR}/${package_name}" ] && rm -rf "${DEBIAN_DIR}/${package_name}"

		# Clean package files in parent directory
		rm -f ../"${package_name}"_*.deb
		rm -f ../"${package_name}"_*.dsc
		rm -f ../"${package_name}"_*.tar.*
		rm -f ../"${package_name}"_*.changes
		rm -f ../"${package_name}"_*.buildinfo
	fi

	# Also clean old package names for backward compatibility
	for old_name in distiller-cm5-sdk distiller-radxa-sdk; do
		[ -d "${DEBIAN_DIR}/${old_name}" ] && rm -rf "${DEBIAN_DIR}/${old_name}"
		rm -f ../"${old_name}"_*.deb
		rm -f ../"${old_name}"_*.dsc
		rm -f ../"${old_name}"_*.tar.*
		rm -f ../"${old_name}"_*.changes
		rm -f ../"${old_name}"_*.buildinfo
	done

	# Clean common debian build files
	[ -f "${DEBIAN_DIR}/files" ] && rm -f "${DEBIAN_DIR}/files"
	[ -f "${DEBIAN_DIR}/*.debhelper.log" ] && rm -f "${DEBIAN_DIR}"/*.debhelper.log
	[ -f "${DEBIAN_DIR}/*.substvars" ] && rm -f "${DEBIAN_DIR}"/*.substvars
	[ -d "${DEBIAN_DIR}/.debhelper" ] && rm -rf "${DEBIAN_DIR}/.debhelper"
	[ -f "${DEBIAN_DIR}/debhelper-build-stamp" ] && rm -f "${DEBIAN_DIR}/debhelper-build-stamp"

	# Clean distribution directory
	rm -rf "${DIST_DIR}"

	# Project-specific cleaning
	local project_type=$(detect_project_type)
	case "$project_type" in
	python-uv | python)
		rm -rf build/ *.egg-info/ .venv/ uv.lock __pycache__/
		find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
		find . -type f -name "*.pyc" -delete 2>/dev/null || true
		;;
	nodejs)
		# Keep node_modules for faster rebuilds unless deep clean requested
		[ "$1" = "deep" ] && rm -rf node_modules/
		;;
	dkms)
		make clean 2>/dev/null || true
		;;
	esac

	log_success "Clean completed"
}

# Check if Rust library needs rebuilding
check_rust_rebuild_needed() {
	local rust_lib="src/distiller_cm5_sdk/hardware/eink/lib/libdistiller_display_sdk_shared.so"
	local rust_src_dir="src/distiller_cm5_sdk/hardware/eink/lib/src"

	# If library doesn't exist, rebuild is needed
	if [ ! -f "$rust_lib" ]; then
		log_info "Rust library not found, rebuild needed"
		return 0
	fi

	# Check if any Rust source file is newer than the library
	local rebuild_needed=false
	if [ -d "$rust_src_dir" ]; then
		# Find any .rs file newer than the library
		if find "$rust_src_dir" -name "*.rs" -newer "$rust_lib" | grep -q .; then
			log_info "Rust source files have changed, rebuild needed"
			rebuild_needed=true
		fi

		# Also check Cargo.toml and Cargo.lock
		local cargo_toml="src/distiller_cm5_sdk/hardware/eink/lib/Cargo.toml"
		local cargo_lock="src/distiller_cm5_sdk/hardware/eink/lib/Cargo.lock"

		if [ -f "$cargo_toml" ] && [ "$cargo_toml" -nt "$rust_lib" ]; then
			log_info "Cargo.toml has changed, rebuild needed"
			rebuild_needed=true
		fi

		if [ -f "$cargo_lock" ] && [ "$cargo_lock" -nt "$rust_lib" ]; then
			log_info "Cargo.lock has changed, rebuild needed"
			rebuild_needed=true
		fi
	fi

	if [ "$rebuild_needed" = true ]; then
		return 0
	else
		log_info "Rust library is up-to-date, no rebuild needed"
		return 1
	fi
}

# Prepare Python project with uv
prepare_python_uv() {
	log_info "Preparing Python project with uv..."

	# Special handling for distiller-cm5-sdk
	local package_name=$(get_package_name)
	if [ "$package_name" = "distiller-cm5-sdk" ]; then
		log_info "Detected distiller-cm5-sdk - checking if build is needed..."

		# Check if build.sh exists
		if [ -f "./build.sh" ]; then
			# Make it executable
			chmod +x ./build.sh

			# Determine if we should skip Rust rebuild
			local build_flags=""
			if check_rust_rebuild_needed; then
				log_info "Running build.sh to download models and build Rust library..."
			else
				log_info "Running build.sh to download models (skipping Rust library rebuild)..."
				build_flags="--skip-rust"
			fi

			# Run build.sh with appropriate flags
			if ./build.sh $build_flags; then
				log_success "build.sh completed successfully"

				# Verify Rust library was built
				if [ -f "src/distiller_cm5_sdk/hardware/eink/lib/libdistiller_display_sdk_shared.so" ]; then
					log_success "Rust library found and ready for packaging"
				else
					log_error "Rust library not found after build.sh"
					return 1
				fi
			else
				log_error "build.sh failed"
				return 1
			fi
		else
			log_error "build.sh not found for distiller-cm5-sdk"
			return 1
		fi
	fi

	# Check for uv.lock - we don't include it in packages
	if [ -f "uv.lock" ]; then
		log_warning "Found uv.lock - this file will not be included in the package"
		log_info "uv.lock will be generated on the target system during installation"
	fi

	# Check for required files
	if [ ! -f "pyproject.toml" ]; then
		log_error "Missing pyproject.toml file"
		return 1
	fi

	return 0
}

# Prepare Node.js project
prepare_nodejs() {
	log_info "Preparing Node.js project..."

	# Check for package.json
	if [ ! -f "package.json" ]; then
		log_error "Missing package.json file"
		return 1
	fi

	# Install production dependencies
	if [ -d "node_modules" ]; then
		log_info "Using existing node_modules directory"
	else
		log_info "Installing production dependencies..."
		npm ci --omit=dev --omit=optional || npm install --production
	fi

	return 0
}

# Prepare DKMS project
prepare_dkms() {
	log_info "Preparing DKMS project..."

	# Check for dkms.conf
	if [ ! -f "dkms.conf" ]; then
		log_error "Missing dkms.conf file"
		return 1
	fi

	# Compile device tree overlays if present
	for dts in *.dts; do
		if [ -f "$dts" ]; then
			local dtbo="${dts%.dts}.dtbo"
			log_info "Compiling device tree overlay: $dts"
			dtc -@ -I dts -O dtb -o "$dtbo" "$dts" || log_warning "Failed to compile $dts"
		fi
	done

	return 0
}

# Build Debian package
build_package() {
	local project_type=$(detect_project_type)
	local package_name=$(get_package_name)

	log_info "Project type: $project_type"
	log_info "Package name: $package_name"
	log_info "Target architecture: $TARGET_ARCHITECTURE"

	# Prepare project based on type
	case "$project_type" in
	python-uv)
		prepare_python_uv || return 1
		;;
	nodejs)
		prepare_nodejs || return 1
		;;
	dkms)
		prepare_dkms || return 1
		;;
	esac

	# Update changelog if needed
	if [ ! -f "${DEBIAN_DIR}/changelog" ]; then
		log_info "Creating initial changelog..."
		dch --create --package "distiller-cm5-sdk" --newversion "1.0.0" --distribution stable "Initial release"
	fi

	log_info "Building universal Debian package..."

	# Check if we're cross-compiling
	local current_arch=$(dpkg --print-architecture)
	local build_flags="-us -uc -b"

	if [ "$current_arch" != "$TARGET_ARCHITECTURE" ]; then
		log_warning "Cross-compiling from $current_arch to $TARGET_ARCHITECTURE"
		log_info "Note: For production packages, building on target architecture is recommended"
		build_flags="$build_flags -d --host-arch=$TARGET_ARCHITECTURE"
	fi

	# Use dpkg-buildpackage with appropriate flags
	if dpkg-buildpackage $build_flags; then
		log_success "Package built successfully"
	else
		log_error "Package build failed"
		return 1
	fi

	# Move built packages to dist directory
	mkdir -p "${DIST_DIR}"

	if ls ../"${package_name}"_*.deb 2>/dev/null; then
		mv ../"${package_name}"_*.deb "${DIST_DIR}/"
		log_success "Package moved to ${DIST_DIR}/"

		# Display package information
		for deb in "${DIST_DIR}"/${package_name}_*.deb; do
			if [ -f "$deb" ]; then
				log_info "Package: $(basename "$deb")"
				log_info "Size: $(du -h "$deb" | cut -f1)"
				log_info "Architecture: $(dpkg --field "$deb" Architecture)"
				log_info "Provides: $(dpkg --field "$deb" Provides || echo 'N/A')"
			fi
		done
	else
		log_error "No .deb package found after build"
		return 1
	fi

	# Clean up other build artifacts
	rm -f ../"${package_name}"_*.dsc
	rm -f ../"${package_name}"_*.tar.*
	rm -f ../"${package_name}"_*.changes
	rm -f ../"${package_name}"_*.buildinfo

	return 0
}

# Display usage information
show_usage() {
	cat <<EOF
Usage: $0 [OPTIONS]

Universal Debian package builder for Pamir AI projects.

OPTIONS:
    clean       Clean build artifacts and exit
    check       Check build dependencies and exit
    help        Show this help message
    native      Build for current architecture instead of arm64

Without options, builds a universal package for arm64 that auto-detects
the platform at installation time.

ENVIRONMENT VARIABLES:
    TARGET_ARCH  Override target architecture (default: arm64)
                 Example: TARGET_ARCH=amd64 ./build-deb.sh

SUPPORTED PROJECT TYPES:
    - Python projects with uv
    - Node.js projects
    - DKMS kernel modules
    - Systemd services

The script automatically detects the project type and builds accordingly.
Default target architecture: arm64 (use 'native' option to build for current arch)
EOF
}

# Main script execution
main() {
	# Parse command line arguments
	case "${1:-}" in
	clean)
		clean_build "$@"
		exit 0
		;;
	check)
		if check_build_dependencies; then
			log_success "All build dependencies are installed"
			exit 0
		else
			exit 1
		fi
		;;
	native)
		# Build for current architecture
		TARGET_ARCHITECTURE=$(dpkg --print-architecture)
		log_info "Building for native architecture: $TARGET_ARCHITECTURE"
		;;
	help | --help | -h)
		show_usage
		exit 0
		;;
	"")
		# Continue with build (default is both)
		;;
	*)
		log_error "Unknown option: $1"
		show_usage
		exit 1
		;;
	esac

	# Check if we're in a valid project directory
	if [ ! -d "$DEBIAN_DIR" ]; then
		log_error "No debian/ directory found. This script must be run from a project root."
		exit 1
	fi

	# Check build dependencies
	if ! check_build_dependencies; then
		exit 1
	fi

	# Detect project type
	local project_type=$(detect_project_type)
	if [ "$project_type" = "unknown" ]; then
		log_warning "Could not detect project type, proceeding with generic build"
	fi

	# Build the package
	if build_package; then
		log_success "Build completed successfully!"
		log_info "Package(s) available in ${DIST_DIR}/"
		exit 0
	else
		log_error "Build failed!"
		exit 1
	fi
}

# Run main function
main "$@"
