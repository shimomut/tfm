"""
Test FileManager S3 file editing restriction

Run with: PYTHONPATH=.:src:ttk pytest test/test_filemanager_s3_edit_restriction.py -v
"""

import unittest
from unittest.mock import Mock, patch


class TestFileManagerS3EditRestriction(unittest.TestCase):
    """Test that FileManager shows error when trying to edit S3 files"""
    
    def test_edit_s3_file_shows_error_message(self):
        """Test that editing S3 file shows error message"""
        # Import here to avoid initialization issues
        from tfm_main import FileManager
        
        # Create a minimal FileManager instance for testing
        file_manager = Mock(spec=FileManager)
        
        # Mock S3 file that doesn't support editing
        mock_s3_file = Mock()
        mock_s3_file.supports_file_editing.return_value = False
        mock_s3_file.name = 'test-file.txt'
        mock_s3_file.is_dir.return_value = False
        
        # Mock the get_current_pane method
        mock_pane = {
            'files': [mock_s3_file],
            'selected_index': 0,
            'path': Mock()
        }
        file_manager.get_current_pane.return_value = mock_pane
        
        # Mock config
        mock_config = Mock()
        mock_config.TEXT_EDITOR = 'nano'
        file_manager.config = mock_config
        
        # Import the actual method and bind it to our mock
        from tfm_main import FileManager
        actual_method = FileManager.edit_selected_file
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            # Call the actual method with our mock instance
            actual_method(file_manager)
            
            # Verify error message was printed
            mock_print.assert_called_with("Editing S3 files is not supported for now")
            
            # Verify supports_file_editing was called
            mock_s3_file.supports_file_editing.assert_called_once()
    
    def test_edit_local_file_works_normally(self):
        """Test that editing local file works normally"""
        # Import here to avoid initialization issues
        from tfm_main import FileManager
        
        # Create a minimal FileManager instance for testing
        file_manager = Mock(spec=FileManager)
        
        # Mock local file that supports editing
        mock_local_file = Mock()
        mock_local_file.supports_file_editing.return_value = True
        mock_local_file.name = 'test-file.txt'
        mock_local_file.is_dir.return_value = False
        mock_local_file.__str__ = Mock(return_value='/path/to/test-file.txt')
        
        # Mock the get_current_pane method
        mock_path = Mock()
        mock_path.__str__ = Mock(return_value='/path/to')
        mock_pane = {
            'files': [mock_local_file],
            'selected_index': 0,
            'path': mock_path
        }
        file_manager.get_current_pane.return_value = mock_pane
        
        # Mock config and external program manager
        mock_config = Mock()
        mock_config.TEXT_EDITOR = 'nano'
        file_manager.config = mock_config
        file_manager.external_program_manager = Mock()
        file_manager.stdscr = Mock()
        
        # Import the actual method
        actual_method = FileManager.edit_selected_file
        
        # Mock subprocess.run to simulate successful editor launch
        with patch('tfm_main.subprocess.run') as mock_run, \
             patch('builtins.print') as mock_print:
            
            mock_run.return_value.returncode = 0
            
            # Call the actual method with our mock instance
            actual_method(file_manager)
            
            # Verify editor was launched
            mock_run.assert_called_once_with(['nano', '/path/to/test-file.txt'], cwd='/path/to')
            
            # Verify success message was printed
            mock_print.assert_called_with("Edited file: test-file.txt")
            
            # Verify supports_file_editing was called
            mock_local_file.supports_file_editing.assert_called_once()
