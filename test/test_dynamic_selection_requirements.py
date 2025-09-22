#!/usr/bin/env python3
"""
Test file for dynamic selection requirements - demonstrating that users can configure
any action with selection requirements through the Config class.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from unittest.mock import Mock
from tfm_config import ConfigManager


class TestDynamicSelectionRequirements(unittest.TestCase):
    """Test that users can configure any action with selection requirements."""
    
    def setUp(self):
        """Set up test fixtures with custom configuration."""
        self.config_manager = ConfigManager()
        
        # Create a custom config class with various selection requirements
        class CustomConfig:
            KEY_BINDINGS = {
                # Standard actions with 'any' (default behavior)
                'quit': ['q', 'Q'],
                'help': ['?'],
                'search': ['f'],
                
                # Actions requiring selection
                'copy_files': {'keys': ['c', 'C'], 'selection': 'required'},
                'delete_files': {'keys': ['k', 'K'], 'selection': 'required'},
                'view_text': {'keys': ['v', 'V'], 'selection': 'required'},  # User configured this to require selection
                
                # Actions that only work when nothing is selected
                'create_file': {'keys': ['E'], 'selection': 'none'},
                'search_dialog': {'keys': ['F'], 'selection': 'none'},  # User configured this to require no selection
                
                # Explicit 'any' configuration
                'toggle_hidden': {'keys': ['.'], 'selection': 'any'},
                'sort_menu': {'keys': ['s', 'S'], 'selection': 'any'},
            }
        
        self.config_manager.config = CustomConfig()
    
    def test_user_configured_selection_requirements(self):
        """Test that users can configure any action with selection requirements."""
        
        # Test actions with 'any' requirement (work regardless of selection)
        any_actions = ['quit', 'help', 'search', 'toggle_hidden', 'sort_menu']
        for action in any_actions:
            self.assertTrue(self.config_manager.is_action_available(action, True))
            self.assertTrue(self.config_manager.is_action_available(action, False))
        
        # Test actions with 'required' requirement (only work with selection)
        required_actions = ['copy_files', 'delete_files', 'view_text']
        for action in required_actions:
            self.assertTrue(self.config_manager.is_action_available(action, True))
            self.assertFalse(self.config_manager.is_action_available(action, False))
        
        # Test actions with 'none' requirement (only work without selection)
        none_actions = ['create_file', 'search_dialog']
        for action in none_actions:
            self.assertFalse(self.config_manager.is_action_available(action, True))
            self.assertTrue(self.config_manager.is_action_available(action, False))
    
    def test_key_binding_with_custom_requirements(self):
        """Test key binding checking with custom selection requirements."""
        
        # Test 'view_text' which user configured to require selection
        self.assertTrue(self.config_manager.is_key_bound_to_action('v', 'view_text'))
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('v', 'view_text', True))
        self.assertFalse(self.config_manager.is_key_bound_to_action_with_selection('v', 'view_text', False))
        
        # Test 'search_dialog' which user configured to require no selection
        self.assertTrue(self.config_manager.is_key_bound_to_action('F', 'search_dialog'))
        self.assertFalse(self.config_manager.is_key_bound_to_action_with_selection('F', 'search_dialog', True))
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('F', 'search_dialog', False))
        
        # Test 'quit' which works regardless of selection
        self.assertTrue(self.config_manager.is_key_bound_to_action('q', 'quit'))
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('q', 'quit', True))
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('q', 'quit', False))
    
    def test_mixed_format_configuration(self):
        """Test that simple and extended formats can be mixed in the same configuration."""
        
        # Simple format actions
        simple_actions = ['quit', 'help', 'search']
        for action in simple_actions:
            keys = self.config_manager.get_key_for_action(action)
            self.assertIsInstance(keys, list)
            self.assertTrue(len(keys) > 0)
            requirement = self.config_manager.get_selection_requirement(action)
            self.assertEqual(requirement, 'any')  # Default for simple format
        
        # Extended format actions
        extended_actions = ['copy_files', 'create_file', 'toggle_hidden']
        for action in extended_actions:
            keys = self.config_manager.get_key_for_action(action)
            self.assertIsInstance(keys, list)
            self.assertTrue(len(keys) > 0)
            requirement = self.config_manager.get_selection_requirement(action)
            self.assertIn(requirement, ['any', 'required', 'none'])
    
    def test_file_manager_integration(self):
        """Test that the unified is_key_for_action method works with custom requirements."""
        
        # Mock file manager
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
        
        file_manager = MockFileManager(self.config_manager)
        
        # Test without selection
        file_manager.left_pane['selected_files'] = set()
        
        # Actions that work without selection
        self.assertTrue(file_manager.is_key_for_action(ord('q'), 'quit'))
        self.assertTrue(file_manager.is_key_for_action(ord('E'), 'create_file'))
        self.assertTrue(file_manager.is_key_for_action(ord('F'), 'search_dialog'))
        
        # Actions that require selection - should not work
        self.assertFalse(file_manager.is_key_for_action(ord('c'), 'copy_files'))
        self.assertFalse(file_manager.is_key_for_action(ord('v'), 'view_text'))
        
        # Test with selection
        file_manager.left_pane['selected_files'] = {'/path/to/file.txt'}
        
        # Actions that work with selection
        self.assertTrue(file_manager.is_key_for_action(ord('q'), 'quit'))  # Still works
        self.assertTrue(file_manager.is_key_for_action(ord('c'), 'copy_files'))  # Now works
        self.assertTrue(file_manager.is_key_for_action(ord('v'), 'view_text'))  # Now works
        
        # Actions that require no selection - should not work
        self.assertFalse(file_manager.is_key_for_action(ord('E'), 'create_file'))
        self.assertFalse(file_manager.is_key_for_action(ord('F'), 'search_dialog'))
    
    def test_user_can_override_default_behavior(self):
        """Test that users can override default TFM behavior through configuration."""
        
        # In our custom config, 'view_text' requires selection (different from default TFM)
        requirement = self.config_manager.get_selection_requirement('view_text')
        self.assertEqual(requirement, 'required')
        
        # 'search_dialog' requires no selection (different from default TFM)
        requirement = self.config_manager.get_selection_requirement('search_dialog')
        self.assertEqual(requirement, 'none')
        
        # This demonstrates that users have full control over selection requirements


if __name__ == '__main__':
    unittest.main()