#!/usr/bin/env python3
"""
Tests for archive extraction confirmation message shortening
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from tfm_archive_operation_ui import ArchiveOperationUI
from tfm_string_width import ShorteningRegion


class TestArchiveExtractionConfirmationShortening(unittest.TestCase):
    """Test archive extraction confirmation message shortening"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock file manager
        self.mock_file_manager = Mock()
        self.mock_file_manager.config = Mock()
        
        # Create ArchiveOperationUI instance
        self.archive_ui = ArchiveOperationUI(self.mock_file_manager)
    
    def test_extraction_confirmation_message_structure(self):
        """Test that extraction confirmation message has correct structure"""
        archive_path = Path("/source/archive.tar.gz")
        destination_path = Path("/destination/folder")
        callback = Mock()
        
        # Call show_confirmation_dialog
        self.archive_ui.show_confirmation_dialog(
            'extract',
            [archive_path],
            destination_path,
            callback
        )
        
        # Verify show_confirmation was called
        self.mock_file_manager.show_confirmation.assert_called_once()
        
        # Extract the arguments
        call_args = self.mock_file_manager.show_confirmation.call_args
        message = call_args[0][0]
        callback_arg = call_args[0][1]
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Verify message structure
        expected_message = f"Extract '{archive_path.name}' to {destination_path}?"
        self.assertEqual(message, expected_message)
        
        # Verify callback is passed through
        self.assertEqual(callback_arg, callback)
        
        # Verify shortening regions are provided
        self.assertIsNotNone(shortening_regions)
        self.assertEqual(len(shortening_regions), 2)
    
    def test_extraction_confirmation_archive_name_region(self):
        """Test that archive name region uses all_or_nothing strategy"""
        archive_path = Path("/source/my_archive.tar.gz")
        destination_path = Path("/destination/folder")
        callback = Mock()
        
        # Call show_confirmation_dialog
        self.archive_ui.show_confirmation_dialog(
            'extract',
            [archive_path],
            destination_path,
            callback
        )
        
        # Extract shortening regions
        call_args = self.mock_file_manager.show_confirmation.call_args
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Find the archive name region (higher priority)
        archive_region = next(r for r in shortening_regions if r.priority == 1)
        
        # Verify it uses all_or_nothing strategy
        self.assertEqual(archive_region.strategy, 'all_or_nothing')
        
        # Verify it covers "'my_archive.tar.gz' " (including quotes and trailing space)
        message = call_args[0][0]
        archive_part = message[archive_region.start:archive_region.end]
        self.assertEqual(archive_part, f"'{archive_path.name}' ")
    
    def test_extraction_confirmation_destination_region(self):
        """Test that destination region uses abbreviation with filepath mode"""
        archive_path = Path("/source/archive.tar.gz")
        destination_path = Path("/very/long/destination/path/folder")
        callback = Mock()
        
        # Call show_confirmation_dialog
        self.archive_ui.show_confirmation_dialog(
            'extract',
            [archive_path],
            destination_path,
            callback
        )
        
        # Extract shortening regions
        call_args = self.mock_file_manager.show_confirmation.call_args
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Find the destination region (lower priority)
        destination_region = next(r for r in shortening_regions if r.priority == 0)
        
        # Verify it uses abbreviation strategy with filepath mode
        self.assertEqual(destination_region.strategy, 'abbreviate')
        self.assertEqual(destination_region.abbrev_position, 'middle')
        self.assertTrue(destination_region.filepath_mode)
        
        # Verify it covers the destination path
        message = call_args[0][0]
        destination_part = message[destination_region.start:destination_region.end]
        self.assertEqual(destination_part, str(destination_path))
    
    def test_extraction_confirmation_priority_order(self):
        """Test that archive name has higher priority than destination"""
        archive_path = Path("/source/archive.tar.gz")
        destination_path = Path("/destination/folder")
        callback = Mock()
        
        # Call show_confirmation_dialog
        self.archive_ui.show_confirmation_dialog(
            'extract',
            [archive_path],
            destination_path,
            callback
        )
        
        # Extract shortening regions
        call_args = self.mock_file_manager.show_confirmation.call_args
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Verify priority order (higher priority = shortened first)
        archive_region = next(r for r in shortening_regions if r.strategy == 'all_or_nothing')
        destination_region = next(r for r in shortening_regions if r.filepath_mode)
        
        self.assertGreater(archive_region.priority, destination_region.priority,
                          "Archive name should have higher priority (shortened first)")
    
    def test_create_confirmation_no_shortening_regions(self):
        """Test that create operations don't use shortening regions"""
        source_path = Path("/source/file.txt")
        destination_path = Path("/destination/archive.tar.gz")
        callback = Mock()
        
        # Call show_confirmation_dialog for create operation
        self.archive_ui.show_confirmation_dialog(
            'create',
            [source_path],
            destination_path,
            callback
        )
        
        # Extract shortening regions
        call_args = self.mock_file_manager.show_confirmation.call_args
        shortening_regions = call_args[1].get('shortening_regions')
        
        # Verify no shortening regions for create operations
        self.assertIsNone(shortening_regions)


if __name__ == '__main__':
    unittest.main()
