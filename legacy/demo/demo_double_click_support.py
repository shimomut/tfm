#!/usr/bin/env python3
"""
Demo: Double-Click Support

This demo showcases the double-click functionality in TFM:
- Double-click files/directories in file lists to open them (same as Enter key)
- Double-click directories in directory diff viewer to expand/collapse
- Double-click files in directory diff viewer to open diff viewer

Instructions:
1. The demo will launch TFM in the current directory
2. Try double-clicking on files and directories in the file lists
3. Press Ctrl+D to open directory diff viewer
4. Try double-clicking on items in the diff viewer
5. Press 'q' to quit

Note: This demo requires a mouse-enabled terminal (most modern terminals support this)
"""

import sys
import os

# Add parent directory to path to import tfm modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tfm import main

if __name__ == '__main__':
    print(__doc__)
    print("\nStarting TFM with double-click support...")
    print("Press any key to continue...")
    input()
    
    # Launch TFM normally - double-click support is built-in
    main()
