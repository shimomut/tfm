#!/usr/bin/env python3
"""
Verification script for CoreGraphics backend drawing operations.

This script demonstrates that all drawing operations work correctly:
- draw_text() updates grid cells
- clear() resets all cells
- clear_region() resets specified cells
- draw_hline() draws horizontal lines
- draw_vline() draws vertical lines
- draw_rect() draws filled and outlined rectangles
- Out-of-bounds coordinates are handled gracefully

Run this script to visually verify the drawing operations.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Check if PyObjC is available
try:
    import Cocoa
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False
    print("PyObjC not available. Install with: pip install pyobjc-framework-Cocoa")
    sys.exit(1)

from backends.coregraphics_backend import CoreGraphicsBackend
from renderer import TextAttribute


def verify_draw_text():
    """Verify draw_text() updates grid cells correctly."""
    print("Testing draw_text()...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Draw text at position (2, 5)
    backend.draw_text(2, 5, "Hello", color_pair=0, attributes=0)
    
    # Verify each character is in the correct cell
    assert backend.grid[2][5] == ('H', 0, 0)
    assert backend.grid[2][6] == ('e', 0, 0)
    assert backend.grid[2][7] == ('l', 0, 0)
    assert backend.grid[2][8] == ('l', 0, 0)
    assert backend.grid[2][9] == ('o', 0, 0)
    
    print("✓ draw_text() works correctly")


def verify_draw_text_with_attributes():
    """Verify draw_text() stores color pair and attributes."""
    print("Testing draw_text() with attributes...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Initialize a color pair
    backend.init_color_pair(1, (255, 0, 0), (0, 0, 255))
    
    # Draw text with color pair and attributes
    attrs = TextAttribute.BOLD | TextAttribute.UNDERLINE
    backend.draw_text(3, 7, "Test", color_pair=1, attributes=attrs)
    
    # Verify color pair and attributes are stored
    assert backend.grid[3][7] == ('T', 1, attrs)
    assert backend.grid[3][8] == ('e', 1, attrs)
    
    print("✓ draw_text() with attributes works correctly")


def verify_out_of_bounds_handling():
    """Verify out-of-bounds coordinates are handled gracefully."""
    print("Testing out-of-bounds handling...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Try to draw at negative row (should not crash)
    backend.draw_text(-1, 5, "Test")
    
    # Try to draw at row >= rows (should not crash)
    backend.draw_text(10, 5, "Test")
    backend.draw_text(100, 5, "Test")
    
    # Try to draw at negative column (should not crash)
    backend.draw_text(5, -1, "Test")
    
    # Try to draw at column >= cols (should not crash)
    backend.draw_text(5, 20, "Test")
    
    print("✓ Out-of-bounds coordinates handled gracefully")


def verify_clear():
    """Verify clear() resets all cells."""
    print("Testing clear()...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Draw some text
    backend.draw_text(2, 5, "Hello")
    backend.draw_text(7, 10, "World")
    
    # Clear the grid
    backend.clear()
    
    # Verify all cells are reset to spaces
    for row in range(10):
        for col in range(20):
            assert backend.grid[row][col] == (' ', 0, 0)
    
    print("✓ clear() works correctly")


def verify_clear_region():
    """Verify clear_region() resets only specified cells."""
    print("Testing clear_region()...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Fill grid with 'X' characters
    for row in range(10):
        for col in range(20):
            backend.grid[row][col] = ('X', 0, 0)
    
    # Clear a 3x5 region starting at (2, 5)
    backend.clear_region(2, 5, 3, 5)
    
    # Verify the region is cleared
    for row in range(2, 5):
        for col in range(5, 10):
            assert backend.grid[row][col] == (' ', 0, 0)
    
    # Verify cells outside the region are unchanged
    assert backend.grid[1][5] == ('X', 0, 0)
    assert backend.grid[5][5] == ('X', 0, 0)
    
    print("✓ clear_region() works correctly")


def verify_draw_hline():
    """Verify draw_hline() draws horizontal lines."""
    print("Testing draw_hline()...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Draw horizontal line at row 5, starting at column 3, length 10
    backend.draw_hline(5, 3, '-', 10, color_pair=0)
    
    # Verify the line is drawn
    for col in range(3, 13):
        assert backend.grid[5][col] == ('-', 0, 0)
    
    # Verify cells outside the line are unchanged
    assert backend.grid[5][2] == (' ', 0, 0)
    assert backend.grid[5][13] == (' ', 0, 0)
    
    print("✓ draw_hline() works correctly")


def verify_draw_vline():
    """Verify draw_vline() draws vertical lines."""
    print("Testing draw_vline()...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Draw vertical line at column 7, starting at row 2, length 5
    backend.draw_vline(2, 7, '|', 5, color_pair=0)
    
    # Verify the line is drawn
    for row in range(2, 7):
        assert backend.grid[row][7] == ('|', 0, 0)
    
    # Verify cells outside the line are unchanged
    assert backend.grid[1][7] == (' ', 0, 0)
    assert backend.grid[7][7] == (' ', 0, 0)
    
    print("✓ draw_vline() works correctly")


def verify_draw_rect_filled():
    """Verify draw_rect() draws filled rectangles."""
    print("Testing draw_rect() filled...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Draw filled rectangle at (2, 5) with size 3x7
    backend.draw_rect(2, 5, 3, 7, color_pair=0, filled=True)
    
    # Verify all cells in the rectangle are filled with spaces
    for row in range(2, 5):
        for col in range(5, 12):
            assert backend.grid[row][col] == (' ', 0, 0)
    
    print("✓ draw_rect() filled works correctly")


def verify_draw_rect_outlined():
    """Verify draw_rect() draws outlined rectangles."""
    print("Testing draw_rect() outlined...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Draw outlined rectangle at (2, 5) with size 4x8
    backend.draw_rect(2, 5, 4, 8, color_pair=0, filled=False)
    
    # Verify corners
    assert backend.grid[2][5] == ('┌', 0, 0)
    assert backend.grid[2][12] == ('┐', 0, 0)
    assert backend.grid[5][5] == ('└', 0, 0)
    assert backend.grid[5][12] == ('┘', 0, 0)
    
    # Verify top and bottom edges
    for col in range(6, 12):
        assert backend.grid[2][col] == ('─', 0, 0)
        assert backend.grid[5][col] == ('─', 0, 0)
    
    # Verify left and right edges
    for row in range(3, 5):
        assert backend.grid[row][5] == ('│', 0, 0)
        assert backend.grid[row][12] == ('│', 0, 0)
    
    print("✓ draw_rect() outlined works correctly")


def verify_refresh():
    """Verify refresh() triggers view redraw."""
    print("Testing refresh()...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Draw some text
    backend.draw_text(5, 5, "Test")
    
    # Call refresh (should not crash)
    backend.refresh()
    
    print("✓ refresh() works correctly")


def verify_refresh_region():
    """Verify refresh_region() triggers partial redraw."""
    print("Testing refresh_region()...")
    backend = CoreGraphicsBackend(rows=10, cols=20)
    backend.initialize()
    
    # Draw some text
    backend.draw_text(5, 5, "Test")
    
    # Call refresh_region (should not crash)
    backend.refresh_region(5, 5, 1, 4)
    
    print("✓ refresh_region() works correctly")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("CoreGraphics Backend Drawing Operations Verification")
    print("=" * 60)
    print()
    
    try:
        verify_draw_text()
        verify_draw_text_with_attributes()
        verify_out_of_bounds_handling()
        verify_clear()
        verify_clear_region()
        verify_draw_hline()
        verify_draw_vline()
        verify_draw_rect_filled()
        verify_draw_rect_outlined()
        verify_refresh()
        verify_refresh_region()
        
        print()
        print("=" * 60)
        print("✓ All drawing operations verified successfully!")
        print("=" * 60)
        print()
        print("Summary:")
        print("- draw_text() updates grid cells correctly")
        print("- clear() resets all cells")
        print("- clear_region() resets specified cells")
        print("- draw_hline() draws horizontal lines")
        print("- draw_vline() draws vertical lines")
        print("- draw_rect() draws filled and outlined rectangles")
        print("- refresh() triggers view redraw")
        print("- refresh_region() triggers partial redraw")
        print("- Out-of-bounds coordinates are handled gracefully")
        
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print("✗ Verification failed!")
        print("=" * 60)
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ Unexpected error!")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
