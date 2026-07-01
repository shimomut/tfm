"""
Test CoreGraphics backend display refresh operations.

This test verifies that the display refresh operations work correctly:
- refresh() marks the entire view for redraw
- refresh_region() marks a specific region for redraw
- View is properly connected to window
- Window is shown with makeKeyAndOrderFront_

Requirements tested: 8.4, 10.3
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import sys


class TestCoreGraphicsDisplayRefresh(unittest.TestCase):
    """Test display refresh operations in CoreGraphics backend."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the Cocoa module
        self.cocoa_mock = MagicMock()
        self.quartz_mock = MagicMock()
        self.objc_mock = MagicMock()
        
        # Set up module mocks
        sys.modules['Cocoa'] = self.cocoa_mock
        sys.modules['Quartz'] = self.quartz_mock
        sys.modules['objc'] = self.objc_mock
        
        # Mock NSFont
        self.mock_font = MagicMock()
        self.cocoa_mock.NSFont.fontWithName_size_.return_value = self.mock_font
        
        # Mock NSAttributedString for character dimension calculation
        self.mock_attr_string = MagicMock()
        self.mock_size = MagicMock()
        self.mock_size.width = 10.0
        self.mock_size.height = 20.0
        self.mock_attr_string.size.return_value = self.mock_size
        self.cocoa_mock.NSAttributedString.alloc.return_value.initWithString_attributes_.return_value = self.mock_attr_string
        
        # Mock NSWindow
        self.mock_window = MagicMock()
        self.mock_content_view = MagicMock()
        self.mock_content_view.frame.return_value = MagicMock()
        self.mock_window.contentView.return_value = self.mock_content_view
        self.cocoa_mock.NSWindow.alloc.return_value.initWithContentRect_styleMask_backing_defer_.return_value = self.mock_window
        
        # Mock TTKView
        self.mock_view = MagicMock()
        self.mock_view_instance = MagicMock()
        self.mock_view.alloc.return_value.initWithFrame_backend_.return_value = self.mock_view_instance
        
        # Mock objc.lookUpClass to raise nosuchclass_error
        self.objc_mock.nosuchclass_error = type('nosuchclass_error', (Exception,), {})
        self.objc_mock.lookUpClass.side_effect = self.objc_mock.nosuchclass_error
        
        # Mock NSMakeRect
        self.cocoa_mock.NSMakeRect = MagicMock(return_value=MagicMock())
        
        # Import backend after mocking
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        self.CoreGraphicsBackend = CoreGraphicsBackend
        
        # Patch TTKView in the backend module
        import ttk.backends.coregraphics_backend as backend_module
        backend_module.TTKView = self.mock_view
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove mocked modules
        if 'Cocoa' in sys.modules:
            del sys.modules['Cocoa']
        if 'Quartz' in sys.modules:
            del sys.modules['Quartz']
        if 'objc' in sys.modules:
            del sys.modules['objc']
        if 'ttk.backends.coregraphics_backend' in sys.modules:
            del sys.modules['ttk.backends.coregraphics_backend']
    
    def test_refresh_marks_entire_view_for_display(self):
        """Test that refresh() marks the entire view as needing display."""
        # Create backend
        backend = self.CoreGraphicsBackend()
        
        # Mock the view
        backend.view = MagicMock()
        
        # Call refresh
        backend.refresh()
        
        # Verify setNeedsDisplay_ was called with True
        backend.view.setNeedsDisplay_.assert_called_once_with(True)
    
    def test_refresh_handles_no_view(self):
        """Test that refresh() handles the case when view is None."""
        # Create backend
        backend = self.CoreGraphicsBackend()
        
        # Set view to None
        backend.view = None
        
        # Call refresh - should not raise an exception
        try:
            backend.refresh()
        except Exception as e:
            self.fail(f"refresh() raised exception with None view: {e}")
    
    def test_refresh_region_marks_specific_region(self):
        """Test that refresh_region() marks a specific region for redraw."""
        # Create backend
        backend = self.CoreGraphicsBackend()
        backend.rows = 24
        backend.cols = 80
        backend.char_width = 10
        backend.char_height = 20
        
        # Mock the view
        backend.view = MagicMock()
        
        # Call refresh_region for a 5x10 region starting at (2, 3)
        backend.refresh_region(2, 3, 5, 10)
        
        # Verify setNeedsDisplayInRect_ was called
        backend.view.setNeedsDisplayInRect_.assert_called_once()
        
        # Get the call arguments
        call_args = backend.view.setNeedsDisplayInRect_.call_args
        
        # Verify NSMakeRect was called with correct parameters
        # x = col * char_width = 3 * 10 = 30
        # y = (rows - row - height) * char_height = (24 - 2 - 5) * 20 = 17 * 20 = 340
        # width = width * char_width = 10 * 10 = 100
        # height = height * char_height = 5 * 20 = 100
        self.cocoa_mock.NSMakeRect.assert_called_with(30, 340, 100, 100)
    
    def test_refresh_region_handles_no_view(self):
        """Test that refresh_region() handles the case when view is None."""
        # Create backend
        backend = self.CoreGraphicsBackend()
        backend.rows = 24
        backend.cols = 80
        backend.char_width = 10
        backend.char_height = 20
        
        # Set view to None
        backend.view = None
        
        # Call refresh_region - should not raise an exception
        try:
            backend.refresh_region(0, 0, 5, 10)
        except Exception as e:
            self.fail(f"refresh_region() raised exception with None view: {e}")
    
    def test_view_connected_to_window_during_initialization(self):
        """Test that view is connected to window as content view during initialization."""
        # Create backend
        backend = self.CoreGraphicsBackend()
        
        # Initialize
        backend.initialize()
        
        # Verify setContentView_ was called on the window
        self.mock_window.setContentView_.assert_called_once()
    
    def test_window_shown_during_initialization(self):
        """Test that window is shown with makeKeyAndOrderFront_ during initialization."""
        # Create backend
        backend = self.CoreGraphicsBackend()
        
        # Initialize
        backend.initialize()
        
        # Verify makeKeyAndOrderFront_ was called on the window
        self.mock_window.makeKeyAndOrderFront_.assert_called_once_with(None)
    
    def test_refresh_region_calculates_correct_coordinates(self):
        """Test that refresh_region() calculates pixel coordinates correctly."""
        # Create backend with specific dimensions
        backend = self.CoreGraphicsBackend()
        backend.rows = 30
        backend.cols = 100
        backend.char_width = 8
        backend.char_height = 16
        backend.view = MagicMock()
        
        # Test various regions
        test_cases = [
            # (row, col, height, width, expected_x, expected_y, expected_width, expected_height)
            (0, 0, 1, 1, 0, 464, 8, 16),  # Top-left corner: y = (30-0-1)*16 = 464
            (29, 99, 1, 1, 792, 0, 8, 16),  # Bottom-right corner: y = (30-29-1)*16 = 0
            (10, 20, 5, 10, 160, 240, 80, 80),  # Middle region: y = (30-10-5)*16 = 240
        ]
        
        for row, col, height, width, exp_x, exp_y, exp_w, exp_h in test_cases:
            # Reset mock
            self.cocoa_mock.NSMakeRect.reset_mock()
            
            # Call refresh_region
            backend.refresh_region(row, col, height, width)
            
            # Verify NSMakeRect was called with correct parameters
            self.cocoa_mock.NSMakeRect.assert_called_once_with(exp_x, exp_y, exp_w, exp_h)


if __name__ == '__main__':
    unittest.main()
