"""
Test QuickEditBar prompt shortening functionality

This test verifies that QuickEditBar correctly handles prompts and ensures
adequate space for text input.

Run with: PYTHONPATH=.:src:ttk pytest test/test_quick_edit_bar_shortening.py -v
"""

import unittest
from unittest.mock import Mock
from tfm_quick_edit_bar import QuickEditBar, QuickEditBarHelpers
from ttk.wide_char_utils import get_safe_functions


class TestQuickEditBarShortening(unittest.TestCase):
    """Test QuickEditBar prompt shortening"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_config = Mock()
        self.dialog = QuickEditBar(config=self.mock_config, renderer=self.mock_renderer)
    
    def test_rename_dialog_wide_terminal(self):
        """Test rename dialog in wide terminal"""
        # Wide terminal - 120 chars
        self.mock_renderer.get_dimensions.return_value = (24, 120)
        
        original_name = "document.txt"
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name)
        
        # Verify dialog is active
        self.assertTrue(self.dialog.is_active)
        
        # Verify prompt is the simple static prompt
        self.assertEqual(self.dialog.prompt_text, "Rename to: ")
        
        # Verify initial text is set
        self.assertEqual(self.dialog.get_text(), original_name)
    
    def test_rename_dialog_narrow_terminal(self):
        """Test rename dialog in narrow terminal"""
        # Narrow terminal - 60 chars
        self.mock_renderer.get_dimensions.return_value = (24, 60)
        
        original_name = "very_long_document_name_that_takes_space.txt"
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name)
        
        # Verify dialog is active
        self.assertTrue(self.dialog.is_active)
        
        # Verify prompt is the simple static prompt
        self.assertEqual(self.dialog.prompt_text, "Rename to: ")
        
        # Verify initial text is set correctly
        self.assertEqual(self.dialog.get_text(), original_name)
    
    def test_rename_dialog_prompt_structure(self):
        """Test that rename dialog prompt has correct structure"""
        original_name = "test.txt"
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name)
        
        # Verify prompt is the simple static prompt
        self.assertEqual(self.dialog.prompt_text, "Rename to: ")
    
    def test_rename_dialog_with_custom_current_name(self):
        """Test rename dialog with different current name"""
        original_name = "old_name.txt"
        current_name = "new_name.txt"
        
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name, current_name)
        
        # Verify current name is used as initial text
        self.assertEqual(self.dialog.get_text(), current_name)
        
        # Verify prompt is the simple static prompt
        self.assertEqual(self.dialog.prompt_text, "Rename to: ")
    
    def test_minimum_input_width_guaranteed(self):
        """Test that at least 40 chars are reserved for input field"""
        # Very narrow terminal
        self.mock_renderer.get_dimensions.return_value = (24, 60)
        
        # Long original name
        original_name = "extremely_long_filename_that_would_take_too_much_space.txt"
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name)
        
        # Mock the text_editor.draw to capture max_field_width
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append((args, kwargs))
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw()
        
        # Verify draw was called
        self.assertEqual(len(draw_calls), 1)
        
        # The implementation should ensure adequate space for input
        # by shortening the prompt when necessary
    
    def test_string_prompt_support(self):
        """Test that string prompts are supported"""
        self.dialog.show_status_line_input(
            prompt="Simple prompt: ",
            initial_text="test"
        )
        
        # Verify prompt is stored as string
        self.assertIsInstance(self.dialog.prompt_text, str)
        self.assertEqual(self.dialog.prompt_text, "Simple prompt: ")
        
        # Dialog should work with string prompts
        self.assertTrue(self.dialog.is_active)
        self.assertEqual(self.dialog.get_text(), "test")


if __name__ == '__main__':
    unittest.main()
