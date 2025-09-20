#!/bin/bash
# BeyondCompare file comparison wrapper script for TFM
# This script launches BeyondCompare to compare selected files from left and right panes

# Check if BeyondCompare is available
if ! command -v bcompare &> /dev/null; then
    echo "Error: BeyondCompare (bcompare) is not installed or not in PATH"
    echo "Please install BeyondCompare and ensure 'bcompare' command is available"
    exit 1
fi

# Check if TFM environment variables are set
if [ -z "$TFM_LEFT_SELECTED" ] || [ -z "$TFM_RIGHT_SELECTED" ]; then
    echo "Error: TFM file selection environment variables not set"
    echo "This script should be run from within TFM with files selected in both panes"
    exit 1
fi

if [ -z "$TFM_LEFT_DIR" ] || [ -z "$TFM_RIGHT_DIR" ]; then
    echo "Error: TFM directory environment variables not set"
    echo "This script should be run from within TFM"
    exit 1
fi

# Parse selected files (remove quotes and get first file from each pane)
LEFT_FILES=($TFM_LEFT_SELECTED)
RIGHT_FILES=($TFM_RIGHT_SELECTED)

# Remove quotes from filenames if present
LEFT_FILE=$(echo "${LEFT_FILES[0]}" | sed 's/^"\(.*\)"$/\1/')
RIGHT_FILE=$(echo "${RIGHT_FILES[0]}" | sed 's/^"\(.*\)"$/\1/')

# Build full paths
LEFT_PATH="$TFM_LEFT_DIR/$LEFT_FILE"
RIGHT_PATH="$TFM_RIGHT_DIR/$RIGHT_FILE"

# Check if files exist
if [ ! -f "$LEFT_PATH" ]; then
    echo "Error: Left file does not exist: $LEFT_PATH"
    exit 1
fi

if [ ! -f "$RIGHT_PATH" ]; then
    echo "Error: Right file does not exist: $RIGHT_PATH"
    exit 1
fi

# Launch BeyondCompare with the files
echo "Launching BeyondCompare for file comparison..."
echo "Left file:  $LEFT_PATH"
echo "Right file: $RIGHT_PATH"
echo

bcompare "$LEFT_PATH" "$RIGHT_PATH"