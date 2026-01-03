"""
Test edge cases for QuickEditBar width handling

This test verifies that the dialog handles narrow terminals correctly
without disappearing elements.

Run with: PYTHONPATH=.:src:ttk pytest test/test_dialog_width_edge_cases.py -v
"""

import unittest
from unittest.mock import Mock
from tfm_quick_edit_bar import QuickEditBar


class TestDialogWidthEdgeCases(unittest.TestCase):
    """Test edge cases for dialog width handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_config = Mock()
        self.dialog = QuickEditBar(config=self.mock_config, renderer=self.mock_renderer)
        
    def test_narrow_terminal_text_editor_visible(self):
        """Test that text editor remains visible even in narrow terminals"""
        # Very narrow terminal
        self.mock_renderer.get_dimensions.return_value = (24, 40)  # Only 40 characters wide
        
        prompt = "Rename file: "
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            initial_text="test.txt"
        )
        
        # Mock the text_editor.draw method to capture arguments
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append((args, kwargs))
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw()
        
        # Verify that draw was called (text editor is visible)
        self.assertEqual(len(draw_calls), 1)
        
        # Extract max_width from the draw call (should be in kwargs or args)
        if 'max_width' in draw_calls[0][1]:
            max_width = draw_calls[0][1]['max_width']
        else:
            max_width = draw_calls[0][0][3] if len(draw_calls[0][0]) > 3 else 40
        
        # Should have reasonable width even in narrow terminal
        self.assertGreater(max_width, len(prompt))
        
        # Available text width should be positive
        available_text_width = max_width - len(prompt)
        self.assertGreater(available_text_width, 0)
        
    def test_wide_terminal_text_editor_visible(self):
        """Test that text editor is visible in wide terminals"""
        # Wide terminal
        self.mock_renderer.get_dimensions.return_value = (24, 100)  # 100 characters wide
        
        prompt = "Filter: "
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            initial_text=""
        )
        
        # Mock the text_editor.draw method
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append((args, kwargs))
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw()
        
        # Verify that draw was called (text editor is visible)
        self.assertEqual(len(draw_calls), 1)
        
    def test_narrow_terminal_with_long_prompt(self):
        """Test that text editor is visible even with long prompt in narrow terminal"""
        # Very narrow terminal
        self.mock_renderer.get_dimensions.return_value = (24, 30)  # Only 30 characters wide
        
        prompt = "Enter long filename: "  # 20 characters
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            initial_text=""
        )
        
        # Mock the text_editor.draw method
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append((args, kwargs))
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw()
        
        # Text editor should still be drawn
        self.assertEqual(len(draw_calls), 1)
        
    def test_minimum_field_width_guaranteed(self):
        """Test that input field gets minimum width in extremely narrow terminal"""
        # Extremely narrow terminal
        self.mock_renderer.get_dimensions.return_value = (24, 25)  # Only 25 characters wide
        
        prompt = "Rename: "  # 8 characters
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            initial_text="file.txt"
        )
        
        # Mock the text_editor.draw method
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append((args, kwargs))
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw()
        
        # Text editor should still be drawn
        self.assertEqual(len(draw_calls), 1)
        
        # Extract max_width from the draw call
        if 'max_width' in draw_calls[0][1]:
            max_width = draw_calls[0][1]['max_width']
        else:
            max_width = draw_calls[0][0][3] if len(draw_calls[0][0]) > 3 else 25
        
        # Should have at least minimum width (prompt + 5 chars for input)
        min_expected_width = len(prompt) + 5
        self.assertGreaterEqual(max_width, min_expected_width)
        
    def test_long_input_text_handling(self):
        """Test that long input text is handled correctly"""
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        
        prompt = "Enter: "
        long_input = "very_long_input_text_that_takes_up_space"
        
        self.dialog.show_status_line_input(
            prompt=prompt,
            initial_text=long_input
        )
        
        # Mock the text_editor.draw method
        draw_calls = []
        def mock_draw(*args, **kwargs):
            draw_calls.append((args, kwargs))
        
        self.dialog.text_editor.draw = mock_draw
        
        # Draw the dialog
        self.dialog.draw()
        
        # Text editor should be drawn
        self.assertEqual(len(draw_calls), 1)
        
        # Verify the text was set correctly
        self.assertEqual(self.dialog.get_text(), long_input)
