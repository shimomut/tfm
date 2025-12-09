#!/usr/bin/env python3
"""
Test unsupported operations on archive paths
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path as PathlibPath
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_file_operations import FileOperationsUI


class TestArchiveUnsupportedOperations(unittest.TestCase):
    """Test that unsupported operations on archives show error messages"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock file manager
        self.mock_file_manager = Mock()
        self.mock_file_manager.log_manager = Mock()
        self.mock_file_manager.progress_manager = Mock()
        self.mock_file_manager.cache_manager = Mock()
        self.mock_file_manager.config = Mock()
        self.mock_file_manager.config.CONFIRM_COPY = False
        self.mock_file_manager.config.CONFIRM_DELETE = False
        
        # Create mock file operations
        self.mock_file_operations = Mock()
        
        # Create FileOperationsUI instance
        self.file_ops_ui = FileOperationsUI(self.mock_file_manager, self.mock_file_operations)
    
    def test_is_archive_path_detection(self):
        """Test that archive paths are correctly detected"""
        # Archive paths should be detected
        self.assertTrue(self.file_ops_ui._is_archive_path(Path('archive:///path/to/file.zip#')))
        self.assertTrue(self.file_ops_ui._is_archive_path(Path('archive:///path/to/file.tar.gz#internal/path')))
        
        # Non-archive paths should not be detected
        self.assertFalse(self.file_ops_ui._is_archive_path(Path('/path/to/file.txt')))
        self.assertFalse(self.file_ops_ui._is_archive_path(Path('s3://bucket/key')))
    
    def test_validate_delete_from_archive(self):
        """Test that deleting from archive is rejected"""
        archive_path = Path('archive:///path/to/file.zip#internal/file.txt')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_on_archives(
            'delete', [archive_path]
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Cannot delete files within archives", error_msg)
        self.assertIn("read-only", error_msg)
    
    def test_validate_delete_from_filesystem(self):
        """Test that deleting from filesystem is allowed"""
        local_path = Path('/path/to/file.txt')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_on_archives(
            'delete', [local_path]
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_move_from_archive(self):
        """Test that moving from archive is rejected"""
        archive_path = Path('archive:///path/to/file.zip#internal/file.txt')
        dest_path = Path('/destination/dir')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_on_archives(
            'move', [archive_path], dest_path
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Cannot move files from archives", error_msg)
        self.assertIn("Use copy instead", error_msg)
        self.assertIn("read-only", error_msg)
    
    def test_validate_move_to_archive(self):
        """Test that moving to archive is rejected"""
        local_path = Path('/path/to/file.txt')
        archive_dest = Path('archive:///path/to/file.zip#')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_on_archives(
            'move', [local_path], archive_dest
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Cannot move files into archives", error_msg)
        self.assertIn("read-only", error_msg)
    
    def test_validate_move_filesystem_to_filesystem(self):
        """Test that moving between filesystem locations is allowed"""
        source_path = Path('/path/to/file.txt')
        dest_path = Path('/destination/dir')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_on_archives(
            'move', [source_path], dest_path
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_copy_to_archive(self):
        """Test that copying to archive is rejected"""
        local_path = Path('/path/to/file.txt')
        archive_dest = Path('archive:///path/to/file.zip#')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_on_archives(
            'copy', [local_path], archive_dest
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Cannot copy files into archives", error_msg)
        self.assertIn("read-only", error_msg)
    
    def test_validate_copy_from_archive(self):
        """Test that copying from archive is allowed (extraction)"""
        archive_path = Path('archive:///path/to/file.zip#internal/file.txt')
        dest_path = Path('/destination/dir')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_on_archives(
            'copy', [archive_path], dest_path
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_copy_filesystem_to_filesystem(self):
        """Test that copying between filesystem locations is allowed"""
        source_path = Path('/path/to/file.txt')
        dest_path = Path('/destination/dir')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_on_archives(
            'copy', [source_path], dest_path
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_delete_shows_error_for_archive_path(self):
        """Test that delete operation shows error for archive paths"""
        # Set up mock pane with archive file
        archive_path = Path('archive:///path/to/file.zip#internal/file.txt')
        
        self.mock_file_manager.get_current_pane.return_value = {
            'selected_files': set(),
            'files': [archive_path],
            'selected_index': 0
        }
        
        # Mock show_dialog to capture the error message
        dialog_calls = []
        def capture_dialog(message, choices, callback):
            dialog_calls.append((message, choices))
        
        self.mock_file_manager.show_dialog = capture_dialog
        
        # Call delete_selected_files
        self.file_ops_ui.delete_selected_files()
        
        # Verify error dialog was shown
        self.assertEqual(len(dialog_calls), 1)
        message, choices = dialog_calls[0]
        self.assertIn("Cannot delete files within archives", message)
        self.assertIn("read-only", message)
        
        # Verify only OK choice is available
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]['text'], 'OK')
    
    def test_move_shows_error_for_archive_source(self):
        """Test that move operation shows error for archive source paths"""
        # Set up mock panes
        archive_path = Path('archive:///path/to/file.zip#internal/file.txt')
        dest_path = Path('/destination/dir')
        
        self.mock_file_manager.get_current_pane.return_value = {
            'selected_files': set(),
            'files': [archive_path],
            'selected_index': 0
        }
        
        self.mock_file_manager.get_inactive_pane.return_value = {
            'path': dest_path
        }
        
        # Mock show_dialog to capture the error message
        dialog_calls = []
        def capture_dialog(message, choices, callback):
            dialog_calls.append((message, choices))
        
        self.mock_file_manager.show_dialog = capture_dialog
        
        # Call move_selected_files
        self.file_ops_ui.move_selected_files()
        
        # Verify error dialog was shown
        self.assertEqual(len(dialog_calls), 1)
        message, choices = dialog_calls[0]
        self.assertIn("Cannot move files from archives", message)
        self.assertIn("Use copy instead", message)
        self.assertIn("read-only", message)
    
    def test_move_shows_error_for_archive_destination(self):
        """Test that move operation shows error for archive destination paths"""
        # Set up mock panes
        local_path = Path('/path/to/file.txt')
        archive_dest = Path('archive:///path/to/file.zip#')
        
        # Mock exists to return True
        with patch.object(Path, 'exists', return_value=True):
            self.mock_file_manager.get_current_pane.return_value = {
                'selected_files': {str(local_path)},
                'files': [local_path],
                'selected_index': 0
            }
            
            self.mock_file_manager.get_inactive_pane.return_value = {
                'path': archive_dest
            }
            
            # Mock show_dialog to capture the error message
            dialog_calls = []
            def capture_dialog(message, choices, callback):
                dialog_calls.append((message, choices))
            
            self.mock_file_manager.show_dialog = capture_dialog
            
            # Call move_selected_files
            self.file_ops_ui.move_selected_files()
            
            # Verify error dialog was shown
            self.assertEqual(len(dialog_calls), 1)
            message, choices = dialog_calls[0]
            self.assertIn("Cannot move files into archives", message)
            self.assertIn("read-only", message)
    
    def test_copy_shows_error_for_archive_destination(self):
        """Test that copy operation shows error for archive destination paths"""
        # Set up mock panes
        local_path = Path('/path/to/file.txt')
        archive_dest = Path('archive:///path/to/file.zip#')
        
        # Mock exists to return True
        with patch.object(Path, 'exists', return_value=True):
            self.mock_file_manager.get_current_pane.return_value = {
                'selected_files': {str(local_path)},
                'files': [local_path],
                'selected_index': 0
            }
            
            self.mock_file_manager.get_inactive_pane.return_value = {
                'path': archive_dest
            }
            
            # Mock show_dialog to capture the error message
            dialog_calls = []
            def capture_dialog(message, choices, callback):
                dialog_calls.append((message, choices))
            
            self.mock_file_manager.show_dialog = capture_dialog
            
            # Call copy_selected_files
            self.file_ops_ui.copy_selected_files()
            
            # Verify error dialog was shown
            self.assertEqual(len(dialog_calls), 1)
            message, choices = dialog_calls[0]
            self.assertIn("Cannot copy files into archives", message)
            self.assertIn("read-only", message)


if __name__ == '__main__':
    unittest.main()
