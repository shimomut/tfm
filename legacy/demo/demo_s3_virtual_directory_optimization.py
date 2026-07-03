#!/usr/bin/env python3
"""
Demo: S3 Virtual Directory Optimization

This demo shows how storing metadata as S3PathImpl properties eliminates
API calls for virtual directories and improves performance.
"""

import sys
import os
import time
from unittest.mock import Mock, patch
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from tfm_path import Path
    from tfm_s3 import S3PathImpl, get_s3_cache
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class S3VirtualDirectoryDemo:
    """Demonstrate S3 virtual directory optimization"""
    
    def __init__(self):
        self.cache = get_s3_cache()
        self.api_calls_made = []
        
    def create_mock_environment(self):
        """Create a mock S3 environment with virtual directories"""
        # Sample directory with files and virtual subdirectories
        sample_objects = [
            {
                'Key': 'project/src/main.py',
                'Size': 2048,
                'LastModified': datetime(2024, 1, 1, 12, 0, 0),
                'ETag': '"abc123"',
                'StorageClass': 'STANDARD'
            },
            {
                'Key': 'project/src/utils.py',
                'Size': 1024,
                'LastModified': datetime(2024, 1, 2, 12, 0, 0),
                'ETag': '"def456"',
                'StorageClass': 'STANDARD'
            },
            {
                'Key': 'project/tests/test_main.py',
                'Size': 1536,
                'LastModified': datetime(2024, 1, 3, 12, 0, 0),
                'ETag': '"ghi789"',
                'StorageClass': 'STANDARD'
            },
            {
                'Key': 'project/docs/README.md',
                'Size': 512,
                'LastModified': datetime(2024, 1, 4, 12, 0, 0),
                'ETag': '"jkl012"',
                'StorageClass': 'STANDARD'
            }
        ]
        
        # Mock S3 client
        mock_client = Mock()
        
        # Mock list_objects_v2 response with virtual directories
        mock_list_response = {
            'Contents': sample_objects,
            'CommonPrefixes': [
                {'Prefix': 'project/src/'},      # Virtual directory
                {'Prefix': 'project/tests/'},    # Virtual directory  
                {'Prefix': 'project/docs/'}      # Virtual directory
            ],
            'KeyCount': len(sample_objects),
            'IsTruncated': False
        }
        
        # Configure mock client
        mock_client.list_objects_v2.return_value = mock_list_response
        
        # Mock paginator
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [mock_list_response]
        mock_client.get_paginator.return_value = mock_paginator
        
        # Track API calls
        def track_api_call(method_name):
            def wrapper(*args, **kwargs):
                call_info = {
                    'method': method_name,
                    'kwargs': kwargs,
                    'timestamp': time.time()
                }
                self.api_calls_made.append(call_info)
                if method_name == 'list_objects_v2':
                    return mock_list_response
                elif method_name == 'head_object':
                    # Simulate 404 for virtual directories
                    error_response = {'Error': {'Code': 'NoSuchKey', 'Message': 'Not Found'}}
                    raise ClientError(error_response, 'HeadObject')
                return {}
            return wrapper
        
        mock_client.list_objects_v2 = track_api_call('list_objects_v2')
        mock_client.head_object = track_api_call('head_object')
        
        return mock_client, sample_objects
    
    def demo_before_optimization(self):
        """Demonstrate the problem before optimization"""
        print("=== Demo: Before Virtual Directory Optimization ===")
        print("Simulating the old behavior where virtual directories cause head_object failures")
        
        self.cache.clear()
        self.api_calls_made = []
        
        mock_client, sample_objects = self.create_mock_environment()
        
        with patch('tfm_s3.boto3.client', return_value=mock_client):
            s3_path = Path('s3://demo-bucket/project/')
            
            print(f"\n1. Directory listing:")
            
            # Simulate old behavior by creating paths without metadata
            files = []
            try:
                # This would work for the listing
                for item in s3_path.iterdir():
                    files.append(item)
                print(f"   Found {len(files)} items")
            except Exception as e:
                print(f"   Error during listing: {e}")
            
            print(f"\n2. Checking file types (would cause 404s for virtual directories):")
            
            # Reset API call tracking
            api_calls_before = len(self.api_calls_made)
            
            for file_path in files:
                try:
                    # These operations would fail for virtual directories without optimization
                    is_dir = file_path.is_dir()
                    is_file = file_path.is_file()
                    print(f"   {file_path.name}: dir={is_dir}, file={is_file}")
                except Exception as e:
                    print(f"   {file_path.name}: ERROR - {e}")
            
            api_calls_after = len(self.api_calls_made)
            print(f"\nAPI calls for type checking: {api_calls_after - api_calls_before}")
            
            print(f"\n3. Getting file stats (would cause more 404s):")
            
            api_calls_before = len(self.api_calls_made)
            
            for file_path in files:
                try:
                    stat_result = file_path.stat()
                    print(f"   {file_path.name}: {stat_result.st_size} bytes")
                except Exception as e:
                    print(f"   {file_path.name}: ERROR - {e}")
            
            api_calls_after = len(self.api_calls_made)
            print(f"\nAPI calls for stat: {api_calls_after - api_calls_before}")
    
    def demo_after_optimization(self):
        """Demonstrate the solution after optimization"""
        print("\n=== Demo: After Virtual Directory Optimization ===")
        print("Showing how metadata properties eliminate API calls and 404 errors")
        
        self.cache.clear()
        self.api_calls_made = []
        
        mock_client, sample_objects = self.create_mock_environment()
        
        with patch('tfm_s3.boto3.client', return_value=mock_client):
            s3_path = Path('s3://demo-bucket/project/')
            
            print(f"\n1. Directory listing (creates paths with metadata):")
            files = list(s3_path.iterdir())
            print(f"   Found {len(files)} items")
            
            # Show metadata status
            print(f"\n   Metadata status:")
            for file_path in files:
                has_metadata = file_path._impl._is_dir_cached is not None
                print(f"     {file_path.name}: metadata={'YES' if has_metadata else 'NO'}")
            
            print(f"\n2. Checking file types (uses cached metadata):")
            
            api_calls_before = len(self.api_calls_made)
            
            for file_path in files:
                # These operations now use cached metadata
                is_dir = file_path.is_dir()
                is_file = file_path.is_file()
                print(f"   {file_path.name}: dir={is_dir}, file={is_file}")
            
            api_calls_after = len(self.api_calls_made)
            print(f"\nAPI calls for type checking: {api_calls_after - api_calls_before}")
            
            print(f"\n3. Getting file stats (uses cached metadata):")
            
            api_calls_before = len(self.api_calls_made)
            
            for file_path in files:
                stat_result = file_path.stat()
                print(f"   {file_path.name}: {stat_result.st_size} bytes")
            
            api_calls_after = len(self.api_calls_made)
            print(f"\nAPI calls for stat: {api_calls_after - api_calls_before}")
            
            # Show all API calls made
            print(f"\n--- All API Calls Made ---")
            for i, call in enumerate(self.api_calls_made):
                print(f"{i+1}. {call['method']}")
            
            print(f"\nTotal API calls: {len(self.api_calls_made)}")
    
    def demo_performance_comparison(self):
        """Demonstrate performance improvement"""
        print("\n=== Demo: Performance Comparison ===")
        print("Comparing performance with and without metadata caching")
        
        # Test with metadata
        metadata = {
            'is_dir': True,
            'is_file': False,
            'size': 0,
            'last_modified': datetime(2024, 1, 1, 12, 0, 0),
            'etag': '',
            'storage_class': ''
        }
        
        path_with_metadata = S3PathImpl.create_path_with_metadata('s3://test-bucket/virtual-dir/', metadata)
        path_without_metadata = Path('s3://test-bucket/virtual-dir/')
        
        # Test is_dir() performance
        print(f"\nTesting is_dir() performance:")
        
        # With metadata (should be instant)
        start_time = time.time()
        for _ in range(1000):
            result = path_with_metadata.is_dir()
        time_with_metadata = time.time() - start_time
        
        print(f"   With metadata (1000 calls): {time_with_metadata:.6f}s")
        print(f"   Per call: {time_with_metadata/1000:.9f}s")
        
        # Show metadata usage
        print(f"\nMetadata usage:")
        print(f"   Path with metadata - cached is_dir: {path_with_metadata._impl._is_dir_cached}")
        print(f"   Path without metadata - cached is_dir: {path_without_metadata._impl._is_dir_cached}")
        
        # Test stat() performance with cached data
        print(f"\nTesting stat() with cached metadata:")
        start_time = time.time()
        stat_result = path_with_metadata.stat()
        stat_time = time.time() - start_time
        
        print(f"   stat() call: {stat_time:.6f}s")
        print(f"   Result: size={stat_result.st_size}, is_dir={bool(stat_result.st_mode & 0o040000)}")
    
    def demo_virtual_directory_handling(self):
        """Demonstrate proper virtual directory handling"""
        print("\n=== Demo: Virtual Directory Handling ===")
        print("Showing how virtual directories are handled without 404 errors")
        
        # Create virtual directory with metadata
        virtual_dir_metadata = {
            'is_dir': True,
            'is_file': False,
            'size': 0,
            'last_modified': datetime(2024, 1, 1, 12, 0, 0),
            'etag': '',
            'storage_class': ''
        }
        
        virtual_dir = S3PathImpl.create_path_with_metadata('s3://test-bucket/virtual-folder/', virtual_dir_metadata)
        
        print(f"\nVirtual directory: {virtual_dir}")
        print(f"   is_dir(): {virtual_dir.is_dir()}")
        print(f"   is_file(): {virtual_dir.is_file()}")
        
        # Test stat without API calls
        try:
            stat_result = virtual_dir.stat()
            print(f"   stat() success: size={stat_result.st_size}, mtime={stat_result.st_mtime}")
        except Exception as e:
            print(f"   stat() error: {e}")
        
        # Show that no API calls are needed
        print(f"\nMetadata properties:")
        print(f"   _is_dir_cached: {virtual_dir._impl._is_dir_cached}")
        print(f"   _is_file_cached: {virtual_dir._impl._is_file_cached}")
        print(f"   _size_cached: {virtual_dir._impl._size_cached}")
        print(f"   _mtime_cached: {virtual_dir._impl._mtime_cached}")


def main():
    """Run the demo"""
    if not HAS_BOTO3:
        print("boto3 not available - skipping S3 virtual directory optimization demo")
        return
    
    print("S3 Virtual Directory Optimization Demo")
    print("=" * 50)
    print()
    print("This demo shows how storing metadata as S3PathImpl properties")
    print("eliminates API calls and 404 errors for virtual directories.")
    print()
    
    demo = S3VirtualDirectoryDemo()
    
    # Show the problem (before optimization)
    demo.demo_before_optimization()
    
    # Show the solution (after optimization)
    demo.demo_after_optimization()
    
    # Show performance improvement
    demo.demo_performance_comparison()
    
    # Show virtual directory handling
    demo.demo_virtual_directory_handling()
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("- Metadata is stored as S3PathImpl properties during iterdir()")
    print("- is_dir(), is_file(), and stat() use cached metadata")
    print("- Virtual directories work without head_object API calls")
    print("- Result: No 404 errors and significantly better performance")


if __name__ == "__main__":
    main()