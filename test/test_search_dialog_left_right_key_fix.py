#!/usr/bin/env python3
"""
Test for SearchDialog left/right key rendering fix

This test verifies the fix for the bug where pressing left or right keys
immediately after opening a SearchDialog would cause the dialog to stop
rendering (appear to disappear) due to the content_changed flag not being
set properly.

Bug Description:
- SearchDialog's handle_input() method only set content_changed=True for
  specific navigation keys (UP, DOWN, PAGE_UP, etc.)
- LEFT and RIGHT keys were handled by the base class and returned True,
  but content_changed remained False
- This caused needs_redraw() to return False, stopping dialog rendering
- The dialog appeared to "disappear" but was actually just not being drawn

Fix:
- Set content_changed=True for ALL handled keys in the elif result: branch
- This ensures the dialog continues to be rendered after any key press
"""

from ttk.input_event import InputEvent, KeyCode, ModifierKey
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_search_dialog import SearchDialog


class TestSearchDialogLeftRightKeyFix(unittest.TestCase):
    """Test SearchDialog left/right key rendering fix"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock config
        self.config = Mock()
        self.config.MAX_SEARCH_RESULTS = 1000
        self.config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        self.config.LIST_DIALOG_MIN_HEIGHT = 15
        
        # Create SearchDialog instance
        self.search_dialog = SearchDialog(self.config)
        
    def test_left_key_sets_content_changed(self):
        """Test that left key sets content_changed flag"""
        # Show dialog and simulate it being drawn
        self.search_dialog.show('filename')
        self.search_dialog.content_changed = False  # Simulate after drawing
        
        # Press left key
        result = self.search_dialog.handle_input(InputEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE))
        
        # Verify the fix
        self.assertTrue(result, "Left key should be handled")
        self.assertTrue(self.search_dialog.content_changed, 
                       "content_changed should be True after left key")
        self.assertTrue(self.search_dialog.needs_redraw(), 
                       "Dialog should need redraw after left key")
        
    def test_right_key_sets_content_changed(self):
        """Test that right key sets content_changed flag"""
        # Show dialog and simulate it being drawn
        self.search_dialog.show('filename')
        self.search_dialog.content_changed = False  # Simulate after drawing
        
        # Press right key
        result = self.search_dialog.handle_input(InputEvent(key_code=KeyCode.RIGHT, modifiers=ModifierKey.NONE))
        
        # Verify the fix
        self.assertTrue(result, "Right key should be handled")
        self.assertTrue(self.search_dialog.content_changed, 
                       "content_changed should be True after right key")
        self.assertTrue(self.search_dialog.needs_redraw(), 
                       "Dialog should need redraw after right key")
        
    def test_all_navigation_keys_set_content_changed(self):
        """Test that all navigation keys properly set content_changed"""
        navigation_keys = [
            KeyCode.LEFT,
            KeyCode.RIGHT, 
            KeyCode.UP,
            KeyCode.DOWN,
            KeyCode.PAGE_UP,
            KeyCode.PAGE_DOWN,
            KeyCode.HOME,
            KeyCode.END
        ]
        
        for key in navigation_keys:
            with self.subTest(key=key):
                # Reset dialog state
                self.search_dialog.show('filename')
                self.search_dialog.content_changed = False
                
                # Press the key
                result = self.search_dialog.handle_input(key)
                
                # All navigation keys should set content_changed
                self.assertTrue(result, f"Key {key} should be handled")
                self.assertTrue(self.search_dialog.content_changed, 
                               f"content_changed should be True after key {key}")
                self.assertTrue(self.search_dialog.needs_redraw(), 
                               f"Dialog should need redraw after key {key}")
                
    def test_printable_keys_trigger_search(self):
        """Test that printable keys trigger search action"""
        # Show dialog and simulate it being drawn
        self.search_dialog.show('filename')
        self.search_dialog.content_changed = False
        
        # Press a printable key
        result = self.search_dialog.handle_input(ord('a'))
        
        # Should trigger search action
        self.assertEqual(result, ('search', None), "Printable key should trigger search")
        
    def test_escape_key_closes_dialog(self):
        """Test that escape key properly closes dialog"""
        # Show dialog
        self.search_dialog.show('filename')
        
        # Press escape
        result = self.search_dialog.handle_input(27)  # ESC
        
        # Should close dialog
        self.assertTrue(result, "Escape should be handled")
        self.assertFalse(self.search_dialog.mode, "Dialog should be closed after escape")
        
    def test_regression_scenario(self):
        """Test the exact regression scenario: left key immediately after opening"""
        # This simulates the exact user scenario that was broken:
        # 1. Open SearchDialog
        # 2. Press left key immediately
        # 3. Dialog should still be visible (needs_redraw = True)
        
        # Step 1: Open dialog
        self.search_dialog.show('filename')
        self.assertTrue(self.search_dialog.mode, "Dialog should be open")
        self.assertTrue(self.search_dialog.needs_redraw(), "Dialog should need initial draw")
        
        # Step 2: Simulate dialog being drawn (main loop would do this)
        self.search_dialog.content_changed = False
        self.assertFalse(self.search_dialog.needs_redraw(), "Dialog should not need redraw after being drawn")
        
        # Step 3: Press left key immediately (the problematic scenario)
        result = self.search_dialog.handle_input(InputEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE))
        
        # Step 4: Verify dialog is still visible
        self.assertTrue(result, "Left key should be handled")
        self.assertTrue(self.search_dialog.mode, "Dialog should still be open")
        self.assertTrue(self.search_dialog.needs_redraw(), 
                       "Dialog should need redraw after left key (this was the bug)")
        
        print("✓ Regression test passed: Dialog remains visible after left key press")


if __name__ == '__main__':
    unittest.main()