#!/usr/bin/env python3
"""
Demo script showing S3 caching functionality in TFM

This script demonstrates:
1. Basic caching behavior for S3 operations
2. Cache invalidation after write operations
3. Cache expiration
4. Cache statistics and management
"""

import sys
import os
import time
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from tfm_s3 import (S3PathImpl, S3Cache, get_s3_cache, configure_s3_cache, 
                        clear_s3_cache, get_s3_cache_stats)
    from tfm_path import Path
    HAS_S3_SUPPORT = True
except ImportError as e:
    print(f"S3 support not available: {e}")
    HAS_S3_SUPPORT = False


def demo_basic_caching():
    """Demonstrate basic caching functionality"""
    print("=== Demo: Basic S3 Caching ===")
    
    # Configure cache with short TTL for demo
    configure_s3_cache(ttl=5, max_entries=100)
    
    cache = S3Cache(default_ttl=3)
    
    print("1. Testing cache miss and hit:")
    
    # Cache miss
    result = cache.get('head_object', 'demo-bucket', 'demo-key')
    print(f"   Cache miss result: {result}")
    
    # Store in cache
    test_data = {'ContentLength': 2048, 'LastModified': '2024-01-01T12:00:00Z'}
    cache.put('head_object', 'demo-bucket', 'demo-key', test_data)
    print(f"   Stored in cache: {test_data}")
    
    # Cache hit
    cached_result = cache.get('head_object', 'demo-bucket', 'demo-key')
    print(f"   Cache hit result: {cached_result}")
    print(f"   Cache hit successful: {cached_result == test_data}")
    
    print("\n2. Testing cache expiration:")
    print("   Waiting 3.5 seconds for cache to expire...")
    time.sleep(3.5)
    
    expired_result = cache.get('head_object', 'demo-bucket', 'demo-key')
    print(f"   After expiration: {expired_result}")
    print(f"   Cache expired successfully: {expired_result is None}")


def demo_cache_invalidation():
    """Demonstrate cache invalidation"""
    print("\n=== Demo: Cache Invalidation ===")
    
    cache = S3Cache(default_ttl=60)  # Long TTL to test invalidation
    
    # Add test data
    cache.put('head_object', 'bucket1', 'file1.txt', {'size': 100})
    cache.put('head_object', 'bucket1', 'file2.txt', {'size': 200})
    cache.put('head_object', 'bucket2', 'file1.txt', {'size': 300})
    cache.put('list_objects_v2', 'bucket1', '', {'files': ['file1.txt', 'file2.txt']})
    
    print("1. Initial cache state:")
    stats = cache.get_stats()
    print(f"   Total entries: {stats['total_entries']}")
    
    print("\n2. Testing key-specific invalidation:")
    cache.invalidate_key('bucket1', 'file1.txt')
    
    result1 = cache.get('head_object', 'bucket1', 'file1.txt')
    result2 = cache.get('head_object', 'bucket1', 'file2.txt')
    result3 = cache.get('head_object', 'bucket2', 'file1.txt')
    
    print(f"   bucket1/file1.txt (should be None): {result1}")
    print(f"   bucket1/file2.txt (should exist): {result2 is not None}")
    print(f"   bucket2/file1.txt (should exist): {result3 is not None}")
    
    print("\n3. Testing bucket-wide invalidation:")
    cache.invalidate_bucket('bucket1')
    
    result2_after = cache.get('head_object', 'bucket1', 'file2.txt')
    result_list = cache.get('list_objects_v2', 'bucket1', '')
    result3_after = cache.get('head_object', 'bucket2', 'file1.txt')
    
    print(f"   bucket1/file2.txt (should be None): {result2_after}")
    print(f"   bucket1 listing (should be None): {result_list}")
    print(f"   bucket2/file1.txt (should exist): {result3_after is not None}")


def demo_lru_eviction():
    """Demonstrate LRU eviction"""
    print("\n=== Demo: LRU Eviction ===")
    
    cache = S3Cache(default_ttl=60, max_entries=3)  # Small cache for demo
    
    print("1. Filling cache to capacity (3 entries):")
    for i in range(3):
        cache.put('head_object', 'bucket', f'file{i}.txt', {'id': i})
        print(f"   Added file{i}.txt")
    
    stats = cache.get_stats()
    print(f"   Cache entries: {stats['total_entries']}")
    
    print("\n2. Accessing file0.txt to make it recently used:")
    result = cache.get('head_object', 'bucket', 'file0.txt')
    print(f"   Retrieved file0.txt: {result}")
    
    print("\n3. Adding file3.txt (should trigger eviction):")
    cache.put('head_object', 'bucket', 'file3.txt', {'id': 3})
    
    print("\n4. Checking which entries remain:")
    for i in range(4):
        result = cache.get('head_object', 'bucket', f'file{i}.txt')
        status = "EXISTS" if result is not None else "EVICTED"
        print(f"   file{i}.txt: {status}")


