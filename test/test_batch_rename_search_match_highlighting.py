#!/usr/bin/env python3
"""
Tests for BatchRenameDialog search match highlighting feature.

This test suite verifies that the preview entries contain the correct
match_start, match_end, replace_start, and replace_end values for
highlighting matched and replaced portions of filenames using COLOR_SEARCH_MATCH.
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path as TFMPath


class TestBatchRenameSearchMatchHighlighting(unittest.TestCase):
    """Test search match highlighting data in preview entries"""
    
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
    
    def test_match_positions_for_middle_replacement(self):
        """Test match positions when replacing middle portion of filename"""
        files = self.create_test_files(['test_file.txt'])
        self.dialog.show(files)
        
        # Set pattern to match "file" in the middle
        self.dialog.regex_editor.set_text('file')
        self.dialog.destination_editor.set_text('document')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'test_file.txt')
        self.assertEqual(preview['new'], 'test_document.txt')
        self.assertEqual(preview['match_start'], 5)  # Position of "file"
        self.assertEqual(preview['match_end'], 9)    # End of "file"
        self.assertEqual(preview['replace_start'], 5)  # Start of replacement
        self.assertEqual(preview['replace_end'], 13)   # End of "document"
        
    def test_match_positions_for_beginning_replacement(self):
        """Test match positions when replacing at beginning"""
        files = self.create_test_files(['old_name.txt'])
        self.dialog.show(files)
        
        self.dialog.regex_editor.set_text('^old')
        self.dialog.destination_editor.set_text('new')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'old_name.txt')
        self.assertEqual(preview['new'], 'new_name.txt')
        self.assertEqual(preview['match_start'], 0)
        self.assertEqual(preview['match_end'], 3)
        self.assertEqual(preview['replace_start'], 0)
        self.assertEqual(preview['replace_end'], 3)
        
    def test_match_positions_for_end_replacement(self):
        """Test match positions when replacing at end"""
        files = self.create_test_files(['document.txt'])
        self.dialog.show(files)
        
        self.dialog.regex_editor.set_text(r'\.txt$')
        self.dialog.destination_editor.set_text('.md')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'document.txt')
        self.assertEqual(preview['new'], 'document.md')
        self.assertEqual(preview['match_start'], 8)
        self.assertEqual(preview['match_end'], 12)
        self.assertEqual(preview['replace_start'], 8)
        self.assertEqual(preview['replace_end'], 11)
        
    def test_no_match_has_none_positions(self):
        """Test that non-matching files have None for position values"""
        files = self.create_test_files(['nomatch.txt'])
        self.dialog.show(files)
        
        self.dialog.regex_editor.set_text('xyz')
        self.dialog.destination_editor.set_text('abc')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'nomatch.txt')
        self.assertEqual(preview['new'], 'nomatch.txt')
        self.assertIsNone(preview['match_start'])
        self.assertIsNone(preview['match_end'])
        self.assertIsNone(preview['replace_start'])
        self.assertIsNone(preview['replace_end'])
        
    def test_empty_patterns_have_no_positions(self):
        """Test that empty patterns result in no position data"""
        files = self.create_test_files(['file.txt'])
        self.dialog.show(files)
        
        # Empty patterns
        self.dialog.regex_editor.set_text('')
        self.dialog.destination_editor.set_text('')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'file.txt')
        self.assertEqual(preview['new'], 'file.txt')
        # Empty patterns don't set position keys
        self.assertNotIn('match_start', preview)
        self.assertNotIn('match_end', preview)
        
    def test_longer_replacement_positions(self):
        """Test positions when replacement is longer than match"""
        files = self.create_test_files(['a_b_c.txt'])
        self.dialog.show(files)
        
        self.dialog.regex_editor.set_text('_')
        self.dialog.destination_editor.set_text('_long_')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'a_b_c.txt')
        self.assertEqual(preview['new'], 'a_long_b_c.txt')
        self.assertEqual(preview['match_start'], 1)  # First underscore
        self.assertEqual(preview['match_end'], 2)
        self.assertEqual(preview['replace_start'], 1)
        self.assertEqual(preview['replace_end'], 7)  # "_long_" is 6 chars
        
    def test_shorter_replacement_positions(self):
        """Test positions when replacement is shorter than match"""
        files = self.create_test_files(['test_long_name.txt'])
        self.dialog.show(files)
        
        self.dialog.regex_editor.set_text('long')
        self.dialog.destination_editor.set_text('x')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'test_long_name.txt')
        self.assertEqual(preview['new'], 'test_x_name.txt')
        self.assertEqual(preview['match_start'], 5)
        self.assertEqual(preview['match_end'], 9)
        self.assertEqual(preview['replace_start'], 5)
        self.assertEqual(preview['replace_end'], 6)
        
    def test_positions_with_regex_groups(self):
        """Test positions when using regex groups in replacement"""
        files = self.create_test_files(['file_123.txt'])
        self.dialog.show(files)
        
        self.dialog.regex_editor.set_text(r'(\d+)')
        self.dialog.destination_editor.set_text(r'num_\1')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'file_123.txt')
        self.assertEqual(preview['new'], 'file_num_123.txt')
        self.assertEqual(preview['match_start'], 5)  # Position of "123"
        self.assertEqual(preview['match_end'], 8)
        self.assertEqual(preview['replace_start'], 5)
        self.assertEqual(preview['replace_end'], 12)  # "num_123" is 7 chars, ends at position 12
        
    def test_positions_with_index_macro(self):
        """Test positions when using \\d index macro"""
        files = self.create_test_files(['file1.txt', 'file2.txt'])
        self.dialog.show(files)
        
        self.dialog.regex_editor.set_text(r'\d')
        self.dialog.destination_editor.set_text(r'\d')
        self.dialog.update_preview()
        
        # First file
        preview1 = self.dialog.preview[0]
        self.assertEqual(preview1['original'], 'file1.txt')
        self.assertEqual(preview1['new'], 'file1.txt')  # "1" replaced with "1"
        self.assertEqual(preview1['match_start'], 4)
        self.assertEqual(preview1['match_end'], 5)
        self.assertEqual(preview1['replace_start'], 4)
        self.assertEqual(preview1['replace_end'], 5)
        
        # Second file
        preview2 = self.dialog.preview[1]
        self.assertEqual(preview2['original'], 'file2.txt')
        self.assertEqual(preview2['new'], 'file2.txt')  # "2" replaced with "2"
        self.assertEqual(preview2['match_start'], 4)
        self.assertEqual(preview2['match_end'], 5)
        self.assertEqual(preview2['replace_start'], 4)
        self.assertEqual(preview2['replace_end'], 5)
        
    def test_positions_with_full_filename_replacement(self):
        """Test positions when replacing entire filename with .*"""
        files = self.create_test_files(['oldname.txt'])
        self.dialog.show(files)
        
        self.dialog.regex_editor.set_text('.*')
        self.dialog.destination_editor.set_text('newname.txt')
        self.dialog.update_preview()
        
        preview = self.dialog.preview[0]
        self.assertEqual(preview['original'], 'oldname.txt')
        self.assertEqual(preview['new'], 'newname.txt')
        self.assertEqual(preview['match_start'], 0)
        self.assertEqual(preview['match_end'], 11)  # Entire filename
        self.assertEqual(preview['replace_start'], 0)
        self.assertEqual(preview['replace_end'], 11)  # New filename length
        
    def test_multiple_files_have_correct_positions(self):
        """Test that each file in batch has correct position data"""
        files = self.create_test_files(['test1.txt', 'test2.txt', 'other.txt'])
        self.dialog.show(files)
        
        self.dialog.regex_editor.set_text('test')
        self.dialog.destination_editor.set_text('file')
        self.dialog.update_preview()
        
        # First two files match
        for i in range(2):
            preview = self.dialog.preview[i]
            self.assertEqual(preview['match_start'], 0)
            self.assertEqual(preview['match_end'], 4)
            self.assertEqual(preview['replace_start'], 0)
            self.assertEqual(preview['replace_end'], 4)
        
        # Third file doesn't match
        preview = self.dialog.preview[2]
        self.assertIsNone(preview['match_start'])
        self.assertIsNone(preview['match_end'])
        self.assertIsNone(preview['replace_start'])
        self.assertIsNone(preview['replace_end'])


if __name__ == '__main__':
    unittest.main()
