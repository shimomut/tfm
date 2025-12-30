#!/usr/bin/env python3
"""
Tests for BatchRenameDialog with empty destination pattern.

This test suite verifies that empty destination pattern correctly
deletes the matched portion of filenames.
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path as TFMPath


class TestBatchRenameEmptyDestination(unittest.TestCase):
    """Test batch rename with empty destination pattern"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.dialog = BatchRenameDialog(config={})
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_files(self, filenames):
        """Create test files and return list of Path objects"""
        files = []
        for filename in filenames:
            file_path = Path(self.temp_dir) / filename
            file_path.touch()
            files.append(TFMPath(str(file_path)))
        return files
    
    def test_empty_destination_deletes_matched_portion(self):
        """Test that empty destination deletes the matched text"""
        files = self.create_test_files(['test_file.txt'])
        self.dialog.show(files)
        
        # Match "test_" and replace with empty string
        self.dialog.regex_editor.set_text('test_')
        self.dialog.destination_editor.set_text('')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'test_file.txt')
        self.assertEqual(preview['new'], 'file.txt')
        self.assertTrue(preview['valid'])
        self.assertFalse(preview['conflict'])
        
    def test_empty_destination_deletes_extension(self):
        """Test deleting file extension with empty destination"""
        files = self.create_test_files(['document.txt'])
        self.dialog.show(files)
        
        # Match ".txt" and replace with empty string
        self.dialog.regex_editor.set_text(r'\.txt$')
        self.dialog.destination_editor.set_text('')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'document.txt')
        self.assertEqual(preview['new'], 'document')
        self.assertTrue(preview['valid'])
        
    def test_empty_destination_deletes_middle_portion(self):
        """Test deleting middle portion with empty destination"""
        files = self.create_test_files(['file_old_name.txt'])
        self.dialog.show(files)
        
        # Match "_old" and replace with empty string
        self.dialog.regex_editor.set_text('_old')
        self.dialog.destination_editor.set_text('')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'file_old_name.txt')
        self.assertEqual(preview['new'], 'file_name.txt')
        self.assertTrue(preview['valid'])
        
    def test_empty_destination_with_multiple_files(self):
        """Test empty destination works with multiple files"""
        files = self.create_test_files(['test1.txt', 'test2.txt', 'test3.txt'])
        self.dialog.show(files)
        
        # Match "test" and replace with empty string
        self.dialog.regex_editor.set_text('test')
        self.dialog.destination_editor.set_text('')
        self.dialog.update_preview()
        
        for i, preview in enumerate(self.dialog.preview):
            self.assertEqual(preview['original'], f'test{i+1}.txt')
            self.assertEqual(preview['new'], f'{i+1}.txt')
            self.assertTrue(preview['valid'])
            
    def test_empty_destination_with_regex_groups_ignored(self):
        """Test that regex groups in empty destination are ignored"""
        files = self.create_test_files(['file_123.txt'])
        self.dialog.show(files)
        
        # Match digits - empty destination means delete them
        self.dialog.regex_editor.set_text(r'_(\d+)')
        self.dialog.destination_editor.set_text('')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'file_123.txt')
        self.assertEqual(preview['new'], 'file.txt')
        self.assertTrue(preview['valid'])
        
    def test_empty_destination_creates_invalid_name(self):
        """Test that empty destination can create invalid names"""
        files = self.create_test_files(['test.txt'])
        self.dialog.show(files)
        
        # Match entire filename - results in empty name (invalid)
        self.dialog.regex_editor.set_text('.*')
        self.dialog.destination_editor.set_text('')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'test.txt')
        self.assertEqual(preview['new'], '')
        self.assertFalse(preview['valid'])
        
    def test_empty_destination_with_no_match(self):
        """Test empty destination with files that don't match"""
        files = self.create_test_files(['file.txt'])
        self.dialog.show(files)
        
        # Pattern doesn't match
        self.dialog.regex_editor.set_text('xyz')
        self.dialog.destination_editor.set_text('')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'file.txt')
        self.assertEqual(preview['new'], 'file.txt')  # Unchanged
        self.assertTrue(preview['valid'])
        
    def test_empty_destination_highlighting_positions(self):
        """Test that highlighting positions are correct with empty destination"""
        files = self.create_test_files(['test_file.txt'])
        self.dialog.show(files)
        
        # Match "test_" and replace with empty string
        self.dialog.regex_editor.set_text('test_')
        self.dialog.destination_editor.set_text('')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['match_start'], 0)
        self.assertEqual(preview['match_end'], 5)
        self.assertEqual(preview['replace_start'], 0)
        self.assertEqual(preview['replace_end'], 0)  # Empty replacement
        
    def test_perform_rename_with_empty_destination(self):
        """Test that actual rename works with empty destination"""
        files = self.create_test_files(['old_file.txt'])
        self.dialog.show(files)
        
        # Match "old_" and replace with empty string
        self.dialog.regex_editor.set_text('old_')
        self.dialog.destination_editor.set_text('')
        self.dialog.update_preview()
        
        # Perform the rename
        success_count, errors = self.dialog.perform_rename()
        
        self.assertEqual(success_count, 1)
        self.assertEqual(len(errors), 0)
        
        # Verify file was renamed
        new_path = Path(self.temp_dir) / 'file.txt'
        old_path = Path(self.temp_dir) / 'old_file.txt'
        self.assertTrue(new_path.exists())
        self.assertFalse(old_path.exists())


if __name__ == '__main__':
    unittest.main()
