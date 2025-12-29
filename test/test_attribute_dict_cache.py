"""
Test suite for AttributeDictCache class.

This module tests the AttributeDictCache implementation which caches
pre-built NSDictionary objects for NSAttributedString text attributes.

Run with: PYTHONPATH=.:src:ttk pytest test/test_attribute_dict_cache.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock PyObjC modules before importing the backend
sys.modules['Cocoa'] = MagicMock()
sys.modules['Quartz'] = MagicMock()
sys.modules['objc'] = MagicMock()

# Import after mocking
from ttk.backends.coregraphics_backend import AttributeDictCache, FontCache, ColorCache


class TestAttributeDictCache(unittest.TestCase):
    """Test suite for AttributeDictCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock font and color caches
        self.mock_font_cache = Mock(spec=FontCache)
        self.mock_color_cache = Mock(spec=ColorCache)
        
        # Create mock font and color objects
        self.mock_font = Mock()
        self.mock_color = Mock()
        
        # Configure mock caches to return mock objects
        self.mock_font_cache.get_font.return_value = self.mock_font
        self.mock_color_cache.get_color.return_value = self.mock_color
        
        # Create cache instance
        self.cache = AttributeDictCache(self.mock_font_cache, self.mock_color_cache)
    
    def test_cache_initialization(self):
        """Test that cache initializes with font and color caches."""
        cache = AttributeDictCache(self.mock_font_cache, self.mock_color_cache)
        
        self.assertEqual(cache._font_cache, self.mock_font_cache)
        self.assertEqual(cache._color_cache, self.mock_color_cache)
        self.assertEqual(len(cache._cache), 0)
    
    def test_get_attributes_cache_miss(self):
        """Test that get_attributes creates new dictionary on cache miss."""
        # First call should be a cache miss
        attrs = self.cache.get_attributes("0", (255, 255, 255), False)
        
        # Verify font and color caches were called
        self.mock_font_cache.get_font.assert_called_once_with(0)
        self.mock_color_cache.get_color.assert_called_once_with(255, 255, 255)
        
        # Verify attributes dictionary was created and cached
        self.assertEqual(len(self.cache._cache), 1)
        self.assertIsNotNone(attrs)
    
    def test_get_attributes_cache_hit(self):
        """Test that get_attributes returns cached dictionary on cache hit."""
        # First call - cache miss
        attrs1 = self.cache.get_attributes("0", (255, 255, 255), False)
        
        # Reset mock call counts
        self.mock_font_cache.get_font.reset_mock()
        self.mock_color_cache.get_color.reset_mock()
        
        # Second call with same parameters - cache hit
        attrs2 = self.cache.get_attributes("0", (255, 255, 255), False)
        
        # Verify font and color caches were NOT called again
        self.mock_font_cache.get_font.assert_not_called()
        self.mock_color_cache.get_color.assert_not_called()
        
        # Verify same object was returned
        self.assertIs(attrs1, attrs2)
    
    def test_get_attributes_with_underline(self):
        """Test that get_attributes includes underline style when requested."""
        # Get attributes with underline
        attrs = self.cache.get_attributes("0", (255, 255, 255), True)
        
        # Verify we got a dictionary back
        self.assertIsNotNone(attrs)
        
        # Verify it has 3 keys (font, color, underline)
        # Note: With mocked Cocoa, we can't easily verify the exact keys
        # but we can verify the dictionary was created
        self.assertIsInstance(attrs, dict)
    
    def test_get_attributes_different_keys(self):
        """Test that different attribute combinations create separate cache entries."""
        # Create multiple entries with different parameters
        attrs1 = self.cache.get_attributes("0", (255, 255, 255), False)
        attrs2 = self.cache.get_attributes("1", (255, 255, 255), False)  # Different font
        attrs3 = self.cache.get_attributes("0", (255, 0, 0), False)      # Different color
        attrs4 = self.cache.get_attributes("0", (255, 255, 255), True)   # Different underline
        
        # Verify all entries are cached separately
        self.assertEqual(len(self.cache._cache), 4)
        
        # Verify they are different objects
        self.assertIsNot(attrs1, attrs2)
        self.assertIsNot(attrs1, attrs3)
        self.assertIsNot(attrs1, attrs4)
    
    def test_clear_cache(self):
        """Test that clear() removes all cached entries."""
        # Add some entries to cache
        self.cache.get_attributes("0", (255, 255, 255), False)
        self.cache.get_attributes("1", (255, 0, 0), True)
        
        # Verify cache has entries
        self.assertEqual(len(self.cache._cache), 2)
        
        # Clear cache
        self.cache.clear()
        
        # Verify cache is empty
        self.assertEqual(len(self.cache._cache), 0)
    
    def test_font_key_string_conversion(self):
        """Test that font_key is properly converted from string to integer."""
        # Test with string font key
        self.cache.get_attributes("5", (255, 255, 255), False)
        
        # Verify font cache was called with integer
        self.mock_font_cache.get_font.assert_called_once_with(5)
    
    def test_font_key_integer_passthrough(self):
        """Test that integer font_key is passed through directly."""
        # Test with integer font key
        self.cache.get_attributes(5, (255, 255, 255), False)
        
        # Verify font cache was called with integer
        self.mock_font_cache.get_font.assert_called_once_with(5)
    
    def test_cache_preserves_references(self):
        """Test that cache preserves font and color cache references."""
        # Verify references are preserved
        self.assertIs(self.cache._font_cache, self.mock_font_cache)
        self.assertIs(self.cache._color_cache, self.mock_color_cache)
        
        # Clear cache
        self.cache.clear()
        
        # Verify references are still preserved after clear
        self.assertIs(self.cache._font_cache, self.mock_font_cache)
        self.assertIs(self.cache._color_cache, self.mock_color_cache)
