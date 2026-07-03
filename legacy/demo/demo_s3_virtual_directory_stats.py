#!/usr/bin/env python3
"""
Demo: S3 Virtual Directory Stats

This demo shows how TFM handles virtual directories in S3 - directories that don't
have actual S3 objects but exist because there are objects with that prefix.

Virtual directories now display:
- Size: 0B (instead of "---")
- Date: Latest timestamp of children (instead of "---")
"""

import sys
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from tfm_s3 import S3PathImpl, S3StatResult
    from botocore.exceptions import ClientError
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("This demo requires boto3 and the S3 modules to be available")
    sys.exit(1)


def format_size(size_bytes):
    """Format size in bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"


def format_timestamp(timestamp):
    """Format timestamp to readable date"""
    if timestamp == 0:
        return "---"
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def demo_virtual_directory_stats():
    """Demonstrate virtual directory stats functionality"""
    print("=" * 60)
    print("S3 Virtual Directory Stats Demo")
    print("=" * 60)
    print()
    
    # Mock boto3 to simulate S3 responses
    mock_boto3 = Mock()
    mock_s3_client = Mock()
    mock_boto3.client.return_value = mock_s3_client
    
    with patch('tfm_s3.boto3', mock_boto3), \
         patch('tfm_s3.HAS_BOTO3', True):
        
        # Demo 1: Virtual directory with children
        print("Demo 1: Virtual Directory with Children")
        print("-" * 40)
        
        s3_path = S3PathImpl('s3://my-bucket/documents/reports/')
        
        # Mock head_object to raise NoSuchKey (no actual directory object)
        error_response = {'Error': {'Code': 'NoSuchKey'}}
        mock_s3_client.head_object.side_effect = ClientError(error_response, 'head_object')
        
        # Create mock child objects with different timestamps
        child_objects = [
            {
                'Key': 'documents/reports/2023/annual_report.pdf',
                'LastModified': datetime(2023, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                'Size': 2048000
            },
            {
                'Key': 'documents/reports/2024/q1_report.pdf',
                'LastModified': datetime(2024, 3, 31, 18, 30, 0, tzinfo=timezone.utc),
                'Size': 1536000
            },
            {
                'Key': 'documents/reports/2024/q2_report.pdf',
                'LastModified': datetime(2024, 6, 30, 17, 45, 30, tzinfo=timezone.utc),  # Latest
                'Size': 1792000
            },
            {
                'Key': 'documents/reports/draft/temp.pdf',
                'LastModified': datetime(2024, 1, 15, 10, 20, 0, tzinfo=timezone.utc),
                'Size': 512000
            }
        ]
        
        mock_list_response = {
            'Contents': child_objects,
            'IsTruncated': False
        }
        mock_s3_client.list_objects_v2.return_value = mock_list_response
        
        # Mock is_dir to return True
        with patch.object(s3_path, 'is_dir', return_value=True):
            print(f"Path: {s3_path}")
            print(f"Type: Virtual Directory (no actual S3 object)")
            print()
            
            # Show child objects
            print("Child objects:")
            for obj in child_objects:
                obj_name = obj['Key'].split('/')[-1]
                obj_size = format_size(obj['Size'])
                obj_date = format_timestamp(obj['LastModified'].timestamp())
                print(f"  {obj_name:<20} {obj_size:>8} {obj_date}")
            print()
            
            # Get virtual directory stats
            try:
                stat_result = s3_path.stat()
                print("Virtual Directory Stats:")
                print(f"  Size: {format_size(stat_result.st_size)}")
                print(f"  Date: {format_timestamp(stat_result.st_mtime)}")
                print(f"  Type: {'Directory' if stat_result.st_mode & 0o040000 else 'File'}")
                
                # Show which child had the latest timestamp
                latest_child = max(child_objects, key=lambda x: x['LastModified'].timestamp())
                latest_name = latest_child['Key'].split('/')[-1]
                print(f"  Latest child: {latest_name}")
                
            except Exception as e:
                print(f"Error getting stats: {e}")
        
        print()
        print()
        
        # Demo 2: Empty virtual directory
        print("Demo 2: Empty Virtual Directory")
        print("-" * 40)
        
        empty_s3_path = S3PathImpl('s3://my-bucket/empty-folder/')
        
        # Mock empty response
        empty_response = {
            'Contents': [],
            'IsTruncated': False
        }
        mock_s3_client.list_objects_v2.return_value = empty_response
        
        with patch.object(empty_s3_path, 'is_dir', return_value=True):
            print(f"Path: {empty_s3_path}")
            print(f"Type: Empty Virtual Directory")
            print()
            
            try:
                stat_result = empty_s3_path.stat()
                print("Empty Virtual Directory Stats:")
                print(f"  Size: {format_size(stat_result.st_size)}")
                print(f"  Date: {format_timestamp(stat_result.st_mtime)} (current time)")
                print(f"  Type: {'Directory' if stat_result.st_mode & 0o040000 else 'File'}")
                
            except Exception as e:
                print(f"Error getting stats: {e}")
        
        print()
        print()
        
        # Demo 3: Actual S3 directory object (for comparison)
        print("Demo 3: Actual S3 Directory Object (for comparison)")
        print("-" * 50)
        
        actual_s3_path = S3PathImpl('s3://my-bucket/actual-folder/')
        
        # Mock successful head_object response
        actual_dir_time = datetime(2024, 5, 15, 14, 30, 0, tzinfo=timezone.utc)
        mock_head_response = {
            'ContentLength': 0,
            'LastModified': actual_dir_time
        }
        mock_s3_client.head_object.return_value = mock_head_response
        
        with patch.object(actual_s3_path, 'is_dir', return_value=True):
            print(f"Path: {actual_s3_path}")
            print(f"Type: Actual S3 Directory Object")
            print()
            
            try:
                stat_result = actual_s3_path.stat()
                print("Actual Directory Object Stats:")
                print(f"  Size: {format_size(stat_result.st_size)}")
                print(f"  Date: {format_timestamp(stat_result.st_mtime)}")
                print(f"  Type: {'Directory' if stat_result.st_mode & 0o040000 else 'File'}")
                
            except Exception as e:
                print(f"Error getting stats: {e}")
        
        print()
        print()
        
        # Demo 4: Large directory with pagination
        print("Demo 4: Large Virtual Directory (Paginated)")
        print("-" * 45)
        
        large_s3_path = S3PathImpl('s3://my-bucket/large-dataset/')
        
        # Mock first response (truncated)
        first_response = {
            'Contents': [
                {
                    'Key': 'large-dataset/data001.csv',
                    'LastModified': datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                    'Size': 1000000
                }
            ],
            'IsTruncated': True
        }
        
        # Mock paginated responses
        page1 = {
            'Contents': [
                {
                    'Key': 'large-dataset/data002.csv',
                    'LastModified': datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
                    'Size': 1100000
                },
                {
                    'Key': 'large-dataset/data003.csv',
                    'LastModified': datetime(2024, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
                    'Size': 1200000
                }
            ]
        }
        
        page2 = {
            'Contents': [
                {
                    'Key': 'large-dataset/data004.csv',
                    'LastModified': datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc),  # Latest
                    'Size': 1300000
                }
            ]
        }
        
        # Reset mock for this demo
        mock_s3_client.reset_mock()
        mock_s3_client.head_object.side_effect = ClientError(error_response, 'head_object')
        mock_s3_client.list_objects_v2.return_value = first_response
        
        # Mock paginator
        mock_paginator = Mock()
        mock_page_iterator = [page1, page2]
        mock_paginator.paginate.return_value = mock_page_iterator
        mock_s3_client.get_paginator.return_value = mock_paginator
        
        with patch.object(large_s3_path, 'is_dir', return_value=True):
            print(f"Path: {large_s3_path}")
            print(f"Type: Large Virtual Directory (>1000 objects)")
            print()
            
            print("Sample objects (showing pagination handling):")
            all_objects = first_response['Contents'] + page1['Contents'] + page2['Contents']
            for obj in all_objects:
                obj_name = obj['Key'].split('/')[-1]
                obj_size = format_size(obj['Size'])
                obj_date = format_timestamp(obj['LastModified'].timestamp())
                print(f"  {obj_name:<20} {obj_size:>8} {obj_date}")
            print("  ... (and many more)")
            print()
            
            try:
                stat_result = large_s3_path.stat()
                print("Large Virtual Directory Stats:")
                print(f"  Size: {format_size(stat_result.st_size)}")
                print(f"  Date: {format_timestamp(stat_result.st_mtime)}")
                print(f"  Type: {'Directory' if stat_result.st_mode & 0o040000 else 'File'}")
                
                # Show which object had the latest timestamp
                latest_obj = max(all_objects, key=lambda x: x['LastModified'].timestamp())
                latest_name = latest_obj['Key'].split('/')[-1]
                print(f"  Latest object: {latest_name}")
                
            except Exception as e:
                print(f"Error getting stats: {e}")
    
    print()
    print("=" * 60)
    print("Summary:")
    print("- Virtual directories now show '0B' instead of '---' for size")
    print("- Virtual directories show the latest child timestamp instead of '---'")
    print("- This provides better user experience when browsing S3 in TFM")
    print("- Caching ensures good performance even with large directories")
    print("=" * 60)


if __name__ == '__main__':
    demo_virtual_directory_stats()