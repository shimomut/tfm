"""
Test error handling for window geometry persistence.

This test verifies that the CoreGraphics backend handles errors gracefully
when window geometry persistence operations fail.
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    import Cocoa
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False


class TestWindowGeometryErrorHandling(unittest.TestCase):
    """Test error handling for window geometry persistence operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not COCOA_AVAILABLE:
            self.skipTest("PyObjC not available")
    
    @patch('Cocoa.NSWindow')
    @patch('Cocoa.NSApplication')
    def test_frame_autosave_attribute_error(self, mock_app, mock_window_class):
        """Test that AttributeError during frame autosave setup is handled gracefully."""
        # Create a mock window that raises AttributeError on setFrameAutosaveName_
        mock_window = MagicMock()
        mock_window.setFrameAutosaveName_.side_effect = AttributeError("Method not available")
        mock_window_class.alloc.return_value.initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        # Mock other required methods
        mock_window.contentView.return_value.frame.return_value = Cocoa.NSMakeRect(0, 0, 800, 600)
        
        # Create backend - should not raise exception
        backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12,
            rows=24,
            cols=80
        )
        
        # Initialize should succeed despite frame autosave error
        try:
            backend.initialize()
            # If we get here, error was handled gracefully
            self.assertTrue(True, "Frame autosave error handled gracefully")
        except AttributeError:
            self.fail("AttributeError should have been caught and handled")
    
    @patch('Cocoa.NSWindow')
    @patch('Cocoa.NSApplication')
    def test_frame_autosave_type_error(self, mock_app, mock_window_class):
        """Test that TypeError during frame autosave setup is handled gracefully."""
        # Create a mock window that raises TypeError on setFrameAutosaveName_
        mock_window = MagicMock()
        mock_window.setFrameAutosaveName_.side_effect = TypeError("Invalid autosave name type")
        mock_window_class.alloc.return_value.initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        # Mock other required methods
        mock_window.contentView.return_value.frame.return_value = Cocoa.NSMakeRect(0, 0, 800, 600)
        
        # Create backend - should not raise exception
        backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12,
            rows=24,
            cols=80
        )
        
        # Initialize should succeed despite frame autosave error
        try:
            backend.initialize()
            # If we get here, error was handled gracefully
            self.assertTrue(True, "Frame autosave error handled gracefully")
        except TypeError:
            self.fail("TypeError should have been caught and handled")
    
    @patch('Cocoa.NSUserDefaults')
    def test_reset_nsuserdefaults_error(self, mock_defaults_class):
        """Test that errors during NSUserDefaults operations are handled gracefully."""
        if not COCOA_AVAILABLE:
            self.skipTest("PyObjC not available")
        
        # Create a mock NSUserDefaults that raises AttributeError
        mock_defaults = MagicMock()
        mock_defaults.removeObjectForKey_.side_effect = AttributeError("Method not available")
        mock_defaults_class.standardUserDefaults.return_value = mock_defaults
        
        # Create a minimal backend with mocked window
        backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12,
            rows=24,
            cols=80
        )
        
        # Mock the window object
        backend.window = MagicMock()
        backend.window.setFrame_display_ = MagicMock()
        
        # Reset should handle the error and continue
        result = backend.reset_window_geometry()
        
        # Should return True because frame application succeeded
        self.assertTrue(result, "Reset should succeed even if NSUserDefaults clearing fails")
    
    @patch('Cocoa.NSWindow')
    def test_reset_window_frame_error(self, mock_window_class):
        """Test that errors during window frame application are handled gracefully."""
        if not COCOA_AVAILABLE:
            self.skipTest("PyObjC not available")
        
        # Create backend with mocked window
        backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12,
            rows=24,
            cols=80
        )
        
        # Mock the window object to raise error on setFrame_display_
        backend.window = MagicMock()
        backend.window.setFrame_display_.side_effect = AttributeError("Method not available")
        
        # Reset should handle the error gracefully
        result = backend.reset_window_geometry()
        
        # Should return False because frame application failed
        self.assertFalse(result, "Reset should return False when frame application fails")
    
    def test_reset_without_window(self):
        """Test that reset handles missing window gracefully."""
        if not COCOA_AVAILABLE:
            self.skipTest("PyObjC not available")
        
        # Create backend without initializing
        backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12,
            rows=24,
            cols=80
        )
        
        # Window should be None
        self.assertIsNone(backend.window)
        
        # Reset should handle missing window gracefully
        result = backend.reset_window_geometry()
        
        # Should return False because window doesn't exist
        self.assertFalse(result, "Reset should return False when window is not initialized")


if __name__ == '__main__':
    unittest.main()
