#!/usr/bin/env python3
"""
Test Jump Dialog Integration
Tests the integration of jump dialog with the main TFM application
"""

import unittest
import tempfile
import time
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_config import DefaultConfig
from tfm_jump_dialog import JumpDialog


class TestJumpDialogIntegration(unittest.TestCase):
    """Test cases for jump dialog integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = DefaultConfig()
        
    def test_jump_dialog_key_binding_exists(self):
        """Test that jump dialog key binding exists in configuration"""
        # Check that jump_dialog key binding is defined
        self.assertIn('jump_dialog', self.config.KEY_BINDINGS)
        
        # Check that it's bound to 'J' (Shift+J)
        jump_keys = self.config.KEY_BINDINGS['jump_dialog']
        self.assertIn('J', jump_keys)
    
    def test_jump_dialog_config_values(self):
        """Test that jump dialog configuration values are set"""
        # Check that MAX_JUMP_DIRECTORIES is defined
        self.assertTrue(hasattr(self.config, 'MAX_JUMP_DIRECTORIES'))
        self.assertIsInstance(self.config.MAX_JUMP_DIRECTORIES, int)
        self.assertGreater(self.config.MAX_JUMP_DIRECTORIES, 0)
    
    def test_jump_dialog_instantiation(self):
        """Test that jump dialog can be instantiated with config"""
        jump_dialog = JumpDialog(self.config)
        
        # Check initial state
        self.assertFalse(jump_dialog.mode)
        self.assertEqual(jump_dialog.max_directories, self.config.MAX_JUMP_DIRECTORIES)
        self.assertIsNotNone(jump_dialog.progress_animator)
    
    def test_jump_dialog_basic_functionality(self):
        """Test basic jump dialog functionality"""
        jump_dialog = JumpDialog(self.config)
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create some subdirectories
            (temp_path / "subdir1").mkdir()
            (temp_path / "subdir2").mkdir()
            
            # Show dialog
            jump_dialog.show(temp_path)
            self.assertTrue(jump_dialog.mode)
            self.assertTrue(jump_dialog.searching)
            
            # Wait for scanning to start
            time.sleep(0.1)
            
            # Exit dialog
            jump_dialog.exit()
            self.assertFalse(jump_dialog.mode)
            self.assertFalse(jump_dialog.searching)
    
    def test_key_binding_uniqueness(self):
        """Test that jump dialog key binding doesn't conflict with others"""
        jump_keys = set(self.config.KEY_BINDINGS['jump_dialog'])
        
        # Check against all other key bindings
        for action, keys in self.config.KEY_BINDINGS.items():
            if action == 'jump_dialog':
                continue
                
            # Handle both simple and extended key binding formats
            if isinstance(keys, dict):
                other_keys = set(keys['keys'])
            else:
                other_keys = set(keys)
            
            # Check for conflicts
            conflicts = jump_keys.intersection(other_keys)
            self.assertEqual(len(conflicts), 0, 
                           f"Jump dialog key binding conflicts with {action}: {conflicts}")
    
    def test_import_statements(self):
        """Test that all required imports work"""
        try:
            # Test importing main components
            from tfm_jump_dialog import JumpDialog, JumpDialogHelpers
            from tfm_main import FileManager
            
            # Test that JumpDialog can be imported in main
            self.assertTrue(hasattr(JumpDialog, 'show'))
            self.assertTrue(hasattr(JumpDialog, 'handle_input'))
            self.assertTrue(hasattr(JumpDialog, 'draw'))
            
            # Test that JumpDialogHelpers has required methods
            self.assertTrue(hasattr(JumpDialogHelpers, 'navigate_to_directory'))
            
        except ImportError as e:
            self.fail(f"Import error: {e}")


def run_integration_tests():
    """Run all integration tests"""
    print("Running Jump Dialog Integration Tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJumpDialogIntegration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} integration tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests")
        
        for test, traceback in result.failures:
            print(f"\nFAILURE: {test}")
            print(traceback)
            
        for test, traceback in result.errors:
            print(f"\nERROR: {test}")
            print(traceback)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_integration_tests()