"""
Test for SingleLineTextEdit cursor rendering bug

This test reproduces the issue where cursor stops rendering when
editing text is longer than the maximum width.

Run with: PYTHONPATH=.:src:ttk pytest test/test_cursor_rendering_bug.py -v
"""

import unittest
from unittest.mock import Mock, patch
from tfm_single_line_text_edit import SingleLineTextEdit
from ttk import TextAttribute


class TestCursorRenderingBug(unittest.TestCase):
    """Test cursor rendering with long text"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.editor = SingleLineTextEdit()
        
    @patch('tfm_single_line_text_edit.get_status_color')
    def test_cursor_renders_at_end_of_long_text(self, mock_get_status_color):
        """Test that cursor renders when at the end of long text"""
        mock_get_status_color.return_value = 0
        
        # Set up long text that exceeds display width
        long_text = "this_is_a_very_long_filename_that_exceeds_the_display_width.txt"
        max_width = 30  # Much shorter than the text
        
        self.editor.set_text(long_text)
        self.editor.set_cursor_pos(len(long_text))  # Cursor at end
        
        # Mock stdscr
        mock_stdscr = Mock()
        
        # Track what gets drawn
        drawn_items = []
        def mock_addstr(y, x, text, attr=0):
            drawn_items.append({
                'y': y, 'x': x, 'text': text, 'attr': attr,
                'is_cursor': bool(attr & TextAttribute.REVERSE)
            })
        
        mock_stdscr.addstr = mock_addstr
        mock_stdscr.getmaxyx.return_value = (24, 80)
        
        # Draw the editor
        self.editor.draw(mock_stdscr, 0, 0, max_width, "", is_active=True)
        
        # Check if cursor was rendered
        cursor_items = [item for item in drawn_items if item['is_cursor']]
        
        self.assertGreater(len(cursor_items), 0, "Cursor should be rendered when at end of long text")
        
    @patch('tfm_single_line_text_edit.get_status_color')
    def test_cursor_renders_in_middle_of_long_text(self, mock_get_status_color):
        """Test that cursor renders when in middle of long text"""
        mock_get_status_color.return_value = 0
        
        # Set up long text
        long_text = "this_is_a_very_long_filename_that_exceeds_the_display_width.txt"
        max_width = 20
        
        self.editor.set_text(long_text)
        self.editor.set_cursor_pos(30)  # Cursor in middle
        
        # Mock stdscr
        mock_stdscr = Mock()
        
        # Track what gets drawn
        drawn_items = []
        def mock_addstr(y, x, text, attr=0):
            drawn_items.append({
                'y': y, 'x': x, 'text': text, 'attr': attr,
                'is_cursor': bool(attr & TextAttribute.REVERSE)
            })
        
        mock_stdscr.addstr = mock_addstr
        mock_stdscr.getmaxyx.return_value = (24, 80)
        
        # Draw the editor
        self.editor.draw(mock_stdscr, 0, 0, max_width, "", is_active=True)
        
        # Check if cursor was rendered
        cursor_items = [item for item in drawn_items if item['is_cursor']]
        
        self.assertGreater(len(cursor_items), 0, "Cursor should be rendered when in middle of long text")
        
    @patch('tfm_single_line_text_edit.get_status_color')
    def test_cursor_renders_at_various_positions(self, mock_get_status_color):
        """Test cursor rendering at various positions in long text"""
        mock_get_status_color.return_value = 0
        
        long_text = "abcdefghijklmnopqrstuvwxyz0123456789"  # 36 characters
        max_width = 15  # Show only 15 characters
        
        self.editor.set_text(long_text)
        
        # Test cursor at various positions
        test_positions = [0, 5, 10, 15, 20, 25, 30, 35, 36]  # Including end
        
        for cursor_pos in test_positions:
            with self.subTest(cursor_pos=cursor_pos):
                self.editor.set_cursor_pos(cursor_pos)
                
                # Mock stdscr
                mock_stdscr = Mock()
                
                # Track what gets drawn
                drawn_items = []
                def mock_addstr(y, x, text, attr=0):
                    drawn_items.append({
                        'y': y, 'x': x, 'text': text, 'attr': attr,
                        'is_cursor': bool(attr & TextAttribute.REVERSE)
                    })
                
                mock_stdscr.addstr = mock_addstr
                mock_stdscr.getmaxyx.return_value = (24, 80)
                
                # Draw the editor
                self.editor.draw(mock_stdscr, 0, 0, max_width, "", is_active=True)
                
                # Check if cursor was rendered
                cursor_items = [item for item in drawn_items if item['is_cursor']]
                
                self.assertGreater(len(cursor_items), 0, 
                    f"Cursor should be rendered at position {cursor_pos}")
                
    def test_visible_window_calculation(self):
        """Test the visible window calculation logic"""
        long_text = "abcdefghijklmnopqrstuvwxyz0123456789"  # 36 characters
        text_max_width = 15
        
        # Test different cursor positions and expected visible windows
        test_cases = [
            # (cursor_pos, expected_visible_start, expected_visible_end)
            (0, 0, 15),      # Cursor at start
            (5, 0, 15),      # Cursor near start
            (7, 0, 15),      # Cursor at text_max_width // 2
            (8, 1, 16),      # Cursor just past middle
            (15, 8, 23),     # Cursor in middle
            (25, 18, 33),    # Cursor near end
            (35, 21, 36),    # Cursor at end
            (36, 21, 36),    # Cursor past end
        ]
        
        for cursor_pos, expected_start, expected_end in test_cases:
            with self.subTest(cursor_pos=cursor_pos):
                # Simulate the visible window calculation from the draw method
                visible_start = 0
                visible_end = len(long_text)
                
                if len(long_text) > text_max_width:
                    if cursor_pos < text_max_width // 2:
                        visible_end = text_max_width
                    elif cursor_pos > len(long_text) - text_max_width // 2:
                        visible_start = len(long_text) - text_max_width
                    else:
                        visible_start = cursor_pos - text_max_width // 2
                        visible_end = visible_start + text_max_width
                
                self.assertEqual(visible_start, expected_start, 
                    f"Wrong visible_start for cursor at {cursor_pos}")
                self.assertEqual(visible_end, expected_end,
                    f"Wrong visible_end for cursor at {cursor_pos}")
                
                # Check that cursor is within visible window
                cursor_in_visible = cursor_pos - visible_start
                self.assertGreaterEqual(cursor_in_visible, 0,
                    f"Cursor should be visible at position {cursor_pos}")
                self.assertLessEqual(cursor_in_visible, text_max_width,
                    f"Cursor should be within visible window at position {cursor_pos}")
