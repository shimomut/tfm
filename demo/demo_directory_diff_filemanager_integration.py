#!/usr/bin/env python3
"""
Demo: Directory Diff Viewer FileManager Integration

This demo shows how to invoke the directory diff viewer from FileManager
using the @ key binding (or by calling show_directory_diff() directly).

The directory diff viewer compares the left and right pane directories
recursively and displays the differences in a tree structure.

Usage:
    python demo/demo_directory_diff_filemanager_integration.py

Key bindings:
    @       - Open directory diff viewer (compares left and right panes)
    Tab     - Switch between left and right panes
    q       - Quit

In the directory diff viewer:
    Up/Down - Navigate through the tree
    Enter   - Expand/collapse directories
    ESC/q   - Close the viewer and return to FileManager
    v       - View diff for content-different files
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path as StdPath

# Add src to path
sys.path.insert(0, 'src')

from tfm_main import FileManager
from tfm_backend_selector import select_backend


def create_test_directories():
    """Create test directory structures for demonstration"""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="tfm_demo_")
    
    # Create left directory structure
    left_dir = StdPath(temp_dir) / "left"
    left_dir.mkdir()
    
    (left_dir / "common_file.txt").write_text("This file exists in both directories")
    (left_dir / "left_only.txt").write_text("This file only exists in the left directory")
    (left_dir / "modified.txt").write_text("Original content")
    
    left_subdir = left_dir / "subdir"
    left_subdir.mkdir()
    (left_subdir / "nested_file.txt").write_text("Nested file in left")
    
    # Create right directory structure
    right_dir = StdPath(temp_dir) / "right"
    right_dir.mkdir()
    
    (right_dir / "common_file.txt").write_text("This file exists in both directories")
    (right_dir / "right_only.txt").write_text("This file only exists in the right directory")
    (right_dir / "modified.txt").write_text("Modified content")
    
    right_subdir = right_dir / "subdir"
    right_subdir.mkdir()
    (right_subdir / "nested_file.txt").write_text("Nested file in right - different content")
    (right_subdir / "right_nested.txt").write_text("Only in right subdir")
    
    print(f"Created test directories:")
    print(f"  Left:  {left_dir}")
    print(f"  Right: {right_dir}")
    print()
    print("Directory structure:")
    print("  Left:")
    print("    - common_file.txt (identical)")
    print("    - left_only.txt (only in left)")
    print("    - modified.txt (different content)")
    print("    - subdir/")
    print("      - nested_file.txt (different content)")
    print()
    print("  Right:")
    print("    - common_file.txt (identical)")
    print("    - right_only.txt (only in right)")
    print("    - modified.txt (different content)")
    print("    - subdir/")
    print("      - nested_file.txt (different content)")
    print("      - right_nested.txt (only in right)")
    print()
    
    return temp_dir, str(left_dir), str(right_dir)


def main():
    """Run the demo"""
    print("=" * 70)
    print("Directory Diff Viewer FileManager Integration Demo")
    print("=" * 70)
    print()
    
    # Create test directories
    temp_dir, left_dir, right_dir = create_test_directories()
    
    try:
        print("Starting TFM with test directories...")
        print()
        print("Instructions:")
        print("  1. Press @ to open the directory diff viewer")
        print("  2. Use Up/Down to navigate the tree")
        print("  3. Press Enter to expand/collapse directories")
        print("  4. Press v on content-different files to view the diff")
        print("  5. Press ESC or q to close the viewer")
        print("  6. Press q in FileManager to quit")
        print()
        print("Press Enter to continue...")
        input()
        
        # Select backend and create renderer
        backend = select_backend()
        renderer = backend.create_renderer()
        
        # Create FileManager with test directories
        file_manager = FileManager(
            renderer,
            left_dir=left_dir,
            right_dir=right_dir
        )
        
        # Run the main loop
        backend.run(renderer)
        
    finally:
        # Clean up temporary directory
        print()
        print(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)
        print("Demo complete!")


if __name__ == '__main__':
    main()
