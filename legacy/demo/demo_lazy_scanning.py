#!/usr/bin/env python3
"""
Demo: Lazy Scanning for One-Sided Directories

This demo demonstrates the lazy scanning feature where directories that exist
only on one side (left or right) are not automatically scanned in the background.
Instead, they are only scanned when the user explicitly expands them.

This optimization significantly improves performance when comparing directories
with large one-sided subtrees.

Usage:
    python3 demo/demo_lazy_scanning.py
"""

import sys
import os
import tempfile
import shutil

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_directory_diff_viewer import DirectoryDiffViewer
from ttk import TTKApplication


def create_demo_directories():
    """
    Create demo directory structure with one-sided directories.
    
    Structure demonstrates:
    - Directories that exist on both sides (will be scanned automatically)
    - Directories that exist only on left (lazy scanned)
    - Directories that exist only on right (lazy scanned)
    - Deep nested structures in one-sided directories
    """
    # Create temporary directories
    temp_dir = tempfile.mkdtemp(prefix="demo_lazy_scan_")
    left_dir = os.path.join(temp_dir, "left")
    right_dir = os.path.join(temp_dir, "right")
    
    os.makedirs(left_dir)
    os.makedirs(right_dir)
    
    print(f"Created demo directories:")
    print(f"  Left:  {left_dir}")
    print(f"  Right: {right_dir}")
    print()
    
    # Create directories that exist on both sides
    print("Creating directories on both sides (will be scanned automatically):")
    os.makedirs(os.path.join(left_dir, "shared"))
    os.makedirs(os.path.join(right_dir, "shared"))
    
    # Add some files
    with open(os.path.join(left_dir, "shared", "file1.txt"), "w") as f:
        f.write("shared content")
    with open(os.path.join(right_dir, "shared", "file1.txt"), "w") as f:
        f.write("shared content")
    
    print("  ✓ shared/ (exists on both sides)")
    print()
    
    # Create large directory structure only on left
    print("Creating large directory structure only on LEFT (lazy scanned):")
    left_only_base = os.path.join(left_dir, "left_only_project")
    os.makedirs(left_only_base)
    
    # Create multiple nested directories
    for i in range(5):
        dir_path = os.path.join(left_only_base, f"module_{i}")
        os.makedirs(dir_path)
        
        # Create subdirectories
        for j in range(3):
            subdir_path = os.path.join(dir_path, f"submodule_{j}")
            os.makedirs(subdir_path)
            
            # Create files
            for k in range(10):
                file_path = os.path.join(subdir_path, f"file_{k}.txt")
                with open(file_path, "w") as f:
                    f.write(f"Content for module {i}, submodule {j}, file {k}")
    
    print(f"  ✓ left_only_project/ (5 modules × 3 submodules × 10 files = 150 files)")
    print(f"    This will NOT be scanned automatically!")
    print(f"    It will only be scanned when you expand it.")
    print()
    
    # Create large directory structure only on right
    print("Creating large directory structure only on RIGHT (lazy scanned):")
    right_only_base = os.path.join(right_dir, "right_only_backup")
    os.makedirs(right_only_base)
    
    # Create multiple nested directories
    for i in range(3):
        dir_path = os.path.join(right_only_base, f"backup_{i}")
        os.makedirs(dir_path)
        
        # Create subdirectories
        for j in range(4):
            subdir_path = os.path.join(dir_path, f"archive_{j}")
            os.makedirs(subdir_path)
            
            # Create files
            for k in range(20):
                file_path = os.path.join(subdir_path, f"backup_{k}.dat")
                with open(file_path, "w") as f:
                    f.write(f"Backup data for {i}/{j}/{k}")
    
    print(f"  ✓ right_only_backup/ (3 backups × 4 archives × 20 files = 240 files)")
    print(f"    This will NOT be scanned automatically!")
    print(f"    It will only be scanned when you expand it.")
    print()
    
    # Create some more shared directories
    os.makedirs(os.path.join(left_dir, "docs"))
    os.makedirs(os.path.join(right_dir, "docs"))
    with open(os.path.join(left_dir, "docs", "README.md"), "w") as f:
        f.write("# Documentation")
    with open(os.path.join(right_dir, "docs", "README.md"), "w") as f:
        f.write("# Documentation")
    
    print("  ✓ docs/ (exists on both sides)")
    print()
    
    return temp_dir, left_dir, right_dir


def main():
    """Run the lazy scanning demo."""
    print("=" * 70)
    print("DEMO: Lazy Scanning for One-Sided Directories")
    print("=" * 70)
    print()
    print("This demo shows how the Directory Diff Viewer optimizes performance")
    print("by NOT automatically scanning directories that exist only on one side.")
    print()
    print("Key features:")
    print("  • Directories on both sides are scanned automatically")
    print("  • One-sided directories show '...' indicator")
    print("  • One-sided directories are scanned only when you expand them")
    print("  • This saves time when comparing directories with large one-sided trees")
    print()
    print("=" * 70)
    print()
    
    # Create demo directories
    temp_dir, left_dir, right_dir = create_demo_directories()
    
    try:
        print("=" * 70)
        print("INSTRUCTIONS:")
        print("=" * 70)
        print()
        print("1. The viewer will open showing the top-level directories")
        print("2. Notice that 'left_only_project' and 'right_only_backup' show '...'")
        print("3. Try expanding 'shared' or 'docs' - they load instantly (already scanned)")
        print("4. Try expanding 'left_only_project' - it will scan on-demand")
        print("5. Notice the '[scanning...]' indicator while it scans")
        print("6. The nested directories inside will also be lazy-scanned")
        print()
        print("Press any key to start the demo...")
        input()
        
        # Create TTK application
        app = TTKApplication()
        
        # Create directory diff viewer
        viewer = DirectoryDiffViewer(
            app.renderer,
            Path(left_dir),
            Path(right_dir)
        )
        
        # Push viewer onto layer stack
        app.layer_stack.push(viewer)
        
        # Run the application
        app.run()
        
    finally:
        # Clean up temporary directories
        print("\nCleaning up temporary directories...")
        shutil.rmtree(temp_dir)
        print("Done!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
