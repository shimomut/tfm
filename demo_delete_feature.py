#!/usr/bin/env python3
"""
Demo script for TFM delete functionality
Creates a test environment and demonstrates the delete feature
"""

import curses
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the current directory to Python path to import TFM modules
sys.path.insert(0, '.')

from tfm_main import FileManager

def create_demo_environment():
    """Create a demo environment with test files"""
    demo_dir = Path(tempfile.mkdtemp(prefix="tfm_delete_demo_"))
    
    # Create various test files
    (demo_dir / "demo_file1.txt").write_text("This is a demo file for deletion testing")
    (demo_dir / "demo_file2.md").write_text("# Demo Markdown File\n\nThis file can be deleted safely.")
    (demo_dir / "demo_script.py").write_text("#!/usr/bin/env python3\nprint('Demo script')")
    
    # Create a demo directory with contents
    demo_subdir = demo_dir / "demo_directory"
    demo_subdir.mkdir()
    (demo_subdir / "nested_file1.txt").write_text("Nested file 1")
    (demo_subdir / "nested_file2.log").write_text("Log file content")
    
    # Create another directory
    another_dir = demo_dir / "empty_directory"
    another_dir.mkdir()
    
    # Create symbolic link if possible
    try:
        link_target = demo_dir / "demo_file1.txt"
        link_path = demo_dir / "demo_link.txt"
        link_path.symlink_to(link_target)
    except OSError:
        print("Note: Symbolic links not supported on this system")
    
    return demo_dir

def demo_main(stdscr):
    """Main demo function"""
    # Create demo environment
    demo_dir = create_demo_environment()
    
    try:
        # Initialize file manager
        fm = FileManager(stdscr)
        
        # Set both panes to the demo directory
        fm.left_pane['path'] = demo_dir
        fm.right_pane['path'] = demo_dir.parent  # Parent directory for context
        
        # Add demo instructions to log
        fm.log_messages.append(("DEMO", "SYSTEM", "=== TFM DELETE FEATURE DEMO ==="))
        fm.log_messages.append(("DEMO", "SYSTEM", f"Demo files created in: {demo_dir}"))
        fm.log_messages.append(("DEMO", "SYSTEM", "Instructions:"))
        fm.log_messages.append(("DEMO", "SYSTEM", "1. Use arrow keys or j/k to navigate"))
        fm.log_messages.append(("DEMO", "SYSTEM", "2. Press SPACE to select files"))
        fm.log_messages.append(("DEMO", "SYSTEM", "3. Press 'k' or 'K' to delete selected files"))
        fm.log_messages.append(("DEMO", "SYSTEM", "4. Confirm deletion in the dialog"))
        fm.log_messages.append(("DEMO", "SYSTEM", "5. Press 'q' to quit when done"))
        fm.log_messages.append(("DEMO", "SYSTEM", ""))
        fm.log_messages.append(("DEMO", "SYSTEM", "Available test files:"))
        
        # List demo files in log
        for item in demo_dir.iterdir():
            if item.is_dir():
                fm.log_messages.append(("DEMO", "SYSTEM", f"  📁 {item.name}/ (directory)"))
            elif item.is_symlink():
                fm.log_messages.append(("DEMO", "SYSTEM", f"  🔗 {item.name} (symbolic link)"))
            else:
                fm.log_messages.append(("DEMO", "SYSTEM", f"  📄 {item.name} (file)"))
        
        fm.log_messages.append(("DEMO", "SYSTEM", ""))
        fm.log_messages.append(("DEMO", "SYSTEM", "Try deleting different types of items!"))
        
        # Run the file manager
        fm.run()
        
    finally:
        # Clean up demo directory
        if demo_dir.exists():
            try:
                shutil.rmtree(demo_dir)
                print(f"\nDemo environment cleaned up: {demo_dir}")
            except Exception as e:
                print(f"\nWarning: Could not clean up demo directory: {e}")
                print(f"Please manually remove: {demo_dir}")

def main():
    """Entry point for the demo"""
    print("TFM Delete Feature Demo")
    print("=" * 40)
    print("This demo will:")
    print("1. Create temporary test files")
    print("2. Launch TFM with delete functionality")
    print("3. Allow you to test the 'k' key for deletion")
    print("4. Clean up when you quit")
    print()
    print("Press Enter to start the demo, or Ctrl+C to cancel...")
    
    try:
        input()
        curses.wrapper(demo_main)
    except KeyboardInterrupt:
        print("\nDemo cancelled.")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()