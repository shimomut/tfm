#!/usr/bin/env python3
"""
Demo: S3 File Editing Capability

This demo shows how S3 file editing capability is indicated in TFM.
"""

import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_s3 import S3PathImpl


def demo_s3_file_editing_capability():
    """Demonstrate S3 file editing capability indication"""
    print("=== S3 File Editing Capability Demo ===\n")
    
    # Mock boto3 to avoid AWS dependencies
    mock_boto3 = Mock()
    mock_client = Mock()
    mock_boto3.client.return_value = mock_client
    
    with patch('tfm_s3.boto3', mock_boto3):
        with patch('tfm_s3.HAS_BOTO3', True):
            # Create S3 path
            s3_path = S3PathImpl('s3://demo-bucket/demo-file.txt')
            print(f"Created S3 path: {s3_path}")
            
            # Check file editing support
            print(f"Supports file editing: {s3_path.supports_file_editing()}")
            print(f"Supports directory rename: {s3_path.supports_directory_rename()}")
            print()
            
            # Mock successful put_object for write operations
            mock_client.put_object.return_value = {}
            
            # Try to open file in write mode
            print("Attempting to open S3 file in write mode...")
            try:
                file_obj = s3_path.open('w')
                print(f"✓ SUCCESS: Write mode works - Got {type(file_obj).__name__}")
            except Exception as e:
                print(f"✗ ERROR: Write mode failed - {e}")
            print()
            
            # Try to open file in append mode
            print("Attempting to open S3 file in append mode...")
            try:
                file_obj = s3_path.open('a')
                print(f"✓ SUCCESS: Append mode works - Got {type(file_obj).__name__}")
            except Exception as e:
                print(f"✗ ERROR: Append mode failed - {e}")
            print()
            
            # Try write_text
            print("Attempting to write text to S3 file...")
            try:
                result = s3_path.write_text("This works!")
                print(f"✓ SUCCESS: write_text works - Wrote {result} characters")
            except Exception as e:
                print(f"✗ ERROR: write_text failed - {e}")
            print()
            
            # Try write_bytes
            print("Attempting to write bytes to S3 file...")
            try:
                result = s3_path.write_bytes(b"This works!")
                print(f"✓ SUCCESS: write_bytes works - Wrote {result} bytes")
            except Exception as e:
                print(f"✗ ERROR: write_bytes failed - {e}")
            print()
            
            # Show that read operations work
            print("Attempting to open S3 file in read mode...")
            try:
                # Mock successful read response
                mock_response = {
                    'Body': Mock()
                }
                mock_response['Body'].read.return_value = b'demo file content'
                mock_client.get_object.return_value = mock_response
                
                with s3_path.open('r') as f:
                    content = f.read()
                    print(f"✓ SUCCESS: Read mode works - Content: '{content}'")
            except Exception as e:
                print(f"✗ ERROR: Read mode failed - {e}")
            print()
            
            print("=== Demo Complete ===")
            print("S3 file editing works normally. The supports_file_editing() method")
            print("returns False as a capability indicator, but doesn't block operations.")


if __name__ == '__main__':
    demo_s3_file_editing_capability()