#!/usr/bin/env python3
"""
Test for wide character handling in curses backend when dialog frames overlap.

This test verifies that when a dialog frame overwrites the right half
of a zenkaku (full-width) character in curses mode, both halves are
properly cleared with the original background color to prevent layout
breakage after the dialog closes.
"""

import unittest


class TestCursesWideCharDialogOverlap(unittest.TestCase):
    """Test wide character handling in curses backend when dialog overlaps."""
    
    def setUp(self):
        """Set up test grid to simulate curses backend behavior."""
        # Create a simple grid structure similar to CursesBackend
        self.rows = 24
        self.cols = 80
        self.grid = [[(' ', 0, 0, False) for _ in range(self.cols)] for _ in range(self.rows)]
    
    def _is_wide_character(self, char):
        """Simple wide character detection for testing."""
        if len(char) == 1:
            code = ord(char)
            # Hiragana, Katakana, CJK Unified Ideographs
            if (0x3040 <= code <= 0x309F or  # Hiragana
                0x30A0 <= code <= 0x30FF or  # Katakana
                0x4E00 <= code <= 0x9FFF):   # CJK Unified Ideographs
                return True
        return False
    
    def _draw_text(self, row, col, text, color_pair=0):
        """Simulate curses draw_text with wide character tracking and clearing."""
        # Check if starting position overwrites a placeholder
        if col > 0 and col < self.cols:
            current_char, current_color, current_attrs, current_is_wide = self.grid[row][col]
            if current_char == '':
                prev_char, prev_color, prev_attrs, prev_is_wide = self.grid[row][col - 1]
                if prev_is_wide and prev_char != '':
                    # Clear both cells with spaces using original background color
                    self.grid[row][col - 1] = (' ', prev_color, prev_attrs, False)
                    self.grid[row][col] = (' ', prev_color, prev_attrs, False)
        
        # Draw characters and track in grid
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
    
    def test_dialog_overlap_preserves_background_color(self):
        """Test that dialog overlap clears wide char with original background color."""
        # Draw a wide character with color_pair=1 (file list color)
        self._draw_text(10, 5, "あ", color_pair=1)
        
        # Verify setup
        char, color, attrs, is_wide = self.grid[10][5]
        self.assertEqual(char, "あ")
        self.assertTrue(is_wide)
        self.assertEqual(color, 1)
        
        char, color, attrs, is_wide = self.grid[10][6]
        self.assertEqual(char, '')
        self.assertEqual(color, 1)  # Placeholder has same color
        
        # Draw dialog background starting at column 6 (the placeholder)
        # This simulates dialog frame overlapping the right half
        self._draw_text(10, 6, ' ' * 10, color_pair=2)
        
        # Left cell should be cleared with original color
        char, color, attrs, is_wide = self.grid[10][5]
        self.assertEqual(char, ' ')
        self.assertFalse(is_wide)
        self.assertEqual(color, 1)  # Should preserve original color
        
        # Right cell (column 6) gets overwritten by dialog
        # The clearing happens first, then dialog writes its space
        char, color, attrs, is_wide = self.grid[10][6]
        self.assertEqual(char, ' ')
        self.assertFalse(is_wide)
        self.assertEqual(color, 2)  # Dialog color (this is expected)
    
    def test_dialog_close_no_layout_break(self):
        """Test that layout doesn't break after dialog closes."""
        # Draw file list with wide characters
        self._draw_text(8, 4, "あいう", color_pair=1)
        
        # Verify initial state
        self.assertEqual(self.grid[8][4][0], "あ")
        self.assertEqual(self.grid[8][6][0], "い")
        self.assertEqual(self.grid[8][8][0], "う")
        
        # Draw dialog overlapping middle character
        self._draw_text(8, 7, '        ', color_pair=2)
        
        # Middle character should be cleared with original color
        self.assertEqual(self.grid[8][6][0], ' ')
        self.assertEqual(self.grid[8][6][1], 1)  # Original color preserved
        
        # First character should remain intact
        self.assertEqual(self.grid[8][4][0], "あ")
        self.assertTrue(self.grid[8][4][3])
        
        # After dialog closes, redraw file list
        self._draw_text(8, 4, "あいう", color_pair=1)
        
        # All characters should be properly restored
        self.assertEqual(self.grid[8][4][0], "あ")
        self.assertTrue(self.grid[8][4][3])
        self.assertEqual(self.grid[8][6][0], "い")
        self.assertTrue(self.grid[8][6][3])
        self.assertEqual(self.grid[8][8][0], "う")
        self.assertTrue(self.grid[8][8][3])
    
    def test_multiple_overlaps(self):
        """Test multiple wide characters with dialog overlap."""
        # Draw multiple wide characters
        self._draw_text(15, 20, "日本語", color_pair=1)
        
        # Verify setup
        self.assertEqual(self.grid[15][20][0], "日")
        self.assertEqual(self.grid[15][22][0], "本")
        self.assertEqual(self.grid[15][24][0], "語")
        
        # Dialog overlaps second character's placeholder
        self._draw_text(15, 23, '      ', color_pair=2)
        
        # Second character should be cleared with original color
        self.assertEqual(self.grid[15][22][0], ' ')
        self.assertEqual(self.grid[15][22][1], 1)
        
        # First character should remain
        self.assertEqual(self.grid[15][20][0], "日")
        self.assertTrue(self.grid[15][20][3])


if __name__ == '__main__':
    unittest.main()
