#!/usr/bin/env python3
"""
Test S3 virtual directory stats functionality.

This test verifies that virtual directories (directories without actual S3 objects)
display "0B" as size and the latest timestamp of their children.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from tfm_s3 import S3PathImpl, S3StatResult
except ImportError as e:
    print(f"Failed to import S3 modules: {e}")
    print("This test requires the S3 modules to be available")
    sys.exit(1)


class TestS3VirtualDirectoryStats(unittest.TestCase):
    """Test S3 virtual directory stats functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock boto3 to avoid requiring AWS credentials
        self.mock_boto3 = Mock()
        self.mock_s3_client = Mock()
        self.mock_boto3.client.return_value = self.mock_s3_client
        
        # Patch boto3 import
        self.boto3_patcher = patch('tfm_s3.boto3', self.mock_boto3)
        self.boto3_patcher.start()
        
        # Patch HAS_BOTO3 to True
        self.has_boto3_patcher = patch('tfm_s3.HAS_BOTO3', True)
        self.has_boto3_patcher.start()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.boto3_patcher.stop()
        self.has_boto3_patcher.stop()
    
    def test_virtual_directory_stats_with_children(self):
        """Test that virtual directories return 0B size and latest child timestamp"""
        # Create S3 path for virtual directory
        s3_path = S3PathImpl('s3://test-bucket/virtual-dir/')
        
        # Mock head_object to raise NoSuchKey (virtual directory has no actual object)
        self.mock_s3_client.head_object.side_effect = Exception("NoSuchKey")
        
        # Create mock response with child objects
        child1_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        child2_time = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)  # Latest
        child3_time = datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc)
        
        mock_list_response = {
            'Contents': [
                {
                    'Key': 'virtual-dir/file1.txt',
                    'LastModified': child1_time,
                    'Size': 100
                },
                {
                    'Key': 'virtual-dir/file2.txt', 
                    'LastModified': child2_time,
                    'Size': 200
                },
                {
                    'Key': 'virtual-dir/subdir/file3.txt',
                    'LastModified': child3_time,
                    'Size': 150
                }
            ],
            'IsTruncated': False
        }
        
        # Mock list_objects_v2 to return child objects
        self.mock_s3_client.list_objects_v2.return_value = mock_list_response
        
        # Mock is_dir to return True (this is a virtual directory)
        with patch.object(s3_path, 'is_dir', return_value=True):
            # Get stats for virtual directory
            size, mtime = s3_path._get_virtual_directory_stats()
            
            # Verify size is 0 (0B)
            self.assertEqual(size, 0)
            
            # Verify mtime is the latest child timestamp
            expected_mtime = child2_time.timestamp()
            self.assertEqual(mtime, expected_mtime)
    
    def test_virtual_directory_stats_no_children(self):
        """Test virtual directory stats when no children exist"""
        s3_path = S3PathImpl('s3://test-bucket/empty-virtual-dir/')
        
        # Mock list_objects_v2 to return empty response
        mock_list_response = {
            'Contents': [],
            'IsTruncated': False
        }
        self.mock_s3_client.list_objects_v2.return_value = mock_list_response
        
        # Get current time before the call
        before_time = time.time()
        
        # Get stats for empty virtual directory
        size, mtime = s3_path._get_virtual_directory_stats()
        
        # Get current time after the call
        after_time = time.time()
        
        # Verify size is 0
        self.assertEqual(size, 0)
        
        # Verify mtime is current time (within reasonable range)
        self.assertGreaterEqual(mtime, before_time)
        self.assertLessEqual(mtime, after_time)
    
    def test_virtual_directory_stats_paginated_results(self):
        """Test virtual directory stats with paginated results"""
        s3_path = S3PathImpl('s3://test-bucket/large-virtual-dir/')
        
        # Create timestamps
        early_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        latest_time = datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc)  # Latest
        
        # Mock first response (truncated)
        first_response = {
            'Contents': [
                {
                    'Key': 'large-virtual-dir/file1.txt',
                    'LastModified': early_time,
                    'Size': 100
                }
            ],
            'IsTruncated': True
        }
        
        # Mock paginated responses
        page1 = {
            'Contents': [
                {
                    'Key': 'large-virtual-dir/file2.txt',
                    'LastModified': early_time,
                    'Size': 200
                }
            ]
        }
        
        page2 = {
            'Contents': [
                {
                    'Key': 'large-virtual-dir/file3.txt',
                    'LastModified': latest_time,  # This should be the latest
                    'Size': 300
                }
            ]
        }
        
        # Mock list_objects_v2 first call
        self.mock_s3_client.list_objects_v2.return_value = first_response
        
        # Mock paginator
        mock_paginator = Mock()
        mock_page_iterator = [page1, page2]
        mock_paginator.paginate.return_value = mock_page_iterator
        self.mock_s3_client.get_paginator.return_value = mock_paginator
        
        # Get stats for large virtual directory
        size, mtime = s3_path._get_virtual_directory_stats()
        
        # Verify size is 0
        self.assertEqual(size, 0)
        
        # Verify mtime is the latest timestamp from all pages
        expected_mtime = latest_time.timestamp()
        self.assertEqual(mtime, expected_mtime)
    
    def test_stat_method_with_virtual_directory(self):
        """Test that stat() method properly handles virtual directories"""
        s3_path = S3PathImpl('s3://test-bucket/virtual-dir/')
        
        # Mock head_object to raise ClientError with NoSuchKey
        from botocore.exceptions import ClientError
        error_response = {'Error': {'Code': 'NoSuchKey'}}
        self.mock_s3_client.head_object.side_effect = ClientError(error_response, 'head_object')
        
        # Mock is_dir to return True
        with patch.object(s3_path, 'is_dir', return_value=True):
            # Mock _get_virtual_directory_stats
            test_size = 0
            test_mtime = 1640995200.0  # 2022-01-01 00:00:00 UTC
            
            with patch.object(s3_path, '_get_virtual_directory_stats', return_value=(test_size, test_mtime)):
                # Call stat method
                stat_result = s3_path.stat()
                
                # Verify it returns S3StatResult with correct values
                self.assertIsInstance(stat_result, S3StatResult)
                self.assertEqual(stat_result.st_size, test_size)
                self.assertEqual(stat_result.st_mtime, test_mtime)
                self.assertTrue(stat_result.st_mode & 0o040000)  # Directory mode
    
    def test_stat_method_with_actual_object(self):
        """Test that stat() method works normally for actual S3 objects"""
        s3_path = S3PathImpl('s3://test-bucket/actual-file.txt')
        
        # Mock head_object to return successful response
        test_size = 1024
        test_mtime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        mock_response = {
            'ContentLength': test_size,
            'LastModified': test_mtime
        }
        self.mock_s3_client.head_object.return_value = mock_response
        
        # Mock is_dir to return False
        with patch.object(s3_path, 'is_dir', return_value=False):
            # Call stat method
            stat_result = s3_path.stat()
            
            # Verify it returns S3StatResult with correct values
            self.assertIsInstance(stat_result, S3StatResult)
            self.assertEqual(stat_result.st_size, test_size)
            self.assertEqual(stat_result.st_mtime, test_mtime.timestamp())
            self.assertFalse(stat_result.st_mode & 0o040000)  # Not directory mode
    
    def test_client_error_handling(self):
        """Test that ClientError is handled properly in _get_virtual_directory_stats"""
        s3_path = S3PathImpl('s3://test-bucket/error-dir/')
        
        # Mock list_objects_v2 to raise ClientError
        from botocore.exceptions import ClientError
        error_response = {'Error': {'Code': 'AccessDenied'}}
        self.mock_s3_client.list_objects_v2.side_effect = ClientError(error_response, 'list_objects_v2')
        
        # Get stats - should return defaults without raising exception
        size, mtime = s3_path._get_virtual_directory_stats()
        
        # Verify defaults are returned
        self.assertEqual(size, 0)
        self.assertIsInstance(mtime, float)
        self.assertGreater(mtime, 0)


if __name__ == '__main__':
    unittest.main()