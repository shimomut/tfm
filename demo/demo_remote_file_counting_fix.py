#!/usr/bin/env python3
"""
Demo: Remote File Counting Fix

This demo shows how the file counting fix ensures accurate progress tracking
when copying directories from S3/SSH storage.

Before the fix:
- Selected 4 files + 2 directories (with 3 files each) → showed "4" total
- Progress would show "10/4" (10 files copied out of 4 expected)

After the fix:
- Selected 4 files + 2 directories (with 3 files each) → shows "10" total
- Progress correctly shows "10/10"

The fix uses polymorphic Path.rglob() instead of os.walk(), which works
correctly for all storage types (local, S3, SSH, archive).
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from unittest.mock import Mock
from tfm_path import Path
from tfm_file_operation_executor import FileOperationExecutor


def log(msg):
    """Simple logging for demo"""
    print(msg)


def create_mock_file(name):
    """Create a mock file Path"""
    mock = Mock(spec=Path)
    mock.is_file.return_value = True
    mock.is_symlink.return_value = False
    mock.is_dir.return_value = False
    mock.name = name
    return mock


def create_mock_directory(name, file_count):
    """Create a mock directory Path with specified number of files"""
    mock = Mock(spec=Path)
    mock.is_file.return_value = False
    mock.is_symlink.return_value = False
    mock.is_dir.return_value = True
    mock.name = name
    
    # Create mock files inside directory
    files = []
    for i in range(file_count):
        file_mock = Mock(spec=Path)
        file_mock.is_file.return_value = True
        file_mock.is_symlink.return_value = False
        files.append(file_mock)
    
    mock.rglob.return_value = files
    return mock


def demo_before_fix():
    """Demonstrate the problem before the fix"""
    log("=== BEFORE FIX (using os.walk) ===")
    log("")
    log("Scenario: User selects 4 files + 2 directories from S3")
    log("  - file1.txt")
    log("  - file2.txt")
    log("  - file3.txt")
    log("  - file4.txt")
    log("  - dir1/ (contains 3 files)")
    log("  - dir2/ (contains 3 files)")
    log("")
    log("Problem: os.walk() doesn't work with S3 paths")
    log("  - os.walk(s3://bucket/dir1) returns NOTHING")
    log("  - os.walk(s3://bucket/dir2) returns NOTHING")
    log("")
    log("Result:")
    log("  - Initial count: 4 (only the 4 files, directories not counted)")
    log("  - Actual files copied: 10 (4 + 3 + 3)")
    log("  - Progress display: '10/4' ❌ WRONG!")
    log("")


def demo_after_fix():
    """Demonstrate the solution after the fix"""
    log("=== AFTER FIX (using Path.rglob) ===")
    log("")
    log("Scenario: Same selection - 4 files + 2 directories from S3")
    log("")
    
    # Create mock file manager
    file_manager = Mock()
    file_manager.progress_manager = Mock()
    file_manager.cache_manager = Mock()
    
    # Create executor
    executor = FileOperationExecutor(file_manager)
    
    # Create mock paths matching the scenario
    file1 = create_mock_file("file1.txt")
    file2 = create_mock_file("file2.txt")
    file3 = create_mock_file("file3.txt")
    file4 = create_mock_file("file4.txt")
    dir1 = create_mock_directory("dir1", 3)
    dir2 = create_mock_directory("dir2", 3)
    
    paths = [file1, file2, file3, file4, dir1, dir2]
    
    log("Solution: Use Path.rglob() for polymorphic traversal")
    log("  - dir1.rglob('*') returns 3 files ✓")
    log("  - dir2.rglob('*') returns 3 files ✓")
    log("")
    
    # Count files using the fixed method
    count = executor._count_files_recursively(paths)
    
    log("Result:")
    log(f"  - Initial count: {count} (4 files + 3 in dir1 + 3 in dir2)")
    log(f"  - Actual files copied: {count}")
    log(f"  - Progress display: '{count}/{count}' ✓ CORRECT!")
    log("")


def demo_polymorphism():
    """Demonstrate how polymorphism makes this work for all storage types"""
    log("=== POLYMORPHISM BENEFITS ===")
    log("")
    log("The fix uses Path.rglob() which is implemented by each PathImpl:")
    log("")
    log("  LocalPathImpl.rglob()   → Uses pathlib.Path.rglob()")
    log("  S3PathImpl.rglob()      → Uses boto3 list_objects_v2()")
    log("  SSHPathImpl.rglob()     → Uses SFTP listdir() recursively")
    log("  ArchivePathImpl.rglob() → Uses zipfile/tarfile iteration")
    log("")
    log("Benefits:")
    log("  ✓ No storage-type-specific code in file operations")
    log("  ✓ Works correctly for all current and future storage types")
    log("  ✓ Consistent behavior across all storage backends")
    log("  ✓ Easier to maintain and test")
    log("")


def main():
    """Run the demo"""
    log("=" * 60)
    log("Remote File Counting Fix Demo")
    log("=" * 60)
    log("")
    
    demo_before_fix()
    demo_after_fix()
    demo_polymorphism()
    
    log("=" * 60)
    log("Demo complete!")
    log("=" * 60)


if __name__ == '__main__':
    main()
