#!/usr/bin/env python3
"""
Debug S3 directory deletion issue

This script helps debug the "No files to delete" error when trying to delete S3 directories.
"""

import os
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from tfm_path import Path as TFMPath
    from tfm_s3 import S3PathImpl
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("boto3 not available, cannot test S3 functionality")


def debug_s3_directory_deletion():
    """Debug S3 directory deletion issue"""
    if not HAS_BOTO3:
        print("Cannot test S3 functionality - boto3 not available")
        return
    
    # Test the specific path that's causing issues
    test_path = "s3://shimomut-files/test1/dir3/dir2/"
    
    print(f"Debugging S3 directory deletion for: {test_path}")
    print("=" * 60)
    
    try:
        # Create TFM Path object
        dir_path = TFMPath(test_path)
        print(f"Path object created: {dir_path}")
        print(f"Path type: {type(dir_path._impl)}")
        
        # Check basic properties
        print(f"exists(): {dir_path.exists()}")
        print(f"is_dir(): {dir_path.is_dir()}")
        print(f"is_file(): {dir_path.is_file()}")
        
        # Try to list contents
        try:
            contents = list(dir_path.iterdir())
            print(f"Directory contents: {len(contents)} items")
            for item in contents:
                print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
        except Exception as e:
            print(f"Error listing directory contents: {e}")
        
        # Check if directory is empty (this is what rmdir checks)
        try:
            # Simulate the rmdir check
            s3_impl = dir_path._impl
            if isinstance(s3_impl, S3PathImpl):
                print(f"S3 bucket: {s3_impl._bucket}")
                print(f"S3 key: '{s3_impl._key}'")
                
                # Check what rmdir would do
                prefix = s3_impl._key.rstrip('/') + '/'
                print(f"Checking prefix: '{prefix}'")
                
                try:
                    response = s3_impl._client.list_objects_v2(
                        Bucket=s3_impl._bucket,
                        Prefix=prefix,
                        MaxKeys=1
                    )
                    key_count = response.get('KeyCount', 0)
                    print(f"Objects with prefix: {key_count}")
                    
                    if key_count > 0:
                        print("Directory is NOT empty - rmdir would fail")
                        # List what's in there
                        response_full = s3_impl._client.list_objects_v2(
                            Bucket=s3_impl._bucket,
                            Prefix=prefix,
                            MaxKeys=10
                        )
                        for obj in response_full.get('Contents', []):
                            print(f"  Found object: {obj['Key']}")
                    else:
                        print("Directory appears empty - rmdir should work")
                        
                        # Check if there's a directory marker
                        directory_key = prefix
                        try:
                            s3_impl._client.head_object(Bucket=s3_impl._bucket, Key=directory_key)
                            print(f"Directory marker exists: {directory_key}")
                        except:
                            print(f"No directory marker found: {directory_key}")
                
                except Exception as e:
                    print(f"Error checking S3 objects: {e}")
        
        except Exception as e:
            print(f"Error accessing S3 implementation: {e}")
        
        # Try the actual deletion
        print("\nTrying rmdir()...")
        try:
            dir_path.rmdir()
            print("✓ rmdir() succeeded")
        except Exception as e:
            print(f"✗ rmdir() failed: {e}")
    
    except Exception as e:
        print(f"Error creating path object: {e}")


def simulate_delete_selected_files_logic():
    """Simulate the logic from delete_selected_files method"""
    print("\nSimulating delete_selected_files logic...")
    print("=" * 60)
    
    # This simulates what happens in the TFM main loop
    test_path = "s3://shimomut-files/test1/dir3/dir2/"
    
    try:
        # Simulate having this path in selected_files
        selected_files = {test_path}  # This is how it would be stored
        
        files_to_delete = []
        
        if selected_files:
            print("Processing selected files...")
            for file_path_str in selected_files:
                print(f"  Checking: {file_path_str}")
                file_path = TFMPath(file_path_str)
                
                print(f"    exists(): {file_path.exists()}")
                
                if file_path.exists():
                    files_to_delete.append(file_path)
                    print(f"    ✓ Added to deletion list")
                else:
                    print(f"    ✗ Does not exist, skipping")
        
        print(f"\nFiles to delete: {len(files_to_delete)}")
        
        if not files_to_delete:
            print("❌ This is where 'No files to delete' error occurs!")
            return False
        else:
            print("✓ Files found for deletion")
            return True
    
    except Exception as e:
        print(f"Error in simulation: {e}")
        return False


def main():
    """Main function"""
    print("S3 Directory Deletion Debug Tool")
    print("=" * 60)
    
    debug_s3_directory_deletion()
    simulate_delete_selected_files_logic()
    
    print("\nDebug complete.")


if __name__ == '__main__':
    main()