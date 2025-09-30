#!/usr/bin/env python3
"""
Demo: S3 Directory Rename Restriction

This demo shows how TFM prevents directory renaming on S3 to avoid
expensive copy/delete operations that could be costly and slow.
"""

import sys
import os
from unittest.mock import Mock

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_s3 import S3PathImpl


def demo_s3_directory_rename_restriction():
    """Demonstrate S3 directory rename restriction"""
    print("=== S3 Directory Rename Restriction Demo ===\n")
    
    # Create mock S3 client
    mock_client = Mock()
    
    print("1. Creating S3 file and directory paths...")
    
    # Create S3 file path
    s3_file = S3PathImpl('s3://demo-bucket/document.txt')
    s3_file._s3_client = mock_client
    s3_file.is_dir = Mock(return_value=False)
    s3_file.unlink = Mock()  # Mock unlink for file operations
    
    # Create S3 directory path
    s3_directory = S3PathImpl('s3://demo-bucket/photos/')
    s3_directory._s3_client = mock_client
    s3_directory.is_dir = Mock(return_value=True)
    
    print(f"   File: {s3_file._uri}")
    print(f"   Directory: {s3_directory._uri}")
    print()
    
    print("2. Attempting to rename S3 file (should succeed)...")
    try:
        result = s3_file.rename('s3://demo-bucket/renamed_document.txt')
        print("   ✓ File rename succeeded (as expected)")
    except OSError as e:
        # Check if it's the directory restriction error
        if "Directory renaming is not supported on S3" in str(e):
            print(f"   ✗ File rename unexpectedly blocked: {e}")
        else:
            print(f"   ✓ File rename attempted (other error expected): {e}")
    print()
    
    print("3. Attempting to rename S3 directory (should fail)...")
    try:
        s3_directory.rename('s3://demo-bucket/renamed_photos/')
        print("   ✗ Directory rename unexpectedly succeeded!")
    except OSError as e:
        print(f"   ✓ Directory rename blocked: {e}")
    print()
    
    print("4. Testing virtual directory (directory without trailing slash)...")
    virtual_dir = S3PathImpl('s3://demo-bucket/documents')
    virtual_dir._s3_client = mock_client
    virtual_dir.is_dir = Mock(return_value=True)
    
    try:
        virtual_dir.rename('s3://demo-bucket/renamed_documents')
        print("   ✗ Virtual directory rename unexpectedly succeeded!")
    except OSError as e:
        print(f"   ✓ Virtual directory rename blocked: {e}")
    print()
    
    print("5. Testing replace method (should also be blocked for directories)...")
    try:
        s3_directory.replace('s3://demo-bucket/replaced_photos/')
        print("   ✗ Directory replace unexpectedly succeeded!")
    except OSError as e:
        print(f"   ✓ Directory replace blocked: {e}")
    print()
    
    print("=== Demo Summary ===")
    print("✓ File renaming on S3: ALLOWED")
    print("✓ Directory renaming on S3: BLOCKED")
    print("✓ Virtual directory renaming on S3: BLOCKED") 
    print("✓ Directory replace on S3: BLOCKED")
    print()
    print("This prevents expensive copy/delete operations for directories")
    print("that could contain many objects and be costly on S3.")


if __name__ == '__main__':
    demo_s3_directory_rename_restriction()