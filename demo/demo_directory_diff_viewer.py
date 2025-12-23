#!/usr/bin/env python3
"""
Demo: Comprehensive Directory Diff Viewer

This demo showcases all features of the DirectoryDiffViewer:
- Various difference types (identical, only-left, only-right, content-different)
- Nested directory structures with contains-difference propagation
- Keyboard navigation (up/down, expand/collapse, page scrolling)
- Filter to hide identical files
- File diff viewer integration
- Error handling (permission errors, inaccessible files)
- Progress feedback during scanning
- Cancellation support
- Side-by-side alignment
- Wide character support in filenames

Usage:
    python demo/demo_directory_diff_viewer.py
"""

import sys
import os
import tempfile
import time
import shutil
from pathlib import Path as StdPath

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_path import Path
from tfm_ui_layer import UILayerStack
import ttk


def create_comprehensive_test_directories():
    """
    Create test directories with comprehensive examples of all difference types.
    
    Returns:
        Tuple of (left_dir, right_dir, temp_dir)
    """
    temp_dir = tempfile.mkdtemp(prefix="tfm_diff_comprehensive_")
    
    left_dir = StdPath(temp_dir) / "left"
    right_dir = StdPath(temp_dir) / "right"
    
    left_dir.mkdir()
    right_dir.mkdir()
    
    print("Creating comprehensive test directory structure...")
    print()
    
    # 1. IDENTICAL FILES
    print("✓ Creating identical files...")
    (left_dir / "identical.txt").write_text("This file is identical in both directories.")
    (right_dir / "identical.txt").write_text("This file is identical in both directories.")
    
    (left_dir / "README.md").write_text("# Project\n\nSame content.")
    (right_dir / "README.md").write_text("# Project\n\nSame content.")
    
    # 2. ONLY-LEFT FILES
    print("✓ Creating files that exist only in left directory...")
    (left_dir / "only_left.txt").write_text("This file only exists in the left directory.")
    (left_dir / "deprecated.py").write_text("# Old code that was removed from right")
    
    # 3. ONLY-RIGHT FILES
    print("✓ Creating files that exist only in right directory...")
    (right_dir / "only_right.txt").write_text("This file only exists in the right directory.")
    (right_dir / "new_feature.py").write_text("# New code added to right")
    
    # 4. CONTENT-DIFFERENT FILES
    print("✓ Creating files with different content...")
    (left_dir / "config.json").write_text('{"version": "1.0", "debug": true}')
    (right_dir / "config.json").write_text('{"version": "2.0", "debug": false}')
    
    (left_dir / "data.txt").write_text("Left version\nwith some data\n")
    (right_dir / "data.txt").write_text("Right version\nwith different data\n")
    
    # 5. NESTED DIRECTORIES - IDENTICAL
    print("✓ Creating identical nested directory...")
    (left_dir / "docs").mkdir()
    (right_dir / "docs").mkdir()
    (left_dir / "docs" / "guide.md").write_text("# User Guide\n\nSame content.")
    (right_dir / "docs" / "guide.md").write_text("# User Guide\n\nSame content.")
    
    # 6. NESTED DIRECTORIES - CONTAINS DIFFERENCES
    print("✓ Creating nested directory with differences...")
    (left_dir / "src").mkdir()
    (right_dir / "src").mkdir()
    
    # Identical file in src
    (left_dir / "src" / "utils.py").write_text("def helper(): pass")
    (right_dir / "src" / "utils.py").write_text("def helper(): pass")
    
    # Different file in src
    (left_dir / "src" / "main.py").write_text("# Version 1.0")
    (right_dir / "src" / "main.py").write_text("# Version 2.0")
    
    # Only in left
    (left_dir / "src" / "old_module.py").write_text("# Removed module")
    
    # Only in right
    (right_dir / "src" / "new_module.py").write_text("# New module")
    
    # 7. DEEPLY NESTED STRUCTURE
    print("✓ Creating deeply nested structure...")
    (left_dir / "project" / "lib" / "core").mkdir(parents=True)
    (right_dir / "project" / "lib" / "core").mkdir(parents=True)
    
    (left_dir / "project" / "lib" / "core" / "engine.py").write_text("# Engine v1")
    (right_dir / "project" / "lib" / "core" / "engine.py").write_text("# Engine v2")
    
    (left_dir / "project" / "lib" / "helpers.py").write_text("# Helpers")
    (right_dir / "project" / "lib" / "helpers.py").write_text("# Helpers")
    
    # 8. WIDE CHARACTER FILENAMES (Japanese, emoji)
    print("✓ Creating files with wide characters...")
    (left_dir / "日本語.txt").write_text("Japanese filename")
    (right_dir / "日本語.txt").write_text("Japanese filename")
    
    (left_dir / "emoji_😀.txt").write_text("Emoji in filename")
    (right_dir / "emoji_😀.txt").write_text("Different content!")
    
    # 9. DIRECTORY ONLY IN LEFT
    print("✓ Creating directory only in left...")
    (left_dir / "legacy").mkdir()
    (left_dir / "legacy" / "old_code.py").write_text("# Legacy code")
    (left_dir / "legacy" / "archive.txt").write_text("Archived data")
    
    # 10. DIRECTORY ONLY IN RIGHT
    print("✓ Creating directory only in right...")
    (right_dir / "experimental").mkdir()
    (right_dir / "experimental" / "new_feature.py").write_text("# Experimental")
    (right_dir / "experimental" / "test.txt").write_text("Test data")
    
    # 11. EMPTY DIRECTORIES
    print("✓ Creating empty directories...")
    (left_dir / "empty_left").mkdir()
    (right_dir / "empty_right").mkdir()
    
    # 12. MIXED DIRECTORY (some identical, some different)
    print("✓ Creating mixed directory...")
    (left_dir / "mixed").mkdir()
    (right_dir / "mixed").mkdir()
    
    (left_dir / "mixed" / "same.txt").write_text("Same")
    (right_dir / "mixed" / "same.txt").write_text("Same")
    
    (left_dir / "mixed" / "diff.txt").write_text("Left")
    (right_dir / "mixed" / "diff.txt").write_text("Right")
    
    (left_dir / "mixed" / "left_only.txt").write_text("Left only")
    (right_dir / "mixed" / "right_only.txt").write_text("Right only")
    
    print()
    print(f"Created test directories:")
    print(f"  Left:  {left_dir}")
    print(f"  Right: {right_dir}")
    print()
    
    return str(left_dir), str(right_dir), temp_dir


