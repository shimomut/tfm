"""
Unit tests for AttributedStringCache class.

This module tests the AttributedStringCache implementation, which caches
NSAttributedString objects to eliminate redundant instantiation overhead
during character drawing.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock PyObjC modules before importing the backend
sys.modules['Cocoa'] = MagicMock()
sys.modules['Quartz'] = MagicMock()
sys.modules['objc'] = MagicMock()

# Import after mocking
from ttk.backends.coregraphics_backend import AttributedStringCache, AttributeDictCache


class TestAttributedStringCache(unittest.TestCase):
    """Test suite for AttributedStringCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock AttributeDictCache
        self.mock_attr_dict_cache = Mock(spec=AttributeDictCache)
        
        # Mock attribute dictionary that will be returned
        self.mock_attributes = {'NSFont': 'mock_font', 'NSForegroundColor': 'mock_color'}
        self.mock_attr_dict_cache.get_attributes.return_value = self.mock_attributes
        
        # Mock NSAttributedString
        self.mock_attr_string = MagicMock()
        
        # Patch NSAttributedString creation
        self.patcher = patch('ttk.backends.coregraphics_backend.Cocoa.NSAttributedString')
        self.mock_ns_attr_string_class = self.patcher.start()
        self.mock_ns_attr_string_class.alloc.return_value.initWithString_attributes_.return_value = self.mock_attr_string
        
        # Create cache instance
        self.cache = AttributedStringCache(self.mock_attr_dict_cache, max_cache_size=3)
    
    def tearDown(self):
        """Clean up after tests."""
        self.patcher.stop()
    
    def test_cache_initialization(self):
        """Test that cache initializes with AttributeDictCache."""
        cache = AttributedStringCache(self.mock_attr_dict_cache, max_cache_size=100)
        
        self.assertEqual(cache._attr_dict_cache, self.mock_attr_dict_cache)
        self.assertEqual(cache._max_cache_size, 100)
        self.assertEqual(len(cache._cache), 0)
        self.assertEqual(len(cache._access_order), 0)
    
    def test_cache_miss_creates_attributed_string(self):
        """Test that cache miss creates new NSAttributedString."""
        text = "Hello"
        font_key = "normal"
        color_rgb = (255, 255, 255)
        underline = False
        
        result = self.cache.get_attributed_string(text, font_key, color_rgb, underline)
        
        # Verify AttributeDictCache was called
        self.mock_attr_dict_cache.get_attributes.assert_called_once_with(
            font_key, color_rgb, underline
        )
        
        # Verify NSAttributedString was created
        self.mock_ns_attr_string_class.alloc.return_value.initWithString_attributes_.assert_called_once_with(
            text, self.mock_attributes
        )
        
        # Verify result is the mock attributed string
        self.assertEqual(result, self.mock_attr_string)
        
        # Verify cache was updated
        key = (text, font_key, color_rgb, underline)
        self.assertIn(key, self.cache._cache)
        self.assertIn(key, self.cache._access_order)
    
    def test_cache_hit_returns_cached_string(self):
        """Test that cache hit returns cached NSAttributedString without creating new one."""
        text = "Hello"
        font_key = "normal"
        color_rgb = (255, 255, 255)
        underline = False
        
        # First call - cache miss
        result1 = self.cache.get_attributed_string(text, font_key, color_rgb, underline)
        
        # Reset mock call counts
        self.mock_attr_dict_cache.get_attributes.reset_mock()
        self.mock_ns_attr_string_class.alloc.return_value.initWithString_attributes_.reset_mock()
        
        # Second call - cache hit
        result2 = self.cache.get_attributed_string(text, font_key, color_rgb, underline)
        
        # Verify no new calls were made
        self.mock_attr_dict_cache.get_attributes.assert_not_called()
        self.mock_ns_attr_string_class.alloc.return_value.initWithString_attributes_.assert_not_called()
        
        # Verify same object returned
        self.assertEqual(result1, result2)
    
    def test_cache_hit_updates_access_order(self):
        """Test that cache hit updates LRU access order."""
        # Add three entries
        self.cache.get_attributed_string("A", "0", (255, 255, 255), False)
        self.cache.get_attributed_string("B", "0", (255, 255, 255), False)
        self.cache.get_attributed_string("C", "0", (255, 255, 255), False)
        
        # Access order should be [A, B, C]
        self.assertEqual(len(self.cache._access_order), 3)
        
        # Access A again
        self.cache.get_attributed_string("A", "0", (255, 255, 255), False)
        
        # Access order should now be [B, C, A]
        key_a = ("A", "0", (255, 255, 255), False)
        self.assertEqual(self.cache._access_order[-1], key_a)
    
    def test_lru_eviction_when_cache_full(self):
        """Test that LRU eviction removes least recently used entry when cache is full."""
        # Fill cache to max size (3)
        self.cache.get_attributed_string("A", "0", (255, 255, 255), False)
        self.cache.get_attributed_string("B", "0", (255, 255, 255), False)
        self.cache.get_attributed_string("C", "0", (255, 255, 255), False)
        
        self.assertEqual(len(self.cache._cache), 3)
        
        # Add fourth entry - should evict A (least recently used)
        self.cache.get_attributed_string("D", "0", (255, 255, 255), False)
        
        # Cache should still have 3 entries
        self.assertEqual(len(self.cache._cache), 3)
        
        # A should be evicted
        key_a = ("A", "0", (255, 255, 255), False)
        self.assertNotIn(key_a, self.cache._cache)
        self.assertNotIn(key_a, self.cache._access_order)
        
        # B, C, D should remain
        key_b = ("B", "0", (255, 255, 255), False)
        key_c = ("C", "0", (255, 255, 255), False)
        key_d = ("D", "0", (255, 255, 255), False)
        self.assertIn(key_b, self.cache._cache)
        self.assertIn(key_c, self.cache._cache)
        self.assertIn(key_d, self.cache._cache)
    
    def test_lru_eviction_respects_access_order(self):
        """Test that LRU eviction respects access order, not insertion order."""
        # Fill cache
        self.cache.get_attributed_string("A", "0", (255, 255, 255), False)
        self.cache.get_attributed_string("B", "0", (255, 255, 255), False)
        self.cache.get_attributed_string("C", "0", (255, 255, 255), False)
        
        # Access A again to make it most recently used
        self.cache.get_attributed_string("A", "0", (255, 255, 255), False)
        
        # Now access order is [B, C, A]
        # Add D - should evict B (least recently used)
        self.cache.get_attributed_string("D", "0", (255, 255, 255), False)
        
        # B should be evicted, A should remain
        key_a = ("A", "0", (255, 255, 255), False)
        key_b = ("B", "0", (255, 255, 255), False)
        self.assertIn(key_a, self.cache._cache)
        self.assertNotIn(key_b, self.cache._cache)
    
    def test_different_text_creates_different_cache_entries(self):
        """Test that different text creates separate cache entries."""
        self.cache.get_attributed_string("Hello", "0", (255, 255, 255), False)
        self.cache.get_attributed_string("World", "0", (255, 255, 255), False)
        
        self.assertEqual(len(self.cache._cache), 2)
    
    def test_different_attributes_create_different_cache_entries(self):
        """Test that different attributes create separate cache entries."""
        # Create cache with larger size to avoid eviction during this test
        cache = AttributedStringCache(self.mock_attr_dict_cache, max_cache_size=10)
        
        # Same text, different font
        cache.get_attributed_string("Hello", "0", (255, 255, 255), False)
        cache.get_attributed_string("Hello", "1", (255, 255, 255), False)
        
        # Same text, different color
        cache.get_attributed_string("Hello", "0", (255, 0, 0), False)
        
        # Same text, different underline
        cache.get_attributed_string("Hello", "0", (255, 255, 255), True)
        
        # Should have 4 different cache entries
        self.assertEqual(len(cache._cache), 4)
    
    def test_clear_removes_all_entries(self):
        """Test that clear() removes all cached entries."""
        # Add some entries
        self.cache.get_attributed_string("A", "0", (255, 255, 255), False)
        self.cache.get_attributed_string("B", "0", (255, 255, 255), False)
        self.cache.get_attributed_string("C", "0", (255, 255, 255), False)
        
        self.assertEqual(len(self.cache._cache), 3)
        self.assertEqual(len(self.cache._access_order), 3)
        
        # Clear cache
        self.cache.clear()
        
        # Verify cache is empty
        self.assertEqual(len(self.cache._cache), 0)
        self.assertEqual(len(self.cache._access_order), 0)
    
    def test_clear_preserves_attr_dict_cache_reference(self):
        """Test that clear() preserves AttributeDictCache reference."""
        self.cache.clear()
        
        # AttributeDictCache reference should still be valid
        self.assertEqual(self.cache._attr_dict_cache, self.mock_attr_dict_cache)


if __name__ == '__main__':
    unittest.main()
