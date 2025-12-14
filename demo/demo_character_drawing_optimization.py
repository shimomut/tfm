#!/usr/bin/env python3
"""
Demo script to visualize the character drawing performance bottleneck.

This demo creates a live TFM instance with a grid filled with non-space characters
to demonstrate the 0.03 seconds character drawing performance issue in the
CoreGraphics backend.

The demo will:
1. Launch TFM with the CoreGraphics backend
2. Fill the screen with colorful text using various attributes
3. Display timing information showing the t4-t3 (character drawing) phase
4. Allow you to see the performance impact in real-time

Usage:
    python demo/demo_character_drawing_optimization.py

Expected output:
    - You should see timing output in the console showing t4-t3 ≈ 0.03 seconds
    - The screen will be filled with colorful characters
    - Each redraw will show the performance metrics
"""

import sys
import time
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

# Add ttk directory to path
ttk_path = Path(__file__).parent.parent / 'ttk'
sys.path.insert(0, str(ttk_path))

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    from ttk.text_attribute import TextAttribute
    import Cocoa
    COREGRAPHICS_AVAILABLE = True
except ImportError:
    COREGRAPHICS_AVAILABLE = False


def create_performance_test_content(backend):
    """
    Fill the backend grid with content that maximizes character drawing workload.
    
    This creates a worst-case scenario for character drawing performance by:
    - Using all non-space characters (every character must be drawn)
    - Using multiple color pairs
    - Applying various text attributes (bold, underline, reverse)
    
    Args:
        backend: The CoreGraphics backend instance
    """
    rows, cols = backend.rows, backend.cols
    
    # Initialize color pairs
    backend.init_pair(0, (255, 255, 255), (0, 0, 0))    # White on black
    backend.init_pair(1, (255, 100, 100), (0, 0, 0))    # Light red
    backend.init_pair(2, (100, 255, 100), (0, 0, 0))    # Light green
    backend.init_pair(3, (100, 100, 255), (0, 0, 0))    # Light blue
    backend.init_pair(4, (255, 255, 100), (0, 0, 0))    # Light yellow
    backend.init_pair(5, (255, 100, 255), (0, 0, 0))    # Light magenta
    backend.init_pair(6, (100, 255, 255), (0, 0, 0))    # Light cyan
    backend.init_pair(7, (200, 200, 200), (0, 0, 0))    # Light gray
    
    # Create a pattern of characters
    char_set = "█▓▒░▄▀■□▪▫●○◆◇★☆♠♣♥♦"
    
    # Fill the grid with a colorful pattern
    for row in range(rows):
        for col in range(cols):
            # Create a wave pattern with different characters
            char_index = (row + col) % len(char_set)
            char = char_set[char_index]
            
            # Use different colors in horizontal bands
            color_pair = (row // 3) % 8
            
            # Apply attributes in a pattern
            attributes = 0
            if row % 4 == 0:
                attributes |= TextAttribute.BOLD
            if col % 6 == 0:
                attributes |= TextAttribute.UNDERLINE
            if (row + col) % 10 == 0:
                attributes |= TextAttribute.REVERSE
            
            backend.addch(row, col, char, color_pair, attributes)
    
    # Add a title at the top
    title = " CHARACTER DRAWING PERFORMANCE TEST "
    title_col = (cols - len(title)) // 2
    for i, char in enumerate(title):
        backend.addch(0, title_col + i, char, 4, TextAttribute.BOLD)
    
    # Add performance info
    info_lines = [
        "This demo demonstrates the character drawing bottleneck",
        "Watch the console for timing output (t4-t3 ≈ 0.03 seconds)",
        "Press Ctrl+C to exit"
    ]
    
    for i, line in enumerate(info_lines):
        start_col = (cols - len(line)) // 2
        for j, char in enumerate(line):
            if start_col + j < cols:
                backend.addch(2 + i, start_col + j, char, 7, 0)


def main():
    """Run the character drawing performance demo."""
    if not COREGRAPHICS_AVAILABLE:
        print("Error: CoreGraphics backend not available")
        print("This demo requires macOS with PyObjC installed")
        return 1
    
    print("=" * 70)
    print("Character Drawing Performance Demo")
    print("=" * 70)
    print()
    print("This demo will launch a window showing the character drawing")
    print("performance bottleneck in the CoreGraphics backend.")
    print()
    print("Expected behavior:")
    print("  - Console will show timing output for each redraw")
    print("  - t4-t3 (character drawing phase) should be ≈ 0.03 seconds (30ms)")
    print("  - Target after optimization: < 0.01 seconds (10ms)")
    print()
    print("Press Ctrl+C to exit the demo")
    print("=" * 70)
    print()
    
    # Create backend
    backend = CoreGraphicsBackend(rows=24, cols=80)
    
    # Fill with performance test content
    create_performance_test_content(backend)
    
    # Create and show window
    app = Cocoa.NSApplication.sharedApplication()
    
    # Create window
    window_rect = Cocoa.NSMakeRect(100, 100, 
                                   80 * backend.char_width, 
                                   24 * backend.char_height)
    window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        window_rect,
        Cocoa.NSWindowStyleMaskTitled | 
        Cocoa.NSWindowStyleMaskClosable |
        Cocoa.NSWindowStyleMaskMiniaturizable,
        Cocoa.NSBackingStoreBuffered,
        False
    )
    
    window.setTitle_("Character Drawing Performance Demo")
    window.setContentView_(backend._view)
    window.makeKeyAndOrderFront_(None)
    
    # Force initial draw
    backend._view.setNeedsDisplay_(True)
    
    print("Window opened. Watch the console for timing output.")
    print("Each redraw will show performance metrics.")
    print()
    
    # Run the application
    try:
        app.run()
    except KeyboardInterrupt:
        print()
        print("Demo terminated by user")
        return 0
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
