"""
Test file to verify help dialog integration with create_directory key binding.

Run with: PYTHONPATH=.:src:ttk pytest test/test_help_dialog_integration.py -v
"""

import unittest
from tfm_config import ConfigManager
from _config import Config


class TestHelpDialogIntegration(unittest.TestCase):
    """Test that help dialog properly shows create_directory key binding."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        self.config_manager.config = Config()
    
    def test_create_directory_in_key_bindings(self):
        """Test that create_directory is properly configured in KEY_BINDINGS."""
        
        # Import the actual config
        config = self.config_manager.get_config()
        
        # Verify create_directory is in KEY_BINDINGS
        self.assertIn('create_directory', config.KEY_BINDINGS)
        
        # Verify it has the expected key
        keys = self.config_manager.get_key_for_action('create_directory')
        self.assertEqual(keys, ['m', 'M'])
    
    def test_format_key_bindings_function_exists(self):
        """Test that the _format_key_bindings function can handle create_directory."""
        
        from tfm_info_dialog import InfoDialogHelpers
        
        # This should not raise an exception
        try:
            formatted = InfoDialogHelpers._format_key_bindings('create_directory')
            # Should return a string
            self.assertIsInstance(formatted, str)
            # Should not be empty
            self.assertTrue(len(formatted.strip()) > 0)
        except Exception as e:
            self.fail(f"_format_key_bindings failed for create_directory: {e}")
    
    def test_create_directory_vs_create_file_formatting(self):
        """Test that create_directory and create_file format differently."""
        
        from tfm_info_dialog import InfoDialogHelpers
        
        create_dir_formatted = InfoDialogHelpers._format_key_bindings('create_directory')
        create_file_formatted = InfoDialogHelpers._format_key_bindings('create_file')
        
        # Should be different strings (they have different keys)
        self.assertNotEqual(create_dir_formatted.strip(), create_file_formatted.strip())
    
    def test_help_dialog_integration(self):
        """Test that help dialog can be generated without errors."""
        
        # This is a basic integration test to ensure the help dialog
        # can be created with the new create_directory action
        
        from tfm_info_dialog import InfoDialog, InfoDialogHelpers
        
        # Create an info dialog instance
        config = self.config_manager.get_config()
        info_dialog = InfoDialog(config)
        
        # Test that we can format all the key bindings without errors
        actions_to_test = [
            'create_directory',
            'create_file', 
            'move_files',
            'copy_files',
            'delete_files',
            'rename_file'
        ]
        
        for action in actions_to_test:
            try:
                formatted = InfoDialogHelpers._format_key_bindings(action)
                self.assertIsInstance(formatted, str)
                self.assertTrue(len(formatted) > 0)
            except Exception as e:
                self.fail(f"Failed to format key binding for {action}: {e}")
