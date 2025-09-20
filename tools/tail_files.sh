#!/bin/bash

# tail_files.sh - Print last 10 lines of selected files
# Reads selected files from TFM_THIS_SELECTED environment variable
# Files are separated by whitespace, with quoted filenames for names containing spaces

if [ -z "$TFM_THIS_SELECTED" ]; then
    echo "Error: No files selected (TFM_THIS_SELECTED environment variable is empty)"
    echo "Please select one or more files in TFM before running this command"
    exit 1
fi

# Parse the whitespace-separated list, handling quoted filenames
eval "files=($TFM_THIS_SELECTED)"

# Check if any files were parsed
if [ ${#files[@]} -eq 0 ]; then
    echo "Error: No valid files found in selection"
    exit 1
fi

# Process each file
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "=== Last 10 lines of: $file ==="
        tail -n 10 "$file"
        echo
    else
        echo "Warning: '$file' is not a regular file or does not exist"
        echo
    fi
done