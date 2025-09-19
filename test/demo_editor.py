#!/usr/bin/env python3
"""
Demo script to show the text editor functionality in TFM
"""

import os
import sys
from pathlib import Path

def main():
    print("TFM Text Editor Feature Demo")
    print("=" * 40)
    print()
    print("The text editor feature has been successfully added to TFM!")
    print()
    print("Key Features:")
    print("• Press 'e' or 'E' to edit the selected file")
    print("• Curses interface is suspended during editing")
    print("• Default editor is 'vim' (configurable)")
    print("• Works with any text editor that accepts file arguments")
    print()
    print("Configuration:")
    print("• Edit ~/.tfm/config.py to change the TEXT_EDITOR setting")
    print("• Example: TEXT_EDITOR = 'nano'  # or 'emacs', 'code', etc.")
    print()
    print("Usage in TFM:")
    print("1. Navigate to a file using arrow keys")
    print("2. Press 'e' or 'E' to edit the file")
    print("3. Your configured editor will open")
    print("4. Save and exit the editor to return to TFM")
    print()
    print("The implementation includes:")
    print("• Proper curses suspension/resumption")
    print("• Error handling for missing editors")
    print("• Support for editing any file type")
    print("• Configurable editor command")
    print()
    
    # Check if vim is available
    import subprocess
    try:
        result = subprocess.run(['which', 'vim'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ vim is available on your system")
        else:
            print("⚠ vim not found - you may want to configure a different editor")
    except:
        print("⚠ Could not check for vim availability")
    
    print()
    print("To test the feature:")
    print(f"1. Run: python3 tfm_main.py")
    print(f"2. Navigate to 'test_edit.txt'")
    print(f"3. Press 'e' to edit the file")

if __name__ == "__main__":
    main()