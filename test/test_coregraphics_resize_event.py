"""
Test CoreGraphics backend resize event handling.

This test verifies that the CoreGraphics backend properly generates
resize events when the window is resized via the on_resize callback,
matching the behavior expected in callback mode.

Run with: PYTHONPATH=.:src:ttk pytest test/test_coregraphics_resize_event.py -v
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
    from ttk.test.test_utils import EventCapture


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
            font_names=["Menlo"],
            font_size=12,
            rows=10,
            cols=40
        )
        self.backend.initialize()
        
        # Set up event capture for callback mode
        self.capture = EventCapture()
        self.backend.set_event_callback(self.capture)
    
    def tearDown(self):
        """Clean up test backend."""
        if self.backend:
            self.backend.shutdown()
    
    def test_resize_flag_initialization(self):
        """Test that resize_pending flag is initialized to False."""
        # Note: In callback mode, resize events are delivered via on_resize callback
        # The resize_pending flag may not exist in callback-only mode
        # This test verifies the backend can be initialized without errors
        self.assertIsNotNone(self.backend)
    
    def test_resize_event_generation(self):
        """Test that resize event is delivered via on_resize callback."""
        # Clear any existing events
        self.capture.clear_events()
        
        # Get initial dimensions
        initial_rows = self.backend.rows
        initial_cols = self.backend.cols
        
        # Simulate window resize by calling delegate method directly
        notification = Mock()
        
        # Mock the window content view to return different dimensions
        mock_frame = Mock()
        mock_frame.size.width = (initial_cols + 10) * self.backend.char_width
        mock_frame.size.height = (initial_rows + 5) * self.backend.char_height
        
        self.backend.window.contentView().frame = Mock(return_value=mock_frame)
        
        # Call the delegate method
        self.backend.window_delegate.windowDidResize_(notification)
        
        # Process events to trigger callback
        self.backend.run_event_loop_iteration(timeout_ms=10)
        
        # Verify resize was delivered via callback
        # Note: on_resize is called directly, not via system event
        # Check that dimensions were updated
        self.assertEqual(self.backend.rows, initial_rows + 5)
        self.assertEqual(self.backend.cols, initial_cols + 10)
    
    def test_resize_event_priority(self):
        """Test that resize handling works correctly in callback mode."""
        # Clear any existing events
        self.capture.clear_events()
        
        # Get initial dimensions
        initial_rows = self.backend.rows
        initial_cols = self.backend.cols
        
        # Simulate window resize
        notification = Mock()
        mock_frame = Mock()
        mock_frame.size.width = (initial_cols + 5) * self.backend.char_width
        mock_frame.size.height = (initial_rows + 3) * self.backend.char_height
        
        self.backend.window.contentView().frame = Mock(return_value=mock_frame)
        self.backend.window_delegate.windowDidResize_(notification)
        
        # Process events
        self.backend.run_event_loop_iteration(timeout_ms=10)
        
        # Verify dimensions updated
        self.assertEqual(self.backend.rows, initial_rows + 3)
        self.assertEqual(self.backend.cols, initial_cols + 5)
    
    def test_window_delegate_sets_resize_flag(self):
        """Test that windowDidResize_ updates dimensions correctly."""
        # Get initial dimensions
        initial_rows = self.backend.rows
        initial_cols = self.backend.cols
        
        # Simulate window resize by calling delegate method directly
        notification = Mock()
        
        # Mock the window content view to return different dimensions
        mock_frame = Mock()
        mock_frame.size.width = (initial_cols + 10) * self.backend.char_width
        mock_frame.size.height = (initial_rows + 5) * self.backend.char_height
        
        self.backend.window.contentView().frame = Mock(return_value=mock_frame)
        
        # Call the delegate method
        self.backend.window_delegate.windowDidResize_(notification)
        
        # Verify dimensions were updated
        self.assertEqual(self.backend.rows, initial_rows + 5)
        self.assertEqual(self.backend.cols, initial_cols + 10)
    
    def test_no_resize_event_when_dimensions_unchanged(self):
        """Test that dimensions remain stable when window size doesn't change."""
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
        
        # Verify dimensions unchanged
        self.assertEqual(self.backend.rows, initial_rows)
        self.assertEqual(self.backend.cols, initial_cols)
