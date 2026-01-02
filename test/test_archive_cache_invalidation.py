#!/usr/bin/env python3
"""
Test cache invalidation for archive operations
"""

import unittest
import tempfile
import shutil
from pathlib import Path as PathlibPath
from unittest.mock import Mock, MagicMock, patch, call

from tfm_path import Path
from tfm_archive_operation_executor import ArchiveOperationExecutor
from tfm_progress_manager import ProgressManager
from tfm_cache_manager import CacheManager


class TestArchiveCacheInvalidation(unittest.TestCase):
    """Test cache invalidation for archive operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp(prefix='tfm_test_')
        self.temp_path = PathlibPath(self.temp_dir)
        
        # Create mock file manager
        self.mock_file_manager = Mock()
        self.mock_file_manager.operation_cancelled = False
        self.mock_file_manager.mark_dirty = Mock()
        
        # Create mock progress manager
        self.mock_progress_manager = Mock(spec=ProgressManager)
        
        # Create mock cache manager
        self.mock_cache_manager = Mock(spec=CacheManager)
        
        # Create executor with mock cache manager
        self.executor = ArchiveOperationExecutor(
            self.mock_file_manager,
            self.mock_progress_manager,
            self.mock_cache_manager
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        if PathlibPath(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_cache_invalidation_on_archive_creation(self):
        """Test that cache is invalidated after successful archive creation"""
        # Create test files
        test_file1 = self.temp_path / 'file1.txt'
        test_file1.write_text('content1')
        test_file2 = self.temp_path / 'file2.txt'
        test_file2.write_text('content2')
        
        source_paths = [Path(test_file1), Path(test_file2)]
        archive_path = Path(self.temp_path / 'test.tar.gz')
        
        # Create archive
        self.executor.perform_create_operation(
            source_paths,
            archive_path,
            'tar.gz',
            completion_callback=None
        )
        
        # Wait for background thread to complete
        if self.executor._current_thread:
            self.executor._current_thread.join(timeout=5)
        
        # Verify cache invalidation was called
        self.mock_cache_manager.invalidate_cache_for_archive_operation.assert_called_once()
        
        # Verify it was called with correct arguments
        call_args = self.mock_cache_manager.invalidate_cache_for_archive_operation.call_args
        self.assertEqual(call_args[0][0], archive_path)  # First arg is archive_path
        self.assertEqual(call_args[0][1], source_paths)  # Second arg is source_paths
    
    def test_cache_invalidation_on_archive_extraction(self):
        """Test that cache is invalidated after successful archive extraction"""
        # Create a test archive
        test_file = self.temp_path / 'test.txt'
        test_file.write_text('test content')
        
        archive_path = Path(self.temp_path / 'test.tar.gz')
        extract_dir = Path(self.temp_path / 'extracted')
        
        # Create archive first
        import tarfile
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            tar.add(str(test_file), arcname='test.txt')
        
        # Extract archive
        self.executor.perform_extract_operation(
            archive_path,
            extract_dir,
            overwrite=True,
            skip_files=[],
            completion_callback=None
        )
        
        # Wait for background thread to complete
        if self.executor._current_thread:
            self.executor._current_thread.join(timeout=5)
        
        # Verify cache invalidation was called
        self.mock_cache_manager.invalidate_cache_for_directory.assert_called_once()
        
        # Verify it was called with correct arguments
        call_args = self.mock_cache_manager.invalidate_cache_for_directory.call_args
        self.assertEqual(call_args[0][0], extract_dir)  # First arg is destination_dir
        self.assertEqual(call_args[0][1], "archive extraction")  # Second arg is operation description
    
    def test_no_cache_invalidation_on_cancelled_creation(self):
        """Test that cache is not invalidated when archive creation is cancelled"""
        # Create test file
        test_file = self.temp_path / 'file1.txt'
        test_file.write_text('content1')
        
        source_paths = [Path(test_file)]
        archive_path = Path(self.temp_path / 'test.tar.gz')
        
        # Set cancellation flag before operation
        self.mock_file_manager.operation_cancelled = True
        
        # Create archive (will be cancelled)
        self.executor.perform_create_operation(
            source_paths,
            archive_path,
            'tar.gz',
            completion_callback=None
        )
        
        # Wait for background thread to complete
        if self.executor._current_thread:
            self.executor._current_thread.join(timeout=5)
        
        # Verify cache invalidation was NOT called (operation was cancelled)
        self.mock_cache_manager.invalidate_cache_for_archive_operation.assert_not_called()
    
    def test_no_cache_invalidation_on_cancelled_extraction(self):
        """Test that cache is not invalidated when archive extraction is cancelled"""
        # Create a test archive
        test_file = self.temp_path / 'test.txt'
        test_file.write_text('test content')
        
        archive_path = Path(self.temp_path / 'test.tar.gz')
        extract_dir = Path(self.temp_path / 'extracted')
        
        # Create archive first
        import tarfile
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            tar.add(str(test_file), arcname='test.txt')
        
        # Set cancellation flag before operation
        self.mock_file_manager.operation_cancelled = True
        
        # Extract archive (will be cancelled)
        self.executor.perform_extract_operation(
            archive_path,
            extract_dir,
            overwrite=True,
            skip_files=[],
            completion_callback=None
        )
        
        # Wait for background thread to complete
        if self.executor._current_thread:
            self.executor._current_thread.join(timeout=5)
        
        # Verify cache invalidation was NOT called (operation was cancelled)
        self.mock_cache_manager.invalidate_cache_for_directory.assert_not_called()
    
    def test_no_cache_invalidation_when_no_cache_manager(self):
        """Test that operations work correctly when no cache manager is provided"""
        # Create executor without cache manager
        executor_no_cache = ArchiveOperationExecutor(
            self.mock_file_manager,
            self.mock_progress_manager,
            cache_manager=None
        )
        
        # Create test file
        test_file = self.temp_path / 'file1.txt'
        test_file.write_text('content1')
        
        source_paths = [Path(test_file)]
        archive_path = Path(self.temp_path / 'test.tar.gz')
        
        # Create archive (should not raise exception)
        executor_no_cache.perform_create_operation(
            source_paths,
            archive_path,
            'tar.gz',
            completion_callback=None
        )
        
        # Wait for background thread to complete
        if executor_no_cache._current_thread:
            executor_no_cache._current_thread.join(timeout=5)
        
        # Verify archive was created successfully
        self.assertTrue(archive_path.exists())


if __name__ == '__main__':
    unittest.main()
