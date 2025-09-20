#!/usr/bin/env python3
"""
TFM Color Scheme Information Tool

This script displays information about TFM's color schemes without starting the full application.
Useful for checking color scheme definitions and testing color support.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

try:
    from tfm_colors import (
        print_current_color_scheme,
        print_all_color_schemes,
        get_available_color_schemes,
        get_current_color_scheme,
        set_color_scheme,
        toggle_color_scheme
    )
except ImportError as e:
    print(f"Error importing TFM color modules: {e}")
    print("Make sure you're running this from the TFM directory.")
    sys.exit(1)

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'current':
            print_current_color_scheme()
        elif command == 'all':
            print_all_color_schemes()
        elif command == 'list':
            schemes = get_available_color_schemes()
            current = get_current_color_scheme()
            print("Available color schemes:")
            for scheme in schemes:
                marker = " (current)" if scheme == current else ""
                print(f"  - {scheme}{marker}")
        elif command == 'toggle':
            old_scheme = get_current_color_scheme()
            new_scheme = toggle_color_scheme()
            print(f"Toggled from {old_scheme} to {new_scheme}")
            print_current_color_scheme()
        elif command in get_available_color_schemes():
            set_color_scheme(command)
            print(f"Set color scheme to: {command}")
            print_current_color_scheme()
        else:
            print(f"Unknown command: {command}")
            show_usage()
    else:
        # Default: show all information
        print("TFM Color Scheme Information")
        print("=" * 50)
        print_all_color_schemes()

def show_usage():
    print("\nUsage:")
    print("  python3 show_color_schemes.py [command]")
    print("\nCommands:")
    print("  current  - Show current color scheme")
    print("  all      - Show all color schemes (default)")
    print("  list     - List available schemes")
    print("  toggle   - Toggle between dark/light")
    print("  dark     - Set to dark scheme")
    print("  light    - Set to light scheme")
    print("\nExamples:")
    print("  python3 show_color_schemes.py")
    print("  python3 show_color_schemes.py current")
    print("  python3 show_color_schemes.py light")

if __name__ == "__main__":
    main()