#!/bin/bash

# create_archive.sh - Create archive from selected files using TFM environment variables
# This script uses TFM environment variables for integration

# Check if TFM environment variables are set
if [ -z "$TFM_THIS_DIR" ]; then
    echo "Error: TFM environment variables not set"
    echo "This script should be run from within TFM"
    exit 1
fi

# Get current directory
CURRENT_DIR="$TFM_THIS_DIR"

# Check if files are selected
if [ -z "$TFM_THIS_SELECTED" ]; then
    echo "Error: No files selected"
    echo "Please select files to archive using Space key in TFM"
    exit 1
fi

# Parse selected files (properly handle quoted filenames)
eval "SELECTED_FILES=($TFM_THIS_SELECTED)"

if [ ${#SELECTED_FILES[@]} -eq 0 ]; then
    echo "Error: No files selected"
    exit 1
fi

echo "Creating archive from ${#SELECTED_FILES[@]} selected files:"
for file in "${SELECTED_FILES[@]}"; do
    if [ -n "$file" ]; then
        echo "  - $file"
    fi
done
echo

# Prompt for archive name
echo -n "Enter archive name (without extension): "
read ARCHIVE_NAME

if [ -z "$ARCHIVE_NAME" ]; then
    echo "Error: Archive name cannot be empty"
    exit 1
fi

# Prompt for archive format
echo
echo "Select archive format:"
echo "1) tar.gz (recommended for cross-platform)"
echo "2) tar.bz2 (better compression)"
echo "3) tar.xz (best compression)"
echo "4) zip (Windows compatible)"
echo "5) tar (uncompressed)"
echo -n "Enter choice (1-5): "
read FORMAT_CHOICE

case $FORMAT_CHOICE in
    1)
        ARCHIVE_EXT=".tar.gz"
        TAR_OPTIONS="czf"
        ;;
    2)
        ARCHIVE_EXT=".tar.bz2"
        TAR_OPTIONS="cjf"
        ;;
    3)
        ARCHIVE_EXT=".tar.xz"
        TAR_OPTIONS="cJf"
        ;;
    4)
        ARCHIVE_EXT=".zip"
        USE_ZIP=true
        ;;
    5)
        ARCHIVE_EXT=".tar"
        TAR_OPTIONS="cf"
        ;;
    *)
        echo "Invalid choice, using tar.gz"
        ARCHIVE_EXT=".tar.gz"
        TAR_OPTIONS="czf"
        ;;
esac

ARCHIVE_PATH="$CURRENT_DIR/${ARCHIVE_NAME}${ARCHIVE_EXT}"

# Check if archive already exists
if [ -f "$ARCHIVE_PATH" ]; then
    echo -n "Archive '$ARCHIVE_NAME$ARCHIVE_EXT' already exists. Overwrite? (y/N): "
    read OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        echo "Archive creation cancelled"
        exit 0
    fi
fi

echo
echo "Creating archive: $ARCHIVE_NAME$ARCHIVE_EXT"

# Change to the directory containing the files
cd "$CURRENT_DIR" || exit 1

# Create the archive
if [ "$USE_ZIP" = true ]; then
    # Use zip for .zip format
    zip -r "$ARCHIVE_PATH" "${SELECTED_FILES[@]}"
    RESULT=$?
else
    # Use tar for all tar formats
    tar $TAR_OPTIONS "$ARCHIVE_PATH" "${SELECTED_FILES[@]}"
    RESULT=$?
fi

if [ $RESULT -eq 0 ]; then
    echo
    echo "Archive created successfully: $ARCHIVE_NAME$ARCHIVE_EXT"
    
    # Show archive size
    if command -v du >/dev/null 2>&1; then
        ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
        echo "Archive size: $ARCHIVE_SIZE"
    fi
    
    # Show archive contents count
    if [ "$USE_ZIP" = true ]; then
        if command -v unzip >/dev/null 2>&1; then
            ITEM_COUNT=$(unzip -l "$ARCHIVE_PATH" 2>/dev/null | tail -1 | awk '{print $2}')
            if [ -n "$ITEM_COUNT" ] && [ "$ITEM_COUNT" != "0" ]; then
                echo "Items in archive: $ITEM_COUNT"
            fi
        fi
    else
        if command -v tar >/dev/null 2>&1; then
            ITEM_COUNT=$(tar -tf "$ARCHIVE_PATH" 2>/dev/null | wc -l)
            if [ -n "$ITEM_COUNT" ] && [ "$ITEM_COUNT" != "0" ]; then
                echo "Items in archive: $ITEM_COUNT"
            fi
        fi
    fi
else
    echo "Error: Failed to create archive"
    exit 1
fi

echo
echo "Press Enter to continue..."
read