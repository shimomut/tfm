"""
Test suite for CoreGraphics backend shutdown functionality.

This module tests the shutdown() method of the CoreGraphics backend to ensure
proper resource cleanup and error handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock PyObjC modules before importing the backend
sys.modules['Cocoa'] = MagicMock()
sys.modules['Quartz'] = MagicMock()
sys.modules['objc'] = MagicMock()

from ttk.backends.coregraphics_backend import CoreGraphicsBackend


class TestCoreGraphicsShutdown(unittest.TestCase):
    """Test suite for CoreGraphics backend shutdown functionality."""
    
    def test_shutdown_closes_window(self):
        """Test that shutdown closes the native window."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Mock the window
        mock_window = Mock()
        backend.window = mock_window
        
        # Call shutdown
        backend.shutdown()
        
        # Verify window.close() was called
        mock_window.close.assert_called_once()
        
        # Verify window reference is cleared
        assert backend.window is None
    
    def test_shutdown_handles_window_close_error(self):
        """Test that shutdown handles errors when closing window."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Mock window that raises RuntimeError on close
        mock_window = Mock()
        mock_window.close.side_effect = RuntimeError("Window already closed")
        backend.window = mock_window
        
        # Shutdown should not raise exception
        backend.shutdown()
        
        # Verify window reference is still cleared despite error
        assert backend.window is None
    
    def test_shutdown_handles_attribute_error(self):
        """Test that shutdown handles AttributeError during window close."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Mock window that raises AttributeError on close
        mock_window = Mock()
        mock_window.close.side_effect = AttributeError("No close method")
        backend.window = mock_window
        
        # Shutdown should not raise exception
        backend.shutdown()
        
        # Verify window reference is cleared
        assert backend.window is None
    
    def test_shutdown_clears_view(self):
        """Test that shutdown clears view reference."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Set up view
        backend.view = Mock()
        
        # Call shutdown
        backend.shutdown()
        
        # Verify view is cleared
        assert backend.view is None
    
    def test_shutdown_clears_font(self):
        """Test that shutdown clears the font reference."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Set up font
        backend.font = Mock()
        
        # Call shutdown
        backend.shutdown()
        
        # Verify font is cleared
        assert backend.font is None
    
    def test_shutdown_clears_character_grid(self):
        """Test that shutdown clears the character grid."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Set up grid with some data
        backend.grid = [
            [('A', 1, 0), ('B', 1, 0)],
            [('C', 1, 0), ('D', 1, 0)]
        ]
        
        # Call shutdown
        backend.shutdown()
        
        # Verify grid is cleared
        assert backend.grid == []
    
    def test_shutdown_clears_color_pairs(self):
        """Test that shutdown clears color pair storage."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Set up color pairs
        backend.color_pairs = {
            0: ((255, 255, 255), (0, 0, 0)),
            1: ((255, 0, 0), (0, 0, 255)),
            2: ((0, 255, 0), (255, 255, 0))
        }
        
        # Call shutdown
        backend.shutdown()
        
        # Verify color pairs are cleared
        assert backend.color_pairs == {}
    
    def test_shutdown_resets_dimensions(self):
        """Test that shutdown resets dimension values."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Set up dimensions
        backend.rows = 40
        backend.cols = 120
        backend.char_width = 10
        backend.char_height = 20
        
        # Call shutdown
        backend.shutdown()
        
        # Verify dimensions are reset
        assert backend.rows == 0
        assert backend.cols == 0
        assert backend.char_width == 0
        assert backend.char_height == 0
    
    def test_shutdown_resets_cursor_state(self):
        """Test that shutdown resets cursor state."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Set up cursor state
        backend.cursor_visible = True
        backend.cursor_row = 10
        backend.cursor_col = 20
        
        # Call shutdown
        backend.shutdown()
        
        # Verify cursor state is reset
        assert backend.cursor_visible is False
        assert backend.cursor_row == 0
        assert backend.cursor_col == 0
    
    def test_shutdown_without_initialization(self):
        """Test that shutdown works even if initialize() was never called."""
        backend = CoreGraphicsBackend()
        
        # Shutdown should not raise exception
        backend.shutdown()
        
        # Verify all resources are cleared
        assert backend.window is None
        assert backend.view is None
        assert backend.font is None
        assert backend.grid == []
        assert backend.color_pairs == {}
        assert backend.rows == 0
        assert backend.cols == 0
    
    def test_shutdown_multiple_times(self):
        """Test that shutdown can be called multiple times safely."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Set up some resources
        backend.window = Mock()
        backend.view = Mock()
        backend.grid = [[(char, 0, 0) for char in "test"]]
        
        # Call shutdown multiple times
        backend.shutdown()
        backend.shutdown()
        backend.shutdown()
        
        # Verify resources remain cleared
        assert backend.window is None
        assert backend.view is None
        assert backend.grid == []
    
    def test_shutdown_clears_all_resources_together(self):
        """Test that shutdown clears all resources in one call."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Set up all resources
        backend.window = Mock()
        backend.view = Mock()
        backend.font = Mock()
        backend.grid = [[('X', 1, 0)]]
        backend.color_pairs = {1: ((255, 0, 0), (0, 0, 255))}
        backend.rows = 24
        backend.cols = 80
        backend.char_width = 10
        backend.char_height = 20
        backend.cursor_visible = True
        backend.cursor_row = 5
        backend.cursor_col = 10
        
        # Call shutdown once
        backend.shutdown()
        
        # Verify all resources are cleared
        assert backend.window is None
        assert backend.view is None
        assert backend.font is None
        assert backend.grid == []
        assert backend.color_pairs == {}
        assert backend.rows == 0
        assert backend.cols == 0
        assert backend.char_width == 0
        assert backend.char_height == 0
        assert backend.cursor_visible is False
        assert backend.cursor_row == 0
        assert backend.cursor_col == 0
    
    def test_shutdown_with_partial_initialization(self):
        """Test shutdown when only some resources were initialized."""
        backend = CoreGraphicsBackend()
        
        # Partially initialize - set only some resources
        backend.window = Mock()
        backend.grid = [[('A', 0, 0)]]
        backend.rows = 24
        # Leave other resources uninitialized
        
        # Shutdown should not raise exception
        backend.shutdown()
        
        # Verify all resources are cleared
        assert backend.window is None
        assert backend.grid == []
        assert backend.rows == 0
    
    def test_shutdown_preserves_configuration(self):
        """Test that shutdown preserves initial configuration parameters."""
        backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Monaco",
            font_size=16,
            rows=40,
            cols=120
        )
        backend.initialize()
        
        # Call shutdown
        backend.shutdown()
        
        # Verify configuration parameters are preserved
        assert backend.window_title == "Test Window"
        assert backend.font_name == "Monaco"
        assert backend.font_size == 16
    
    def test_shutdown_handles_unexpected_exception(self):
        """Test that shutdown handles unexpected exceptions during cleanup."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Mock window that raises unexpected exception
        mock_window = Mock()
        mock_window.close.side_effect = ValueError("Unexpected error")
        backend.window = mock_window
        
        # Shutdown should not raise exception
        backend.shutdown()
        
        # Verify window reference is still cleared
        assert backend.window is None
        
        # Verify other resources are also cleared
        assert backend.view is None
        assert backend.grid == []


if __name__ == '__main__':
    unittest.main()
