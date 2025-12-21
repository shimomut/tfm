#!/usr/bin/env python3
"""
Test edge cases for QuickEditBar width handling

This test verifies that the dialog handles narrow terminals and help text
display correctly without disappearing elements.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from unittest.mock import Mock, patch
from tfm_quick_edit_bar import QuickEditBar


class TestDialogWidthEdgeCases(unittest.TestCase):
    """Test edge cases for dialog width handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dialog = QuickEditBar()
        
    @patch('tfm_quick_edit_bar.get_status_color')
    def test_narrow_terminal_text_editor_visible(self, mock_get_status_color):
        """Test that text editor remains visible even in narrow terminals"""
        mock_get_status_color.return_value = 0
        
        # Very narrow terminal
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 40)  # Only 40 characters wide
        mock_safe_addstr = Mock()
        
        prompt = "Rename file: "
        help_text = "ESC:cancel Enter:confirm"
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            help_text=help_text,
            initial_text="test.txt"
        )
        
        # Mock the text_editor.draw method to capture arguments
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append(args)
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw(mock_stdscr, mock_safe_addstr)
        
        # Verify that draw was called (text editor is visible)
        self.assertEqual(len(draw_calls), 1)
        
        # Extract max_width from the draw call
        max_width = draw_calls[0][3]
        
        # Should have reasonable width even in narrow terminal
        self.assertGreater(max_width, len(prompt))
        
        # Available text width should be positive
        available_text_width = max_width - len(prompt)
        self.assertGreater(available_text_width, 0)
        
    @patch('tfm_quick_edit_bar.get_status_color')
    def test_help_text_shows_when_space_available(self, mock_get_status_color):
        """Test that help text shows when there's adequate space"""
        mock_get_status_color.return_value = 0
        
        # Wide enough terminal for help text
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 100)  # 100 characters wide
        mock_safe_addstr = Mock()
        
        prompt = "Filter: "
        help_text = "ESC:cancel"
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            help_text=help_text,
            initial_text=""
        )
        
        # Mock the text_editor.draw method
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append(args)
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw(mock_stdscr, mock_safe_addstr)
        
        # Check if help text was drawn
        help_text_drawn = False
        for call in mock_safe_addstr.call_args_list:
            if len(call[0]) >= 3 and help_text in str(call[0][2]):
                help_text_drawn = True
                break
        
        self.assertTrue(help_text_drawn, "Help text should be drawn when space is available")
        
    @patch('tfm_quick_edit_bar.get_status_color')
    def test_help_text_hidden_when_no_space(self, mock_get_status_color):
        """Test that help text is hidden when terminal is too narrow"""
        mock_get_status_color.return_value = 0
        
        # Very narrow terminal
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 30)  # Only 30 characters wide
        mock_safe_addstr = Mock()
        
        prompt = "Enter long filename: "  # 20 characters
        help_text = "ESC:cancel Enter:confirm"  # 24 characters
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            help_text=help_text,
            initial_text=""
        )
        
        # Mock the text_editor.draw method
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append(args)
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw(mock_stdscr, mock_safe_addstr)
        
        # Text editor should still be drawn
        self.assertEqual(len(draw_calls), 1)
        
        # Check that help text was NOT drawn (no space)
        help_text_drawn = False
        for call in mock_safe_addstr.call_args_list:
            if len(call[0]) >= 3 and help_text in str(call[0][2]):
                help_text_drawn = True
                break
        
        self.assertFalse(help_text_drawn, "Help text should be hidden when no space available")
        
    @patch('tfm_quick_edit_bar.get_status_color')
    def test_minimum_field_width_guaranteed(self, mock_get_status_color):
        """Test that input field gets minimum width even without help text space"""
        mock_get_status_color.return_value = 0
        
        # Extremely narrow terminal
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 25)  # Only 25 characters wide
        mock_safe_addstr = Mock()
        
        prompt = "Rename: "  # 8 characters
        help_text = "ESC:cancel Enter:confirm"
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            help_text=help_text,
            initial_text="file.txt"
        )
        
        # Mock the text_editor.draw method
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append(args)
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw(mock_stdscr, mock_safe_addstr)
        
        # Text editor should still be drawn
        self.assertEqual(len(draw_calls), 1)
        
        # Extract max_width from the draw call
        max_width = draw_calls[0][3]
        
        # Should have at least minimum width (prompt + 5 chars for input)
        min_expected_width = len(prompt) + 5
        self.assertGreaterEqual(max_width, min_expected_width)
        
    @patch('tfm_quick_edit_bar.get_status_color')
    def test_help_text_positioning_no_overlap(self, mock_get_status_color):
        """Test that help text doesn't overlap with input field"""
        mock_get_status_color.return_value = 0
        
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        mock_safe_addstr = Mock()
        
        prompt = "Enter: "
        help_text = "Help"
        long_input = "very_long_input_text_that_takes_up_space"
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            help_text=help_text,
            initial_text=long_input
        )
        
        # Mock the text_editor.draw method
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append(args)
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw(mock_stdscr, mock_safe_addstr)
        
        # Find help text position
        help_x = None
        for call in mock_safe_addstr.call_args_list:
            if len(call[0]) >= 3 and help_text in str(call[0][2]):
                help_x = call[0][1]  # x position
                break
        
        if help_x is not None:
            # Calculate input field end position
            max_width = draw_calls[0][3]
            input_start_x = 2
            input_end_x = input_start_x + min(max_width, len(prompt) + len(long_input) + 1)
            
            # Help text should start after input field with gap
            self.assertGreater(help_x, input_end_x + 1, "Help text should not overlap input field")


if __name__ == '__main__':
    unittest.main()