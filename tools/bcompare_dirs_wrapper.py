#!/usr/bin/env python3
"""
BeyondCompare wrapper script for TFM
This script launches BeyondCompare with the left and right pane directories
"""

import os
import sys
import subprocess
import shutil


def main():
    """Launch BeyondCompare with TFM directory environment variables."""
    # Check if BeyondCompare is available
    if not shutil.which('bcompare'):
        print("Error: BeyondCompare (bcompare) is not installed or not in PATH")
        print("Please install BeyondCompare and ensure 'bcompare' command is available")
        sys.exit(1)

    # Check if TFM environment variables are set
    left_dir = os.environ.get('TFM_LEFT_DIR')
    right_dir = os.environ.get('TFM_RIGHT_DIR')
    
    if not left_dir or not right_dir:
        print("Error: TFM environment variables not set")
        print("This script should be run from within TFM")
        sys.exit(1)

    # Launch BeyondCompare with the directories
    print("Launching BeyondCompare...")
    print(f"Left directory: {left_dir}")
    print(f"Right directory: {right_dir}")

    # Store the directories before unsetting environment variables
    dirs_to_compare = [left_dir, right_dir]

    # Unset TFM environment variables before launching GUI app
    # These variables are not needed for BeyondCompare and can sometimes cause issues
    tfm_vars = [
        'TFM_THIS_DIR', 'TFM_THIS_SELECTED', 'TFM_OTHER_DIR', 'TFM_OTHER_SELECTED',
        'TFM_LEFT_DIR', 'TFM_LEFT_SELECTED', 'TFM_RIGHT_DIR', 'TFM_RIGHT_SELECTED', 'TFM_ACTIVE'
    ]
    
    for var in tfm_vars:
        os.environ.pop(var, None)

    try:
        subprocess.run(['bcompare'] + dirs_to_compare, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error launching BeyondCompare: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: BeyondCompare executable not found")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        sys.exit(1)