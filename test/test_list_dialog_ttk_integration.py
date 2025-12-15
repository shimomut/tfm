#!/usr/bin/env python3
"""
Test suite for ListDialog TTK integration
Tests the migration from curses to TTK Renderer API
"""

import unittest
import sys
from unittest.mock import Mock, MagicMock, patch, call
from ttk import TextAttribute, KeyCode, KeyEvent, ModifierKey


class TestListDialogTTKIntegration(unittest.TestCase):
    """Test ListDialog TTK integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Import after setting up path
        sys.path.insert(0, 'src')
        from tfm_list_dialog import ListDialog
        from tfm_path import Path
        self.ListDialog = ListDialog
        self.Path = Path
        
        self.config = Mock()
        self.config.LIST_DIALOG_WIDTH_RATIO = 0.6
        self.config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        self.config.LIST_DIALOG_MIN_WIDTH = 40
        self.config.LIST_DIALOG_MIN_HEIGHT = 15
        
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (24, 80)
        
        self.dialog = self.ListDialog(self.config, self.renderer)
        
    def test_initialization_with_renderer(self):
        """Test that ListDialog initializes with renderer parameter"""
        self.assertIsNotNone(self.dialog.renderer)
        self.assertEqual(self.dialog.renderer, self.renderer)
        self.assertFalse(self.dialog.is_active)
        self.assertEqual(self.dialog.selected, 0)
        self.assertEqual(self.dialog.scroll, 0)
        
    def test_show_dialog(self):
        """Test showing the dialog with items"""
        items = ["Apple", "Banana", "Cherry"]
        callback = Mock()
        
        self.dialog.show("Test Dialog", items, callback)
        
        self.assertTrue(self.dialog.is_active)
        self.assertEqual(self.dialog.title, "Test Dialog")
        self.assertEqual(self.dialog.items, items)
        self.assertEqual(self.dialog.filtered_items, items)
        self.assertEqual(self.dialog.callback, callback)
        self.assertTrue(self.dialog.content_changed)
        
    def test_exit_dialog(self):
        """Test exiting the dialog"""
        self.dialog.show("Test", ["Item"], Mock())
        self.dialog.exit()
        
        self.assertFalse(self.dialog.is_active)
        self.assertEqual(self.dialog.title, "")
        self.assertEqual(self.dialog.items, [])
        self.assertEqual(self.dialog.filtered_items, [])
        self.assertIsNone(self.dialog.callback)
        
    def test_handle_input_escape_cancels(self):
        """Test that ESC key cancels the dialog"""
        callback = Mock()
        self.dialog.show("Test", ["Item"], callback)
        
        event = KeyEvent(key_code=KeyCode.ESCAPE, char='', modifiers=ModifierKey.NONE)
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        self.assertFalse(self.dialog.is_active)
        callback.assert_called_once_with(None)
        
    def test_handle_input_enter_selects(self):
        """Test that Enter key selects current item"""
        callback = Mock()
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test", items, callback)
        self.dialog.selected = 1
        
        event = KeyEvent(key_code=KeyCode.ENTER, char='', modifiers=ModifierKey.NONE)
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        self.assertFalse(self.dialog.is_active)
        callback.assert_called_once_with("Banana")
        
    def test_handle_input_navigation_up(self):
        """Test up arrow navigation"""
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test", items, Mock())
        self.dialog.selected = 2
        
        event = KeyEvent(key_code=KeyCode.UP, char='', modifiers=ModifierKey.NONE)
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.selected, 1)
        self.assertTrue(self.dialog.content_changed)
        
    def test_handle_input_navigation_down(self):
        """Test down arrow navigation"""
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test", items, Mock())
        self.dialog.selected = 0
        
        event = KeyEvent(key_code=KeyCode.DOWN, char='', modifiers=ModifierKey.NONE)
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.selected, 1)
        self.assertTrue(self.dialog.content_changed)
        
    def test_handle_input_text_filters_items(self):
        """Test that typing filters the item list"""
        items = ["Apple", "Banana", "Cherry", "Apricot"]
        self.dialog.show("Test", items, Mock())
        
        # Type 'a' to filter (use 0 for no special key)
        event = KeyEvent(key_code=0, char='a', modifiers=ModifierKey.NONE)
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        # Should filter to items containing 'a' (case-insensitive)
        # Apple, Banana, Apricot contain 'a', but Cherry does not
        self.assertEqual(len(self.dialog.filtered_items), 3)
        self.assertTrue(self.dialog.content_changed)
        
    def test_filter_items_case_insensitive(self):
        """Test that filtering is case-insensitive"""
        items = ["Apple", "banana", "CHERRY"]
        self.dialog.show("Test", items, Mock())
        
        # Manually set search text and filter
        self.dialog.text_editor.text = "app"
        self.dialog._filter_items()
        
        self.assertEqual(len(self.dialog.filtered_items), 1)
        self.assertEqual(self.dialog.filtered_items[0], "Apple")
        
    def test_filter_items_resets_selection(self):
        """Test that filtering resets selection to top"""
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test", items, Mock())
        self.dialog.selected = 2
        
        self.dialog.text_editor.text = "ban"
        self.dialog._filter_items()
        
        self.assertEqual(self.dialog.selected, 0)
        self.assertEqual(self.dialog.scroll, 0)
        
    def test_draw_uses_renderer(self):
        """Test that draw() uses renderer instead of stdscr"""
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test Dialog", items, Mock())
        
        self.dialog.draw()
        
        # Verify renderer methods were called
        self.renderer.get_dimensions.assert_called()
        self.renderer.draw_text.assert_called()
        self.renderer.draw_hline.assert_called()
        
    def test_draw_displays_title(self):
        """Test that draw() displays the dialog title"""
        self.dialog.show("My Title", ["Item"], Mock())
        
        self.dialog.draw()
        
        # Check that title was drawn
        draw_calls = self.renderer.draw_text.call_args_list
        title_drawn = any(" My Title " in str(call) for call in draw_calls)
        self.assertTrue(title_drawn, "Title should be drawn")
        
    def test_draw_displays_items(self):
        """Test that draw() displays list items"""
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test", items, Mock())
        
        self.dialog.draw()
        
        # Check that items were drawn
        draw_calls = self.renderer.draw_text.call_args_list
        items_drawn = [any(item in str(call) for call in draw_calls) for item in items]
        self.assertTrue(all(items_drawn), "All items should be drawn")
        
    def test_draw_highlights_selected_item(self):
        """Test that draw() highlights the selected item"""
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test", items, Mock())
        self.dialog.selected = 1
        
        self.dialog.draw()
        
        # Check that selected item has REVERSE attribute
        draw_calls = self.renderer.draw_text.call_args_list
        banana_calls = [call for call in draw_calls if "Banana" in str(call)]
        self.assertTrue(len(banana_calls) > 0, "Selected item should be drawn")
        
        # Check for REVERSE attribute in the call
        has_reverse = any(
            call.kwargs.get('attributes', 0) & TextAttribute.REVERSE 
            for call in banana_calls
        )
        self.assertTrue(has_reverse, "Selected item should have REVERSE attribute")
        
    def test_draw_shows_status_info(self):
        """Test that draw() shows status information"""
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test", items, Mock())
        self.dialog.selected = 1
        
        self.dialog.draw()
        
        # Check that status text was drawn
        draw_calls = self.renderer.draw_text.call_args_list
        status_drawn = any("2/3 items" in str(call) for call in draw_calls)
        self.assertTrue(status_drawn, "Status info should be drawn")
        
    def test_draw_shows_filter_in_status(self):
        """Test that draw() shows filter text in status"""
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test", items, Mock())
        self.dialog.text_editor.text = "app"
        self.dialog._filter_items()
        
        self.dialog.draw()
        
        # Check that filter text appears in status
        draw_calls = self.renderer.draw_text.call_args_list
        filter_shown = any("Filter: 'app'" in str(call) for call in draw_calls)
        self.assertTrue(filter_shown, "Filter text should be shown in status")
        
    def test_draw_shows_help_text(self):
        """Test that draw() shows help text"""
        self.dialog.show("Test", ["Item"], Mock())
        
        # Reset mock to clear show() calls
        self.renderer.reset_mock()
        
        self.dialog.draw()
        
        # Check that help text was drawn
        draw_calls = self.renderer.draw_text.call_args_list
        # Extract all text arguments from draw calls
        all_texts = []
        for call_obj in draw_calls:
            args, kwargs = call_obj
            if args and len(args) >= 3:
                all_texts.append(str(args[2]))  # Third argument is the text
        
        # Join all text and check for help text components
        combined_text = ' '.join(all_texts)
        # The help text should contain navigation and cancel instructions
        has_help = any(keyword in combined_text for keyword in ['ESC', 'cancel', 'select', 'choose'])
        self.assertTrue(has_help, f"Help text should be drawn. Texts: {all_texts[-5:]}")
        
    def test_draw_shows_custom_help_text(self):
        """Test that draw() shows custom help text when provided"""
        custom_help = "Custom help text here"
        self.dialog.show("Test", ["Item"], Mock(), custom_help_text=custom_help)
        
        self.dialog.draw()
        
        # Check that custom help text was drawn
        draw_calls = self.renderer.draw_text.call_args_list
        custom_help_drawn = any(custom_help in str(call) for call in draw_calls)
        self.assertTrue(custom_help_drawn, "Custom help text should be drawn")
        
    def test_needs_redraw_when_content_changed(self):
        """Test that needs_redraw() returns True when content changed"""
        self.dialog.show("Test", ["Item"], Mock())
        self.assertTrue(self.dialog.needs_redraw())
        
    def test_needs_redraw_false_after_draw(self):
        """Test that needs_redraw() returns False after drawing"""
        self.dialog.show("Test", ["Item"], Mock())
        self.dialog.draw()
        self.assertFalse(self.dialog.needs_redraw())
        
    def test_custom_key_handler(self):
        """Test that custom key handler is called"""
        custom_handler = Mock(return_value=True)
        self.dialog.show("Test", ["Item"], Mock(), custom_key_handler=custom_handler)
        
        event = KeyEvent(key_code=KeyCode.F1, char='', modifiers=ModifierKey.NONE)
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        custom_handler.assert_called_once_with(event)
        
    def test_handle_input_page_up(self):
        """Test page up navigation"""
        items = [f"Item {i}" for i in range(20)]
        self.dialog.show("Test", items, Mock())
        self.dialog.selected = 15
        
        event = KeyEvent(key_code=KeyCode.PAGE_UP, char='', modifiers=ModifierKey.NONE)
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.selected, 5)  # Moved up by 10
        
    def test_handle_input_page_down(self):
        """Test page down navigation"""
        items = [f"Item {i}" for i in range(20)]
        self.dialog.show("Test", items, Mock())
        self.dialog.selected = 5
        
        event = KeyEvent(key_code=KeyCode.PAGE_DOWN, char='', modifiers=ModifierKey.NONE)
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.selected, 15)  # Moved down by 10
        
    def test_handle_input_home(self):
        """Test home key navigation"""
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test", items, Mock())
        self.dialog.selected = 2
        
        event = KeyEvent(key_code=KeyCode.HOME, char='', modifiers=ModifierKey.NONE)
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.selected, 0)
        
    def test_handle_input_end(self):
        """Test end key navigation"""
        items = ["Apple", "Banana", "Cherry"]
        self.dialog.show("Test", items, Mock())
        self.dialog.selected = 0
        
        event = KeyEvent(key_code=KeyCode.END, char='', modifiers=ModifierKey.NONE)
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.selected, 2)


class TestListDialogHelpers(unittest.TestCase):
    """Test ListDialogHelpers functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Import after setting up path
        sys.path.insert(0, 'src')
        from tfm_list_dialog import ListDialog, ListDialogHelpers
        self.ListDialog = ListDialog
        self.ListDialogHelpers = ListDialogHelpers
        
        self.config = Mock()
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (24, 80)
        self.list_dialog = self.ListDialog(self.config, self.renderer)
        
    def test_show_demo(self):
        """Test demo function"""
        self.ListDialogHelpers.show_demo(self.list_dialog)
        
        self.assertTrue(self.list_dialog.is_active)
        self.assertEqual(self.list_dialog.title, "Choose a Fruit")
        self.assertTrue(len(self.list_dialog.items) > 0)
        
    @patch('tfm_list_dialog.get_favorite_directories')
    def test_show_favorite_directories_empty(self, mock_get_favs):
        """Test showing favorite directories when none configured"""
        mock_get_favs.return_value = []
        print_func = Mock()
        pane_manager = Mock()
        
        self.ListDialogHelpers.show_favorite_directories(self.list_dialog, pane_manager, print_func)
        
        print_func.assert_called_once_with("No favorite directories configured")
        self.assertFalse(self.list_dialog.is_active)
        
    @patch('tfm_list_dialog.get_favorite_directories')
    def test_show_favorite_directories_with_items(self, mock_get_favs):
        """Test showing favorite directories with items"""
        mock_get_favs.return_value = [
            {'name': 'Home', 'path': '/home/user'},
            {'name': 'Documents', 'path': '/home/user/docs'}
        ]
        print_func = Mock()
        pane_manager = Mock()
        
        self.ListDialogHelpers.show_favorite_directories(self.list_dialog, pane_manager, print_func)
        
        self.assertTrue(self.list_dialog.is_active)
        self.assertEqual(self.list_dialog.title, "Go to Favorite Directory")
        self.assertEqual(len(self.list_dialog.items), 2)
        
    @patch('tfm_list_dialog.get_programs')
    def test_show_programs_dialog_empty(self, mock_get_progs):
        """Test showing programs dialog when none configured"""
        mock_get_progs.return_value = []
        print_func = Mock()
        execute_func = Mock()
        
        self.ListDialogHelpers.show_programs_dialog(self.list_dialog, execute_func, print_func)
        
        print_func.assert_called_once_with("No external programs configured")
        self.assertFalse(self.list_dialog.is_active)
        
    @patch('tfm_list_dialog.get_programs')
    def test_show_programs_dialog_with_items(self, mock_get_progs):
        """Test showing programs dialog with items"""
        mock_get_progs.return_value = [
            {'name': 'Editor', 'command': ['vim']},
            {'name': 'Browser', 'command': ['firefox']}
        ]
        print_func = Mock()
        execute_func = Mock()
        
        self.ListDialogHelpers.show_programs_dialog(self.list_dialog, execute_func, print_func)
        
        self.assertTrue(self.list_dialog.is_active)
        self.assertEqual(self.list_dialog.title, "External Programs")
        self.assertEqual(len(self.list_dialog.items), 2)


if __name__ == '__main__':
    unittest.main()
