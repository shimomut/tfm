#!/usr/bin/env python3
"""
Unit tests for emoji rendering with UTF-16 surrogate pairs.

Tests that the CoreGraphics backend correctly handles emoji characters
that require surrogate pairs in UTF-16 encoding.
"""

import sys
import os
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend


class TestEmojiSurrogatePairs(unittest.TestCase):
    """Test emoji rendering with surrogate pairs."""
    
    def setUp(self):
        """Set up test backend."""
        self.backend = CoreGraphicsBackend(
            window_title="Test",
            font_size=12,
            rows=10,
            cols=40
        )
        self.backend.initialize()
    
    def tearDown(self):
        """Clean up test backend."""
        self.backend.shutdown()
    
    def test_emoji_storage_in_grid(self):
        """Test that emoji are stored correctly in the grid."""
        emoji = "😀"
        self.backend.draw_text(0, 0, emoji, color_pair=0)
        
        # Check grid storage
        cell = self.backend.grid[0][0]
        char, color_pair, attributes, is_wide = cell
        
        # Verify character is stored correctly
        self.assertEqual(char, emoji)
        self.assertEqual(len(char), 1)  # Python stores as single character
        self.assertTrue(is_wide)  # Emoji should be marked as wide
    
    def test_emoji_utf16_encoding(self):
        """Test that emoji have correct UTF-16 surrogate pair encoding."""
        test_cases = [
            ("😀", 0x1F600, 0xD83D, 0xDE00),  # Grinning face
            ("🚀", 0x1F680, 0xD83D, 0xDE80),  # Rocket
            ("🎉", 0x1F389, 0xD83C, 0xDF89),  # Party popper
            ("💻", 0x1F4BB, 0xD83D, 0xDCBB),  # Laptop
        ]
        
        for emoji, codepoint, high_surrogate, low_surrogate in test_cases:
            with self.subTest(emoji=emoji):
                # Check codepoint
                self.assertEqual(ord(emoji), codepoint)
                
                # Check UTF-16 encoding
                utf16_bytes = emoji.encode('utf-16-le')
                self.assertEqual(len(utf16_bytes), 4)  # 2 bytes per surrogate
                
                # Extract surrogates
                high = int.from_bytes(utf16_bytes[0:2], 'little')
                low = int.from_bytes(utf16_bytes[2:4], 'little')
                
                # Verify surrogate values
                self.assertEqual(high, high_surrogate)
                self.assertEqual(low, low_surrogate)
                
                # Verify they're valid surrogates
                self.assertGreaterEqual(high, 0xD800)
                self.assertLessEqual(high, 0xDBFF)
                self.assertGreaterEqual(low, 0xDC00)
                self.assertLessEqual(low, 0xDFFF)
    
    def test_emoji_rendering_no_crash(self):
        """Test that rendering emoji doesn't crash."""
        emojis = ["😀", "😎", "🚀", "🎉", "💻", "❤️", "🌟", "🔥"]
        
        for i, emoji in enumerate(emojis):
            self.backend.draw_text(i, 0, f"{emoji} Test", color_pair=0)
        
        # This should not raise an exception
        try:
            self.backend.refresh()
        except Exception as e:
            self.fail(f"refresh() raised exception: {e}")
    
    def test_mixed_emoji_and_text(self):
        """Test rendering mixed emoji and regular text."""
        text = "Hello 😀 World 🚀 Test 💻"
        self.backend.draw_text(0, 0, text, color_pair=0)
        
        # Should not crash
        try:
            self.backend.refresh()
        except Exception as e:
            self.fail(f"refresh() raised exception: {e}")
    
    def test_consecutive_emoji(self):
        """Test rendering consecutive emoji characters."""
        emoji_string = "😀😎🚀🎉💻"
        self.backend.draw_text(0, 0, emoji_string, color_pair=0)
        
        # Should not crash
        try:
            self.backend.refresh()
        except Exception as e:
            self.fail(f"refresh() raised exception: {e}")
    
    def test_emoji_with_variation_selector(self):
        """Test emoji with variation selectors (multi-codepoint sequences)."""
        # Heart with variation selector: ❤️ = U+2764 + U+FE0F
        heart = "❤️"
        self.backend.draw_text(0, 0, heart, color_pair=0)
        
        # Should not crash
        try:
            self.backend.refresh()
        except Exception as e:
            self.fail(f"refresh() raised exception: {e}")


def run_tests():
    """Run the test suite."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEmojiSurrogatePairs)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
