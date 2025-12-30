#!/usr/bin/env python3
"""
Test that BatchRenameDialog always shows preview
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path as TFMPath


class TestBatchRenameAlwaysPreview:
    """Test that preview is always displayed"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.dialog = BatchRenameDialog(self.config)
    
    def test_preview_shown_on_initial_show(self, tmp_path):
        """Test that preview is populated when dialog is first shown"""
        # Create test files
        files = []
        for i in range(3):
            file_path = tmp_path / f"test_{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
        
        # Show dialog - should populate preview immediately
        self.dialog.show(files)
        
        # Verify preview exists and shows all files as unchanged
        assert len(self.dialog.preview) == 3
        for i, preview in enumerate(self.dialog.preview):
            assert preview['original'] == f"test_{i}.txt"
            assert preview['new'] == f"test_{i}.txt"
            assert preview['valid'] is True
            assert preview['conflict'] is False
    
    def test_preview_shown_with_empty_regex(self, tmp_path):
        """Test that preview is shown even when regex is empty"""
        # Create test files
        files = []
        for i in range(2):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
        
        self.dialog.show(files)
        
        # Set only destination (no regex)
        self.dialog.destination_editor.set_text("renamed")
        self.dialog.update_preview()
        
        # Preview should still show all files as unchanged
        assert len(self.dialog.preview) == 2
        for preview in self.dialog.preview:
            assert preview['original'] == preview['new']
    
    def test_preview_shown_with_empty_destination(self, tmp_path):
        """Test that preview is shown even when destination is empty"""
        # Create test files
        files = []
        for i in range(2):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
        
        self.dialog.show(files)
        
        # Set only regex (no destination)
        self.dialog.regex_editor.set_text("file")
        self.dialog.update_preview()
        
        # Preview should still show all files as unchanged
        assert len(self.dialog.preview) == 2
        for preview in self.dialog.preview:
            assert preview['original'] == preview['new']
    
    def test_preview_shown_with_invalid_regex(self, tmp_path):
        """Test that preview is shown even when regex is invalid"""
        # Create test files
        files = []
        for i in range(2):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
        
        self.dialog.show(files)
        
        # Set invalid regex
        self.dialog.regex_editor.set_text("[invalid(regex")
        self.dialog.destination_editor.set_text("renamed")
        self.dialog.update_preview()
        
        # Preview should still show all files as unchanged
        assert len(self.dialog.preview) == 2
        for preview in self.dialog.preview:
            assert preview['original'] == preview['new']
    
    def test_preview_updates_when_patterns_added(self, tmp_path):
        """Test that preview updates correctly when patterns are added"""
        # Create test files
        files = []
        for i in range(2):
            file_path = tmp_path / f"test{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
        
        self.dialog.show(files)
        
        # Initially all unchanged
        assert all(p['original'] == p['new'] for p in self.dialog.preview)
        
        # Add patterns - match entire filename
        self.dialog.regex_editor.set_text(r".*")
        self.dialog.destination_editor.set_text(r"renamed_\d.txt")
        self.dialog.update_preview()
        
        # Now should show changes
        assert self.dialog.preview[0]['new'] == "renamed_1.txt"
        assert self.dialog.preview[1]['new'] == "renamed_2.txt"
    
    def test_preview_shows_non_matching_files_as_unchanged(self, tmp_path):
        """Test that files not matching regex are shown as unchanged"""
        # Create test files with different patterns
        files = []
        file1 = tmp_path / "match_1.txt"
        file1.write_text("content")
        files.append(TFMPath(str(file1)))
        
        file2 = tmp_path / "nomatch.txt"
        file2.write_text("content")
        files.append(TFMPath(str(file2)))
        
        self.dialog.show(files)
        
        # Set pattern that only matches first file
        self.dialog.regex_editor.set_text(r"match_(\d)")
        self.dialog.destination_editor.set_text(r"renamed_\1")
        self.dialog.update_preview()
        
        # First file should change (only matched portion), second should be unchanged
        assert self.dialog.preview[0]['new'] == "renamed_1.txt"
        assert self.dialog.preview[1]['original'] == "nomatch.txt"
        assert self.dialog.preview[1]['new'] == "nomatch.txt"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
