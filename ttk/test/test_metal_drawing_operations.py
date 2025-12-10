"""
Unit tests for Metal backend drawing operations.

This module tests the drawing operations implemented in the Metal backend:
- draw_text(): Drawing text at specified positions
- draw_hline(): Drawing horizontal lines
- draw_vline(): Drawing vertical lines
- draw_rect(): Drawing rectangles (filled and outlined)
- clear(): Clearing the entire grid
- clear_region(): Clearing rectangular regions

Tests verify:
1. Drawing operations update the grid buffer correctly
2. Out-of-bounds coordinates are handled gracefully
3. Color pairs and attributes are stored correctly
4. Edge cases (empty strings, zero dimensions) are handled
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock PyObjC modules before importing MetalBackend
sys.modules['Metal'] = MagicMock()
sys.modules['Cocoa'] = MagicMock()
sys.modules['CoreText'] = MagicMock()
sys.modules['Quartz'] = MagicMock()
sys.modules['MetalKit'] = MagicMock()

from ttk.backends.metal_backend import MetalBackend
from ttk.renderer import TextAttribute


class TestMetalDrawText(unittest.TestCase):
    """Test draw_text() method."""
    
    def setUp(self):
        """Set up test backend with mocked initialization."""
        self.backend = MetalBackend()
        # Manually initialize grid without calling initialize()
        self.backend.rows = 10
        self.backend.cols = 20
        self.backend.grid = [
            [(' ', 0, 0) for _ in range(self.backend.cols)]
            for _ in range(self.backend.rows)
        ]
    
    def test_draw_text_basic(self):
        """Test basic text drawing."""
        self.backend.draw_text(0, 0, "Hello", color_pair=1, attributes=0)
        
        # Verify characters are in grid
        self.assertEqual(self.backend.grid[0][0], ('H', 1, 0))
        self.assertEqual(self.backend.grid[0][1], ('e', 1, 0))
        self.assertEqual(self.backend.grid[0][2], ('l', 1, 0))
        self.assertEqual(self.backend.grid[0][3], ('l', 1, 0))
        self.assertEqual(self.backend.grid[0][4], ('o', 1, 0))
    
    def test_draw_text_with_attributes(self):
        """Test text drawing with attributes."""
        attrs = TextAttribute.BOLD | TextAttribute.UNDERLINE
        self.backend.draw_text(1, 0, "Test", color_pair=2, attributes=attrs)
        
        # Verify attributes are stored
        self.assertEqual(self.backend.grid[1][0], ('T', 2, attrs))
        self.assertEqual(self.backend.grid[1][1], ('e', 2, attrs))
    
    def test_draw_text_out_of_bounds_row(self):
        """Test text drawing with out-of-bounds row."""
        # Should not crash
        self.backend.draw_text(-1, 0, "Test")
        self.backend.draw_text(100, 0, "Test")
        
        # Grid should be unchanged
        self.assertEqual(self.backend.grid[0][0], (' ', 0, 0))
    
    def test_draw_text_partial_out_of_bounds(self):
        """Test text drawing that extends beyond grid boundary."""
        # Draw text that extends past right edge
        self.backend.draw_text(0, 18, "Hello", color_pair=1)
        
        # Only "He" should fit
        self.assertEqual(self.backend.grid[0][18], ('H', 1, 0))
        self.assertEqual(self.backend.grid[0][19], ('e', 1, 0))
    
    def test_draw_text_empty_string(self):
        """Test drawing empty string."""
        # Should not crash
        self.backend.draw_text(0, 0, "")
        
        # Grid should be unchanged
        self.assertEqual(self.backend.grid[0][0], (' ', 0, 0))
    
    def test_draw_text_overwrites_existing(self):
        """Test that drawing text overwrites existing content."""
        self.backend.draw_text(0, 0, "AAA", color_pair=1)
        self.backend.draw_text(0, 0, "BBB", color_pair=2)
        
        # Should have new content
        self.assertEqual(self.backend.grid[0][0], ('B', 2, 0))
        self.assertEqual(self.backend.grid[0][1], ('B', 2, 0))
        self.assertEqual(self.backend.grid[0][2], ('B', 2, 0))


class TestMetalDrawHLine(unittest.TestCase):
    """Test draw_hline() method."""
    
    def setUp(self):
        """Set up test backend."""
        self.backend = MetalBackend()
        self.backend.rows = 10
        self.backend.cols = 20
        self.backend.grid = [
            [(' ', 0, 0) for _ in range(self.backend.cols)]
            for _ in range(self.backend.rows)
        ]
    
    def test_draw_hline_basic(self):
        """Test basic horizontal line drawing."""
        self.backend.draw_hline(0, 0, '-', 5, color_pair=1)
        
        # Verify line is drawn
        for i in range(5):
            self.assertEqual(self.backend.grid[0][i], ('-', 1, 0))
    
    def test_draw_hline_custom_char(self):
        """Test horizontal line with custom character."""
        self.backend.draw_hline(1, 0, '=', 3, color_pair=2)
        
        self.assertEqual(self.backend.grid[1][0], ('=', 2, 0))
        self.assertEqual(self.backend.grid[1][1], ('=', 2, 0))
        self.assertEqual(self.backend.grid[1][2], ('=', 2, 0))
    
    def test_draw_hline_out_of_bounds(self):
        """Test horizontal line with out-of-bounds coordinates."""
        # Should not crash
        self.backend.draw_hline(-1, 0, '-', 5)
        self.backend.draw_hline(100, 0, '-', 5)
    
    def test_draw_hline_partial_out_of_bounds(self):
        """Test horizontal line that extends beyond grid."""
        self.backend.draw_hline(0, 18, '-', 5, color_pair=1)
        
        # Only 2 characters should fit
        self.assertEqual(self.backend.grid[0][18], ('-', 1, 0))
        self.assertEqual(self.backend.grid[0][19], ('-', 1, 0))
    
    def test_draw_hline_zero_length(self):
        """Test horizontal line with zero length."""
        # Should not crash
        self.backend.draw_hline(0, 0, '-', 0)
        
        # Grid should be unchanged
        self.assertEqual(self.backend.grid[0][0], (' ', 0, 0))


class TestMetalDrawVLine(unittest.TestCase):
    """Test draw_vline() method."""
    
    def setUp(self):
        """Set up test backend."""
        self.backend = MetalBackend()
        self.backend.rows = 10
        self.backend.cols = 20
        self.backend.grid = [
            [(' ', 0, 0) for _ in range(self.backend.cols)]
            for _ in range(self.backend.rows)
        ]
    
    def test_draw_vline_basic(self):
        """Test basic vertical line drawing."""
        self.backend.draw_vline(0, 0, '|', 5, color_pair=1)
        
        # Verify line is drawn
        for i in range(5):
            self.assertEqual(self.backend.grid[i][0], ('|', 1, 0))
    
    def test_draw_vline_custom_char(self):
        """Test vertical line with custom character."""
        self.backend.draw_vline(0, 1, '#', 3, color_pair=2)
        
        self.assertEqual(self.backend.grid[0][1], ('#', 2, 0))
        self.assertEqual(self.backend.grid[1][1], ('#', 2, 0))
        self.assertEqual(self.backend.grid[2][1], ('#', 2, 0))
    
    def test_draw_vline_out_of_bounds_col(self):
        """Test vertical line with out-of-bounds column."""
        # Should not crash
        self.backend.draw_vline(0, -1, '|', 5)
        self.backend.draw_vline(0, 100, '|', 5)
        
        # Grid should be unchanged
        self.assertEqual(self.backend.grid[0][0], (' ', 0, 0))
    
    def test_draw_vline_partial_out_of_bounds(self):
        """Test vertical line that extends beyond grid."""
        self.backend.draw_vline(8, 0, '|', 5, color_pair=1)
        
        # Only 2 characters should fit (rows 8 and 9)
        self.assertEqual(self.backend.grid[8][0], ('|', 1, 0))
        self.assertEqual(self.backend.grid[9][0], ('|', 1, 0))
    
    def test_draw_vline_zero_length(self):
        """Test vertical line with zero length."""
        # Should not crash
        self.backend.draw_vline(0, 0, '|', 0)
        
        # Grid should be unchanged
        self.assertEqual(self.backend.grid[0][0], (' ', 0, 0))
    
    def test_draw_vline_empty_char(self):
        """Test vertical line with empty character."""
        # Should not crash
        self.backend.draw_vline(0, 0, '', 5)
        
        # Grid should be unchanged
        self.assertEqual(self.backend.grid[0][0], (' ', 0, 0))


class TestMetalDrawRect(unittest.TestCase):
    """Test draw_rect() method."""
    
    def setUp(self):
        """Set up test backend."""
        self.backend = MetalBackend()
        self.backend.rows = 10
        self.backend.cols = 20
        self.backend.grid = [
            [(' ', 0, 0) for _ in range(self.backend.cols)]
            for _ in range(self.backend.rows)
        ]
    
    def test_draw_rect_outline(self):
        """Test drawing outlined rectangle."""
        self.backend.draw_rect(1, 1, 3, 5, color_pair=1, filled=False)
        
        # Check top edge (middle positions, not corners)
        self.assertEqual(self.backend.grid[1][2], ('-', 1, 0))
        self.assertEqual(self.backend.grid[1][3], ('-', 1, 0))
        self.assertEqual(self.backend.grid[1][4], ('-', 1, 0))
        
        # Check bottom edge (middle positions, not corners)
        self.assertEqual(self.backend.grid[3][2], ('-', 1, 0))
        self.assertEqual(self.backend.grid[3][3], ('-', 1, 0))
        self.assertEqual(self.backend.grid[3][4], ('-', 1, 0))
        
        # Check left edge (middle position, not corners)
        self.assertEqual(self.backend.grid[2][1], ('|', 1, 0))
        
        # Check right edge (middle position, not corners)
        self.assertEqual(self.backend.grid[2][5], ('|', 1, 0))
        
        # Corners will have either '-' or '|' depending on draw order
        # Just verify they're not empty
        self.assertNotEqual(self.backend.grid[1][1], (' ', 0, 0))
        self.assertNotEqual(self.backend.grid[1][5], (' ', 0, 0))
        self.assertNotEqual(self.backend.grid[3][1], (' ', 0, 0))
        self.assertNotEqual(self.backend.grid[3][5], (' ', 0, 0))
    
    def test_draw_rect_filled(self):
        """Test drawing filled rectangle."""
        self.backend.draw_rect(1, 1, 3, 5, color_pair=2, filled=True)
        
        # Check that all cells in rectangle are filled with spaces
        for r in range(1, 4):
            for c in range(1, 6):
                self.assertEqual(self.backend.grid[r][c], (' ', 2, 0))
    
    def test_draw_rect_single_cell(self):
        """Test drawing 1x1 rectangle."""
        self.backend.draw_rect(0, 0, 1, 1, color_pair=1, filled=False)
        
        # Should draw at least one character
        self.assertNotEqual(self.backend.grid[0][0], (' ', 0, 0))
    
    def test_draw_rect_zero_dimensions(self):
        """Test drawing rectangle with zero dimensions."""
        # Should not crash
        self.backend.draw_rect(0, 0, 0, 0, filled=False)
        self.backend.draw_rect(0, 0, 0, 5, filled=False)
        self.backend.draw_rect(0, 0, 5, 0, filled=False)
    
    def test_draw_rect_out_of_bounds(self):
        """Test drawing rectangle that extends beyond grid."""
        # Should not crash
        self.backend.draw_rect(8, 18, 5, 5, color_pair=1, filled=True)
        
        # Should fill only the visible portion
        self.assertEqual(self.backend.grid[8][18], (' ', 1, 0))
        self.assertEqual(self.backend.grid[9][19], (' ', 1, 0))


class TestMetalClear(unittest.TestCase):
    """Test clear() and clear_region() methods."""
    
    def setUp(self):
        """Set up test backend with some content."""
        self.backend = MetalBackend()
        self.backend.rows = 10
        self.backend.cols = 20
        self.backend.grid = [
            [('X', 1, 1) for _ in range(self.backend.cols)]
            for _ in range(self.backend.rows)
        ]
    
    def test_clear_entire_grid(self):
        """Test clearing entire grid."""
        self.backend.clear()
        
        # Verify all cells are cleared
        for row in range(self.backend.rows):
            for col in range(self.backend.cols):
                self.assertEqual(self.backend.grid[row][col], (' ', 0, 0))
    
    def test_clear_region_basic(self):
        """Test clearing a rectangular region."""
        self.backend.clear_region(2, 3, 3, 5)
        
        # Verify region is cleared
        for r in range(2, 5):
            for c in range(3, 8):
                self.assertEqual(self.backend.grid[r][c], (' ', 0, 0))
        
        # Verify outside region is unchanged
        self.assertEqual(self.backend.grid[0][0], ('X', 1, 1))
        self.assertEqual(self.backend.grid[9][19], ('X', 1, 1))
    
    def test_clear_region_out_of_bounds(self):
        """Test clearing region that extends beyond grid."""
        # Should not crash
        self.backend.clear_region(8, 18, 5, 5)
        
        # Should clear only visible portion
        self.assertEqual(self.backend.grid[8][18], (' ', 0, 0))
        self.assertEqual(self.backend.grid[9][19], (' ', 0, 0))
    
    def test_clear_region_negative_coords(self):
        """Test clearing region with negative coordinates."""
        # Should not crash
        self.backend.clear_region(-5, -5, 10, 10)
        
        # Should clear only visible portion (top-left corner)
        self.assertEqual(self.backend.grid[0][0], (' ', 0, 0))
        self.assertEqual(self.backend.grid[4][4], (' ', 0, 0))
    
    def test_clear_region_zero_dimensions(self):
        """Test clearing region with zero dimensions."""
        # Should not crash
        self.backend.clear_region(0, 0, 0, 0)
        self.backend.clear_region(0, 0, 0, 5)
        self.backend.clear_region(0, 0, 5, 0)
        
        # Grid should be unchanged (all still 'X')
        self.assertEqual(self.backend.grid[0][0], ('X', 1, 1))


class TestMetalDrawingCoordinateSystem(unittest.TestCase):
    """Test coordinate system behavior for drawing operations."""
    
    def setUp(self):
        """Set up test backend."""
        self.backend = MetalBackend()
        self.backend.rows = 10
        self.backend.cols = 20
        self.backend.grid = [
            [(' ', 0, 0) for _ in range(self.backend.cols)]
            for _ in range(self.backend.rows)
        ]
    
    def test_origin_at_top_left(self):
        """Test that (0,0) is at top-left corner."""
        self.backend.draw_text(0, 0, "A", color_pair=1)
        
        # Should be at first row, first column
        self.assertEqual(self.backend.grid[0][0], ('A', 1, 0))
    
    def test_row_increases_downward(self):
        """Test that row coordinate increases downward."""
        self.backend.draw_text(0, 0, "A", color_pair=1)
        self.backend.draw_text(1, 0, "B", color_pair=1)
        self.backend.draw_text(2, 0, "C", color_pair=1)
        
        # Should be in vertical sequence
        self.assertEqual(self.backend.grid[0][0], ('A', 1, 0))
        self.assertEqual(self.backend.grid[1][0], ('B', 1, 0))
        self.assertEqual(self.backend.grid[2][0], ('C', 1, 0))
    
    def test_col_increases_rightward(self):
        """Test that column coordinate increases rightward."""
        self.backend.draw_text(0, 0, "A", color_pair=1)
        self.backend.draw_text(0, 1, "B", color_pair=1)
        self.backend.draw_text(0, 2, "C", color_pair=1)
        
        # Should be in horizontal sequence
        self.assertEqual(self.backend.grid[0][0], ('A', 1, 0))
        self.assertEqual(self.backend.grid[0][1], ('B', 1, 0))
        self.assertEqual(self.backend.grid[0][2], ('C', 1, 0))


if __name__ == '__main__':
    unittest.main()
