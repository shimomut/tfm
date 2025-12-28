#!/usr/bin/env python3
"""
Test key bindings with KeyEvent support.

This test verifies that the key binding system correctly handles KeyEvent objects
from TTK, including both printable characters and special keys with modifiers.
"""

import sys
import unittest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ttk import KeyEvent, KeyCode, ModifierKey
from tfm_config import (
    ConfigManager,
    find_action_for_event
)


class TestKeyBindingsKeyEvent(unittest.TestCase):
    """Test key bindings with KeyEvent objects."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
    
    def test_printable_char_input_event(self):
        """Test that printable character KeyEvents are recognized."""
        # Create KeyEvent for 'Q' (quit)
        event = KeyEvent(key_code=KeyCode.Q, modifiers=ModifierKey.NONE, char='q')
        
        # Check if it's bound to quit action
        action = find_action_for_event(event, has_selection=False)
        self.assertEqual(
            action, 'quit',
            "KeyEvent for 'Q' should be bound to quit action"
        )
    
    def test_special_key_input_event(self):
        """Test that special key KeyEvents are recognized."""
        # Create KeyEvent for HOME key (select_all)
        event = KeyEvent(key_code=KeyCode.HOME, modifiers=ModifierKey.NONE)
        
        # Check if it's bound to select_all action
        action = find_action_for_event(event, has_selection=False)
        self.assertEqual(
            action, 'select_all',
            "KeyEvent for HOME key should be bound to select_all action"
        )
    
    def test_input_event_with_selection_requirement(self):
        """Test KeyEvent with selection requirements."""
        # Create KeyEvent for 'C' (copy_files - requires selection)
        event = KeyEvent(key_code=KeyCode.C, modifiers=ModifierKey.NONE, char='c')
        
        # Should be bound when files are selected
        action_with_selection = find_action_for_event(event, has_selection=True)
        self.assertEqual(
            action_with_selection, 'copy_files',
            "KeyEvent for 'C' should be bound to copy_files when files are selected"
        )
        
        # Should NOT be bound when no files are selected
        action_without_selection = find_action_for_event(event, has_selection=False)
        self.assertIsNone(
            action_without_selection,
            "KeyEvent for 'C' should NOT be bound to copy_files when no files are selected"
        )
    
    def test_input_event_no_selection_requirement(self):
        """Test KeyEvent with 'none' selection requirement."""
        # Create KeyEvent for 'M' (create_directory - requires no selection)
        event = KeyEvent(key_code=KeyCode.M, modifiers=ModifierKey.NONE, char='m')
        
        # Should be bound when no files are selected
        action_without_selection = find_action_for_event(event, has_selection=False)
        self.assertEqual(
            action_without_selection, 'create_directory',
            "KeyEvent for 'M' should be bound to create_directory when no files are selected"
        )
        
        # Should NOT be bound when files are selected (move_files takes precedence)
        action_with_selection = find_action_for_event(event, has_selection=True)
        self.assertEqual(
            action_with_selection, 'move_files',
            "KeyEvent for 'M' should be bound to move_files when files are selected"
        )
    
    def test_input_event_any_selection_requirement(self):
        """Test KeyEvent with 'any' selection requirement."""
        # Create KeyEvent for 'Q' (quit - works regardless of selection)
        event = KeyEvent(key_code=KeyCode.Q, modifiers=ModifierKey.NONE, char='q')
        
        # Should be bound with selection
        action_with_selection = find_action_for_event(event, has_selection=True)
        self.assertEqual(
            action_with_selection, 'quit',
            "KeyEvent for 'Q' should be bound to quit with selection"
        )
        
        # Should be bound without selection
        action_without_selection = find_action_for_event(event, has_selection=False)
        self.assertEqual(
            action_without_selection, 'quit',
            "KeyEvent for 'Q' should be bound to quit without selection"
        )
    
    def test_null_input_event(self):
        """Test that None KeyEvent is handled gracefully."""
        # None event should return None
        action = find_action_for_event(None, has_selection=False)
        self.assertIsNone(
            action,
            "None KeyEvent should return None"
        )
        
        action_with_selection = find_action_for_event(None, has_selection=True)
        self.assertIsNone(
            action_with_selection,
            "None KeyEvent should return None with selection check"
        )
    
    def test_unbound_input_event(self):
        """Test that unbound KeyEvents return None."""
        # Create KeyEvent for a key that's not bound to anything
        event = KeyEvent(key_code=ord('~'), modifiers=ModifierKey.NONE, char='~')
        
        # Should not be bound to any action
        action = find_action_for_event(event, has_selection=False)
        self.assertIsNone(
            action,
            "Unbound KeyEvent should return None"
        )
    
    def test_module_level_functions(self):
        """Test module-level convenience function."""
        # Test find_action_for_event
        event = KeyEvent(key_code=KeyCode.Q, modifiers=ModifierKey.NONE, char='q')
        action = find_action_for_event(event, has_selection=False)
        self.assertEqual(
            action, 'quit',
            "Module-level find_action_for_event should work"
        )
        
        # Test with selection requirement
        event_copy = KeyEvent(key_code=KeyCode.C, modifiers=ModifierKey.NONE, char='c')
        action_with_selection = find_action_for_event(event_copy, has_selection=True)
        self.assertEqual(
            action_with_selection, 'copy_files',
            "Module-level function should work with selection"
        )
        
        action_without_selection = find_action_for_event(event_copy, has_selection=False)
        self.assertIsNone(
            action_without_selection,
            "Module-level function should respect selection requirements"
        )
    
    def test_case_sensitivity(self):
        """Test that alphabet keys are case-insensitive (both 'm' and 'M' map to KeyCode.M)."""
        # For alphabet keys, both lowercase and uppercase map to the same KeyCode
        # The difference between actions is in selection requirements, not case
        event_lower = KeyEvent(key_code=KeyCode.M, modifiers=ModifierKey.NONE, char='m')
        event_upper = KeyEvent(key_code=KeyCode.M, modifiers=ModifierKey.NONE, char='M')
        
        # Both 'm' and 'M' should behave identically since they use KeyCode.M
        # 'm' with selection should work for move_files
        action_lower_with_sel = find_action_for_event(event_lower, has_selection=True)
        self.assertEqual(
            action_lower_with_sel, 'move_files',
            "'m' should be bound to move_files with selection"
        )
        
        # 'M' with selection should also work for move_files (case-insensitive)
        action_upper_with_sel = find_action_for_event(event_upper, has_selection=True)
        self.assertEqual(
            action_upper_with_sel, 'move_files',
            "'M' should be bound to move_files with selection (case-insensitive)"
        )
        
        # 'm' without selection should work for create_directory
        action_lower_no_sel = find_action_for_event(event_lower, has_selection=False)
        self.assertEqual(
            action_lower_no_sel, 'create_directory',
            "'m' should be bound to create_directory without selection"
        )
        
        # 'M' without selection should also work for create_directory (case-insensitive)
        action_upper_no_sel = find_action_for_event(event_upper, has_selection=False)
        self.assertEqual(
            action_upper_no_sel, 'create_directory',
            "'M' should be bound to create_directory without selection (case-insensitive)"
        )


if __name__ == '__main__':
    unittest.main()
