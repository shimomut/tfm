#!/usr/bin/env python3
"""
Demo: S3 Cache Fix

This demo shows how the S3 cache fix prevents 404 errors and ensures
that stat information cached during directory listings is properly used.
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
    from tfm_s3 import get_s3_cache
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class S3CacheFixDemo:
    """Demonstrate S3 cache fix"""
    
    def __init__(self):
        self.cache = get_s3_cache()
        self.api_calls_made = []
        
    def create_mock_environment(self):
        """Create a mock S3 environment for testing"""
        # Sample directory with files
        sample_objects = [
            {
                'Key': 'demo-folder/document1.pdf',
                'Size': 5120,
                'LastModified': datetime(2024, 1, 1, 12, 0, 0),
                'ETag': '"abc123"',
                'StorageClass': 'STANDARD'
            },
            {
                'Key': 'demo-folder/image1.jpg',
                'Size': 2048,
                'LastModified': datetime(2024, 1, 2, 12, 0, 0),
                'ETag': '"def456"',
                'StorageClass': 'STANDARD'
            },
            {
                'Key': 'demo-folder/data.csv',
                'Size': 8192,
                'LastModified': datetime(2024, 1, 3, 12, 0, 0),
                'ETag': '"ghi789"',
                'StorageClass': 'STANDARD'
            }
        ]
        
        # Mock S3 client
        mock_client = Mock()
        
        # Mock list_objects_v2 response
        mock_list_response = {
            'Contents': sample_objects,
            'CommonPrefixes': [],
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
                return mock_list_response if method_name == 'list_objects_v2' else {}
            return wrapper
        
        mock_client.list_objects_v2 = track_api_call('list_objects_v2')
        mock_client.head_object = track_api_call('head_object')
        
        return mock_client, sample_objects
    
    def demo_before_fix(self):
        """Demonstrate the problem before the fix"""
        print("=== Demo: Before Cache Fix ===")
        print("Simulating the old behavior where stat() calls would make head_object API calls")
        
        self.cache.clear()
        self.api_calls_made = []
        
        mock_client, sample_objects = self.create_mock_environment()
        
        # Configure head_object to raise 404 errors (simulating the problem)
        error_response = {'Error': {'Code': 'NoSuchKey', 'Message': 'Not Found'}}
        mock_client.head_object.side_effect = ClientError(error_response, 'HeadObject')
        
        with patch('tfm_s3.boto3.client', return_value=mock_client):
            s3_path = Path('s3://demo-bucket/demo-folder/')
            
            print(f"\n1. Directory listing:")
            files = list(s3_path.iterdir())
            print(f"   Found {len(files)} files")
            
            print(f"\n2. Attempting to get file info (would fail with 404s before fix):")
            
            # Simulate old behavior by clearing cache after directory listing
            # This simulates the bug where stat info wasn't cached properly
            self.cache.clear()
            
            for file_path in files:
                if file_path.is_file():
                    try:
                        stat_result = file_path.stat()
                        print(f"   ✓ {file_path.name}: {stat_result.st_size} bytes")
                    except Exception as e:
                        print(f"   ✗ {file_path.name}: ERROR - {e}")
            
            print(f"\nAPI calls made: {len(self.api_calls_made)}")
            for call in self.api_calls_made:
                print(f"   - {call['method']}")
    
    def demo_after_fix(self):
        """Demonstrate the solution after the fix"""
        print("\n=== Demo: After Cache Fix ===")
        print("Showing how the fix caches stat info and prevents 404 errors")
        
        self.cache.clear()
        self.api_calls_made = []
        
        mock_client, sample_objects = self.create_mock_environment()
        
        # Configure head_object to raise 404 errors (but cache should prevent calls)
        error_response = {'Error': {'Code': 'NoSuchKey', 'Message': 'Not Found'}}
        mock_client.head_object.side_effect = ClientError(error_response, 'HeadObject')
        
        with patch('tfm_s3.boto3.client', return_value=mock_client):
            s3_path = Path('s3://demo-bucket/demo-folder/')
            
            print(f"\n1. Directory listing (caches stat info):")
            files = list(s3_path.iterdir())
            print(f"   Found {len(files)} files")
            
            # Show cache contents
            cache_entries = self.cache._cache
            head_object_entries = sum(1 for entry in cache_entries.values() 
                                    if entry['operation'] == 'head_object')
            print(f"   Cached {head_object_entries} head_object entries")
            
            print(f"\n2. Getting file info (uses cached data):")
            
            for file_path in files:
                if file_path.is_file():
                    try:
                        # Check if cached before calling stat
                        cached_head = self.cache.get('head_object', file_path._impl._bucket, file_path._impl._key)
                        cache_status = "CACHED" if cached_head else "NOT CACHED"
                        
                        stat_result = file_path.stat()
                        print(f"   ✓ {file_path.name}: {stat_result.st_size} bytes ({cache_status})")
                    except Exception as e:
                        print(f"   ✗ {file_path.name}: ERROR - {e}")
            
            print(f"\nAPI calls made: {len(self.api_calls_made)}")
            for call in self.api_calls_made:
                print(f"   - {call['method']}")
            
            # Count head_object calls (should be 0 with the fix)
            head_object_calls = sum(1 for call in self.api_calls_made if call['method'] == 'head_object')
            print(f"\nhead_object API calls: {head_object_calls} (should be 0 with fix)")
    
    def demo_cache_effectiveness(self):
        """Demonstrate cache effectiveness"""
        print("\n=== Demo: Cache Effectiveness ===")
        print("Showing cache hit rates and performance improvement")
        
        self.cache.clear()
        self.api_calls_made = []
        
        mock_client, sample_objects = self.create_mock_environment()
        
        with patch('tfm_s3.boto3.client', return_value=mock_client):
            s3_path = Path('s3://demo-bucket/demo-folder/')
            
            # First access - populates cache
            print(f"\nFirst access (populates cache):")
            start_time = time.time()
            files = list(s3_path.iterdir())
            for file_path in files:
                if file_path.is_file():
                    file_path.stat()
            first_time = time.time() - start_time
            first_api_calls = len(self.api_calls_made)
            
            print(f"   Time: {first_time:.3f}s")
            print(f"   API calls: {first_api_calls}")
            
            # Second access - uses cache
            print(f"\nSecond access (uses cache):")
            start_time = time.time()
            files = list(s3_path.iterdir())
            for file_path in files:
                if file_path.is_file():
                    file_path.stat()
            second_time = time.time() - start_time
            second_api_calls = len(self.api_calls_made) - first_api_calls
            
            print(f"   Time: {second_time:.3f}s")
            print(f"   API calls: {second_api_calls}")
            
            # Show improvement
            if first_api_calls > 0:
                api_reduction = (1 - second_api_calls / first_api_calls) * 100
                print(f"\nImprovement:")
                print(f"   API call reduction: {api_reduction:.1f}%")
            
            if first_time > 0:
                time_improvement = (1 - second_time / first_time) * 100
                print(f"   Time improvement: {time_improvement:.1f}%")


def main():
    """Run the demo"""
    if not HAS_BOTO3:
        print("boto3 not available - skipping S3 cache fix demo")
        return
    
    print("S3 Cache Fix Demo")
    print("=" * 40)
    print()
    print("This demo shows how the S3 cache fix prevents 404 errors")
    print("by properly caching stat information from directory listings.")
    print()
    
    demo = S3CacheFixDemo()
    
    # Show the problem (before fix)
    demo.demo_before_fix()
    
    # Show the solution (after fix)
    demo.demo_after_fix()
    
    # Show cache effectiveness
    demo.demo_cache_effectiveness()
    
    print("\n" + "=" * 40)
    print("Summary:")
    print("- The fix caches head_object data during directory listings")
    print("- This prevents 404 errors when stat() is called later")
    print("- Result: Reliable file information display and better performance")
    print("- Cache keys are now consistent between iterdir() and stat() calls")


if __name__ == "__main__":
    main()