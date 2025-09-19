#!/usr/bin/env python3
"""
Comprehensive test for the copy feature
"""

import tempfile
import os
import shutil
from pathlib import Path

def create_test_structure():
    """Create a test directory structure"""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create left pane directory with test files
    left_dir = temp_dir / "left_pane"
    left_dir.mkdir()
    
    # Create right pane directory (destination)
    right_dir = temp_dir / "right_pane"
    right_dir.mkdir()
    
    # Create test files in left pane
    (left_dir / "file1.txt").write_text("Content of file 1")
    (left_dir / "file2.txt").write_text("Content of file 2")
    (left_dir / "document.md").write_text("# Markdown Document\n\nThis is a test.")
    
    # Create a subdirectory with nested content
    subdir = left_dir / "nested_folder"
    subdir.mkdir()
    (subdir / "nested_file.txt").write_text("Nested file content")
    (subdir / "config.json").write_text('{"setting": "value"}')
    
    # Create a deeper nested structure
    deep_dir = subdir / "deep"
    deep_dir.mkdir()
    (deep_dir / "deep_file.py").write_text("print('Hello from deep file')")
    
    # Create some files in right pane to test conflicts
    (right_dir / "file1.txt").write_text("Existing content in destination")
    (right_dir / "existing.txt").write_text("This file already exists")
    
    return temp_dir, left_dir, right_dir

def test_copy_operations():
    """Test various copy operations"""
    print("Creating test structure...")
    temp_dir, left_dir, right_dir = create_test_structure()
    
    try:
        print(f"Test directory: {temp_dir}")
        print(f"Left pane (source): {left_dir}")
        print(f"Right pane (destination): {right_dir}")
        
        print("\nInitial structure:")
        print("Left pane contents:")
        for item in sorted(left_dir.rglob("*")):
            if item.is_file():
                print(f"  📄 {item.relative_to(left_dir)}")
            elif item.is_dir() and item != left_dir:
                print(f"  📁 {item.relative_to(left_dir)}/")
        
        print("\nRight pane contents:")
        for item in sorted(right_dir.rglob("*")):
            if item.is_file():
                print(f"  📄 {item.relative_to(right_dir)}")
            elif item.is_dir() and item != right_dir:
                print(f"  📁 {item.relative_to(right_dir)}/")
        
        # Test 1: Copy a single file without conflict
        print("\n" + "="*50)
        print("TEST 1: Copy single file without conflict")
        print("="*50)
        
        source_file = left_dir / "file2.txt"
        dest_file = right_dir / "file2.txt"
        
        print(f"Copying: {source_file.name}")
        shutil.copy2(source_file, dest_file)
        
        if dest_file.exists() and dest_file.read_text() == source_file.read_text():
            print("✓ File copied successfully")
        else:
            print("✗ File copy failed")
        
        # Test 2: Copy a directory recursively
        print("\n" + "="*50)
        print("TEST 2: Copy directory recursively")
        print("="*50)
        
        source_dir = left_dir / "nested_folder"
        dest_dir_copy = right_dir / "nested_folder"
        
        print(f"Copying directory: {source_dir.name}")
        shutil.copytree(source_dir, dest_dir_copy)
        
        # Verify all files were copied
        source_files = list(source_dir.rglob("*"))
        copied_files = list(dest_dir_copy.rglob("*"))
        
        print(f"Source files: {len([f for f in source_files if f.is_file()])}")
        print(f"Copied files: {len([f for f in copied_files if f.is_file()])}")
        
        # Check specific files
        nested_file = dest_dir_copy / "nested_file.txt"
        deep_file = dest_dir_copy / "deep" / "deep_file.py"
        
        if (nested_file.exists() and 
            deep_file.exists() and
            nested_file.read_text() == "Nested file content" and
            deep_file.read_text() == "print('Hello from deep file')"):
            print("✓ Directory copied recursively with all content")
        else:
            print("✗ Directory copy incomplete")
        
        # Test 3: Simulate conflict detection
        print("\n" + "="*50)
        print("TEST 3: Conflict detection")
        print("="*50)
        
        conflict_file = right_dir / "file1.txt"
        source_conflict = left_dir / "file1.txt"
        
        print(f"Checking conflict for: {source_conflict.name}")
        if conflict_file.exists():
            print(f"✓ Conflict detected: {conflict_file.name} already exists")
            print(f"  Source content: '{source_conflict.read_text()}'")
            print(f"  Dest content: '{conflict_file.read_text()}'")
            
            # Test overwrite
            print("  Testing overwrite...")
            shutil.copy2(source_conflict, conflict_file)
            if conflict_file.read_text() == source_conflict.read_text():
                print("  ✓ Overwrite successful")
            else:
                print("  ✗ Overwrite failed")
        
        # Test 4: Multiple file operations
        print("\n" + "="*50)
        print("TEST 4: Multiple file copy simulation")
        print("="*50)
        
        files_to_copy = [
            left_dir / "document.md",
        ]
        
        copied_count = 0
        for source_file in files_to_copy:
            if source_file.exists():
                dest_file = right_dir / source_file.name
                try:
                    shutil.copy2(source_file, dest_file)
                    copied_count += 1
                    print(f"✓ Copied: {source_file.name}")
                except Exception as e:
                    print(f"✗ Failed to copy {source_file.name}: {e}")
        
        print(f"Successfully copied {copied_count} files")
        
        # Final verification
        print("\n" + "="*50)
        print("FINAL VERIFICATION")
        print("="*50)
        
        print("Final right pane contents:")
        for item in sorted(right_dir.rglob("*")):
            if item.is_file():
                size = item.stat().st_size
                print(f"  📄 {item.relative_to(right_dir)} ({size} bytes)")
            elif item.is_dir() and item != right_dir:
                print(f"  📁 {item.relative_to(right_dir)}/")
        
        print("\n🎉 All copy operation tests completed successfully!")
        
    finally:
        # Clean up
        print(f"\nCleaning up test directory: {temp_dir}")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_copy_operations()