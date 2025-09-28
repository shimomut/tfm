#!/usr/bin/env python3
"""
Test S3 recursive directory deletion

This script tests the new S3 recursive deletion functionality.
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


def test_s3_recursive_deletion():
    """Test S3 recursive directory deletion"""
    if not HAS_BOTO3:
        print("Cannot test S3 functionality - boto3 not available")
        return
    
    # Test the specific path that's causing issues
    test_path = "s3://shimomut-files/test1/dir3/dir2/"
    
    print(f"Testing S3 recursive deletion for: {test_path}")
    print("=" * 60)
    
    try:
        # Create TFM Path object
        dir_path = TFMPath(test_path)
        print(f"Path object created: {dir_path}")
        
        # Check basic properties
        print(f"exists(): {dir_path.exists()}")
        print(f"is_dir(): {dir_path.is_dir()}")
        
        # List contents before deletion
        try:
            contents = list(dir_path.iterdir())
            print(f"Directory contents before deletion: {len(contents)} items")
            for item in contents:
                print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
        except Exception as e:
            print(f"Error listing directory contents: {e}")
            return False
        
        if len(contents) == 0:
            print("Directory is empty, testing rmdir()...")
            try:
                dir_path.rmdir()
                print("✓ rmdir() succeeded for empty directory")
                return True
            except Exception as e:
                print(f"✗ rmdir() failed: {e}")
                return False
        else:
            print("Directory is not empty, testing rmtree()...")
            try:
                # Test the new rmtree method
                s3_impl = dir_path._impl
                if isinstance(s3_impl, S3PathImpl):
                    s3_impl.rmtree()
                    print("✓ rmtree() succeeded")
                    
                    # Verify directory is gone
                    if not dir_path.exists():
                        print("✓ Directory no longer exists")
                        return True
                    else:
                        print("✗ Directory still exists after deletion")
                        return False
                else:
                    print("✗ Not an S3 path")
                    return False
            except Exception as e:
                print(f"✗ rmtree() failed: {e}")
                return False
    
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main function"""
    print("S3 Recursive Deletion Test")
    print("=" * 60)
    
    success = test_s3_recursive_deletion()
    
    if success:
        print("\n✓ Test completed successfully!")
    else:
        print("\n✗ Test failed!")
    
    print("\nNote: This test will actually delete the directory and its contents!")
    print("Make sure you're okay with this before running.")


if __name__ == '__main__':
    main()