@patch('tfm_s3.boto3')
def demo_s3_path_caching(mock_boto3):
    """Demonstrate caching with S3PathImpl"""
    print("\n=== Demo: S3PathImpl Caching Integration ===")
    
    # Configure cache
    configure_s3_cache(ttl=10, max_entries=100)
    clear_s3_cache()
    
    # Mock S3 client
    mock_client = Mock()
    mock_boto3.client.return_value = mock_client
    
    # Mock responses
    from datetime import datetime
    mock_client.head_object.return_value = {
        'ContentLength': 1024,
        'LastModified': datetime.now()
    }
    mock_client.list_objects_v2.return_value = {'KeyCount': 0}
    mock_client.put_object.return_value = {}
    
    # Create S3 path
    s3_path = S3PathImpl('s3://demo-bucket/demo-file.txt')
    
    print("1. First exists() call (should hit API):")
    result1 = s3_path.exists()
    print(f"   Result: {result1}")
    print(f"   API calls made: {mock_client.head_object.call_count}")
    
    print("\n2. Second exists() call (should use cache):")
    result2 = s3_path.exists()
    print(f"   Result: {result2}")
    print(f"   API calls made: {mock_client.head_object.call_count}")
    
    print("\n3. stat() call (should also use cache):")
    stat_result = s3_path.stat()
    print(f"   File size: {stat_result.st_size}")
    print(f"   API calls made: {mock_client.head_object.call_count}")
    
    print("\n4. Write operation (should invalidate cache):")
    s3_path.write_text("New content")
    print(f"   Write completed, put_object calls: {mock_client.put_object.call_count}")
    
    print("\n5. exists() call after write (should hit API again):")
    result3 = s3_path.exists()
    print(f"   Result: {result3}")
    print(f"   API calls made: {mock_client.head_object.call_count}")
    
    # Show cache stats
    stats = get_s3_cache_stats()
    print(f"\n6. Final cache stats:")
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Max entries: {stats['max_entries']}")
    print(f"   Default TTL: {stats['default_ttl']} seconds")


def demo_cache_management():
    """Demonstrate cache management functions"""
    print("\n=== Demo: Cache Management ===")
    
    print("1. Initial cache configuration:")
    stats = get_s3_cache_stats()
    print(f"   Default TTL: {stats['default_ttl']} seconds")
    print(f"   Max entries: {stats['max_entries']}")
    print(f"   Current entries: {stats['total_entries']}")
    
    print("\n2. Reconfiguring cache:")
    configure_s3_cache(ttl=30, max_entries=500)
    stats = get_s3_cache_stats()
    print(f"   New TTL: {stats['default_ttl']} seconds")
    print(f"   New max entries: {stats['max_entries']}")
    
    print("\n3. Adding some test entries:")
    cache = get_s3_cache()
    for i in range(5):
        cache.put('test_op', f'bucket{i}', f'key{i}', {'data': f'test{i}'})
    
    stats = get_s3_cache_stats()
    print(f"   Entries after adding: {stats['total_entries']}")
    
    print("\n4. Clearing cache:")
    clear_s3_cache()
    stats = get_s3_cache_stats()
    print(f"   Entries after clearing: {stats['total_entries']}")


def main():
    """Run all demos"""
    if not HAS_S3_SUPPORT:
        print("S3 support not available. Please install boto3 to run this demo.")
        return
    
    print("TFM S3 Caching System Demo")
    print("=" * 50)
    
    try:
        demo_basic_caching()
        demo_cache_invalidation()
        demo_lru_eviction()
        demo_s3_path_caching()
        demo_cache_management()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nKey benefits of S3 caching:")
        print("• Reduced API calls and improved response times")
        print("• Configurable TTL (default 60 seconds)")
        print("• Automatic cache invalidation on write operations")
        print("• LRU eviction to manage memory usage")
        print("• Thread-safe operations")
        print("• Comprehensive cache statistics")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()