#!/bin/bash
# This script activates the Distiller SDK Python virtual environment1

[ -f /opt/distiller-sdk/.venv/bin/activate ] || {
	echo "ERROR: Virtual environment activation script not found." >&2
	exit 1
}

[ -d /opt/distiller-sdk/src ] || {
	echo "ERROR: SDK source directory not found." >&2
	exit 1
}

[ -d /opt/distiller-sdk/lib ] || {
	echo "ERROR: SDK library directory not found." >&2
	exit 1
}

# shellcheck disable=SC1091
source /opt/distiller-sdk/.venv/bin/activate
export PYTHONPATH="/opt/distiller-sdk/src:$PYTHONPATH"
export LD_LIBRARY_PATH="/opt/distiller-sdk/lib:$LD_LIBRARY_PATH"

echo "INFO: Distiller SDK environment activated"
