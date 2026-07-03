#!/usr/bin/env python3
"""
Demo script for Task 12: Visual indicators for pending status.

This demo creates a directory structure and shows how the Directory Diff Viewer
displays pending status indicators during progressive scanning.

The demo shows:
1. Directories with "..." indicator when not yet scanned
2. Files with "[pending]" indicator when not yet compared
3. Directories with "[scanning...]" indicator during on-demand scanning
4. Status bar showing "Scanning... (N pending)" and "Comparing... (N pending)"
5. PENDING status using neutral colors (dimmed) distinct from IDENTICAL
"""

import sys
import os
import tempfile
import shutil
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_directory_diff_viewer import DirectoryDiffViewer
import ttk


def create_test_directories():
    """Create test directory structures for the demo."""
    # Create temporary directories
    temp_dir = tempfile.mkdtemp(prefix="diff_viewer_demo_")
    left_dir = os.path.join(temp_dir, "left")
    right_dir = os.path.join(temp_dir, "right")
    
    os.makedirs(left_dir)
    os.makedirs(right_dir)
    
    # Create a large directory structure to demonstrate progressive scanning
    # This will show pending indicators as directories are scanned
    
    # Create identical files
    for i in range(5):
        filename = f"identical_{i}.txt"
        content = f"This is identical file {i}\n" * 10
        with open(os.path.join(left_dir, filename), 'w') as f:
            f.write(content)
        with open(os.path.join(right_dir, filename), 'w') as f:
            f.write(content)
    
    # Create different files
    for i in range(3):
        filename = f"different_{i}.txt"
        with open(os.path.join(left_dir, filename), 'w') as f:
            f.write(f"Left version of file {i}\n" * 10)
        with open(os.path.join(right_dir, filename), 'w') as f:
            f.write(f"Right version of file {i}\n" * 10)
    
    # Create files only on left
    for i in range(2):
        filename = f"only_left_{i}.txt"
        with open(os.path.join(left_dir, filename), 'w') as f:
            f.write(f"This file only exists on the left side {i}\n" * 10)
    
    # Create files only on right
    for i in range(2):
        filename = f"only_right_{i}.txt"
        with open(os.path.join(right_dir, filename), 'w') as f:
            f.write(f"This file only exists on the right side {i}\n" * 10)
    
    # Create nested directories to demonstrate progressive scanning
    # These will show "..." indicator until expanded
    for side_dir in [left_dir, right_dir]:
        for i in range(3):
            subdir = os.path.join(side_dir, f"subdir_{i}")
            os.makedirs(subdir)
            
            # Add files in subdirectories
            for j in range(5):
                filename = f"file_{j}.txt"
                with open(os.path.join(subdir, filename), 'w') as f:
                    f.write(f"Content in subdir_{i}/file_{j}\n" * 5)
            
            # Add nested subdirectories
            nested_dir = os.path.join(subdir, "nested")
            os.makedirs(nested_dir)
            for j in range(3):
                filename = f"nested_file_{j}.txt"
                with open(os.path.join(nested_dir, filename), 'w') as f:
                    f.write(f"Content in nested directory {j}\n" * 5)
    
    return temp_dir, left_dir, right_dir


def main():
    """Run the demo."""
    print("=" * 70)
    print("Directory Diff Viewer - Visual Indicators Demo (Task 12)")
    print("=" * 70)
    print()
    print("This demo shows the visual indicators for pending status:")
    print("  • Directories not yet scanned show '...'")
    print("  • Files not yet compared show '[pending]'")
    print("  • Directories being scanned show '[scanning...]'")
    print("  • Status bar shows 'Scanning... (N pending)' and 'Comparing... (N pending)'")
    print("  • PENDING items use dimmed colors to distinguish from IDENTICAL")
    print()
    print("Creating test directories...")
    
    temp_dir = None
    try:
        # Create test directories
        temp_dir, left_dir, right_dir = create_test_directories()
        print(f"Left directory:  {left_dir}")
        print(f"Right directory: {right_dir}")
        print()
        print("Starting Directory Diff Viewer...")
        print()
        print("INSTRUCTIONS:")
        print("  • Watch the status bar for scanning progress indicators")
        print("  • Notice directories show '...' until scanned")
        print("  • Notice files show '[pending]' until compared")
        print("  • Expand directories (→ or Enter) to trigger on-demand scanning")
        print("  • Watch for '[scanning...]' indicator during on-demand scans")
        print("  • Press 'q' or ESC to quit")
        print()
        print("-" * 70)
        
        # Initialize TTK
        ttk.init()
        
        try:
            # Create renderer
            renderer = ttk.get_renderer()
            
            # Create and run the directory diff viewer
            left_path = Path(left_dir)
            right_path = Path(right_dir)
            
            viewer = DirectoryDiffViewer(renderer, left_path, right_path)
            
            # Run the viewer
            while not viewer.should_close():
                # Handle events
                event = ttk.get_event()
                if event:
                    if hasattr(event, 'key_code'):
                        viewer.handle_key_event(event)
                    elif hasattr(event, 'char'):
                        viewer.handle_char_event(event)
                    else:
                        viewer.handle_system_event(event)
                
                # Render
                if viewer.needs_redraw():
                    viewer.render(renderer)
                    renderer.refresh()
                    viewer.clear_dirty()
                
                # Small delay to prevent busy-waiting
                time.sleep(0.01)
        
        finally:
            ttk.shutdown()
    
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up temporary directories
        if temp_dir and os.path.exists(temp_dir):
            print(f"\nCleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
    
    print("\nDemo complete!")


if __name__ == "__main__":
    main()
