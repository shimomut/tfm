#!/usr/bin/env python3
"""
Demo: Basic Directory Diff Viewer

This demo shows the DirectoryDiffViewer in action with simple test directories.
It demonstrates the UILayer interface implementation and basic scanning functionality.
"""

import sys
import os
import tempfile
import time
from pathlib import Path as StdPath

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_path import Path
from tfm_ui_layer import UILayerStack
import ttk


def create_test_directories():
    """Create test directories with some differences."""
    temp_dir = tempfile.mkdtemp(prefix="tfm_diff_demo_")
    
    left_dir = StdPath(temp_dir) / "left"
    right_dir = StdPath(temp_dir) / "right"
    
    left_dir.mkdir()
    right_dir.mkdir()
    
    # Create identical files
    (left_dir / "identical.txt").write_text("This file is the same in both directories.")
    (right_dir / "identical.txt").write_text("This file is the same in both directories.")
    
    # Create file only in left
    (left_dir / "only_left.txt").write_text("This file only exists in the left directory.")
    
    # Create file only in right
    (right_dir / "only_right.txt").write_text("This file only exists in the right directory.")
    
    # Create files with different content
    (left_dir / "different.txt").write_text("Left version of the file.")
    (right_dir / "different.txt").write_text("Right version of the file.")
    
    # Create subdirectories
    (left_dir / "subdir").mkdir()
    (right_dir / "subdir").mkdir()
    
    (left_dir / "subdir" / "file1.txt").write_text("File in subdirectory.")
    (right_dir / "subdir" / "file1.txt").write_text("File in subdirectory.")
    
    (left_dir / "subdir" / "only_left_sub.txt").write_text("Only in left subdir.")
    
    print(f"Created test directories:")
    print(f"  Left:  {left_dir}")
    print(f"  Right: {right_dir}")
    print()
    
    return str(left_dir), str(right_dir), temp_dir


def main():
    """Run the demo."""
    print("Directory Diff Viewer - Basic Demo")
    print("=" * 60)
    print()
    
    # Create test directories
    left_dir, right_dir, temp_dir = create_test_directories()
    
    # Initialize TTK renderer (use CoreGraphics backend on macOS)
    try:
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        renderer = CoreGraphicsBackend()
    except ImportError:
        # Fall back to curses backend
        from ttk.backends.curses_backend import CursesBackend
        renderer = CursesBackend()
    
    try:
        # Create mock bottom layer (normally FileManager)
        class MockBottomLayer:
            def handle_key_event(self, event):
                return False
            def handle_char_event(self, event):
                return False
            def handle_system_event(self, event):
                return False
            def render(self, renderer):
                renderer.clear()
                renderer.draw_text(0, 0, "Mock FileManager (bottom layer)")
            def is_full_screen(self):
                return True
            def needs_redraw(self):
                return False
            def mark_dirty(self):
                pass
            def clear_dirty(self):
                pass
            def should_close(self):
                return False
            def on_activate(self):
                pass
            def on_deactivate(self):
                pass
        
        # Create UI layer stack
        bottom_layer = MockBottomLayer()
        layer_stack = UILayerStack(bottom_layer)
        
        # Create and push directory diff viewer
        left_path = Path(left_dir)
        right_path = Path(right_dir)
        viewer = DirectoryDiffViewer(renderer, left_path, right_path, layer_stack)
        layer_stack.push(viewer)
        
        print("Directory Diff Viewer opened!")
        print("Scanning directories...")
        print()
        print("Instructions:")
        print("  - Wait for scan to complete")
        print("  - Press ESC or Q to close the viewer")
        print()
        
        # Main event loop
        running = True
        while running:
            # Render
            layer_stack.render(renderer)
            
            # Handle events
            event = renderer.get_event(timeout_ms=100)
            
            if event:
                if isinstance(event, ttk.KeyEvent):
                    layer_stack.handle_key_event(event)
                elif isinstance(event, ttk.CharEvent):
                    layer_stack.handle_char_event(event)
                elif isinstance(event, ttk.SystemEvent):
                    layer_stack.handle_system_event(event)
            
            # Check if viewer wants to close
            if layer_stack.check_and_close_top_layer():
                print("\nViewer closed!")
                running = False
            
            # Small delay to avoid busy loop
            time.sleep(0.01)
    
    finally:
        # Cleanup
        renderer.shutdown()
        
        # Clean up test directories
        import shutil
        shutil.rmtree(temp_dir)
        print(f"Cleaned up test directories: {temp_dir}")


if __name__ == '__main__':
    main()
