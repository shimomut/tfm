"""
Test BaseListDialog TTK Integration

This test verifies that BaseListDialog has been successfully migrated to use
the TTK Renderer API instead of curses.

Run with: PYTHONPATH=.:src:ttk pytest test/test_base_list_dialog_ttk_integration.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from ttk import TextAttribute, KeyCode
from ttk import KeyEvent


class TestBaseListDialogTTKIntegration(unittest.TestCase):
    """Test BaseListDialog TTK integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        
        # Create mock config
        self.mock_config = Mock()
        self.mock_config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        self.mock_config.LIST_DIALOG_MIN_HEIGHT = 15
        
        # Import after mocking to avoid import-time dependencies
        import sys
        from tfm_base_list_dialog import BaseListDialog
        self.BaseListDialog = BaseListDialog
    def test_init_accepts_renderer(self):
        """Test that BaseListDialog accepts renderer parameter"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        
        self.assertIsNotNone(dialog.renderer)
        self.assertEqual(dialog.renderer, self.mock_renderer)
        
    def test_handle_common_navigation_uses_input_event(self):
        """Test that handle_common_navigation uses KeyEvent instead of key codes"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        items = ['item1', 'item2', 'item3']
        
        # Test UP arrow
        event = KeyEvent(key_code=KeyCode.UP, char=None, modifiers=0)
        dialog.selected = 1
        result = dialog.handle_common_navigation(event, items)
        self.assertTrue(result)
        self.assertEqual(dialog.selected, 0)
        
        # Test DOWN arrow
        event = KeyEvent(key_code=KeyCode.DOWN, char=None, modifiers=0)
        result = dialog.handle_common_navigation(event, items)
        self.assertTrue(result)
        self.assertEqual(dialog.selected, 1)
        
        # Test ESCAPE
        event = KeyEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=0)
        result = dialog.handle_common_navigation(event, items)
        self.assertEqual(result, 'cancel')
        
        # Test ENTER
        event = KeyEvent(key_code=KeyCode.ENTER, char=None, modifiers=0)
        result = dialog.handle_common_navigation(event, items)
        self.assertEqual(result, 'select')
        
    def test_draw_dialog_frame_uses_renderer(self):
        """Test that draw_dialog_frame uses renderer instead of stdscr"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        
        # Call draw_dialog_frame
        start_y, start_x, dialog_width, dialog_height = dialog.draw_dialog_frame("Test Dialog")
        
        # Verify renderer methods were called
        self.mock_renderer.get_dimensions.assert_called()
        self.mock_renderer.draw_hline.assert_called()
        self.mock_renderer.draw_text.assert_called()
        
        # Verify dimensions are reasonable
        self.assertGreater(dialog_width, 0)
        self.assertGreater(dialog_height, 0)
        
    def test_draw_text_input_uses_renderer(self):
        """Test that draw_text_input uses renderer"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        
        # Mock the text editor's draw method
        dialog.text_editor.draw = Mock()
        
        # Call draw_text_input
        dialog.draw_text_input(5, 10, 60, "Search:")
        
        # Verify text editor's draw was called with renderer
        dialog.text_editor.draw.assert_called_once()
        call_args = dialog.text_editor.draw.call_args[0]
        self.assertEqual(call_args[0], self.mock_renderer)
        
    def test_draw_separator_uses_renderer(self):
        """Test that draw_separator uses renderer"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        
        # Call draw_separator
        dialog.draw_separator(10, 5, 60)
        
        # Verify renderer.draw_text was called
        self.mock_renderer.draw_text.assert_called()
        
        # Verify separator line was drawn
        call_args = self.mock_renderer.draw_text.call_args
        self.assertIn("├", call_args[0][2])  # Check for separator character
        
    def test_draw_list_items_uses_renderer(self):
        """Test that draw_list_items uses renderer"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        items = ['item1', 'item2', 'item3']
        
        # Call draw_list_items
        dialog.draw_list_items(items, 5, 15, 10, 50)
        
        # Verify renderer.draw_text was called for items
        self.mock_renderer.draw_text.assert_called()
        
        # Verify at least one item was drawn
        self.assertGreater(self.mock_renderer.draw_text.call_count, 0)
        
    def test_draw_scrollbar_uses_renderer(self):
        """Test that draw_scrollbar uses renderer"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        items = ['item' + str(i) for i in range(20)]  # More items than can fit
        
        # Call draw_scrollbar
        dialog.draw_scrollbar(items, 5, 10, 70)
        
        # Verify renderer.draw_text was called for scrollbar
        self.mock_renderer.draw_text.assert_called()
        
    def test_draw_help_text_uses_renderer(self):
        """Test that draw_help_text uses renderer"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        
        # Call draw_help_text
        dialog.draw_help_text("Press ESC to cancel", 20, 5, 60)
        
        # Verify renderer.draw_text was called
        self.mock_renderer.draw_text.assert_called()
        
        # Verify help text was drawn
        call_args = self.mock_renderer.draw_text.call_args[0]
        self.assertIn("ESC", call_args[2])
        
    def test_no_curses_imports(self):
        """Test that BaseListDialog doesn't import curses"""
        import tfm_base_list_dialog
        import sys
        
        # Check that curses is not imported in the module
        self.assertNotIn('curses', dir(tfm_base_list_dialog))
        
    def test_uses_text_attribute_enum(self):
        """Test that BaseListDialog uses TextAttribute enum"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        
        # Draw something that uses attributes
        dialog.draw_dialog_frame("Test")
        
        # Verify TextAttribute values were used
        for call in self.mock_renderer.draw_text.call_args_list:
            if len(call[1]) > 0 and 'attributes' in call[1]:
                attributes = call[1]['attributes']
                # Verify it's an integer (TextAttribute enum value)
                self.assertIsInstance(attributes, int)
                
    def test_page_up_down_navigation(self):
        """Test PAGE_UP and PAGE_DOWN navigation"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        items = ['item' + str(i) for i in range(30)]
        
        # Test PAGE_DOWN
        dialog.selected = 0
        event = KeyEvent(key_code=KeyCode.PAGE_DOWN, char=None, modifiers=0)
        result = dialog.handle_common_navigation(event, items)
        self.assertTrue(result)
        self.assertEqual(dialog.selected, 10)
        
        # Test PAGE_UP
        event = KeyEvent(key_code=KeyCode.PAGE_UP, char=None, modifiers=0)
        result = dialog.handle_common_navigation(event, items)
        self.assertTrue(result)
        self.assertEqual(dialog.selected, 0)
        
    def test_home_end_navigation(self):
        """Test HOME and END navigation"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        items = ['item' + str(i) for i in range(30)]
        
        # Test END
        dialog.selected = 0
        event = KeyEvent(key_code=KeyCode.END, char=None, modifiers=0)
        result = dialog.handle_common_navigation(event, items)
        self.assertTrue(result)
        self.assertEqual(dialog.selected, 29)
        
        # Test HOME
        event = KeyEvent(key_code=KeyCode.HOME, char=None, modifiers=0)
        result = dialog.handle_common_navigation(event, items)
        self.assertTrue(result)
        self.assertEqual(dialog.selected, 0)
        
    def test_color_usage_returns_tuples(self):
        """Test that color functions return (color_pair, attributes) tuples"""
        dialog = self.BaseListDialog(self.mock_config, renderer=self.mock_renderer)
        
        # Draw dialog frame which uses colors
        dialog.draw_dialog_frame("Test")
        
        # Verify that draw_text was called with color_pair and attributes as separate parameters
        for call in self.mock_renderer.draw_text.call_args_list:
            if len(call[1]) > 0:
                self.assertIn('color_pair', call[1])
                self.assertIn('attributes', call[1])
