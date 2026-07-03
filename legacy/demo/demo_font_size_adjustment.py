#!/usr/bin/env python3
"""
Demo: Dynamic Font Size Adjustment in Desktop Mode

This demo demonstrates the dynamic font size adjustment feature in TFM's
desktop mode using Cmd-Plus and Cmd-Minus keyboard shortcuts.

Features demonstrated:
- Cmd-Plus (or Cmd-=): Increase font size
- Cmd-Minus: Decrease font size
- Font size limits (8-72 points)
- Window resizing to maintain grid dimensions
- Real-time font rendering updates

Requirements:
    - macOS (CoreGraphics backend)
    - Desktop mode enabled
    - PyObjC framework installed

Usage:
    python3 demo/demo_font_size_adjustment.py

Expected behavior:
- Window opens in desktop mode with default font size
- Press Cmd-Plus to increase font size (window stays same size, fewer rows/cols)
- Press Cmd-Minus to decrease font size (window stays same size, more rows/cols)
- Font size changes are logged in the log pane
- Minimum font size is 8pt, maximum is 72pt
- Grid dimensions adjust to fit more/fewer characters
- Character rendering updates immediately
- Works in all contexts (main screen, dialogs, text viewer, etc.)

Testing steps:
1. Launch the demo
2. Press Cmd-Plus several times to increase font size
3. Observe text becoming larger, fewer files visible
4. Press Cmd-Minus several times to decrease font size
5. Observe text becoming smaller, more files visible
6. Try in different contexts:
   - Main file manager screen
   - Help dialog (press ?)
   - Text viewer (view a file)
   - Search dialog (press F)
7. Verify shortcuts work everywhere
8. Try to go below 8pt or above 72pt (should be prevented)
9. Verify log messages show current font size
10. Press 'q' to quit

Note: This feature is only available in desktop mode (CoreGraphics backend).
In terminal mode (curses backend), these shortcuts have no effect.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Run the font size adjustment demo."""
    print("=" * 70)
    print("Font Size Adjustment Demo")
    print("=" * 70)
    print()
    print("This demo demonstrates dynamic font size adjustment in desktop mode.")
    print()
    print("Features:")
    print("  • Cmd-Plus (or Cmd-=): Increase font size")
    print("  • Cmd-Minus: Decrease font size")
    print("  • Font size range: 8-72 points")
    print("  • Window resizes to maintain grid dimensions")
    print("  • Real-time rendering updates")
    print()
    print("Instructions:")
    print("  1. Press Cmd-Plus to increase font size")
    print("  2. Press Cmd-Minus to decrease font size")
    print("  3. Watch the log pane for font size updates")
    print("  4. Try to exceed limits (8pt min, 72pt max)")
    print("  5. Try in different contexts (main screen, dialogs, viewer)")
    print("  6. Press 'q' to quit")
    print()
    print("Starting TFM in desktop mode...")
    print()
    
    # Import TFM main
    from tfm_main import main as tfm_main
    
    # Run TFM (will use Desktop mode if available)
    sys.exit(tfm_main())

if __name__ == '__main__':
    main()
