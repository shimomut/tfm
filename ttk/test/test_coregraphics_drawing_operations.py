"""
Test CoreGraphics backend drawing operations.

This test suite verifies that the drawing operations (draw_text, clear,
clear_region, draw_hline, draw_vline, draw_rect) work correctly and handle
out-of-bounds coordinates gracefully.

Tests cover:
- draw_text() updates grid cells correctly
- clear() resets all cells
- clear_region() resets specified cells
- draw_hline() draws horizontal lines
- draw_vline() draws vertical lines
- draw_rect() draws filled and outlined rectangles
- Out-of-bounds coordinates are handled gracefully
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

import pytest
from backends.coregraphics_backend import CoreGraphicsBackend
from renderer import TextAttribute


@pytest.mark.skipif(not COCOA_AVAILABLE, reason="PyObjC not available")
class TestCoreGraphicsDrawingOperations:
    """Test suite for CoreGraphics backend drawing operations."""
    
    def test_draw_text_updates_grid(self):
        """Test that draw_text updates grid cells correctly."""
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
        
        # Verify other cells are unchanged
        assert backend.grid[2][4] == (' ', 0, 0)
        assert backend.grid[2][10] == (' ', 0, 0)
        assert backend.grid[1][5] == (' ', 0, 0)
        assert backend.grid[3][5] == (' ', 0, 0)
    
    def test_draw_text_with_color_and_attributes(self):
        """Test that draw_text stores color pair and attributes."""
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
        assert backend.grid[3][9] == ('s', 1, attrs)
        assert backend.grid[3][10] == ('t', 1, attrs)
    
    def test_draw_text_out_of_bounds_row(self):
        """Test that draw_text handles out-of-bounds row gracefully."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Try to draw at negative row
        backend.draw_text(-1, 5, "Test")
        
        # Try to draw at row >= rows
        backend.draw_text(10, 5, "Test")
        backend.draw_text(100, 5, "Test")
        
        # Verify grid is unchanged (all cells still empty)
        for row in range(10):
            for col in range(20):
                assert backend.grid[row][col] == (' ', 0, 0)
    
    def test_draw_text_out_of_bounds_col(self):
        """Test that draw_text handles out-of-bounds column gracefully."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Try to draw at negative column
        backend.draw_text(5, -1, "Test")
        
        # Try to draw at column >= cols
        backend.draw_text(5, 20, "Test")
        backend.draw_text(5, 100, "Test")
        
        # Verify grid is unchanged
        for row in range(10):
            for col in range(20):
                assert backend.grid[row][col] == (' ', 0, 0)
    
    def test_draw_text_truncates_at_edge(self):
        """Test that draw_text truncates text at grid edge."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Draw text that extends beyond the right edge
        backend.draw_text(5, 17, "Hello")
        
        # Verify only characters that fit are drawn
        assert backend.grid[5][17] == ('H', 0, 0)
        assert backend.grid[5][18] == ('e', 0, 0)
        assert backend.grid[5][19] == ('l', 0, 0)
        
        # Verify no characters beyond the edge
        # (can't check grid[5][20] as it doesn't exist)
    
    def test_clear_resets_all_cells(self):
        """Test that clear() resets all cells to spaces."""
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
    
    def test_clear_region_resets_specified_cells(self):
        """Test that clear_region() resets only specified cells."""
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
        assert backend.grid[2][4] == ('X', 0, 0)
        assert backend.grid[2][10] == ('X', 0, 0)
    
    def test_clear_region_handles_out_of_bounds(self):
        """Test that clear_region() handles out-of-bounds coordinates."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Fill grid with 'X' characters
        for row in range(10):
            for col in range(20):
                backend.grid[row][col] = ('X', 0, 0)
        
        # Clear region that extends beyond grid bounds
        backend.clear_region(8, 18, 5, 5)
        
        # Verify only valid cells are cleared
        assert backend.grid[8][18] == (' ', 0, 0)
        assert backend.grid[8][19] == (' ', 0, 0)
        assert backend.grid[9][18] == (' ', 0, 0)
        assert backend.grid[9][19] == (' ', 0, 0)
        
        # Verify cells outside the clamped region are unchanged
        assert backend.grid[7][18] == ('X', 0, 0)
        assert backend.grid[8][17] == ('X', 0, 0)
    
    def test_draw_hline_draws_horizontal_line(self):
        """Test that draw_hline() draws a horizontal line."""
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
        assert backend.grid[4][5] == (' ', 0, 0)
        assert backend.grid[6][5] == (' ', 0, 0)
    
    def test_draw_hline_handles_out_of_bounds_row(self):
        """Test that draw_hline() handles out-of-bounds row."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Try to draw at negative row
        backend.draw_hline(-1, 5, '-', 10)
        
        # Try to draw at row >= rows
        backend.draw_hline(10, 5, '-', 10)
        
        # Verify grid is unchanged
        for row in range(10):
            for col in range(20):
                assert backend.grid[row][col] == (' ', 0, 0)
    
    def test_draw_hline_truncates_at_edge(self):
        """Test that draw_hline() truncates at grid edge."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Draw line that extends beyond right edge
        backend.draw_hline(5, 15, '-', 10)
        
        # Verify only characters that fit are drawn
        for col in range(15, 20):
            assert backend.grid[5][col] == ('-', 0, 0)
    
    def test_draw_vline_draws_vertical_line(self):
        """Test that draw_vline() draws a vertical line."""
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
        assert backend.grid[3][6] == (' ', 0, 0)
        assert backend.grid[3][8] == (' ', 0, 0)
    
    def test_draw_vline_handles_out_of_bounds_col(self):
        """Test that draw_vline() handles out-of-bounds column."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Try to draw at negative column
        backend.draw_vline(2, -1, '|', 5)
        
        # Try to draw at column >= cols
        backend.draw_vline(2, 20, '|', 5)
        
        # Verify grid is unchanged
        for row in range(10):
            for col in range(20):
                assert backend.grid[row][col] == (' ', 0, 0)
    
    def test_draw_vline_truncates_at_edge(self):
        """Test that draw_vline() truncates at grid edge."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Draw line that extends beyond bottom edge
        backend.draw_vline(7, 10, '|', 5)
        
        # Verify only characters that fit are drawn
        for row in range(7, 10):
            assert backend.grid[row][10] == ('|', 0, 0)
    
    def test_draw_rect_filled(self):
        """Test that draw_rect() draws a filled rectangle."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Draw filled rectangle at (2, 5) with size 3x7
        backend.draw_rect(2, 5, 3, 7, color_pair=0, filled=True)
        
        # Verify all cells in the rectangle are filled with spaces
        for row in range(2, 5):
            for col in range(5, 12):
                assert backend.grid[row][col] == (' ', 0, 0)
        
        # Note: Filled rectangles use space characters, so they look the same
        # as empty cells. The difference is visible when a non-zero color pair
        # is used, as the background color will show through.
    
    def test_draw_rect_outlined(self):
        """Test that draw_rect() draws an outlined rectangle."""
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
        
        # Verify interior is unchanged (still spaces)
        for row in range(3, 5):
            for col in range(6, 12):
                assert backend.grid[row][col] == (' ', 0, 0)
    
    def test_draw_rect_handles_out_of_bounds(self):
        """Test that draw_rect() handles out-of-bounds coordinates."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Draw rectangle that extends beyond grid bounds
        backend.draw_rect(8, 18, 5, 5, color_pair=0, filled=False)
        
        # Verify only valid cells are drawn
        # Top-left corner should be at (8, 18)
        assert backend.grid[8][18] == ('┌', 0, 0)
        
        # Top-right corner should be at (8, 19) since that's the edge
        assert backend.grid[8][19] == ('┐', 0, 0)
        
        # Bottom-left corner should be at (9, 18) since that's the edge
        assert backend.grid[9][18] == ('└', 0, 0)
        
        # Bottom-right corner should be at (9, 19)
        assert backend.grid[9][19] == ('┘', 0, 0)
    
    def test_draw_rect_with_invalid_dimensions(self):
        """Test that draw_rect() handles invalid dimensions."""
        backend = CoreGraphicsBackend(rows=10, cols=20)
        backend.initialize()
        
        # Fill grid with 'X' to verify nothing changes
        for row in range(10):
            for col in range(20):
                backend.grid[row][col] = ('X', 0, 0)
        
        # Try to draw rectangle with zero height
        backend.draw_rect(5, 5, 0, 5)
        
        # Try to draw rectangle with zero width
        backend.draw_rect(5, 5, 5, 0)
        
        # Try to draw rectangle with negative dimensions
        backend.draw_rect(5, 5, -3, 5)
        backend.draw_rect(5, 5, 5, -3)
        
        # Verify grid is unchanged
        for row in range(10):
            for col in range(20):
                assert backend.grid[row][col] == ('X', 0, 0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
