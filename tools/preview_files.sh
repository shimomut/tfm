#!/bin/bash
#
# Preview Files Script for TFM
# Opens selected files with macOS Preview.app
# 
# Features:
# - macOS-only support (other OS support planned for future)
# - Supports image files: jpg, jpeg, png, gif, bmp, tiff, tif, webp, heic, heif, pdf, svg
# - Handles multiple file selection
# - Validates file types and existence
# - Provides informative error messages
#
# Usage:
# This script is designed to be called from TFM's external programs menu.
# It uses TFM environment variables:
# - TFM_THIS_DIR: Current directory
# - TFM_THIS_SELECTED: Space-separated quoted list of selected files
#

# Check if we're running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: This script only supports macOS"
    echo "Preview functionality for other operating systems will be supported in the future"
    exit 1
fi

# Check if Preview.app is available
if [[ ! -d "/System/Applications/Preview.app" ]] && [[ ! -d "/Applications/Preview.app" ]]; then
    echo "Error: Preview.app not found"
    echo "Please ensure Preview.app is installed"
    exit 1
fi

# Get the current directory and selected files from TFM environment variables
CURRENT_DIR="${TFM_THIS_DIR:-$(pwd)}"
SELECTED_FILES="${TFM_THIS_SELECTED:-}"

# Verify the current directory exists
if [[ ! -d "$CURRENT_DIR" ]]; then
    echo "Error: Current directory does not exist: $CURRENT_DIR"
    exit 1
fi

# Check if any files are selected
if [[ -z "$SELECTED_FILES" ]]; then
    echo "Error: No files selected"
    echo "Please select one or more files to preview"
    exit 1
fi

# Define supported image file extensions
SUPPORTED_EXTENSIONS=("jpg" "jpeg" "png" "gif" "bmp" "tiff" "tif" "webp" "heic" "heif" "pdf" "svg")

# Function to check if a file extension is supported
is_supported_extension() {
    local file="$1"
    local extension="${file##*.}"
    extension=$(echo "$extension" | tr '[:upper:]' '[:lower:]')
    
    for ext in "${SUPPORTED_EXTENSIONS[@]}"; do
        if [[ "$extension" == "$ext" ]]; then
            return 0
        fi
    done
    return 1
}

# Function to check if a file is an image using file command as fallback
is_image_file() {
    local file="$1"
    
    # First check by extension
    if is_supported_extension "$file"; then
        return 0
    fi
    
    # Fallback: use file command to detect image files
    if command -v file &> /dev/null; then
        local file_type=$(file -b --mime-type "$file" 2>/dev/null)
        if [[ "$file_type" =~ ^image/ ]] || [[ "$file_type" == "application/pdf" ]]; then
            return 0
        fi
    fi
    
    return 1
}

# Parse selected files and build list of valid files to preview
PREVIEW_FILES=()
SKIPPED_FILES=()

# TFM_THIS_SELECTED contains space-separated quoted filenames
# We need to evaluate them to remove quotes and handle spaces properly
eval "selected_array=($SELECTED_FILES)"

for file in "${selected_array[@]}"; do
    if [[ -n "$file" ]]; then
        # Convert relative paths to absolute paths
        if [[ ! "$file" = /* ]]; then
            file="$CURRENT_DIR/$file"
        fi
        
        # Check if file exists and is a regular file
        if [[ -f "$file" ]]; then
            if is_image_file "$file"; then
                PREVIEW_FILES+=("$file")
                echo "Adding to preview: $(basename "$file")"
            else
                SKIPPED_FILES+=("$file")
                echo "Skipping unsupported file type: $(basename "$file")"
            fi
        elif [[ -d "$file" ]]; then
            SKIPPED_FILES+=("$file")
            echo "Skipping directory: $(basename "$file")"
        else
            SKIPPED_FILES+=("$file")
            echo "Warning: File does not exist: $(basename "$file")"
        fi
    fi
done

# Report skipped files
if [[ ${#SKIPPED_FILES[@]} -gt 0 ]]; then
    echo ""
    echo "Skipped ${#SKIPPED_FILES[@]} file(s):"
    echo "Currently supported file types: ${SUPPORTED_EXTENSIONS[*]}"
    echo "Support for other file types will be added in the future"
fi

# Check if we have any files to preview
if [[ ${#PREVIEW_FILES[@]} -eq 0 ]]; then
    echo ""
    echo "Error: No supported files found to preview"
    echo "Supported file types: ${SUPPORTED_EXTENSIONS[*]}"
    exit 1
fi

# Open files with Preview.app
echo ""
echo "Opening ${#PREVIEW_FILES[@]} file(s) with Preview.app..."

# Use 'open' command to open files with Preview.app
# The -a flag specifies the application to use
exec open -a "Preview" "${PREVIEW_FILES[@]}"