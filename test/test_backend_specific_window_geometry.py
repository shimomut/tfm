"""
Test backend-specific behavior for window geometry persistence.

This test verifies that window geometry persistence is only enabled in the
CoreGraphics backend and that the curses backend is unaffected.

Run with: PYTHONPATH=.:src:ttk pytest test/test_backend_specific_window_geometry.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock, patch

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    import Cocoa
    COREGRAPHICS_AVAILABLE = True
except ImportError:
    COREGRAPHICS_AVAILABLE = False

try:
    from ttk.backends.curses_backend import CursesBackend
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False


class TestBackendSpecificWindowGeometry(unittest.TestCase):
    """Test that window geometry persistence is backend-specific."""
    
    @patch('Cocoa.NSWindow')
    @patch('Cocoa.NSApplication')
    def test_coregraphics_enables_frame_autosave(self, mock_app, mock_window_class):
        """Test that CoreGraphics backend enables frame autosave during initialization."""
        if not COREGRAPHICS_AVAILABLE:
            self.skipTest("CoreGraphics backend not available")
        
        # Create a mock window
        mock_window = MagicMock()
        mock_window_class.alloc.return_value.initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        # Mock other required methods
        mock_window.contentView.return_value.frame.return_value = Cocoa.NSMakeRect(0, 0, 800, 600)
        
        # Create and initialize backend
        backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_names=["Menlo"],
            font_size=12,
            rows=24,
            cols=80
        )
        backend.initialize()
        
        # Verify setFrameAutosaveName_ was called with the correct name
        mock_window.setFrameAutosaveName_.assert_called_once_with("TFMMainWindow")
    
    def test_curses_backend_has_no_window_geometry_methods(self):
        """Test that curses backend doesn't have window geometry methods."""
        if not CURSES_AVAILABLE:
            self.skipTest("Curses backend not available")
        
        # Create curses backend instance
        backend = CursesBackend()
        
        # Verify curses backend doesn't have window geometry methods
        self.assertFalse(hasattr(backend, 'reset_window_geometry'),
                        "Curses backend should not have reset_window_geometry method")
        self.assertFalse(hasattr(backend, 'WINDOW_FRAME_AUTOSAVE_NAME'),
                        "Curses backend should not have WINDOW_FRAME_AUTOSAVE_NAME constant")
    
    def test_coregraphics_has_window_geometry_methods(self):
        """Test that CoreGraphics backend has window geometry methods."""
        if not COREGRAPHICS_AVAILABLE:
            self.skipTest("CoreGraphics backend not available")
        
        # Create CoreGraphics backend instance (without initializing)
        backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_names=["Menlo"],
            font_size=12,
            rows=24,
            cols=80
        )
        
        # Verify CoreGraphics backend has window geometry methods
        self.assertTrue(hasattr(backend, 'reset_window_geometry'),
                       "CoreGraphics backend should have reset_window_geometry method")
        self.assertTrue(hasattr(backend, 'WINDOW_FRAME_AUTOSAVE_NAME'),
                       "CoreGraphics backend should have WINDOW_FRAME_AUTOSAVE_NAME constant")
        self.assertEqual(backend.WINDOW_FRAME_AUTOSAVE_NAME, "TFMMainWindow",
                        "WINDOW_FRAME_AUTOSAVE_NAME should be 'TFMMainWindow'")
    
    @patch('Cocoa.NSWindow')
    @patch('Cocoa.NSApplication')
    def test_coregraphics_reset_requires_initialization(self, mock_app, mock_window_class):
        """Test that reset_window_geometry requires window to be initialized."""
        if not COREGRAPHICS_AVAILABLE:
            self.skipTest("CoreGraphics backend not available")
        
        # Create backend without initializing
        backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_names=["Menlo"],
            font_size=12,
            rows=24,
            cols=80
        )
        
        # Window should be None before initialization
        self.assertIsNone(backend.window)
        
        # Calling reset_window_geometry should return False
        result = backend.reset_window_geometry()
        self.assertFalse(result, "reset_window_geometry should return False when window is not initialized")
    
    def test_backend_type_differentiation(self):
        """Test that we can differentiate between backend types."""
        if not COREGRAPHICS_AVAILABLE or not CURSES_AVAILABLE:
            self.skipTest("Both backends not available")
        
        # Create instances of both backends
        cg_backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_names=["Menlo"],
            font_size=12,
            rows=24,
            cols=80
        )
        curses_backend = CursesBackend()
        
        # Verify they are different types
        self.assertIsInstance(cg_backend, CoreGraphicsBackend)
        self.assertIsInstance(curses_backend, CursesBackend)
        self.assertNotIsInstance(cg_backend, CursesBackend)
        self.assertNotIsInstance(curses_backend, CoreGraphicsBackend)
        
        # Verify only CoreGraphics has window geometry support
        has_cg_geometry = hasattr(cg_backend, 'reset_window_geometry')
        has_curses_geometry = hasattr(curses_backend, 'reset_window_geometry')
        
        self.assertTrue(has_cg_geometry, "CoreGraphics should have window geometry support")
        self.assertFalse(has_curses_geometry, "Curses should not have window geometry support")
