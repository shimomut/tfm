#!/bin/bash

# reveal_in_finder.sh - Opens Finder and selects the current file/directory on macOS
# This script uses TFM environment variables to get the current selection

# Check if running on macOS
if [ "$(uname)" != "Darwin" ]; then
    echo "Error: reveal_in_finder.sh only works on macOS"
    exit 1
fi

# Check if TFM environment variables are set
if [ -z "$TFM_THIS_DIR" ]; then
    echo "Error: TFM environment variables not set"
    echo "This script should be run from within TFM"
    exit 1
fi

# Get the current directory
CURRENT_DIR="$TFM_THIS_DIR"

# Check if there are selected files
if [ -n "$TFM_THIS_SELECTED" ]; then
    # Parse selected files (properly handle quoted filenames)
    eval "SELECTED_FILES=($TFM_THIS_SELECTED)"
    
    # Get the first selected file
    SELECTED_FILE="${SELECTED_FILES[0]}"
    
    if [ -n "$SELECTED_FILE" ]; then
        # Build full path to the selected file
        TARGET_PATH="$CURRENT_DIR/$SELECTED_FILE"
        
        # Check if the target exists
        if [ -e "$TARGET_PATH" ]; then
            echo "Revealing selected file in Finder: $SELECTED_FILE"
            open -R "$TARGET_PATH"
        else
            echo "Error: Selected file does not exist: $TARGET_PATH"
            exit 1
        fi
    else
        echo "Error: No valid file selected"
        exit 1
    fi
else
    # No files selected, reveal the current directory
    if [ -d "$CURRENT_DIR" ]; then
        echo "Revealing current directory in Finder: $CURRENT_DIR"
        open "$CURRENT_DIR"
    else
        echo "Error: Current directory does not exist: $CURRENT_DIR"
        exit 1
    fi
fi