#!/usr/bin/env python3
"""
Demo: Shift+Space Selection Feature

This demo shows the Shift+Space key binding for selecting files and moving up.

Key Bindings:
- Space: Select current file and move down (existing feature)
- Shift+Space: Select current file and move up (NEW feature)

Usage:
1. Navigate to a directory with multiple files
2. Press Space to select files moving down
3. Press Shift+Space to select files moving up
4. Press 'q' to quit

The implementation:
- toggle_selection_up() method calls toggle_selection() with direction=-1
- Key handler checks for Shift+Space before regular Space
- Help dialog updated to show the new key binding
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tfm_main import TFMApplication

def main():
    """Run TFM to demonstrate Shift+Space selection."""
    print("Starting TFM with Shift+Space selection feature...")
    print()
    print("Instructions:")
    print("1. Navigate to any directory with files")
    print("2. Press Space to select and move DOWN")
    print("3. Press Shift+Space to select and move UP")
    print("4. Press '?' to see help with all key bindings")
    print("5. Press 'q' to quit")
    print()
    print("Note: Selected files are highlighted")
    print()
    input("Press Enter to start TFM...")
    
    app = TFMApplication()
    app.run()

if __name__ == '__main__':
    main()
