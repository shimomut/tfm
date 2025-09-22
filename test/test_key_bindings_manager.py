#!/usr/bin/env python3
"""
Test file for KeyBindingManager utility class.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from tfm_key_bindings import KeyBindingManager, get_keys_for_action, is_action_available
from _config import Config


class TestKeyBindingManager(unittest.TestCase):
    """Test the KeyBindingManager utility class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Save original bindings
        self.original_bindings = Config.KEY_BINDINGS.copy()
        
        # Add test bindings
        Config.KEY_BINDINGS.update({
            'test_simple': ['@'],
            'test_required': {'keys': ['#'], 'selection': 'required'},
            'test_none': {'keys': ['$'], 'selection': 'none'},
            'test_any': {'keys': ['%'], 'selection': 'any'},
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original bindings
        Config.KEY_BINDINGS = self.original_bindings
    
    def test_get_keys_for_action(self):
        """Test getting keys for actions."""
        # Simple format
        self.assertEqual(KeyBindingManager.get_keys_for_action('test_simple'), ['@'])
        
        # Extended format
        self.assertEqual(KeyBindingManager.get_keys_for_action('test_required'), ['#'])
        self.assertEqual(KeyBindingManager.get_keys_for_action('test_none'), ['$'])
        self.assertEqual(KeyBindingManager.get_keys_for_action('test_any'), ['%'])
        
        # Non-existent action
        self.assertEqual(KeyBindingManager.get_keys_for_action('nonexistent'), [])
    
    def test_get_selection_requirement(self):
        """Test getting selection requirements."""
        # Simple format defaults to 'any'
        self.assertEqual(KeyBindingManager.get_selection_requirement('test_simple'), 'any')
        
        # Extended format
        self.assertEqual(KeyBindingManager.get_selection_requirement('test_required'), 'required')
        self.assertEqual(KeyBindingManager.get_selection_requirement('test_none'), 'none')
        self.assertEqual(KeyBindingManager.get_selection_requirement('test_any'), 'any')
        
        # Non-existent action defaults to 'any'
        self.assertEqual(KeyBindingManager.get_selection_requirement('nonexistent'), 'any')
    
    def test_is_action_available(self):
        """Test action availability based on selection status."""
        # Simple format (any) - always available
        self.assertTrue(KeyBindingManager.is_action_available('test_simple', True))
        self.assertTrue(KeyBindingManager.is_action_available('test_simple', False))
        
        # Required selection
        self.assertTrue(KeyBindingManager.is_action_available('test_required', True))
        self.assertFalse(KeyBindingManager.is_action_available('test_required', False))
        
        # No selection required
        self.assertFalse(KeyBindingManager.is_action_available('test_none', True))
        self.assertTrue(KeyBindingManager.is_action_available('test_none', False))
        
        # Any selection (explicit)
        self.assertTrue(KeyBindingManager.is_action_available('test_any', True))
        self.assertTrue(KeyBindingManager.is_action_available('test_any', False))
    
    def test_get_available_actions(self):
        """Test getting available actions based on selection status."""
        # With selection
        available_with_selection = KeyBindingManager.get_available_actions(True)
        self.assertIn('test_simple', available_with_selection)
        self.assertIn('test_required', available_with_selection)
        self.assertNotIn('test_none', available_with_selection)
        self.assertIn('test_any', available_with_selection)
        
        # Without selection
        available_without_selection = KeyBindingManager.get_available_actions(False)
        self.assertIn('test_simple', available_without_selection)
        self.assertNotIn('test_required', available_without_selection)
        self.assertIn('test_none', available_without_selection)
        self.assertIn('test_any', available_without_selection)
    
    def test_get_key_to_action_mapping(self):
        """Test key to action mapping."""
        # All actions
        all_mapping = KeyBindingManager.get_key_to_action_mapping()
        self.assertEqual(all_mapping['@'], 'test_simple')
        self.assertEqual(all_mapping['#'], 'test_required')
        self.assertEqual(all_mapping['$'], 'test_none')
        self.assertEqual(all_mapping['%'], 'test_any')
        
        # With selection
        with_selection_mapping = KeyBindingManager.get_key_to_action_mapping(True)
        self.assertEqual(with_selection_mapping['@'], 'test_simple')
        self.assertEqual(with_selection_mapping['#'], 'test_required')
        self.assertNotIn('$', with_selection_mapping)  # test_none not available
        self.assertEqual(with_selection_mapping['%'], 'test_any')
        
        # Without selection
        without_selection_mapping = KeyBindingManager.get_key_to_action_mapping(False)
        self.assertEqual(without_selection_mapping['@'], 'test_simple')
        self.assertNotIn('#', without_selection_mapping)  # test_required not available
        self.assertEqual(without_selection_mapping['$'], 'test_none')
        self.assertEqual(without_selection_mapping['%'], 'test_any')
    
    def test_validate_key_bindings(self):
        """Test key bindings validation."""
        # Should be valid with current test setup
        is_valid, errors = KeyBindingManager.validate_key_bindings()
        self.assertTrue(is_valid, f"Validation errors: {errors}")
        
        # Test invalid bindings
        Config.KEY_BINDINGS['invalid_empty_keys'] = []
        is_valid, errors = KeyBindingManager.validate_key_bindings()
        self.assertFalse(is_valid)
        self.assertTrue(any('empty key list' in error for error in errors))
        
        Config.KEY_BINDINGS['invalid_missing_keys'] = {'selection': 'any'}
        is_valid, errors = KeyBindingManager.validate_key_bindings()
        self.assertFalse(is_valid)
        self.assertTrue(any("missing 'keys' field" in error for error in errors))
        
        Config.KEY_BINDINGS['invalid_selection'] = {'keys': ['x'], 'selection': 'invalid'}
        is_valid, errors = KeyBindingManager.validate_key_bindings()
        self.assertFalse(is_valid)
        self.assertTrue(any('invalid selection value' in error for error in errors))
    
    def test_get_actions_by_selection_requirement(self):
        """Test grouping actions by selection requirement."""
        groups = KeyBindingManager.get_actions_by_selection_requirement()
        
        self.assertIn('test_simple', groups['any'])
        self.assertIn('test_any', groups['any'])
        self.assertIn('test_required', groups['required'])
        self.assertIn('test_none', groups['none'])
    
    def test_convenience_functions(self):
        """Test convenience functions for backward compatibility."""
        # Test convenience functions
        self.assertEqual(get_keys_for_action('test_simple'), ['@'])
        self.assertTrue(is_action_available('test_simple', True))
        self.assertTrue(is_action_available('test_simple', False))
        
        mapping = KeyBindingManager.get_key_to_action_mapping()
        self.assertIn('@', mapping)


if __name__ == '__main__':
    unittest.main()