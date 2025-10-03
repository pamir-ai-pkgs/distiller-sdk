#!/bin/bash

# Platform detection helper script for Distiller SDK
# Supports Raspberry Pi CM5 (BCM2712), Rockchip RK3566 (Radxa Zero 3/3W), and Armbian platforms
#
# Environment variable override:
#   DISTILLER_PLATFORM=cm5|radxa|armbian|unknown

# Validate if the provided platform is supported
validate_platform() {
	local platform="$1"
	case "$platform" in
	cm5 | radxa | armbian | unknown)
		return 0
		;;
	*)
		return 1
		;;
	esac
}

# Detect if running on Armbian by checking kernel naming patterns
# This is useful during Armbian build when /etc/armbian-release doesn't exist yet
is_armbian_kernel() {
	# Check running kernel first
	if uname -r 2>/dev/null | grep -qE '(vendor|current|edge|legacy)-(rk35xx|rockchip64)'; then
		return 0
	fi

	# Check installed kernels in /lib/modules (useful during build/chroot)
	if ls /lib/modules/ 2>/dev/null | grep -qE '(vendor|current|edge|legacy)-(rk35xx|rockchip64)'; then
		return 0
	fi

	return 1
}

detect_platform() {
	local platform="unknown"

	# Environment variable override
	if [ -n "$DISTILLER_PLATFORM" ] && validate_platform "$DISTILLER_PLATFORM"; then
		[ -t 2 ] && echo "Platform overridden by DISTILLER_PLATFORM: $DISTILLER_PLATFORM" >&2
		echo "$DISTILLER_PLATFORM"
		return
	elif [ -n "$DISTILLER_PLATFORM" ]; then
		echo "Warning: Invalid DISTILLER_PLATFORM value: $DISTILLER_PLATFORM" >&2
	fi

	# Armbian detection
	if [ -f /etc/armbian-release ] || [ -f /boot/armbianEnv.txt ] || is_armbian_kernel; then
		echo "armbian"
		return
	fi

	# Device tree compatibility checks
	if [ -f /proc/device-tree/compatible ]; then
		local compat
		compat=$(tr '\0' '\n' </proc/device-tree/compatible 2>/dev/null)
		if echo "$compat" | grep -q -e "raspberrypi,5" -e "bcm2712"; then
			echo "cm5"
			return
		elif echo "$compat" | grep -q -e "radxa,zero3" -e "rockchip,rk3566"; then
			echo "radxa"
			return
		fi
	fi

	echo "$platform"
}

get_spi_device() {
	local platform="${1:-$(detect_platform)}"

	case "$platform" in
	armbian | radxa)
		echo "/dev/spidev3.0"
		;;
	cm5)
		echo "/dev/spidev0.0"
		;;
	*)
		echo "/dev/spidev0.0"
		;;
	esac
}

get_gpio_chip() {
	local platform="${1:-$(detect_platform)}"

	case "$platform" in
	armbian | radxa)
		echo "/dev/gpiochip3"
		;;
	cm5)
		echo "/dev/gpiochip0"
		;;
	*)
		echo "/dev/gpiochip0"
		;;
	esac
}

get_gpio_pins() {
	local platform="${1:-$(detect_platform)}"

	case "$platform" in
	armbian | radxa)
		echo "dc_pin=8 rst_pin=2 busy_pin=1"
		;;
	cm5)
		echo "dc_pin=7 rst_pin=13 busy_pin=9"
		;;
	*)
		echo "dc_pin=7 rst_pin=13 busy_pin=9"
		;;
	esac
}

get_config_file() {
	local platform="${1:-$(detect_platform)}"

	case "$platform" in
	armbian | radxa)
		echo "/opt/distiller-sdk/configs/radxa-zero3.conf"
		;;
	cm5)
		echo "/opt/distiller-sdk/configs/cm5.conf"
		;;
	*)
		echo "/opt/distiller-sdk/configs/cm5.conf"
		;;
	esac
}

get_platform_description() {
	local platform="${1:-$(detect_platform)}"

	case "$platform" in
	armbian | radxa)
		echo "Radxa Zero 3/3W (RK3566)"
		;;
	cm5)
		echo "Raspberry Pi CM5"
		;;
	*)
		echo "Unknown Platform"
		;;
	esac
}

print_platform_info() {
	local platform=$(detect_platform)
	local detection_method="auto-detected"

	# Check if platform was overridden
	if [ -n "$DISTILLER_PLATFORM" ] && validate_platform "$DISTILLER_PLATFORM"; then
		detection_method="overridden by DISTILLER_PLATFORM"
	fi

	echo "Platform: $platform ($detection_method)"
	if [ -n "$DISTILLER_PLATFORM" ]; then
		echo "DISTILLER_PLATFORM env var: $DISTILLER_PLATFORM"
	fi
	echo "Description: $(get_platform_description "$platform")"
	echo "SPI Device: $(get_spi_device "$platform")"
	echo "GPIO Chip: $(get_gpio_chip "$platform")"
	echo "GPIO Pins: $(get_gpio_pins "$platform")"
	echo "Config File: $(get_config_file "$platform")"
}

# If script is run directly (not sourced), print platform info
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
	print_platform_info
fi
