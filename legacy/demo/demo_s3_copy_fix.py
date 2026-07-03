#!/usr/bin/env python3
"""
Demo: S3 Copy Fix - Demonstrates the fix for copying files to/from S3

This demo shows how the new copy_to() method enables copying files between
local filesystem and S3, fixing the "Permission denied: Cannot write to s3://"
error that occurred when using shutil.copy2() with S3 paths.
"""

import os
import sys
import tempfile
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path


def demo_local_to_local_copy():
    """Demonstrate local to local file copying"""
    print("=== Local to Local Copy ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create source file
        source = Path(temp_dir) / "source.txt"
        source.write_text("Hello, this is a test file for copying!")
        
        # Copy to destination
        dest = Path(temp_dir) / "destination.txt"
        result = source.copy_to(dest)
        
        print(f"Source: {source}")
        print(f"Destination: {dest}")
        print(f"Copy result: {result}")
        print(f"Destination exists: {dest.exists()}")
        print(f"Content matches: {dest.read_text() == source.read_text()}")
        print()
        
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def demo_s3_copy_simulation():
    """Demonstrate S3 copy operations with mocked boto3"""
    print("=== S3 Copy Simulation (Mocked) ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a local test file
        local_file = Path(temp_dir) / "local_test.txt"
        test_content = "This file will be copied to S3!"
        local_file.write_text(test_content)
        
        # Mock boto3 for S3 operations
        with patch('tfm_s3.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            # Test local to S3 copy
            print("--- Local to S3 Copy ---")
            s3_dest = Path("s3://my-bucket/uploaded-file.txt")
            
            try:
                result = local_file.copy_to(s3_dest, overwrite=True)
                print(f"Local file: {local_file}")
                print(f"S3 destination: {s3_dest}")
                print(f"Copy result: {result}")
                
                # Verify S3 put_object was called
                if mock_client.put_object.called:
                    call_args = mock_client.put_object.call_args
                    print(f"S3 put_object called with bucket: {call_args[1]['Bucket']}")
                    print(f"S3 put_object called with key: {call_args[1]['Key']}")
                    print(f"Content uploaded: {call_args[1]['Body'].decode('utf-8')}")
                
            except Exception as e:
                print(f"Error during local to S3 copy: {e}")
            
            print()
            
            # Test S3 to local copy
            print("--- S3 to Local Copy ---")
            
            # Mock S3 get_object response
            mock_response = {
                'Body': Mock(),
                'ContentLength': len(test_content),
                'LastModified': Mock()
            }
            mock_response['Body'].read.return_value = test_content.encode('utf-8')
            mock_response['LastModified'].timestamp.return_value = 1234567890
            mock_client.get_object.return_value = mock_response
            
            # Also mock head_object for the cache system
            mock_client.head_object.return_value = {
                'ContentLength': len(test_content),
                'LastModified': Mock()
            }
            mock_client.head_object.return_value['LastModified'].timestamp.return_value = 1234567890
            
            s3_source = Path("s3://my-bucket/downloaded-file.txt")
            local_dest = Path(temp_dir) / "downloaded.txt"
            
            try:
                result = s3_source.copy_to(local_dest, overwrite=True)
                print(f"S3 source: {s3_source}")
                print(f"Local destination: {local_dest}")
                print(f"Copy result: {result}")
                print(f"File exists locally: {local_dest.exists()}")
                
                if local_dest.exists():
                    print(f"Downloaded content: {local_dest.read_text()}")
                
            except Exception as e:
                print(f"Error during S3 to local copy: {e}")
            
            print()
    
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def demo_error_handling():
    """Demonstrate error handling in copy operations"""
    print("=== Error Handling Demo ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Test copying non-existent file
        print("--- Copying Non-existent File ---")
        nonexistent = Path(temp_dir) / "does_not_exist.txt"
        dest = Path(temp_dir) / "destination.txt"
        
        try:
            nonexistent.copy_to(dest)
        except FileNotFoundError as e:
            print(f"✓ Correctly caught FileNotFoundError: {e}")
        
        # Test copying to existing file without overwrite
        print("\n--- Copying to Existing File (no overwrite) ---")
        source = Path(temp_dir) / "source.txt"
        source.write_text("source content")
        
        existing = Path(temp_dir) / "existing.txt"
        existing.write_text("existing content")
        
        try:
            source.copy_to(existing, overwrite=False)
        except FileExistsError as e:
            print(f"✓ Correctly caught FileExistsError: {e}")
        
        # Test copying to existing file with overwrite
        print("\n--- Copying to Existing File (with overwrite) ---")
        try:
            result = source.copy_to(existing, overwrite=True)
            print(f"✓ Overwrite successful: {result}")
            print(f"Content after overwrite: {existing.read_text()}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
        
        print()
    
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def demo_cross_storage_benefits():
    """Explain the benefits of the new cross-storage copy system"""
    print("=== Cross-Storage Copy Benefits ===")
    print()
    print("Before the fix:")
    print("  • TFM used shutil.copy2() for all copy operations")
    print("  • shutil.copy2() only works with local filesystem paths")
    print("  • Copying to S3 failed with 'Permission denied' error")
    print("  • No support for cross-storage operations")
    print()
    print("After the fix:")
    print("  • New copy_to() method handles cross-storage copying")
    print("  • Automatically detects source and destination storage types")
    print("  • Uses appropriate APIs for each storage system:")
    print("    - Local to Local: shutil.copy2() (fast)")
    print("    - Local to S3: read local file, upload via S3 API")
    print("    - S3 to Local: download via S3 API, write local file")
    print("    - S3 to S3: download and re-upload (could be optimized)")
    print("  • Proper error handling with meaningful error messages")
    print("  • Support for overwrite control")
    print("  • Maintains file metadata where possible")
    print()
    print("Usage in TFM:")
    print("  • File copy operations (Ctrl+C) now work with S3")
    print("  • Directory copy operations work recursively")
    print("  • Progress tracking works for cross-storage operations")
    print("  • Conflict resolution dialogs work properly")
    print()


def main():
    """Run all demonstrations"""
    print("S3 Copy Fix Demonstration")
    print("=" * 50)
    print()
    
    demo_local_to_local_copy()
    demo_s3_copy_simulation()
    demo_error_handling()
    demo_cross_storage_benefits()
    
    print("Demo completed successfully!")
    print()
    print("To test with real S3:")
    print("1. Ensure AWS credentials are configured")
    print("2. Install boto3: pip install boto3")
    print("3. Use TFM to navigate to an S3 bucket")
    print("4. Try copying files between local and S3 directories")


if __name__ == '__main__':
    main()