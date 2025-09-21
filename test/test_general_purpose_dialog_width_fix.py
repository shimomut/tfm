#!/usr/bin/env python3
"""
Test for GeneralPurposeDialog width calculation fix

This test verifies that the input field width is calculated correctly
and doesn't truncate text unnecessarily due to incorrect width calculation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from unittest.mock import Mock, patch
from tfm_general_purpose_dialog import GeneralPurposeDialog


class TestGeneralPurposeDialogWidthFix(unittest.TestCase):
    """Test the width calculation fix in GeneralPurposeDialog"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dialog = GeneralPurposeDialog()
        
    @patch('tfm_general_purpose_dialog.get_status_color')
    def test_width_calculation_with_prompt(self, mock_get_status_color):
        """Test that max_width includes both prompt and input area"""
        # Mock the color function to avoid curses initialization
        mock_get_status_color.return_value = 0
        
        # Mock stdscr and safe_addstr_func
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 80)  # 80 character width
        
        mock_safe_addstr = Mock()
        
        # Show a dialog with a prompt
        prompt = "Enter filename: "  # 16 characters
        help_text = "ESC:cancel Enter:confirm"  # 24 characters
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            help_text=help_text,
            initial_text="test_file.txt"
        )
        
        # Mock the text_editor.draw method to capture the arguments
        draw_calls = []
        
        def mock_draw(*args, **kwargs):
            draw_calls.append(args)
            # Don't call the original draw to avoid curses issues
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw(mock_stdscr, mock_safe_addstr)
        
        # Verify that draw was called
        self.assertEqual(len(draw_calls), 1)
        
        # Extract the arguments passed to text_editor.draw
        args = draw_calls[0]
        stdscr, y, x, max_width, label = args[:5]
        is_active = args[5] if len(args) > 5 else True
        
        # Verify the arguments
        self.assertEqual(y, 23)  # status_y = height - 1 = 24 - 1 = 23
        self.assertEqual(x, 2)
        self.assertEqual(label, prompt)
        self.assertTrue(is_active)
        
        # Calculate expected max_width
        # help_space = len(help_text) + 6 = 24 + 6 = 30
        # max_field_width = width - help_space - 4 = 80 - 30 - 4 = 46
        expected_max_width = 46
        self.assertEqual(max_width, expected_max_width)
        
        # Verify that the available text width is reasonable
        # text_width = max_width - len(prompt) = 46 - 16 = 30
        available_text_width = max_width - len(prompt)
        self.assertEqual(available_text_width, 30)
        
        # This should be enough for reasonable input text
        self.assertGreaterEqual(available_text_width, 20)
        
    @patch('tfm_general_purpose_dialog.get_status_color')
    def test_width_calculation_without_help_text(self, mock_get_status_color):
        """Test width calculation when no help text is provided"""
        mock_get_status_color.return_value = 0
        
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        
        mock_safe_addstr = Mock()
        
        prompt = "Filter: "  # 8 characters
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            help_text="",  # No help text
            initial_text=""
        )
        
        # Mock the text_editor.draw method
        draw_calls = []
        
        def mock_draw(*args, **kwargs):
            draw_calls.append(args)
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw(mock_stdscr, mock_safe_addstr)
        
        # Extract max_width from the draw call
        max_width = draw_calls[0][3]
        
        # Calculate expected max_width when no help text
        # help_space = 0 (no help text)
        # max_field_width = width - help_space - 4 = 80 - 0 - 4 = 76
        expected_max_width = 76
        self.assertEqual(max_width, expected_max_width)
        
        # Available text width should be much larger
        available_text_width = max_width - len(prompt)
        self.assertEqual(available_text_width, 68)
        
    @patch('tfm_general_purpose_dialog.get_status_color')
    def test_long_text_input_not_truncated_unnecessarily(self, mock_get_status_color):
        """Test that long text input is not truncated due to width bug"""
        mock_get_status_color.return_value = 0
        
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 100)  # Wider terminal
        
        mock_safe_addstr = Mock()
        
        prompt = "Rename to: "  # 11 characters
        long_filename = "very_long_filename_that_should_not_be_truncated.txt"  # 51 characters
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            help_text="ESC:cancel Enter:confirm",
            initial_text=long_filename
        )
        
        # Mock the text_editor.draw method
        draw_calls = []
        
        def mock_draw(*args, **kwargs):
            draw_calls.append(args)
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw(mock_stdscr, mock_safe_addstr)
        
        # Extract max_width from the draw call
        max_width = draw_calls[0][3]
        
        # Calculate available text width
        available_text_width = max_width - len(prompt)
        
        # With the fix, there should be enough space for the long filename
        # help_space = 24 + 6 = 30
        # max_field_width = 100 - 30 - 4 = 66
        # available_text_width = 66 - 11 = 55
        self.assertEqual(available_text_width, 55)
        
        # The long filename (51 chars) should fit in the available space (55 chars)
        self.assertGreaterEqual(available_text_width, len(long_filename))

    def test_width_calculation_logic_directly(self):
        """Test the width calculation logic directly without drawing"""
        # Test the calculation logic that was fixed
        
        # Scenario 1: With help text
        width = 80
        prompt_text = "Enter filename: "  # 16 chars
        help_text = "ESC:cancel Enter:confirm"  # 24 chars
        
        # Old (buggy) calculation:
        # max_input_width = width - len(prompt_text) - help_space - 4
        # help_space = len(help_text) + 6 = 30
        # max_input_width = 80 - 16 - 30 - 4 = 30
        old_buggy_width = width - len(prompt_text) - (len(help_text) + 6) - 4
        
        # New (fixed) calculation:
        # max_field_width = width - help_space - 4
        # max_field_width = 80 - 30 - 4 = 46
        new_fixed_width = width - (len(help_text) + 6) - 4
        
        # The new calculation should give more space
        self.assertGreater(new_fixed_width, old_buggy_width)
        
        # Available text space with new calculation
        available_text_space = new_fixed_width - len(prompt_text)
        self.assertEqual(available_text_space, 30)
        
        # Scenario 2: Without help text
        width = 80
        prompt_text = "Filter: "  # 8 chars
        help_text = ""
        
        # Old calculation would be: 80 - 8 - 0 - 4 = 68
        old_buggy_width_no_help = width - len(prompt_text) - 0 - 4
        
        # New calculation: 80 - 0 - 4 = 76
        new_fixed_width_no_help = width - 0 - 4
        
        # New calculation should give more space
        self.assertGreater(new_fixed_width_no_help, old_buggy_width_no_help)
        
        # Available text space
        available_text_space_no_help = new_fixed_width_no_help - len(prompt_text)
        self.assertEqual(available_text_space_no_help, 68)


if __name__ == '__main__':
    unittest.main()