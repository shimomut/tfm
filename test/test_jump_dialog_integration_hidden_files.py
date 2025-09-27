#!/usr/bin/env python3
"""
Integration test for JumpDialog hidden files behavior with main TFM application
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_file_operations import FileOperations


class TestJumpDialogIntegrationHiddenFiles(unittest.TestCase):
    """Test JumpDialog integration with main TFM application for hidden files"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory with hidden subdirectories
        self.temp_dir = Path(tempfile.mkdtemp())
        (self.temp_dir / "visible").mkdir()
        (self.temp_dir / ".hidden").mkdir()
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_operations_show_hidden_setting_affects_jump_dialog(self):
        """Test that changing show_hidden setting affects JumpDialog behavior"""
        # Create mock config
        config = Mock()
        config.SHOW_HIDDEN_FILES = False
        config.MAX_JUMP_DIRECTORIES = 1000
        
        # Create FileOperations and JumpDialog
        file_ops = FileOperations(config)
        
        # Import here to avoid circular imports in test setup
        from tfm_jump_dialog import JumpDialog
        jump_dialog = JumpDialog(config)
        
        # Test with show_hidden = False
        file_ops.show_hidden = False
        
        # Test the _should_include_directory method directly
        jump_dialog.file_operations = file_ops
        
        visible_dir = self.temp_dir / "visible"
        hidden_dir = self.temp_dir / ".hidden"
        
        self.assertTrue(jump_dialog._should_include_directory(visible_dir, self.temp_dir, self.temp_dir))
        self.assertFalse(jump_dialog._should_include_directory(hidden_dir, self.temp_dir, self.temp_dir))
        
        # Test with show_hidden = True
        file_ops.show_hidden = True
        
        self.assertTrue(jump_dialog._should_include_directory(visible_dir, self.temp_dir, self.temp_dir))
        self.assertTrue(jump_dialog._should_include_directory(hidden_dir, self.temp_dir, self.temp_dir))
    
    def test_jump_dialog_signature_compatibility(self):
        """Test that JumpDialog maintains backward compatibility"""
        # Create mock config
        config = Mock()
        config.MAX_JUMP_DIRECTORIES = 1000
        
        # Import here to avoid circular imports in test setup
        from tfm_jump_dialog import JumpDialog
        jump_dialog = JumpDialog(config)
        
        # Test old signature (should not raise exception)
        try:
            jump_dialog.show(self.temp_dir)
            # Immediately exit to avoid threading issues in test
            jump_dialog.exit()
            success = True
        except Exception as e:
            success = False
            
        self.assertTrue(success, "Old signature should still work for backward compatibility")
        
        # Test new signature (should not raise exception)
        file_ops = FileOperations(config)
        try:
            jump_dialog.show(self.temp_dir, file_ops)
            # Immediately exit to avoid threading issues in test
            jump_dialog.exit()
            success = True
        except Exception as e:
            success = False
            
        self.assertTrue(success, "New signature should work with file_operations parameter")


if __name__ == '__main__':
    unittest.main()