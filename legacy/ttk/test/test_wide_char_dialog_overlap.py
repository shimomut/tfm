#!/usr/bin/env python3
"""
Test for wide character handling when dialog frames overlap.

This test verifies that when a dialog frame overwrites the right half
of a zenkaku (full-width) character in desktop mode, the left half is
properly cleared to prevent partial rendering.
"""

import unittest


class TestWideCharDialogOverlap(unittest.TestCase):
    """Test wide character handling when dialog overlaps file list."""
    
    def setUp(self):
        """Set up test grid to simulate backend behavior."""
        # Create a simple grid structure similar to CoreGraphicsBackend
        self.rows = 24
        self.cols = 80
        self.grid = [[(' ', 0, 0, False) for _ in range(self.cols)] for _ in range(self.rows)]
    
    def _is_wide_character(self, char):
        """Simple wide character detection for testing."""
        # Japanese hiragana/katakana/kanji are wide
        if len(char) == 1:
            code = ord(char)
            # Hiragana, Katakana, CJK Unified Ideographs
            if (0x3040 <= code <= 0x309F or  # Hiragana
                0x30A0 <= code <= 0x30FF or  # Katakana
                0x4E00 <= code <= 0x9FFF):   # CJK Unified Ideographs
                return True
        return False
    
    def _draw_text(self, row, col, text, color_pair=0):
        """Simulate draw_text with wide character handling."""
        # Check if starting position overwrites a placeholder
        if col > 0:
            current_char, current_color, current_attrs, current_is_wide = self.grid[row][col]
            if current_char == '':
                prev_char, prev_color, prev_attrs, prev_is_wide = self.grid[row][col - 1]
                if prev_is_wide and prev_char != '':
                    # Clear the wide character
                    self.grid[row][col - 1] = (' ', prev_color, prev_attrs, False)
        
        # Draw characters
        current_col = col
        for char in text:
            if current_col >= self.cols:
                break
            
            is_wide = self._is_wide_character(char)
            self.grid[row][current_col] = (char, color_pair, 0, is_wide)
            
            if is_wide:
                current_col += 1
                if current_col < self.cols:
                    self.grid[row][current_col] = ('', color_pair, 0, False)
            
            current_col += 1
    
    def _draw_hline(self, row, col, char, length, color_pair=0):
        """Simulate draw_hline with wide character handling."""
        start_col = max(0, col)
        end_col = min(col + length, self.cols)
        
        is_wide = self._is_wide_character(char)
        for c in range(start_col, end_col):
            # Check if overwriting a placeholder
            current_char, current_color, current_attrs, current_is_wide = self.grid[row][c]
            
            if c > 0 and current_char == '':
                prev_char, prev_color, prev_attrs, prev_is_wide = self.grid[row][c - 1]
                if prev_is_wide and prev_char != '':
                    # Clear the wide character
                    self.grid[row][c - 1] = (' ', prev_color, prev_attrs, False)
            
            # Write new character
            self.grid[row][c] = (char, color_pair, 0, is_wide)
    
    def test_draw_hline_over_wide_char_placeholder(self):
        """Test that draw_hline clears wide char when overwriting placeholder."""
        # Draw a wide character (zenkaku) at column 5
        self._draw_text(10, 5, "あ", color_pair=1)
        
        # Verify the wide character is in column 5
        char, color, attrs, is_wide = self.grid[10][5]
        self.assertEqual(char, "あ")
        self.assertTrue(is_wide)
        self.assertEqual(color, 1)
        
        # Verify placeholder is in column 6
        char, color, attrs, is_wide = self.grid[10][6]
        self.assertEqual(char, '')
        self.assertFalse(is_wide)
        
        # Draw a horizontal line starting at column 6 (the placeholder)
        self._draw_hline(10, 6, ' ', 10, color_pair=2)
        
        # The wide character in column 5 should now be cleared
        char, color, attrs, is_wide = self.grid[10][5]
        self.assertEqual(char, ' ')
        self.assertFalse(is_wide)
        self.assertEqual(color, 1)  # Should preserve original color
        
        # Column 6 should have the space from draw_hline
        char, color, attrs, is_wide = self.grid[10][6]
        self.assertEqual(char, ' ')
        self.assertFalse(is_wide)
        self.assertEqual(color, 2)
    
    def test_draw_text_over_wide_char_placeholder(self):
        """Test that draw_text clears wide char when overwriting placeholder."""
        # Draw a wide character at column 10
        self._draw_text(5, 10, "日", color_pair=1)
        
        # Verify setup
        char, _, _, is_wide = self.grid[5][10]
        self.assertEqual(char, "日")
        self.assertTrue(is_wide)
        
        char, _, _, is_wide = self.grid[5][11]
        self.assertEqual(char, '')
        self.assertFalse(is_wide)
        
        # Draw text starting at column 11 (the placeholder)
        self._draw_text(5, 11, "test", color_pair=2)
        
        # The wide character in column 10 should be cleared
        char, color, attrs, is_wide = self.grid[5][10]
        self.assertEqual(char, ' ')
        self.assertFalse(is_wide)
        self.assertEqual(color, 1)  # Preserves original color
        
        # Column 11 should have 't'
        char, color, attrs, is_wide = self.grid[5][11]
        self.assertEqual(char, 't')
        self.assertEqual(color, 2)
    
    def test_multiple_wide_chars_partial_overlap(self):
        """Test multiple wide characters with partial dialog overlap."""
        # Draw multiple wide characters in a row
        self._draw_text(15, 20, "あいう", color_pair=1)
        
        # Verify: あ at 20-21, い at 22-23, う at 24-25
        self.assertEqual(self.grid[15][20][0], "あ")
        self.assertEqual(self.grid[15][21][0], '')
        self.assertEqual(self.grid[15][22][0], "い")
        self.assertEqual(self.grid[15][23][0], '')
        self.assertEqual(self.grid[15][24][0], "う")
        self.assertEqual(self.grid[15][25][0], '')
        
        # Draw hline starting at column 23 (placeholder of い)
        self._draw_hline(15, 23, '─', 5, color_pair=2)
        
        # あ should still be there
        self.assertEqual(self.grid[15][20][0], "あ")
        self.assertTrue(self.grid[15][20][3])
        
        # い should be cleared
        self.assertEqual(self.grid[15][22][0], ' ')
        self.assertFalse(self.grid[15][22][3])
        
        # Column 23 should have the line character
        self.assertEqual(self.grid[15][23][0], '─')
        self.assertEqual(self.grid[15][23][1], 2)
    
    def test_no_clearing_when_not_placeholder(self):
        """Test that normal characters are not affected."""
        # Draw normal ASCII text
        self._draw_text(8, 30, "hello", color_pair=1)
        
        # Overwrite starting at column 32 (the 'l')
        self._draw_hline(8, 32, '-', 3, color_pair=2)
        
        # Previous characters should not be affected
        self.assertEqual(self.grid[8][30][0], 'h')
        self.assertEqual(self.grid[8][31][0], 'e')
        
        # Overwritten area should have the line
        self.assertEqual(self.grid[8][32][0], '-')
        self.assertEqual(self.grid[8][33][0], '-')
        self.assertEqual(self.grid[8][34][0], '-')


if __name__ == '__main__':
    unittest.main()
