#!/bin/bash

# Platform detection helper script for Distiller SDK
# Supports Raspberry Pi CM5 (BCM2712) and MYIR MYD-LR3576 (RK3576) platforms
#
# Environment variable override:
#   DISTILLER_PLATFORM=cm5|myd-lr3576|unknown

# Validate if the provided platform is supported
validate_platform() {
	local platform="$1"
	case "$platform" in
	cm5 | myd-lr3576 | unknown)
		return 0
		;;
	*)
		return 1
		;;
	esac
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

	# Raspberry Pi CM5 detection via cpuinfo
	if grep -q "Raspberry Pi Compute Module 5" /proc/cpuinfo 2>/dev/null; then
		echo "cm5"
		return
	fi

	# MYIR MYD-LR3576 detection (check model string)
	if [ -f /proc/device-tree/model ]; then
		local model
		model=$(tr '\0' ' ' </proc/device-tree/model 2>/dev/null)
		if echo "$model" | grep -qiE "MYIR|MYD-LR3576"; then
			echo "myd-lr3576"
			return
		fi
	fi

	# Device tree compatibility checks
	if [ -f /proc/device-tree/compatible ]; then
		local compat
		compat=$(tr '\0' '\n' </proc/device-tree/compatible 2>/dev/null)
		if echo "$compat" | grep -q -e "raspberrypi,5" -e "bcm2712"; then
			echo "cm5"
			return
		elif echo "$compat" | grep -q "rockchip,rk3576"; then
			# RK3576 - assume MYIR board
			echo "myd-lr3576"
			return
		fi
	fi

	echo "$platform"
}

get_spi_device() {
	local platform="${1:-$(detect_platform)}"

	case "$platform" in
	myd-lr3576)
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
	myd-lr3576)
		echo "/dev/gpiochip4"
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
	myd-lr3576)
		# TBD: Determine actual GPIO pins during hardware bringup
		echo "dc_pin=0 rst_pin=0 busy_pin=0"
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
	myd-lr3576)
		echo "/opt/distiller-sdk/configs/myd-lr3576.conf"
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
	myd-lr3576)
		echo "MYIR MYD-LR3576 (RK3576)"
		;;
	cm5)
		echo "Raspberry Pi CM5"
		;;
	*)
		echo "Unknown Platform"
		;;
	esac
}

# Main execution - if script is called directly (not sourced)
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
	detect_platform
fi
