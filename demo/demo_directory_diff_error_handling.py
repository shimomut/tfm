#!/usr/bin/env python3
"""
Demo: Directory Diff Viewer Error Handling

This demo demonstrates the error handling capabilities of the Directory Diff Viewer:
1. Permission errors during scanning
2. I/O errors during file comparison
3. Empty directories
4. Identical directories

The demo creates test directory structures and shows how the viewer handles various error conditions.
"""

import tempfile
import os
from pathlib import Path as StdPath

from src.tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_path import Path
from ttk import TTKApplication


def create_test_directories_with_errors():
    """
    Create test directory structures with various error conditions.
    
    Returns:
        Tuple of (left_dir, right_dir) paths
    """
    # Create temporary directories
    tmpdir = tempfile.mkdtemp(prefix="tfm_diff_error_test_")
    left_dir = StdPath(tmpdir) / "left"
    right_dir = StdPath(tmpdir) / "right"
    left_dir.mkdir()
    right_dir.mkdir()
    
    print(f"Created test directories:")
    print(f"  Left:  {left_dir}")
    print(f"  Right: {right_dir}")
    print()
    
    # Create some normal files
    (left_dir / "normal.txt").write_text("This is a normal file")
    (right_dir / "normal.txt").write_text("This is a normal file")
    
    # Create files that exist only on one side
    (left_dir / "only_left.txt").write_text("Only in left")
    (right_dir / "only_right.txt").write_text("Only in right")
    
    # Create files with different content
    (left_dir / "different.txt").write_text("Left version")
    (right_dir / "different.txt").write_text("Right version")
    
    # Create a subdirectory with files
    (left_dir / "subdir").mkdir()
    (right_dir / "subdir").mkdir()
    (left_dir / "subdir" / "file1.txt").write_text("File 1")
    (right_dir / "subdir" / "file1.txt").write_text("File 1")
    
    # Create a file that we'll make unreadable (permission error simulation)
    # Note: On some systems, this might not work as expected due to user permissions
    restricted_file = left_dir / "restricted.txt"
    restricted_file.write_text("This file will be restricted")
    try:
        os.chmod(restricted_file, 0o000)  # Remove all permissions
        print("Created restricted file (permission error simulation)")
    except Exception as e:
        print(f"Note: Could not restrict file permissions: {e}")
    
    print()
    print("Test directory structure created:")
    print("  - normal.txt (identical in both)")
    print("  - only_left.txt (only in left)")
    print("  - only_right.txt (only in right)")
    print("  - different.txt (different content)")
    print("  - subdir/file1.txt (identical in both)")
    print("  - restricted.txt (permission error - left only)")
    print()
    
    return str(left_dir), str(right_dir)


def create_empty_directories():
    """
    Create empty test directories.
    
    Returns:
        Tuple of (left_dir, right_dir) paths
    """
    tmpdir = tempfile.mkdtemp(prefix="tfm_diff_empty_test_")
    left_dir = StdPath(tmpdir) / "left"
    right_dir = StdPath(tmpdir) / "right"
    left_dir.mkdir()
    right_dir.mkdir()
    
    print(f"Created empty test directories:")
    print(f"  Left:  {left_dir}")
    print(f"  Right: {right_dir}")
    print()
    
    return str(left_dir), str(right_dir)


def create_identical_directories():
    """
    Create identical test directories.
    
    Returns:
        Tuple of (left_dir, right_dir) paths
    """
    tmpdir = tempfile.mkdtemp(prefix="tfm_diff_identical_test_")
    left_dir = StdPath(tmpdir) / "left"
    right_dir = StdPath(tmpdir) / "right"
    left_dir.mkdir()
    right_dir.mkdir()
    
    # Create identical files
    (left_dir / "file1.txt").write_text("Identical content")
    (right_dir / "file1.txt").write_text("Identical content")
    
    (left_dir / "file2.txt").write_text("Also identical")
    (right_dir / "file2.txt").write_text("Also identical")
    
    # Create identical subdirectory
    (left_dir / "subdir").mkdir()
    (right_dir / "subdir").mkdir()
    (left_dir / "subdir" / "nested.txt").write_text("Nested file")
    (right_dir / "subdir" / "nested.txt").write_text("Nested file")
    
    print(f"Created identical test directories:")
    print(f"  Left:  {left_dir}")
    print(f"  Right: {right_dir}")
    print()
    print("Both directories contain:")
    print("  - file1.txt (identical)")
    print("  - file2.txt (identical)")
    print("  - subdir/nested.txt (identical)")
    print()
    
    return str(left_dir), str(right_dir)


def main():
    """Main demo function."""
    print("=" * 80)
    print("Directory Diff Viewer - Error Handling Demo")
    print("=" * 80)
    print()
    print("This demo shows how the Directory Diff Viewer handles:")
    print("  1. Permission errors during scanning")
    print("  2. I/O errors during file comparison")
    print("  3. Empty directories")
    print("  4. Identical directories")
    print()
    print("Choose a test scenario:")
    print("  1. Directories with errors (permission errors, different files)")
    print("  2. Empty directories")
    print("  3. Identical directories")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    print()
    
    if choice == "1":
        left_dir, right_dir = create_test_directories_with_errors()
        print("Starting Directory Diff Viewer with error test directories...")
    elif choice == "2":
        left_dir, right_dir = create_empty_directories()
        print("Starting Directory Diff Viewer with empty directories...")
    elif choice == "3":
        left_dir, right_dir = create_identical_directories()
        print("Starting Directory Diff Viewer with identical directories...")
    else:
        print("Invalid choice. Exiting.")
        return
    
    print()
    print("Instructions:")
    print("  - Use ↑↓ to navigate")
    print("  - Use ←→ or Enter to expand/collapse directories")
    print("  - Press 'i' to toggle showing identical files")
    print("  - Press 'q' or ESC to quit")
    print("  - Look for ⚠ symbols indicating errors")
    print()
    print("Press Enter to start...")
    input()
    
    # Create and run the application
    app = TTKApplication()
    
    def create_viewer(renderer):
        return DirectoryDiffViewer(renderer, Path(left_dir), Path(right_dir))
    
    app.run(create_viewer)
    
    print()
    print("Demo completed.")
    print()
    print("Note: Test directories were created in temporary location.")
    print("They will be cleaned up automatically by the system.")


if __name__ == "__main__":
    main()