def create_error_test_directories():
    """
    Create test directories with permission errors for error handling demo.
    
    Returns:
        Tuple of (left_dir, right_dir, temp_dir)
    """
    temp_dir = tempfile.mkdtemp(prefix="tfm_diff_errors_")
    
    left_dir = StdPath(temp_dir) / "left"
    right_dir = StdPath(temp_dir) / "right"
    
    left_dir.mkdir()
    right_dir.mkdir()
    
    print("Creating test directories with permission errors...")
    print()
    
    # Create some normal files
    (left_dir / "normal.txt").write_text("Normal file")
    (right_dir / "normal.txt").write_text("Normal file")
    
    # Create a directory with restricted permissions
    restricted_dir = left_dir / "restricted"
    restricted_dir.mkdir()
    (restricted_dir / "secret.txt").write_text("Secret data")
    
    # Remove read permissions (this will cause permission error)
    try:
        restricted_dir.chmod(0o000)
        print(f"✓ Created restricted directory: {restricted_dir}")
    except Exception as e:
        print(f"⚠ Could not restrict permissions: {e}")
    
    # Create a file with restricted permissions
    restricted_file = left_dir / "restricted_file.txt"
    restricted_file.write_text("Restricted content")
    
    try:
        restricted_file.chmod(0o000)
        print(f"✓ Created restricted file: {restricted_file}")
    except Exception as e:
        print(f"⚠ Could not restrict file permissions: {e}")
    
    # Create corresponding accessible items in right
    (right_dir / "restricted").mkdir()
    (right_dir / "restricted" / "secret.txt").write_text("Secret data")
    (right_dir / "restricted_file.txt").write_text("Restricted content")
    
    print()
    print(f"Created test directories with errors:")
    print(f"  Left:  {left_dir}")
    print(f"  Right: {right_dir}")
    print()
    
    return str(left_dir), str(right_dir), temp_dir


def cleanup_error_directories(temp_dir):
    """Clean up directories with restricted permissions."""
    try:
        # Restore permissions before cleanup
        for root, dirs, files in os.walk(temp_dir):
            for d in dirs:
                try:
                    os.chmod(os.path.join(root, d), 0o755)
                except:
                    pass
            for f in files:
                try:
                    os.chmod(os.path.join(root, f), 0o644)
                except:
                    pass
        
        shutil.rmtree(temp_dir)
        print(f"Cleaned up test directories: {temp_dir}")
    except Exception as e:
        print(f"Warning: Could not fully clean up {temp_dir}: {e}")


class MockBottomLayer:
    """Mock bottom layer for testing (normally FileManager)."""
    
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


