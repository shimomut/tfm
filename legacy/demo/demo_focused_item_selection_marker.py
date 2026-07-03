#!/usr/bin/env python3
"""
Demo: Focused Item Selection Marker Background Fix

This demo shows that the focused item's special background color is NOT applied
to the selection indicator (left 2 char width). The selection marker should
always use the status bar color, while the filename/size/date portion uses
the focused background color.

Visual Test:
1. Launch the demo
2. Navigate through files with arrow keys
3. Observe that the focused item has a colored background
4. Verify that the selection marker (● or space) does NOT have the focused background
5. Press Space to select/deselect files
6. Verify selected files show ● marker without focused background
"""

import sys
import os
from pathlib import Path as StdPath

# Add src and ttk to path
sys.path.insert(0, str(StdPath(__file__).parent.parent / 'src'))
sys.path.insert(0, str(StdPath(__file__).parent.parent / 'ttk'))

import tempfile
from tfm_main import TUIFileManager
from tfm_backend_selector import select_backend


def create_test_directory():
    """Create a temporary directory with test files"""
    temp_dir = tempfile.mkdtemp(prefix='tfm_demo_focused_')
    
    # Create various test files
    test_files = [
        'document.txt',
        'image.png',
        'script.py',
        'data.json',
        'readme.md',
        'config.yaml',
        'archive.zip',
        'video.mp4',
    ]
    
    for filename in test_files:
        filepath = StdPath(temp_dir) / filename
        filepath.write_text(f"Test content for {filename}\n")
    
    # Create a subdirectory
    subdir = StdPath(temp_dir) / 'subdirectory'
    subdir.mkdir()
    (subdir / 'nested_file.txt').write_text("Nested content\n")
    
    return temp_dir


def main():
    print("=" * 70)
    print("Focused Item Selection Marker Background Fix Demo")
    print("=" * 70)
    print()
    print("This demo verifies that the focused item's background color")
    print("does NOT apply to the selection marker (left 2 characters).")
    print()
    print("Instructions:")
    print("  1. Use arrow keys to navigate through files")
    print("  2. Observe the focused item has a colored background")
    print("  3. Verify the selection marker (● or space) has NO background")
    print("  4. Press Space to select/deselect files")
    print("  5. Press Q to quit")
    print()
    print("Expected behavior:")
    print("  - Focused item: filename/size/date has colored background")
    print("  - Selection marker: always uses status bar color (no background)")
    print()
    input("Press Enter to start the demo...")
    
    # Create test directory
    test_dir = create_test_directory()
    print(f"\nCreated test directory: {test_dir}")
    print("Starting TFM...")
    
    try:
        # Select backend and create renderer
        backend_module = select_backend()
        renderer = backend_module.create_renderer()
        
        # Initialize and run TFM
        tfm = TUIFileManager(renderer, StdPath(test_dir), StdPath(test_dir))
        tfm.run()
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        print(f"\nCleaned up test directory: {test_dir}")


if __name__ == '__main__':
    main()
