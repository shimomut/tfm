#!/usr/bin/env python3
"""
Demo: S3 iterdir Caching Improvement

This demo shows how the improved iterdir() method caches complete directory
listings and avoids API calls on subsequent access.
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
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class S3IterdirCachingDemo:
    """Demonstrate S3 iterdir caching improvement"""
    
    def __init__(self):
        self.cache = get_s3_cache()
        self.api_calls_made = []
        
    def create_mock_environment(self):
        """Create a mock S3 environment with multiple pages"""
        # Sample directory with many files (simulating large directory)
        sample_objects_page1 = [
            {
                'Key': 'large-project/src/main.py',
                'Size': 2048,
                'LastModified': datetime(2024, 1, 1, 12, 0, 0),
                'ETag': '"abc123"',
                'StorageClass': 'STANDARD'
            },
            {
                'Key': 'large-project/src/utils.py',
                'Size': 1024,
                'LastModified': datetime(2024, 1, 2, 12, 0, 0),
                'ETag': '"def456"',
                'StorageClass': 'STANDARD'
            },
            {
                'Key': 'large-project/src/config.py',
                'Size': 512,
                'LastModified': datetime(2024, 1, 3, 12, 0, 0),
                'ETag': '"ghi789"',
                'StorageClass': 'STANDARD'
            }
        ]
        
        sample_objects_page2 = [
            {
                'Key': 'large-project/tests/test_main.py',
                'Size': 1536,
                'LastModified': datetime(2024, 1, 4, 12, 0, 0),
                'ETag': '"jkl012"',
                'StorageClass': 'STANDARD'
            },
            {
                'Key': 'large-project/tests/test_utils.py',
                'Size': 768,
                'LastModified': datetime(2024, 1, 5, 12, 0, 0),
                'ETag': '"mno345"',
                'StorageClass': 'STANDARD'
            }
        ]
        
        # Mock S3 client
        mock_client = Mock()
        
        # Mock paginated responses (simulating large directory)
        page1 = {
            'Contents': sample_objects_page1,
            'CommonPrefixes': [{'Prefix': 'large-project/src/'}],
            'KeyCount': len(sample_objects_page1),
            'IsTruncated': True
        }
        
        page2 = {
            'Contents': sample_objects_page2,
            'CommonPrefixes': [{'Prefix': 'large-project/tests/'}],
            'KeyCount': len(sample_objects_page2),
            'IsTruncated': False
        }
        
        # Mock paginator
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [page1, page2]
        mock_client.get_paginator.return_value = mock_paginator
        
        # Track API calls
        def track_paginate(*args, **kwargs):
            call_info = {
                'method': 'paginate',
                'args': args,
                'kwargs': kwargs,
                'timestamp': time.time()
            }
            self.api_calls_made.append(call_info)
            return [page1, page2]
        
        def track_get_paginator(*args, **kwargs):
            call_info = {
                'method': 'get_paginator',
                'args': args,
                'kwargs': kwargs,
                'timestamp': time.time()
            }
            self.api_calls_made.append(call_info)
            return mock_paginator
        
        mock_client.get_paginator = track_get_paginator
        mock_paginator.paginate = track_paginate
        
        return mock_client, sample_objects_page1 + sample_objects_page2
    
    def demo_before_improvement(self):
        """Show what the old method was doing"""
        print("=== Before Improvement ===")
        print("The old iterdir() method had these issues:")
        print("1. Always created paginator and made API calls")
        print("2. Cached individual pages instead of complete listing")
        print("3. No cache check before making API calls")
        print("4. Repeated calls would still make some API calls")
        print()
        print("Problems:")
        print("- Inefficient for repeated directory access")
        print("- Multiple API calls even with partial caching")
        print("- Complex page-based cache management")
        print("- Poor performance for large directories")
    
    def demo_after_improvement(self):
        """Show what the new method does"""
        print("\n=== After Improvement ===")
        print("The new iterdir() method is optimized:")
        print("1. Checks for cached complete listing FIRST")
        print("2. Only makes API calls if no cache exists")
        print("3. Aggregates ALL pages into single cached result")
        print("4. Subsequent calls use cache with ZERO API calls")
        print()
        print("Benefits:")
        print("- Complete cache avoidance for repeated access")
        print("- Single cached entry per directory")
        print("- Optimal performance for large directories")
        print("- Simpler cache management")
    
    def demo_caching_behavior(self):
        """Demonstrate the improved caching behavior"""
        print("\n=== Caching Behavior Demo ===")
        
        self.cache.clear()
        self.api_calls_made = []
        
        mock_client, sample_objects = self.create_mock_environment()
        
        with patch('tfm_s3.boto3.client', return_value=mock_client):
            s3_path = Path('s3://demo-bucket/large-project/')
            
            print(f"Directory: {s3_path}")
            
            # First call - should make API calls and cache complete listing
            print(f"\n1. First iterdir() call (cache miss):")
            start_time = time.time()
            files1 = list(s3_path.iterdir())
            first_call_time = time.time() - start_time
            
            print(f"   Found {len(files1)} items")
            print(f"   Time taken: {first_call_time:.6f} seconds")
            print(f"   API calls made: {len(self.api_calls_made)}")
            
            # Show what was cached
            cache_entry = self.cache.get(
                operation='list_objects_v2_complete',
                bucket='demo-bucket',
                key='large-project/',
                prefix='large-project/',
                delimiter='/',
                complete_listing=True
            )
            
            if cache_entry:
                print(f"   Cached complete listing:")
                print(f"     Contents: {len(cache_entry['Contents'])} files")
                print(f"     CommonPrefixes: {len(cache_entry['CommonPrefixes'])} directories")
            
            # Reset API call tracking
            api_calls_first = len(self.api_calls_made)
            
            # Second call - should use cache with NO API calls
            print(f"\n2. Second iterdir() call (cache hit):")
            start_time = time.time()
            files2 = list(s3_path.iterdir())
            second_call_time = time.time() - start_time
            
            print(f"   Found {len(files2)} items")
            print(f"   Time taken: {second_call_time:.6f} seconds")
            print(f"   API calls made: {len(self.api_calls_made) - api_calls_first}")
            
            # Third call - should also use cache
            print(f"\n3. Third iterdir() call (cache hit):")
            start_time = time.time()
            files3 = list(s3_path.iterdir())
            third_call_time = time.time() - start_time
            
            print(f"   Found {len(files3)} items")
            print(f"   Time taken: {third_call_time:.6f} seconds")
            print(f"   API calls made: {len(self.api_calls_made) - api_calls_first}")
            
            # Show performance improvement
            print(f"\nPerformance Summary:")
            print(f"   First call (with API): {first_call_time:.6f}s")
            print(f"   Second call (cached): {second_call_time:.6f}s")
            print(f"   Third call (cached): {third_call_time:.6f}s")
            
            if first_call_time > 0:
                improvement2 = (1 - second_call_time / first_call_time) * 100
                improvement3 = (1 - third_call_time / first_call_time) * 100
                print(f"   Improvement: {improvement2:.1f}% and {improvement3:.1f}%")
    
    def demo_aggregated_caching(self):
        """Demonstrate aggregated caching from multiple pages"""
        print("\n=== Aggregated Caching Demo ===")
        
        self.cache.clear()
        self.api_calls_made = []
        
        mock_client, sample_objects = self.create_mock_environment()
        
        with patch('tfm_s3.boto3.client', return_value=mock_client):
            s3_path = Path('s3://demo-bucket/large-project/')
            
            print("Simulating large directory with multiple S3 pages...")
            
            # Call iterdir - should aggregate all pages
            files = list(s3_path.iterdir())
            
            print(f"Total items found: {len(files)}")
            print(f"API calls made: {len(self.api_calls_made)}")
            
            # Show the aggregated cache entry
            cache_entry = self.cache.get(
                operation='list_objects_v2_complete',
                bucket='demo-bucket',
                key='large-project/',
                prefix='large-project/',
                delimiter='/',
                complete_listing=True
            )
            
            if cache_entry:
                print(f"\nAggregated cache entry:")
                print(f"  Total Contents: {len(cache_entry['Contents'])}")
                print(f"  Total CommonPrefixes: {len(cache_entry['CommonPrefixes'])}")
                print(f"  Files from all pages combined:")
                
                for i, obj in enumerate(cache_entry['Contents']):
                    print(f"    {i+1}. {obj['Key']} ({obj['Size']} bytes)")
                
                print(f"  Directories:")
                for i, prefix in enumerate(cache_entry['CommonPrefixes']):
                    print(f"    {i+1}. {prefix['Prefix']}")
            
            # Verify subsequent calls use the aggregated cache
            print(f"\nTesting subsequent calls use aggregated cache:")
            api_calls_before = len(self.api_calls_made)
            
            files2 = list(s3_path.iterdir())
            
            api_calls_after = len(self.api_calls_made)
            print(f"  Additional API calls: {api_calls_after - api_calls_before}")
            print(f"  Same results: {len(files) == len(files2)}")
    
    def demo_cache_efficiency(self):
        """Demonstrate cache efficiency"""
        print("\n=== Cache Efficiency Demo ===")
        
        # Test multiple directories
        directories = [
            's3://demo-bucket/project1/',
            's3://demo-bucket/project2/',
            's3://demo-bucket/project3/'
        ]
        
        self.cache.clear()
        
        print("Testing cache efficiency with multiple directories:")
        
        for i, dir_path in enumerate(directories):
            print(f"\n{i+1}. Directory: {dir_path}")
            
            # Simulate cache entry for this directory
            cache_entry = {
                'Contents': [
                    {
                        'Key': f'project{i+1}/file1.txt',
                        'Size': 1024,
                        'LastModified': datetime.now(),
                        'ETag': f'"etag{i+1}"',
                        'StorageClass': 'STANDARD'
                    }
                ],
                'CommonPrefixes': [],
                'KeyCount': 1,
                'Prefix': f'project{i+1}/',
                'Delimiter': '/'
            }
            
            # Cache the entry
            self.cache.put(
                operation='list_objects_v2_complete',
                bucket='demo-bucket',
                key=f'project{i+1}/',
                data=cache_entry,
                prefix=f'project{i+1}/',
                delimiter='/',
                complete_listing=True
            )
            
            print(f"   Cached complete listing for project{i+1}")
        
        # Show cache statistics
        cache_stats = self.cache.get_stats()
        print(f"\nCache Statistics:")
        print(f"  Total entries: {cache_stats['total_entries']}")
        print(f"  Max entries: {cache_stats['max_entries']}")
        print(f"  Default TTL: {cache_stats['default_ttl']} seconds")
        
        # Test cache retrieval performance
        print(f"\nTesting cache retrieval performance:")
        
        for i, dir_path in enumerate(directories):
            start_time = time.time()
            
            cached_entry = self.cache.get(
                operation='list_objects_v2_complete',
                bucket='demo-bucket',
                key=f'project{i+1}/',
                prefix=f'project{i+1}/',
                delimiter='/',
                complete_listing=True
            )
            
            retrieval_time = time.time() - start_time
            
            print(f"  {dir_path}: {retrieval_time:.9f}s ({'HIT' if cached_entry else 'MISS'})")


def main():
    """Run the demo"""
    if not HAS_BOTO3:
        print("boto3 not available - skipping S3 iterdir caching improvement demo")
        return
    
    print("S3 iterdir Caching Improvement Demo")
    print("=" * 45)
    print()
    print("This demo shows how the improved iterdir() method caches")
    print("complete directory listings and avoids API calls.")
    print()
    
    demo = S3IterdirCachingDemo()
    
    # Show before and after
    demo.demo_before_improvement()
    demo.demo_after_improvement()
    
    # Show caching behavior
    demo.demo_caching_behavior()
    
    # Show aggregated caching
    demo.demo_aggregated_caching()
    
    # Show cache efficiency
    demo.demo_cache_efficiency()
    
    print("\n" + "=" * 45)
    print("Summary:")
    print("- Complete listing cached instead of individual pages")
    print("- Zero API calls for cached directory access")
    print("- Aggregated results from all pages in single cache entry")
    print("- Significant performance improvement for repeated access")
    print("- Simpler and more efficient cache management")


if __name__ == "__main__":
    main()