#!/usr/bin/env python3
"""
Test that BatchRenameDialog replaces only the matched portion of filenames
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path as TFMPath


class TestBatchRenamePartialReplacement:
    """Test partial filename replacement behavior"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.dialog = BatchRenameDialog(self.config)
    
    def test_replace_middle_portion(self, tmp_path):
        """Test replacing a portion in the middle of filename"""
        # Create test file
        file_path = tmp_path / "prefix_middle_suffix.txt"
        file_path.write_text("content")
        files = [TFMPath(str(file_path))]
        
        self.dialog.show(files)
        
        # Match only "middle" and replace it
        self.dialog.regex_editor.set_text("middle")
        self.dialog.destination_editor.set_text("REPLACED")
        self.dialog.update_preview()
        
        # Should keep prefix and suffix intact
        assert self.dialog.preview[0]['new'] == "prefix_REPLACED_suffix.txt"
    
    def test_replace_beginning(self, tmp_path):
        """Test replacing the beginning of filename"""
        # Create test file
        file_path = tmp_path / "old_name.txt"
        file_path.write_text("content")
        files = [TFMPath(str(file_path))]
        
        self.dialog.show(files)
        
        # Match "old" at the beginning
        self.dialog.regex_editor.set_text("^old")
        self.dialog.destination_editor.set_text("new")
        self.dialog.update_preview()
        
        # Should keep the rest intact
        assert self.dialog.preview[0]['new'] == "new_name.txt"
    
    def test_replace_end_before_extension(self, tmp_path):
        """Test replacing the end of filename before extension"""
        # Create test file
        file_path = tmp_path / "document_draft.txt"
        file_path.write_text("content")
        files = [TFMPath(str(file_path))]
        
        self.dialog.show(files)
        
        # Match "draft" before extension
        self.dialog.regex_editor.set_text("draft")
        self.dialog.destination_editor.set_text("final")
        self.dialog.update_preview()
        
        # Should keep prefix and extension intact
        assert self.dialog.preview[0]['new'] == "document_final.txt"
    
    def test_replace_with_captured_groups(self, tmp_path):
        """Test replacing with captured groups preserves surrounding text"""
        # Create test file
        file_path = tmp_path / "photo_2024_01_15.jpg"
        file_path.write_text("content")
        files = [TFMPath(str(file_path))]
        
        self.dialog.show(files)
        
        # Match date pattern and reformat it
        self.dialog.regex_editor.set_text("(\\d{4})_(\\d{2})_(\\d{2})")
        self.dialog.destination_editor.set_text("\\1-\\2-\\3")
        self.dialog.update_preview()
        
        # Should keep "photo_" prefix and ".jpg" extension
        assert self.dialog.preview[0]['new'] == "photo_2024-01-15.jpg"
    
    def test_replace_extension_only(self, tmp_path):
        """Test replacing only the file extension"""
        # Create test file
        file_path = tmp_path / "document.txt"
        file_path.write_text("content")
        files = [TFMPath(str(file_path))]
        
        self.dialog.show(files)
        
        # Match extension
        self.dialog.regex_editor.set_text("\\.txt$")
        self.dialog.destination_editor.set_text(".md")
        self.dialog.update_preview()
        
        # Should keep filename intact, change extension
        assert self.dialog.preview[0]['new'] == "document.md"
    
    def test_multiple_matches_replaces_first_only(self, tmp_path):
        """Test that only the first match is replaced (search behavior)"""
        # Create test file with repeated pattern
        file_path = tmp_path / "test_test_file.txt"
        file_path.write_text("content")
        files = [TFMPath(str(file_path))]
        
        self.dialog.show(files)
        
        # Match "test" - should replace first occurrence only
        self.dialog.regex_editor.set_text("test")
        self.dialog.destination_editor.set_text("demo")
        self.dialog.update_preview()
        
        # Only first "test" should be replaced
        assert self.dialog.preview[0]['new'] == "demo_test_file.txt"
    
    def test_no_match_keeps_original(self, tmp_path):
        """Test that files without matches keep original name"""
        # Create test file
        file_path = tmp_path / "document.txt"
        file_path.write_text("content")
        files = [TFMPath(str(file_path))]
        
        self.dialog.show(files)
        
        # Pattern that doesn't match
        self.dialog.regex_editor.set_text("nomatch")
        self.dialog.destination_editor.set_text("replaced")
        self.dialog.update_preview()
        
        # Should keep original name
        assert self.dialog.preview[0]['new'] == "document.txt"
    
    def test_replace_entire_filename_with_dot_star(self, tmp_path):
        """Test that .* pattern replaces entire filename"""
        # Create test file
        file_path = tmp_path / "old_name.txt"
        file_path.write_text("content")
        files = [TFMPath(str(file_path))]
        
        self.dialog.show(files)
        
        # Match entire filename
        self.dialog.regex_editor.set_text(".*")
        self.dialog.destination_editor.set_text("new_name.txt")
        self.dialog.update_preview()
        
        # Should replace entire filename
        assert self.dialog.preview[0]['new'] == "new_name.txt"
    
    def test_add_prefix_with_empty_match(self, tmp_path):
        """Test adding prefix by matching start of string"""
        # Create test file
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        files = [TFMPath(str(file_path))]
        
        self.dialog.show(files)
        
        # Match start of string (zero-width)
        self.dialog.regex_editor.set_text("^")
        self.dialog.destination_editor.set_text("prefix_")
        self.dialog.update_preview()
        
        # Should add prefix
        assert self.dialog.preview[0]['new'] == "prefix_file.txt"
    
    def test_add_suffix_before_extension(self, tmp_path):
        """Test adding suffix before extension"""
        # Create test file
        file_path = tmp_path / "document.txt"
        file_path.write_text("content")
        files = [TFMPath(str(file_path))]
        
        self.dialog.show(files)
        
        # Match position before extension
        self.dialog.regex_editor.set_text("(?=\\.txt$)")
        self.dialog.destination_editor.set_text("_backup")
        self.dialog.update_preview()
        
        # Should add suffix before extension
        assert self.dialog.preview[0]['new'] == "document_backup.txt"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
