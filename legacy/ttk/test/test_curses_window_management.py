"""
Unit tests for TTK CursesBackend window management.

This module tests the window management functionality of the CursesBackend,
including dimension queries, cursor control, and resize event handling.
"""

import curses
import unittest
from unittest.mock import Mock, patch, MagicMock

from ttk.backends.curses_backend import CursesBackend
from ttk.input_event import KeyCode


class TestCursesWindowManagement(unittest.TestCase):
    """Test cases for CursesBackend window management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = CursesBackend()
        # Mock the stdscr to avoid actual curses initialization
        self.backend.stdscr = Mock()
    
    def test_get_dimensions_returns_tuple(self):
        """Test that get_dimensions returns a tuple of two integers."""
        # Mock getmaxyx to return dimensions
        self.backend.stdscr.getmaxyx.return_value = (24, 80)
        
        dimensions = self.backend.get_dimensions()
        
        # Verify it's a tuple
        self.assertIsInstance(dimensions, tuple)
        self.assertEqual(len(dimensions), 2)
        
        # Verify values
        rows, cols = dimensions
        self.assertEqual(rows, 24)
        self.assertEqual(cols, 80)
    
    def test_get_dimensions_various_sizes(self):
        """Test get_dimensions with various terminal sizes."""
        test_sizes = [
            (24, 80),   # Standard terminal
            (40, 120),  # Larger terminal
            (10, 40),   # Small terminal
            (100, 200), # Very large terminal
            (1, 1),     # Minimal size
        ]
        
        for expected_rows, expected_cols in test_sizes:
            self.backend.stdscr.getmaxyx.return_value = (expected_rows, expected_cols)
            
            rows, cols = self.backend.get_dimensions()
            
            self.assertEqual(rows, expected_rows)
            self.assertEqual(cols, expected_cols)
    
    def test_set_cursor_visibility_show(self):
        """Test setting cursor visibility to visible."""
        self.backend.set_cursor_visibility(True)
        
        # Verify curses.curs_set was called with 1 (visible)
        # We need to patch curses.curs_set for this test
        with patch('curses.curs_set') as mock_curs_set:
            self.backend.set_cursor_visibility(True)
            mock_curs_set.assert_called_once_with(1)
    
    def test_set_cursor_visibility_hide(self):
        """Test setting cursor visibility to hidden."""
        with patch('curses.curs_set') as mock_curs_set:
            self.backend.set_cursor_visibility(False)
            mock_curs_set.assert_called_once_with(0)
    
    def test_set_cursor_visibility_handles_error(self):
        """Test that set_cursor_visibility handles curses.error gracefully."""
        with patch('curses.curs_set', side_effect=curses.error):
            # Should not raise an exception
            try:
                self.backend.set_cursor_visibility(True)
                self.backend.set_cursor_visibility(False)
            except curses.error:
                self.fail("set_cursor_visibility should handle curses.error gracefully")
    
    def test_move_cursor_valid_position(self):
        """Test moving cursor to valid positions."""
        test_positions = [
            (0, 0),      # Top-left corner
            (10, 20),    # Middle position
            (23, 79),    # Near bottom-right
            (5, 0),      # Left edge
            (0, 40),     # Top edge
        ]
        
        for row, col in test_positions:
            self.backend.move_cursor(row, col)
            
            # Verify stdscr.move was called with correct arguments
            self.backend.stdscr.move.assert_called_with(row, col)
    
    def test_move_cursor_handles_out_of_bounds(self):
        """Test that move_cursor handles out-of-bounds positions gracefully."""
        # Mock move to raise curses.error for out-of-bounds
        self.backend.stdscr.move.side_effect = curses.error
        
        # Should not raise an exception
        try:
            self.backend.move_cursor(100, 200)  # Way out of bounds
            self.backend.move_cursor(-1, -1)    # Negative coordinates
        except curses.error:
            self.fail("move_cursor should handle curses.error gracefully")
    
    def test_move_cursor_multiple_calls(self):
        """Test multiple cursor movements."""
        positions = [(0, 0), (5, 10), (15, 30), (20, 50)]
        
        for row, col in positions:
            self.backend.stdscr.move.reset_mock()
            self.backend.move_cursor(row, col)
            self.backend.stdscr.move.assert_called_once_with(row, col)
    
    def test_resize_event_handling(self):
        """Test that KEY_RESIZE is properly translated to KeyCode.RESIZE."""
        # This is tested in input handling, but verify it's available
        event = self.backend._translate_curses_key(curses.KEY_RESIZE)
        
        self.assertEqual(event.key_code, KeyCode.RESIZE)
        self.assertIsNone(event.char)
    
    def test_dimensions_after_resize(self):
        """Test that get_dimensions returns updated values after resize."""
        # Initial size
        self.backend.stdscr.getmaxyx.return_value = (24, 80)
        rows, cols = self.backend.get_dimensions()
        self.assertEqual((rows, cols), (24, 80))
        
        # Simulate resize
        self.backend.stdscr.getmaxyx.return_value = (40, 120)
        rows, cols = self.backend.get_dimensions()
        self.assertEqual((rows, cols), (40, 120))
        
        # Another resize
        self.backend.stdscr.getmaxyx.return_value = (30, 100)
        rows, cols = self.backend.get_dimensions()
        self.assertEqual((rows, cols), (30, 100))
    
    def test_cursor_operations_sequence(self):
        """Test a sequence of cursor operations."""
        # Hide cursor
        with patch('curses.curs_set') as mock_curs_set:
            self.backend.set_cursor_visibility(False)
            mock_curs_set.assert_called_with(0)
        
        # Move cursor
        self.backend.move_cursor(10, 20)
        self.backend.stdscr.move.assert_called_with(10, 20)
        
        # Show cursor
        with patch('curses.curs_set') as mock_curs_set:
            self.backend.set_cursor_visibility(True)
            mock_curs_set.assert_called_with(1)
        
        # Move cursor again
        self.backend.move_cursor(5, 15)
        self.backend.stdscr.move.assert_called_with(5, 15)
    
    def test_window_management_integration(self):
        """Test integration of window management features."""
        # Set up mock dimensions
        self.backend.stdscr.getmaxyx.return_value = (30, 100)
        
        # Get dimensions
        rows, cols = self.backend.get_dimensions()
        self.assertEqual(rows, 30)
        self.assertEqual(cols, 100)
        
        # Move cursor to center
        center_row = rows // 2
        center_col = cols // 2
        self.backend.move_cursor(center_row, center_col)
        self.backend.stdscr.move.assert_called_with(center_row, center_col)
        
        # Hide cursor
        with patch('curses.curs_set') as mock_curs_set:
            self.backend.set_cursor_visibility(False)
            mock_curs_set.assert_called_with(0)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
