#!/usr/bin/env python3
"""
Test file for history key binding functionality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from tfm_config import ConfigManager
from _config import Config


class TestHistoryKeyBinding(unittest.TestCase):
    """Test the history key binding functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        self.config_manager.config = Config()
    
    def test_history_key_binding_exists(self):
        """Test that history action is properly configured."""
        keys = self.config_manager.get_key_for_action('history')
        self.assertEqual(keys, ['h', 'H'])
        
        # Test that both keys are bound
        self.assertTrue(self.config_manager.is_key_bound_to_action('h', 'history'))
        self.assertTrue(self.config_manager.is_key_bound_to_action('H', 'history'))
        self.assertFalse(self.config_manager.is_key_bound_to_action('x', 'history'))
    
    def test_history_selection_requirement(self):
        """Test that history has the correct selection requirement."""
        requirement = self.config_manager.get_selection_requirement('history')
        # Should default to 'any' since it's in simple format
        self.assertEqual(requirement, 'any')
        
        # Should be available regardless of selection status
        self.assertTrue(self.config_manager.is_action_available('history', True))
        self.assertTrue(self.config_manager.is_action_available('history', False))
    
    def test_history_key_binding_with_selection(self):
        """Test history key binding with different selection states."""
        # Should work regardless of selection status
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('h', 'history', True))
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('h', 'history', False))
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('H', 'history', True))
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('H', 'history', False))
    
    def test_history_vs_other_actions(self):
        """Test that history is separate from other actions."""
        history_keys = self.config_manager.get_key_for_action('history')
        favorites_keys = self.config_manager.get_key_for_action('favorites')
        
        self.assertEqual(history_keys, ['h', 'H'])
        self.assertEqual(favorites_keys, ['j', 'J'])
        
        # Different keys should be bound to different actions
        self.assertTrue(self.config_manager.is_key_bound_to_action('h', 'history'))
        self.assertFalse(self.config_manager.is_key_bound_to_action('h', 'favorites'))
        
        self.assertTrue(self.config_manager.is_key_bound_to_action('j', 'favorites'))
        self.assertFalse(self.config_manager.is_key_bound_to_action('j', 'history'))
    
    def test_unified_key_handling(self):
        """Test that history works with the unified key handling approach."""
        
        # Mock file manager to test unified approach
        class MockFileManager:
            def __init__(self, config_manager):
                self.config_manager = config_manager
                self.left_pane = {'selected_files': set()}
                self.active_pane = 'left'
            
            def get_current_pane(self):
                return self.left_pane
            
            def is_key_for_action(self, key, action):
                """Unified method that respects selection requirements."""
                if 32 <= key <= 126:  # Printable ASCII
                    key_char = chr(key)
                    current_pane = self.get_current_pane()
                    has_selection = len(current_pane['selected_files']) > 0
                    return self.config_manager.is_key_bound_to_action_with_selection(key_char, action, has_selection)
                return False
        
        fm = MockFileManager(self.config_manager)
        
        # Test without selection
        fm.left_pane['selected_files'] = set()
        self.assertTrue(fm.is_key_for_action(ord('h'), 'history'))
        self.assertTrue(fm.is_key_for_action(ord('H'), 'history'))
        
        # Test with selection
        fm.left_pane['selected_files'] = {'/path/to/file.txt'}
        self.assertTrue(fm.is_key_for_action(ord('h'), 'history'))
        self.assertTrue(fm.is_key_for_action(ord('H'), 'history'))


if __name__ == '__main__':
    unittest.main()