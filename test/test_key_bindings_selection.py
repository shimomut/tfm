#!/usr/bin/env python3
"""
Test file for extended KEY_BINDINGS format with selection requirements.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from _config import Config


class TestKeyBindingsSelection(unittest.TestCase):
    """Test the extended KEY_BINDINGS format with selection requirements."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.key_bindings = Config.KEY_BINDINGS
    
    def test_simple_format_parsing(self):
        """Test that simple format key bindings are parsed correctly."""
        # Test simple format (list of keys)
        simple_bindings = ['quit', 'help', 'toggle_hidden', 'search']
        
        for action in simple_bindings:
            self.assertIn(action, self.key_bindings)
            binding = self.key_bindings[action]
            self.assertIsInstance(binding, list, f"Action '{action}' should have simple list format")
            self.assertTrue(len(binding) > 0, f"Action '{action}' should have at least one key")
    
    def test_extended_format_parsing(self):
        """Test that extended format key bindings are parsed correctly."""
        # Test extended format (dict with keys and selection)
        extended_bindings = ['copy_files', 'move_files', 'delete_files', 'create_archive']
        
        for action in extended_bindings:
            self.assertIn(action, self.key_bindings)
            binding = self.key_bindings[action]
            self.assertIsInstance(binding, dict, f"Action '{action}' should have extended dict format")
            self.assertIn('keys', binding, f"Action '{action}' should have 'keys' field")
            self.assertIn('selection', binding, f"Action '{action}' should have 'selection' field")
            self.assertIsInstance(binding['keys'], list, f"Action '{action}' keys should be a list")
            self.assertTrue(len(binding['keys']) > 0, f"Action '{action}' should have at least one key")
    
    def test_selection_requirements(self):
        """Test that selection requirements are set correctly."""
        # Test actions that require selection
        required_selection_actions = ['copy_files', 'move_files', 'delete_files', 'create_archive']
        
        for action in required_selection_actions:
            binding = self.key_bindings[action]
            self.assertEqual(binding['selection'], 'required', 
                           f"Action '{action}' should require selection")
    
    def test_valid_selection_values(self):
        """Test that all selection values are valid."""
        valid_selections = {'any', 'required', 'none'}
        
        for action, binding in self.key_bindings.items():
            if isinstance(binding, dict) and 'selection' in binding:
                selection = binding['selection']
                self.assertIn(selection, valid_selections, 
                            f"Action '{action}' has invalid selection value: '{selection}'")
    
    def test_key_binding_utility_functions(self):
        """Test utility functions for working with key bindings."""
        
        def get_keys_for_action(action):
            """Get keys for an action, handling both simple and extended formats."""
            binding = Config.KEY_BINDINGS.get(action)
            if isinstance(binding, list):
                return binding
            elif isinstance(binding, dict) and 'keys' in binding:
                return binding['keys']
            return []
        
        def get_selection_requirement(action):
            """Get selection requirement for an action."""
            binding = Config.KEY_BINDINGS.get(action)
            if isinstance(binding, dict) and 'selection' in binding:
                return binding['selection']
            return 'any'  # default
        
        def is_action_available(action, has_selection):
            """Check if action is available based on selection status."""
            requirement = get_selection_requirement(action)
            if requirement == 'required':
                return has_selection
            elif requirement == 'none':
                return not has_selection
            else:  # 'any'
                return True
        
        # Test utility functions
        # Note: With alphabet case-insensitive behavior, 'q' alone matches both 'q' and 'Q'
        self.assertEqual(get_keys_for_action('quit'), ['q'])
        self.assertEqual(get_keys_for_action('copy_files'), ['c'])
        self.assertEqual(get_keys_for_action('nonexistent'), [])
        
        self.assertEqual(get_selection_requirement('quit'), 'any')
        self.assertEqual(get_selection_requirement('copy_files'), 'required')
        self.assertEqual(get_selection_requirement('nonexistent'), 'any')
        
        # Test availability logic
        self.assertTrue(is_action_available('quit', True))
        self.assertTrue(is_action_available('quit', False))
        
        self.assertTrue(is_action_available('copy_files', True))
        self.assertFalse(is_action_available('copy_files', False))
        
        # Test hypothetical 'none' requirement
        test_binding = {'keys': ['test'], 'selection': 'none'}
        Config.KEY_BINDINGS['test_none'] = test_binding
        self.assertFalse(is_action_available('test_none', True))
        self.assertTrue(is_action_available('test_none', False))
        del Config.KEY_BINDINGS['test_none']
    
    def test_backward_compatibility(self):
        """Test that existing simple format bindings still work."""
        # All simple format bindings should be accessible
        simple_actions = []
        extended_actions = []
        
        for action, binding in self.key_bindings.items():
            if isinstance(binding, list):
                simple_actions.append(action)
            elif isinstance(binding, dict):
                extended_actions.append(action)
        
        # Should have both types
        self.assertTrue(len(simple_actions) > 0, "Should have simple format bindings")
        self.assertTrue(len(extended_actions) > 0, "Should have extended format bindings")
        
        # Simple actions should work regardless of selection
        for action in simple_actions:
            keys = self.key_bindings[action]
            self.assertIsInstance(keys, list)
            self.assertTrue(len(keys) > 0)


if __name__ == '__main__':
    unittest.main()