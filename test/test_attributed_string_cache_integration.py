"""
Integration tests for AttributedStringCache with AttributeDictCache.

This module tests the integration between AttributedStringCache and
AttributeDictCache to ensure they work together correctly.

Run with: PYTHONPATH=.:src:ttk pytest test/test_attributed_string_cache_integration.py -v
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
    AttributedStringCache, 
    AttributeDictCache,
    FontCache,
    ColorCache
)


class TestAttributedStringCacheIntegration(unittest.TestCase):
    """Integration tests for AttributedStringCache with AttributeDictCache."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock font and color
        self.mock_font = MagicMock()
        self.mock_color = MagicMock()
        
        # Patch NSFont and NSColor
        self.font_patcher = patch('ttk.backends.coregraphics_backend.Cocoa.NSFont')
        self.color_patcher = patch('ttk.backends.coregraphics_backend.Cocoa.NSColor')
        self.attr_string_patcher = patch('ttk.backends.coregraphics_backend.Cocoa.NSAttributedString')
        
        self.mock_ns_font = self.font_patcher.start()
        self.mock_ns_color = self.color_patcher.start()
        self.mock_ns_attr_string = self.attr_string_patcher.start()
        
        # Configure mocks
        self.mock_ns_font.fontWithName_size_.return_value = self.mock_font
        self.mock_ns_color.colorWithCalibratedRed_green_blue_alpha_.return_value = self.mock_color
        
        # Mock NSAttributedString creation
        self.mock_attr_string_instance = MagicMock()
        self.mock_ns_attr_string.alloc.return_value.initWithString_attributes_.return_value = self.mock_attr_string_instance
        
        # Create real cache instances
        font_cache = FontCache(self.mock_font)
        color_cache = ColorCache(max_size=256)
        attr_dict_cache = AttributeDictCache(font_cache, color_cache)
        self.attr_string_cache = AttributedStringCache(attr_dict_cache, max_cache_size=100)
    
    def tearDown(self):
        """Clean up after tests."""
        self.font_patcher.stop()
        self.color_patcher.stop()
        self.attr_string_patcher.stop()
    
    def test_attributed_string_cache_uses_attr_dict_cache(self):
        """Test that AttributedStringCache uses AttributeDictCache for attributes."""
        text = "Hello"
        font_key = "0"
        color_rgb = (255, 255, 255)
        underline = False
        
        # Get attributed string
        result = self.attr_string_cache.get_attributed_string(text, font_key, color_rgb, underline)
        
        # Verify NSAttributedString was created with attributes from AttributeDictCache
        self.mock_ns_attr_string.alloc.return_value.initWithString_attributes_.assert_called_once()
        call_args = self.mock_ns_attr_string.alloc.return_value.initWithString_attributes_.call_args
        
        # Verify text was passed correctly
        self.assertEqual(call_args[0][0], text)
        
        # Verify attributes dictionary was passed
        attributes = call_args[0][1]
        self.assertIsInstance(attributes, dict)
    
    def test_repeated_calls_reuse_cached_attributed_string(self):
        """Test that repeated calls with same parameters reuse cached NSAttributedString."""
        text = "World"
        font_key = "0"
        color_rgb = (255, 0, 0)
        underline = True
        
        # First call
        result1 = self.attr_string_cache.get_attributed_string(text, font_key, color_rgb, underline)
        
        # Get call count
        call_count_after_first = self.mock_ns_attr_string.alloc.return_value.initWithString_attributes_.call_count
        
        # Second call with same parameters
        result2 = self.attr_string_cache.get_attributed_string(text, font_key, color_rgb, underline)
        
        # Verify no additional NSAttributedString was created
        self.assertEqual(
            self.mock_ns_attr_string.alloc.return_value.initWithString_attributes_.call_count,
            call_count_after_first
        )
        
        # Verify same object returned
        self.assertEqual(result1, result2)
    
    def test_different_text_creates_new_attributed_string(self):
        """Test that different text creates new NSAttributedString."""
        font_key = "0"
        color_rgb = (255, 255, 255)
        underline = False
        
        # Create attributed strings with different text
        result1 = self.attr_string_cache.get_attributed_string("Hello", font_key, color_rgb, underline)
        result2 = self.attr_string_cache.get_attributed_string("World", font_key, color_rgb, underline)
        
        # Verify two NSAttributedString objects were created
        self.assertEqual(
            self.mock_ns_attr_string.alloc.return_value.initWithString_attributes_.call_count,
            2
        )
        
        # Verify cache has two entries
        self.assertEqual(len(self.attr_string_cache._cache), 2)
    
    def test_cache_clear_removes_all_entries(self):
        """Test that clearing cache removes all entries."""
        # Add some entries
        self.attr_string_cache.get_attributed_string("A", "0", (255, 255, 255), False)
        self.attr_string_cache.get_attributed_string("B", "0", (255, 255, 255), False)
        self.attr_string_cache.get_attributed_string("C", "0", (255, 255, 255), False)
        
        self.assertEqual(len(self.attr_string_cache._cache), 3)
        
        # Clear cache
        self.attr_string_cache.clear()
        
        # Verify cache is empty
        self.assertEqual(len(self.attr_string_cache._cache), 0)
        self.assertEqual(len(self.attr_string_cache._access_order), 0)
    
    def test_lru_eviction_with_real_caches(self):
        """Test LRU eviction works correctly with real cache instances."""
        # Create cache with small max size
        font_cache = FontCache(self.mock_font)
        color_cache = ColorCache(max_size=256)
        attr_dict_cache = AttributeDictCache(font_cache, color_cache)
        small_cache = AttributedStringCache(attr_dict_cache, max_cache_size=2)
        
        # Fill cache
        small_cache.get_attributed_string("A", "0", (255, 255, 255), False)
        small_cache.get_attributed_string("B", "0", (255, 255, 255), False)
        
        self.assertEqual(len(small_cache._cache), 2)
        
        # Add third entry - should evict A
        small_cache.get_attributed_string("C", "0", (255, 255, 255), False)
        
        # Cache should still have 2 entries
        self.assertEqual(len(small_cache._cache), 2)
        
        # A should be evicted
        key_a = ("A", "0", (255, 255, 255), False)
        self.assertNotIn(key_a, small_cache._cache)
    
    def test_attribute_dict_cache_integration(self):
        """Test that AttributeDictCache is properly integrated."""
        # Verify AttributeDictCache reference is set
        self.assertIsNotNone(self.attr_string_cache._attr_dict_cache)
        self.assertIsInstance(self.attr_string_cache._attr_dict_cache, AttributeDictCache)
        
        # Create attributed string
        self.attr_string_cache.get_attributed_string("Test", "0", (255, 255, 255), False)
        
        # Verify AttributeDictCache was used (it should have cached the attributes)
        self.assertGreater(len(self.attr_string_cache._attr_dict_cache._cache), 0)
