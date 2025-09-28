#!/bin/bash
#
# VSCode Wrapper Script for TFM
# Opens VSCode with the focused directory and selected files
# Intelligently detects git repositories and opens the repo root instead
#

# Check if VSCode is available
if ! command -v code &> /dev/null; then
    echo "Error: VSCode (code) is not installed or not in PATH"
    echo "Please install VSCode and ensure 'code' command is available"
    echo "You may need to install the VSCode command line tools:"
    echo "  1. Open VSCode"
    echo "  2. Press Cmd+Shift+P (macOS) or Ctrl+Shift+P (Linux/Windows)"
    echo "  3. Type 'Shell Command: Install 'code' command in PATH'"
    echo "  4. Select and run the command"
    exit 1
fi

# Function to find git repository root
find_git_root() {
    local dir="$1"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.git" ]]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    return 1
}

# Get the current directory from TFM environment variables
# TFM sets TFM_THIS_DIR to the current pane's directory
CURRENT_DIR="${TFM_THIS_DIR:-$(pwd)}"
SELECTED_FILES="${TFM_THIS_SELECTED:-}"

# Verify the current directory exists
if [[ ! -d "$CURRENT_DIR" ]]; then
    echo "Error: Current directory does not exist: $CURRENT_DIR"
    exit 1
fi

# Check if we're in a git repository
GIT_ROOT=$(find_git_root "$CURRENT_DIR")
if [[ $? -eq 0 ]]; then
    # Open git repository root
    TARGET_DIR="$GIT_ROOT"
    echo "Opening git repository root: $TARGET_DIR"
else
    # Open the current directory
    TARGET_DIR="$CURRENT_DIR"
    echo "Opening directory: $TARGET_DIR"
fi

# Build VSCode command
VSCODE_CMD="code"
VSCODE_ARGS=("$TARGET_DIR")

# Add selected files if any
if [[ -n "$SELECTED_FILES" ]]; then
    echo "Opening selected files: $SELECTED_FILES"
    # TFM_THIS_SELECTED contains space-separated quoted filenames
    # We need to evaluate them to remove quotes and handle spaces properly
    eval "selected_array=($SELECTED_FILES)"
    
    for file in "${selected_array[@]}"; do
        if [[ -n "$file" ]]; then
            # Convert relative paths to absolute paths
            if [[ ! "$file" = /* ]]; then
                file="$CURRENT_DIR/$file"
            fi
            
            # Only add regular files, skip directories
            if [[ -f "$file" ]]; then
                VSCODE_ARGS+=("$file")
            elif [[ -d "$file" ]]; then
                echo "Skipping directory: '$file' (only files are opened)"
            else
                echo "Warning: '$file' does not exist, skipping"
            fi
        fi
    done
fi

# Unset TFM environment variables before launching GUI app
# These variables are not needed for VSCode and can sometimes cause issues
unset TFM_THIS_DIR TFM_THIS_SELECTED TFM_OTHER_DIR TFM_OTHER_SELECTED TFM_LEFT_DIR TFM_LEFT_SELECTED TFM_RIGHT_DIR TFM_RIGHT_SELECTED TFM_ACTIVE

# Execute VSCode
echo "Executing: $VSCODE_CMD ${VSCODE_ARGS[*]}"
exec "$VSCODE_CMD" ${VSCODE_ARGS[*]}