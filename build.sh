#!/bin/bash

# Script Name: build.sh
# Description: Downloads required model files and builds the Python SDK wheel package.
# Usage: Run this script inside the distiller-cm5-sdk directory.
#        To include Whisper model download, run: ./build.sh.sh --whisper

set -e

# Parse arguments
INCLUDE_WHISPER=false
for arg in "$@"; do
    if [ "$arg" == "--whisper" ]; then
        INCLUDE_WHISPER=true
    fi
done

# Helper function to create directory if it does not exist
make_dir_if_not_exists() {
    if [ ! -d "$1" ]; then
        echo "[INFO] Creating directory: $1"
        mkdir -p "$1"
    fi
}

# Helper function to download a file if it does not already exist
download_if_not_exists() {
    local url="$1"
    local output_path="$2"
    if [ ! -f "$output_path" ]; then
        echo "[INFO] Downloading $output_path"
        curl -L "$url" -o "$output_path"
    else
        echo "[INFO] File already exists: $output_path"
    fi
}

# Whisper model files (only if --whisper passed)
download_whisper_models() {
    WHISPER_DIR="src/distiller_cm5_sdk/whisper/models/faster-distil-whisper-small.en"
    make_dir_if_not_exists "$WHISPER_DIR"

    download_if_not_exists "https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/model.bin?download=true" "$WHISPER_DIR/model.bin"
    download_if_not_exists "https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/config.json?download=true" "$WHISPER_DIR/config.json"
    download_if_not_exists "https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/preprocessor_config.json?download=true" "$WHISPER_DIR/preprocessor_config.json"
    download_if_not_exists "https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/tokenizer.json?download=true" "$WHISPER_DIR/tokenizer.json"
    download_if_not_exists "https://huggingface.co/Systran/faster-distil-whisper-small.en/resolve/main/vocabulary.json?download=true" "$WHISPER_DIR/vocabulary.json"
}

# Conditionally download Whisper models
if [ "$INCLUDE_WHISPER" = true ]; then
    echo "[INFO] --whisper flag detected, downloading Whisper model files..."
    download_whisper_models
else
    echo "[INFO] Skipping Whisper model download (use --whisper to enable)"
fi

# Parakeet model files
PARAKEET_DIR="src/distiller_cm5_sdk/parakeet/models"
make_dir_if_not_exists "$PARAKEET_DIR"

download_if_not_exists "https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/encoder.onnx" "$PARAKEET_DIR/encoder.onnx"
download_if_not_exists "https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/decoder.onnx" "$PARAKEET_DIR/decoder.onnx"
download_if_not_exists "https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/joiner.onnx" "$PARAKEET_DIR/joiner.onnx"
download_if_not_exists "https://huggingface.co/tommy1900/Parakeet-onnx/resolve/main/tokens.txt" "$PARAKEET_DIR/tokens.txt"
download_if_not_exists "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx" "$PARAKEET_DIR/silero_vad.onnx"

# Piper files
PIPER_MODEL_DIR="src/distiller_cm5_sdk/piper/models"
PIPER_EXE_FILE_DIR="src/distiller_cm5_sdk/piper/piper"
PIPER_EXE_FILE_UNZIP_DIR="src/distiller_cm5_sdk/piper"
PIPER_TAR="src/distiller_cm5_sdk/piper/piper_arm64.tar.gz"
make_dir_if_not_exists "$PIPER_MODEL_DIR"
make_dir_if_not_exists "$PIPER_EXE_FILE_DIR"

# Check for Piper executable files
PIPER_REQUIRED_FILES=(
    "libespeak-ng.so.1"
    "libespeak-ng.so.1.1.51"
    "libonnxruntime.so.1.14.1"
    "libpiper_phonemize.so.1"
    "libpiper_phonemize.so.1.1.0"
    "libtashkeel_model.ort"
    "piper"
)

piper_needs_download=false
for file in "${PIPER_REQUIRED_FILES[@]}"; do
    if [ ! -f "$PIPER_EXE_FILE_DIR/$file" ]; then
        piper_needs_download=true
        break
    fi
done

if [ "$piper_needs_download" = true ]; then
    echo "[INFO] Piper files are incomplete. Downloading and extracting..."
    download_if_not_exists "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz" "$PIPER_TAR"
    tar -xvf "$PIPER_TAR" -C "$PIPER_EXE_FILE_UNZIP_DIR"
    rm "$PIPER_TAR"
else
    echo "[INFO] All Piper executable files already exist."
fi

# Piper voice model and config
PIPER_MODEL_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true"
PIPER_CONFIG_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true"

PIPER_MODEL_FILE="$PIPER_MODEL_DIR/en_US-amy-medium.onnx"
PIPER_CONFIG_FILE="$PIPER_MODEL_DIR/en_US-amy-medium.onnx.json"

download_if_not_exists "$PIPER_MODEL_URL" "$PIPER_MODEL_FILE"
download_if_not_exists "$PIPER_CONFIG_URL" "$PIPER_CONFIG_FILE"

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Activating Python virtual environment..."
    source .venv/bin/activate
else
    echo "[ERROR] Python virtual environment not found in .venv"
    echo "        Please create one with: python3 -m venv .venv"
    exit 1
fi

# Build wheel package
echo "[INFO] Building the Python wheel package..."
python -m build

echo "[INFO] Build completed successfully."
