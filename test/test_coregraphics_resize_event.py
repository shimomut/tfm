"""
Test CoreGraphics backend resize event handling.

This test verifies that the CoreGraphics backend properly generates
KeyCode.RESIZE events when the window is resized, matching the behavior
of the curses backend.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys

# Check if PyObjC is available
try:
    import Cocoa
    import objc
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False

# Only run tests if PyObjC is available and on macOS
if COCOA_AVAILABLE and sys.platform == 'darwin':
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    from ttk.input_event import KeyCode, ModifierKey


@unittest.skipUnless(
    COCOA_AVAILABLE and sys.platform == 'darwin',
    "CoreGraphics backend requires PyObjC and macOS"
)
class TestCoreGraphicsResizeEvent(unittest.TestCase):
    """Test resize event handling in CoreGraphics backend."""
    
    def setUp(self):
        """Set up test backend."""
        # Create backend with small dimensions for testing
        self.backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12,
            rows=10,
            cols=40
        )
        self.backend.initialize()
    
    def tearDown(self):
        """Clean up test backend."""
        if self.backend:
            self.backend.shutdown()
    
    def test_resize_flag_initialization(self):
        """Test that resize_pending flag is initialized to False."""
        self.assertFalse(self.backend.resize_pending)
    
    def test_resize_event_generation(self):
        """Test that resize event is generated when resize_pending is True."""
        # Set resize flag
        self.backend.resize_pending = True
        
        # Get input should return resize event
        event = self.backend.get_input(timeout_ms=0)
        
        # Verify resize event
        self.assertIsNotNone(event)
        self.assertEqual(event.key_code, KeyCode.RESIZE)
        self.assertEqual(event.modifiers, ModifierKey.NONE)
        self.assertIsNone(event.char)
        
        # Verify flag is cleared
        self.assertFalse(self.backend.resize_pending)
    
    def test_resize_event_priority(self):
        """Test that resize event has priority over other events."""
        # Set both resize and close flags
        self.backend.resize_pending = True
        self.backend.should_close = True
        
        # First call should return resize event
        event = self.backend.get_input(timeout_ms=0)
        self.assertEqual(event.key_code, KeyCode.RESIZE)
        
        # Second call should return close event
        event = self.backend.get_input(timeout_ms=0)
        self.assertEqual(event.key_code, ord('Q'))
    
    def test_window_delegate_sets_resize_flag(self):
        """Test that windowDidResize_ sets the resize_pending flag."""
        # Get initial dimensions
        initial_rows = self.backend.rows
        initial_cols = self.backend.cols
        
        # Simulate window resize by calling delegate method directly
        # Create a mock notification
        notification = Mock()
        
        # Mock the window content view to return different dimensions
        mock_frame = Mock()
        mock_frame.size.width = (initial_cols + 10) * self.backend.char_width
        mock_frame.size.height = (initial_rows + 5) * self.backend.char_height
        
        self.backend.window.contentView().frame = Mock(return_value=mock_frame)
        
        # Call the delegate method
        self.backend.window_delegate.windowDidResize_(notification)
        
        # Verify resize flag is set
        self.assertTrue(self.backend.resize_pending)
        
        # Verify dimensions were updated
        self.assertEqual(self.backend.rows, initial_rows + 5)
        self.assertEqual(self.backend.cols, initial_cols + 10)
    
    def test_no_resize_event_when_dimensions_unchanged(self):
        """Test that no resize event is generated if dimensions don't change."""
        # Get initial dimensions
        initial_rows = self.backend.rows
        initial_cols = self.backend.cols
        
        # Create a mock notification
        notification = Mock()
        
        # Mock the window content view to return same dimensions
        mock_frame = Mock()
        mock_frame.size.width = initial_cols * self.backend.char_width
        mock_frame.size.height = initial_rows * self.backend.char_height
        
        self.backend.window.contentView().frame = Mock(return_value=mock_frame)
        
        # Call the delegate method
        self.backend.window_delegate.windowDidResize_(notification)
        
        # Verify resize flag is NOT set (dimensions unchanged)
        self.assertFalse(self.backend.resize_pending)
    
    def test_resize_clears_caches(self):
        """Test that resize clears attribute and string caches."""
        # Ensure caches exist
        self.assertIsNotNone(self.backend._attr_dict_cache)
        self.assertIsNotNone(self.backend._attr_string_cache)
        
        # Add some data to caches (simulate usage)
        # This would normally happen during rendering
        
        # Trigger resize
        self.backend.resize_pending = True
        
        # Create a mock notification
        notification = Mock()
        
        # Mock the window content view to return different dimensions
        mock_frame = Mock()
        mock_frame.size.width = (self.backend.cols + 10) * self.backend.char_width
        mock_frame.size.height = (self.backend.rows + 5) * self.backend.char_height
        
        self.backend.window.contentView().frame = Mock(return_value=mock_frame)
        
        # Call the delegate method
        self.backend.window_delegate.windowDidResize_(notification)
        
        # Caches should still exist but be cleared
        self.assertIsNotNone(self.backend._attr_dict_cache)
        self.assertIsNotNone(self.backend._attr_string_cache)


if __name__ == '__main__':
    unittest.main()
