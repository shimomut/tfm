"""
Visual verification of CoreGraphics TTKView drawRect_ rendering.

This script creates a window and displays various characters with different
attributes and colors to visually verify that the rendering works correctly.
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Check if we're on macOS and PyObjC is available
try:
    import Cocoa
    import objc
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False
    print("PyObjC not available - skipping CoreGraphics verification")
    sys.exit(0)

from backends.coregraphics_backend import CoreGraphicsBackend
from renderer import TextAttribute


def main():
    """Create a window and display test content."""
    print("=" * 60)
    print("CoreGraphics TTKView drawRect_ Visual Verification")
    print("=" * 60)
    print()
    print("Creating window with test content...")
    print("The window should display:")
    print("  - Row 0: Various text attributes (bold, underline, reverse)")
    print("  - Row 2: Different color pairs")
    print("  - Row 4: Combined attributes")
    print("  - Row 6: Coordinate transformation test (corners)")
    print()
    print("Close the window to exit.")
    print()
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="CoreGraphics drawRect_ Verification",
        font_name="Menlo",
        font_size=14,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize some color pairs
    backend.color_pairs[1] = ((255, 0, 0), (0, 0, 0))      # Red on black
    backend.color_pairs[2] = ((0, 255, 0), (0, 0, 0))      # Green on black
    backend.color_pairs[3] = ((0, 0, 255), (0, 0, 0))      # Blue on black
    backend.color_pairs[4] = ((255, 255, 0), (0, 0, 0))    # Yellow on black
    backend.color_pairs[5] = ((255, 0, 255), (0, 0, 0))    # Magenta on black
    backend.color_pairs[6] = ((0, 255, 255), (0, 0, 0))    # Cyan on black
    backend.color_pairs[7] = ((255, 255, 255), (128, 0, 0))  # White on dark red
    
    # Row 0: Text attributes
    text = "Normal "
    for i, char in enumerate(text):
        backend.grid[0][i] = (char, 0, 0)
    
    text = "Bold "
    for i, char in enumerate(text):
        backend.grid[0][7 + i] = (char, 0, TextAttribute.BOLD)
    
    text = "Underline "
    for i, char in enumerate(text):
        backend.grid[0][12 + i] = (char, 0, TextAttribute.UNDERLINE)
    
    text = "Reverse"
    for i, char in enumerate(text):
        backend.grid[0][22 + i] = (char, 0, TextAttribute.REVERSE)
    
    # Row 2: Color pairs
    text = "Red Green Blue Yellow Magenta Cyan"
    colors = [1, 1, 1, 0, 2, 2, 2, 2, 2, 0, 3, 3, 3, 3, 0, 4, 4, 4, 4, 4, 4, 0, 5, 5, 5, 5, 5, 5, 5, 0, 6, 6, 6, 6]
    for i, (char, color) in enumerate(zip(text, colors)):
        backend.grid[2][i] = (char, color, 0)
    
    # Row 4: Combined attributes
    text = "Bold+Underline"
    for i, char in enumerate(text):
        backend.grid[4][i] = (char, 0, TextAttribute.BOLD | TextAttribute.UNDERLINE)
    
    text = " Bold+Reverse"
    for i, char in enumerate(text):
        backend.grid[4][14 + i] = (char, 0, TextAttribute.BOLD | TextAttribute.REVERSE)
    
    # Row 6: Coordinate transformation test
    backend.grid[0][0] = ('┌', 0, 0)  # Top-left corner
    backend.grid[0][79] = ('┐', 0, 0)  # Top-right corner
    backend.grid[23][0] = ('└', 0, 0)  # Bottom-left corner
    backend.grid[23][79] = ('┘', 0, 0)  # Bottom-right corner
    
    # Row 8: Background colors
    text = "Background Colors"
    for i, char in enumerate(text):
        backend.grid[8][i] = (char, 7, 0)
    
    # Trigger a refresh to display the content
    backend.view.setNeedsDisplay_(True)
    
    # Run the application event loop
    # This will keep the window open until the user closes it
    try:
        Cocoa.NSApp.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    # Cleanup
    backend.shutdown()
    
    print("Verification complete.")


if __name__ == '__main__':
    main()
