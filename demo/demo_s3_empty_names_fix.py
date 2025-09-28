#!/usr/bin/env python3
"""
Demo script to verify the S3 empty names fix
This demonstrates that S3 directories now show proper names instead of empty strings
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path

def demo_s3_directory_names():
    """Demonstrate that S3 directories now show proper names"""
    print("S3 Empty Names Fix Demo")
    print("=" * 40)
    print()
    
    # Test with the bucket that was showing the issue
    bucket_path = Path("s3://shimomut-files/")
    
    print(f"Listing contents of: {bucket_path}")
    print()
    
    try:
        entries = list(bucket_path.iterdir())
        
        if not entries:
            print("No entries found in bucket")
            return
        
        print(f"Found {len(entries)} entries:")
        print()
        
        for i, entry in enumerate(entries, 1):
            name = entry.name
            is_dir = entry.is_dir()
            is_file = entry.is_file()
            
            # Show the fix in action
            entry_type = "Directory" if is_dir else "File"
            size_info = ""
            
            if is_file:
                try:
                    stat_info = entry.stat()
                    size_info = f" ({stat_info.st_size} bytes)"
                except Exception:
                    size_info = " (size unknown)"
            
            print(f"{i:2d}. {entry_type}: '{name}'{size_info}")
            print(f"    Full path: {entry}")
            
            # Show internal details for debugging
            if hasattr(entry, '_impl'):
                print(f"    Internal key: '{entry._impl._key}'")
            print()
        
        # Verify no empty names
        empty_names = [entry for entry in entries if not entry.name.strip()]
        if empty_names:
            print(f"⚠ WARNING: Found {len(empty_names)} entries with empty names!")
            for entry in empty_names:
                print(f"  - {entry}")
        else:
            print("✓ SUCCESS: All entries have proper names!")
            
    except Exception as e:
        print(f"Error listing bucket contents: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_s3_directory_names()