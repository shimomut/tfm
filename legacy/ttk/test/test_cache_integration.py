"""
Unit tests for cache integration in CoreGraphicsBackend.

This test module verifies that the ColorCache and FontCache are properly
integrated into the CoreGraphicsBackend initialization and cleanup processes.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock


class TestCacheIntegration(unittest.TestCase):
    """Test cache integration in CoreGraphicsBackend initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock PyObjC modules to allow testing without macOS
        self.cocoa_mock = MagicMock()
        self.quartz_mock = MagicMock()
        self.objc_mock = MagicMock()
        
        # Set up module mocks
        self.modules = {
            'Cocoa': self.cocoa_mock,
            'Quartz': self.quartz_mock,
            'objc': self.objc_mock,
        }
        
        # Patch sys.modules to inject our mocks
        self.patcher = patch.dict('sys.modules', self.modules)
        self.patcher.start()
        
        # Now import the backend module (will use our mocks)
        import ttk.backends.coregraphics_backend as cg_module
        self.cg_module = cg_module
        
        # Set COCOA_AVAILABLE to True for testing
        cg_module.COCOA_AVAILABLE = True
    
    def tearDown(self):
        """Clean up after tests."""
        self.patcher.stop()
    
    def test_cache_attributes_initialized_in_init(self):
        """Test that cache attributes are initialized to None in __init__."""
        backend = self.cg_module.CoreGraphicsBackend()
        
        # Verify cache attributes exist and are None before initialize()
        self.assertIsNone(backend._color_cache)
        self.assertIsNone(backend._font_cache)
    
    def test_caches_created_during_initialize(self):
        """Test that caches are created during initialize()."""
        # Mock the NSApplication and other Cocoa objects
        mock_app = MagicMock()
        self.cocoa_mock.NSApplication.sharedApplication.return_value = mock_app
        
        # Mock font creation
        mock_font = MagicMock()
        self.cocoa_mock.NSFont.fontWithName_size_.return_value = mock_font
        
        # Mock attributed string for character dimension calculation
        mock_attr_string = MagicMock()
        mock_size = MagicMock()
        mock_size.width = 10.0
        mock_size.height = 20.0
        mock_attr_string.size.return_value = mock_size
        self.cocoa_mock.NSAttributedString.alloc.return_value.initWithString_attributes_.return_value = mock_attr_string
        
        # Mock window creation
        mock_window = MagicMock()
        self.cocoa_mock.NSWindow.alloc.return_value.initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        # Mock window delegate
        mock_delegate = MagicMock()
        self.cg_module.TTKWindowDelegate = MagicMock(return_value=mock_delegate)
        
        # Mock view creation
        mock_view = MagicMock()
        self.cg_module.TTKView = MagicMock()
        self.cg_module.TTKView.alloc.return_value.initWithFrame_backend_.return_value = mock_view
        
        # Create backend and initialize
        backend = self.cg_module.CoreGraphicsBackend()
        backend.initialize()
        
        # Verify caches are created
        self.assertIsNotNone(backend._color_cache)
        self.assertIsNotNone(backend._font_cache)
        
        # Verify cache types
        self.assertIsInstance(backend._color_cache, self.cg_module.ColorCache)
        self.assertIsInstance(backend._font_cache, self.cg_module.FontCache)
    
    def test_color_cache_initialized_with_correct_size(self):
        """Test that ColorCache is initialized with max_size=256."""
        # Mock the NSApplication and other Cocoa objects
        mock_app = MagicMock()
        self.cocoa_mock.NSApplication.sharedApplication.return_value = mock_app
        
        # Mock font creation
        mock_font = MagicMock()
        self.cocoa_mock.NSFont.fontWithName_size_.return_value = mock_font
        
        # Mock attributed string for character dimension calculation
        mock_attr_string = MagicMock()
        mock_size = MagicMock()
        mock_size.width = 10.0
        mock_size.height = 20.0
        mock_attr_string.size.return_value = mock_size
        self.cocoa_mock.NSAttributedString.alloc.return_value.initWithString_attributes_.return_value = mock_attr_string
        
        # Mock window creation
        mock_window = MagicMock()
        self.cocoa_mock.NSWindow.alloc.return_value.initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        # Mock window delegate
        mock_delegate = MagicMock()
        self.cg_module.TTKWindowDelegate = MagicMock(return_value=mock_delegate)
        
        # Mock view creation
        mock_view = MagicMock()
        self.cg_module.TTKView = MagicMock()
        self.cg_module.TTKView.alloc.return_value.initWithFrame_backend_.return_value = mock_view
        
        # Create backend and initialize
        backend = self.cg_module.CoreGraphicsBackend()
        backend.initialize()
        
        # Verify ColorCache max_size is 256
        self.assertEqual(backend._color_cache._max_size, 256)
    
    def test_font_cache_initialized_with_base_font(self):
        """Test that FontCache is initialized with the base font."""
        # Mock the NSApplication and other Cocoa objects
        mock_app = MagicMock()
        self.cocoa_mock.NSApplication.sharedApplication.return_value = mock_app
        
        # Mock font creation
        mock_font = MagicMock()
        self.cocoa_mock.NSFont.fontWithName_size_.return_value = mock_font
        
        # Mock attributed string for character dimension calculation
        mock_attr_string = MagicMock()
        mock_size = MagicMock()
        mock_size.width = 10.0
        mock_size.height = 20.0
        mock_attr_string.size.return_value = mock_size
        self.cocoa_mock.NSAttributedString.alloc.return_value.initWithString_attributes_.return_value = mock_attr_string
        
        # Mock window creation
        mock_window = MagicMock()
        self.cocoa_mock.NSWindow.alloc.return_value.initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        # Mock window delegate
        mock_delegate = MagicMock()
        self.cg_module.TTKWindowDelegate = MagicMock(return_value=mock_delegate)
        
        # Mock view creation
        mock_view = MagicMock()
        self.cg_module.TTKView = MagicMock()
        self.cg_module.TTKView.alloc.return_value.initWithFrame_backend_.return_value = mock_view
        
        # Create backend and initialize
        backend = self.cg_module.CoreGraphicsBackend()
        backend.initialize()
        
        # Verify FontCache has the base font
        self.assertIs(backend._font_cache._base_font, backend.font)
    
    def test_caches_cleared_during_shutdown(self):
        """Test that caches are cleared during shutdown."""
        # Mock the NSApplication and other Cocoa objects
        mock_app = MagicMock()
        self.cocoa_mock.NSApplication.sharedApplication.return_value = mock_app
        
        # Mock font creation
        mock_font = MagicMock()
        self.cocoa_mock.NSFont.fontWithName_size_.return_value = mock_font
        
        # Mock attributed string for character dimension calculation
        mock_attr_string = MagicMock()
        mock_size = MagicMock()
        mock_size.width = 10.0
        mock_size.height = 20.0
        mock_attr_string.size.return_value = mock_size
        self.cocoa_mock.NSAttributedString.alloc.return_value.initWithString_attributes_.return_value = mock_attr_string
        
        # Mock window creation
        mock_window = MagicMock()
        self.cocoa_mock.NSWindow.alloc.return_value.initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        # Mock window delegate
        mock_delegate = MagicMock()
        self.cg_module.TTKWindowDelegate = MagicMock(return_value=mock_delegate)
        
        # Mock view creation
        mock_view = MagicMock()
        self.cg_module.TTKView = MagicMock()
        self.cg_module.TTKView.alloc.return_value.initWithFrame_backend_.return_value = mock_view
        
        # Create backend and initialize
        backend = self.cg_module.CoreGraphicsBackend()
        backend.initialize()
        
        # Verify caches exist
        self.assertIsNotNone(backend._color_cache)
        self.assertIsNotNone(backend._font_cache)
        
        # Shutdown
        backend.shutdown()
        
        # Verify caches are cleared (set to None)
        self.assertIsNone(backend._color_cache)
        self.assertIsNone(backend._font_cache)
    
    def test_shutdown_handles_none_caches_gracefully(self):
        """Test that shutdown handles None caches without errors."""
        backend = self.cg_module.CoreGraphicsBackend()
        
        # Verify caches are None
        self.assertIsNone(backend._color_cache)
        self.assertIsNone(backend._font_cache)
        
        # Shutdown should not raise an error
        try:
            backend.shutdown()
        except Exception as e:
            self.fail(f"shutdown() raised an exception with None caches: {e}")
        
        # Verify caches are still None
        self.assertIsNone(backend._color_cache)
        self.assertIsNone(backend._font_cache)


if __name__ == '__main__':
    unittest.main()
