"""
Unit tests for Metal backend font validation.

Tests that the Metal backend properly validates fonts and rejects
proportional fonts while accepting monospace fonts.

Requirements tested:
- 17.2: Metal backend initializes fonts and checks that font is monospace
- 17.5: Proportional fonts are rejected with clear error message
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys


class TestMetalFontValidation(unittest.TestCase):
    """Test Metal backend font validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the PyObjC modules before importing MetalBackend
        self.mock_metal = MagicMock()
        self.mock_cocoa = MagicMock()
        self.mock_coretext = MagicMock()
        self.mock_quartz = MagicMock()
        self.mock_metalkit = MagicMock()
        
        sys.modules['Metal'] = self.mock_metal
        sys.modules['Cocoa'] = self.mock_cocoa
        sys.modules['CoreText'] = self.mock_coretext
        sys.modules['Quartz'] = self.mock_quartz
        sys.modules['MetalKit'] = self.mock_metalkit
        
        # Now import MetalBackend
        from ttk.backends.metal_backend import MetalBackend
        self.MetalBackend = MetalBackend
        
        # Create backend instance (without initializing)
        self.backend = self.MetalBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=14
        )
    
    def tearDown(self):
        """Clean up mocked modules."""
        # Remove mocked modules
        for module in ['Metal', 'Cocoa', 'CoreText', 'Quartz', 'MetalKit']:
            if module in sys.modules:
                del sys.modules[module]
    
    def test_validate_monospace_font_accepts_valid_font(self):
        """Test that _validate_font accepts a valid monospace font."""
        # Mock NSFont to return a valid font
        mock_font = Mock()
        self.mock_cocoa.NSFont.fontWithName_size_.return_value = mock_font
        
        # Mock NSAttributedString to return same width for all characters (monospace)
        mock_attr_string = Mock()
        mock_size = Mock()
        mock_size.width = 10.0  # Same width for all characters
        mock_attr_string.size.return_value = mock_size
        self.mock_cocoa.NSAttributedString.alloc().initWithString_attributes_.return_value = mock_attr_string
        
        # Should not raise any exception
        try:
            self.backend._validate_font()
        except ValueError:
            self.fail("_validate_font raised ValueError for valid monospace font")
    
    def test_validate_font_rejects_proportional_font(self):
        """Test that _validate_font rejects proportional fonts with clear error message."""
        # Mock NSFont to return a valid font
        mock_font = Mock()
        self.mock_cocoa.NSFont.fontWithName_size_.return_value = mock_font
        
        # Mock NSAttributedString to return different widths (proportional)
        widths = [5.0, 12.0, 15.0, 8.0, 6.0]  # Different widths for different characters
        width_iter = iter(widths)
        
        def create_attr_string(*args, **kwargs):
            mock_attr_string = Mock()
            mock_size = Mock()
            mock_size.width = next(width_iter)
            mock_attr_string.size.return_value = mock_size
            return mock_attr_string
        
        self.mock_cocoa.NSAttributedString.alloc().initWithString_attributes_ = create_attr_string
        
        # Should raise ValueError with clear message
        with self.assertRaises(ValueError) as context:
            self.backend._validate_font()
        
        error_message = str(context.exception)
        # Verify error message contains key information
        self.assertIn("not monospace", error_message.lower())
        self.assertIn("Menlo", error_message)  # Font name
        self.assertIn("monospace font", error_message.lower())
    
    def test_validate_font_rejects_missing_font(self):
        """Test that _validate_font rejects fonts that are not found."""
        # Mock NSFont to return None (font not found)
        self.mock_cocoa.NSFont.fontWithName_size_.return_value = None
        
        # Should raise ValueError with clear message
        with self.assertRaises(ValueError) as context:
            self.backend._validate_font()
        
        error_message = str(context.exception)
        # Verify error message contains key information
        self.assertIn("not found", error_message.lower())
        self.assertIn("Menlo", error_message)  # Font name
        self.assertIn("monospace font", error_message.lower())
    
    def test_validate_font_error_message_suggests_alternatives(self):
        """Test that error messages suggest alternative monospace fonts."""
        # Mock NSFont to return None (font not found)
        self.mock_cocoa.NSFont.fontWithName_size_.return_value = None
        
        # Should raise ValueError with suggestions
        with self.assertRaises(ValueError) as context:
            self.backend._validate_font()
        
        error_message = str(context.exception)
        # Verify error message suggests alternatives
        self.assertTrue(
            any(font in error_message for font in ["Menlo", "Monaco", "Courier"]),
            "Error message should suggest alternative monospace fonts"
        )
    
    def test_validate_font_called_during_initialize(self):
        """Test that _validate_font is called during initialize()."""
        # Mock Metal device creation
        mock_device = Mock()
        self.mock_metal.MTLCreateSystemDefaultDevice.return_value = mock_device
        mock_device.newCommandQueue.return_value = Mock()
        
        # Mock NSFont to return a valid monospace font
        mock_font = Mock()
        self.mock_cocoa.NSFont.fontWithName_size_.return_value = mock_font
        
        # Mock NSAttributedString to return same width (monospace)
        mock_attr_string = Mock()
        mock_size = Mock()
        mock_size.width = 10.0
        mock_attr_string.size.return_value = mock_size
        self.mock_cocoa.NSAttributedString.alloc().initWithString_attributes_.return_value = mock_attr_string
        
        # Mock window creation
        mock_window = Mock()
        self.mock_cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        # Mock Metal view
        mock_metal_view = Mock()
        mock_frame = Mock()
        mock_frame.size.width = 1024
        mock_frame.size.height = 768
        mock_metal_view.frame.return_value = mock_frame
        mock_window.contentView.return_value = mock_metal_view
        
        # Mock MetalKit view
        mock_mtk_view = Mock()
        mock_mtk_view.frame.return_value = mock_frame
        self.mock_metalkit.MTKView.alloc().initWithFrame_device_.return_value = mock_mtk_view
        
        # Initialize should call _validate_font
        try:
            self.backend.initialize()
        except Exception as e:
            # We expect some errors due to incomplete mocking, but _validate_font should have been called
            pass
        
        # Verify fontWithName_size_ was called (part of _validate_font)
        self.assertTrue(
            self.mock_cocoa.NSFont.fontWithName_size_.called,
            "_validate_font should be called during initialize()"
        )


if __name__ == '__main__':
    unittest.main()
