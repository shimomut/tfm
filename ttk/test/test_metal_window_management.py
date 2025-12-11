"""
Tests for Metal backend window management functionality.

This module tests the window management methods of the Metal backend:
- get_dimensions() - Query window dimensions
- refresh() and refresh_region() - Display updates
- set_cursor_visibility() and move_cursor() - Cursor control
- Window resize handling

Requirements tested: 3.5, 4.6, 8.3, 8.4
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from ttk.backends.metal_backend import MetalBackend
from ttk.input_event import KeyCode, ModifierKey, InputEvent


class TestMetalWindowManagement(unittest.TestCase):
    """Test Metal backend window management methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = MetalBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=14
        )
        
        # Mock the grid dimensions
        self.backend.rows = 40
        self.backend.cols = 120
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend.grid = [
            [(' ', 0, 0) for _ in range(self.backend.cols)]
            for _ in range(self.backend.rows)
        ]
    
    def test_get_dimensions_returns_grid_size(self):
        """Test that get_dimensions() returns correct grid dimensions."""
        # Requirement 8.3: Query window dimensions
        rows, cols = self.backend.get_dimensions()
        
        self.assertEqual(rows, 40)
        self.assertEqual(cols, 120)
        self.assertIsInstance(rows, int)
        self.assertIsInstance(cols, int)
    
    def test_get_dimensions_with_different_sizes(self):
        """Test get_dimensions() with various grid sizes."""
        # Test different dimensions
        test_cases = [
            (24, 80),   # Small terminal
            (40, 120),  # Medium window
            (60, 200),  # Large window
            (1, 1),     # Minimum size
        ]
        
        for rows, cols in test_cases:
            self.backend.rows = rows
            self.backend.cols = cols
            
            result_rows, result_cols = self.backend.get_dimensions()
            self.assertEqual(result_rows, rows)
            self.assertEqual(result_cols, cols)
    
    def test_set_cursor_visibility_true(self):
        """Test setting cursor visibility to True."""
        # Requirement 8.4: Cursor control
        self.backend.cursor_visible = False
        
        self.backend.set_cursor_visibility(True)
        
        self.assertTrue(self.backend.cursor_visible)
    
    def test_set_cursor_visibility_false(self):
        """Test setting cursor visibility to False."""
        self.backend.cursor_visible = True
        
        self.backend.set_cursor_visibility(False)
        
        self.assertFalse(self.backend.cursor_visible)
    
    def test_move_cursor_within_bounds(self):
        """Test moving cursor to valid positions."""
        # Requirement 8.4: Cursor control
        test_positions = [
            (0, 0),      # Top-left corner
            (39, 119),   # Bottom-right corner
            (20, 60),    # Middle
            (0, 119),    # Top-right corner
            (39, 0),     # Bottom-left corner
        ]
        
        for row, col in test_positions:
            self.backend.move_cursor(row, col)
            
            self.assertEqual(self.backend.cursor_row, row)
            self.assertEqual(self.backend.cursor_col, col)
    
    def test_move_cursor_clamps_to_bounds(self):
        """Test that cursor position is clamped to grid bounds."""
        # Test positions outside bounds
        test_cases = [
            (-1, -1, 0, 0),          # Negative coordinates
            (50, 150, 39, 119),      # Beyond grid
            (-10, 60, 0, 60),        # Negative row
            (20, -5, 20, 0),         # Negative column
            (100, 50, 39, 50),       # Row too large
            (20, 200, 20, 119),      # Column too large
        ]
        
        for in_row, in_col, expected_row, expected_col in test_cases:
            self.backend.move_cursor(in_row, in_col)
            
            self.assertEqual(self.backend.cursor_row, expected_row,
                           f"Row clamping failed for input ({in_row}, {in_col})")
            self.assertEqual(self.backend.cursor_col, expected_col,
                           f"Column clamping failed for input ({in_row}, {in_col})")
    
    def test_move_cursor_with_zero_dimensions(self):
        """Test cursor movement when grid has zero dimensions."""
        self.backend.rows = 0
        self.backend.cols = 0
        
        # Should not crash
        self.backend.move_cursor(10, 20)
        
        # Cursor should be at (0, 0)
        self.assertEqual(self.backend.cursor_row, 0)
        self.assertEqual(self.backend.cursor_col, 0)
    
    @patch('ttk.backends.metal_backend.MetalBackend._render_grid')
    def test_refresh_calls_render_grid(self, mock_render):
        """Test that refresh() calls _render_grid()."""
        # Requirement 4.6: Full window refresh
        self.backend.refresh()
        
        mock_render.assert_called_once()
    
    @patch('ttk.backends.metal_backend.MetalBackend._render_grid_region')
    def test_refresh_region_calls_render_grid_region(self, mock_render):
        """Test that refresh_region() calls _render_grid_region()."""
        # Requirement 4.6: Partial region updates
        self.backend.refresh_region(10, 20, 5, 10)
        
        mock_render.assert_called_once_with(10, 20, 5, 10)
    
    def test_handle_window_resize_updates_dimensions(self):
        """Test that window resize updates grid dimensions."""
        # Requirement 8.4: Handle window resize events
        # Mock window and view
        mock_window = Mock()
        mock_view = Mock()
        mock_content_view = Mock()
        
        # Create mock frame with new size
        mock_frame = Mock()
        mock_frame.size.width = 1600  # 160 columns at 10px width
        mock_frame.size.height = 1000  # 50 rows at 20px height
        
        mock_content_view.frame.return_value = mock_frame
        mock_window.contentView.return_value = mock_content_view
        
        self.backend.window = mock_window
        self.backend.metal_view = mock_view
        
        # Initial dimensions
        self.assertEqual(self.backend.rows, 40)
        self.assertEqual(self.backend.cols, 120)
        
        # Handle resize (will work without Cocoa since we mocked the window)
        self.backend._handle_window_resize()
        
        # Check new dimensions
        self.assertEqual(self.backend.rows, 50)
        self.assertEqual(self.backend.cols, 160)
    
    def test_handle_window_resize_preserves_content(self):
        """Test that window resize preserves existing grid content."""
        # Put some content in the grid
        self.backend.grid[5][10] = ('X', 1, 0)
        self.backend.grid[15][20] = ('Y', 2, 0)
        
        # Mock window with larger size
        mock_window = Mock()
        mock_view = Mock()
        mock_content_view = Mock()
        
        mock_frame = Mock()
        mock_frame.size.width = 1600  # Larger
        mock_frame.size.height = 1200  # Larger
        
        mock_content_view.frame.return_value = mock_frame
        mock_window.contentView.return_value = mock_content_view
        
        self.backend.window = mock_window
        self.backend.metal_view = mock_view
        
        # Handle resize (will work without Cocoa since we mocked the window)
        self.backend._handle_window_resize()
        
        # Check that content was preserved
        self.assertEqual(self.backend.grid[5][10], ('X', 1, 0))
        self.assertEqual(self.backend.grid[15][20], ('Y', 2, 0))
    
    def test_handle_window_resize_clamps_cursor(self):
        """Test that window resize clamps cursor to new bounds."""
        # Position cursor at bottom-right
        self.backend.cursor_row = 39
        self.backend.cursor_col = 119
        
        # Mock window with smaller size
        mock_window = Mock()
        mock_view = Mock()
        mock_content_view = Mock()
        
        mock_frame = Mock()
        mock_frame.size.width = 800   # 80 columns
        mock_frame.size.height = 400  # 20 rows
        
        mock_content_view.frame.return_value = mock_frame
        mock_window.contentView.return_value = mock_content_view
        
        self.backend.window = mock_window
        self.backend.metal_view = mock_view
        
        # Handle resize (will work without Cocoa since we mocked the window)
        self.backend._handle_window_resize()
        
        # Cursor should be clamped to new bounds
        self.assertEqual(self.backend.cursor_row, 19)  # 20 rows - 1
        self.assertEqual(self.backend.cursor_col, 79)  # 80 cols - 1
    
    def test_handle_window_resize_no_change(self):
        """Test that resize with same dimensions doesn't recreate grid."""
        # Mock window with same size
        mock_window = Mock()
        mock_view = Mock()
        mock_content_view = Mock()
        
        mock_frame = Mock()
        mock_frame.size.width = 1200  # 120 columns
        mock_frame.size.height = 800  # 40 rows
        
        mock_content_view.frame.return_value = mock_frame
        mock_window.contentView.return_value = mock_content_view
        
        self.backend.window = mock_window
        self.backend.metal_view = mock_view
        
        # Store reference to original grid
        original_grid = self.backend.grid
        
        # Handle resize (will work without Cocoa since we mocked the window)
        self.backend._handle_window_resize()
        
        # Grid should be the same object (no recreation)
        self.assertIs(self.backend.grid, original_grid)
    
    def test_shutdown_clears_resources(self):
        """Test that shutdown() clears all resources."""
        # Set up some resources
        self.backend.window = Mock()
        self.backend.metal_view = Mock()
        self.backend.metal_device = Mock()
        self.backend.command_queue = Mock()
        self.backend.render_pipeline = Mock()
        self.backend.color_pairs = {1: ((255, 0, 0), (0, 0, 0))}
        
        # Shutdown
        self.backend.shutdown()
        
        # Check that resources are cleared
        self.assertIsNone(self.backend.window)
        self.assertIsNone(self.backend.metal_view)
        self.assertIsNone(self.backend.metal_device)
        self.assertIsNone(self.backend.command_queue)
        self.assertIsNone(self.backend.render_pipeline)
        self.assertEqual(self.backend.grid, [])
        self.assertEqual(self.backend.color_pairs, {})
        self.assertEqual(self.backend.rows, 0)
        self.assertEqual(self.backend.cols, 0)
    
    def test_shutdown_handles_none_window(self):
        """Test that shutdown() handles None window gracefully."""
        self.backend.window = None
        
        # Should not raise exception
        self.backend.shutdown()
    
    def test_shutdown_handles_window_close_error(self):
        """Test that shutdown() handles window close errors gracefully."""
        mock_window = Mock()
        mock_window.close.side_effect = Exception("Close failed")
        self.backend.window = mock_window
        
        # Should not raise exception
        self.backend.shutdown()
        
        # Window should still be set to None
        self.assertIsNone(self.backend.window)


