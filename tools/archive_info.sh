#!/bin/bash

# archive_info.sh - Display detailed information about archive files
# This script uses TFM environment variables for integration

# Check if TFM environment variables are set
if [ -z "$TFM_THIS_DIR" ]; then
    echo "Error: TFM environment variables not set"
    echo "This script should be run from within TFM"
    exit 1
fi

# Get current directory
CURRENT_DIR="$TFM_THIS_DIR"

# Function to detect archive type
detect_archive_type() {
    local file="$1"
    local filename=$(basename "$file")
    local lowercase_name=$(echo "$filename" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lowercase_name" == *.tar.gz || "$lowercase_name" == *.tgz ]]; then
        echo "tar.gz"
    elif [[ "$lowercase_name" == *.tar.bz2 || "$lowercase_name" == *.tbz2 ]]; then
        echo "tar.bz2"
    elif [[ "$lowercase_name" == *.tar.xz || "$lowercase_name" == *.txz ]]; then
        echo "tar.xz"
    elif [[ "$lowercase_name" == *.tar ]]; then
        echo "tar"
    elif [[ "$lowercase_name" == *.zip ]]; then
        echo "zip"
    elif [[ "$lowercase_name" == *.gz ]]; then
        echo "gz"
    elif [[ "$lowercase_name" == *.bz2 ]]; then
        echo "bz2"
    elif [[ "$lowercase_name" == *.xz ]]; then
        echo "xz"
    else
        echo "unknown"
    fi
}

# Function to get archive info
get_archive_info() {
    local archive_path="$1"
    local archive_type="$2"
    local filename=$(basename "$archive_path")
    
    echo "Archive Information"
    echo "==================="
    echo "File: $filename"
    echo "Type: $archive_type"
    echo "Path: $archive_path"
    
    # Get file size
    if [ -f "$archive_path" ]; then
        local size_bytes=$(stat -f%z "$archive_path" 2>/dev/null || stat -c%s "$archive_path" 2>/dev/null)
        if [ -n "$size_bytes" ]; then
            local size_human=$(du -h "$archive_path" | cut -f1)
            echo "Size: $size_human ($size_bytes bytes)"
        fi
        
        # Get modification time
        local mod_time=$(stat -f%Sm "$archive_path" 2>/dev/null || stat -c%y "$archive_path" 2>/dev/null)
        if [ -n "$mod_time" ]; then
            echo "Modified: $mod_time"
        fi
    fi
    
    echo
    
    # Get archive-specific information
    case $archive_type in
        tar.gz|tgz)
            echo "Archive Contents (tar.gz):"
            echo "=========================="
            local file_count=$(tar -tzf "$archive_path" 2>/dev/null | wc -l)
            local dir_count=$(tar -tzf "$archive_path" 2>/dev/null | grep '/$' | wc -l)
            echo "Total items: $file_count"
            echo "Directories: $dir_count"
            echo "Files: $((file_count - dir_count))"
            echo
            echo "Contents preview:"
            tar -tzf "$archive_path" 2>/dev/null | head -20
            if [ "$file_count" -gt 20 ]; then
                echo "... and $((file_count - 20)) more items"
            fi
            ;;
        tar.bz2|tbz2)
            echo "Archive Contents (tar.bz2):"
            echo "==========================="
            local file_count=$(tar -tjf "$archive_path" 2>/dev/null | wc -l)
            local dir_count=$(tar -tjf "$archive_path" 2>/dev/null | grep '/$' | wc -l)
            echo "Total items: $file_count"
            echo "Directories: $dir_count"
            echo "Files: $((file_count - dir_count))"
            echo
            echo "Contents preview:"
            tar -tjf "$archive_path" 2>/dev/null | head -20
            if [ "$file_count" -gt 20 ]; then
                echo "... and $((file_count - 20)) more items"
            fi
            ;;
        tar.xz|txz)
            echo "Archive Contents (tar.xz):"
            echo "=========================="
            local file_count=$(tar -tJf "$archive_path" 2>/dev/null | wc -l)
            local dir_count=$(tar -tJf "$archive_path" 2>/dev/null | grep '/$' | wc -l)
            echo "Total items: $file_count"
            echo "Directories: $dir_count"
            echo "Files: $((file_count - dir_count))"
            echo
            echo "Contents preview:"
            tar -tJf "$archive_path" 2>/dev/null | head -20
            if [ "$file_count" -gt 20 ]; then
                echo "... and $((file_count - 20)) more items"
            fi
            ;;
        tar)
            echo "Archive Contents (tar):"
            echo "======================"
            local file_count=$(tar -tf "$archive_path" 2>/dev/null | wc -l)
            local dir_count=$(tar -tf "$archive_path" 2>/dev/null | grep '/$' | wc -l)
            echo "Total items: $file_count"
            echo "Directories: $dir_count"
            echo "Files: $((file_count - dir_count))"
            echo
            echo "Contents preview:"
            tar -tf "$archive_path" 2>/dev/null | head -20
            if [ "$file_count" -gt 20 ]; then
                echo "... and $((file_count - 20)) more items"
            fi
            ;;
        zip)
            echo "Archive Contents (zip):"
            echo "======================"
            if command -v unzip >/dev/null 2>&1; then
                unzip -l "$archive_path" 2>/dev/null | head -25
                echo
                local info_line=$(unzip -l "$archive_path" 2>/dev/null | tail -1)
                echo "Summary: $info_line"
            else
                echo "unzip command not available"
            fi
            ;;
        gz)
            echo "Compressed File (gzip):"
            echo "======================"
            local original_name=$(basename "$archive_path" .gz)
            echo "Original filename: $original_name"
            echo "Compression: gzip"
            if command -v gzip >/dev/null 2>&1; then
                local compressed_size=$(stat -f%z "$archive_path" 2>/dev/null || stat -c%s "$archive_path" 2>/dev/null)
                echo "Compressed size: $(du -h "$archive_path" | cut -f1)"
                # Try to get uncompressed size
                local uncompressed_size=$(gzip -l "$archive_path" 2>/dev/null | tail -1 | awk '{print $2}')
                if [ -n "$uncompressed_size" ] && [ "$uncompressed_size" != "uncompressed" ]; then
                    local ratio=$(gzip -l "$archive_path" 2>/dev/null | tail -1 | awk '{print $3}')
                    echo "Uncompressed size: $uncompressed_size bytes"
                    echo "Compression ratio: $ratio%"
                fi
            fi
            ;;
        bz2)
            echo "Compressed File (bzip2):"
            echo "======================="
            local original_name=$(basename "$archive_path" .bz2)
            echo "Original filename: $original_name"
            echo "Compression: bzip2"
            ;;
        xz)
            echo "Compressed File (xz):"
            echo "===================="
            local original_name=$(basename "$archive_path" .xz)
            echo "Original filename: $original_name"
            echo "Compression: xz"
            if command -v xz >/dev/null 2>&1; then
                xz -l "$archive_path" 2>/dev/null
            fi
            ;;
        *)
            echo "Unknown or unsupported archive type"
            echo "File may not be a valid archive"
            ;;
    esac
}

# Main script logic
if [ -n "$TFM_THIS_SELECTED" ]; then
    # Files are selected, show info for each selected archive
    eval "SELECTED_FILES=($TFM_THIS_SELECTED)"
    
    for file in "${SELECTED_FILES[@]}"; do
        if [ -n "$file" ]; then
            ARCHIVE_PATH="$CURRENT_DIR/$file"
            
            if [ ! -f "$ARCHIVE_PATH" ]; then
                echo "Warning: File not found: $file"
                echo
                continue
            fi
            
            ARCHIVE_TYPE=$(detect_archive_type "$ARCHIVE_PATH")
            
            get_archive_info "$ARCHIVE_PATH" "$ARCHIVE_TYPE"
            echo
            echo "----------------------------------------"
            echo
        fi
    done
else
    # No files selected, check if cursor is on an archive
    echo "No files selected."
    echo "Please select archive files to view information using Space key in TFM"
    exit 1
fi

echo "Press Enter to continue..."
read