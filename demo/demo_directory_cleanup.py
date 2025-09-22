#!/usr/bin/env python3
"""
Demo: Directory Existence Check and Cleanup

This demo shows how TFM checks for directory existence during startup
and cleans up cursor history entries for directories that no longer exist.
"""

import os
import sys
import tempfile
import shutil
import time
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_state_manager import TFMStateManager


def demo_directory_cleanup():
    """Demonstrate directory cleanup functionality."""
    
    print("=" * 60)
    print("TFM Directory Existence Check and Cleanup Demo")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"Working in temporary directory: {temp_path}")
        
        # Create test directories
        print("\n1. Creating test directories...")
        dirs = []
        for i in range(5):
            dir_path = temp_path / f"test_dir_{i+1}"
            dir_path.mkdir()
            # Add some files to make it realistic
            (dir_path / f"file_{i+1}.txt").write_text(f"Content of file {i+1}")
            (dir_path / f"document_{i+1}.md").write_text(f"# Document {i+1}")
            dirs.append(dir_path)
            print(f"   Created: {dir_path.name}")
        
        # Create state manager
        print("\n2. Setting up TFM state manager...")
        state_db_path = temp_path / "demo_state.db"
        state_manager = TFMStateManager()
        state_manager.db_path = state_db_path
        state_manager._initialize_database()
        
        # Save cursor positions for all directories
        print("\n3. Saving cursor positions for all directories...")
        for i, dir_path in enumerate(dirs):
            filename = f"file_{i+1}.txt"
            state_manager.save_pane_cursor_position("left", str(dir_path), filename)
            print(f"   Left pane: {dir_path.name} -> {filename}")
            
            if i < 3:  # Only save some to right pane
                filename = f"document_{i+1}.md"
                state_manager.save_pane_cursor_position("right", str(dir_path), filename)
                print(f"   Right pane: {dir_path.name} -> {filename}")
        
        # Show current cursor history
        print("\n4. Current cursor history:")
        left_history = state_manager.get_pane_cursor_positions("left")
        right_history = state_manager.get_pane_cursor_positions("right")
        
        print(f"   Left pane: {len(left_history)} entries")
        for path, filename in left_history.items():
            print(f"     {Path(path).name} -> {filename}")
        
        print(f"   Right pane: {len(right_history)} entries")
        for path, filename in right_history.items():
            print(f"     {Path(path).name} -> {filename}")
        
        # Remove some directories to simulate deletion
        print("\n5. Simulating directory deletion...")
        dirs_to_remove = dirs[1:4]  # Remove dirs 2, 3, 4
        for dir_path in dirs_to_remove:
            print(f"   Removing: {dir_path.name}")
            shutil.rmtree(dir_path)
        
        # Verify directories are gone
        print("\n6. Verifying directories are deleted...")
        for dir_path in dirs:
            exists = dir_path.exists()
            status = "EXISTS" if exists else "DELETED"
            print(f"   {dir_path.name}: {status}")
        
        # Simulate TFM startup - this is where cleanup happens
        print("\n7. Simulating TFM startup (cleanup occurs here)...")
        print("   Calling cleanup_non_existing_directories()...")
        
        cleanup_result = state_manager.cleanup_non_existing_directories()
        
        if cleanup_result:
            print("   ✓ Cleanup completed successfully")
        else:
            print("   ✗ Cleanup failed")
        
        # Show cursor history after cleanup
        print("\n8. Cursor history after cleanup:")
        left_history_after = state_manager.get_pane_cursor_positions("left")
        right_history_after = state_manager.get_pane_cursor_positions("right")
        
        print(f"   Left pane: {len(left_history_after)} entries (was {len(left_history)})")
        for path, filename in left_history_after.items():
            print(f"     {Path(path).name} -> {filename}")
        
        print(f"   Right pane: {len(right_history_after)} entries (was {len(right_history)})")
        for path, filename in right_history_after.items():
            print(f"     {Path(path).name} -> {filename}")
        
        # Summary
        print("\n9. Summary:")
        left_removed = len(left_history) - len(left_history_after)
        right_removed = len(right_history) - len(right_history_after)
        total_removed = left_removed + right_removed
        
        print(f"   • Directories created: {len(dirs)}")
        print(f"   • Directories deleted: {len(dirs_to_remove)}")
        print(f"   • Cursor history entries removed: {total_removed}")
        print(f"     - Left pane: {left_removed} entries removed")
        print(f"     - Right pane: {right_removed} entries removed")
        print(f"   • Remaining entries point to existing directories only")
        
        # Verify all remaining entries point to existing directories
        print("\n10. Verification:")
        all_valid = True
        for path in left_history_after.keys():
            if not Path(path).exists():
                print(f"   ✗ ERROR: {path} does not exist!")
                all_valid = False
        
        for path in right_history_after.keys():
            if not Path(path).exists():
                print(f"   ✗ ERROR: {path} does not exist!")
                all_valid = False
        
        if all_valid:
            print("   ✓ All remaining cursor history entries point to existing directories")
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("This cleanup happens automatically when TFM starts up.")
        print("=" * 60)


if __name__ == "__main__":
    demo_directory_cleanup()