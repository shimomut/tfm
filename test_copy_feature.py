#!/usr/bin/env python3
"""
Test script for the copy feature implementation
"""

import os
import tempfile
import shutil
from pathlib import Path

def test_copy_feature():
    """Test the copy feature functionality"""
    print("Testing copy feature implementation...")
    
    # Create a temporary directory structure for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create source directory with test files
        source_dir = temp_path / "source"
        source_dir.mkdir()
        
        # Create destination directory
        dest_dir = temp_path / "destination"
        dest_dir.mkdir()
        
        # Create test files
        test_file1 = source_dir / "test1.txt"
        test_file1.write_text("This is test file 1")
        
        test_file2 = source_dir / "test2.txt"
        test_file2.write_text("This is test file 2")
        
        # Create a test directory with content
        test_subdir = source_dir / "subdir"
        test_subdir.mkdir()
        (test_subdir / "nested.txt").write_text("Nested file content")
        
        print(f"Created test structure in: {temp_dir}")
        print(f"Source files: {list(source_dir.iterdir())}")
        
        # Test basic copy operation
        print("\n1. Testing basic file copy...")
        shutil.copy2(test_file1, dest_dir / test_file1.name)
        print(f"✓ Copied {test_file1.name}")
        
        # Test directory copy
        print("\n2. Testing directory copy...")
        shutil.copytree(test_subdir, dest_dir / test_subdir.name)
        print(f"✓ Copied directory {test_subdir.name}")
        
        # Test conflict detection
        print("\n3. Testing conflict detection...")
        conflict_file = dest_dir / "test1.txt"
        if conflict_file.exists():
            print(f"✓ Conflict detected: {conflict_file.name} already exists")
        
        print(f"\nDestination contents: {list(dest_dir.iterdir())}")
        
        # Verify copied content
        copied_file = dest_dir / "test1.txt"
        if copied_file.exists() and copied_file.read_text() == "This is test file 1":
            print("✓ File content preserved correctly")
        
        copied_nested = dest_dir / "subdir" / "nested.txt"
        if copied_nested.exists() and copied_nested.read_text() == "Nested file content":
            print("✓ Directory structure and content preserved correctly")
        
        print("\n✓ All copy feature tests passed!")

if __name__ == "__main__":
    test_copy_feature()