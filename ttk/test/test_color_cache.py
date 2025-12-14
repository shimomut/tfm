"""
Unit tests for ColorCache class.

This module tests the ColorCache implementation to ensure:
1. Colors are cached correctly
2. Cache hits return the same object
3. Cache size management works properly
4. Color accuracy is maintained
5. Clear method works correctly
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys

# Mock Cocoa module BEFORE any imports
cocoa_mock = MagicMock()
sys.modules['Cocoa'] = cocoa_mock
sys.modules['Quartz'] = MagicMock()
sys.modules['objc'] = MagicMock()

# Now import ColorCache
from ttk.backends.coregraphics_backend import ColorCache


class TestColorCache(unittest.TestCase):
    """Test suite for ColorCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset the mock for each test
        cocoa_mock.reset_mock()
        
        # Create a cache instance
        self.cache = ColorCache(max_size=4)
    
    def test_cache_initialization(self):
        """Test that cache initializes with correct max_size."""
        cache = ColorCache(max_size=256)
        self.assertEqual(cache._max_size, 256)
        self.assertEqual(len(cache._cache), 0)
    
    def test_cache_default_max_size(self):
        """Test that cache uses default max_size of 256."""
        cache = ColorCache()
        self.assertEqual(cache._max_size, 256)
    
    def test_get_color_creates_nscolor(self):
        """Test that get_color creates NSColor with correct parameters."""
        # Mock NSColor creation
        mock_color = Mock()
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.side_effect = None
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.return_value = mock_color
        
        # Get a color
        result = self.cache.get_color(255, 128, 64, 0.5)
        
        # Verify NSColor was created with correct normalized values
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.assert_called_once_with(
            1.0,  # 255/255
            0.5019607843137255,  # 128/255
            0.25098039215686274,  # 64/255
            0.5
        )
        
        # Verify the returned color is the mock color
        self.assertEqual(result, mock_color)
    
    def test_get_color_caches_result(self):
        """Test that get_color caches the NSColor object."""
        # Mock NSColor creation
        mock_color = Mock()
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.side_effect = None
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.return_value = mock_color
        
        # Get the same color twice
        color1 = self.cache.get_color(255, 0, 0)
        color2 = self.cache.get_color(255, 0, 0)
        
        # NSColor should only be created once
        self.assertEqual(cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.call_count, 1)
        
        # Both calls should return the same object
        self.assertIs(color1, color2)
    
    def test_get_color_different_colors(self):
        """Test that different colors create different cache entries."""
        # Mock NSColor creation
        mock_color1 = Mock()
        mock_color2 = Mock()
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.side_effect = [mock_color1, mock_color2]
        
        # Get two different colors
        color1 = self.cache.get_color(255, 0, 0)
        color2 = self.cache.get_color(0, 255, 0)
        
        # NSColor should be created twice
        self.assertEqual(cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.call_count, 2)
        
        # Colors should be different objects
        self.assertIsNot(color1, color2)
    
    def test_get_color_alpha_variations(self):
        """Test that different alpha values create different cache entries."""
        # Mock NSColor creation
        mock_color1 = Mock()
        mock_color2 = Mock()
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.side_effect = [mock_color1, mock_color2]
        
        # Get same RGB with different alpha
        color1 = self.cache.get_color(255, 0, 0, 1.0)
        color2 = self.cache.get_color(255, 0, 0, 0.5)
        
        # NSColor should be created twice
        self.assertEqual(cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.call_count, 2)
        
        # Colors should be different objects
        self.assertIsNot(color1, color2)
    
    def test_cache_eviction_on_max_size(self):
        """Test that cache clears when max_size is reached."""
        # Create mock colors
        mock_colors = [Mock() for _ in range(5)]
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.side_effect = mock_colors
        
        # Fill cache to max_size (4)
        self.cache.get_color(255, 0, 0)  # Color 1
        self.cache.get_color(0, 255, 0)  # Color 2
        self.cache.get_color(0, 0, 255)  # Color 3
        self.cache.get_color(255, 255, 0)  # Color 4
        
        # Cache should have 4 entries
        self.assertEqual(len(self.cache._cache), 4)
        
        # Add one more color to trigger eviction
        self.cache.get_color(255, 0, 255)  # Color 5
        
        # Cache should have been cleared and now has 1 entry
        self.assertEqual(len(self.cache._cache), 1)
        
        # NSColor should have been created 5 times
        self.assertEqual(cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.call_count, 5)
    
    def test_cache_eviction_recreates_colors(self):
        """Test that colors are recreated after cache eviction."""
        # Create mock colors
        mock_colors = [Mock() for _ in range(6)]
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.side_effect = mock_colors
        
        # Fill cache to max_size
        color1_first = self.cache.get_color(255, 0, 0)
        self.cache.get_color(0, 255, 0)
        self.cache.get_color(0, 0, 255)
        self.cache.get_color(255, 255, 0)
        
        # Trigger eviction
        self.cache.get_color(255, 0, 255)
        
        # Request the first color again (should be recreated)
        color1_second = self.cache.get_color(255, 0, 0)
        
        # Should be different objects (recreated after eviction)
        self.assertIsNot(color1_first, color1_second)
        
        # NSColor should have been created 6 times total
        self.assertEqual(cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.call_count, 6)
    
    def test_clear_method(self):
        """Test that clear() removes all cached colors."""
        # Mock NSColor creation
        mock_colors = [Mock() for _ in range(3)]
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.side_effect = mock_colors
        
        # Add some colors to cache
        self.cache.get_color(255, 0, 0)
        self.cache.get_color(0, 255, 0)
        self.cache.get_color(0, 0, 255)
        
        # Cache should have 3 entries
        self.assertEqual(len(self.cache._cache), 3)
        
        # Clear the cache
        self.cache.clear()
        
        # Cache should be empty
        self.assertEqual(len(self.cache._cache), 0)
    
    def test_clear_method_allows_reuse(self):
        """Test that cache can be used after clear()."""
        # Mock NSColor creation
        mock_colors = [Mock() for _ in range(2)]
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.side_effect = mock_colors
        
        # Add a color
        color1 = self.cache.get_color(255, 0, 0)
        
        # Clear the cache
        self.cache.clear()
        
        # Add the same color again
        color2 = self.cache.get_color(255, 0, 0)
        
        # Should be different objects (recreated after clear)
        self.assertIsNot(color1, color2)
        
        # NSColor should have been created twice
        self.assertEqual(cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.call_count, 2)
    
    def test_default_alpha_value(self):
        """Test that default alpha value is 1.0."""
        # Mock NSColor creation
        mock_color = Mock()
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.side_effect = None
        cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.return_value = mock_color
        
        # Get a color without specifying alpha
        self.cache.get_color(255, 0, 0)
        
        # Verify alpha was 1.0
        call_args = cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.call_args
        self.assertEqual(call_args[0][3], 1.0)
    
    def test_color_accuracy_rgb_normalization(self):
        """Test that RGB values are correctly normalized to 0.0-1.0 range."""
        # Test various RGB values
        test_cases = [
            (0, 0, 0, (0.0, 0.0, 0.0)),
            (255, 255, 255, (1.0, 1.0, 1.0)),
            (128, 128, 128, (128/255, 128/255, 128/255)),
            (64, 192, 32, (64/255, 192/255, 32/255)),
        ]
        
        for r, g, b, expected in test_cases:
            # Create a fresh cache for each test case
            cache = ColorCache(max_size=4)
            
            # Mock NSColor creation
            mock_color = Mock()
            cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.side_effect = None
            cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.return_value = mock_color
            cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.reset_mock()
            
            cache.get_color(r, g, b)
            
            call_args = cocoa_mock.NSColor.colorWithRed_green_blue_alpha_.call_args[0]
            self.assertAlmostEqual(call_args[0], expected[0], places=5)
            self.assertAlmostEqual(call_args[1], expected[1], places=5)
            self.assertAlmostEqual(call_args[2], expected[2], places=5)


if __name__ == '__main__':
    unittest.main()
