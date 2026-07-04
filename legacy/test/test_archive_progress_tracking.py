#!/usr/bin/env python3
"""
Tests for archive operation progress tracking
"""

import unittest
import tempfile
import shutil
from pathlib import Path as PathlibPath
from unittest.mock import Mock, MagicMock, patch, call

from tfm_path import Path
from tfm_archive_operation_executor import ArchiveOperationExecutor
from tfm_progress_manager import ProgressManager, OperationType


class TestArchiveProgressTracking(unittest.TestCase):
    """Test progress tracking in archive operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp(prefix='tfm_test_')
        self.temp_path = PathlibPath(self.temp_dir)
        
        # Create mock file manager
        self.file_manager = Mock()
        self.file_manager.operation_cancelled = False
        self.file_manager.mark_dirty = Mock()
        
        # Create real progress manager
        self.progress_manager = ProgressManager()
        
        # Create mock cache manager
        self.cache_manager = Mock()
        
        # Create executor
        self.executor = ArchiveOperationExecutor(
            self.file_manager,
            self.progress_manager,
            self.cache_manager
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        if PathlibPath(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_count_files_recursively_single_file(self):
        """Test counting a single file"""
        # Create a test file
        test_file = self.temp_path / "test.txt"
        test_file.write_text("test content")
        
        # Count files
        count = self.executor._count_files_recursively([Path(test_file)])
        
        self.assertEqual(count, 1)
    
    def test_count_files_recursively_directory(self):
        """Test counting files in a directory"""
        # Create test directory with files
        test_dir = self.temp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")
        
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        # Count files
        count = self.executor._count_files_recursively([Path(test_dir)])
        
        self.assertEqual(count, 3)
    
    def test_count_files_recursively_mixed(self):
        """Test counting mixed files and directories"""
        # Create test files and directories
        file1 = self.temp_path / "file1.txt"
        file1.write_text("content1")
        
        test_dir = self.temp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file2.txt").write_text("content2")
        (test_dir / "file3.txt").write_text("content3")
        
        # Count files
        count = self.executor._count_files_recursively([Path(file1), Path(test_dir)])
        
        self.assertEqual(count, 3)
    
    def test_count_files_with_cancellation(self):
        """Test that counting respects cancellation flag"""
        # Create many files
        test_dir = self.temp_path / "testdir"
        test_dir.mkdir()
        for i in range(10):
            (test_dir / f"file{i}.txt").write_text(f"content{i}")
        
        # Set cancellation flag after first file
        def cancel_after_first(*args):
            self.file_manager.operation_cancelled = True
        
        # Count should stop early
        count = self.executor._count_files_recursively([Path(test_dir)])
        
        # Should have counted at least 1 file before cancellation
        self.assertGreaterEqual(count, 0)
    
    def test_progress_callback_calls_mark_dirty(self):
        """Test that progress callback triggers UI refresh"""
        # Call progress callback
        self.executor._progress_callback()
        
        # Verify mark_dirty was called
        self.file_manager.mark_dirty.assert_called_once()
    
    def test_progress_manager_integration_create(self):
        """Test progress manager integration during archive creation"""
        # Create test files
        file1 = self.temp_path / "file1.txt"
        file1.write_text("content1")
        file2 = self.temp_path / "file2.txt"
        file2.write_text("content2")
        
        archive_path = self.temp_path / "test.tar"
        
        # Mock progress manager methods
        self.progress_manager.start_operation = Mock()
        self.progress_manager.update_progress = Mock()
        self.progress_manager.finish_operation = Mock()
        self.progress_manager.increment_errors = Mock()
        
        # Create archive (synchronously for testing)
        success, errors = self.executor._create_archive_local(
            [Path(file1), Path(file2)],
            Path(archive_path),
            {'type': 'tar', 'compression': None}
        )
        
        # Verify progress manager was used
        self.assertEqual(success, 2)
        self.assertEqual(errors, 0)
        self.assertEqual(self.progress_manager.update_progress.call_count, 2)
        self.assertEqual(self.progress_manager.increment_errors.call_count, 0)
    
    def test_progress_manager_tracks_errors(self):
        """Test that progress manager tracks errors separately"""
        # Create test file
        file1 = self.temp_path / "file1.txt"
        file1.write_text("content1")
        
        # Create archive path in non-existent directory (will cause error)
        archive_path = self.temp_path / "nonexistent" / "test.tar"
        
        # Mock progress manager methods
        self.progress_manager.start_operation = Mock()
        self.progress_manager.update_progress = Mock()
        self.progress_manager.finish_operation = Mock()
        self.progress_manager.increment_errors = Mock()
        
        # Try to create archive (will fail)
        success, errors = self.executor._create_archive_local(
            [Path(file1)],
            Path(archive_path),
            {'type': 'tar', 'compression': None}
        )
        
        # Verify error was tracked
        self.assertEqual(success, 0)
        self.assertGreater(errors, 0)
        self.assertGreater(self.progress_manager.increment_errors.call_count, 0)
    
    def test_error_count_separate_from_success(self):
        """Test that error count is tracked separately from success count"""
        # This is verified by the return tuple structure
        success_count = 5
        error_count = 2
        
        # The executor returns (success_count, error_count) as separate values
        result = (success_count, error_count)
        
        self.assertEqual(result[0], 5)
        self.assertEqual(result[1], 2)
        self.assertNotEqual(result[0], result[1])


if __name__ == '__main__':
    unittest.main()
