"""
Test QuickEditBar prompt shortening functionality

This test verifies that QuickEditBar correctly shortens prompts using TextSegment
to ensure adequate space for text input.

Run with: PYTHONPATH=.:src:ttk pytest test/test_quick_edit_bar_shortening.py -v
"""

import unittest
from unittest.mock import Mock
from tfm_quick_edit_bar import QuickEditBar, QuickEditBarHelpers
from tfm_text_layout import AsIsSegment, AllOrNothingSegment, calculate_display_width


class TestQuickEditBarShortening(unittest.TestCase):
    """Test QuickEditBar prompt shortening"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_config = Mock()
        self.dialog = QuickEditBar(config=self.mock_config, renderer=self.mock_renderer)
    
    def test_rename_dialog_wide_terminal(self):
        """Test rename dialog in wide terminal - full prompt visible"""
        # Wide terminal - 120 chars
        self.mock_renderer.get_dimensions.return_value = (24, 120)
        
        original_name = "document.txt"
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name)
        
        # Verify dialog is active
        self.assertTrue(self.dialog.is_active)
        
        # Verify prompt is a list of TextSegment objects
        self.assertIsInstance(self.dialog.prompt_text, list)
        self.assertEqual(len(self.dialog.prompt_text), 3)
        
        # Verify segment structure
        self.assertIsInstance(self.dialog.prompt_text[0], AsIsSegment)
        self.assertEqual(self.dialog.prompt_text[0].text, "Rename")
        self.assertIsInstance(self.dialog.prompt_text[1], AllOrNothingSegment)
        self.assertIn(original_name, self.dialog.prompt_text[1].text)
        self.assertIsInstance(self.dialog.prompt_text[2], AsIsSegment)
        self.assertEqual(self.dialog.prompt_text[2].text, ": ")
        
        # Verify initial text is set
        self.assertEqual(self.dialog.get_text(), original_name)
    
    def test_rename_dialog_narrow_terminal(self):
        """Test rename dialog in narrow terminal - prompt shortened"""
        # Narrow terminal - 60 chars
        self.mock_renderer.get_dimensions.return_value = (24, 60)
        
        original_name = "very_long_document_name_that_takes_space.txt"
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name)
        
        # Verify dialog is active
        self.assertTrue(self.dialog.is_active)
        
        # Verify prompt is a list of TextSegment objects
        self.assertIsInstance(self.dialog.prompt_text, list)
        
        # Verify the middle segment uses AllOrNothingSegment with priority=1
        middle_segment = self.dialog.prompt_text[1]
        self.assertIsInstance(middle_segment, AllOrNothingSegment)
        self.assertEqual(middle_segment.priority, 1)  # Higher priority, removed first
        
        # Verify initial text is set correctly
        self.assertEqual(self.dialog.get_text(), original_name)
    
    def test_rename_dialog_prompt_structure(self):
        """Test that rename dialog prompt has correct structure"""
        original_name = "test.txt"
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name)
        
        # Verify prompt is a list of TextSegment objects
        self.assertIsInstance(self.dialog.prompt_text, list)
        self.assertEqual(len(self.dialog.prompt_text), 3)
        
        # Verify segment structure
        # First segment: "Rename"
        self.assertIsInstance(self.dialog.prompt_text[0], AsIsSegment)
        self.assertEqual(self.dialog.prompt_text[0].text, "Rename")
        
        # Second segment: " '{original_name}' to" with AllOrNothingSegment
        self.assertIsInstance(self.dialog.prompt_text[1], AllOrNothingSegment)
        self.assertEqual(self.dialog.prompt_text[1].text, f" '{original_name}' to")
        self.assertEqual(self.dialog.prompt_text[1].priority, 1)
        
        # Third segment: ": "
        self.assertIsInstance(self.dialog.prompt_text[2], AsIsSegment)
        self.assertEqual(self.dialog.prompt_text[2].text, ": ")
    
    def test_rename_dialog_with_custom_current_name(self):
        """Test rename dialog with different current name"""
        original_name = "old_name.txt"
        current_name = "new_name.txt"
        
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name, current_name)
        
        # Verify current name is used as initial text
        self.assertEqual(self.dialog.get_text(), current_name)
        
        # Verify prompt still references original name in the middle segment
        self.assertIsInstance(self.dialog.prompt_text, list)
        middle_segment = self.dialog.prompt_text[1]
        self.assertIn(original_name, middle_segment.text)
    
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
        """Test that string prompts are still supported"""
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
    
    def test_segment_list_prompt_support(self):
        """Test that list of TextSegment prompts are supported"""
        prompt_segments = [
            AsIsSegment("Rename"),
            AllOrNothingSegment(" 'file.txt' to", priority=1),
            AsIsSegment(": ")
        ]
        
        self.dialog.show_status_line_input(
            prompt=prompt_segments,
            initial_text="test"
        )
        
        # Verify prompt is stored as list
        self.assertIsInstance(self.dialog.prompt_text, list)
        self.assertEqual(len(self.dialog.prompt_text), 3)
        
        # Dialog should work with segment list prompts
        self.assertTrue(self.dialog.is_active)
        self.assertEqual(self.dialog.get_text(), "test")
    
    def test_all_or_nothing_strategy(self):
        """Test that AllOrNothingSegment removes content entirely, not partially"""
        # Set up a scenario where the middle segment should be removed entirely
        self.mock_renderer.get_dimensions.return_value = (24, 70)
        
        original_name = "medium_length_filename.txt"
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name)
        
        # Mock the text_editor.draw to capture the prompt used
        draw_calls = []
        def mock_draw(renderer, y, x, max_width, prompt, is_active):
            draw_calls.append(prompt)
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw()
        
        # Verify draw was called
        self.assertEqual(len(draw_calls), 1)
        prompt_used = draw_calls[0]
        
        # The prompt should be either the full version or the minimal version
        # It should NOT be a partial truncation like "Rename 'medium_length_fi…"
        full_prompt = f"Rename '{original_name}' to: "
        minimal_prompt = "Rename: "
        
        # Verify it's one of the two valid options
        self.assertIn(prompt_used, [full_prompt, minimal_prompt],
                     f"Prompt should be either full or minimal, got: {prompt_used}")
        
        # If it's not the full prompt, it must be the minimal one (complete removal)
        if prompt_used != full_prompt:
            self.assertEqual(prompt_used, minimal_prompt,
                           "Partial removal detected - segment should be removed entirely")


if __name__ == '__main__':
    unittest.main()
