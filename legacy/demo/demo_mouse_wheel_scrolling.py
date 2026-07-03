#!/usr/bin/env python3
"""
Demo: Mouse Wheel Scrolling in File Lists

This demo showcases the mouse wheel scrolling functionality in TFM file lists.
Users can scroll through file lists using the mouse wheel in both left and right panes.

Features demonstrated:
- Mouse wheel scrolling in left pane
- Mouse wheel scrolling in right pane
- Smooth scrolling with multiplier for responsive feel
- Boundary checking (won't scroll past top or bottom)
- Works independently of which pane has focus

Usage:
    python demo/demo_mouse_wheel_scrolling.py

Instructions:
    1. Use mouse wheel to scroll through file lists in either pane
    2. Scroll up (positive delta) moves focus up in the list
    3. Scroll down (negative delta) moves focus down in the list
    4. Scrolling is responsive with a 3x multiplier
    5. Click in a pane to switch focus (existing feature)
    6. Press 'q' to quit

Note: This demo requires a backend that supports mouse wheel events
      (CoreGraphics on macOS or compatible terminal emulators).
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tfm_main import main


if __name__ == '__main__':
    print("Starting TFM with mouse wheel scrolling support...")
    print()
    print("Instructions:")
    print("  - Use mouse wheel to scroll through file lists")
    print("  - Scroll up moves focus up, scroll down moves focus down")
    print("  - Works in both left and right panes")
    print("  - Click in a pane to switch focus")
    print("  - Press 'q' to quit")
    print()
    
    # Run TFM normally - mouse wheel support is automatically enabled
    main()
