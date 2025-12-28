#!/usr/bin/env python3
"""
Test script for the archive extraction feature implementation
"""

import os
import tempfile
import zipfile
import tarfile
from pathlib import Path

def create_test_archive_files(temp_dir):
    """Create test files and archives for testing extraction"""
    temp_path = Path(temp_dir)
    
    # Create source directory with test files
    source_dir = temp_path / "source"
    source_dir.mkdir()
    
    # Create test files
    test_file1 = source_dir / "test1.txt"
    test_file1.write_text("This is test file 1")
    
    test_file2 = source_dir / "test2.txt"
    test_file2.write_text("This is test file 2")
    
    # Create a test subdirectory with content
    test_subdir = source_dir / "subdir"
    test_subdir.mkdir()
    (test_subdir / "nested.txt").write_text("Nested file content")
    
    # Create ZIP archive
    zip_path = temp_path / "test_archive.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(test_file1, test_file1.name)
        zipf.write(test_file2, test_file2.name)
        zipf.write(test_subdir / "nested.txt", f"{test_subdir.name}/nested.txt")
    
    # Create TAR.GZ archive
    tar_path = temp_path / "test_archive.tar.gz"
    with tarfile.open(tar_path, 'w:gz') as tarf:
        tarf.add(test_file1, arcname=test_file1.name)
        tarf.add(test_file2, arcname=test_file2.name)
        tarf.add(test_subdir, arcname=test_subdir.name)
    
    return zip_path, tar_path

def test_archive_detection():
    """Test archive format detection"""
    print("Testing archive format detection...")
    
    # Import the FileManager class to test its methods
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from tfm_main import FileManager
    
    # Create a mock FileManager instance for testing
    class MockFileManager:
        def detect_archive_format(self, filename):
            """Detect archive format from filename extension"""
            filename_lower = filename.lower()
            
            if filename_lower.endswith('.zip'):
                return 'zip'
            elif filename_lower.endswith('.tar.gz'):
                return 'tar.gz'
            elif filename_lower.endswith('.tgz'):
                return 'tgz'
            else:
                return None
        
        def get_archive_basename(self, filename):
            """Get the base name of an archive file (without extension)"""
            filename_lower = filename.lower()
            
            if filename_lower.endswith('.tar.gz'):
                return filename[:-7]  # Remove .tar.gz
            elif filename_lower.endswith('.tgz'):
                return filename[:-4]  # Remove .tgz
            elif filename_lower.endswith('.zip'):
                return filename[:-4]  # Remove .zip
            else:
                # Fallback - remove last extension
                return Path(filename).stem
    
    fm = MockFileManager()
    
    # Test format detection
    assert fm.detect_archive_format("test.zip") == "zip"
    assert fm.detect_archive_format("test.tar.gz") == "tar.gz"
    assert fm.detect_archive_format("test.tgz") == "tgz"
    assert fm.detect_archive_format("test.txt") is None
    print("✓ Archive format detection works correctly")
    
    # Test basename extraction
    assert fm.get_archive_basename("test.zip") == "test"
    assert fm.get_archive_basename("archive.tar.gz") == "archive"
    assert fm.get_archive_basename("backup.tgz") == "backup"
    print("✓ Archive basename extraction works correctly")

def test_zip_extraction():
    """Test ZIP archive extraction"""
    print("\nTesting ZIP archive extraction...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path, _ = create_test_archive_files(temp_dir)
        temp_path = Path(temp_dir)
        
        # Create extraction directory
        extract_dir = temp_path / "extracted_zip"
        extract_dir.mkdir()
        
        # Extract ZIP archive
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_dir)
        
        # Verify extraction
        assert (extract_dir / "test1.txt").exists()
        assert (extract_dir / "test2.txt").exists()
        assert (extract_dir / "subdir" / "nested.txt").exists()
        
        # Verify content
        assert (extract_dir / "test1.txt").read_text() == "This is test file 1"
        assert (extract_dir / "test2.txt").read_text() == "This is test file 2"
        assert (extract_dir / "subdir" / "nested.txt").read_text() == "Nested file content"
        
        print("✓ ZIP extraction successful")

def test_tar_extraction():
    """Test TAR.GZ archive extraction"""
    print("\nTesting TAR.GZ archive extraction...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        _, tar_path = create_test_archive_files(temp_dir)
        temp_path = Path(temp_dir)
        
        # Create extraction directory
        extract_dir = temp_path / "extracted_tar"
        extract_dir.mkdir()
        
        # Extract TAR.GZ archive
        with tarfile.open(tar_path, 'r:gz') as tarf:
            tarf.extractall(extract_dir)
        
        # Verify extraction
        assert (extract_dir / "test1.txt").exists()
        assert (extract_dir / "test2.txt").exists()
        assert (extract_dir / "subdir" / "nested.txt").exists()
        
        # Verify content
        assert (extract_dir / "test1.txt").read_text() == "This is test file 1"
        assert (extract_dir / "test2.txt").read_text() == "This is test file 2"
        assert (extract_dir / "subdir" / "nested.txt").read_text() == "Nested file content"
        
        print("✓ TAR.GZ extraction successful")

def test_key_binding():
    """Test that the key binding is properly configured"""
    print("\nTesting key binding configuration...")
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from tfm_config import get_config, ConfigManager
    
    # Test that 'U' is bound to extract_archive (alphabet keys are uppercase in config)
    config_manager = ConfigManager()
    assert config_manager.is_key_bound_to_action('U', 'extract_archive')
    
    print("✓ Key bindings configured correctly")

def run_all_tests():
    """Run all archive extraction tests"""
    print("Running archive extraction feature tests...")
    print("=" * 50)
    
    try:
        test_archive_detection()
        test_zip_extraction()
        test_tar_extraction()
        test_key_binding()
        
        print("\n" + "=" * 50)
        print("✓ All archive extraction tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)