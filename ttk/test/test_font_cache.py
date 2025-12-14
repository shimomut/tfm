"""
Unit tests for FontCache class.

This module tests the FontCache implementation to ensure:
1. Fonts are cached correctly
2. Cache hits return the same object
3. BOLD attribute is applied correctly
4. Clear method works correctly
5. Font attribute preservation
"""

import unittest
from unittest.mock import Mock, MagicMock, call
import sys

# Mock Cocoa module BEFORE any imports
cocoa_mock = MagicMock()
sys.modules['Cocoa'] = cocoa_mock
sys.modules['Quartz'] = MagicMock()
sys.modules['objc'] = MagicMock()

# Now import FontCache and TextAttribute
from ttk.backends.coregraphics_backend import FontCache
from ttk.renderer import TextAttribute


class TestFontCache(unittest.TestCase):
    """Test suite for FontCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset the mock for each test
        cocoa_mock.reset_mock()
        
        # Create a mock base font
        self.mock_base_font = Mock()
        self.mock_base_font.fontName.return_value = "Menlo"
        self.mock_base_font.pointSize.return_value = 12
        
        # Create a cache instance
        self.cache = FontCache(self.mock_base_font)
    
    def test_cache_initialization(self):
        """Test that cache initializes with base font."""
        cache = FontCache(self.mock_base_font)
        self.assertEqual(cache._base_font, self.mock_base_font)
        self.assertEqual(len(cache._cache), 0)
    
    def test_get_font_no_attributes(self):
        """Test that get_font returns base font when no attributes."""
        result = self.cache.get_font(0)
        
        # Should return the base font
        self.assertEqual(result, self.mock_base_font)
        
        # Should be cached
        self.assertEqual(len(self.cache._cache), 1)
        self.assertIn(0, self.cache._cache)
    
    def test_get_font_caches_result(self):
        """Test that get_font caches the font object."""
        # Get the same font twice
        font1 = self.cache.get_font(0)
        font2 = self.cache.get_font(0)
        
        # Both calls should return the same object
        self.assertIs(font1, font2)
        
        # Cache should have one entry
        self.assertEqual(len(self.cache._cache), 1)
    
    def test_get_font_bold_attribute(self):
        """Test that get_font applies BOLD attribute correctly."""
        # Mock NSFontManager
        mock_font_manager = Mock()
        mock_bold_font = Mock()
        mock_bold_font.fontName.return_value = "Menlo-Bold"
        
        cocoa_mock.NSFontManager.sharedFontManager.return_value = mock_font_manager
        mock_font_manager.convertFont_toHaveTrait_.return_value = mock_bold_font
        cocoa_mock.NSBoldFontMask = 2  # Standard value
        
        # Get bold font
        result = self.cache.get_font(TextAttribute.BOLD)
        
        # Verify NSFontManager was called correctly
        cocoa_mock.NSFontManager.sharedFontManager.assert_called_once()
        mock_font_manager.convertFont_toHaveTrait_.assert_called_once_with(
            self.mock_base_font,
            cocoa_mock.NSBoldFontMask
        )
        
        # Should return the bold font
        self.assertEqual(result, mock_bold_font)
        
        # Should be cached
        self.assertEqual(len(self.cache._cache), 1)
        self.assertIn(TextAttribute.BOLD, self.cache._cache)
    
    def test_get_font_bold_caches_result(self):
        """Test that bold font is cached and reused."""
        # Mock NSFontManager
        mock_font_manager = Mock()
        mock_bold_font = Mock()
        
        cocoa_mock.NSFontManager.sharedFontManager.return_value = mock_font_manager
        mock_font_manager.convertFont_toHaveTrait_.return_value = mock_bold_font
        cocoa_mock.NSBoldFontMask = 2
        
        # Get bold font twice
        font1 = self.cache.get_font(TextAttribute.BOLD)
        font2 = self.cache.get_font(TextAttribute.BOLD)
        
        # NSFontManager should only be called once
        self.assertEqual(mock_font_manager.convertFont_toHaveTrait_.call_count, 1)
        
        # Both calls should return the same object
        self.assertIs(font1, font2)
    
    def test_get_font_different_attributes(self):
        """Test that different attributes create different cache entries."""
        # Mock NSFontManager
        mock_font_manager = Mock()
        mock_bold_font = Mock()
        
        cocoa_mock.NSFontManager.sharedFontManager.return_value = mock_font_manager
        mock_font_manager.convertFont_toHaveTrait_.return_value = mock_bold_font
        cocoa_mock.NSBoldFontMask = 2
        
        # Get normal and bold fonts
        normal_font = self.cache.get_font(0)
        bold_font = self.cache.get_font(TextAttribute.BOLD)
        
        # Should be different objects
        self.assertIsNot(normal_font, bold_font)
        
        # Cache should have two entries
        self.assertEqual(len(self.cache._cache), 2)
    
    def test_get_font_underline_attribute(self):
        """Test that UNDERLINE attribute doesn't affect font (handled separately)."""
        # Get font with underline attribute
        result = self.cache.get_font(TextAttribute.UNDERLINE)
        
        # Should return the base font (underline is handled in text attributes)
        self.assertEqual(result, self.mock_base_font)
        
        # Should be cached
        self.assertEqual(len(self.cache._cache), 1)
    
    def test_get_font_reverse_attribute(self):
        """Test that REVERSE attribute doesn't affect font (handled separately)."""
        # Get font with reverse attribute
        result = self.cache.get_font(TextAttribute.REVERSE)
        
        # Should return the base font (reverse is handled by swapping colors)
        self.assertEqual(result, self.mock_base_font)
        
        # Should be cached
        self.assertEqual(len(self.cache._cache), 1)
    
    def test_get_font_combined_attributes(self):
        """Test that combined attributes work correctly."""
        # Mock NSFontManager
        mock_font_manager = Mock()
        mock_bold_font = Mock()
        
        cocoa_mock.NSFontManager.sharedFontManager.return_value = mock_font_manager
        mock_font_manager.convertFont_toHaveTrait_.return_value = mock_bold_font
        cocoa_mock.NSBoldFontMask = 2
        
        # Get font with BOLD | UNDERLINE
        result = self.cache.get_font(TextAttribute.BOLD | TextAttribute.UNDERLINE)
        
        # Should apply bold (underline is handled separately)
        self.assertEqual(result, mock_bold_font)
        
        # Verify NSFontManager was called
        mock_font_manager.convertFont_toHaveTrait_.assert_called_once_with(
            self.mock_base_font,
            cocoa_mock.NSBoldFontMask
        )
    
    def test_get_font_combined_attributes_cached_separately(self):
        """Test that combined attributes are cached separately from individual attributes."""
        # Mock NSFontManager
        mock_font_manager = Mock()
        mock_bold_font = Mock()
        
        cocoa_mock.NSFontManager.sharedFontManager.return_value = mock_font_manager
        mock_font_manager.convertFont_toHaveTrait_.return_value = mock_bold_font
        cocoa_mock.NSBoldFontMask = 2
        
        # Get bold font
        bold_font = self.cache.get_font(TextAttribute.BOLD)
        
        # Get bold+underline font
        bold_underline_font = self.cache.get_font(TextAttribute.BOLD | TextAttribute.UNDERLINE)
        
        # Should be the same object (both have BOLD, underline doesn't affect font)
        self.assertIs(bold_font, bold_underline_font)
        
        # Cache should have two entries (different keys)
        self.assertEqual(len(self.cache._cache), 2)
    
    def test_clear_method(self):
        """Test that clear() removes all cached fonts."""
        # Mock NSFontManager
        mock_font_manager = Mock()
        mock_bold_font = Mock()
        
        cocoa_mock.NSFontManager.sharedFontManager.return_value = mock_font_manager
        mock_font_manager.convertFont_toHaveTrait_.return_value = mock_bold_font
        cocoa_mock.NSBoldFontMask = 2
        
        # Add some fonts to cache
        self.cache.get_font(0)
        self.cache.get_font(TextAttribute.BOLD)
        self.cache.get_font(TextAttribute.UNDERLINE)
        
        # Cache should have 3 entries
        self.assertEqual(len(self.cache._cache), 3)
        
        # Clear the cache
        self.cache.clear()
        
        # Cache should be empty
        self.assertEqual(len(self.cache._cache), 0)
    
    def test_clear_method_preserves_base_font(self):
        """Test that clear() preserves the base font reference."""
        # Clear the cache
        self.cache.clear()
        
        # Base font should still be accessible
        self.assertEqual(self.cache._base_font, self.mock_base_font)
    
    def test_clear_method_allows_reuse(self):
        """Test that cache can be used after clear()."""
        # Mock NSFontManager
        mock_font_manager = Mock()
        mock_bold_font1 = Mock()
        mock_bold_font2 = Mock()
        
        cocoa_mock.NSFontManager.sharedFontManager.return_value = mock_font_manager
        mock_font_manager.convertFont_toHaveTrait_.side_effect = [mock_bold_font1, mock_bold_font2]
        cocoa_mock.NSBoldFontMask = 2
        
        # Add a bold font
        font1 = self.cache.get_font(TextAttribute.BOLD)
        
        # Clear the cache
        self.cache.clear()
        
        # Add the same bold font again
        font2 = self.cache.get_font(TextAttribute.BOLD)
        
        # Should be different objects (recreated after clear)
        self.assertIsNot(font1, font2)
        
        # NSFontManager should have been called twice
        self.assertEqual(mock_font_manager.convertFont_toHaveTrait_.call_count, 2)
    
    def test_multiple_caches_independent(self):
        """Test that multiple FontCache instances are independent."""
        # Create two caches with different base fonts
        mock_base_font2 = Mock()
        cache2 = FontCache(mock_base_font2)
        
        # Add fonts to both caches
        font1 = self.cache.get_font(0)
        font2 = cache2.get_font(0)
        
        # Should return different base fonts
        self.assertEqual(font1, self.mock_base_font)
        self.assertEqual(font2, mock_base_font2)
        self.assertIsNot(font1, font2)
    
    def test_cache_key_is_attribute_bitmask(self):
        """Test that cache uses attribute bitmask as key."""
        # Get fonts with different attribute combinations
        self.cache.get_font(0)
        self.cache.get_font(TextAttribute.BOLD)
        self.cache.get_font(TextAttribute.UNDERLINE)
        self.cache.get_font(TextAttribute.BOLD | TextAttribute.UNDERLINE)
        
        # Cache should have 4 entries with correct keys
        self.assertEqual(len(self.cache._cache), 4)
        self.assertIn(0, self.cache._cache)
        self.assertIn(TextAttribute.BOLD, self.cache._cache)
        self.assertIn(TextAttribute.UNDERLINE, self.cache._cache)
        self.assertIn(TextAttribute.BOLD | TextAttribute.UNDERLINE, self.cache._cache)


if __name__ == '__main__':
    unittest.main()
