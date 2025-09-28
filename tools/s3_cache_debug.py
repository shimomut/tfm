#!/usr/bin/env python3
"""
S3 Cache Debug Tool - Analyze S3 caching behavior in TFM

This tool helps debug S3 performance issues by monitoring cache hits/misses
and API call patterns during directory operations.
"""

import sys
import os
import time
import json
from datetime import datetime
from unittest.mock import patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from tfm_path import Path
    from tfm_s3 import get_s3_cache
    import boto3
    from botocore.exceptions import ClientError
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this from the TFM project root directory")
    sys.exit(1)


class S3CacheDebugger:
    """Debug S3 cache behavior"""
    
    def __init__(self):
        self.cache = get_s3_cache()
        self.api_call_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.start_time = None
        self.api_calls_made = []  # Track actual API calls
        
    def reset_stats(self):
        """Reset debugging statistics"""
        self.api_call_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.start_time = time.time()
        
    def print_cache_stats(self):
        """Print current cache statistics"""
        stats = self.cache.get_stats()
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print(f"\n=== S3 Cache Debug Statistics ===")
        print(f"Elapsed time: {elapsed:.2f} seconds")
        print(f"API calls made: {self.api_call_count}")
        print(f"Cache hits: {self.cache_hits}")
        print(f"Cache misses: {self.cache_misses}")
        print(f"Hit ratio: {self.cache_hits/(self.cache_hits + self.cache_misses)*100:.1f}%" if (self.cache_hits + self.cache_misses) > 0 else "N/A")
        print(f"Cache entries: {stats['total_entries']}")
        print(f"Expired entries: {stats['expired_entries']}")
        print(f"Max entries: {stats['max_entries']}")
        print(f"Default TTL: {stats['default_ttl']} seconds")
        
    def debug_directory_listing(self, s3_path: str):
        """Debug directory listing performance"""
        print(f"\n=== Debugging Directory Listing: {s3_path} ===")
        
        # Clear cache to start fresh
        self.cache.clear()
        self.reset_stats()
        self.api_calls_made = []
        
        # Patch boto3 client methods to track API calls
        def track_api_call(original_method, method_name):
            def wrapper(*args, **kwargs):
                self.api_call_count += 1
                call_info = {
                    'method': method_name,
                    'args': args,
                    'kwargs': kwargs,
                    'timestamp': time.time()
                }
                self.api_calls_made.append(call_info)
                print(f"  API CALL: {method_name}({kwargs})")
                return original_method(*args, **kwargs)
            return wrapper
        
        try:
            path = Path(s3_path)
            
            print(f"Path type: {type(path._impl).__name__}")
            
            # Patch the S3 client to track calls
            s3_client = path._impl._client
            original_list_objects_v2 = s3_client.list_objects_v2
            original_head_object = s3_client.head_object
            
            s3_client.list_objects_v2 = track_api_call(original_list_objects_v2, 'list_objects_v2')
            s3_client.head_object = track_api_call(original_head_object, 'head_object')
            
            print(f"Is directory: {path.is_dir()}")
            
            # Time the directory listing
            print(f"\n--- Directory Listing ---")
            start_time = time.time()
            files = list(path.iterdir())
            listing_time = time.time() - start_time
            
            print(f"Directory listing took: {listing_time:.3f} seconds")
            print(f"Found {len(files)} items")
            print(f"API calls during listing: {len([c for c in self.api_calls_made if c['method'] == 'list_objects_v2'])}")
            
            # Show cache contents after listing
            print(f"\n--- Cache Contents After Listing ---")
            cache_entries = self.cache._cache
            print(f"Total cache entries: {len(cache_entries)}")
            
            head_object_entries = 0
            for cache_key, entry in cache_entries.items():
                if entry['operation'] == 'head_object':
                    head_object_entries += 1
                    print(f"  Cached head_object for key: {entry['key']}")
            
            print(f"head_object entries cached: {head_object_entries}")
            
            # Now test stat calls on first few files
            print(f"\n--- Testing stat() calls on first 5 items ---")
            stat_start = time.time()
            api_calls_before_stat = len(self.api_calls_made)
            
            for i, file_path in enumerate(files[:5]):
                item_start = time.time()
                print(f"\n  Testing {file_path.name} (key: {file_path._impl._key})")
                
                # Check if this file's stat info is cached
                cached_head = self.cache.get('head_object', file_path._impl._bucket, file_path._impl._key)
                print(f"    Cached head_object: {'YES' if cached_head else 'NO'}")
                
                try:
                    stat_result = file_path.stat()
                    item_time = time.time() - item_start
                    print(f"    Result: {item_time:.3f}s (size: {stat_result.st_size}, dir: {file_path.is_dir()})")
                except Exception as e:
                    item_time = time.time() - item_start
                    print(f"    ERROR: {item_time:.3f}s ({e})")
            
            stat_time = time.time() - stat_start
            api_calls_during_stat = len(self.api_calls_made) - api_calls_before_stat
            print(f"Stat calls took: {stat_time:.3f} seconds total")
            print(f"API calls during stat: {api_calls_during_stat}")
            
            # Restore original methods
            s3_client.list_objects_v2 = original_list_objects_v2
            s3_client.head_object = original_head_object
            
            self.print_cache_stats()
            
            # Show all API calls made
            print(f"\n--- All API Calls Made ---")
            for i, call in enumerate(self.api_calls_made):
                print(f"{i+1}. {call['method']} - {call['kwargs']}")
            
        except Exception as e:
            print(f"Error during debugging: {e}")
            import traceback
            traceback.print_exc()
    
    def analyze_cache_keys(self, s3_path: str):
        """Analyze what cache keys are being generated"""
        print(f"\n=== Analyzing Cache Keys for: {s3_path} ===")
        
        # Clear cache and reset
        self.cache.clear()
        self.reset_stats()
        
        try:
            path = Path(s3_path)
            
            # Perform operations and examine cache
            print("Performing directory listing...")
            files = list(path.iterdir())
            
            print("Performing stat calls...")
            for file_path in files[:3]:
                try:
                    file_path.stat()
                except:
                    pass
            
            # Examine cache contents
            print(f"\n--- Cache Contents ---")
            cache_entries = self.cache._cache
            
            for i, (cache_key, entry) in enumerate(cache_entries.items()):
                print(f"Entry {i+1}:")
                print(f"  Key: {cache_key}")
                print(f"  Operation: {entry['operation']}")
                print(f"  Bucket: {entry['bucket']}")
                print(f"  S3 Key: {entry['key']}")
                print(f"  TTL: {entry['ttl']}s")
                print(f"  Age: {time.time() - entry['timestamp']:.1f}s")
                print()
                
        except Exception as e:
            print(f"Error during cache analysis: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python s3_cache_debug.py <s3://bucket/path/>")
        print("Example: python s3_cache_debug.py s3://my-bucket/folder/")
        sys.exit(1)
    
    s3_path = sys.argv[1]
    
    if not s3_path.startswith('s3://'):
        print("Error: Path must start with s3://")
        sys.exit(1)
    
    debugger = S3CacheDebugger()
    
    print("S3 Cache Debug Tool")
    print("==================")
    
    # Test directory listing performance
    debugger.debug_directory_listing(s3_path)
    
    # Analyze cache keys
    debugger.analyze_cache_keys(s3_path)


if __name__ == "__main__":
    main()