#!/usr/bin/env python3
"""
Demo: Tree expand/collapse cursor position fix

This demo verifies that the cursor stays on the correct node when
expanding or collapsing tree nodes in the directory diff viewer.

Test scenario:
1. Create two test directories with nested structure
2. Open directory diff viewer
3. Navigate to a node below a collapsed directory
4. Expand the directory above - cursor should stay on the same node
5. Collapse the directory - cursor should adjust appropriately
"""

import sys
import os
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_path import Path
from tfm_directory_diff_viewer import DirectoryDiffViewer
from ttk import TTKApplication, KeyEvent, KeyCode


def create_test_directories():
    """Create test directory structure."""
    # Create temporary directories
    temp_dir = tempfile.mkdtemp(prefix="tfm_tree_test_")
    left_dir = os.path.join(temp_dir, "left")
    right_dir = os.path.join(temp_dir, "right")
    
    os.makedirs(left_dir)
    os.makedirs(right_dir)
    
    # Create nested structure in left
    os.makedirs(os.path.join(left_dir, "dir1"))
    with open(os.path.join(left_dir, "dir1", "file1.txt"), "w") as f:
        f.write("Content 1\n")
    with open(os.path.join(left_dir, "dir1", "file2.txt"), "w") as f:
        f.write("Content 2\n")
    
    os.makedirs(os.path.join(left_dir, "dir2"))
    with open(os.path.join(left_dir, "dir2", "file3.txt"), "w") as f:
        f.write("Content 3\n")
    
    with open(os.path.join(left_dir, "file4.txt"), "w") as f:
        f.write("Content 4\n")
    
    # Create similar structure in right with some differences
    os.makedirs(os.path.join(right_dir, "dir1"))
    with open(os.path.join(right_dir, "dir1", "file1.txt"), "w") as f:
        f.write("Content 1\n")  # Same
    with open(os.path.join(right_dir, "dir1", "file2.txt"), "w") as f:
        f.write("Different content\n")  # Different
    
    os.makedirs(os.path.join(right_dir, "dir2"))
    with open(os.path.join(right_dir, "dir2", "file3.txt"), "w") as f:
        f.write("Content 3\n")  # Same
    
    with open(os.path.join(right_dir, "file4.txt"), "w") as f:
        f.write("Content 4\n")  # Same
    
    return temp_dir, Path(left_dir), Path(right_dir)


def main():
    """Run the demo."""
    print("Creating test directories...")
    temp_dir, left_path, right_path = create_test_directories()
    
    try:
        print(f"Left:  {left_path}")
        print(f"Right: {right_path}")
        print("\nStarting directory diff viewer...")
        print("\nTest instructions:")
        print("1. Wait for scan to complete")
        print("2. Use DOWN arrow to move cursor to 'file4.txt' (below dir1 and dir2)")
        print("3. Press RIGHT or ENTER on 'dir1' to expand it")
        print("4. Notice cursor stays on 'file4.txt' (doesn't jump)")
        print("5. Press LEFT on 'dir1' to collapse it")
        print("6. Notice cursor stays on 'file4.txt'")
        print("7. Move cursor to a file inside dir1, then collapse dir1")
        print("8. Notice cursor moves to dir1 (parent)")
        print("\nPress Q or ESC to quit\n")
        
        # Create TTK application
        app = TTKApplication()
        
        # Create directory diff viewer
        viewer = DirectoryDiffViewer(
            app.renderer,
            left_path,
            right_path,
            layer_stack=None
        )
        
        # Push viewer onto layer stack
        app.layer_stack.push(viewer)
        
        # Run application
        app.run()
        
    finally:
        # Cleanup
        print("\nCleaning up test directories...")
        shutil.rmtree(temp_dir)
        print("Done!")


if __name__ == "__main__":
    main()
