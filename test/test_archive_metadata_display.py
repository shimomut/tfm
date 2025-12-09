#!/usr/bin/env python3
"""
Test archive metadata display in file details dialog
"""

import os
import sys
import tempfile
import zipfile
import tarfile
from pathlib import Path as PathlibPath

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_info_dialog import InfoDialogHelpers


def test_archive_metadata_display():
    """Test that archive entry metadata is displayed correctly"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test zip archive with a file
        archive_path = PathlibPath(tmpdir) / "test.zip"
        test_content = b"Hello, World! This is test content for compression."
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test.txt", test_content)
        
        # Create archive path
        archive_uri = f"archive://{archive_path}#test.txt"
        file_path = Path(archive_uri)
        
        # Mock info dialog to capture output
        class MockInfoDialog:
            def __init__(self):
                self.title = None
                self.lines = []
            
            def show(self, title, lines):
                self.title = title
                self.lines = lines
        
        mock_dialog = MockInfoDialog()
        
        # Show file details
        InfoDialogHelpers.show_file_details(mock_dialog, [file_path], None)
        
        # Verify the output contains archive-specific metadata
        lines_text = '\n'.join(mock_dialog.lines)
        
        print("File details output:")
        print(lines_text)
        print()
        
        # Check for required fields
        assert "Archive:" in lines_text, "Should show archive file path"
        assert "Internal Path:" in lines_text, "Should show internal path"
        assert "Archive Type:" in lines_text, "Should show archive type"
        assert "Uncompressed Size:" in lines_text, "Should show uncompressed size"
        assert "Compressed Size:" in lines_text, "Should show compressed size"
        assert "Compression Ratio:" in lines_text, "Should show compression ratio"
        
        # Verify archive type is correct
        assert "zip" in lines_text.lower(), "Should identify as zip archive"
        
        # Verify internal path is shown
        assert "test.txt" in lines_text, "Should show internal path to file"
        
        print("✓ Archive metadata display test passed")


def test_archive_directory_metadata():
    """Test metadata display for directories within archives"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test zip archive with a directory
        archive_path = PathlibPath(tmpdir) / "test.zip"
        
        with zipfile.ZipFile(archive_path, 'w') as zf:
            # Create a directory entry
            zf.writestr("testdir/", "")
            zf.writestr("testdir/file.txt", "content")
        
        # Create archive path for directory
        archive_uri = f"archive://{archive_path}#testdir/"
        dir_path = Path(archive_uri)
        
        # Mock info dialog
        class MockInfoDialog:
            def __init__(self):
                self.title = None
                self.lines = []
            
            def show(self, title, lines):
                self.title = title
                self.lines = lines
        
        mock_dialog = MockInfoDialog()
        
        # Show file details
        InfoDialogHelpers.show_file_details(mock_dialog, [dir_path], None)
        
        lines_text = '\n'.join(mock_dialog.lines)
        
        print("Directory details output:")
        print(lines_text)
        print()
        
        # Check for required fields
        assert "Archive:" in lines_text, "Should show archive file path"
        assert "Internal Path:" in lines_text, "Should show internal path"
        assert "Type: Directory" in lines_text, "Should identify as directory"
        
        # Directories should not show size/compression info
        assert "Uncompressed Size:" not in lines_text, "Directories should not show uncompressed size"
        assert "Compressed Size:" not in lines_text, "Directories should not show compressed size"
        
        print("✓ Archive directory metadata test passed")


def test_regular_file_still_works():
    """Test that regular file details still work correctly"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a regular file
        test_file = PathlibPath(tmpdir) / "regular.txt"
        test_file.write_text("Regular file content")
        
        file_path = Path(str(test_file))
        
        # Mock info dialog
        class MockInfoDialog:
            def __init__(self):
                self.title = None
                self.lines = []
            
            def show(self, title, lines):
                self.title = title
                self.lines = lines
        
        mock_dialog = MockInfoDialog()
        
        # Show file details
        InfoDialogHelpers.show_file_details(mock_dialog, [file_path], None)
        
        lines_text = '\n'.join(mock_dialog.lines)
        
        print("Regular file details output:")
        print(lines_text)
        print()
        
        # Check for regular file fields
        assert "Name:" in lines_text, "Should show name"
        assert "Path:" in lines_text, "Should show path"
        assert "Type:" in lines_text, "Should show type"
        assert "Size:" in lines_text, "Should show size"
        assert "Permissions:" in lines_text, "Should show permissions"
        assert "Modified:" in lines_text, "Should show modification time"
        
        # Should NOT show archive-specific fields
        assert "Archive:" not in lines_text, "Should not show archive field for regular files"
        assert "Internal Path:" not in lines_text, "Should not show internal path for regular files"
        assert "Archive Type:" not in lines_text, "Should not show archive type for regular files"
        assert "Compression Ratio:" not in lines_text, "Should not show compression ratio for regular files"
        
        print("✓ Regular file details test passed")


def test_tar_archive_metadata():
    """Test metadata display for tar archives"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test tar.gz archive
        archive_path = PathlibPath(tmpdir) / "test.tar.gz"
        test_content = b"Test content for tar archive"
        
        with tarfile.open(archive_path, 'w:gz') as tf:
            # Create a file in memory
            import io
            file_data = io.BytesIO(test_content)
            tarinfo = tarfile.TarInfo(name="test.txt")
            tarinfo.size = len(test_content)
            tf.addfile(tarinfo, file_data)
        
        # Create archive path
        archive_uri = f"archive://{archive_path}#test.txt"
        file_path = Path(archive_uri)
        
        # Mock info dialog
        class MockInfoDialog:
            def __init__(self):
                self.title = None
                self.lines = []
            
            def show(self, title, lines):
                self.title = title
                self.lines = lines
        
        mock_dialog = MockInfoDialog()
        
        # Show file details
        InfoDialogHelpers.show_file_details(mock_dialog, [file_path], None)
        
        lines_text = '\n'.join(mock_dialog.lines)
        
        print("Tar archive details output:")
        print(lines_text)
        print()
        
        # Check for required fields
        assert "Archive:" in lines_text, "Should show archive file path"
        assert "Archive Type:" in lines_text, "Should show archive type"
        
        # Verify archive type mentions tar
        assert "tar" in lines_text.lower(), "Should identify as tar archive"
        
        print("✓ Tar archive metadata test passed")


if __name__ == '__main__':
    print("Testing archive metadata display...")
    print()
    
    test_archive_metadata_display()
    print()
    
    test_archive_directory_metadata()
    print()
    
    test_regular_file_still_works()
    print()
    
    test_tar_archive_metadata()
    print()
    
    print("All archive metadata display tests passed!")
