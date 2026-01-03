#!/usr/bin/env python3
"""
Tests for archive conflict dialog message shortening
"""

import unittest
from unittest.mock import Mock, MagicMock
from pathlib import Path

from tfm_archive_operation_ui import ArchiveOperationUI
from tfm_string_width import ShorteningRegion


class TestArchiveConflictDialogShortening(unittest.TestCase):
    """Test archive conflict dialog message shortening"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock file manager
        self.mock_file_manager = Mock()
        self.mock_file_manager.config = Mock()
        
        # Create ArchiveOperationUI instance
        self.archive_ui = ArchiveOperationUI(self.mock_file_manager)
    
    def test_archive_exists_conflict_message_structure(self):
        """Test that archive exists conflict message has correct structure"""
        conflict_info = {
            'path': Path("/destination/archive.tar.gz"),
            'display_name': 'archive.tar.gz',
            'size': 1024000
        }
        callback = Mock()
        
        # Call show_conflict_dialog
        self.archive_ui.show_conflict_dialog(
            'archive_exists',
            conflict_info,
            1,
            1,
            callback
        )
        
        # Verify show_dialog was called
        self.mock_file_manager.show_dialog.assert_called_once()
        
        # Extract the arguments
        call_args = self.mock_file_manager.show_dialog.call_args
        message = call_args[0][0]
        choices = call_args[0][1]
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Verify message starts with "Archive exists: "
        self.assertTrue(message.startswith("Archive exists: "))
        
        # Verify shortening regions are provided
        self.assertIsNotNone(shortening_regions)
        self.assertEqual(len(shortening_regions), 1)
    
    def test_archive_exists_filename_region(self):
        """Test that archive exists uses abbreviation strategy with filepath mode"""
        conflict_info = {
            'path': Path("/destination/very_long_archive_name.tar.gz"),
            'display_name': 'very_long_archive_name.tar.gz',
            'size': 1024000
        }
        callback = Mock()
        
        # Call show_conflict_dialog
        self.archive_ui.show_conflict_dialog(
            'archive_exists',
            conflict_info,
            1,
            1,
            callback
        )
        
        # Extract shortening regions
        call_args = self.mock_file_manager.show_dialog.call_args
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Verify it uses abbreviation strategy with middle position and filepath mode
        region = shortening_regions[0]
        self.assertEqual(region.strategy, 'abbreviate')
        self.assertEqual(region.abbrev_position, 'middle')
        self.assertTrue(region.filepath_mode)
        
        # Verify it covers the filename
        message = call_args[0][0]
        filename_part = message[region.start:region.end]
        self.assertEqual(filename_part, conflict_info['display_name'])
    
    def test_file_exists_conflict_message_structure(self):
        """Test that file exists conflict message has correct structure"""
        conflict_info = {
            'path': Path("/destination/document.txt"),
            'display_name': 'document.txt',
            'size': 2048,
            'is_directory': False
        }
        callback = Mock()
        
        # Call show_conflict_dialog
        self.archive_ui.show_conflict_dialog(
            'file_exists',
            conflict_info,
            1,
            3,
            callback
        )
        
        # Verify show_dialog was called
        self.mock_file_manager.show_dialog.assert_called_once()
        
        # Extract the arguments
        call_args = self.mock_file_manager.show_dialog.call_args
        message = call_args[0][0]
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Verify message starts with "File exists: "
        self.assertTrue(message.startswith("File exists: "))
        
        # Verify shortening regions are provided
        self.assertIsNotNone(shortening_regions)
        self.assertEqual(len(shortening_regions), 1)
    
    def test_file_exists_filename_region(self):
        """Test that file exists uses abbreviation strategy with filepath mode"""
        conflict_info = {
            'path': Path("/destination/very_long_filename_with_many_characters.txt"),
            'display_name': 'very_long_filename_with_many_characters.txt',
            'size': 2048,
            'is_directory': False
        }
        callback = Mock()
        
        # Call show_conflict_dialog
        self.archive_ui.show_conflict_dialog(
            'file_exists',
            conflict_info,
            2,
            5,
            callback
        )
        
        # Extract shortening regions
        call_args = self.mock_file_manager.show_dialog.call_args
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Verify it uses abbreviation strategy with middle position and filepath mode
        region = shortening_regions[0]
        self.assertEqual(region.strategy, 'abbreviate')
        self.assertEqual(region.abbrev_position, 'middle')
        self.assertTrue(region.filepath_mode)
        
        # Verify it covers the filename
        message = call_args[0][0]
        filename_part = message[region.start:region.end]
        self.assertEqual(filename_part, conflict_info['display_name'])
    
    def test_directory_exists_conflict_message_structure(self):
        """Test that directory exists conflict message has correct structure"""
        conflict_info = {
            'path': Path("/destination/my_folder"),
            'display_name': 'my_folder',
            'is_directory': True
        }
        callback = Mock()
        
        # Call show_conflict_dialog
        self.archive_ui.show_conflict_dialog(
            'file_exists',
            conflict_info,
            1,
            1,
            callback
        )
        
        # Extract the arguments
        call_args = self.mock_file_manager.show_dialog.call_args
        message = call_args[0][0]
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Verify message starts with "Directory exists: "
        self.assertTrue(message.startswith("Directory exists: "))
        
        # Verify shortening regions are provided
        self.assertIsNotNone(shortening_regions)
        self.assertEqual(len(shortening_regions), 1)
    
    def test_directory_exists_filename_region(self):
        """Test that directory exists uses abbreviation strategy with filepath mode"""
        conflict_info = {
            'path': Path("/destination/very_long_directory_name_with_many_characters"),
            'display_name': 'very_long_directory_name_with_many_characters',
            'is_directory': True
        }
        callback = Mock()
        
        # Call show_conflict_dialog
        self.archive_ui.show_conflict_dialog(
            'file_exists',
            conflict_info,
            1,
            1,
            callback
        )
        
        # Extract shortening regions
        call_args = self.mock_file_manager.show_dialog.call_args
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Verify it uses abbreviation strategy with middle position and filepath mode
        region = shortening_regions[0]
        self.assertEqual(region.strategy, 'abbreviate')
        self.assertEqual(region.abbrev_position, 'middle')
        self.assertTrue(region.filepath_mode)
        
        # Verify it covers the directory name
        message = call_args[0][0]
        dirname_part = message[region.start:region.end]
        self.assertEqual(dirname_part, conflict_info['display_name'])
    
    def test_conflict_with_size_and_counter(self):
        """Test that size and counter don't interfere with filename region"""
        conflict_info = {
            'path': Path("/destination/file.txt"),
            'display_name': 'file.txt',
            'size': 1024,
            'is_directory': False
        }
        callback = Mock()
        
        # Call show_conflict_dialog with counter
        self.archive_ui.show_conflict_dialog(
            'file_exists',
            conflict_info,
            3,
            10,
            callback
        )
        
        # Extract shortening regions
        call_args = self.mock_file_manager.show_dialog.call_args
        message = call_args[0][0]
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Verify message contains size and counter
        self.assertIn("(", message)  # Size or counter in parentheses
        
        # Verify filename region only covers the filename, not size or counter
        region = shortening_regions[0]
        filename_part = message[region.start:region.end]
        self.assertEqual(filename_part, 'file.txt')
        self.assertNotIn("(", filename_part)  # No parentheses in filename region


if __name__ == '__main__':
    unittest.main()
