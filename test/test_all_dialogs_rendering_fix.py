#!/usr/bin/env python3
"""
Comprehensive test for dialog rendering fixes across all dialog types

This test verifies that all dialogs properly handle keys without causing
rendering issues (dialogs disappearing due to content_changed not being set).
"""

from ttk.input_event import InputEvent, KeyCode, ModifierKey
import unittest
from unittest.mock import Mock, patch
import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_search_dialog import SearchDialog
from tfm_jump_dialog import JumpDialog
from tfm_list_dialog import ListDialog
from tfm_info_dialog import InfoDialog
from tfm_batch_rename_dialog import BatchRenameDialog


class TestAllDialogsRenderingFix(unittest.TestCase):
    """Test rendering fixes across all dialog types"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock config
        self.config = Mock()
        self.config.MAX_SEARCH_RESULTS = 1000
        self.config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        self.config.LIST_DIALOG_MIN_HEIGHT = 15
        self.config.MAX_DIRECTORY_SCAN_RESULTS = 1000
        self.config.INFO_DIALOG_WIDTH_RATIO = 0.8
        self.config.INFO_DIALOG_HEIGHT_RATIO = 0.8
        self.config.INFO_DIALOG_MIN_WIDTH = 20
        self.config.INFO_DIALOG_MIN_HEIGHT = 10
        
    def _test_key_handling(self, dialog, dialog_name, key, key_name, setup_func=None):
        """Helper method to test key handling for any dialog"""
        if setup_func:
            setup_func(dialog)
        
        # Simulate dialog being drawn
        dialog.content_changed = False
        initial_needs_redraw = dialog.needs_redraw()
        
        # Press the key
        result = dialog.handle_input(key)
        
        # Check results
        if result:  # If key was handled
            self.assertTrue(dialog.content_changed, 
                          f"{dialog_name} should set content_changed after {key_name} key")
            self.assertTrue(dialog.needs_redraw(), 
                          f"{dialog_name} should need redraw after {key_name} key")
        
        return result
        
    def test_search_dialog_keys(self):
        """Test SearchDialog key handling"""
        dialog = SearchDialog(self.config)
        
        def setup(d):
            d.show('filename')
            
        # Test various keys
        keys_to_test = [
            (KeyCode.LEFT, 'LEFT'),
            (KeyCode.RIGHT, 'RIGHT'),
            (KeyCode.UP, 'UP'),
            (KeyCode.DOWN, 'DOWN'),
        ]
        
        for key, key_name in keys_to_test:
            with self.subTest(key=key_name):
                result = self._test_key_handling(dialog, 'SearchDialog', key, key_name, setup)
                self.assertTrue(result, f"SearchDialog should handle {key_name} key")
                
    def test_jump_dialog_keys(self):
        """Test JumpDialog key handling"""
        dialog = JumpDialog(self.config)
        
        def setup(d):
            d.show(Path('/tmp'))
            
        # Test various keys
        keys_to_test = [
            (KeyCode.LEFT, 'LEFT'),
            (KeyCode.RIGHT, 'RIGHT'),
            (KeyCode.UP, 'UP'),
            (KeyCode.DOWN, 'DOWN'),
        ]
        
        for key, key_name in keys_to_test:
            with self.subTest(key=key_name):
                result = self._test_key_handling(dialog, 'JumpDialog', key, key_name, setup)
                self.assertTrue(result, f"JumpDialog should handle {key_name} key")
                
    def test_list_dialog_keys(self):
        """Test ListDialog key handling"""
        dialog = ListDialog(self.config)
        
        def setup(d):
            callback = Mock()
            d.show("Test", ['item1', 'item2'], callback)
            
        # Test various keys
        keys_to_test = [
            (KeyCode.LEFT, 'LEFT'),
            (KeyCode.RIGHT, 'RIGHT'),
            (KeyCode.UP, 'UP'),
            (KeyCode.DOWN, 'DOWN'),
        ]
        
        for key, key_name in keys_to_test:
            with self.subTest(key=key_name):
                result = self._test_key_handling(dialog, 'ListDialog', key, key_name, setup)
                self.assertTrue(result, f"ListDialog should handle {key_name} key")
                
    def test_info_dialog_keys(self):
        """Test InfoDialog key handling (the HelpDialog)"""
        dialog = InfoDialog(self.config)
        
        def setup(d):
            test_lines = ["Line 1", "Line 2", "Line 3"]
            d.show("Test Dialog", test_lines)
            
        # Test various keys, especially UP which was the reported issue
        keys_to_test = [
            (KeyCode.UP, 'UP'),
            (KeyCode.DOWN, 'DOWN'),
            (KeyCode.PAGE_UP, 'PAGE_UP'),
            (KeyCode.PAGE_DOWN, 'PAGE_DOWN'),
            (KeyCode.HOME, 'HOME'),
            (KeyCode.END, 'END'),
        ]
        
        for key, key_name in keys_to_test:
            with self.subTest(key=key_name):
                result = self._test_key_handling(dialog, 'InfoDialog', key, key_name, setup)
                self.assertTrue(result, f"InfoDialog should handle {key_name} key")
                
    def test_batch_rename_dialog_keys(self):
        """Test BatchRenameDialog key handling"""
        dialog = BatchRenameDialog(self.config)
        
        def setup(d):
            test_files = [Path('/tmp/file1.txt'), Path('/tmp/file2.txt')]
            d.show(test_files)
            
        # Test various keys
        keys_to_test = [
            (KeyCode.UP, 'UP'),
            (KeyCode.DOWN, 'DOWN'),
            (KeyCode.PAGE_UP, 'PAGE_UP'),
            (KeyCode.PAGE_DOWN, 'PAGE_DOWN'),
        ]
        
        for key, key_name in keys_to_test:
            with self.subTest(key=key_name):
                result = self._test_key_handling(dialog, 'BatchRenameDialog', key, key_name, setup)
                # Note: BatchRenameDialog might return tuples for some keys
                if isinstance(result, tuple):
                    result = True
                self.assertTrue(result, f"BatchRenameDialog should handle {key_name} key")
                
    def test_info_dialog_regression_scenario(self):
        """Test the exact regression scenario: UP key immediately after opening HelpDialog"""
        dialog = InfoDialog(self.config)
        
        # Step 1: Open dialog (simulating HelpDialog)
        test_lines = ["Help Line 1", "Help Line 2", "Help Line 3"]
        dialog.show("Help", test_lines)
        self.assertTrue(dialog.mode, "Dialog should be open")
        self.assertEqual(dialog.scroll, 0, "Should start at top")
        self.assertTrue(dialog.needs_redraw(), "Dialog should need initial draw")
        
        # Step 2: Simulate dialog being drawn (main loop would do this)
        dialog.content_changed = False
        self.assertFalse(dialog.needs_redraw(), "Dialog should not need redraw after being drawn")
        
        # Step 3: Press UP key immediately (the problematic scenario)
        result = dialog.handle_input(InputEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE))
        
        # Step 4: Verify dialog is still visible
        self.assertTrue(result, "UP key should be handled")
        self.assertTrue(dialog.mode, "Dialog should still be open")
        self.assertEqual(dialog.scroll, 0, "Should still be at top (can't scroll up)")
        self.assertTrue(dialog.needs_redraw(), 
                       "Dialog should need redraw after UP key (this was the bug)")
        
        print("✓ InfoDialog regression test passed: Dialog remains visible after UP key press")
        
    def test_all_dialogs_consistent_behavior(self):
        """Test that all dialogs have consistent key handling behavior"""
        test_cases = [
            ('SearchDialog', SearchDialog(self.config), lambda d: d.show('filename')),
            ('JumpDialog', JumpDialog(self.config), lambda d: d.show(Path('/tmp'))),
            ('ListDialog', ListDialog(self.config), lambda d: d.show("Test", ['item1'], Mock())),
            ('InfoDialog', InfoDialog(self.config), lambda d: d.show("Test", ["Line 1"])),
            ('BatchRenameDialog', BatchRenameDialog(self.config), lambda d: d.show([Path('/tmp/file1.txt')])),
        ]
        
        for dialog_name, dialog, setup_func in test_cases:
            with self.subTest(dialog=dialog_name):
                # Setup dialog
                setup_func(dialog)
                
                # Test that all dialogs have the required methods
                self.assertTrue(hasattr(dialog, 'needs_redraw'), 
                              f"{dialog_name} should have needs_redraw method")
                self.assertTrue(hasattr(dialog, 'handle_input'), 
                              f"{dialog_name} should have handle_input method")
                self.assertTrue(hasattr(dialog, 'content_changed'), 
                              f"{dialog_name} should have content_changed attribute")
                
                # Test that needs_redraw works correctly
                dialog.content_changed = True
                self.assertTrue(dialog.needs_redraw(), 
                              f"{dialog_name} should need redraw when content_changed=True")
                
                dialog.content_changed = False
                # Note: Some dialogs (SearchDialog, JumpDialog) might still need redraw due to animation
                # so we don't test the False case universally
                
        print("✓ All dialogs have consistent interface and behavior")


if __name__ == '__main__':
    unittest.main()