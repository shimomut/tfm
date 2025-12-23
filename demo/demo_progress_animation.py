#!/usr/bin/env python3
"""
Demo: Progress Animation in Directory Diff Viewer

This demo demonstrates the progress animation feature in the Directory Diff Viewer:
1. Animated spinner during scanning operations
2. Progress percentage display when available
3. Continuous animation updates during background work
4. Different status messages for different operations

The demo creates a large directory structure to show the animation in action.
"""

import sys
import os
import tempfile
import shutil

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_path import Path
from tfm_ui_layer import UILayerStack

# Import TTK for rendering
try:
    import ttk
except ImportError:
    print("Error: TTK module not found. Make sure ttk_coregraphics_render.so is built.")
    sys.exit(1)


def create_large_directory_structure():
    """Create a large directory structure to demonstrate progress animation."""
    temp_dir = tempfile.mkdtemp(prefix="demo_progress_")
    left_dir = os.path.join(temp_dir, "left")
    right_dir = os.path.join(temp_dir, "right")
    
    os.makedirs(left_dir)
    os.makedirs(right_dir)
    
    print(f"Creating test directories in: {temp_dir}")
    print("This will take a moment to create enough files to show animation...")
    
    # Create a deeper directory structure with more files
    for i in range(20):  # 20 top-level directories
        left_subdir = os.path.join(left_dir, f"category_{i:02d}")
        right_subdir = os.path.join(right_dir, f"category_{i:02d}")
        os.makedirs(left_subdir)
        os.makedirs(right_subdir)
        
        # Create subdirectories
        for j in range(10):  # 10 subdirectories each
            left_subsubdir = os.path.join(left_subdir, f"subdir_{j:02d}")
            right_subsubdir = os.path.join(right_subdir, f"subdir_{j:02d}")
            os.makedirs(left_subsubdir)
            os.makedirs(right_subsubdir)
            
            # Create files in subdirectories
            for k in range(5):  # 5 files each
                left_file = os.path.join(left_subsubdir, f"file_{k:02d}.txt")
                right_file = os.path.join(right_subsubdir, f"file_{k:02d}.txt")
                
                # Make some files different
                if (i + j + k) % 3 == 0:
                    with open(left_file, 'w') as f:
                        f.write(f"Left content {i}-{j}-{k}")
                    with open(right_file, 'w') as f:
                        f.write(f"Right content {i}-{j}-{k} - DIFFERENT")
                else:
                    content = f"Same content {i}-{j}-{k}"
                    with open(left_file, 'w') as f:
                        f.write(content)
                    with open(right_file, 'w') as f:
                        f.write(content)
    
    # Add some files only on left
    for i in range(5):
        left_only_dir = os.path.join(left_dir, f"left_only_{i}")
        os.makedirs(left_only_dir)
        for j in range(3):
            with open(os.path.join(left_only_dir, f"file_{j}.txt"), 'w') as f:
                f.write(f"Left only {i}-{j}")
    
    # Add some files only on right
    for i in range(5):
        right_only_dir = os.path.join(right_dir, f"right_only_{i}")
        os.makedirs(right_only_dir)
        for j in range(3):
            with open(os.path.join(right_only_dir, f"file_{j}.txt"), 'w') as f:
                f.write(f"Right only {i}-{j}")
    
    print(f"Created directory structure with ~1000 files")
    print()
    
    return temp_dir, left_dir, right_dir


def main():
    """Run the demo."""
    print("=" * 70)
    print("Directory Diff Viewer - Progress Animation Demo")
    print("=" * 70)
    print()
    print("This demo shows the progress animation feature:")
    print("  • Animated spinner during scanning")
    print("  • Progress percentage when available")
    print("  • Continuous updates during background work")
    print()
    print("Watch the status bar at the bottom for the animation!")
    print()
    print("Controls:")
    print("  • Arrow keys: Navigate")
    print("  • Enter/Right: Expand directory")
    print("  • Left: Collapse directory")
    print("  • i: Toggle showing identical files")
    print("  • q or ESC: Quit")
    print()
    input("Press Enter to start the demo...")
    print()
    
    # Create test directories
    temp_dir, left_dir, right_dir = create_large_directory_structure()
    
    try:
        # Initialize TTK
        ttk.init()
        renderer = ttk.Renderer()
        
        # Create UI layer stack
        layer_stack = UILayerStack(renderer)
        
        # Create directory diff viewer
        print("Opening Directory Diff Viewer...")
        print("Watch the status bar for the animated spinner and progress!")
        print()
        
        viewer = DirectoryDiffViewer(
            renderer,
            Path(left_dir),
            Path(right_dir),
            layer_stack=layer_stack
        )
        
        # Push viewer onto stack
        layer_stack.push(viewer)
        
        # Run the UI loop
        layer_stack.run()
        
    finally:
        # Cleanup
        ttk.shutdown()
        print("\nCleaning up test directories...")
        shutil.rmtree(temp_dir)
        print("Demo complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
