#!/usr/bin/env python3
"""
VSCode Wrapper Script for TFM
Opens VSCode with the focused directory and selected files
Intelligently detects git repositories and opens the repo root instead
"""

import os
import sys
import subprocess
import shutil
import shlex


def find_git_root(directory):
    """Find git repository root starting from the given directory."""
    current_dir = os.path.abspath(directory)
    
    while current_dir != os.path.dirname(current_dir):  # Not at filesystem root
        if os.path.isdir(os.path.join(current_dir, '.git')):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    
    return None


def main():
    """Main function to open VSCode with TFM context."""
    # Check if VSCode is available
    if not shutil.which('code'):
        print("Error: VSCode (code) is not installed or not in PATH")
        print("Please install VSCode and ensure 'code' command is available")
        print("You may need to install the VSCode command line tools:")
        print("  1. Open VSCode")
        print("  2. Press Cmd+Shift+P (macOS) or Ctrl+Shift+P (Linux/Windows)")
        print("  3. Type 'Shell Command: Install 'code' command in PATH'")
        print("  4. Select and run the command")
        sys.exit(1)

    # Get the current directory from TFM environment variables
    # TFM sets TFM_THIS_DIR to the current pane's directory
    current_dir = os.environ.get('TFM_THIS_DIR', os.getcwd())
    selected_files = os.environ.get('TFM_THIS_SELECTED', '')

    # Verify the current directory exists
    try:
        dir_exists = os.path.isdir(current_dir)
    except (OSError, PermissionError) as e:
        print(f"Error accessing current directory: {e}")
        sys.exit(1)
        
    if not dir_exists:
        print(f"Error: Current directory does not exist: {current_dir}")
        sys.exit(1)

    # Check if we're in a git repository
    git_root = find_git_root(current_dir)
    if git_root:
        # Open git repository root
        target_dir = git_root
        print(f"Opening git repository root: {target_dir}")
    else:
        # Open the current directory
        target_dir = current_dir
        print(f"Opening directory: {target_dir}")

    # Build VSCode command
    vscode_args = [target_dir]

    # Add selected files if any
    if selected_files:
        print(f"Opening selected files: {selected_files}")
        
        try:
            # TFM_THIS_SELECTED contains space-separated quoted filenames
            # We need to parse them to remove quotes and handle spaces properly
            selected_array = shlex.split(selected_files)
        except ValueError as e:
            print(f"Error parsing selected files: {e}")
            selected_array = []
        
        for file in selected_array:
            if file:
                # Convert relative paths to absolute paths
                if not os.path.isabs(file):
                    file_path = os.path.join(current_dir, file)
                else:
                    file_path = file
                
                # Only add regular files, skip directories
                try:
                    is_file = os.path.isfile(file_path)
                    is_dir = os.path.isdir(file_path)
                    exists = os.path.exists(file_path)
                except (OSError, PermissionError) as e:
                    print(f"Warning: Cannot access '{file}': {e}")
                    continue
                    
                if is_file:
                    vscode_args.append(file_path)
                elif is_dir:
                    print(f"Skipping directory: '{file}' (only files are opened)")
                else:
                    print(f"Warning: '{file}' does not exist, skipping")

    # Unset TFM environment variables before launching GUI app
    # These variables are not needed for VSCode and can sometimes cause issues
    tfm_vars = [
        'TFM_THIS_DIR', 'TFM_THIS_SELECTED', 'TFM_OTHER_DIR', 'TFM_OTHER_SELECTED',
        'TFM_LEFT_DIR', 'TFM_LEFT_SELECTED', 'TFM_RIGHT_DIR', 'TFM_RIGHT_SELECTED', 'TFM_ACTIVE'
    ]
    
    for var in tfm_vars:
        os.environ.pop(var, None)

    # Execute VSCode
    print(f"Executing: code {' '.join(vscode_args)}")
    
    try:
        subprocess.run(['code'] + vscode_args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error launching VSCode: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: VSCode executable not found")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        sys.exit(1)