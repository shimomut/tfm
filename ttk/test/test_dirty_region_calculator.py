"""
Unit tests for DirtyRegionCalculator.

This module tests the DirtyRegionCalculator class which converts dirty rectangles
from CoreGraphics coordinates to TTK cell coordinates.
"""

import unittest
from unittest.mock import Mock


class TestDirtyRegionCalculator(unittest.TestCase):
    """Test cases for DirtyRegionCalculator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to avoid import errors if PyObjC is not available
        try:
            from ttk.backends.coregraphics_backend import DirtyRegionCalculator
            self.DirtyRegionCalculator = DirtyRegionCalculator
            self.available = True
        except (ImportError, RuntimeError):
            self.available = False
            self.skipTest("PyObjC not available")
    
    def _make_rect(self, x, y, width, height):
        """Create a mock NSRect object."""
        rect = Mock()
        rect.origin = Mock()
        rect.origin.x = x
        rect.origin.y = y
        rect.size = Mock()
        rect.size.width = width
        rect.size.height = height
        return rect
    
    def test_full_screen_dirty_rect(self):
        """Test dirty region calculation for full-screen rect."""
        # Full screen: 24 rows × 80 cols, 10px wide × 20px tall chars
        # Total size: 800px × 480px
        rect = self._make_rect(0, 0, 800, 480)
        
        start_row, end_row, start_col, end_col = (
            self.DirtyRegionCalculator.get_dirty_cells(
                rect, rows=24, cols=80,
                char_width=10.0, char_height=20.0
            )
        )
        
        # Should cover entire grid
        self.assertEqual(start_row, 0)
        self.assertEqual(end_row, 24)
        self.assertEqual(start_col, 0)
        self.assertEqual(end_col, 80)
    
    def test_top_left_corner(self):
        """Test dirty region for top-left corner."""
        # Top-left corner: 4 rows × 20 cols
        # In CG coords: x=0, y=400 (bottom of region), width=200, height=80
        # CG y=400 to y=480 maps to TTK rows 0-3
        rect = self._make_rect(0, 400, 200, 80)
        
        start_row, end_row, start_col, end_col = (
            self.DirtyRegionCalculator.get_dirty_cells(
                rect, rows=24, cols=80,
                char_width=10.0, char_height=20.0
            )
        )
        
        # Should cover top-left 4×20 region
        self.assertEqual(start_row, 0)
        self.assertEqual(end_row, 4)
        self.assertEqual(start_col, 0)
        self.assertEqual(end_col, 20)
    
    def test_bottom_right_corner(self):
        """Test dirty region for bottom-right corner."""
        # Bottom-right corner: 4 rows × 20 cols
        # In CG coords: x=600, y=0 (bottom of region), width=200, height=80
        # CG y=0 to y=80 maps to TTK rows 20-23
        rect = self._make_rect(600, 0, 200, 80)
        
        start_row, end_row, start_col, end_col = (
            self.DirtyRegionCalculator.get_dirty_cells(
                rect, rows=24, cols=80,
                char_width=10.0, char_height=20.0
            )
        )
        
        # Should cover bottom-right 4×20 region
        self.assertEqual(start_row, 20)
        self.assertEqual(end_row, 24)
        self.assertEqual(start_col, 60)
        self.assertEqual(end_col, 80)
    
    def test_middle_region(self):
        """Test dirty region for middle of screen."""
        # Middle region: rows 10-14, cols 30-50
        # In CG coords: x=300, y=200, width=200, height=80
        # CG y=200 to y=280 maps to TTK rows 10-13
        rect = self._make_rect(300, 200, 200, 80)
        
        start_row, end_row, start_col, end_col = (
            self.DirtyRegionCalculator.get_dirty_cells(
                rect, rows=24, cols=80,
                char_width=10.0, char_height=20.0
            )
        )
        
        # Should cover middle region
        self.assertEqual(start_row, 10)
        self.assertEqual(end_row, 14)
        self.assertEqual(start_col, 30)
        self.assertEqual(end_col, 50)
    
    def test_single_cell(self):
        """Test dirty region for single cell."""
        # Single cell at row 5, col 10
        # In CG coords: x=100, y=360, width=10, height=20
        rect = self._make_rect(100, 360, 10, 20)
        
        start_row, end_row, start_col, end_col = (
            self.DirtyRegionCalculator.get_dirty_cells(
                rect, rows=24, cols=80,
                char_width=10.0, char_height=20.0
            )
        )
        
        # Should cover single cell
        self.assertEqual(start_row, 5)
        self.assertEqual(end_row, 6)
        self.assertEqual(start_col, 10)
        self.assertEqual(end_col, 11)
    
    def test_boundary_clamping_negative(self):
        """Test boundary clamping for negative coordinates."""
        # Rect extends beyond left and top edges
        rect = self._make_rect(-50, 450, 100, 100)
        
        start_row, end_row, start_col, end_col = (
            self.DirtyRegionCalculator.get_dirty_cells(
                rect, rows=24, cols=80,
                char_width=10.0, char_height=20.0
            )
        )
        
        # Should clamp to valid bounds
        self.assertGreaterEqual(start_row, 0)
        self.assertGreaterEqual(start_col, 0)
        self.assertLessEqual(end_row, 24)
        self.assertLessEqual(end_col, 80)
    
    def test_boundary_clamping_overflow(self):
        """Test boundary clamping for coordinates beyond grid."""
        # Rect extends beyond right and bottom edges
        rect = self._make_rect(700, -50, 200, 100)
        
        start_row, end_row, start_col, end_col = (
            self.DirtyRegionCalculator.get_dirty_cells(
                rect, rows=24, cols=80,
                char_width=10.0, char_height=20.0
            )
        )
        
        # Should clamp to valid bounds
        self.assertGreaterEqual(start_row, 0)
        self.assertGreaterEqual(start_col, 0)
        self.assertLessEqual(end_row, 24)
        self.assertLessEqual(end_col, 80)
    
    def test_zero_size_rect(self):
        """Test handling of zero-size rect."""
        # Zero-size rect
        rect = self._make_rect(100, 200, 0, 0)
        
        start_row, end_row, start_col, end_col = (
            self.DirtyRegionCalculator.get_dirty_cells(
                rect, rows=24, cols=80,
                char_width=10.0, char_height=20.0
            )
        )
        
        # Should return valid (possibly empty) range
        self.assertGreaterEqual(start_row, 0)
        self.assertGreaterEqual(start_col, 0)
        self.assertLessEqual(end_row, 24)
        self.assertLessEqual(end_col, 80)
        self.assertLessEqual(start_row, end_row)
        self.assertLessEqual(start_col, end_col)
    
    def test_different_char_dimensions(self):
        """Test with different character dimensions."""
        # Test with larger characters: 15px × 25px
        rect = self._make_rect(0, 0, 1200, 600)
        
        start_row, end_row, start_col, end_col = (
            self.DirtyRegionCalculator.get_dirty_cells(
                rect, rows=24, cols=80,
                char_width=15.0, char_height=25.0
            )
        )
        
        # Should cover entire grid
        self.assertEqual(start_row, 0)
        self.assertEqual(end_row, 24)
        self.assertEqual(start_col, 0)
        self.assertEqual(end_col, 80)
    
    def test_fractional_coordinates(self):
        """Test handling of fractional pixel coordinates."""
        # Rect with fractional coordinates
        rect = self._make_rect(105.5, 205.7, 95.3, 78.9)
        
        start_row, end_row, start_col, end_col = (
            self.DirtyRegionCalculator.get_dirty_cells(
                rect, rows=24, cols=80,
                char_width=10.0, char_height=20.0
            )
        )
        
        # Should handle fractional coordinates correctly
        self.assertGreaterEqual(start_row, 0)
        self.assertGreaterEqual(start_col, 0)
        self.assertLessEqual(end_row, 24)
        self.assertLessEqual(end_col, 80)
        self.assertLess(start_row, end_row)
        self.assertLess(start_col, end_col)


if __name__ == '__main__':
    unittest.main()
