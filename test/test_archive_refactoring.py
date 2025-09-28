#!/usr/bin/env python3
"""
Test script to verify the archive operations refactoring works correctly
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_archive import ArchiveOperations, ArchiveUI
from tfm_path import Path as TFMPath


def test_archive_operations():
    """Test basic archive operations functionality"""
    print("Testing ArchiveOperations class...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        test_file1 = temp_path / "test1.txt"
        test_file2 = temp_path / "test2.txt"
        test_file1.write_text("Test content 1")
        test_file2.write_text("Test content 2")
        
        # Initialize archive operations
        archive_ops = ArchiveOperations()
        
        # Test archive format detection
        assert archive_ops.get_archive_format("test.zip") is not None
        assert archive_ops.get_archive_format("test.tar.gz") is not None
        assert archive_ops.get_archive_format("test.txt") is None
        
        # Test is_archive method
        zip_path = TFMPath(temp_path / "test.zip")
        assert not archive_ops.is_archive(zip_path)  # File doesn't exist yet
        
        # Create a simple archive
        source_paths = [TFMPath(test_file1), TFMPath(test_file2)]
        archive_path = TFMPath(temp_path / "test_archive.zip")
        
        success = archive_ops.create_archive(source_paths, archive_path, "zip")
        assert success, "Archive creation should succeed"
        assert archive_path.exists(), "Archive file should exist"
        assert archive_ops.is_archive(archive_path), "Created file should be recognized as archive"
        
        # Test archive extraction
        extract_dir = TFMPath(temp_path / "extracted")
        success = archive_ops.extract_archive(archive_path, extract_dir)
        assert success, "Archive extraction should succeed"
        assert extract_dir.exists(), "Extract directory should exist"
        assert (extract_dir / "test1.txt").exists(), "Extracted file should exist"
        assert (extract_dir / "test2.txt").exists(), "Extracted file should exist"
        
        # Test archive content listing
        contents = archive_ops.list_archive_contents(archive_path)
        assert len(contents) == 2, "Archive should contain 2 files"
        
        print("✓ ArchiveOperations tests passed")


def test_archive_ui_initialization():
    """Test that ArchiveUI can be initialized properly"""
    print("Testing ArchiveUI initialization...")
    
    # Mock file manager object
    class MockFileManager:
        def __init__(self):
            self.log_manager = None
            self.progress_manager = None
            self.cache_manager = None
            self.config = None
    
    # Initialize components
    archive_ops = ArchiveOperations()
    mock_fm = MockFileManager()
    
    # Test ArchiveUI initialization
    archive_ui = ArchiveUI(mock_fm, archive_ops)
    
    assert archive_ui.file_manager == mock_fm
    assert archive_ui.archive_operations == archive_ops
    
    # Test utility methods
    basename = archive_ui.get_archive_basename("test.tar.gz")
    assert basename == "test", f"Expected 'test', got '{basename}'"
    
    basename = archive_ui.get_archive_basename("archive.zip")
    assert basename == "archive", f"Expected 'archive', got '{basename}'"
    
    # Test format detection
    format_type = archive_ui._get_archive_format_from_filename("test.tar.gz")
    assert format_type == "tar.gz", f"Expected 'tar.gz', got '{format_type}'"
    
    format_type = archive_ui._get_archive_format_from_filename("test.zip")
    assert format_type == "zip", f"Expected 'zip', got '{format_type}'"
    
    print("✓ ArchiveUI initialization tests passed")


def test_backward_compatibility():
    """Test that the refactoring maintains backward compatibility"""
    print("Testing backward compatibility...")
    
    # This test would require a full FileManager instance which needs curses
    # For now, just test that the classes can be imported and initialized
    try:
        from tfm_archive import ArchiveOperations, ArchiveUI
        archive_ops = ArchiveOperations()
        
        # Test that legacy method signatures still work
        format_result = archive_ops.get_archive_format("test.zip")
        assert format_result is not None
        
        is_archive_result = archive_ops.is_archive(TFMPath("nonexistent.zip"))
        assert is_archive_result == False  # File doesn't exist
        
        print("✓ Backward compatibility tests passed")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("Running archive operations refactoring tests...\n")
    
    try:
        test_archive_operations()
        test_archive_ui_initialization()
        test_backward_compatibility()
        
        print("\n✅ All tests passed! Archive operations refactoring is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)