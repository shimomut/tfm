#!/usr/bin/env python3
"""
Demo: S3 Caching Optimization

This demo shows the performance improvement from caching stat information
during S3 directory listings, reducing the number of API calls needed.
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
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class S3PerformanceDemo:
    """Demonstrate S3 caching optimization performance"""
    
    def __init__(self):
        self.api_call_count = 0
        self.cache = get_s3_cache()
        
    def create_mock_s3_environment(self):
        """Create a mock S3 environment for testing"""
        # Sample directory with multiple files
        sample_objects = []
        
        # Create 20 sample files
        for i in range(20):
            sample_objects.append({
                'Key': f'demo-folder/file_{i:02d}.txt',
                'Size': 1024 * (i + 1),
                'LastModified': datetime(2024, 1, i + 1, 12, 0, 0),
                'ETag': f'"etag_{i:02d}"',
                'StorageClass': 'STANDARD'
            })
        
        # Add some subdirectories
        for i in range(3):
            sample_objects.append({
                'Key': f'demo-folder/subdir_{i}/',
                'Size': 0,
                'LastModified': datetime(2024, 1, 15 + i, 12, 0, 0),
                'ETag': f'"dir_etag_{i}"',
                'StorageClass': 'STANDARD'
            })
        
        # Mock S3 client
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        
        # Mock paginator response
        mock_page = {
            'Contents': sample_objects,
            'CommonPrefixes': [{'Prefix': f'demo-folder/subdir_{i}/'} for i in range(3)],
            'KeyCount': len(sample_objects),
            'IsTruncated': False
        }
        
        mock_paginator.paginate.return_value = [mock_page]
        
        # Track API calls
        def track_api_call(*args, **kwargs):
            self.api_call_count += 1
            return mock_page
        
        mock_client.list_objects_v2 = Mock(side_effect=track_api_call)
        mock_client.head_object = Mock(side_effect=track_api_call)
        
        return mock_client, sample_objects
    
    def demo_without_optimization(self):
        """Demonstrate performance without optimization (simulated)"""
        print("=== Demo: Without Stat Caching Optimization ===")
        print("Simulating the old behavior where each file stat() makes a separate API call")
        
        # Clear cache
        self.cache.clear()
        self.api_call_count = 0
        
        mock_client, sample_objects = self.create_mock_s3_environment()
        
        with patch('tfm_s3.boto3.client', return_value=mock_client):
            start_time = time.time()
            
            # Simulate old behavior: directory listing + individual head_object calls
            s3_path = Path('s3://demo-bucket/demo-folder/')
            
            # Directory listing (1 API call)
            files = list(s3_path.iterdir())
            listing_api_calls = self.api_call_count
            
            # Simulate individual stat calls (would be N API calls without optimization)
            file_count = 0
            for file_path in files:
                if file_path.is_file():
                    file_count += 1
                    # In the old implementation, this would make a head_object call
                    mock_client.head_object()  # Simulate the API call
            
            total_time = time.time() - start_time
            total_api_calls = self.api_call_count
            
            print(f"Files found: {file_count}")
            print(f"Total API calls: {total_api_calls}")
            print(f"  - Directory listing: {listing_api_calls}")
            print(f"  - Individual stat calls: {total_api_calls - listing_api_calls}")
            print(f"Time taken: {total_time:.3f} seconds")
            print(f"API calls per file: {total_api_calls / max(file_count, 1):.1f}")
    
    def demo_with_optimization(self):
        """Demonstrate performance with optimization"""
        print("\n=== Demo: With Stat Caching Optimization ===")
        print("Using the new optimization where stat info is cached from directory listing")
        
        # Clear cache
        self.cache.clear()
        self.api_call_count = 0
        
        mock_client, sample_objects = self.create_mock_s3_environment()
        
        with patch('tfm_s3.boto3.client', return_value=mock_client):
            start_time = time.time()
            
            # With optimization: directory listing caches stat info
            s3_path = Path('s3://demo-bucket/demo-folder/')
            
            # Directory listing (1 API call, but caches stat info)
            files = list(s3_path.iterdir())
            listing_api_calls = self.api_call_count
            
            # Stat calls now use cached data (0 additional API calls)
            file_count = 0
            for file_path in files:
                if file_path.is_file():
                    file_count += 1
                    # This now uses cached data from the directory listing
                    stat_result = file_path.stat()
                    # Verify we got valid data
                    assert stat_result.st_size > 0
                    assert stat_result.st_mtime > 0
            
            total_time = time.time() - start_time
            total_api_calls = self.api_call_count
            
            print(f"Files found: {file_count}")
            print(f"Total API calls: {total_api_calls}")
            print(f"  - Directory listing: {listing_api_calls}")
            print(f"  - Individual stat calls: {total_api_calls - listing_api_calls}")
            print(f"Time taken: {total_time:.3f} seconds")
            print(f"API calls per file: {total_api_calls / max(file_count, 1):.1f}")
            
            # Show cache statistics
            cache_stats = self.cache.get_stats()
            print(f"Cache entries created: {cache_stats['total_entries']}")
    
    def demo_cache_effectiveness(self):
        """Demonstrate cache effectiveness with repeated operations"""
        print("\n=== Demo: Cache Effectiveness ===")
        print("Showing how repeated operations benefit from caching")
        
        # Clear cache
        self.cache.clear()
        self.api_call_count = 0
        
        mock_client, sample_objects = self.create_mock_s3_environment()
        
        with patch('tfm_s3.boto3.client', return_value=mock_client):
            s3_path = Path('s3://demo-bucket/demo-folder/')
            
            # First iteration
            print("\nFirst iteration (populates cache):")
            start_time = time.time()
            files = list(s3_path.iterdir())
            for file_path in files:
                if file_path.is_file():
                    file_path.stat()
            first_time = time.time() - start_time
            first_api_calls = self.api_call_count
            print(f"  Time: {first_time:.3f}s, API calls: {first_api_calls}")
            
            # Second iteration (should be cached)
            print("Second iteration (uses cache):")
            start_time = time.time()
            files = list(s3_path.iterdir())
            for file_path in files:
                if file_path.is_file():
                    file_path.stat()
            second_time = time.time() - start_time
            second_api_calls = self.api_call_count - first_api_calls
            print(f"  Time: {second_time:.3f}s, API calls: {second_api_calls}")
            
            # Show improvement
            if first_api_calls > 0:
                api_reduction = (1 - second_api_calls / first_api_calls) * 100
                print(f"API call reduction: {api_reduction:.1f}%")
            
            if first_time > 0:
                time_improvement = (1 - second_time / first_time) * 100
                print(f"Time improvement: {time_improvement:.1f}%")


def main():
    """Run the demo"""
    if not HAS_BOTO3:
        print("boto3 not available - skipping S3 caching optimization demo")
        return
    
    print("S3 Caching Optimization Demo")
    print("=" * 40)
    print()
    print("This demo shows how caching stat information from S3 directory")
    print("listings reduces API calls and improves performance in TFM.")
    print()
    
    demo = S3PerformanceDemo()
    
    # Show the problem (without optimization)
    demo.demo_without_optimization()
    
    # Show the solution (with optimization)
    demo.demo_with_optimization()
    
    # Show cache effectiveness
    demo.demo_cache_effectiveness()
    
    print("\n" + "=" * 40)
    print("Summary:")
    print("- The optimization caches file metadata from directory listings")
    print("- This eliminates the need for separate head_object API calls")
    print("- Result: Faster directory rendering and reduced AWS costs")
    print("- Typical improvement: N+1 API calls reduced to 1 API call")


if __name__ == "__main__":
    main()