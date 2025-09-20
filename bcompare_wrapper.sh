#!/bin/bash
# BeyondCompare wrapper script for TFM
# This script launches BeyondCompare with the left and right pane directories

# Check if BeyondCompare is available
if ! command -v bcompare &> /dev/null; then
    echo "Error: BeyondCompare (bcompare) is not installed or not in PATH"
    echo "Please install BeyondCompare and ensure 'bcompare' command is available"
    exit 1
fi

# Check if TFM environment variables are set
if [ -z "$TFM_LEFT_DIR" ] || [ -z "$TFM_RIGHT_DIR" ]; then
    echo "Error: TFM environment variables not set"
    echo "This script should be run from within TFM"
    exit 1
fi

# Launch BeyondCompare with the directories
echo "Launching BeyondCompare..."
echo "Left directory: $TFM_LEFT_DIR"
echo "Right directory: $TFM_RIGHT_DIR"

bcompare "$TFM_LEFT_DIR" "$TFM_RIGHT_DIR"