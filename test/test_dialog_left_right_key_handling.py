"""
Comprehensive test for left/right key rendering fix across all BaseListDialog subclasses

This test verifies that all dialogs that extend BaseListDialog properly handle
left and right keys without causing rendering issues.

Run with: PYTHONPATH=.:src:ttk pytest test/test_dialog_left_right_key_handling.py -v
"""

from ttk import KeyEvent, KeyCode, ModifierKey
import unittest
from unittest.mock import Mock, patch

from tfm_search_dialog import SearchDialog

from tfm_list_dialog import ListDialog

class TestAllDialogsLeftRightKeyFix(unittest.TestCase):
    """Test left/right key handling across all BaseListDialog subclasses"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock config
        self.config = Mock()
        self.config.MAX_SEARCH_RESULTS = 1000
        self.config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        self.config.LIST_DIALOG_MIN_HEIGHT = 15
        self.config.MAX_DIRECTORY_SCAN_RESULTS = 1000
        
    def test_search_dialog_left_right_keys(self):
        """Test SearchDialog left/right key handling"""
        dialog = SearchDialog(self.config)
        
        # Test left key
        dialog.show('filename')
        dialog.content_changed = False
        result = dialog.handle_input(KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE))
        self.assertTrue(result, "SearchDialog should handle left key")
        self.assertTrue(dialog.content_changed, "SearchDialog should set content_changed after left key")
        self.assertTrue(dialog.needs_redraw(), "SearchDialog should need redraw after left key")
        
        # Test right key
        dialog.show('filename')
        dialog.content_changed = False
        result = dialog.handle_input(KeyEvent(key_code=KeyCode.RIGHT, modifiers=ModifierKey.NONE))
        self.assertTrue(result, "SearchDialog should handle right key")
        self.assertTrue(dialog.content_changed, "SearchDialog should set content_changed after right key")
        self.assertTrue(dialog.needs_redraw(), "SearchDialog should need redraw after right key")
        
    def test_jump_dialog_left_right_keys(self):
        """Test JumpDialog left/right key handling"""
        dialog = JumpDialog(self.config)
        
        # Create a mock root directory
        from pathlib import Path
        root_dir = Path('/tmp')
        
        # Test left key
        dialog.show(root_dir)
        dialog.content_changed = False
        result = dialog.handle_input(KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE))
        self.assertTrue(result, "JumpDialog should handle left key")
        self.assertTrue(dialog.content_changed, "JumpDialog should set content_changed after left key")
        self.assertTrue(dialog.needs_redraw(), "JumpDialog should need redraw after left key")
        
        # Test right key
        dialog.show(root_dir)
        dialog.content_changed = False
        result = dialog.handle_input(KeyEvent(key_code=KeyCode.RIGHT, modifiers=ModifierKey.NONE))
        self.assertTrue(result, "JumpDialog should handle right key")
        self.assertTrue(dialog.content_changed, "JumpDialog should set content_changed after right key")
        self.assertTrue(dialog.needs_redraw(), "JumpDialog should need redraw after right key")
        
    def test_list_dialog_left_right_keys(self):
        """Test ListDialog left/right key handling"""
        dialog = ListDialog(self.config)
        
        # Set up some test items and callback
        test_items = ['item1', 'item2', 'item3']
        callback = Mock()
        
        # Test left key
        dialog.show("Test Dialog", test_items, callback)
        dialog.content_changed = False
        result = dialog.handle_input(KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE))
        self.assertTrue(result, "ListDialog should handle left key")
        self.assertTrue(dialog.content_changed, "ListDialog should set content_changed after left key")
        self.assertTrue(dialog.needs_redraw(), "ListDialog should need redraw after left key")
        
        # Test right key
        dialog.show("Test Dialog", test_items, callback)
        dialog.content_changed = False
        result = dialog.handle_input(KeyEvent(key_code=KeyCode.RIGHT, modifiers=ModifierKey.NONE))
        self.assertTrue(result, "ListDialog should handle right key")
        self.assertTrue(dialog.content_changed, "ListDialog should set content_changed after right key")
        self.assertTrue(dialog.needs_redraw(), "ListDialog should need redraw after right key")
        
    def test_all_dialogs_consistent_behavior(self):
        """Test that all dialogs have consistent left/right key behavior"""
        dialogs = [
            ('SearchDialog', SearchDialog(self.config)),
            ('JumpDialog'(self.config)),
            ('ListDialog', ListDialog(self.config))
        ]
        
        for dialog_name, dialog in dialogs:
            with self.subTest(dialog=dialog_name):
                # Show dialog appropriately
                if dialog_name == 'SearchDialog':
                    dialog.show('filename')
                elif dialog_name == 'JumpDialog':
                    from pathlib import Path
                    dialog.show(Path('/tmp'))
                elif dialog_name == 'ListDialog':
                    callback = Mock()
                    dialog.show("Test", ['item1', 'item2'], callback)
                
                # Test both left and right keys
                for key_name, key_code in [('LEFT', KeyCode.LEFT), ('RIGHT', KeyCode.RIGHT)]:
                    with self.subTest(key=key_name):
                        # Reset state
                        dialog.content_changed = False
                        
                        # Press key
                        result = dialog.handle_input(key_code)
                        
                        # All dialogs should behave consistently
                        self.assertTrue(result, f"{dialog_name} should handle {key_name} key")
                        self.assertTrue(dialog.content_changed, 
                                     f"{dialog_name} should set content_changed after {key_name} key")
                        self.assertTrue(dialog.needs_redraw(), 
                                     f"{dialog_name} should need redraw after {key_name} key")
                        
        print("✓ All dialogs handle left/right keys consistently")
