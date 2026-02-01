#!/usr/bin/env python3
"""
Demo: Directory Diff Viewer Copy and Delete Operations

This demo demonstrates the copy and delete file operations in the Directory Diff Viewer.
It shows how to:
1. Copy files from one pane to another using configured keybindings
2. Delete files from the active pane using configured keybindings
3. Switch between panes to select which side to operate on

Key Features Demonstrated:
- Copy focused file from active pane to opposite pane (C key by default)
- Delete focused file from active pane (K/Delete key by default)
- Active pane indication (bold header shows which pane is active)
- Tab/Arrow keys to switch active pane

Usage:
    python demo/demo_directory_diff_copy_delete.py
"""

import sys
import os
import tempfile
import shutil

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_path import Path
from tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_config import ConfigManager
from tfm_file_operation_ui import FileOperationUI
from tfm_file_list_manager import FileListManager
from tfm_ui_layer import UILayerStack
from ttk import TtkApplication


def create_test_directories():
    """Create test directories with sample files for demonstration."""
    # Create temporary directories
    temp_dir = tempfile.mkdtemp(prefix="tfm_diff_demo_")
    left_dir = os.path.join(temp_dir, "left")
    right_dir = os.path.join(temp_dir, "right")
    
    os.makedirs(left_dir)
    os.makedirs(right_dir)
    
    # Create files in left directory
    with open(os.path.join(left_dir, "file1.txt"), "w") as f:
        f.write("This file exists only on the left side.\n")
    
    with open(os.path.join(left_dir, "file2.txt"), "w") as f:
        f.write("This file has different content on both sides.\n")
    
    with open(os.path.join(left_dir, "common.txt"), "w") as f:
        f.write("This file is identical on both sides.\n")
    
    # Create subdirectory in left
    os.makedirs(os.path.join(left_dir, "subdir"))
    with open(os.path.join(left_dir, "subdir", "nested.txt"), "w") as f:
        f.write("Nested file in left subdirectory.\n")
    
    # Create files in right directory
    with open(os.path.join(right_dir, "file2.txt"), "w") as f:
        f.write("This file has DIFFERENT content on both sides.\n")
    
    with open(os.path.join(right_dir, "file3.txt"), "w") as f:
        f.write("This file exists only on the right side.\n")
    
    with open(os.path.join(right_dir, "common.txt"), "w") as f:
        f.write("This file is identical on both sides.\n")
    
    return temp_dir, left_dir, right_dir


def main():
    """Main demo function."""
    print("Directory Diff Viewer - Copy and Delete Operations Demo")
    print("=" * 60)
    print()
    print("This demo shows how to copy and delete files in the Directory Diff Viewer.")
    print()
    print("Setup:")
    print("  - Creating test directories with sample files...")
    
    # Create test directories
    temp_dir, left_dir, right_dir = create_test_directories()
    
    print(f"  - Left directory:  {left_dir}")
    print(f"  - Right directory: {right_dir}")
    print()
    print("Instructions:")
    print("  1. Use ↑/↓ to navigate between files")
    print("  2. Use Tab or ←/→ to switch active pane (bold header shows active pane)")
    print("  3. Press C to copy focused file from active pane to opposite pane")
    print("  4. Press K or Delete to delete focused file from active pane")
    print("  5. Press Enter to view file differences")
    print("  6. Press ? for full help")
    print("  7. Press q or ESC to exit")
    print()
    print("Try this:")
    print("  - Navigate to 'file1.txt' (only on left)")
    print("  - Make sure left pane is active (header should be bold)")
    print("  - Press C to copy it to the right side")
    print("  - Switch to right pane with Tab")
    print("  - Navigate to 'file3.txt' (only on right)")
    print("  - Press K to delete it from the right side")
    print()
    input("Press Enter to start the demo...")
    
    try:
        # Initialize TFM components
        config_manager = ConfigManager()
        config_manager.load_config()
        
        # Create application
        app = TtkApplication()
        
        # Create file list manager (for show_hidden setting)
        file_list_manager = FileListManager(config_manager)
        
        # Create UI layer stack
        layer_stack = UILayerStack(app.renderer)
        
        # Create a minimal mock FileManager for copy/delete operations
        # In a real application, this would be the actual FileManager instance
        from unittest.mock import Mock
        from tfm_file_operation_executor import FileOperationExecutor
        
        file_manager = Mock()
        file_manager.file_operations_executor = FileOperationExecutor(
            app.renderer,
            layer_stack,
            config_manager,
            None  # cache_manager not needed for demo
        )
        
        # Create directory diff viewer
        left_path = Path(left_dir)
        right_path = Path(right_dir)
        
        viewer = DirectoryDiffViewer(
            app.renderer,
            left_path,
            right_path,
            layer_stack,
            file_list_manager,
            file_manager,  # Pass file_manager directly
            config_manager
        )
        
        # Push viewer onto layer stack
        layer_stack.push(viewer)
        
        # Run the application
        app.run()
        
    finally:
        # Cleanup temporary directory
        print()
        print("Cleaning up temporary files...")
        try:
            shutil.rmtree(temp_dir)
            print(f"Removed temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not remove temporary directory: {e}")
        
        print()
        print("Demo completed!")


if __name__ == "__main__":
    main()
