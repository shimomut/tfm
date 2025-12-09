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
    
    def test_capability_detection(self):
        """Test that storage capabilities are correctly detected"""
        # Archive paths should not support file editing
        archive_path = Path('archive:///path/to/file.zip#')
        self.assertFalse(archive_path.supports_file_editing())
        
        archive_path2 = Path('archive:///path/to/file.tar.gz#internal/path')
        self.assertFalse(archive_path2.supports_file_editing())
        
        # Local paths should support file editing
        local_path = Path('/path/to/file.txt')
        self.assertTrue(local_path.supports_file_editing())
    
    def test_validate_delete_from_read_only_storage(self):
        """Test that deleting from read-only storage is rejected"""
        archive_path = Path('archive:///path/to/file.zip#internal/file.txt')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'delete', [archive_path]
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Cannot delete files from read-only storage", error_msg)
    
    def test_validate_delete_from_writable_storage(self):
        """Test that deleting from writable storage is allowed"""
        local_path = Path('/path/to/file.txt')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'delete', [local_path]
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_move_from_read_only_storage(self):
        """Test that moving from read-only storage is rejected"""
        archive_path = Path('archive:///path/to/file.zip#internal/file.txt')
        dest_path = Path('/destination/dir')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'move', [archive_path], dest_path
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Cannot move files from read-only storage", error_msg)
        self.assertIn("Use copy instead", error_msg)
    
    def test_validate_move_to_read_only_storage(self):
        """Test that moving to read-only storage is rejected"""
        local_path = Path('/path/to/file.txt')
        archive_dest = Path('archive:///path/to/file.zip#')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'move', [local_path], archive_dest
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Cannot move files to read-only storage", error_msg)
    
    def test_validate_move_between_writable_storage(self):
        """Test that moving between writable storage locations is allowed"""
        source_path = Path('/path/to/file.txt')
        dest_path = Path('/destination/dir')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'move', [source_path], dest_path
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_copy_to_read_only_storage(self):
        """Test that copying to read-only storage is rejected"""
        local_path = Path('/path/to/file.txt')
        archive_dest = Path('archive:///path/to/file.zip#')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'copy', [local_path], archive_dest
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Cannot copy files to read-only storage", error_msg)
    
    def test_validate_copy_from_read_only_storage(self):
        """Test that copying from read-only storage is allowed (extraction)"""
        archive_path = Path('archive:///path/to/file.zip#internal/file.txt')
        dest_path = Path('/destination/dir')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'copy', [archive_path], dest_path
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_copy_between_writable_storage(self):
        """Test that copying between writable storage locations is allowed"""
        source_path = Path('/path/to/file.txt')
        dest_path = Path('/destination/dir')
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'copy', [source_path], dest_path
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_delete_shows_error_for_read_only_storage(self):
        """Test that delete operation shows error for read-only storage"""
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
        self.assertIn("Cannot delete files from read-only storage", message)
        
        # Verify only OK choice is available
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]['text'], 'OK')
    
    def test_move_shows_error_for_read_only_source(self):
        """Test that move operation shows error for read-only source storage"""
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
        self.assertIn("Cannot move files from read-only storage", message)
        self.assertIn("Use copy instead", message)
    
    def test_move_shows_error_for_read_only_destination(self):
        """Test that move operation shows error for read-only destination storage"""
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
            self.assertIn("Cannot move files to read-only storage", message)
    
    def test_copy_shows_error_for_read_only_destination(self):
        """Test that copy operation shows error for read-only destination storage"""
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
            self.assertIn("Cannot copy files to read-only storage", message)


if __name__ == '__main__':
    unittest.main()
