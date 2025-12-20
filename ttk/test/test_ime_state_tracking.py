"""
Test IME state tracking in TTKView.

This test verifies that the IME state tracking instance variables are properly
initialized in the TTKView.initWithFrame_backend_ method.

Requirements tested:
- 3.2: NSTextInputClient protocol implementation (marked text tracking)
- 3.3: NSTextInputClient protocol implementation (selected range tracking)
- 5.1: IME state tracking per text field
"""

import unittest
from unittest.mock import Mock, MagicMock

# Check if PyObjC is available
try:
    import Cocoa
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False


@unittest.skipUnless(COCOA_AVAILABLE, "PyObjC not available")
class TestIMEStateTracking(unittest.TestCase):
    """Test IME state tracking initialization in TTKView."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to avoid import errors when PyObjC is not available
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        
        # Create a mock backend
        self.backend = Mock(spec=CoreGraphicsBackend)
        self.backend.rows = 24
        self.backend.cols = 80
        self.backend.char_width = 10.0
        self.backend.char_height = 20.0
        self.backend.grid = [[(' ', 0, 0) for _ in range(80)] for _ in range(24)]
        self.backend.color_pairs = {0: ((255, 255, 255), (0, 0, 0))}
        self.backend.font = Cocoa.NSFont.monospacedSystemFontOfSize_weight_(12.0, 0.0)
    
    def test_ime_state_variables_initialized(self):
        """Test that IME state variables are initialized in initWithFrame_backend_."""
        from ttk.backends.coregraphics_backend import TTKView
        
        # Create a frame for the view
        frame = Cocoa.NSMakeRect(0, 0, 800, 480)
        
        # Create TTKView instance
        view = TTKView.alloc().initWithFrame_backend_(frame, self.backend)
        
        # Verify IME state variables are initialized
        self.assertIsNotNone(view, "View should be initialized")
        self.assertTrue(hasattr(view, 'marked_text'), "View should have marked_text attribute")
        self.assertTrue(hasattr(view, 'marked_range'), "View should have marked_range attribute")
        self.assertTrue(hasattr(view, 'selected_range'), "View should have selected_range attribute")
    
    def test_marked_text_initialized_to_empty_string(self):
        """Test that marked_text is initialized to empty string."""
        from ttk.backends.coregraphics_backend import TTKView
        
        frame = Cocoa.NSMakeRect(0, 0, 800, 480)
        view = TTKView.alloc().initWithFrame_backend_(frame, self.backend)
        
        self.assertEqual(view.marked_text, "", "marked_text should be initialized to empty string")
    
    def test_marked_range_initialized_with_nsnotfound(self):
        """Test that marked_range is initialized with NSNotFound location."""
        from ttk.backends.coregraphics_backend import TTKView
        
        frame = Cocoa.NSMakeRect(0, 0, 800, 480)
        view = TTKView.alloc().initWithFrame_backend_(frame, self.backend)
        
        # Verify marked_range has NSNotFound location
        self.assertEqual(view.marked_range.location, Cocoa.NSNotFound,
                        "marked_range location should be NSNotFound")
        self.assertEqual(view.marked_range.length, 0,
                        "marked_range length should be 0")
    
    def test_selected_range_initialized_as_zero_length(self):
        """Test that selected_range is initialized as zero-length range."""
        from ttk.backends.coregraphics_backend import TTKView
        
        frame = Cocoa.NSMakeRect(0, 0, 800, 480)
        view = TTKView.alloc().initWithFrame_backend_(frame, self.backend)
        
        # Verify selected_range is zero-length at position 0
        self.assertEqual(view.selected_range.location, 0,
                        "selected_range location should be 0")
        self.assertEqual(view.selected_range.length, 0,
                        "selected_range length should be 0")
    
    def test_backend_reference_preserved(self):
        """Test that backend reference is still properly stored."""
        from ttk.backends.coregraphics_backend import TTKView
        
        frame = Cocoa.NSMakeRect(0, 0, 800, 480)
        view = TTKView.alloc().initWithFrame_backend_(frame, self.backend)
        
        # Verify backend reference is preserved
        self.assertIs(view.backend, self.backend,
                     "View should store reference to backend")


if __name__ == '__main__':
    unittest.main()
