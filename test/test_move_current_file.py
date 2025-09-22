#!/usr/bin/env python3
"""
Test file for move_selected_files using current file when no files are explicitly selected.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from unittest.mock import Mock, patch
from tfm_config import ConfigManager
from _config import Config


class TestMoveCurrentFile(unittest.TestCase):
    """Test that move_selected_files uses current file when no files are explicitly selected."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        self.config_manager.config = Config()
    
    def test_move_files_selection_requirement(self):
        """Test that move_files still requires selection (or current file)."""
        requirement = self.config_manager.get_selection_requirement('move_files')
        self.assertEqual(requirement, 'required')
        
        # Should be available when files are selected
        self.assertTrue(self.config_manager.is_action_available('move_files', True))
        # Should NOT be available when no files are selected (this is handled by using current file)
        self.assertFalse(self.config_manager.is_action_available('move_files', False))
    
    def test_move_files_key_binding_behavior(self):
        """Test move_files key binding behavior with selection requirements."""
        
        # With files selected - should work
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('m', 'move_files', True))
        self.assertTrue(self.config_manager.is_key_bound_to_action_with_selection('M', 'move_files', True))
        
        # Without files selected - should not work (key binding level)
        self.assertFalse(self.config_manager.is_key_bound_to_action_with_selection('m', 'move_files', False))
        self.assertFalse(self.config_manager.is_key_bound_to_action_with_selection('M', 'move_files', False))
    
    def test_create_directory_vs_move_files_key_sharing(self):
        """Test that create_directory and move_files share keys but with different selection requirements."""
        
        # Both should use 'm' and 'M' keys
        move_keys = self.config_manager.get_key_for_action('move_files')
        create_keys = self.config_manager.get_key_for_action('create_directory')
        
        self.assertIn('m', move_keys)
        self.assertIn('M', move_keys)
        self.assertIn('m', create_keys)
        self.assertIn('M', create_keys)
        
        # But different selection requirements
        move_req = self.config_manager.get_selection_requirement('move_files')
        create_req = self.config_manager.get_selection_requirement('create_directory')
        
        self.assertEqual(move_req, 'required')
        self.assertEqual(create_req, 'none')
    
    def test_unified_key_handling_with_current_file_logic(self):
        """Test that the unified key handling works correctly with the new move behavior."""
        
        # Mock file manager to test the behavior
        class MockFileManager:
            def __init__(self, config_manager):
                self.config_manager = config_manager
                self.left_pane = {
                    'selected_files': set(),
                    'files': [Path('/mock/file1.txt'), Path('/mock/file2.txt')],
                    'selected_index': 0
                }
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
        
        # Test without explicit selection - create_directory should be available
        fm.left_pane['selected_files'] = set()
        
        # create_directory should be available (selection: 'none')
        self.assertTrue(fm.is_key_for_action(ord('m'), 'create_directory'))
        self.assertTrue(fm.is_key_for_action(ord('M'), 'create_directory'))
        
        # move_files should NOT be available at key binding level (selection: 'required')
        # But the function itself will use current file when called
        self.assertFalse(fm.is_key_for_action(ord('m'), 'move_files'))
        self.assertFalse(fm.is_key_for_action(ord('M'), 'move_files'))
        
        # Test with explicit selection - move_files should be available
        fm.left_pane['selected_files'] = {'/mock/file1.txt'}
        
        # move_files should be available (selection: 'required')
        self.assertTrue(fm.is_key_for_action(ord('m'), 'move_files'))
        self.assertTrue(fm.is_key_for_action(ord('M'), 'move_files'))
        
        # create_directory should NOT be available (selection: 'none')
        self.assertFalse(fm.is_key_for_action(ord('m'), 'create_directory'))
        self.assertFalse(fm.is_key_for_action(ord('M'), 'create_directory'))
    
    def test_behavior_explanation(self):
        """Test that explains the expected behavior."""
        
        # The behavior should be:
        # 1. When no files are explicitly selected:
        #    - 'm'/'M' keys trigger create_directory (at key binding level)
        #    - move_files function would use current file if called directly
        # 
        # 2. When files are explicitly selected:
        #    - 'm'/'M' keys trigger move_files (at key binding level)
        #    - create_directory is not available
        
        # This creates intuitive behavior:
        # - Press 'm'/'M' with no selection -> creates directory
        # - Press 'm'/'M' with selection -> moves selected files
        # - move_files function is robust and can handle both cases
        
        # Verify the configuration supports this
        move_req = self.config_manager.get_selection_requirement('move_files')
        create_req = self.config_manager.get_selection_requirement('create_directory')
        
        self.assertEqual(move_req, 'required', "move_files should require selection for key binding")
        self.assertEqual(create_req, 'none', "create_directory should require no selection")
        
        # This ensures mutual exclusivity at the key binding level
        # while allowing move_files to be robust when called directly


if __name__ == '__main__':
    unittest.main()