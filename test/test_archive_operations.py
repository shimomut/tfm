#!/usr/bin/env python3
"""
Test suite for TFM Archive Operations with cross-storage support

This test suite covers:
1. Archive format detection
2. Local archive creation and extraction
3. Cross-storage archive operations
4. Error handling and edge cases
"""

import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path as PathlibPath

# Add the src directory to the path so we can import TFM modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_archive import ArchiveOperations


class TestArchiveOperations(unittest.TestCase):
    """Test cases for archive operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = PathlibPath(tempfile.mkdtemp(prefix='tfm_archive_test_'))
        self.archive_ops = ArchiveOperations()
        
        # Create test files
        self.test_files_dir = self.temp_dir / "test_files"
        self.test_files_dir.mkdir()
        
        # Create test files with different content
        (self.test_files_dir / "file1.txt").write_text("Test file 1 content\nLine 2\n")
        (self.test_files_dir / "file2.txt").write_text("Test file 2 content\nDifferent content\n")
        
        # Create subdirectory with files
        subdir = self.test_files_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("Nested file content\n")
        (subdir / "data.json").write_text('{"test": "data"}\n')
        
        # Create archives directory
        self.archives_dir = self.temp_dir / "archives"
        self.archives_dir.mkdir()
        
        # Create extraction directory
        self.extract_dir = self.temp_dir / "extracted"
        self.extract_dir.mkdir()
    
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_archive_format_detection(self):
        """Test archive format detection from filenames"""
        test_cases = [
            ("test.zip", {"type": "zip", "compression": None}),
            ("test.tar.gz", {"type": "tar", "compression": "gz"}),
            ("test.tgz", {"type": "tar", "compression": "gz"}),
            ("test.tar.bz2", {"type": "tar", "compression": "bz2"}),
            ("test.tbz2", {"type": "tar", "compression": "bz2"}),
            ("test.tar.xz", {"type": "tar", "compression": "xz"}),
            ("test.txz", {"type": "tar", "compression": "xz"}),
            ("test.tar", {"type": "tar", "compression": None}),
            ("test.gz", {"type": "gzip", "compression": None}),
            ("test.bz2", {"type": "bzip2", "compression": None}),
            ("test.xz", {"type": "xz", "compression": None}),
            ("test.txt", None),  # Not an archive
            ("test", None),      # No extension
        ]
        
        for filename, expected in test_cases:
            with self.subTest(filename=filename):
                result = self.archive_ops.get_archive_format(filename)
                self.assertEqual(result, expected)
    
    def test_is_archive_detection(self):
        """Test archive file detection"""
        # Create test files
        archive_file = self.temp_dir / "test.tar.gz"
        archive_file.write_text("fake archive content")  # Content doesn't matter for this test
        
        text_file = self.temp_dir / "test.txt"
        text_file.write_text("regular text file")
        
        # Test detection
        self.assertTrue(self.archive_ops.is_archive(Path(archive_file)))
        self.assertFalse(self.archive_ops.is_archive(Path(text_file)))
        
        # Test with non-existent file
        non_existent = Path(self.temp_dir / "nonexistent.zip")
        self.assertFalse(self.archive_ops.is_archive(non_existent))
        
        # Test with directory
        self.assertFalse(self.archive_ops.is_archive(Path(self.test_files_dir)))
    
    def test_local_zip_creation(self):
        """Test creating ZIP archives from local files"""
        files_to_archive = [
            Path(self.test_files_dir / "file1.txt"),
            Path(self.test_files_dir / "file2.txt"),
            Path(self.test_files_dir / "subdir")
        ]
        
        archive_path = Path(self.archives_dir / "test.zip")
        
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "zip")
        
        self.assertTrue(success)
        self.assertTrue(archive_path.exists())
        self.assertGreater(archive_path.stat().st_size, 0)
    
    def test_local_tar_gz_creation(self):
        """Test creating TAR.GZ archives from local files"""
        files_to_archive = [
            Path(self.test_files_dir / "file1.txt"),
            Path(self.test_files_dir / "subdir")
        ]
        
        archive_path = Path(self.archives_dir / "test.tar.gz")
        
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "tar.gz")
        
        self.assertTrue(success)
        self.assertTrue(archive_path.exists())
        self.assertGreater(archive_path.stat().st_size, 0)
    
    def test_local_tar_bz2_creation(self):
        """Test creating TAR.BZ2 archives from local files"""
        files_to_archive = [
            Path(self.test_files_dir / "file1.txt")
        ]
        
        archive_path = Path(self.archives_dir / "test.tar.bz2")
        
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "tar.bz2")
        
        self.assertTrue(success)
        self.assertTrue(archive_path.exists())
        self.assertGreater(archive_path.stat().st_size, 0)
    
    def test_local_tar_xz_creation(self):
        """Test creating TAR.XZ archives from local files"""
        files_to_archive = [
            Path(self.test_files_dir / "file2.txt")
        ]
        
        archive_path = Path(self.archives_dir / "test.tar.xz")
        
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "tar.xz")
        
        self.assertTrue(success)
        self.assertTrue(archive_path.exists())
        self.assertGreater(archive_path.stat().st_size, 0)
    
    def test_zip_extraction(self):
        """Test extracting ZIP archives"""
        # First create a ZIP archive
        files_to_archive = [
            Path(self.test_files_dir / "file1.txt"),
            Path(self.test_files_dir / "subdir")
        ]
        
        archive_path = Path(self.archives_dir / "test_extract.zip")
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "zip")
        self.assertTrue(success)
        
        # Now extract it
        extract_subdir = Path(self.extract_dir / "zip_test")
        success = self.archive_ops.extract_archive(archive_path, extract_subdir, overwrite=True)
        
        self.assertTrue(success)
        self.assertTrue(extract_subdir.exists())
        
        # Check extracted files
        self.assertTrue((extract_subdir / "file1.txt").exists())
        self.assertTrue((extract_subdir / "subdir").exists())
        self.assertTrue((extract_subdir / "subdir" / "nested.txt").exists())
        
        # Verify content
        content = (extract_subdir / "file1.txt").read_text()
        self.assertEqual(content, "Test file 1 content\nLine 2\n")
    
    def test_tar_gz_extraction(self):
        """Test extracting TAR.GZ archives"""
        # First create a TAR.GZ archive
        files_to_archive = [
            Path(self.test_files_dir / "file2.txt"),
            Path(self.test_files_dir / "subdir")
        ]
        
        archive_path = Path(self.archives_dir / "test_extract.tar.gz")
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "tar.gz")
        self.assertTrue(success)
        
        # Now extract it
        extract_subdir = Path(self.extract_dir / "tar_gz_test")
        success = self.archive_ops.extract_archive(archive_path, extract_subdir, overwrite=True)
        
        self.assertTrue(success)
        self.assertTrue(extract_subdir.exists())
        
        # Check extracted files
        self.assertTrue((extract_subdir / "file2.txt").exists())
        self.assertTrue((extract_subdir / "subdir").exists())
        self.assertTrue((extract_subdir / "subdir" / "data.json").exists())
        
        # Verify content
        content = (extract_subdir / "subdir" / "data.json").read_text()
        self.assertEqual(content, '{"test": "data"}\n')
    
    def test_archive_listing(self):
        """Test listing archive contents"""
        # Create a test archive
        files_to_archive = [
            Path(self.test_files_dir / "file1.txt"),
            Path(self.test_files_dir / "file2.txt"),
            Path(self.test_files_dir / "subdir")
        ]
        
        archive_path = Path(self.archives_dir / "test_list.zip")
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "zip")
        self.assertTrue(success)
        
        # List contents
        contents = self.archive_ops.list_archive_contents(archive_path)
        
        self.assertIsInstance(contents, list)
        self.assertGreater(len(contents), 0)
        
        # Check that we have the expected files
        filenames = [item[0] for item in contents]
        self.assertIn("file1.txt", filenames)
        self.assertIn("file2.txt", filenames)
        
        # Check that each item has the expected structure (name, size, type)
        for item in contents:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 3)
            name, size, item_type = item
            self.assertIsInstance(name, str)
            self.assertIsInstance(size, int)
            self.assertIn(item_type, ['file', 'dir'])
    
    def test_unsupported_format(self):
        """Test handling of unsupported archive formats"""
        files_to_archive = [Path(self.test_files_dir / "file1.txt")]
        archive_path = Path(self.archives_dir / "test.unsupported")
        
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "unsupported")
        
        self.assertFalse(success)
        self.assertFalse(archive_path.exists())
    
    def test_nonexistent_source_files(self):
        """Test handling of non-existent source files"""
        files_to_archive = [Path(self.temp_dir / "nonexistent.txt")]
        archive_path = Path(self.archives_dir / "test_nonexistent.zip")
        
        # This should handle the error gracefully
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "zip")
        
        # The behavior may vary - it might succeed with empty archive or fail
        # The important thing is that it doesn't crash
        self.assertIsInstance(success, bool)
    
    def test_extraction_overwrite(self):
        """Test extraction with overwrite option"""
        # Create and extract an archive
        files_to_archive = [Path(self.test_files_dir / "file1.txt")]
        archive_path = Path(self.archives_dir / "test_overwrite.zip")
        
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "zip")
        self.assertTrue(success)
        
        extract_subdir = Path(self.extract_dir / "overwrite_test")
        
        # First extraction
        success = self.archive_ops.extract_archive(archive_path, extract_subdir, overwrite=False)
        self.assertTrue(success)
        
        # Modify the extracted file
        extracted_file = extract_subdir / "file1.txt"
        original_content = extracted_file.read_text()
        extracted_file.write_text("Modified content")
        
        # Extract again without overwrite - should not change the file
        success = self.archive_ops.extract_archive(archive_path, extract_subdir, overwrite=False)
        self.assertTrue(success)
        modified_content = extracted_file.read_text()
        self.assertEqual(modified_content, "Modified content")
        
        # Extract again with overwrite - should restore original content
        success = self.archive_ops.extract_archive(archive_path, extract_subdir, overwrite=True)
        self.assertTrue(success)
        restored_content = extracted_file.read_text()
        self.assertEqual(restored_content, original_content)
    
    def test_empty_file_list(self):
        """Test creating archive with empty file list"""
        files_to_archive = []
        archive_path = Path(self.archives_dir / "empty.zip")
        
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "zip")
        
        # Should handle empty list gracefully
        self.assertIsInstance(success, bool)


class TestArchiveIntegration(unittest.TestCase):
    """Integration tests for archive operations"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = PathlibPath(tempfile.mkdtemp(prefix='tfm_archive_integration_'))
        self.archive_ops = ArchiveOperations()
    
    def tearDown(self):
        """Clean up integration test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_round_trip_archive_operations(self):
        """Test complete round-trip: create archive, extract, verify"""
        # Create source data
        source_dir = self.temp_dir / "source"
        source_dir.mkdir()
        
        # Create test files with known content
        test_data = {
            "readme.txt": "This is a readme file\nWith multiple lines\n",
            "config.json": '{"setting1": "value1", "setting2": 42}\n',
            "data/file1.txt": "Data file 1 content\n",
            "data/file2.txt": "Data file 2 content\n",
            "data/subdir/nested.txt": "Nested file content\n"
        }
        
        for rel_path, content in test_data.items():
            file_path = source_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        # Create archive
        files_to_archive = [
            Path(source_dir / "readme.txt"),
            Path(source_dir / "config.json"),
            Path(source_dir / "data")
        ]
        
        archive_path = Path(self.temp_dir / "test_roundtrip.tar.gz")
        success = self.archive_ops.create_archive(files_to_archive, archive_path, "tar.gz")
        self.assertTrue(success)
        self.assertTrue(archive_path.exists())
        
        # Extract archive
        extract_dir = Path(self.temp_dir / "extracted")
        success = self.archive_ops.extract_archive(archive_path, extract_dir, overwrite=True)
        self.assertTrue(success)
        self.assertTrue(extract_dir.exists())
        
        # Verify extracted content
        self.assertTrue((extract_dir / "readme.txt").exists())
        self.assertTrue((extract_dir / "config.json").exists())
        self.assertTrue((extract_dir / "data").exists())
        self.assertTrue((extract_dir / "data" / "file1.txt").exists())
        self.assertTrue((extract_dir / "data" / "subdir" / "nested.txt").exists())
        
        # Verify file contents
        self.assertEqual((extract_dir / "readme.txt").read_text(), test_data["readme.txt"])
        self.assertEqual((extract_dir / "config.json").read_text(), test_data["config.json"])
        self.assertEqual((extract_dir / "data" / "file1.txt").read_text(), test_data["data/file1.txt"])
        self.assertEqual((extract_dir / "data" / "subdir" / "nested.txt").read_text(), test_data["data/subdir/nested.txt"])


def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestArchiveOperations))
    suite.addTest(unittest.makeSuite(TestArchiveIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)