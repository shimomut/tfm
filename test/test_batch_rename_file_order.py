#!/usr/bin/env python3
r"""
Test that BatchRenameDialog preserves file list order for \d numbering
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path as TFMPath


class TestBatchRenameFileOrder:
    """Test file ordering in batch rename dialog"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.dialog = BatchRenameDialog(self.config)
    
    def test_file_order_preserved_in_preview(self, tmp_path):
        """Test that file order is preserved when generating preview with \\d"""
        # Create test files in specific order
        files = []
        for i in range(5):
            file_path = tmp_path / f"file_{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
        
        # Show dialog with files in specific order
        self.dialog.show(files)
        
        # Set regex and destination with \d numbering (preserve extension)
        self.dialog.regex_editor.set_text("file_(\\d)\\.txt")
        self.dialog.destination_editor.set_text("renamed_\\1_num_\\d.txt")
        self.dialog.update_preview()
        
        # Verify preview maintains order
        assert len(self.dialog.preview) == 5
        for i, preview in enumerate(self.dialog.preview):
            expected_new_name = f"renamed_{i}_num_{i+1}.txt"
            assert preview['new'] == expected_new_name, \
                f"File {i} should be renamed to {expected_new_name}, got {preview['new']}"
    
    def test_file_order_with_reverse_selection(self, tmp_path):
        """Test that file order matches list order even if selected in reverse"""
        # Create test files
        files = []
        for i in range(3):
            file_path = tmp_path / f"test_{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
        
        # Pass files in specific order (simulating selection from file list)
        self.dialog.show(files)
        
        # Use \d for numbering (preserve extension)
        self.dialog.regex_editor.set_text("test_(\\d)\\.txt")
        self.dialog.destination_editor.set_text("item_\\d.txt")
        self.dialog.update_preview()
        
        # Verify numbering follows input order
        assert self.dialog.preview[0]['new'] == "item_1.txt"
        assert self.dialog.preview[1]['new'] == "item_2.txt"
        assert self.dialog.preview[2]['new'] == "item_3.txt"
    
    def test_numbering_starts_at_one(self, tmp_path):
        """Test that \\d numbering starts at 1, not 0"""
        # Create test files
        files = []
        for i in range(3):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
        
        self.dialog.show(files)
        
        # Use only \d for numbering (preserve extension)
        self.dialog.regex_editor.set_text("file\\d\\.txt")
        self.dialog.destination_editor.set_text("renamed_\\d.txt")
        self.dialog.update_preview()
        
        # Verify numbering starts at 1
        assert self.dialog.preview[0]['new'] == "renamed_1.txt"
        assert self.dialog.preview[1]['new'] == "renamed_2.txt"
        assert self.dialog.preview[2]['new'] == "renamed_3.txt"
    
    def test_mixed_regex_groups_and_numbering(self, tmp_path):
        """Test that both regex groups and \\d numbering work together"""
        # Create test files with pattern
        files = []
        for i, name in enumerate(['alpha', 'beta', 'gamma']):
            file_path = tmp_path / f"{name}_old.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
        
        self.dialog.show(files)
        
        # Use both regex group and \d (preserve extension)
        self.dialog.regex_editor.set_text("(\\w+)_old\\.txt")
        self.dialog.destination_editor.set_text("\\d_\\1_new.txt")
        self.dialog.update_preview()
        
        # Verify both work correctly
        assert self.dialog.preview[0]['new'] == "1_alpha_new.txt"
        assert self.dialog.preview[1]['new'] == "2_beta_new.txt"
        assert self.dialog.preview[2]['new'] == "3_gamma_new.txt"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
