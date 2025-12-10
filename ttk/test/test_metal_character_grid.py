"""
Unit tests for Metal backend character grid initialization.

Tests verify that the Metal backend correctly initializes the character grid
buffer with proper dimensions and structure.
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


class TestMetalCharacterGrid(unittest.TestCase):
    """Test cases for Metal backend character grid initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = MetalBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=14
        )
    
    def test_grid_initialization_creates_2d_structure(self):
        """Test that _initialize_grid creates a 2D list structure."""
        # Set up dimensions
        self.backend.rows = 40
        self.backend.cols = 80
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend._initialize_grid()
        
        # Verify grid is a 2D list
        self.assertIsInstance(self.backend.grid, list)
        self.assertEqual(len(self.backend.grid), 40)  # rows
        
        # Verify each row is a list
        for row in self.backend.grid:
            self.assertIsInstance(row, list)
            self.assertEqual(len(row), 80)  # cols
    
    def test_grid_cells_store_char_color_attributes_tuple(self):
        """Test that each grid cell stores (char, color_pair, attributes) tuple."""
        # Set up dimensions
        self.backend.rows = 40
        self.backend.cols = 80
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend._initialize_grid()
        
        # Verify each cell is a tuple with 3 elements
        for row in self.backend.grid:
            for cell in row:
                self.assertIsInstance(cell, tuple)
                self.assertEqual(len(cell), 3)
                
                # Verify tuple structure: (char, color_pair, attributes)
                char, color_pair, attributes = cell
                self.assertIsInstance(char, str)
                self.assertIsInstance(color_pair, int)
                self.assertIsInstance(attributes, int)
    
    def test_grid_initialized_with_spaces(self):
        """Test that grid is initialized with space characters."""
        # Set up dimensions
        self.backend.rows = 40
        self.backend.cols = 80
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend._initialize_grid()
        
        # Verify all cells contain spaces
        for row in self.backend.grid:
            for cell in row:
                char, color_pair, attributes = cell
                self.assertEqual(char, ' ')
    
    def test_grid_initialized_with_default_colors(self):
        """Test that grid is initialized with default color pair (0)."""
        # Set up dimensions
        self.backend.rows = 40
        self.backend.cols = 80
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend._initialize_grid()
        
        # Verify all cells use color pair 0
        for row in self.backend.grid:
            for cell in row:
                char, color_pair, attributes = cell
                self.assertEqual(color_pair, 0)
    
    def test_grid_initialized_with_no_attributes(self):
        """Test that grid is initialized with no text attributes."""
        # Set up dimensions
        self.backend.rows = 40
        self.backend.cols = 80
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend._initialize_grid()
        
        # Verify all cells have no attributes (0)
        for row in self.backend.grid:
            for cell in row:
                char, color_pair, attributes = cell
                self.assertEqual(attributes, 0)
    
    def test_grid_dimensions_calculated_from_window_size(self):
        """Test that grid dimensions are calculated from window size and character dimensions."""
        # Mock window and view
        mock_window = Mock()
        mock_view = Mock()
        mock_frame = Mock()
        mock_frame.size.width = 1200
        mock_frame.size.height = 800
        mock_view.frame.return_value = mock_frame
        mock_window.contentView.return_value = mock_view
        
        self.backend.window = mock_window
        self.backend.metal_view = mock_view
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend._initialize_grid()
        
        # Verify dimensions: 1200/10 = 120 cols, 800/20 = 40 rows
        self.assertEqual(self.backend.cols, 120)
        self.assertEqual(self.backend.rows, 40)
        self.assertEqual(len(self.backend.grid), 40)
        self.assertEqual(len(self.backend.grid[0]), 120)
    
    def test_grid_uses_fallback_dimensions_when_window_not_created(self):
        """Test that grid uses fallback dimensions when window is not created."""
        # Don't set window or metal_view
        self.backend.window = None
        self.backend.metal_view = None
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend._initialize_grid()
        
        # Verify fallback dimensions (40 rows x 80 cols)
        self.assertEqual(self.backend.rows, 40)
        self.assertEqual(self.backend.cols, 80)
        self.assertEqual(len(self.backend.grid), 40)
        self.assertEqual(len(self.backend.grid[0]), 80)
    
    def test_grid_coordinate_system_origin_at_top_left(self):
        """Test that grid coordinate system has origin (0,0) at top-left (Requirement 8.2)."""
        # Set up dimensions
        self.backend.rows = 40
        self.backend.cols = 80
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend._initialize_grid()
        
        # Verify grid[0][0] is the top-left cell
        # This is implicit in the list structure: first row, first column
        self.assertIsNotNone(self.backend.grid[0][0])
        
        # Verify we can access all corners
        top_left = self.backend.grid[0][0]
        top_right = self.backend.grid[0][79]
        bottom_left = self.backend.grid[39][0]
        bottom_right = self.backend.grid[39][79]
        
        # All should be valid cells
        for cell in [top_left, top_right, bottom_left, bottom_right]:
            self.assertIsInstance(cell, tuple)
            self.assertEqual(len(cell), 3)
    
    def test_grid_uses_character_based_coordinates(self):
        """Test that grid uses character-based coordinate system (Requirement 8.1)."""
        # Set up dimensions
        self.backend.rows = 40
        self.backend.cols = 80
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend._initialize_grid()
        
        # Verify grid dimensions are in character rows and columns
        self.assertEqual(len(self.backend.grid), self.backend.rows)
        self.assertEqual(len(self.backend.grid[0]), self.backend.cols)
        
        # Verify each cell represents one character position
        # Access by [row][col] indices
        for row_idx in range(self.backend.rows):
            for col_idx in range(self.backend.cols):
                cell = self.backend.grid[row_idx][col_idx]
                char, color_pair, attributes = cell
                # Each cell stores exactly one character
                self.assertEqual(len(char), 1)
    
    def test_grid_handles_minimum_dimensions(self):
        """Test that grid handles minimum dimensions correctly."""
        # Mock window with very small size
        mock_window = Mock()
        mock_view = Mock()
        mock_frame = Mock()
        mock_frame.size.width = 5
        mock_frame.size.height = 5
        mock_view.frame.return_value = mock_frame
        mock_window.contentView.return_value = mock_view
        
        self.backend.window = mock_window
        self.backend.metal_view = mock_view
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend._initialize_grid()
        
        # Verify minimum dimensions (at least 1x1)
        self.assertGreaterEqual(self.backend.rows, 1)
        self.assertGreaterEqual(self.backend.cols, 1)
        self.assertGreaterEqual(len(self.backend.grid), 1)
        self.assertGreaterEqual(len(self.backend.grid[0]), 1)


if __name__ == '__main__':
    unittest.main()
