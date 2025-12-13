"""
Unit tests for CoreGraphics backend cursor management.

Tests the cursor visibility and positioning functionality of the CoreGraphics
backend, ensuring proper state management and coordinate clamping.
"""

import sys
import unittest
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, '..')

# Mock PyObjC before importing the backend
sys.modules['objc'] = Mock()
sys.modules['Cocoa'] = Mock()
sys.modules['Quartz'] = Mock()

from ttk.backends.coregraphics_backend import CoreGraphicsBackend


class TestCoreGraphicsCursorManagement(unittest.TestCase):
    """Test cursor management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create backend instance
        self.backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12
        )
        
        # Mock the view
        self.backend.view = Mock()
        self.backend.rows = 24
        self.backend.cols = 80
    
    def test_cursor_initially_hidden(self):
        """Test that cursor is initially hidden."""
        self.assertFalse(self.backend.cursor_visible)
    
    def test_cursor_initial_position(self):
        """Test that cursor starts at position (0, 0)."""
        self.assertEqual(self.backend.cursor_row, 0)
        self.assertEqual(self.backend.cursor_col, 0)
    
    def test_set_cursor_visibility_show(self):
        """Test showing the cursor."""
        self.backend.set_cursor_visibility(True)
        self.assertTrue(self.backend.cursor_visible)
        # Verify view refresh was triggered
        self.backend.view.setNeedsDisplay_.assert_called_with(True)
    
    def test_set_cursor_visibility_hide(self):
        """Test hiding the cursor."""
        self.backend.cursor_visible = True
        self.backend.set_cursor_visibility(False)
        self.assertFalse(self.backend.cursor_visible)
        # Verify view refresh was triggered
        self.backend.view.setNeedsDisplay_.assert_called_with(True)
    
    def test_set_cursor_visibility_without_view(self):
        """Test that set_cursor_visibility handles missing view gracefully."""
        self.backend.view = None
        # Should not raise an exception
        self.backend.set_cursor_visibility(True)
        self.assertTrue(self.backend.cursor_visible)
    
    def test_move_cursor_valid_position(self):
        """Test moving cursor to a valid position."""
        self.backend.cursor_visible = True
        self.backend.move_cursor(10, 20)
        self.assertEqual(self.backend.cursor_row, 10)
        self.assertEqual(self.backend.cursor_col, 20)
        # Verify view refresh was triggered
        self.backend.view.setNeedsDisplay_.assert_called_with(True)
    
    def test_move_cursor_clamps_row_upper_bound(self):
        """Test that cursor row is clamped to grid bounds."""
        self.backend.move_cursor(100, 10)
        self.assertEqual(self.backend.cursor_row, 23)  # rows - 1
        self.assertEqual(self.backend.cursor_col, 10)
    
    def test_move_cursor_clamps_row_lower_bound(self):
        """Test that cursor row is clamped to zero."""
        self.backend.move_cursor(-5, 10)
        self.assertEqual(self.backend.cursor_row, 0)
        self.assertEqual(self.backend.cursor_col, 10)
    
    def test_move_cursor_clamps_col_upper_bound(self):
        """Test that cursor column is clamped to grid bounds."""
        self.backend.move_cursor(10, 200)
        self.assertEqual(self.backend.cursor_row, 10)
        self.assertEqual(self.backend.cursor_col, 79)  # cols - 1
    
    def test_move_cursor_clamps_col_lower_bound(self):
        """Test that cursor column is clamped to zero."""
        self.backend.move_cursor(10, -10)
        self.assertEqual(self.backend.cursor_row, 10)
        self.assertEqual(self.backend.cursor_col, 0)
    
    def test_move_cursor_clamps_both_bounds(self):
        """Test that both coordinates are clamped simultaneously."""
        self.backend.move_cursor(-5, 200)
        self.assertEqual(self.backend.cursor_row, 0)
        self.assertEqual(self.backend.cursor_col, 79)
    
    def test_move_cursor_hidden_no_refresh(self):
        """Test that moving hidden cursor doesn't trigger refresh."""
        self.backend.cursor_visible = False
        self.backend.view.reset_mock()
        self.backend.move_cursor(10, 20)
        # Verify view refresh was NOT triggered
        self.backend.view.setNeedsDisplay_.assert_not_called()
    
    def test_move_cursor_without_view(self):
        """Test that move_cursor handles missing view gracefully."""
        self.backend.view = None
        self.backend.cursor_visible = True
        # Should not raise an exception
        self.backend.move_cursor(10, 20)
        self.assertEqual(self.backend.cursor_row, 10)
        self.assertEqual(self.backend.cursor_col, 20)
    
    def test_cursor_state_persistence(self):
        """Test that cursor state persists across operations."""
        # Set cursor visible and move it
        self.backend.set_cursor_visibility(True)
        self.backend.move_cursor(5, 10)
        
        # Verify state persists
        self.assertTrue(self.backend.cursor_visible)
        self.assertEqual(self.backend.cursor_row, 5)
        self.assertEqual(self.backend.cursor_col, 10)
        
        # Hide cursor
        self.backend.set_cursor_visibility(False)
        
        # Position should still be preserved
        self.assertFalse(self.backend.cursor_visible)
        self.assertEqual(self.backend.cursor_row, 5)
        self.assertEqual(self.backend.cursor_col, 10)


if __name__ == '__main__':
    unittest.main()
