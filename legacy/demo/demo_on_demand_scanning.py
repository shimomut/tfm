#!/usr/bin/env python3
"""
Demo: On-Demand Scanning in Directory Diff Viewer

This demo shows how the directory diff viewer performs on-demand scanning
when users expand directories that haven't been scanned yet.

Features demonstrated:
1. Initial display shows top-level items immediately
2. Unscanned directories show "..." indicator
3. Expanding an unscanned directory triggers immediate scanning
4. "[scanning...]" indicator appears during scan
5. Tree updates with new children after scan completes

Usage:
    python3 demo/demo_on_demand_scanning.py
"""

import sys
import os
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_path import Path
from ttk import TTKApplication, KeyCode, KeyEvent


def create_deep_directory_structure():
    """Create a deep directory structure to demonstrate on-demand scanning."""
    temp_dir = tempfile.mkdtemp(prefix='demo_on_demand_')
    
    left_dir = os.path.join(temp_dir, 'left')
    right_dir = os.path.join(temp_dir, 'right')
    
    os.makedirs(left_dir)
    os.makedirs(right_dir)
    
    # Create a deep nested structure
    # Left side
    for i in range(3):
        dir_path = os.path.join(left_dir, f'level1_dir{i}')
        os.makedirs(dir_path)
        
        for j in range(3):
            subdir_path = os.path.join(dir_path, f'level2_dir{j}')
            os.makedirs(subdir_path)
            
            for k in range(3):
                subsubdir_path = os.path.join(subdir_path, f'level3_dir{k}')
                os.makedirs(subsubdir_path)
                
                # Add some files at the deepest level
                for m in range(2):
                    file_path = os.path.join(subsubdir_path, f'file{m}.txt')
                    with open(file_path, 'w') as f:
                        f.write(f'Content for file {m} in level3_dir{k}')
    
    # Right side - similar structure with some differences
    for i in range(3):
        dir_path = os.path.join(right_dir, f'level1_dir{i}')
        os.makedirs(dir_path)
        
        for j in range(3):
            subdir_path = os.path.join(dir_path, f'level2_dir{j}')
            os.makedirs(subdir_path)
            
            for k in range(3):
                subsubdir_path = os.path.join(subdir_path, f'level3_dir{k}')
                os.makedirs(subsubdir_path)
                
                # Add some files at the deepest level
                for m in range(2):
                    file_path = os.path.join(subsubdir_path, f'file{m}.txt')
                    with open(file_path, 'w') as f:
                        # Make some files different
                        if i == 1 and j == 1 and k == 1:
                            f.write(f'DIFFERENT content for file {m}')
                        else:
                            f.write(f'Content for file {m} in level3_dir{k}')
    
    return temp_dir, left_dir, right_dir


def main():
    """Run the on-demand scanning demo."""
    print("=" * 80)
    print("Directory Diff Viewer - On-Demand Scanning Demo")
    print("=" * 80)
    print()
    print("This demo shows how the directory diff viewer performs on-demand scanning")
    print("when you expand directories that haven't been scanned yet.")
    print()
    print("Features:")
    print("  • Initial display shows top-level items immediately (< 100ms)")
    print("  • Unscanned directories show '...' indicator")
    print("  • Expanding an unscanned directory triggers immediate scanning")
    print("  • '[scanning...]' indicator appears during scan")
    print("  • Tree updates with new children after scan completes")
    print()
    print("Controls:")
    print("  • UP/DOWN: Navigate through tree")
    print("  • RIGHT/ENTER: Expand directory")
    print("  • LEFT: Collapse directory")
    print("  • q/ESC: Quit")
    print()
    print("Creating deep directory structure...")
    
    # Create test directories
    temp_dir, left_dir, right_dir = create_deep_directory_structure()
    
    print(f"Left directory: {left_dir}")
    print(f"Right directory: {right_dir}")
    print()
    print("Starting directory diff viewer...")
    print("Notice how the initial display appears immediately!")
    print("Try expanding directories to see on-demand scanning in action.")
    print()
    
    try:
        # Create TTK application
        app = TTKApplication()
        
        # Create directory diff viewer
        left_path = Path(left_dir)
        right_path = Path(right_dir)
        viewer = DirectoryDiffViewer(app.renderer, left_path, right_path)
        
        # Push viewer onto layer stack
        app.layer_stack.push(viewer)
        
        # Run application
        app.run()
        
    finally:
        # Clean up
        print()
        print("Cleaning up temporary directories...")
        shutil.rmtree(temp_dir)
        print(f"Removed {temp_dir}")
        print()
        print("Demo complete!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
