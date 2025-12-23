#!/usr/bin/env python3
"""
Demo: Progressive Scanning in Directory Diff Viewer

This demo demonstrates the progressive scanning feature with large directory structures.
It shows:
1. Immediate display of top-level items (< 100ms)
2. Progressive background scanning of subdirectories
3. Priority-based scanning of visible items
4. Visual indicators for pending/scanning status

The demo creates two large directory structures with 1000+ files to showcase
the performance improvements of progressive scanning.
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_path import Path as TFMPath


def create_large_directory_structure(base_path: Path, name: str, num_files: int = 1000):
    """
    Create a large directory structure for testing progressive scanning.
    
    Structure:
    - 10 top-level directories
    - Each with 10 subdirectories
    - Each subdirectory with ~10 files
    - Total: ~1000 files
    """
    root = base_path / name
    root.mkdir(exist_ok=True)
    
    print(f"Creating {name} with {num_files} files...")
    
    files_per_subdir = max(1, num_files // 100)
    
    for i in range(10):
        top_dir = root / f"category_{i:02d}"
        top_dir.mkdir(exist_ok=True)
        
        for j in range(10):
            sub_dir = top_dir / f"subcategory_{j:02d}"
            sub_dir.mkdir(exist_ok=True)
            
            for k in range(files_per_subdir):
                file_path = sub_dir / f"file_{k:03d}.txt"
                with open(file_path, 'w') as f:
                    f.write(f"Content for {file_path.name}\n")
                    f.write(f"Category: {i}, Subcategory: {j}, File: {k}\n")
    
    print(f"  Created {name} successfully")
    return root


def create_directory_with_differences(base_path: Path, name: str, num_files: int = 1000):
    """
    Create a directory structure with intentional differences for comparison.
    
    Differences include:
    - Some files only in left
    - Some files only in right
    - Some files with different content
    - Some identical files
    """
    root = base_path / name
    root.mkdir(exist_ok=True)
    
    print(f"Creating {name} with differences...")
    
    files_per_subdir = max(1, num_files // 100)
    
    for i in range(10):
        top_dir = root / f"category_{i:02d}"
        top_dir.mkdir(exist_ok=True)
        
        # Add some directories only in right
        if i % 3 == 0:
            extra_dir = top_dir / f"extra_subcategory"
            extra_dir.mkdir(exist_ok=True)
            for k in range(5):
                file_path = extra_dir / f"extra_file_{k:03d}.txt"
                with open(file_path, 'w') as f:
                    f.write(f"Extra content in right side\n")
        
        for j in range(10):
            # Skip some subdirectories to create only-left differences
            if i % 4 == 0 and j % 3 == 0:
                continue
                
            sub_dir = top_dir / f"subcategory_{j:02d}"
            sub_dir.mkdir(exist_ok=True)
            
            for k in range(files_per_subdir):
                file_path = sub_dir / f"file_{k:03d}.txt"
                
                # Create different content for some files
                if k % 5 == 0:
                    with open(file_path, 'w') as f:
                        f.write(f"MODIFIED content for {file_path.name}\n")
                        f.write(f"This file has been changed in the right side\n")
                else:
                    # Identical content
                    with open(file_path, 'w') as f:
                        f.write(f"Content for {file_path.name}\n")
                        f.write(f"Category: {i}, Subcategory: {j}, File: {k}\n")
    
    print(f"  Created {name} with differences successfully")
    return root


def print_instructions():
    """Print instructions for using the demo."""
    print("\n" + "="*70)
    print("PROGRESSIVE SCANNING DEMO")
    print("="*70)
    print("\nThis demo showcases progressive scanning with large directory structures.")
    print("\nKey Features to Observe:")
    print("  1. IMMEDIATE DISPLAY: Tree appears in < 100ms with top-level items")
    print("  2. PROGRESSIVE LOADING: Subdirectories load in background")
    print("  3. VISUAL INDICATORS: '...' shows unscanned directories")
    print("  4. PRIORITY SCANNING: Visible items load first")
    print("  5. ON-DEMAND SCANNING: Expanding unscanned dirs loads immediately")
    print("\nDirectory Structure:")
    print("  - 10 top-level categories")
    print("  - 100 subdirectories")
    print("  - ~1000 files total")
    print("  - Various differences (only-left, only-right, modified)")
    print("\nNavigation:")
    print("  UP/DOWN    - Move cursor")
    print("  RIGHT/ENTER - Expand directory")
    print("  LEFT       - Collapse directory")
    print("  PgUp/PgDn  - Scroll page")
    print("  i          - Toggle identical files")
    print("  v          - View file diff (on modified files)")
    print("  q/ESC      - Quit")
    print("\nWatch the status bar for scanning progress!")
    print("="*70)
    print("\nPress ENTER to start the demo...")
    input()


def main():
    """Main demo function."""
    print_instructions()
    
    # Create temporary directory for demo
    temp_dir = Path(tempfile.mkdtemp(prefix="tfm_progressive_demo_"))
    print(f"\nCreating demo directories in: {temp_dir}")
    
    try:
        # Create large directory structures
        print("\nSetting up test data (this may take a moment)...")
        left_dir = create_large_directory_structure(temp_dir, "left_side", num_files=1000)
        right_dir = create_directory_with_differences(temp_dir, "right_side", num_files=1000)
        
        print("\n" + "="*70)
        print("STARTING DIRECTORY DIFF VIEWER")
        print("="*70)
        print("\nNotice how quickly the tree appears!")
        print("Top-level items display immediately while subdirectories load in background.")
        print("\nStarting in 2 seconds...")
        time.sleep(2)
        
        # Import TTK and create renderer
        try:
            import ttk
        except ImportError:
            print("\nError: TTK library not found. Make sure it's installed.")
            return 1
        
        # Create renderer
        renderer = ttk.TTKRenderer()
        
        # Measure time to first display
        start_time = time.time()
        
        # Create and run the directory diff viewer
        viewer = DirectoryDiffViewer(
            renderer,
            TFMPath(str(left_dir)),
            TFMPath(str(right_dir))
        )
        
        # Start the scan (should return quickly with top-level only)
        viewer.start_scan()
        
        first_display_time = time.time() - start_time
        print(f"\nTime to first display: {first_display_time*1000:.1f}ms")
        
        # Run the viewer
        renderer.run(viewer)
        
        print("\n" + "="*70)
        print("Demo completed!")
        print("="*70)
        
    finally:
        # Cleanup
        print(f"\nCleaning up temporary directory: {temp_dir}")
        try:
            shutil.rmtree(temp_dir)
            print("Cleanup successful")
        except Exception as e:
            print(f"Warning: Could not remove temporary directory: {e}")
            print(f"Please manually remove: {temp_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
