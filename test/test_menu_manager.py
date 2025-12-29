"""
Unit tests for MenuManager class

Run with: PYTHONPATH=.:src:ttk pytest test/test_menu_manager.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock
import platform
from src.tfm_menu_manager import MenuManager


class TestMenuManager(unittest.TestCase):
    """Test cases for MenuManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock file manager
        self.mock_file_manager = Mock()
        
        # Create mock pane as dictionary (matching actual TFM structure)
        from pathlib import Path
        self.mock_pane = {
            'selected_files': set(),
            'path': Path('/test/path')
        }
        
        # Configure file manager to return mock pane
        self.mock_file_manager.get_current_pane.return_value = self.mock_pane
        self.mock_file_manager.clipboard = []
        
        # Create MenuManager instance
        self.menu_manager = MenuManager(self.mock_file_manager)
    
    def test_initialization(self):
        """Test MenuManager initialization"""
        self.assertIsNotNone(self.menu_manager.file_manager)
        self.assertIsNotNone(self.menu_manager.menu_structure)
        self.assertIn('menus', self.menu_manager.menu_structure)
    
    def test_menu_structure_has_four_menus(self):
        """Test that menu structure contains App, File, Edit, View, Go, and Help menus"""
        menus = self.menu_manager.menu_structure['menus']
        self.assertEqual(len(menus), 6)
        
        menu_ids = [menu['id'] for menu in menus]
        self.assertIn('app', menu_ids)
        self.assertIn('file', menu_ids)
        self.assertIn('edit', menu_ids)
        self.assertIn('view', menu_ids)
        self.assertIn('go', menu_ids)
        self.assertIn('help', menu_ids)
    
    def test_file_menu_structure(self):
        """Test File menu contains required items"""
        menus = self.menu_manager.menu_structure['menus']
        file_menu = next(m for m in menus if m['id'] == 'file')
        
        # Get non-separator items
        items = [item for item in file_menu['items'] if 'separator' not in item]
        item_ids = [item['id'] for item in items]
        
        # Check required items exist
        self.assertIn(MenuManager.FILE_NEW_FILE, item_ids)
        self.assertIn(MenuManager.FILE_NEW_FOLDER, item_ids)
        self.assertIn(MenuManager.FILE_OPEN, item_ids)
        self.assertIn(MenuManager.FILE_DELETE, item_ids)
        self.assertIn(MenuManager.FILE_RENAME, item_ids)
    
    def test_edit_menu_structure(self):
        """Test Edit menu contains required items"""
        menus = self.menu_manager.menu_structure['menus']
        edit_menu = next(m for m in menus if m['id'] == 'edit')
        
        items = [item for item in edit_menu['items'] if 'separator' not in item]
        item_ids = [item['id'] for item in items]
        
        self.assertIn(MenuManager.EDIT_COPY, item_ids)
        self.assertIn(MenuManager.EDIT_CUT, item_ids)
        self.assertIn(MenuManager.EDIT_PASTE, item_ids)
        self.assertIn(MenuManager.EDIT_SELECT_ALL, item_ids)
    
    def test_view_menu_structure(self):
        """Test View menu contains required items"""
        menus = self.menu_manager.menu_structure['menus']
        view_menu = next(m for m in menus if m['id'] == 'view')
        
        items = [item for item in view_menu['items'] if 'separator' not in item]
        item_ids = [item['id'] for item in items]
        
        self.assertIn(MenuManager.VIEW_SHOW_HIDDEN, item_ids)
        self.assertIn(MenuManager.VIEW_SORT_BY_NAME, item_ids)
        self.assertIn(MenuManager.VIEW_SORT_BY_SIZE, item_ids)
        self.assertIn(MenuManager.VIEW_SORT_BY_DATE, item_ids)
        self.assertIn(MenuManager.VIEW_SORT_BY_EXTENSION, item_ids)
        self.assertIn(MenuManager.VIEW_REFRESH, item_ids)
    
    def test_go_menu_structure(self):
        """Test Go menu contains required items"""
        menus = self.menu_manager.menu_structure['menus']
        go_menu = next(m for m in menus if m['id'] == 'go')
        
        items = [item for item in go_menu['items'] if 'separator' not in item]
        item_ids = [item['id'] for item in items]
        
        self.assertIn(MenuManager.GO_PARENT, item_ids)
        self.assertIn(MenuManager.GO_HOME, item_ids)
        self.assertIn(MenuManager.GO_FAVORITES, item_ids)
        self.assertIn(MenuManager.GO_RECENT, item_ids)
    
    def test_menu_item_ids_are_unique(self):
        """Test that all menu item IDs are unique across entire menu structure"""
        menus = self.menu_manager.menu_structure['menus']
        all_item_ids = []
        
        for menu in menus:
            for item in menu['items']:
                if 'id' in item:
                    all_item_ids.append(item['id'])
        
        # Check for duplicates
        self.assertEqual(len(all_item_ids), len(set(all_item_ids)),
                        "Menu item IDs must be unique")
    
    def test_keyboard_shortcuts_use_correct_modifier(self):
        """Test that keyboard shortcuts use platform-appropriate modifier"""
        expected_modifier = 'Cmd' if platform.system() == 'Darwin' else 'Ctrl'
        
        menus = self.menu_manager.menu_structure['menus']
        for menu in menus:
            for item in menu['items']:
                if 'shortcut' in item and item['shortcut']:
                    self.assertTrue(
                        item['shortcut'].startswith(expected_modifier),
                        f"Shortcut '{item['shortcut']}' should start with '{expected_modifier}'"
                    )
    
    def test_update_menu_states_no_selection(self):
        """Test menu states when no files are selected"""
        self.mock_pane['selected_files'] = set()
        
        states = self.menu_manager.update_menu_states()
        
        # Selection-dependent items should be disabled
        self.assertFalse(states[MenuManager.FILE_DELETE])
        self.assertFalse(states[MenuManager.FILE_RENAME])
        self.assertFalse(states[MenuManager.EDIT_COPY])
        self.assertFalse(states[MenuManager.EDIT_CUT])
        
        # Always-enabled items should be enabled
        self.assertTrue(states[MenuManager.FILE_NEW_FILE])
        self.assertTrue(states[MenuManager.FILE_NEW_FOLDER])
        self.assertTrue(states[MenuManager.APP_QUIT])
        self.assertTrue(states[MenuManager.EDIT_SELECT_ALL])
    
    def test_update_menu_states_with_selection(self):
        """Test menu states when files are selected"""
        self.mock_pane['selected_files'] = {'file1.txt', 'file2.txt'}
        
        states = self.menu_manager.update_menu_states()
        
        # Selection-dependent items should be enabled
        self.assertTrue(states[MenuManager.FILE_DELETE])
        self.assertTrue(states[MenuManager.FILE_RENAME])
        self.assertTrue(states[MenuManager.EDIT_COPY])
        self.assertTrue(states[MenuManager.EDIT_CUT])
    
    def test_update_menu_states_with_clipboard(self):
        """Test paste menu state when clipboard has content"""
        self.mock_file_manager.clipboard = ['file1.txt']
        
        states = self.menu_manager.update_menu_states()
        
        # Paste should be enabled when clipboard has content
        self.assertTrue(states[MenuManager.EDIT_PASTE])
    
    def test_update_menu_states_empty_clipboard(self):
        """Test paste menu state when clipboard is empty"""
        self.mock_file_manager.clipboard = []
        
        states = self.menu_manager.update_menu_states()
        
        # Paste should be disabled when clipboard is empty
        self.assertFalse(states[MenuManager.EDIT_PASTE])
    
    def test_update_menu_states_at_root(self):
        """Test parent directory menu state when at root"""
        # Make path equal to its parent (indicates root)
        from pathlib import Path
        root_path = Path('/')
        self.mock_pane['path'] = root_path
        
        states = self.menu_manager.update_menu_states()
        
        # Parent directory should be disabled at root
        self.assertFalse(states[MenuManager.GO_PARENT])
    
    def test_update_menu_states_not_at_root(self):
        """Test parent directory menu state when not at root"""
        # Make path different from its parent (not at root)
        from pathlib import Path
        self.mock_pane['path'] = Path('/test/path/subdir')
        
        states = self.menu_manager.update_menu_states()
        
        # Parent directory should be enabled when not at root
        self.assertTrue(states[MenuManager.GO_PARENT])
    
    def test_view_menu_items_always_enabled(self):
        """Test that all View menu items are always enabled"""
        states = self.menu_manager.update_menu_states()
        
        self.assertTrue(states[MenuManager.VIEW_SHOW_HIDDEN])
        self.assertTrue(states[MenuManager.VIEW_SORT_BY_NAME])
        self.assertTrue(states[MenuManager.VIEW_SORT_BY_SIZE])
        self.assertTrue(states[MenuManager.VIEW_SORT_BY_DATE])
        self.assertTrue(states[MenuManager.VIEW_SORT_BY_EXTENSION])
        self.assertTrue(states[MenuManager.VIEW_REFRESH])
    
    def test_go_menu_items_enabled_except_parent_at_root(self):
        """Test that Go menu items are enabled (except parent at root)"""
        states = self.menu_manager.update_menu_states()
        
        self.assertTrue(states[MenuManager.GO_HOME])
        self.assertTrue(states[MenuManager.GO_FAVORITES])
        self.assertTrue(states[MenuManager.GO_RECENT])
    
    def test_should_enable_item(self):
        """Test should_enable_item method"""
        self.mock_pane['selected_files'] = {'file1.txt'}
        
        # Should return True for items that should be enabled
        self.assertTrue(self.menu_manager.should_enable_item(MenuManager.FILE_DELETE))
        self.assertTrue(self.menu_manager.should_enable_item(MenuManager.EDIT_COPY))
        
        # Should return False for items that should be disabled
        self.assertFalse(self.menu_manager.should_enable_item(MenuManager.EDIT_PASTE))
    
    def test_get_menu_structure(self):
        """Test get_menu_structure returns the menu structure"""
        structure = self.menu_manager.get_menu_structure()
        
        self.assertIsNotNone(structure)
        self.assertIn('menus', structure)
        self.assertEqual(len(structure['menus']), 6)
    
    def test_menu_items_have_required_fields(self):
        """Test that all menu items have required fields"""
        menus = self.menu_manager.menu_structure['menus']
        
        for menu in menus:
            self.assertIn('id', menu)
            self.assertIn('label', menu)
            self.assertIn('items', menu)
            
            for item in menu['items']:
                if 'separator' in item:
                    # Separators only need the separator flag
                    self.assertTrue(item['separator'])
                else:
                    # Regular items need id, label, and enabled
                    self.assertIn('id', item)
                    self.assertIn('label', item)
                    self.assertIn('enabled', item)
    
    def test_error_handling_when_pane_unavailable(self):
        """Test that menu states handle errors gracefully when pane is unavailable"""
        # Make get_current_pane raise an exception
        self.mock_file_manager.get_current_pane.side_effect = Exception("Pane not available")
        
        # Should not raise exception
        states = self.menu_manager.update_menu_states()
        
        # Selection-dependent items should be disabled
        self.assertFalse(states[MenuManager.FILE_DELETE])
        self.assertFalse(states[MenuManager.EDIT_COPY])
        
        # Always-enabled items should still be enabled
        self.assertTrue(states[MenuManager.FILE_NEW_FILE])
        self.assertTrue(states[MenuManager.APP_QUIT])
    
    def test_clipboard_with_copy_buffer_attribute(self):
        """Test clipboard detection with copy_buffer attribute"""
        # Remove clipboard attribute and add copy_buffer
        delattr(self.mock_file_manager, 'clipboard')
        self.mock_file_manager.copy_buffer = ['file1.txt']
        
        states = self.menu_manager.update_menu_states()
        
        # Paste should be enabled when copy_buffer has content
        self.assertTrue(states[MenuManager.EDIT_PASTE])
