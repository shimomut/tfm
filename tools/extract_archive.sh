#!/bin/bash

# extract_archive.sh - Extract archive files using TFM environment variables
# This script uses TFM environment variables for integration

# Check if TFM environment variables are set
if [ -z "$TFM_THIS_DIR" ]; then
    echo "Error: TFM environment variables not set"
    echo "This script should be run from within TFM"
    exit 1
fi

# Get current directory and other pane directory
CURRENT_DIR="$TFM_THIS_DIR"
OTHER_DIR="$TFM_OTHER_DIR"

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

# Function to list archive contents
list_archive_contents() {
    local archive_path="$1"
    local archive_type="$2"
    
    echo "Archive contents:"
    echo "=================="
    
    case $archive_type in
        tar.gz|tgz)
            tar -tzf "$archive_path" | head -20
            ;;
        tar.bz2|tbz2)
            tar -tjf "$archive_path" | head -20
            ;;
        tar.xz|txz)
            tar -tJf "$archive_path" | head -20
            ;;
        tar)
            tar -tf "$archive_path" | head -20
            ;;
        zip)
            unzip -l "$archive_path" | head -25 | tail -n +4
            ;;
        gz)
            echo "$(basename "$archive_path" .gz) (single compressed file)"
            ;;
        bz2)
            echo "$(basename "$archive_path" .bz2) (single compressed file)"
            ;;
        xz)
            echo "$(basename "$archive_path" .xz) (single compressed file)"
            ;;
        *)
            echo "Cannot list contents of unknown archive type"
            return 1
            ;;
    esac
    
    # Show count if it's a multi-file archive
    case $archive_type in
        tar.gz|tgz|tar.bz2|tbz2|tar.xz|txz|tar)
            local count=$(tar -tf "$archive_path" 2>/dev/null | wc -l)
            if [ "$count" -gt 20 ]; then
                echo "... and $((count - 20)) more items"
            fi
            echo "Total items: $count"
            ;;
        zip)
            local count=$(unzip -l "$archive_path" 2>/dev/null | tail -1 | awk '{print $2}')
            if [ -n "$count" ] && [ "$count" != "0" ]; then
                echo "Total items: $count"
            fi
            ;;
    esac
}

# Function to extract archive
extract_archive() {
    local archive_path="$1"
    local dest_dir="$2"
    local archive_type="$3"
    local overwrite="$4"
    
    echo "Extracting to: $dest_dir"
    echo
    
    # Create destination directory if it doesn't exist
    mkdir -p "$dest_dir"
    
    # Change to destination directory
    cd "$dest_dir" || {
        echo "Error: Cannot access destination directory: $dest_dir"
        return 1
    }
    
    case $archive_type in
        tar.gz|tgz)
            if [ "$overwrite" = "yes" ]; then
                tar -xzf "$archive_path"
            else
                tar -xzf "$archive_path" --keep-old-files 2>/dev/null || tar -xzf "$archive_path"
            fi
            ;;
        tar.bz2|tbz2)
            if [ "$overwrite" = "yes" ]; then
                tar -xjf "$archive_path"
            else
                tar -xjf "$archive_path" --keep-old-files 2>/dev/null || tar -xjf "$archive_path"
            fi
            ;;
        tar.xz|txz)
            if [ "$overwrite" = "yes" ]; then
                tar -xJf "$archive_path"
            else
                tar -xJf "$archive_path" --keep-old-files 2>/dev/null || tar -xJf "$archive_path"
            fi
            ;;
        tar)
            if [ "$overwrite" = "yes" ]; then
                tar -xf "$archive_path"
            else
                tar -xf "$archive_path" --keep-old-files 2>/dev/null || tar -xf "$archive_path"
            fi
            ;;
        zip)
            if [ "$overwrite" = "yes" ]; then
                unzip -o "$archive_path"
            else
                unzip -n "$archive_path"
            fi
            ;;
        gz)
            local output_name=$(basename "$archive_path" .gz)
            if [ -f "$output_name" ] && [ "$overwrite" != "yes" ]; then
                echo "File $output_name already exists. Skipping."
                return 1
            fi
            gunzip -c "$archive_path" > "$output_name"
            ;;
        bz2)
            local output_name=$(basename "$archive_path" .bz2)
            if [ -f "$output_name" ] && [ "$overwrite" != "yes" ]; then
                echo "File $output_name already exists. Skipping."
                return 1
            fi
            bunzip2 -c "$archive_path" > "$output_name"
            ;;
        xz)
            local output_name=$(basename "$archive_path" .xz)
            if [ -f "$output_name" ] && [ "$overwrite" != "yes" ]; then
                echo "File $output_name already exists. Skipping."
                return 1
            fi
            unxz -c "$archive_path" > "$output_name"
            ;;
        *)
            echo "Error: Unsupported archive type: $archive_type"
            return 1
            ;;
    esac
}

