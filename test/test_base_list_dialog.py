#!/usr/bin/env python3
"""
Test BaseListDialog and its derived classes
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from unittest.mock import Mock, MagicMock
from ttk import KeyEvent, KeyCode, ModifierKey

from tfm_base_list_dialog import BaseListDialog
from tfm_list_dialog import ListDialog
from tfm_search_dialog import SearchDialog
from tfm_jump_dialog import JumpDialog


class TestBaseListDialog(unittest.TestCase):
    """Test BaseListDialog functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        self.config.LIST_DIALOG_MIN_HEIGHT = 15
        self.base_dialog = BaseListDialog(self.config)
        
    def test_init(self):
        """Test BaseListDialog initialization"""
        self.assertFalse(self.base_dialog.is_active)
        self.assertEqual(self.base_dialog.selected, 0)
        self.assertEqual(self.base_dialog.scroll, 0)
        self.assertIsNotNone(self.base_dialog.text_editor)
        
    def test_exit(self):
        """Test exit method"""
        self.base_dialog.is_active = True
        self.base_dialog.selected = 5
        self.base_dialog.scroll = 2
        self.base_dialog.text_editor.text = "test"
        
        self.base_dialog.exit()
        
        self.assertFalse(self.base_dialog.is_active)
        self.assertEqual(self.base_dialog.selected, 0)
        self.assertEqual(self.base_dialog.scroll, 0)
        self.assertEqual(self.base_dialog.text_editor.text, "")
        
    def test_handle_common_navigation_cancel(self):
        """Test ESC key handling"""
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=0)
        result = self.base_dialog.handle_common_navigation(event, ["item1", "item2"])
        self.assertEqual(result, 'cancel')
        
    def test_handle_common_navigation_select(self):
        """Test ENTER key handling"""
        event = KeyEvent(key_code=KeyCode.ENTER, modifiers=0)
        result = self.base_dialog.handle_common_navigation(event, ["item1", "item2"])
        self.assertEqual(result, 'select')
        
    def test_handle_common_navigation_up_down(self):
        """Test UP/DOWN key handling"""
        items = ["item1", "item2", "item3"]
        
        # Test DOWN key
        event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0)
        result = self.base_dialog.handle_common_navigation(event, items)
        self.assertTrue(result)
        self.assertEqual(self.base_dialog.selected, 1)
        
        # Test UP key
        event = KeyEvent(key_code=KeyCode.UP, modifiers=0)
        result = self.base_dialog.handle_common_navigation(event, items)
        self.assertTrue(result)
        self.assertEqual(self.base_dialog.selected, 0)
        
    def test_adjust_scroll(self):
        """Test scroll adjustment"""
        self.base_dialog.selected = 15
        self.base_dialog._adjust_scroll(20, 10)  # 20 items, 10 content height
        
        # Should adjust scroll to keep selected item visible
        self.assertGreaterEqual(self.base_dialog.scroll, 6)  # 15 - 10 + 1


class TestListDialog(unittest.TestCase):
    """Test ListDialog functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.config.LIST_DIALOG_WIDTH_RATIO = 0.6
        self.config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        self.config.LIST_DIALOG_MIN_WIDTH = 40
        self.config.LIST_DIALOG_MIN_HEIGHT = 15
        self.list_dialog = ListDialog(self.config)
        
    def test_init(self):
        """Test ListDialog initialization"""
        self.assertIsInstance(self.list_dialog, BaseListDialog)
        self.assertEqual(self.list_dialog.title, "")
        self.assertEqual(self.list_dialog.items, [])
        self.assertEqual(self.list_dialog.filtered_items, [])
        self.assertIsNone(self.list_dialog.callback)
        
    def test_show(self):
        """Test show method"""
        items = ["apple", "banana", "cherry"]
        callback = Mock()
        
        self.list_dialog.show("Test Title", items, callback)
        
        self.assertTrue(self.list_dialog.is_active)
        self.assertEqual(self.list_dialog.title, "Test Title")
        self.assertEqual(self.list_dialog.items, items)
        self.assertEqual(self.list_dialog.filtered_items, items)
        self.assertEqual(self.list_dialog.callback, callback)
        
    def test_filter_items(self):
        """Test item filtering"""
        self.list_dialog.items = ["apple", "banana", "cherry", "apricot"]
        self.list_dialog.text_editor.text = "ap"
        
        self.list_dialog._filter_items()
        
        expected = ["apple", "apricot"]
        self.assertEqual(self.list_dialog.filtered_items, expected)
        self.assertEqual(self.list_dialog.selected, 0)
        self.assertEqual(self.list_dialog.scroll, 0)
        
    def test_handle_input_select(self):
        """Test item selection"""
        items = ["apple", "banana", "cherry"]
        callback = Mock()
        self.list_dialog.show("Test", items, callback)
        self.list_dialog.selected = 1
        
        result = self.list_dialog.handle_input(KeyEvent(key_code=KeyCode.ENTER, modifiers=ModifierKey.NONE))
        
        self.assertTrue(result)
        self.assertFalse(self.list_dialog.is_active)  # Should exit
        callback.assert_called_once_with("banana")


class TestSearchDialog(unittest.TestCase):
    """Test SearchDialog functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.config.MAX_SEARCH_RESULTS = 1000
        self.search_dialog = SearchDialog(self.config)
        
    def test_init(self):
        """Test SearchDialog initialization"""
        self.assertIsInstance(self.search_dialog, BaseListDialog)
        self.assertEqual(self.search_dialog.search_type, 'filename')
        self.assertEqual(self.search_dialog.results, [])
        self.assertFalse(self.search_dialog.searching)
        
    def test_show(self):
        """Test show method"""
        self.search_dialog.show('content')
        
        self.assertTrue(self.search_dialog.is_active)
        self.assertEqual(self.search_dialog.search_type, 'content')
        self.assertEqual(self.search_dialog.results, [])
        
    def test_handle_input_tab_switch(self):
        """Test Tab key for switching search type"""
        self.search_dialog.search_type = 'filename'
        
        result = self.search_dialog.handle_input(ord('\t'))
        
        self.assertEqual(result, ('search', None))
        self.assertEqual(self.search_dialog.search_type, 'content')


class TestJumpDialog(unittest.TestCase):
    """Test JumpDialog functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.config.MAX_JUMP_DIRECTORIES = 5000
        self.jump_dialog = JumpDialog(self.config)
        
    def test_init(self):
        """Test JumpDialog initialization"""
        self.assertIsInstance(self.jump_dialog, BaseListDialog)
        self.assertEqual(self.jump_dialog.directories, [])
        self.assertEqual(self.jump_dialog.filtered_directories, [])
        self.assertFalse(self.jump_dialog.searching)
        
    def test_filter_directories_internal(self):
        """Test directory filtering"""
        from pathlib import Path
        
        self.jump_dialog.directories = [
            Path("/home/user/documents"),
            Path("/home/user/downloads"),
            Path("/home/user/desktop")
        ]
        self.jump_dialog.text_editor.text = "doc"
        
        self.jump_dialog._filter_directories_internal()
        
        expected = [Path("/home/user/documents")]
        self.assertEqual(self.jump_dialog.filtered_directories, expected)


if __name__ == '__main__':
    unittest.main()