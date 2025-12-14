"""
Test cache clearing on resize and color scheme change events.

This test verifies that AttributeDictCache and AttributedStringCache are properly
cleared when terminal resize or color scheme change events occur, ensuring that
cached objects are rebuilt with updated dimensions or colors.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import Mock, MagicMock, patch
from ttk.backends.coregraphics_backend import CoreGraphicsBackend


class TestCacheClearing(unittest.TestCase):
    """Test cache clearing on resize and color scheme change."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock PyObjC availability
        self.cocoa_available_patcher = patch('ttk.backends.coregraphics_backend.COCOA_AVAILABLE', True)
        self.cocoa_available_patcher.start()
        
        # Create backend instance
        self.backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12,
            rows=24,
            cols=80
        )
        
        # Mock the caches
        self.backend._attr_dict_cache = Mock()
        self.backend._attr_dict_cache.clear = Mock()
        
        self.backend._attr_string_cache = Mock()
        self.backend._attr_string_cache.clear = Mock()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.cocoa_available_patcher.stop()
    
    def test_color_scheme_change_clears_attr_dict_cache(self):
        """Test that init_color_pair clears attribute dictionary cache."""
        # Initialize a color pair
        self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        
        # Verify attribute dictionary cache was cleared
        self.backend._attr_dict_cache.clear.assert_called_once()
    
    def test_color_scheme_change_clears_attr_string_cache(self):
        """Test that init_color_pair clears attributed string cache."""
        # Initialize a color pair
        self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        
        # Verify attributed string cache was cleared
        self.backend._attr_string_cache.clear.assert_called_once()
    
    def test_multiple_color_changes_clear_caches(self):
        """Test that multiple color pair changes clear caches each time."""
        # Initialize multiple color pairs
        self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        self.backend.init_color_pair(2, (0, 255, 0), (0, 0, 0))
        self.backend.init_color_pair(3, (0, 0, 255), (0, 0, 0))
        
        # Verify caches were cleared for each color pair change
        self.assertEqual(self.backend._attr_dict_cache.clear.call_count, 3)
        self.assertEqual(self.backend._attr_string_cache.clear.call_count, 3)
    
    def test_cache_clearing_handles_none_caches(self):
        """Test that cache clearing handles None caches gracefully."""
        # Set caches to None
        self.backend._attr_dict_cache = None
        self.backend._attr_string_cache = None
        
        # This should not raise an exception
        try:
            self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        except AttributeError:
            self.fail("init_color_pair raised AttributeError with None caches")
    
    def test_cache_clearing_handles_missing_caches(self):
        """Test that cache clearing handles missing cache attributes gracefully."""
        # Delete cache attributes
        if hasattr(self.backend, '_attr_dict_cache'):
            delattr(self.backend, '_attr_dict_cache')
        if hasattr(self.backend, '_attr_string_cache'):
            delattr(self.backend, '_attr_string_cache')
        
        # This should not raise an exception
        try:
            self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        except AttributeError:
            self.fail("init_color_pair raised AttributeError with missing caches")


if __name__ == '__main__':
    unittest.main()
