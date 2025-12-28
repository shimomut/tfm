#!/usr/bin/env python3
"""
Test file for integration between extended key bindings and tfm_config.py.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from tfm_config import ConfigManager, is_action_available
from _config import Config


class TestConfigIntegration(unittest.TestCase):
    """Test the integration between extended key bindings and tfm_config.py."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        # Use the Config class directly for testing
        self.config_manager.config = Config()
    
    def test_get_key_for_action_simple_format(self):
        """Test getting keys for actions in simple format."""
        # Note: With alphabet case-insensitive behavior, 'q' alone matches both 'q' and 'Q'
        keys = self.config_manager.get_key_for_action('quit')
        self.assertEqual(keys, ['q'])
        
        keys = self.config_manager.get_key_for_action('help')
        self.assertEqual(keys, ['?'])
    
    def test_get_key_for_action_extended_format(self):
        """Test getting keys for actions in extended format."""
        # Note: With alphabet case-insensitive behavior, 'c' alone matches both 'c' and 'C'
        keys = self.config_manager.get_key_for_action('copy_files')
        self.assertEqual(keys, ['c'])
        
        keys = self.config_manager.get_key_for_action('delete_files')
        self.assertEqual(keys, ['k'])
    
    def test_get_selection_requirement(self):
        """Test getting selection requirements."""
        # Simple format defaults to 'any'
        requirement = self.config_manager.get_selection_requirement('quit')
        self.assertEqual(requirement, 'any')
        
        # Extended format with explicit requirement
        requirement = self.config_manager.get_selection_requirement('copy_files')
        self.assertEqual(requirement, 'required')
        
        requirement = self.config_manager.get_selection_requirement('delete_files')
        self.assertEqual(requirement, 'required')
    
    def test_is_action_available(self):
        """Test action availability based on selection status."""
        # Actions with 'any' requirement
        self.assertTrue(self.config_manager.is_action_available('quit', True))
        self.assertTrue(self.config_manager.is_action_available('quit', False))
        
        # Actions with 'required' requirement
        self.assertTrue(self.config_manager.is_action_available('copy_files', True))
        self.assertFalse(self.config_manager.is_action_available('copy_files', False))
        
        self.assertTrue(self.config_manager.is_action_available('delete_files', True))
        self.assertFalse(self.config_manager.is_action_available('delete_files', False))
    
    def test_is_key_bound_to_action(self):
        """Test basic key binding checking."""
        # Simple format - alphabet is case-insensitive, so 'q' matches both 'q' and 'Q'
        self.assertTrue(self.config_manager.is_key_bound_to_action('q', 'quit'))
        # Note: 'Q' is not explicitly in the config, but should match due to case-insensitive alphabet behavior
        # However, is_key_bound_to_action checks the literal key list, not the matching behavior
        # So this test should check what's actually in the config
        self.assertFalse(self.config_manager.is_key_bound_to_action('Q', 'quit'))
        self.assertFalse(self.config_manager.is_key_bound_to_action('x', 'quit'))
        
        # Extended format
        self.assertTrue(self.config_manager.is_key_bound_to_action('c', 'copy_files'))
        self.assertFalse(self.config_manager.is_key_bound_to_action('C', 'copy_files'))
        self.assertFalse(self.config_manager.is_key_bound_to_action('x', 'copy_files'))
    
    def test_is_key_bound_to_action_with_selection(self):
        """Test selection-aware key binding checking."""
        # Actions with 'any' requirement - always available
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('q', 'quit', True))
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('q', 'quit', False))
        
        # Actions with 'required' requirement - only available with selection
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('c', 'copy_files', True))
        self.assertFalse(self.config_manager.is_key_bound_to_action_with_selection('c', 'copy_files', False))
        
        # Non-bound keys should always return False
        self.assertFalse(self.config_manager.is_key_bound_to_action_with_selection('x', 'copy_files', True))
        self.assertFalse(self.config_manager.is_key_bound_to_action_with_selection('x', 'copy_files', False))
    
    def test_module_level_functions(self):
        """Test module-level convenience functions."""
        # Basic key binding
        self.assertTrue(is_key_bound_to('q', 'quit'))
        self.assertFalse(is_key_bound_to('x', 'quit'))
        
        # Selection-aware key binding
        self.assertTrue(is_key_bound_to_with_selection('q', 'quit', True))
        self.assertTrue(is_key_bound_to_with_selection('q', 'quit', False))
        
        self.assertTrue(is_key_bound_to_with_selection('c', 'copy_files', True))
        self.assertFalse(is_key_bound_to_with_selection('c', 'copy_files', False))
        
        # Action availability
        self.assertTrue(is_action_available('quit', True))
        self.assertTrue(is_action_available('quit', False))
        
        self.assertTrue(is_action_available('copy_files', True))
        self.assertFalse(is_action_available('copy_files', False))
    
    def test_nonexistent_action(self):
        """Test behavior with non-existent actions."""
        keys = self.config_manager.get_key_for_action('nonexistent_action')
        self.assertEqual(keys, [])
        
        requirement = self.config_manager.get_selection_requirement('nonexistent_action')
        self.assertEqual(requirement, 'any')
        
        self.assertTrue(self.config_manager.is_action_available('nonexistent_action', True))
        self.assertTrue(self.config_manager.is_action_available('nonexistent_action', False))
        
        self.assertFalse(self.config_manager.is_key_bound_to_action('x', 'nonexistent_action'))
        self.assertFalse(self.config_manager.is_key_bound_to_action_with_selection('x', 'nonexistent_action', True))


if __name__ == '__main__':
    unittest.main()