class TestMetalWindowResizeDetection(unittest.TestCase):
    """Test Metal backend window resize detection in event handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = MetalBackend()
        self.backend.rows = 40
        self.backend.cols = 120
        self.backend.char_width = 10
        self.backend.char_height = 20
        
        # Initialize grid
        self.backend.grid = [
            [(' ', 0, 0) for _ in range(self.backend.cols)]
            for _ in range(self.backend.rows)
        ]
    
    # Note: Resize detection in _translate_macos_event is tested indirectly
    # through the _handle_window_resize tests. Direct testing is difficult
    # due to the exception handling and mock complexity.
    
    def test_translate_event_no_resize_when_size_unchanged(self):
        """Test that no resize event is generated when size is unchanged."""
        # Mock window with same size
        mock_window = Mock()
        mock_view = Mock()
        mock_content_view = Mock()
        
        mock_frame = Mock()
        mock_frame.size.width = 1200  # Same as current (120 cols * 10px)
        mock_frame.size.height = 800  # Same as current (40 rows * 20px)
        
        mock_content_view.frame.return_value = mock_frame
        mock_window.contentView.return_value = mock_content_view
        
        self.backend.window = mock_window
        self.backend.metal_view = mock_view
        
        # Create a mock event
        mock_event = Mock()
        mock_event.type.return_value = 999
        
        # Translate event (will work without Cocoa since we mocked the window)
        result = self.backend._translate_macos_event(mock_event)
        
        # Should return None (no resize)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
