#!/usr/bin/env python3
"""
Tests for TTK Wide Character Utilities

This test suite verifies the wide character detection and display width
calculation functions work correctly across different Unicode scenarios.
"""

import sys
import os
import unittest

# Add TTK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from wide_char_utils import (
    _is_wide_character,
    get_display_width,
    truncate_to_width,
    pad_to_width,
    split_at_width,
)


class TestWideCharacterDetection(unittest.TestCase):
    """Test wide character detection functionality."""
    
    def test_ascii_characters(self):
        """ASCII characters should not be wide."""
        self.assertFalse(_is_wide_character('A'))
        self.assertFalse(_is_wide_character('z'))
        self.assertFalse(_is_wide_character('0'))
        self.assertFalse(_is_wide_character(' '))
    
    def test_japanese_characters(self):
        """Japanese characters should be wide."""
        self.assertTrue(_is_wide_character('あ'))
        self.assertTrue(_is_wide_character('ア'))
        self.assertTrue(_is_wide_character('漢'))
    
    def test_chinese_characters(self):
        """Chinese characters should be wide."""
        self.assertTrue(_is_wide_character('中'))
        self.assertTrue(_is_wide_character('文'))
    
    def test_korean_characters(self):
        """Korean characters should be wide."""
        self.assertTrue(_is_wide_character('한'))
        self.assertTrue(_is_wide_character('글'))


class TestDisplayWidth(unittest.TestCase):
    """Test display width calculation."""
    
    def test_ascii_string(self):
        """ASCII strings should have width equal to length."""
        self.assertEqual(get_display_width("hello"), 5)
        self.assertEqual(get_display_width("test"), 4)
    
    def test_japanese_string(self):
        """Japanese strings should have double width."""
        self.assertEqual(get_display_width("こんにちは"), 10)
    
    def test_mixed_string(self):
        """Mixed strings should calculate correctly."""
        self.assertEqual(get_display_width("hello世界"), 9)  # 5 + 4
    
    def test_empty_string(self):
        """Empty string should have zero width."""
        self.assertEqual(get_display_width(""), 0)


class TestTruncateToWidth(unittest.TestCase):
    """Test text truncation functionality."""
    
    def test_ascii_truncation(self):
        """ASCII truncation should work correctly."""
        result = truncate_to_width("hello world", 8)
        # Result should be at most 8 characters wide
        self.assertLessEqual(get_display_width(result), 8)
        self.assertTrue(result.endswith("…"))
    
    def test_no_truncation_needed(self):
        """Short strings should not be truncated."""
        result = truncate_to_width("short", 10)
        self.assertEqual(result, "short")
    
    def test_wide_char_truncation(self):
        """Wide character truncation should preserve boundaries."""
        result = truncate_to_width("こんにちは", 6)
        self.assertTrue(get_display_width(result) <= 6)
        self.assertTrue(result.endswith("…"))


class TestPadToWidth(unittest.TestCase):
    """Test text padding functionality."""
    
    def test_left_padding(self):
        """Left padding should add spaces on right."""
        result = pad_to_width("test", 10, align='left')
        self.assertEqual(get_display_width(result), 10)
        self.assertTrue(result.startswith("test"))
    
    def test_right_padding(self):
        """Right padding should add spaces on left."""
        result = pad_to_width("test", 10, align='right')
        self.assertEqual(get_display_width(result), 10)
        self.assertTrue(result.endswith("test"))
    
    def test_center_padding(self):
        """Center padding should add spaces on both sides."""
        result = pad_to_width("test", 10, align='center')
        self.assertEqual(get_display_width(result), 10)


class TestSplitAtWidth(unittest.TestCase):
    """Test text splitting functionality."""
    
    def test_ascii_split(self):
        """ASCII splitting should work correctly."""
        left, right = split_at_width("hello world", 6)
        self.assertEqual(left, "hello ")
        self.assertEqual(right, "world")
    
    def test_wide_char_split(self):
        """Wide character splitting should preserve boundaries."""
        left, right = split_at_width("こんにちは世界", 8)
        self.assertTrue(get_display_width(left) <= 8)
        # Verify no characters were lost
        self.assertEqual(left + right, "こんにちは世界")


if __name__ == '__main__':
    unittest.main()
