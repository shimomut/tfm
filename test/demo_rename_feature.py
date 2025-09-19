#!/usr/bin/env python3
"""
Demo script for the rename feature in TFM
Creates test files and shows how to use the rename functionality
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def create_demo_files():
    """Create demo files for testing rename functionality"""
    print("Creating demo files for rename testing...")
    
    # Create demo directory in current directory
    demo_dir = Path("rename_demo")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    
    demo_dir.mkdir()
    
    # Create various test files
    test_files = [
        "document.txt",
        "image.jpg", 
        "script.py",
        "data.csv",
        "readme.md"
    ]
    
    test_dirs = [
        "folder1",
        "folder2", 
        "temp_dir"
    ]
    
    # Create test files
    for filename in test_files:
        file_path = demo_dir / filename
        file_path.write_text(f"This is a test file: {filename}")
        print(f"Created: {file_path}")
    
    # Create test directories
    for dirname in test_dirs:
        dir_path = demo_dir / dirname
        dir_path.mkdir()
        
        # Add a file inside each directory
        (dir_path / "inside.txt").write_text(f"File inside {dirname}")
        print(f"Created: {dir_path}/")
    
    print(f"\nDemo files created in: {demo_dir.absolute()}")
    print("\nTo test rename functionality:")
    print("1. Run TFM: python tfm.py")
    print("2. Navigate to the rename_demo directory")
    print("3. Select a file or directory")
    print("4. Press 'r' or 'R' to rename")
    print("5. Type the new name and press Enter")
    print("6. Press ESC to cancel rename")
    print("\nNote: Rename only works when no files are selected (bulk rename not implemented yet)")
    
    return demo_dir

def cleanup_demo_files():
    """Clean up demo files"""
    demo_dir = Path("rename_demo")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
        print(f"Cleaned up: {demo_dir}")

if __name__ == "__main__":
    print("TFM Rename Feature Demo")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_demo_files()
    else:
        demo_dir = create_demo_files()
        
        print("\n" + "=" * 40)
        print("Demo setup complete!")
        print(f"Run 'python {sys.argv[0]} cleanup' to remove demo files")