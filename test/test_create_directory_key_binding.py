#!/usr/bin/env python3
"""
Test file for create_directory key binding functionality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from tfm_config import ConfigManager
from _config import Config


class TestCreateDirectoryKeyBinding(unittest.TestCase):
    """Test the create_directory key binding functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        self.config_manager.config = Config()
    
    def test_create_directory_key_binding_exists(self):
        """Test that create_directory action is properly configured."""
        keys = self.config_manager.get_key_for_action('create_directory')
        self.assertEqual(keys, ['M'])
        
        # Test that the key is bound
        self.assertTrue(self.config_manager.is_key_bound_to_action('M', 'create_directory'))
        self.assertFalse(self.config_manager.is_key_bound_to_action('D', 'create_directory'))
    
    def test_create_directory_selection_requirement(self):
        """Test that create_directory has the correct selection requirement."""
        requirement = self.config_manager.get_selection_requirement('create_directory')
        # Should be 'none' since it uses extended format
        self.assertEqual(requirement, 'none')
        
        # Should only be available when no files are selected
        self.assertFalse(self.config_manager.is_action_available('create_directory', True))
        self.assertTrue(self.config_manager.is_action_available('create_directory', False))
    
    def test_create_directory_key_binding_with_selection(self):
        """Test create_directory key binding with different selection states."""
        # Should only work when no files are selected
        self.assertFalse(self.config_manager.is_key_bound_to_action_with_selection('M', 'create_directory', True))
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('M', 'create_directory', False))
    
    def test_move_files_still_requires_selection(self):
        """Test that move_files still requires selection after removing directory creation."""
        requirement = self.config_manager.get_selection_requirement('move_files')
        self.assertEqual(requirement, 'required')
        
        # Should only be available with selection
        self.assertTrue(self.config_manager.is_action_available('move_files', True))
        self.assertFalse(self.config_manager.is_action_available('move_files', False))
        
        # Key binding should respect selection requirement
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('m', 'move_files', True))
        self.assertFalse(self.config_manager.is_key_bound_to_action_with_selection('m', 'move_files', False))
    
    def test_create_directory_vs_create_file(self):
        """Test that create_directory and create_file are separate actions."""
        dir_keys = self.config_manager.get_key_for_action('create_directory')
        file_keys = self.config_manager.get_key_for_action('create_file')
        
        self.assertEqual(dir_keys, ['M'])
        self.assertEqual(file_keys, ['E'])
        
        # Different keys should be bound to different actions
        self.assertTrue(self.config_manager.is_key_bound_to_action('M', 'create_directory'))
        self.assertFalse(self.config_manager.is_key_bound_to_action('M', 'create_file'))
        
        self.assertTrue(self.config_manager.is_key_bound_to_action('E', 'create_file'))
        self.assertFalse(self.config_manager.is_key_bound_to_action('E', 'create_directory'))
    
    def test_unified_key_handling(self):
        """Test that create_directory works with the unified key handling approach."""
        
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
        self.assertTrue(fm.is_key_for_action(ord('M'), 'create_directory'))  # Should work
        self.assertFalse(fm.is_key_for_action(ord('M'), 'move_files'))  # Should not work (same key, different selection)
        
        # Test with selection
        fm.left_pane['selected_files'] = {'/path/to/file.txt'}
        self.assertFalse(fm.is_key_for_action(ord('M'), 'create_directory'))  # Should not work
        self.assertTrue(fm.is_key_for_action(ord('M'), 'move_files'))  # Should now work (same key, different selection)


if __name__ == '__main__':
    unittest.main()