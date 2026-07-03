#!/usr/bin/env python3
"""
Demo: Natural Sorting Feature

This demo demonstrates TFM's natural sorting capability for filenames with numeric parts.

Natural sorting treats numeric sequences as numbers rather than strings, so:
- "Test1.txt" comes before "Test10.txt" (not after as in dictionary order)
- "file2.txt" comes before "file10.txt"
- Leading zeros are handled correctly: "file001.txt" < "file010.txt"

The demo creates a temporary directory with test files that showcase natural sorting.
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'ttk'))

from tfm_main import FileManager
from tfm_log_manager import getLogger

logger = getLogger("NatSortDemo")


def create_test_files(test_dir):
    """Create test files that demonstrate natural sorting"""
    
    # Create files with numeric sequences
    test_files = [
        "Test1.txt",
        "Test2.txt",
        "Test3.txt",
        "Test10.txt",
        "Test11.txt",
        "Test100.txt",
        "file1-part2.txt",
        "file1-part10.txt",
        "file2-part1.txt",
        "Report001.pdf",
        "Report002.pdf",
        "Report010.pdf",
        "Report100.pdf",
        "Chapter1.md",
        "Chapter2.md",
        "Chapter10.md",
        "Chapter20.md",
        "Image1.jpg",
        "Image5.jpg",
        "Image10.jpg",
        "Image50.jpg",
        "Image100.jpg",
    ]
    
    # Create directories with numeric sequences
    test_dirs = [
        "Dir1",
        "Dir2",
        "Dir10",
        "Dir20",
        "Folder1",
        "Folder10",
        "Folder100",
    ]
    
    for filename in test_files:
        (test_dir / filename).touch()
    
    for dirname in test_dirs:
        (test_dir / dirname).mkdir()
    
    logger.info(f"Created {len(test_files)} test files and {len(test_dirs)} test directories")
    logger.info(f"Test directory: {test_dir}")


def main():
    """Run the natural sorting demo"""
    
    # Create temporary directory for demo
    temp_dir = Path(tempfile.mkdtemp(prefix="tfm_natural_sort_demo_"))
    
    try:
        logger.info("=" * 70)
        logger.info("TFM Natural Sorting Demo")
        logger.info("=" * 70)
        logger.info("")
        logger.info("This demo showcases natural sorting of filenames with numeric parts.")
        logger.info("")
        logger.info("Natural sorting treats numbers as numbers, not strings:")
        logger.info("  Dictionary order: Test1, Test10, Test100, Test2, Test3")
        logger.info("  Natural order:    Test1, Test2, Test3, Test10, Test100")
        logger.info("")
        logger.info("Creating test files...")
        logger.info("")
        
        create_test_files(temp_dir)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("Starting TFM in demo directory...")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Instructions:")
        logger.info("  - Files are sorted naturally by default (sort by Name)")
        logger.info("  - Notice how Test1, Test2, Test3 come before Test10, Test11, Test100")
        logger.info("  - Same applies to directories: Dir1, Dir2 come before Dir10, Dir20")
        logger.info("  - Press 's' to open sort menu and try different sort modes")
        logger.info("  - Press 'q' to quit when done")
        logger.info("")
        input("Press Enter to start TFM...")
        
        # Start TFM in the test directory
        file_manager = FileManager(initial_dir=str(temp_dir))
        file_manager.run()
        
    finally:
        # Clean up temporary directory
        logger.info("")
        logger.info("Cleaning up temporary directory...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info("Demo complete!")


if __name__ == '__main__':
    main()