def run_demo(left_dir, right_dir, demo_name):
    """
    Run the directory diff viewer demo.
    
    Args:
        left_dir: Path to left directory
        right_dir: Path to right directory
        demo_name: Name of the demo for display
    """
    print(f"\n{'=' * 70}")
    print(f"Running: {demo_name}")
    print(f"{'=' * 70}\n")
    
    # Initialize TTK renderer
    try:
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        renderer = CoreGraphicsBackend()
        print("✓ Using CoreGraphics backend")
    except ImportError:
        from ttk.backends.curses_backend import CursesBackend
        renderer = CursesBackend()
        print("✓ Using Curses backend")
    
    try:
        # Create UI layer stack
        bottom_layer = MockBottomLayer()
        layer_stack = UILayerStack(bottom_layer)
        
        # Create and push directory diff viewer
        left_path = Path(left_dir)
        right_path = Path(right_dir)
        viewer = DirectoryDiffViewer(renderer, left_path, right_path, layer_stack)
        layer_stack.push(viewer)
        
        print("\n" + "=" * 70)
        print("DIRECTORY DIFF VIEWER - INTERACTIVE DEMO")
        print("=" * 70)
        print()
        print("Features to try:")
        print("  • UP/DOWN arrows    - Navigate through tree")
        print("  • LEFT/RIGHT/ENTER  - Expand/collapse directories")
        print("  • PgUp/PgDn         - Page scrolling")
        print("  • 'i' key           - Toggle hide/show identical files")
        print("  • 'd' key           - Open file diff for content-different files")
        print("  • ESC or 'q'        - Close viewer")
        print()
        print("Difference types:")
        print("  • Green background  - Only in left directory")
        print("  • Blue background   - Only in right directory")
        print("  • Yellow background - Content different")
        print("  • Cyan background   - Directory contains differences")
        print("  • Gray background   - Blank alignment space")
        print()
        print("Wait for scan to complete, then explore the tree structure!")
        print("=" * 70)
        print()
        
        # Main event loop
        running = True
        last_render = 0
        render_interval = 0.05  # 20 FPS
        
        while running:
            current_time = time.time()
            
            # Render at fixed interval
            if current_time - last_render >= render_interval:
                layer_stack.render(renderer)
                last_render = current_time
            
            # Handle events
            event = renderer.get_event(timeout_ms=50)
            
            if event:
                if isinstance(event, ttk.KeyEvent):
                    layer_stack.handle_key_event(event)
                elif isinstance(event, ttk.CharEvent):
                    layer_stack.handle_char_event(event)
                elif isinstance(event, ttk.SystemEvent):
                    layer_stack.handle_system_event(event)
            
            # Check if viewer wants to close
            if layer_stack.check_and_close_top_layer():
                print("\n✓ Viewer closed!")
                running = False
            
            # Small delay to avoid busy loop
            time.sleep(0.01)
    
    finally:
        renderer.shutdown()


def main():
    """Main demo entry point."""
    print("\n" + "=" * 70)
    print("DIRECTORY DIFF VIEWER - COMPREHENSIVE DEMO")
    print("=" * 70)
    print()
    print("This demo showcases all features of the Directory Diff Viewer:")
    print("  1. Comprehensive feature demo (various difference types)")
    print("  2. Error handling demo (permission errors)")
    print()
    
    # Ask which demo to run
    print("Select demo to run:")
    print("  1 - Comprehensive feature demo (recommended)")
    print("  2 - Error handling demo")
    print("  3 - Both demos")
    print()
    
    choice = input("Enter choice (1-3, default=1): ").strip() or "1"
    print()
    
    temp_dirs = []
    
    try:
        if choice in ["1", "3"]:
            # Run comprehensive demo
            left_dir, right_dir, temp_dir = create_comprehensive_test_directories()
            temp_dirs.append((temp_dir, False))  # False = normal cleanup
            
            input("Press ENTER to start comprehensive demo...")
            run_demo(left_dir, right_dir, "Comprehensive Feature Demo")
        
        if choice in ["2", "3"]:
            # Run error handling demo
            left_dir, right_dir, temp_dir = create_error_test_directories()
            temp_dirs.append((temp_dir, True))  # True = special cleanup needed
            
            input("\nPress ENTER to start error handling demo...")
            run_demo(left_dir, right_dir, "Error Handling Demo")
        
        print("\n" + "=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        print()
        print("Summary of demonstrated features:")
        print("  ✓ Various difference types (identical, only-left, only-right, different)")
        print("  ✓ Nested directory structures with difference propagation")
        print("  ✓ Keyboard navigation (arrows, expand/collapse, page scrolling)")
        print("  ✓ Filter to hide identical files")
        print("  ✓ Side-by-side alignment")
        print("  ✓ Wide character support in filenames")
        print("  ✓ Progress feedback during scanning")
        print("  ✓ Error handling (permission errors)")
        print("  ✓ File diff viewer integration")
        print()
    
    finally:
        # Cleanup all temp directories
        print("Cleaning up test directories...")
        for temp_dir, needs_special_cleanup in temp_dirs:
            if needs_special_cleanup:
                cleanup_error_directories(temp_dir)
            else:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up: {temp_dir}")
        print()
        print("Demo finished!")


if __name__ == '__main__':
    main()
