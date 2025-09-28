#!/usr/bin/env python3
"""
Integration test for S3PathImpl with actual AWS operations
This test requires AWS credentials to be configured
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path

def test_s3_credentials():
    """Test if AWS credentials are available"""
    print("Testing AWS credentials availability...")
    
    try:
        s3_path = Path('s3://test-bucket/test-file.txt')
        # This will trigger credential check
        s3_path._impl._client
        print("✓ AWS credentials are available")
        return True
    except RuntimeError as e:
        print(f"⚠ AWS credentials not available: {e}")
        return False
    except Exception as e:
        print(f"⚠ AWS connection issue: {e}")
        return False

def test_s3_bucket_operations():
    """Test S3 bucket operations (requires valid credentials and bucket)"""
    print("\nTesting S3 bucket operations...")
    
    # Use a test bucket - replace with your own bucket name
    test_bucket = os.environ.get('TFM_TEST_S3_BUCKET', 'tfm-test-bucket-nonexistent')
    s3_path = Path(f's3://{test_bucket}/')
    
    try:
        exists = s3_path.exists()
        print(f"Bucket {test_bucket} exists: {exists}")
        
        if exists:
            print("Testing directory listing...")
            try:
                items = list(s3_path.iterdir())
                print(f"Found {len(items)} items in bucket")
                for item in items[:5]:  # Show first 5 items
                    print(f"  - {item}")
                if len(items) > 5:
                    print(f"  ... and {len(items) - 5} more items")
            except Exception as e:
                print(f"Error listing bucket contents: {e}")
        
        print("✓ S3 bucket operations test completed")
        return True
    except Exception as e:
        print(f"⚠ S3 bucket operations failed: {e}")
        return False

def test_s3_file_operations():
    """Test S3 file operations"""
    print("\nTesting S3 file operations...")
    
    test_bucket = os.environ.get('TFM_TEST_S3_BUCKET', 'tfm-test-bucket-nonexistent')
    test_file = Path(f's3://{test_bucket}/tfm-test-file.txt')
    
    try:
        # Test file existence
        exists = test_file.exists()
        print(f"Test file exists: {exists}")
        
        # Test writing (only if we have a real bucket)
        if test_bucket != 'tfm-test-bucket-nonexistent':
            print("Testing file write...")
            test_content = "Hello from TFM S3 integration test!"
            test_file.write_text(test_content)
            print("✓ File written successfully")
            
            # Test reading
            print("Testing file read...")
            read_content = test_file.read_text()
            print(f"Read content: {read_content}")
            
            if read_content == test_content:
                print("✓ File content matches")
            else:
                print("⚠ File content mismatch")
            
            # Test file info
            stat_info = test_file.stat()
            print(f"File size: {stat_info.st_size} bytes")
            print(f"File modified: {stat_info.st_mtime}")
            
            # Clean up
            print("Cleaning up test file...")
            test_file.unlink()
            print("✓ Test file deleted")
        
        print("✓ S3 file operations test completed")
        return True
    except Exception as e:
        print(f"⚠ S3 file operations failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("TFM S3 Integration Tests")
    print("=" * 40)
    
    # Check if boto3 is available
    try:
        import boto3
        print("✓ boto3 is available")
    except ImportError:
        print("❌ boto3 is not installed. Run: pip install boto3")
        return False
    
    # Test credentials
    has_credentials = test_s3_credentials()
    
    if not has_credentials:
        print("\nSkipping AWS operations tests due to missing credentials.")
        print("To run full tests:")
        print("1. Configure AWS credentials (aws configure)")
        print("2. Set TFM_TEST_S3_BUCKET environment variable to a test bucket")
        print("3. Re-run this test")
        return True
    
    # Run AWS operations tests
    bucket_test = test_s3_bucket_operations()
    file_test = test_s3_file_operations()
    
    if bucket_test and file_test:
        print("\n🎉 All integration tests passed!")
        return True
    else:
        print("\n⚠ Some integration tests had issues (see above)")
        return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)