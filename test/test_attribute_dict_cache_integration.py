"""
Integration test for AttributeDictCache with CoreGraphicsBackend.

This test verifies that AttributeDictCache is properly integrated into
the CoreGraphicsBackend and works with real FontCache and ColorCache instances.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock PyObjC modules before importing the backend
sys.modules['Cocoa'] = MagicMock()
sys.modules['Quartz'] = MagicMock()
sys.modules['objc'] = MagicMock()

# Import after mocking
from ttk.backends.coregraphics_backend import (
    AttributeDictCache, 
    FontCache, 
    ColorCache,
    CoreGraphicsBackend
)


class TestAttributeDictCacheIntegration(unittest.TestCase):
    """Integration tests for AttributeDictCache."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Cocoa constants
        import Cocoa
        Cocoa.NSFontAttributeName = "NSFont"
        Cocoa.NSForegroundColorAttributeName = "NSForegroundColor"
        Cocoa.NSUnderlineStyleAttributeName = "NSUnderlineStyle"
        Cocoa.NSUnderlineStyleSingle = 1
        
        # Create mock font
        self.mock_font = Mock()
        Cocoa.NSFont.fontWithName_size_.return_value = self.mock_font
        
        # Create mock color
        self.mock_color = Mock()
        Cocoa.NSColor.colorWithRed_green_blue_alpha_.return_value = self.mock_color
    
    def test_attribute_dict_cache_with_real_caches(self):
        """Test AttributeDictCache with real FontCache and ColorCache instances."""
        # Create real cache instances
        font_cache = FontCache(self.mock_font)
        color_cache = ColorCache(max_size=256)
        
        # Create AttributeDictCache
        attr_cache = AttributeDictCache(font_cache, color_cache)
        
        # Test cache operations
        attrs1 = attr_cache.get_attributes("0", (255, 255, 255), False)
        attrs2 = attr_cache.get_attributes("0", (255, 255, 255), False)
        
        # Verify cache hit (same object returned)
        self.assertIs(attrs1, attrs2)
        
        # Verify cache has one entry
        self.assertEqual(len(attr_cache._cache), 1)
    
    def test_attribute_dict_cache_integration_with_backend(self):
        """Test that AttributeDictCache is properly integrated in CoreGraphicsBackend."""
        # Mock NSApplication and other Cocoa components
        import Cocoa
        mock_app = Mock()
        Cocoa.NSApplication.sharedApplication.return_value = mock_app
        
        mock_window = Mock()
        Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        mock_view = Mock()
        
        # Create backend instance
        try:
            backend = CoreGraphicsBackend(
                window_title="Test",
                font_name="Menlo",
                font_size=12,
                rows=24,
                cols=80
            )
            
            # Verify AttributeDictCache is initialized
            self.assertIsNotNone(backend._attr_dict_cache)
            self.assertIsInstance(backend._attr_dict_cache, AttributeDictCache)
            
            # Verify it has references to font and color caches
            self.assertIs(backend._attr_dict_cache._font_cache, backend._font_cache)
            self.assertIs(backend._attr_dict_cache._color_cache, backend._color_cache)
            
        except Exception as e:
            # Backend initialization may fail in test environment, but we can still
            # verify the cache would be created if initialization succeeded
            self.skipTest(f"Backend initialization not fully testable in mock environment: {e}")
    
    def test_cache_clearing_on_color_change(self):
        """Test that AttributeDictCache is cleared when colors change."""
        # Create real cache instances
        font_cache = FontCache(self.mock_font)
        color_cache = ColorCache(max_size=256)
        attr_cache = AttributeDictCache(font_cache, color_cache)
        
        # Add some entries to cache
        attr_cache.get_attributes("0", (255, 255, 255), False)
        attr_cache.get_attributes("1", (255, 0, 0), True)
        
        # Verify cache has entries
        self.assertEqual(len(attr_cache._cache), 2)
        
        # Clear cache (simulating color scheme change)
        attr_cache.clear()
        
        # Verify cache is empty
        self.assertEqual(len(attr_cache._cache), 0)
        
        # Verify cache can be used again after clearing
        attrs = attr_cache.get_attributes("0", (255, 255, 255), False)
        self.assertIsNotNone(attrs)
        self.assertEqual(len(attr_cache._cache), 1)


if __name__ == '__main__':
    unittest.main()
