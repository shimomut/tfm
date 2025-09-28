#!/usr/bin/env python3
"""
Test S3 Cache Invalidation - Tests cache invalidation after file operations

This test verifies that S3 cache is properly invalidated after file/archive operations
to ensure directory listings are refreshed correctly.
"""

import unittest
import tempfile
import shutil
from pathlib import Path as PathlibPath
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_cache_manager import CacheManager
from tfm_path import Path


class TestS3CacheInvalidation(unittest.TestCase):
    """Test S3 cache invalidation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.log_manager = Mock()
        self.cache_manager = CacheManager(self.log_manager)
        
        # Mock S3 cache
        self.mock_s3_cache = Mock()
        self.mock_s3_cache.invalidate_key = Mock()
        
        # Mock S3 paths
        self.mock_s3_path = Mock()
        self.mock_s3_path.get_scheme.return_value = 's3'
        self.mock_s3_path._impl = Mock()
        self.mock_s3_path._impl._bucket = 'test-bucket'
        self.mock_s3_path._impl._key = 'test/file.txt'
        
        self.mock_s3_dir = Mock()
        self.mock_s3_dir.get_scheme.return_value = 's3'
        self.mock_s3_dir._impl = Mock()
        self.mock_s3_dir._impl._bucket = 'test-bucket'
        self.mock_s3_dir._impl._key = 'test/'
    
    @patch('tfm_cache_manager.get_s3_cache')
    def test_invalidate_cache_for_copy_operation(self, mock_get_s3_cache):
        """Test cache invalidation for copy operations"""
        mock_get_s3_cache.return_value = self.mock_s3_cache
        
        source_paths = [self.mock_s3_path]
        destination_dir = self.mock_s3_dir
        
        # Test copy operation cache invalidation
        self.cache_manager.invalidate_cache_for_copy_operation(source_paths, destination_dir)
        
        # Verify S3 cache invalidation was called
        self.assertTrue(self.mock_s3_cache.invalidate_key.called)
        
        # Check that appropriate keys were invalidated
        call_args_list = self.mock_s3_cache.invalidate_key.call_args_list
        
        # Should invalidate destination directory and destination file path
        expected_calls = [
            ('test-bucket', 'test/'),  # destination directory
            ('test-bucket', 'test/file.txt'),  # destination file
            ('test-bucket', ''),  # bucket root (for top-level changes)
        ]
        
        actual_calls = [(call[0][0], call[0][1]) for call in call_args_list]
        
        # Check that all expected calls were made
        for expected_call in expected_calls:
            self.assertIn(expected_call, actual_calls)
    
    @patch('tfm_cache_manager.get_s3_cache')
    def test_invalidate_cache_for_move_operation(self, mock_get_s3_cache):
        """Test cache invalidation for move operations"""
        mock_get_s3_cache.return_value = self.mock_s3_cache
        
        # Create source path with parent
        source_parent = Mock()
        source_parent.get_scheme.return_value = 's3'
        source_parent._impl = Mock()
        source_parent._impl._bucket = 'test-bucket'
        source_parent._impl._key = 'source/'
        
        self.mock_s3_path.parent = source_parent
        
        source_paths = [self.mock_s3_path]
        destination_dir = self.mock_s3_dir
        
        # Test move operation cache invalidation
        self.cache_manager.invalidate_cache_for_move_operation(source_paths, destination_dir)
        
        # Verify S3 cache invalidation was called
        self.assertTrue(self.mock_s3_cache.invalidate_key.called)
        
        # Should invalidate both source and destination directories
        call_args_list = self.mock_s3_cache.invalidate_key.call_args_list
        actual_calls = [(call[0][0], call[0][1]) for call in call_args_list]
        
        # Should include source parent, destination directory, and destination file
        expected_buckets = ['test-bucket'] * len(actual_calls)
        actual_buckets = [call[0] for call in actual_calls]
        
        self.assertEqual(actual_buckets, expected_buckets)
    
    @patch('tfm_cache_manager.get_s3_cache')
    def test_invalidate_cache_for_delete_operation(self, mock_get_s3_cache):
        """Test cache invalidation for delete operations"""
        mock_get_s3_cache.return_value = self.mock_s3_cache
        
        # Create parent for deleted path
        parent_path = Mock()
        parent_path.get_scheme.return_value = 's3'
        parent_path._impl = Mock()
        parent_path._impl._bucket = 'test-bucket'
        parent_path._impl._key = 'test/'
        
        self.mock_s3_path.parent = parent_path
        
        deleted_paths = [self.mock_s3_path]
        
        # Test delete operation cache invalidation
        self.cache_manager.invalidate_cache_for_delete_operation(deleted_paths)
        
        # Verify S3 cache invalidation was called
        self.assertTrue(self.mock_s3_cache.invalidate_key.called)
        
        # Should invalidate both the deleted file and its parent directory
        call_args_list = self.mock_s3_cache.invalidate_key.call_args_list
        actual_calls = [(call[0][0], call[0][1]) for call in call_args_list]
        
        # Should include both the deleted path and its parent
        expected_keys = ['test/file.txt', 'test/']
        actual_keys = [call[1] for call in actual_calls]
        
        for expected_key in expected_keys:
            self.assertIn(expected_key, actual_keys)
    
    @patch('tfm_cache_manager.get_s3_cache')
    def test_invalidate_cache_for_archive_operation(self, mock_get_s3_cache):
        """Test cache invalidation for archive operations"""
        mock_get_s3_cache.return_value = self.mock_s3_cache
        
        # Create archive path
        archive_path = Mock()
        archive_path.get_scheme.return_value = 's3'
        archive_path._impl = Mock()
        archive_path._impl._bucket = 'test-bucket'
        archive_path._impl._key = 'archives/test.zip'
        
        archive_parent = Mock()
        archive_parent.get_scheme.return_value = 's3'
        archive_parent._impl = Mock()
        archive_parent._impl._bucket = 'test-bucket'
        archive_parent._impl._key = 'archives/'
        
        archive_path.parent = archive_parent
        
        source_paths = [self.mock_s3_path]
        
        # Test archive operation cache invalidation
        self.cache_manager.invalidate_cache_for_archive_operation(archive_path, source_paths)
        
        # Verify S3 cache invalidation was called
        self.assertTrue(self.mock_s3_cache.invalidate_key.called)
        
        # Should invalidate archive path, archive parent, and source parent directories
        call_args_list = self.mock_s3_cache.invalidate_key.call_args_list
        actual_calls = [(call[0][0], call[0][1]) for call in call_args_list]
        
        # Should include archive-related paths
        expected_keys = ['archives/test.zip', 'archives/']
        actual_keys = [call[1] for call in actual_calls]
        
        for expected_key in expected_keys:
            self.assertIn(expected_key, actual_keys)
    
    @patch('tfm_cache_manager.get_s3_cache')
    def test_invalidate_cache_for_create_operation(self, mock_get_s3_cache):
        """Test cache invalidation for create operations"""
        mock_get_s3_cache.return_value = self.mock_s3_cache
        
        # Create parent for new path
        parent_path = Mock()
        parent_path.get_scheme.return_value = 's3'
        parent_path._impl = Mock()
        parent_path._impl._bucket = 'test-bucket'
        parent_path._impl._key = 'test/'
        
        self.mock_s3_path.parent = parent_path
        
        # Test create operation cache invalidation
        self.cache_manager.invalidate_cache_for_create_operation(self.mock_s3_path)
        
        # Verify S3 cache invalidation was called
        self.assertTrue(self.mock_s3_cache.invalidate_key.called)
        
        # Should invalidate both the created path and its parent directory
        call_args_list = self.mock_s3_cache.invalidate_key.call_args_list
        actual_calls = [(call[0][0], call[0][1]) for call in call_args_list]
        
        # Should include both the created path and its parent
        expected_keys = ['test/file.txt', 'test/']
        actual_keys = [call[1] for call in actual_calls]
        
        for expected_key in expected_keys:
            self.assertIn(expected_key, actual_keys)
    
    def test_non_s3_paths_ignored(self):
        """Test that non-S3 paths are ignored for cache invalidation"""
        # Create local path
        local_path = Mock()
        local_path.get_scheme.return_value = 'file'
        
        # Test that no S3 cache operations are performed for local paths
        with patch('tfm_cache_manager.get_s3_cache') as mock_get_s3_cache:
            self.cache_manager.invalidate_cache_for_paths([local_path], "test operation")
            
            # S3 cache should not be accessed for local paths
            mock_get_s3_cache.assert_not_called()
    
    def test_cache_invalidation_error_handling(self):
        """Test that cache invalidation errors are handled gracefully"""
        # Mock S3 cache to raise an exception
        with patch('tfm_cache_manager.get_s3_cache') as mock_get_s3_cache:
            mock_get_s3_cache.side_effect = Exception("Cache error")
            
            # Should not raise exception, but log warning
            self.cache_manager.invalidate_cache_for_paths([self.mock_s3_path], "test operation")
            
            # Should have logged a warning
            self.log_manager.add_message.assert_called()
            warning_calls = [call for call in self.log_manager.add_message.call_args_list 
                           if len(call[0]) > 1 and call[0][1] == "WARNING"]
            self.assertTrue(len(warning_calls) > 0)


if __name__ == '__main__':
    unittest.main()