# Main script logic
if [ -n "$TFM_THIS_SELECTED" ]; then
    # Files are selected, process each selected archive
    eval "SELECTED_FILES=($TFM_THIS_SELECTED)"
    
    for file in "${SELECTED_FILES[@]}"; do
        if [ -n "$file" ]; then
            ARCHIVE_PATH="$CURRENT_DIR/$file"
            
            if [ ! -f "$ARCHIVE_PATH" ]; then
                echo "Warning: File not found: $file"
                continue
            fi
            
            ARCHIVE_TYPE=$(detect_archive_type "$ARCHIVE_PATH")
            
            if [ "$ARCHIVE_TYPE" = "unknown" ]; then
                echo "Warning: Unknown archive type for file: $file"
                continue
            fi
            
            echo "Processing archive: $file"
            echo "Archive type: $ARCHIVE_TYPE"
            echo
            
            # List contents first
            list_archive_contents "$ARCHIVE_PATH" "$ARCHIVE_TYPE"
            echo
            
            # Ask where to extract
            echo "Extract options:"
            echo "1) Extract to current directory ($CURRENT_DIR)"
            echo "2) Extract to other pane directory ($OTHER_DIR)"
            echo "3) Extract to new subdirectory"
            echo "4) Skip this archive"
            echo -n "Choose option (1-4): "
            read EXTRACT_CHOICE
            
            case $EXTRACT_CHOICE in
                1)
                    DEST_DIR="$CURRENT_DIR"
                    ;;
                2)
                    DEST_DIR="$OTHER_DIR"
                    ;;
                3)
                    echo -n "Enter subdirectory name: "
                    read SUBDIR_NAME
                    if [ -z "$SUBDIR_NAME" ]; then
                        echo "Invalid subdirectory name. Skipping."
                        continue
                    fi
                    DEST_DIR="$CURRENT_DIR/$SUBDIR_NAME"
                    ;;
                4)
                    echo "Skipping $file"
                    continue
                    ;;
                *)
                    echo "Invalid choice. Skipping $file"
                    continue
                    ;;
            esac
            
            # Ask about overwriting
            echo -n "Overwrite existing files? (y/N): "
            read OVERWRITE_CHOICE
            if [[ "$OVERWRITE_CHOICE" =~ ^[Yy]$ ]]; then
                OVERWRITE="yes"
            else
                OVERWRITE="no"
            fi
            
            echo
            extract_archive "$ARCHIVE_PATH" "$DEST_DIR" "$ARCHIVE_TYPE" "$OVERWRITE"
            RESULT=$?
            
            if [ $RESULT -eq 0 ]; then
                echo "Successfully extracted: $file"
            else
                echo "Failed to extract: $file"
            fi
            echo
        fi
    done
else
    echo "No files selected."
    echo "Please select archive files to extract using Space key in TFM"
    exit 1
fi

echo "Extraction process completed."
echo
echo "Press Enter to continue..."
read