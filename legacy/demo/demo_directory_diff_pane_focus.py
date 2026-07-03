#!/usr/bin/env python3
"""
Demo: Directory Diff Viewer Pane Focus

This demo showcases the pane focus feature in DirectoryDiffViewer:
- Tab key switches focus between left and right panes
- Focus indicator (►) shows which pane is active
- Cursor position remains synchronized between panes
- Prepares for future copy operations between panes

Usage:
    python demo/demo_directory_diff_pane_focus.py
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_path import Path as TFMPath
from tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_backend_selector import select_backend


def create_demo_directories():
    """Create temporary directories with sample files for demo."""
    temp_dir = tempfile.mkdtemp(prefix="tfm_diff_demo_")
    
    left_dir = Path(temp_dir) / "left"
    right_dir = Path(temp_dir) / "right"
    
    left_dir.mkdir()
    right_dir.mkdir()
    
    # Create some files in both directories
    (left_dir / "README.md").write_text("# Left Directory\n\nThis is the left side.")
    (right_dir / "README.md").write_text("# Right Directory\n\nThis is the right side.")
    
    # Create a file only on left
    (left_dir / "left_only.txt").write_text("This file exists only on the left side.")
    
    # Create a file only on right
    (right_dir / "right_only.txt").write_text("This file exists only on the right side.")
    
    # Create identical files
    (left_dir / "identical.txt").write_text("Same content on both sides.")
    (right_dir / "identical.txt").write_text("Same content on both sides.")
    
    # Create different files with same name
    (left_dir / "different.txt").write_text("Left version of the file.")
    (right_dir / "different.txt").write_text("Right version of the file.")
    
    # Create subdirectories
    (left_dir / "subdir").mkdir()
    (right_dir / "subdir").mkdir()
    
    (left_dir / "subdir" / "file1.txt").write_text("File in left subdir")
    (right_dir / "subdir" / "file1.txt").write_text("File in right subdir")
    
    return temp_dir, left_dir, right_dir


def main():
    """Run the directory diff viewer demo with pane focus."""
    print("Directory Diff Viewer - Pane Focus Demo")
    print("=" * 50)
    print()
    print("Creating demo directories...")
    
    temp_dir, left_dir, right_dir = create_demo_directories()
    
    try:
        print(f"Left directory:  {left_dir}")
        print(f"Right directory: {right_dir}")
        print()
        print("Starting directory diff viewer...")
        print()
        print("Key Features:")
        print("  • Tab key switches focus between left and right panes")
        print("  • Focus indicator (►) shows which pane is active")
        print("  • Cursor position stays synchronized between panes")
        print("  • Prepares for future copy operations")
        print()
        print("Try it:")
        print("  1. Press Tab to switch between panes")
        print("  2. Notice the ► indicator moves in the header")
        print("  3. Navigate with arrow keys - cursor stays in sync")
        print("  4. Press q to quit")
        print()
        input("Press Enter to start the demo...")
        
        # Initialize backend
        backend = select_backend()
        renderer = backend.create_renderer()
        
        # Create directory diff viewer
        viewer = DirectoryDiffViewer(
            renderer,
            TFMPath(str(left_dir)),
            TFMPath(str(right_dir))
        )
        
        # Run the viewer
        try:
            while not viewer.should_close():
                # Render
                if viewer.needs_redraw():
                    viewer.render(renderer)
                    renderer.refresh()
                    viewer.clear_dirty()
                
                # Handle input
                event = renderer.get_event(timeout=100)
                if event:
                    from ttk import KeyEvent, CharEvent, SystemEvent
                    
                    if isinstance(event, KeyEvent):
                        viewer.handle_key_event(event)
                    elif isinstance(event, CharEvent):
                        viewer.handle_char_event(event)
                    elif isinstance(event, SystemEvent):
                        viewer.handle_system_event(event)
        
        finally:
            backend.cleanup()
    
    finally:
        # Clean up temporary directory
        print()
        print("Cleaning up demo directories...")
        shutil.rmtree(temp_dir)
        print("Demo complete!")


if __name__ == "__main__":
    main()
