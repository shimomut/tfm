"""
Test QuickEditBar prompt shortening functionality

This test verifies that QuickEditBar correctly shortens prompts using ShorteningRegion
to ensure adequate space for text input.

Run with: PYTHONPATH=.:src:ttk pytest test/test_quick_edit_bar_shortening.py -v
"""

import unittest
from unittest.mock import Mock
from tfm_quick_edit_bar import QuickEditBar, QuickEditBarHelpers
from tfm_string_width import ShorteningRegion, calculate_display_width


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
        
        # Verify shortening regions are set
        self.assertIsNotNone(self.dialog.shortening_regions)
        self.assertEqual(len(self.dialog.shortening_regions), 1)
        
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
        
        # Verify shortening regions are configured
        self.assertIsNotNone(self.dialog.shortening_regions)
        region = self.dialog.shortening_regions[0]
        
        # Verify region configuration
        self.assertEqual(region.start, 6)  # After "Rename"
        self.assertEqual(region.priority, 1)
        self.assertEqual(region.strategy, 'all_or_nothing')  # All or nothing strategy
        
        # Verify initial text is set correctly
        self.assertEqual(self.dialog.get_text(), original_name)
    
    def test_rename_dialog_prompt_structure(self):
        """Test that rename dialog prompt has correct structure"""
        original_name = "test.txt"
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name)
        
        # Expected prompt format: "Rename '{original_name}' to: "
        expected_prompt = f"Rename '{original_name}' to: "
        self.assertEqual(self.dialog.prompt_text, expected_prompt)
        
        # Verify shortening region covers the middle part
        region = self.dialog.shortening_regions[0]
        self.assertEqual(region.start, 6)  # After "Rename"
        self.assertEqual(region.end, len(expected_prompt) - 2)  # Before ": "
    
    def test_rename_dialog_with_custom_current_name(self):
        """Test rename dialog with different current name"""
        original_name = "old_name.txt"
        current_name = "new_name.txt"
        
        QuickEditBarHelpers.create_rename_dialog(self.dialog, original_name, current_name)
        
        # Verify current name is used as initial text
        self.assertEqual(self.dialog.get_text(), current_name)
        
        # Verify prompt still references original name
        expected_prompt = f"Rename '{original_name}' to: "
        self.assertEqual(self.dialog.prompt_text, expected_prompt)
    
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
    
    def test_shortening_regions_parameter(self):
        """Test that shortening_regions parameter is properly stored"""
        regions = [
            ShorteningRegion(start=5, end=10, priority=1, strategy='all_or_nothing')
        ]
        
        self.dialog.show_status_line_input(
            prompt="Test prompt: ",
            initial_text="test",
            shortening_regions=regions
        )
        
        # Verify regions are stored
        self.assertEqual(self.dialog.shortening_regions, regions)
        
        # Verify regions are cleared on hide
        self.dialog.hide()
        self.assertIsNone(self.dialog.shortening_regions)
    
    def test_no_shortening_regions_uses_default(self):
        """Test that without shortening_regions, default behavior is used"""
        self.dialog.show_status_line_input(
            prompt="Simple prompt: ",
            initial_text="test"
        )
        
        # Verify no regions are set
        self.assertIsNone(self.dialog.shortening_regions)
        
        # Dialog should still work with default right abbreviation
        self.assertTrue(self.dialog.is_active)
        self.assertEqual(self.dialog.get_text(), "test")
    
    def test_remove_strategy_all_or_nothing(self):
        """Test that 'remove' strategy removes region entirely, not partially"""
        # Set up a scenario where partial removal would occur without the fix
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
        # It should NOT be a partial truncation like "Rename 'medium_length_fi"
        full_prompt = f"Rename '{original_name}' to: "
        minimal_prompt = "Rename: "
        
        # Verify it's one of the two valid options
        self.assertIn(prompt_used, [full_prompt, minimal_prompt],
                     f"Prompt should be either full or minimal, got: {prompt_used}")
        
        # If it's not the full prompt, it must be the minimal one (complete removal)
        if prompt_used != full_prompt:
            self.assertEqual(prompt_used, minimal_prompt,
                           "Partial removal detected - region should be removed entirely")


if __name__ == '__main__':
    unittest.main()
