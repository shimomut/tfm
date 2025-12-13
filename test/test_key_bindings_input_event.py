#!/usr/bin/env python3
"""
Test key bindings with InputEvent support.

This test verifies that the key binding system correctly handles InputEvent objects
from TTK, including both printable characters and special keys with modifiers.
"""

import sys
import unittest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ttk import InputEvent, KeyCode, ModifierKey
from tfm_config import (
    ConfigManager,
    is_input_event_bound_to,
    is_input_event_bound_to_with_selection
)


class TestKeyBindingsInputEvent(unittest.TestCase):
    """Test key bindings with InputEvent objects."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
    
    def test_printable_char_input_event(self):
        """Test that printable character InputEvents are recognized."""
        # Create InputEvent for 'q' (quit)
        event = InputEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
        
        # Check if it's bound to quit action
        self.assertTrue(
            self.config_manager.is_input_event_bound_to_action(event, 'quit'),
            "InputEvent for 'q' should be bound to quit action"
        )
    
    def test_special_key_input_event(self):
        """Test that special key InputEvents are recognized."""
        # Create InputEvent for HOME key (select_all)
        event = InputEvent(key_code=KeyCode.HOME, modifiers=ModifierKey.NONE)
        
        # Check if it's bound to select_all action
        self.assertTrue(
            self.config_manager.is_input_event_bound_to_action(event, 'select_all'),
            "InputEvent for HOME key should be bound to select_all action"
        )
    
    def test_ctrl_modified_input_event(self):
        """Test that Ctrl-modified InputEvents are recognized."""
        # Create InputEvent for Ctrl+L (redraw - this is a common TFM binding)
        # Note: We'll test with a regular key since Ctrl combinations may not be in default config
        # Let's test that a Ctrl-modified event is properly converted to key string
        event = InputEvent(key_code=ord('r'), modifiers=ModifierKey.CONTROL, char='r')
        
        # The event should be converted to 'CTRL_R' format
        # Even if not bound, the conversion should work
        from tfm_input_utils import input_event_to_key_char
        key_char = input_event_to_key_char(event)
        self.assertEqual(key_char, 'CTRL_R', "Ctrl+R should be converted to 'CTRL_R'")
    
    def test_input_event_with_selection_requirement(self):
        """Test InputEvent with selection requirements."""
        # Create InputEvent for 'c' (copy_files - requires selection)
        event = InputEvent(key_code=ord('c'), modifiers=ModifierKey.NONE, char='c')
        
        # Should be bound when files are selected
        self.assertTrue(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                event, 'copy_files', has_selection=True
            ),
            "InputEvent for 'c' should be bound to copy_files when files are selected"
        )
        
        # Should NOT be bound when no files are selected
        self.assertFalse(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                event, 'copy_files', has_selection=False
            ),
            "InputEvent for 'c' should NOT be bound to copy_files when no files are selected"
        )
    
    def test_input_event_no_selection_requirement(self):
        """Test InputEvent with 'none' selection requirement."""
        # Create InputEvent for 'M' (create_directory - requires no selection)
        event = InputEvent(key_code=ord('M'), modifiers=ModifierKey.NONE, char='M')
        
        # Should be bound when no files are selected
        self.assertTrue(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                event, 'create_directory', has_selection=False
            ),
            "InputEvent for 'M' should be bound to create_directory when no files are selected"
        )
        
        # Should NOT be bound when files are selected
        self.assertFalse(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                event, 'create_directory', has_selection=True
            ),
            "InputEvent for 'M' should NOT be bound to create_directory when files are selected"
        )
    
    def test_input_event_any_selection_requirement(self):
        """Test InputEvent with 'any' selection requirement."""
        # Create InputEvent for 'q' (quit - works regardless of selection)
        event = InputEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
        
        # Should be bound with selection
        self.assertTrue(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                event, 'quit', has_selection=True
            ),
            "InputEvent for 'q' should be bound to quit with selection"
        )
        
        # Should be bound without selection
        self.assertTrue(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                event, 'quit', has_selection=False
            ),
            "InputEvent for 'q' should be bound to quit without selection"
        )
    
    def test_null_input_event(self):
        """Test that None InputEvent is handled gracefully."""
        # None event should return False
        self.assertFalse(
            self.config_manager.is_input_event_bound_to_action(None, 'quit'),
            "None InputEvent should return False"
        )
        
        self.assertFalse(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                None, 'quit', has_selection=True
            ),
            "None InputEvent should return False with selection check"
        )
    
    def test_unbound_input_event(self):
        """Test that unbound InputEvents return False."""
        # Create InputEvent for a key that's not bound to anything
        event = InputEvent(key_code=ord('~'), modifiers=ModifierKey.NONE, char='~')
        
        # Should not be bound to any action
        self.assertFalse(
            self.config_manager.is_input_event_bound_to_action(event, 'quit'),
            "Unbound InputEvent should return False"
        )
    
    def test_module_level_functions(self):
        """Test module-level convenience functions."""
        # Test is_input_event_bound_to
        event = InputEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
        self.assertTrue(
            is_input_event_bound_to(event, 'quit'),
            "Module-level is_input_event_bound_to should work"
        )
        
        # Test is_input_event_bound_to_with_selection
        event_copy = InputEvent(key_code=ord('c'), modifiers=ModifierKey.NONE, char='c')
        self.assertTrue(
            is_input_event_bound_to_with_selection(event_copy, 'copy_files', True),
            "Module-level is_input_event_bound_to_with_selection should work"
        )
        
        self.assertFalse(
            is_input_event_bound_to_with_selection(event_copy, 'copy_files', False),
            "Module-level function should respect selection requirements"
        )
    
    def test_case_sensitivity(self):
        """Test that case sensitivity is preserved."""
        # Both 'm' and 'M' are bound to both move_files and create_directory
        # The difference is in selection requirements
        event_lower = InputEvent(key_code=ord('m'), modifiers=ModifierKey.NONE, char='m')
        
        # 'm' with selection should work for move_files
        self.assertTrue(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                event_lower, 'move_files', has_selection=True
            ),
            "'m' should be bound to move_files with selection"
        )
        
        # 'm' without selection should work for create_directory
        self.assertTrue(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                event_lower, 'create_directory', has_selection=False
            ),
            "'m' should be bound to create_directory without selection"
        )
        
        # But not the other way around
        self.assertFalse(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                event_lower, 'move_files', has_selection=False
            ),
            "'m' should NOT be bound to move_files without selection"
        )
        
        self.assertFalse(
            self.config_manager.is_input_event_bound_to_action_with_selection(
                event_lower, 'create_directory', has_selection=True
            ),
            "'m' should NOT be bound to create_directory with selection"
        )


if __name__ == '__main__':
    unittest.main()
