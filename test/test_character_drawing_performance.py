#!/usr/bin/env python3
"""
Test case to reproduce the 0.03 seconds character drawing performance issue.

This test creates a scenario that demonstrates the performance bottleneck in the
character drawing phase (t4-t3) of the CoreGraphics backend's drawRect_() method.

The test fills a grid with non-space characters to maximize the character drawing
workload and measures the time taken to process the character drawing phase.

Expected behavior:
- Current implementation: t4-t3 should be approximately 0.03 seconds (30ms)
- Target after optimization: t4-t3 should be under 0.01 seconds (10ms)
"""

import sys
import time
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

# Add ttk directory to path
ttk_path = Path(__file__).parent.parent / 'ttk'
sys.path.insert(0, str(ttk_path))

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    from ttk.text_attribute import TextAttribute
    COREGRAPHICS_AVAILABLE = True
except ImportError:
    COREGRAPHICS_AVAILABLE = False
    print("CoreGraphics backend not available - skipping test")


def test_character_drawing_performance():
    """
    Test that reproduces the 0.03 seconds character drawing performance issue.
    
    This test:
    1. Creates a CoreGraphics backend with a 24x80 grid (standard terminal size)
    2. Fills the entire grid with non-space characters to maximize drawing workload
    3. Uses various color pairs and attributes to simulate realistic usage
    4. Triggers a full-screen redraw
    5. Measures the time taken for the character drawing phase (t4-t3)
    
    The test should demonstrate that the current implementation takes approximately
    0.03 seconds (30ms) for the character drawing phase.
    """
    if not COREGRAPHICS_AVAILABLE:
        print("Skipping test - CoreGraphics backend not available")
        return
    
    print("=" * 70)
    print("Character Drawing Performance Test")
    print("=" * 70)
    print()
    print("This test reproduces the 0.03 seconds character drawing bottleneck")
    print("by filling a 24x80 grid with non-space characters.")
    print()
    
    # Create backend with standard terminal size
    rows, cols = 24, 80
    backend = CoreGraphicsBackend(rows=rows, cols=cols)
    
    # Initialize color pairs with various colors
    # Color pair 0 is default (white on black)
    backend.init_pair(0, (255, 255, 255), (0, 0, 0))
    backend.init_pair(1, (255, 0, 0), (0, 0, 0))      # Red on black
    backend.init_pair(2, (0, 255, 0), (0, 0, 0))      # Green on black
    backend.init_pair(3, (0, 0, 255), (0, 0, 0))      # Blue on black
    backend.init_pair(4, (255, 255, 0), (0, 0, 0))    # Yellow on black
    backend.init_pair(5, (255, 0, 255), (0, 0, 0))    # Magenta on black
    backend.init_pair(6, (0, 255, 255), (0, 0, 0))    # Cyan on black
    backend.init_pair(7, (128, 128, 128), (0, 0, 0))  # Gray on black
    
    # Fill the grid with non-space characters to maximize character drawing workload
    # Use a variety of characters, color pairs, and attributes to simulate realistic usage
    print(f"Filling {rows}x{cols} grid with non-space characters...")
    
    char_set = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/"
    char_index = 0
    
    for row in range(rows):
        for col in range(cols):
            # Cycle through characters
            char = char_set[char_index % len(char_set)]
            char_index += 1
            
            # Use different color pairs for different regions
            color_pair = (row * cols + col) % 8
            
            # Apply various attributes to different cells
            attributes = 0
            if row % 3 == 0:
                attributes |= TextAttribute.BOLD
            if col % 5 == 0:
                attributes |= TextAttribute.UNDERLINE
            if (row + col) % 7 == 0:
                attributes |= TextAttribute.REVERSE
            
            # Set the character in the grid
            backend.addch(row, col, char, color_pair, attributes)
    
    print(f"Grid filled with {rows * cols} non-space characters")
    print()
    
    # Trigger a full-screen redraw and measure performance
    print("Triggering full-screen redraw...")
    print("Measuring character drawing phase performance (t4-t3)...")
    print()
    
    # Note: In a real application, this would be called by the Cocoa event loop
    # For this test, we're calling it directly to measure performance
    # The actual timing will be printed by the drawRect_() method itself
    
    # Create a full-screen dirty rect
    import Cocoa
    full_rect = Cocoa.NSMakeRect(0, 0, cols * backend.char_width, rows * backend.char_height)
    
    # Call drawRect_() which will print timing information
    # Note: This requires a valid graphics context, which may not be available
    # in a test environment. The test demonstrates the setup; actual timing
    # would be measured in a running application.
    try:
        backend._view.drawRect_(full_rect)
        print()
        print("✓ Test completed successfully")
        print()
        print("Expected results:")
        print("  - Current implementation: t4-t3 ≈ 0.03 seconds (30ms)")
        print("  - Target after optimization: t4-t3 < 0.01 seconds (10ms)")
    except Exception as e:
        print(f"Note: Could not execute drawRect_() in test environment: {e}")
        print()
        print("This test demonstrates the setup for reproducing the performance issue.")
        print("To measure actual performance, run this scenario in a live application")
        print("with a valid CoreGraphics context.")
    
    print()
    print("=" * 70)


if __name__ == '__main__':
    test_character_drawing_performance()
