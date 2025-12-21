#!/usr/bin/env python3
"""
Test S3 directory rename dialog prevention functionality.

This test verifies that TFM prevents the rename dialog from opening
for S3 directories, providing immediate feedback to users.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_s3 import S3PathImpl


class TestS3DirectoryRenameDialogPrevention(unittest.TestCase):
    """Test S3 directory rename dialog prevention"""
    
    def test_s3_directory_blocks_rename_dialog(self):
        """Test that S3 directories block the rename dialog from opening"""
        # Create a real S3PathImpl for testing
        s3_directory = S3PathImpl('s3://test-bucket/test-directory/')
        s3_directory._s3_client = Mock()
        s3_directory.is_dir = Mock(return_value=True)
        
        # Create a Path object with the S3 implementation
        from tfm_path import Path
        s3_path = Path('s3://test-bucket/test-directory/')
        s3_path._impl = s3_directory
        s3_path.is_dir = Mock(return_value=True)
        s3_path.supports_directory_rename = Mock(return_value=False)
        
        # Mock the FileManager
        from tfm_main import FileManager
        file_manager = Mock(spec=FileManager)
        file_manager.get_current_pane.return_value = {
            'selected_files': [],
            'files': [s3_path],
            'selected_index': 0
        }
        file_manager.quick_edit_bar = Mock()
        file_manager.needs_full_redraw = False
        
        # Mock print to capture the error message
        with patch('builtins.print') as mock_print:
            # Call the actual enter_rename_mode method
            FileManager.enter_rename_mode(file_manager)
            
            # Verify the error message was printed
            mock_print.assert_called_with(
                "Directory renaming is not supported on this storage type due to performance and cost considerations"
            )
        
        # Verify that rename_file_path was not set (dialog not opened)
        self.assertFalse(hasattr(file_manager, 'rename_file_path'))
    
    def test_s3_file_allows_rename_dialog(self):
        """Test that S3 files allow the rename dialog to open"""
        # Create a real S3PathImpl for a file
        s3_file = S3PathImpl('s3://test-bucket/test-file.txt')
        s3_file._s3_client = Mock()
        s3_file.is_dir = Mock(return_value=False)
        
        # Create a Path object with the S3 implementation
        from tfm_path import Path
        s3_path = Path('s3://test-bucket/test-file.txt')
        s3_path._impl = s3_file
        s3_path.is_dir = Mock(return_value=False)
        s3_path.supports_directory_rename = Mock(return_value=False)
        
        # Mock the FileManager
        from tfm_main import FileManager
        file_manager = Mock(spec=FileManager)
        file_manager.get_current_pane.return_value = {
            'selected_files': [],
            'files': [s3_path],
            'selected_index': 0
        }
        file_manager.quick_edit_bar = Mock()
        file_manager.needs_full_redraw = False
        
        # Mock QuickEditBarHelpers to verify dialog creation
        with patch('tfm_main.QuickEditBarHelpers') as mock_dialog_helpers:
            # Call the actual enter_rename_mode method
            FileManager.enter_rename_mode(file_manager)
            
            # Verify dialog was created
            mock_dialog_helpers.create_rename_dialog.assert_called_once()
            
            # Verify rename_file_path was set
            self.assertEqual(file_manager.rename_file_path, s3_path)
    
    def test_local_directory_allows_rename_dialog(self):
        """Test that local directories allow the rename dialog to open"""
        # Create a mock local path (not S3)
        from tfm_path import LocalPathImpl, Path
        local_impl = Mock(spec=LocalPathImpl)
        local_path = Path('/tmp/test-directory')
        local_path._impl = local_impl
        local_path.is_dir = Mock(return_value=True)
        local_path.supports_directory_rename = Mock(return_value=True)
        
        # Mock the FileManager
        from tfm_main import FileManager
        file_manager = Mock(spec=FileManager)
        file_manager.get_current_pane.return_value = {
            'selected_files': [],
            'files': [local_path],
            'selected_index': 0
        }
        file_manager.quick_edit_bar = Mock()
        file_manager.needs_full_redraw = False
        
        # Mock QuickEditBarHelpers to verify dialog creation
        with patch('tfm_main.QuickEditBarHelpers') as mock_dialog_helpers:
            # Call the actual enter_rename_mode method
            FileManager.enter_rename_mode(file_manager)
            
            # Verify dialog was created (local directories can be renamed)
            mock_dialog_helpers.create_rename_dialog.assert_called_once()
            
            # Verify rename_file_path was set
            self.assertEqual(file_manager.rename_file_path, local_path)
    
    def test_error_handling_graceful_fallback(self):
        """Test that errors in S3 checking don't prevent normal operation"""
        # Create a mock path that will cause an error in supports_directory_rename()
        mock_path = Mock()
        mock_path._impl = Mock(spec=S3PathImpl)
        mock_path.is_dir.return_value = True
        mock_path.supports_directory_rename.side_effect = Exception("Test error")
        mock_path.name = "test-file"
        
        # Mock the FileManager
        from tfm_main import FileManager
        file_manager = Mock(spec=FileManager)
        file_manager.get_current_pane.return_value = {
            'selected_files': [],
            'files': [mock_path],
            'selected_index': 0
        }
        file_manager.quick_edit_bar = Mock()
        file_manager.needs_full_redraw = False
        
        # Mock QuickEditBarHelpers and print
        with patch('tfm_main.QuickEditBarHelpers') as mock_dialog_helpers:
            with patch('builtins.print') as mock_print:
                # Call the actual enter_rename_mode method
                FileManager.enter_rename_mode(file_manager)
                
                # Verify warning was printed
                mock_print.assert_any_call("Warning: Could not check directory rename capability: Test error")
                
                # Verify dialog was still created (fallback behavior)
                mock_dialog_helpers.create_rename_dialog.assert_called_once()


def run_test():
    """Run the test"""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_test()