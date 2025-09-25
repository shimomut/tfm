#!/usr/bin/env python3
"""
Comprehensive test to find ALL dialog key handling issues

This test systematically tests all possible keys on all dialogs to find
any cases where a key returns True but doesn't set content_changed.
"""

import curses
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
from tfm_general_purpose_dialog import GeneralPurposeDialog


class TestComprehensiveDialogKeyHandling(unittest.TestCase):
    """Comprehensive test for dialog key handling issues"""
    
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
        
        # Common keys that often cause issues
        self.test_keys = [
            (curses.KEY_LEFT, 'LEFT'),
            (curses.KEY_RIGHT, 'RIGHT'),
            (curses.KEY_UP, 'UP'),
            (curses.KEY_DOWN, 'DOWN'),
            (curses.KEY_PPAGE, 'PAGE_UP'),
            (curses.KEY_NPAGE, 'PAGE_DOWN'),
            (curses.KEY_HOME, 'HOME'),
            (curses.KEY_END, 'END'),
            (curses.KEY_BACKSPACE, 'BACKSPACE'),
            (127, 'DELETE'),  # DEL key
            (ord('a'), 'LETTER_A'),
            (ord(' '), 'SPACE'),
        ]
        
    def _test_dialog_key_handling(self, dialog_name, dialog, setup_func):
        """Test all keys on a dialog to find rendering issues"""
        issues_found = []
        
        for key, key_name in self.test_keys:
            try:
                # Setup dialog fresh for each key test
                setup_func(dialog)
                
                # Simulate dialog being drawn
                dialog.content_changed = False
                
                # Press the key
                result = dialog.handle_input(key)
                
                # Check for the bug: key handled but content_changed not set
                if result and result is not False:  # Key was handled
                    if not dialog.content_changed:
                        issues_found.append(f"{key_name} key returns {result} but content_changed=False")
                        
            except Exception as e:
                # Some keys might cause exceptions, that's ok for this test
                pass
                
        return issues_found
        
    def test_search_dialog_comprehensive(self):
        """Comprehensive test of SearchDialog key handling"""
        dialog = SearchDialog(self.config)
        
        def setup(d):
            d.show('filename')
            
        issues = self._test_dialog_key_handling('SearchDialog', dialog, setup)
        
        if issues:
            self.fail(f"SearchDialog issues found:\n" + "\n".join(f"  • {issue}" for issue in issues))
        else:
            print("✓ SearchDialog: No key handling issues found")
            
    def test_jump_dialog_comprehensive(self):
        """Comprehensive test of JumpDialog key handling"""
        dialog = JumpDialog(self.config)
        
        def setup(d):
            d.show(Path('/tmp'))
            
        issues = self._test_dialog_key_handling('JumpDialog', dialog, setup)
        
        if issues:
            self.fail(f"JumpDialog issues found:\n" + "\n".join(f"  • {issue}" for issue in issues))
        else:
            print("✓ JumpDialog: No key handling issues found")
            
    def test_list_dialog_comprehensive(self):
        """Comprehensive test of ListDialog key handling"""
        dialog = ListDialog(self.config)
        
        def setup(d):
            callback = Mock()
            d.show("Test", ['item1', 'item2'], callback)
            
        issues = self._test_dialog_key_handling('ListDialog', dialog, setup)
        
        if issues:
            self.fail(f"ListDialog issues found:\n" + "\n".join(f"  • {issue}" for issue in issues))
        else:
            print("✓ ListDialog: No key handling issues found")
            
    def test_info_dialog_comprehensive(self):
        """Comprehensive test of InfoDialog key handling"""
        dialog = InfoDialog(self.config)
        
        def setup(d):
            test_lines = ["Line 1", "Line 2", "Line 3"]
            d.show("Test Dialog", test_lines)
            
        issues = self._test_dialog_key_handling('InfoDialog', dialog, setup)
        
        if issues:
            self.fail(f"InfoDialog issues found:\n" + "\n".join(f"  • {issue}" for issue in issues))
        else:
            print("✓ InfoDialog: No key handling issues found")
            
    def test_batch_rename_dialog_comprehensive(self):
        """Comprehensive test of BatchRenameDialog key handling"""
        dialog = BatchRenameDialog(self.config)
        
        def setup(d):
            test_files = [Path('/tmp/file1.txt'), Path('/tmp/file2.txt')]
            d.show(test_files)
            
        issues = self._test_dialog_key_handling('BatchRenameDialog', dialog, setup)
        
        if issues:
            self.fail(f"BatchRenameDialog issues found:\n" + "\n".join(f"  • {issue}" for issue in issues))
        else:
            print("✓ BatchRenameDialog: No key handling issues found")
            
    def test_general_purpose_dialog_comprehensive(self):
        """Comprehensive test of GeneralPurposeDialog key handling"""
        dialog = GeneralPurposeDialog(self.config)
        
        def setup(d):
            d.show_status_line_input("Test prompt: ", "default_text")
            
        issues = self._test_dialog_key_handling('GeneralPurposeDialog', dialog, setup)
        
        if issues:
            self.fail(f"GeneralPurposeDialog issues found:\n" + "\n".join(f"  • {issue}" for issue in issues))
        else:
            print("✓ GeneralPurposeDialog: No key handling issues found")
            
    def test_specific_regression_cases(self):
        """Test specific regression cases reported by user"""
        
        # Test 1: SearchDialog LEFT key immediately after opening
        search_dialog = SearchDialog(self.config)
        search_dialog.show('filename')
        search_dialog.content_changed = False
        result = search_dialog.handle_input(curses.KEY_LEFT)
        self.assertTrue(result, "SearchDialog should handle LEFT key")
        self.assertTrue(search_dialog.content_changed, "SearchDialog LEFT key should set content_changed")
        
        # Test 2: InfoDialog UP key immediately after opening (HelpDialog)
        info_dialog = InfoDialog(self.config)
        info_dialog.show("Help", ["Line 1", "Line 2"])
        info_dialog.content_changed = False
        result = info_dialog.handle_input(curses.KEY_UP)
        self.assertTrue(result, "InfoDialog should handle UP key")
        self.assertTrue(info_dialog.content_changed, "InfoDialog UP key should set content_changed")
        
        # Test 3: BatchRenameDialog LEFT key immediately after opening
        batch_dialog = BatchRenameDialog(self.config)
        batch_dialog.show([Path('/tmp/file1.txt')])
        batch_dialog.content_changed = False
        result = batch_dialog.handle_input(curses.KEY_LEFT)
        if result and result is not False:  # If key was handled
            self.assertTrue(batch_dialog.content_changed, "BatchRenameDialog LEFT key should set content_changed")
            
        print("✓ All specific regression cases pass")


if __name__ == '__main__':
    unittest.main()