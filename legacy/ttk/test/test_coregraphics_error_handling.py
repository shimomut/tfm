"""
Unit tests for CoreGraphics backend error handling.

This module tests error handling for initialization and runtime operations
in the CoreGraphics backend, verifying that:
- PyObjC availability is checked
- Font validation works correctly
- Window creation is validated
- Color pair validation works correctly
- Drawing operations handle failures gracefully
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import io
import importlib
from contextlib import redirect_stdout


class TestCoreGraphicsErrorHandling(unittest.TestCase):
    """Test error handling in CoreGraphics backend."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock PyObjC modules before importing backend
        self.cocoa_mock = MagicMock()
        self.quartz_mock = MagicMock()
        self.objc_mock = MagicMock()
        
        sys.modules['Cocoa'] = self.cocoa_mock
        sys.modules['Quartz'] = self.quartz_mock
        sys.modules['objc'] = self.objc_mock
        
        # Import after mocking
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        self.CoreGraphicsBackend = CoreGraphicsBackend
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove mocked modules
        if 'Cocoa' in sys.modules:
            del sys.modules['Cocoa']
        if 'Quartz' in sys.modules:
            del sys.modules['Quartz']
        if 'objc' in sys.modules:
            del sys.modules['objc']
        
        # Remove backend module to force reimport
        if 'ttk.backends.coregraphics_backend' in sys.modules:
            del sys.modules['ttk.backends.coregraphics_backend']
    
    def test_pyobjc_not_available_raises_runtime_error(self):
        """Test that missing PyObjC raises RuntimeError with installation instructions."""
        # This test verifies the error handling logic when PyObjC is not available
        # We need to patch the COCOA_AVAILABLE flag directly
        
        # Reimport backend module
        if 'ttk.backends.coregraphics_backend' in sys.modules:
            del sys.modules['ttk.backends.coregraphics_backend']
        
        # Patch the module to simulate PyObjC not being available
        with patch.dict('sys.modules', {'Cocoa': None, 'Quartz': None, 'objc': None}):
            # Force reimport with patched modules
            import ttk.backends.coregraphics_backend as backend_module
            importlib.reload(backend_module)
            
            # Now COCOA_AVAILABLE should be False
            # Attempt to create backend should raise RuntimeError
            with self.assertRaises(RuntimeError) as context:
                backend = backend_module.CoreGraphicsBackend()
            
            # Verify error message includes installation instructions
            error_message = str(context.exception)
            self.assertIn("PyObjC", error_message)
            self.assertIn("pip install", error_message)
            self.assertIn("pyobjc-framework-Cocoa", error_message)
    
    def test_invalid_font_raises_value_error(self):
        """Test that invalid font name raises ValueError."""
        # Create backend instance
        backend = self.CoreGraphicsBackend(font_name="NonExistentFont")
        
        # Mock font loading to return None (font not found)
        self.cocoa_mock.NSFont.fontWithName_size_.return_value = None
        
        # Attempt to initialize should raise ValueError
        with self.assertRaises(ValueError) as context:
            backend.initialize()
        
        # Verify error message includes font name and suggestions
        error_message = str(context.exception)
        self.assertIn("NonExistentFont", error_message)
        self.assertIn("not found", error_message)
        self.assertIn("Menlo", error_message)  # Should suggest valid fonts
    
    def test_window_creation_failure_raises_runtime_error(self):
        """Test that window creation failure raises RuntimeError."""
        # Create backend instance
        backend = self.CoreGraphicsBackend()
        
        # Mock successful font loading
        mock_font = MagicMock()
        self.cocoa_mock.NSFont.fontWithName_size_.return_value = mock_font
        
        # Mock font size calculation
        mock_attr_string = MagicMock()
        mock_size = MagicMock()
        mock_size.width = 10
        mock_size.height = 20
        mock_attr_string.size.return_value = mock_size
        self.cocoa_mock.NSAttributedString.alloc().initWithString_attributes_.return_value = mock_attr_string
        
        # Mock window creation to return None (failure)
        self.cocoa_mock.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_.return_value = None
        
        # Attempt to initialize should raise RuntimeError
        with self.assertRaises(RuntimeError) as context:
            backend.initialize()
        
        # Verify error message mentions window creation failure
        error_message = str(context.exception)
        self.assertIn("window", error_message.lower())
        self.assertIn("failed", error_message.lower())
    
    def test_color_pair_id_out_of_range_raises_value_error(self):
        """Test that color pair ID out of range raises ValueError."""
        # Create and initialize backend
        backend = self.CoreGraphicsBackend()
        
        # Mock successful initialization
        self._mock_successful_initialization(backend)
        backend.initialize()
        
        # Test color pair ID too low (0 is reserved)
        with self.assertRaises(ValueError) as context:
            backend.init_color_pair(0, (255, 255, 255), (0, 0, 0))
        
        error_message = str(context.exception)
        self.assertIn("1-255", error_message)
        self.assertIn("reserved", error_message)
        
        # Test color pair ID too high
        with self.assertRaises(ValueError) as context:
            backend.init_color_pair(256, (255, 255, 255), (0, 0, 0))
        
        error_message = str(context.exception)
        self.assertIn("1-255", error_message)
    
    def test_rgb_component_out_of_range_raises_value_error(self):
        """Test that RGB component out of range raises ValueError."""
        # Create and initialize backend
        backend = self.CoreGraphicsBackend()
        
        # Mock successful initialization
        self._mock_successful_initialization(backend)
        backend.initialize()
        
        # Test foreground RGB component too low
        with self.assertRaises(ValueError) as context:
            backend.init_color_pair(1, (-1, 255, 255), (0, 0, 0))
        
        error_message = str(context.exception)
        self.assertIn("0-255", error_message)
        self.assertIn("foreground", error_message)
        
        # Test foreground RGB component too high
        with self.assertRaises(ValueError) as context:
            backend.init_color_pair(1, (256, 255, 255), (0, 0, 0))
        
        error_message = str(context.exception)
        self.assertIn("0-255", error_message)
        
        # Test background RGB component out of range
        with self.assertRaises(ValueError) as context:
            backend.init_color_pair(1, (255, 255, 255), (0, 0, 300))
        
        error_message = str(context.exception)
        self.assertIn("0-255", error_message)
        self.assertIn("background", error_message)
    
    def test_drawing_operations_handle_failures_gracefully(self):
        """Test that drawing operations handle failures without crashing."""
        # Create and initialize backend
        backend = self.CoreGraphicsBackend()
        
        # Mock successful initialization
        self._mock_successful_initialization(backend)
        backend.initialize()
        
        # Corrupt the grid to cause failures
        backend.grid = None
        
        # These operations should not raise exceptions, just print warnings
        # We capture stdout to verify warnings are printed
        f = io.StringIO()
        with redirect_stdout(f):
            backend.draw_text(0, 0, "test")
            backend.clear()
            backend.clear_region(0, 0, 5, 5)
            backend.draw_hline(0, 0, '-', 10)
            backend.draw_vline(0, 0, '|', 10)
            backend.draw_rect(0, 0, 5, 5)
        
        # Verify warnings were printed
        output = f.getvalue()
        self.assertIn("Warning", output)
    
    def test_refresh_operations_handle_failures_gracefully(self):
        """Test that refresh operations handle failures without crashing."""
        # Create and initialize backend
        backend = self.CoreGraphicsBackend()
        
        # Mock successful initialization
        self._mock_successful_initialization(backend)
        backend.initialize()
        
        # Mock view to raise exception
        backend.view = MagicMock()
        backend.view.setNeedsDisplay_.side_effect = RuntimeError("Mock error")
        
        # These operations should not raise exceptions, just print warnings
        f = io.StringIO()
        with redirect_stdout(f):
            backend.refresh()
            backend.refresh_region(0, 0, 5, 5)
        
        # Verify warnings were printed
        output = f.getvalue()
        self.assertIn("Warning", output)
    
    def _mock_successful_initialization(self, backend):
        """Helper method to mock successful initialization."""
        # Mock successful font loading
        mock_font = MagicMock()
        self.cocoa_mock.NSFont.fontWithName_size_.return_value = mock_font
        
        # Mock font size calculation
        mock_attr_string = MagicMock()
        mock_size = MagicMock()
        mock_size.width = 10
        mock_size.height = 20
        mock_attr_string.size.return_value = mock_size
        self.cocoa_mock.NSAttributedString.alloc().initWithString_attributes_.return_value = mock_attr_string
        
        # Mock successful window creation
        mock_window = MagicMock()
        self.cocoa_mock.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        # Mock view creation
        mock_view = MagicMock()
        mock_window.contentView().frame.return_value = MagicMock()
        
        # Store mocks
        backend.font = mock_font
        backend.window = mock_window
        backend.view = mock_view


if __name__ == '__main__':
    unittest.main()
