#!/usr/bin/env python3
"""
Demo: S3 Cache Invalidation

This demo shows how TFM invalidates S3 cache after file and archive operations
to ensure directory listings are refreshed correctly.
"""

import sys
import os
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_cache_manager import CacheManager


def demo_cache_invalidation():
    """Demonstrate S3 cache invalidation functionality"""
    print("=== TFM S3 Cache Invalidation Demo ===\n")
    
    # Create cache manager
    cache_manager = CacheManager()
    
    # Mock S3 cache
    mock_s3_cache = Mock()
    mock_s3_cache.invalidate_key = Mock()
    
    print("1. Setting up mock S3 paths...")
    
    # Create mock S3 paths
    def create_mock_s3_path(bucket, key):
        path = Mock()
        path.get_scheme.return_value = 's3'
        path._impl = Mock()
        path._impl._bucket = bucket
        path._impl._key = key
        path.name = key.split('/')[-1] if key else bucket
        return path
    
    # Create test paths
    source_file = create_mock_s3_path('my-bucket', 'documents/report.pdf')
    source_dir = create_mock_s3_path('my-bucket', 'documents/')
    dest_dir = create_mock_s3_path('my-bucket', 'backup/')
    archive_path = create_mock_s3_path('my-bucket', 'archives/backup.zip')
    
    # Set up parent relationships
    source_parent = create_mock_s3_path('my-bucket', 'documents/')
    source_file.parent = source_parent
    
    archive_parent = create_mock_s3_path('my-bucket', 'archives/')
    archive_path.parent = archive_parent
    
    print(f"   Source file: s3://{source_file._impl._bucket}/{source_file._impl._key}")
    print(f"   Destination: s3://{dest_dir._impl._bucket}/{dest_dir._impl._key}")
    print(f"   Archive:     s3://{archive_path._impl._bucket}/{archive_path._impl._key}")
    print()
    
    # Patch the S3 cache
    with patch('tfm_cache_manager.get_s3_cache', return_value=mock_s3_cache):
        
        print("2. Demonstrating copy operation cache invalidation...")
        cache_manager.invalidate_cache_for_copy_operation([source_file], dest_dir)
        
        print("   Cache invalidation calls for copy operation:")
        for call in mock_s3_cache.invalidate_key.call_args_list:
            bucket, key = call[0]
            print(f"     - Invalidated: s3://{bucket}/{key}")
        
        mock_s3_cache.reset_mock()
        print()
        
        print("3. Demonstrating move operation cache invalidation...")
        cache_manager.invalidate_cache_for_move_operation([source_file], dest_dir)
        
        print("   Cache invalidation calls for move operation:")
        for call in mock_s3_cache.invalidate_key.call_args_list:
            bucket, key = call[0]
            print(f"     - Invalidated: s3://{bucket}/{key}")
        
        mock_s3_cache.reset_mock()
        print()
        
        print("4. Demonstrating delete operation cache invalidation...")
        cache_manager.invalidate_cache_for_delete_operation([source_file])
        
        print("   Cache invalidation calls for delete operation:")
        for call in mock_s3_cache.invalidate_key.call_args_list:
            bucket, key = call[0]
            print(f"     - Invalidated: s3://{bucket}/{key}")
        
        mock_s3_cache.reset_mock()
        print()
        
        print("5. Demonstrating archive operation cache invalidation...")
        cache_manager.invalidate_cache_for_archive_operation(archive_path, [source_file])
        
        print("   Cache invalidation calls for archive operation:")
        for call in mock_s3_cache.invalidate_key.call_args_list:
            bucket, key = call[0]
            print(f"     - Invalidated: s3://{bucket}/{key}")
        
        mock_s3_cache.reset_mock()
        print()
        
        print("6. Demonstrating create operation cache invalidation...")
        new_file = create_mock_s3_path('my-bucket', 'documents/new_file.txt')
        new_file.parent = source_parent
        cache_manager.invalidate_cache_for_create_operation(new_file)
        
        print("   Cache invalidation calls for create operation:")
        for call in mock_s3_cache.invalidate_key.call_args_list:
            bucket, key = call[0]
            print(f"     - Invalidated: s3://{bucket}/{key}")
        
        print()
    
    print("7. Demonstrating local file handling (no S3 cache invalidation)...")
    
    # Create mock local path
    local_path = Mock()
    local_path.get_scheme.return_value = 'file'
    
    with patch('tfm_cache_manager.get_s3_cache') as mock_get_s3_cache:
        cache_manager.invalidate_cache_for_paths([local_path], "local operation")
        
        # S3 cache should not be accessed for local paths
        if not mock_get_s3_cache.called:
            print("   ✓ Local paths correctly ignored for S3 cache invalidation")
        else:
            print("   ✗ Local paths incorrectly triggered S3 cache operations")
    
    print()
    
    print("8. Demonstrating error handling...")
    
    with patch('tfm_cache_manager.get_s3_cache') as mock_get_s3_cache:
        mock_get_s3_cache.side_effect = Exception("Simulated cache error")
        
        # Should handle error gracefully
        try:
            cache_manager.invalidate_cache_for_paths([source_file], "error test")
            print("   ✓ Cache invalidation errors handled gracefully")
        except Exception as e:
            print(f"   ✗ Cache invalidation error not handled: {e}")
    
    print()
    print("=== Demo completed ===")
    print()
    print("Key benefits of S3 cache invalidation:")
    print("• Ensures directory listings are refreshed after file operations")
    print("• Prevents stale cache entries from showing outdated information")
    print("• Improves user experience by showing accurate file states")
    print("• Handles both individual files and directory operations")
    print("• Works across different S3 operations (copy, move, delete, archive)")
    print("• Gracefully handles errors without breaking file operations")


if __name__ == '__main__':
    demo_cache_invalidation()