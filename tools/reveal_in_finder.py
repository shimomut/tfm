#!/usr/bin/env python3
"""
Reveal in File Manager Script for TFM
Opens the system file manager and selects the current file/directory

Cross-platform support:
- macOS: Opens Finder and selects the file/directory
- Windows: Opens Explorer and selects the file/directory  
- Linux: Opens the default file manager

This script uses TFM environment variables to get the current selection
"""

import os
import sys
import platform
import subprocess
import shlex


def reveal_in_file_manager(target_path):
    """Reveal a file or directory in the system file manager."""
    system = platform.system()
    
    try:
        if system == 'Darwin':  # macOS
            if os.path.isfile(target_path):
                # Reveal file in Finder
                subprocess.run(['open', '-R', target_path], check=True)
            else:
                # Open directory in Finder
                subprocess.run(['open', target_path], check=True)
                
        elif system == 'Windows':
            if os.path.isfile(target_path):
                # Select file in Explorer
                subprocess.run(['explorer', '/select,', target_path], check=True)
            else:
                # Open directory in Explorer
                subprocess.run(['explorer', target_path], check=True)
                
        elif system == 'Linux':
            # Try different file managers commonly available on Linux
            file_managers = ['nautilus', 'dolphin', 'thunar', 'pcmanfm', 'nemo']
            
            for fm in file_managers:
                if subprocess.run(['which', fm], capture_output=True).returncode == 0:
                    if os.path.isfile(target_path):
                        # Some file managers support selecting files
                        if fm in ['nautilus', 'nemo']:
                            subprocess.run([fm, '--select', target_path], check=True)
                        else:
                            # Fallback: open parent directory
                            parent_dir = os.path.dirname(target_path)
                            subprocess.run([fm, parent_dir], check=True)
                    else:
                        # Open directory
                        subprocess.run([fm, target_path], check=True)
                    return True
            
            # Fallback: use xdg-open
            if os.path.isfile(target_path):
                parent_dir = os.path.dirname(target_path)
                subprocess.run(['xdg-open', parent_dir], check=True)
            else:
                subprocess.run(['xdg-open', target_path], check=True)
                
        else:
            print(f"Error: Unsupported operating system: {system}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error opening file manager: {e}")
        return False
    except FileNotFoundError:
        print("Error: Required system command not found")
        return False
        
    return True


def main():
    """Main function to reveal files in the system file manager."""
    # Check if TFM environment variables are set
    current_dir = os.environ.get('TFM_THIS_DIR')
    
    if not current_dir:
        print("Error: TFM environment variables not set")
        print("This script should be run from within TFM")
        sys.exit(1)

    selected_files = os.environ.get('TFM_THIS_SELECTED', '')

    # Check if there are selected files
    if selected_files:
        try:
            # Parse selected files (properly handle quoted filenames)
            selected_array = shlex.split(selected_files)
        except ValueError as e:
            print(f"Error parsing selected files: {e}")
            sys.exit(1)
        
        # Get the first selected file
        if selected_array and selected_array[0]:
            selected_file = selected_array[0]
            
            # Build full path to the selected file
            target_path = os.path.join(current_dir, selected_file)
            
            # Check if the target exists
            try:
                target_exists = os.path.exists(target_path)
            except (OSError, PermissionError) as e:
                print(f"Error accessing target path: {e}")
                sys.exit(1)
                
            if target_exists:
                system_name = platform.system()
                file_manager_name = {
                    'Darwin': 'Finder',
                    'Windows': 'Explorer', 
                    'Linux': 'file manager'
                }.get(system_name, 'file manager')
                
                print(f"Revealing selected file in {file_manager_name}: {selected_file}")
                
                if not reveal_in_file_manager(target_path):
                    sys.exit(1)
            else:
                print(f"Error: Selected file does not exist: {target_path}")
                sys.exit(1)
        else:
            print("Error: No valid file selected")
            sys.exit(1)
    else:
        # No files selected, reveal the current directory
        try:
            is_directory = os.path.isdir(current_dir)
        except (OSError, PermissionError) as e:
            print(f"Error accessing current directory: {e}")
            sys.exit(1)
            
        if is_directory:
            system_name = platform.system()
            file_manager_name = {
                'Darwin': 'Finder',
                'Windows': 'Explorer',
                'Linux': 'file manager'
            }.get(system_name, 'file manager')
            
            print(f"Revealing current directory in {file_manager_name}: {current_dir}")
            
            if not reveal_in_file_manager(current_dir):
                sys.exit(1)
        else:
            print(f"Error: Current directory does not exist: {current_dir}")
            sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        sys.exit(1)