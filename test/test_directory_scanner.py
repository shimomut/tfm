"""
Unit tests for DirectoryScanner class.

Tests the recursive directory scanning functionality including:
- Basic directory traversal
- Progress callback invocation
- Cancellation support
- Error handling for inaccessible files

Run with: PYTHONPATH=.:src:ttk pytest test/test_directory_scanner.py -v
"""

import unittest
import tempfile
import os
from pathlib import Path as PathlibPath
from src.tfm_path import Path
from src.tfm_directory_diff_viewer import DirectoryScanner, FileInfo


class TestDirectoryScanner(unittest.TestCase):
    """Test cases for DirectoryScanner class."""
    
    def setUp(self):
        """Create temporary test directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.left_dir = PathlibPath(self.temp_dir) / "left"
        self.right_dir = PathlibPath(self.temp_dir) / "right"
        
        # Create test directory structures
        self.left_dir.mkdir()
        self.right_dir.mkdir()
        
        # Create some test files in left directory
        (self.left_dir / "file1.txt").write_text("content1")
        (self.left_dir / "file2.txt").write_text("content2")
        (self.left_dir / "subdir").mkdir()
        (self.left_dir / "subdir" / "file3.txt").write_text("content3")
        
        # Create some test files in right directory
        (self.right_dir / "file1.txt").write_text("content1")
        (self.right_dir / "file4.txt").write_text("content4")
        (self.right_dir / "subdir").mkdir()
        (self.right_dir / "subdir" / "file5.txt").write_text("content5")
    
    def tearDown(self):
        """Clean up temporary directories."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_scan(self):
        """Test basic directory scanning."""
        left_path = Path(self.left_dir)
        right_path = Path(self.right_dir)
        
        scanner = DirectoryScanner(left_path, right_path, None)
        left_files, right_files = scanner.scan()
        
        # Verify left directory files
        self.assertIn("file1.txt", left_files)
        self.assertIn("file2.txt", left_files)
        self.assertIn("subdir", left_files)
        self.assertIn("subdir/file3.txt", left_files)
        
        # Verify right directory files
        self.assertIn("file1.txt", right_files)
        self.assertIn("file4.txt", right_files)
        self.assertIn("subdir", right_files)
        self.assertIn("subdir/file5.txt", right_files)
        
        # Verify FileInfo properties
        file1_info = left_files["file1.txt"]
        self.assertFalse(file1_info.is_directory)
        self.assertTrue(file1_info.is_accessible)
        self.assertIsNone(file1_info.error_message)
        self.assertGreater(file1_info.size, 0)
        
        subdir_info = left_files["subdir"]
        self.assertTrue(subdir_info.is_directory)
        self.assertTrue(subdir_info.is_accessible)
    
    def test_progress_callback(self):
        """Test that progress callback is invoked during scanning."""
        left_path = Path(self.left_dir)
        right_path = Path(self.right_dir)
        
        progress_calls = []
        
        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))
        
        scanner = DirectoryScanner(left_path, right_path, progress_callback)
        scanner.scan()
        
        # Verify progress callback was called
        self.assertGreater(len(progress_calls), 0)
        
        # Verify we got messages for both directories
        messages = [call[2] for call in progress_calls]
        self.assertTrue(any("left" in msg.lower() for msg in messages))
        self.assertTrue(any("right" in msg.lower() for msg in messages))
        self.assertTrue(any("complete" in msg.lower() for msg in messages))
    
    def test_cancellation(self):
        """Test that scanning can be cancelled."""
        # Create a larger directory structure for cancellation test
        large_dir = PathlibPath(self.temp_dir) / "large"
        large_dir.mkdir()
        for i in range(100):
            (large_dir / f"file{i}.txt").write_text(f"content{i}")
        
        left_path = Path(large_dir)
        right_path = Path(self.right_dir)
        
        scanner = DirectoryScanner(left_path, right_path, None)
        
        # Cancel immediately
        scanner.cancel()
        left_files, right_files = scanner.scan()
        
        # Should return empty dictionaries when cancelled
        self.assertEqual(len(left_files), 0)
        self.assertEqual(len(right_files), 0)
    
    def test_empty_directory(self):
        """Test scanning empty directories."""
        empty_left = PathlibPath(self.temp_dir) / "empty_left"
        empty_right = PathlibPath(self.temp_dir) / "empty_right"
        empty_left.mkdir()
        empty_right.mkdir()
        
        left_path = Path(empty_left)
        right_path = Path(empty_right)
        
        scanner = DirectoryScanner(left_path, right_path, None)
        left_files, right_files = scanner.scan()
        
        # Empty directories should return empty dictionaries
        self.assertEqual(len(left_files), 0)
        self.assertEqual(len(right_files), 0)
    
    def test_nested_directories(self):
        """Test scanning deeply nested directory structures."""
        nested_dir = PathlibPath(self.temp_dir) / "nested"
        nested_dir.mkdir()
        
        # Create nested structure: nested/a/b/c/file.txt
        current = nested_dir
        for level in ["a", "b", "c"]:
            current = current / level
            current.mkdir()
        (current / "file.txt").write_text("deep content")
        
        left_path = Path(nested_dir)
        right_path = Path(self.right_dir)
        
        scanner = DirectoryScanner(left_path, right_path, None)
        left_files, right_files = scanner.scan()
        
        # Verify nested structure is captured
        self.assertIn("a", left_files)
        self.assertIn("a/b", left_files)
        self.assertIn("a/b/c", left_files)
        self.assertIn("a/b/c/file.txt", left_files)
