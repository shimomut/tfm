#!/usr/bin/env python3
"""
Test Configuration Completeness
Verifies that all configuration parameters are properly defined
"""

import unittest
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_config import DefaultConfig
from _config import Config


class TestConfigCompleteness(unittest.TestCase):
    """Test that all configuration parameters are properly defined"""
    
    def setUp(self):
        """Set up test environment"""
        self.default_config = DefaultConfig()
        self.user_config = Config()
    
    def test_performance_settings_exist(self):
        """Test that all performance settings are defined"""
        performance_settings = [
            'MAX_LOG_MESSAGES',
            'MAX_SEARCH_RESULTS', 
            'MAX_JUMP_DIRECTORIES',
            'MAX_HISTORY_ENTRIES'
        ]
        
        for setting in performance_settings:
            with self.subTest(setting=setting):
                # Check default config
                self.assertTrue(hasattr(self.default_config, setting), 
                              f"DefaultConfig missing {setting}")
                
                # Check user config
                self.assertTrue(hasattr(self.user_config, setting), 
                              f"Config missing {setting}")
                
                # Check values are reasonable
                default_value = getattr(self.default_config, setting)
                user_value = getattr(self.user_config, setting)
                
                self.assertIsInstance(default_value, int, 
                                    f"DefaultConfig.{setting} should be int")
                self.assertIsInstance(user_value, int, 
                                    f"Config.{setting} should be int")
                self.assertGreater(default_value, 0, 
                                 f"DefaultConfig.{setting} should be positive")
                self.assertGreater(user_value, 0, 
                                 f"Config.{setting} should be positive")
    
    def test_dialog_settings_exist(self):
        """Test that all dialog settings are defined"""
        dialog_settings = [
            'INFO_DIALOG_WIDTH_RATIO',
            'INFO_DIALOG_HEIGHT_RATIO', 
            'INFO_DIALOG_MIN_WIDTH',
            'INFO_DIALOG_MIN_HEIGHT',
            'LIST_DIALOG_WIDTH_RATIO',
            'LIST_DIALOG_HEIGHT_RATIO',
            'LIST_DIALOG_MIN_WIDTH',
            'LIST_DIALOG_MIN_HEIGHT'
        ]
        
        for setting in dialog_settings:
            with self.subTest(setting=setting):
                # Check default config
                self.assertTrue(hasattr(self.default_config, setting), 
                              f"DefaultConfig missing {setting}")
                
                # Check user config
                self.assertTrue(hasattr(self.user_config, setting), 
                              f"Config missing {setting}")
                
                # Check values are reasonable
                default_value = getattr(self.default_config, setting)
                user_value = getattr(self.user_config, setting)
                
                if 'RATIO' in setting:
                    # Ratio values should be floats between 0 and 1
                    self.assertIsInstance(default_value, (int, float), 
                                        f"DefaultConfig.{setting} should be numeric")
                    self.assertIsInstance(user_value, (int, float), 
                                        f"Config.{setting} should be numeric")
                    self.assertGreater(default_value, 0, 
                                     f"DefaultConfig.{setting} should be positive")
                    self.assertLessEqual(default_value, 1, 
                                       f"DefaultConfig.{setting} should be <= 1")
                else:
                    # Min width/height values should be positive integers
                    self.assertIsInstance(default_value, int, 
                                        f"DefaultConfig.{setting} should be int")
                    self.assertIsInstance(user_value, int, 
                                        f"Config.{setting} should be int")
                    self.assertGreater(default_value, 0, 
                                     f"DefaultConfig.{setting} should be positive")
    
    def test_animation_settings_exist(self):
        """Test that animation settings are defined"""
        animation_settings = [
            'PROGRESS_ANIMATION_PATTERN',
            'PROGRESS_ANIMATION_SPEED'
        ]
        
        for setting in animation_settings:
            with self.subTest(setting=setting):
                # Check default config
                self.assertTrue(hasattr(self.default_config, setting), 
                              f"DefaultConfig missing {setting}")
                
                # Check user config
                self.assertTrue(hasattr(self.user_config, setting), 
                              f"Config missing {setting}")
    
    def test_jump_dialog_key_binding_exists(self):
        """Test that jump dialog key binding exists in both configs"""
        # Check default config
        self.assertIn('jump_dialog', self.default_config.KEY_BINDINGS)
        self.assertIn('J', self.default_config.KEY_BINDINGS['jump_dialog'])
        
        # Check user config
        self.assertIn('jump_dialog', self.user_config.KEY_BINDINGS)
        self.assertIn('J', self.user_config.KEY_BINDINGS['jump_dialog'])
    
    def test_config_values_consistency(self):
        """Test that default and user config have consistent values for key settings"""
        # These settings should have the same default values
        consistent_settings = [
            'MAX_LOG_MESSAGES',
            'MAX_SEARCH_RESULTS',
            'MAX_JUMP_DIRECTORIES',
            'MAX_HISTORY_ENTRIES',
            'INFO_DIALOG_WIDTH_RATIO',
            'INFO_DIALOG_HEIGHT_RATIO',
            'LIST_DIALOG_WIDTH_RATIO',
            'LIST_DIALOG_HEIGHT_RATIO'
        ]
        
        for setting in consistent_settings:
            with self.subTest(setting=setting):
                default_value = getattr(self.default_config, setting)
                user_value = getattr(self.user_config, setting)
                
                self.assertEqual(default_value, user_value, 
                               f"{setting} should have same value in both configs")
    
    def test_jump_dialog_can_use_config_values(self):
        """Test that jump dialog can access its configuration values"""
        from tfm_jump_dialog import JumpDialog
        
        # Test with default config
        jump_dialog_default = JumpDialog(self.default_config)
        self.assertEqual(jump_dialog_default.max_directories, 
                        self.default_config.MAX_JUMP_DIRECTORIES)
        
        # Test with user config
        jump_dialog_user = JumpDialog(self.user_config)
        self.assertEqual(jump_dialog_user.max_directories, 
                        self.user_config.MAX_JUMP_DIRECTORIES)


def run_config_tests():
    """Run all configuration tests"""
    print("Running Configuration Completeness Tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfigCompleteness)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} configuration tests passed!")
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
    run_config_tests()