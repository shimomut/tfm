#!/usr/bin/env python3
"""
Preview Files Script for TFM
Opens selected files with the system's default preview application

Features:
- Cross-platform support (macOS, Windows, Linux)
- Supports image files: jpg, jpeg, png, gif, bmp, tiff, tif, webp, heic, heif, pdf, svg
- Handles multiple file selection
- Validates file types and existence
- Provides informative error messages

Usage:
This script is designed to be called from TFM's external programs menu.
It uses TFM environment variables:
- TFM_THIS_DIR: Current directory
- TFM_THIS_SELECTED: Space-separated quoted list of selected files
"""

import os
import sys
import platform
import subprocess
import shlex
import mimetypes


def get_supported_extensions():
    """Get list of supported file extensions."""
    return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'heic', 'heif', 'pdf', 'svg']


def is_supported_extension(file_path):
    """Check if a file extension is supported."""
    supported_extensions = get_supported_extensions()
    extension = os.path.splitext(file_path)[1].lower().lstrip('.')
    return extension in supported_extensions


def is_image_file(file_path):
    """Check if a file is an image using extension and MIME type detection."""
    # First check by extension
    if is_supported_extension(file_path):
        return True
    
    # Fallback: use mimetypes to detect image files
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type.startswith('image/') or mime_type == 'application/pdf'
    
    return False


def open_files_cross_platform(file_paths):
    """Open files with the system's default application."""
    system = platform.system()
    
    try:
        if system == 'Darwin':  # macOS
            # Check if Preview.app is available
            preview_paths = ['/System/Applications/Preview.app', '/Applications/Preview.app']
            preview_available = any(os.path.exists(path) for path in preview_paths)
            
            if preview_available:
                subprocess.run(['open', '-a', 'Preview'] + file_paths, check=True)
            else:
                # Fallback to default application
                for file_path in file_paths:
                    subprocess.run(['open', file_path], check=True)
                    
        elif system == 'Windows':
            # Windows
            for file_path in file_paths:
                subprocess.run(['start', '', file_path], shell=True, check=True)
                
        elif system == 'Linux':
            # Linux
            for file_path in file_paths:
                subprocess.run(['xdg-open', file_path], check=True)
                
        else:
            print(f"Error: Unsupported operating system: {system}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error opening files: {e}")
        return False
    except FileNotFoundError:
        print("Error: Required system command not found")
        return False
        
    return True


def main():
    """Main function to preview selected files."""
    # Get the current directory and selected files from TFM environment variables
    current_dir = os.environ.get('TFM_THIS_DIR', os.getcwd())
    selected_files = os.environ.get('TFM_THIS_SELECTED', '')

    # Verify the current directory exists
    if not os.path.isdir(current_dir):
        print(f"Error: Current directory does not exist: {current_dir}")
        sys.exit(1)

    # Check if any files are selected
    if not selected_files:
        print("Error: No files selected")
        print("Please select one or more files to preview")
        sys.exit(1)

    # Parse selected files and build list of valid files to preview
    preview_files = []
    skipped_files = []

    try:
        # TFM_THIS_SELECTED contains space-separated quoted filenames
        selected_array = shlex.split(selected_files)
    except ValueError as e:
        print(f"Error parsing selected files: {e}")
        sys.exit(1)

    for file in selected_array:
        if file:
            # Convert relative paths to absolute paths
            if not os.path.isabs(file):
                file_path = os.path.join(current_dir, file)
            else:
                file_path = file
            
            # Check if file exists and is a regular file
            try:
                is_file = os.path.isfile(file_path)
                is_dir = os.path.isdir(file_path)
            except (OSError, PermissionError) as e:
                print(f"Error accessing file: {os.path.basename(file_path)} - {e}")
                skipped_files.append(file_path)
                continue
                
            if is_file:
                if is_image_file(file_path):
                    preview_files.append(file_path)
                    print(f"Adding to preview: {os.path.basename(file_path)}")
                else:
                    skipped_files.append(file_path)
                    print(f"Skipping unsupported file type: {os.path.basename(file_path)}")
            elif is_dir:
                skipped_files.append(file_path)
                print(f"Skipping directory: {os.path.basename(file_path)}")
            else:
                skipped_files.append(file_path)
                print(f"Warning: File does not exist: {os.path.basename(file_path)}")

    # Report skipped files
    if skipped_files:
        print()
        print(f"Skipped {len(skipped_files)} file(s):")
        supported_extensions = get_supported_extensions()
        print(f"Currently supported file types: {', '.join(supported_extensions)}")

    # Check if we have any files to preview
    if not preview_files:
        print()
        print("Error: No supported files found to preview")
        supported_extensions = get_supported_extensions()
        print(f"Supported file types: {', '.join(supported_extensions)}")
        sys.exit(1)

    # Open files with system's default preview application
    print()
    print(f"Opening {len(preview_files)} file(s) with system preview application...")

    if not open_files_cross_platform(preview_files):
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        sys.exit(1)