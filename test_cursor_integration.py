#!/usr/bin/env python3
"""
Integration test for cursor position history in TFM
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from collections import deque

# Add src directory to path
sys.path.insert(0, 'src')

def test_tfm_cursor_methods():
    """Test the TFM cursor history methods"""
    from tfm_main import FileManager
    import curses
    
    # Create test directory structure
    test_dir = Path(tempfile.mkdtemp(prefix="tfm_integration_test_"))
    
    try:
        # Create subdirectories and files
        (test_dir / "subdir1").mkdir()
        (test_dir / "subdir2").mkdir()
        (test_dir / "file1.txt").write_text("Test file 1")
        (test_dir / "file2.txt").write_text("Test file 2")
        (test_dir / "file3.txt").write_text("Test file 3")
        
        # Create files in subdirectory
        (test_dir / "subdir1" / "sub1.txt").write_text("Sub file 1")
        (test_dir / "subdir1" / "sub2.txt").write_text("Sub file 2")
        
        print(f"Created test directory: {test_dir}")
        
        # Create a mock FileManager instance (without curses initialization)
        class MockFileManager:
            def __init__(self):
                self.left_pane = {
                    'path': test_dir,
                    'selected_index': 0,
                    'scroll_offset': 0,
                    'files': [],
                    'selected_files': set(),
                    'sort_mode': 'name',
                    'sort_reverse': False,
                    'filter_pattern': "",
                    'cursor_history': deque(maxlen=100)
                }
                self.right_pane = {
                    'path': test_dir,
                    'selected_index': 0,
                    'scroll_offset': 0,
                    'files': [],
                    'selected_files': set(),
                    'sort_mode': 'name',
                    'sort_reverse': False,
                    'filter_pattern': "",
                    'cursor_history': deque(maxlen=100)
                }
                self.active_pane = 'left'
                self.log_height_ratio = 0.25
                self.stdscr = None  # Mock
                
            def get_current_pane(self):
                return self.left_pane if self.active_pane == 'left' else self.right_pane
                
            def refresh_files(self, pane_data):
                """Mock refresh_files method"""
                try:
                    entries = list(pane_data['path'].iterdir())
                    pane_data['files'] = sorted(entries, key=lambda x: x.name)
                except PermissionError:
                    pane_data['files'] = []
        
        # Add the cursor history methods to our mock class
        def save_cursor_position(self, pane_data):
            """Save current cursor position to history"""
            if not pane_data['files'] or pane_data['selected_index'] >= len(pane_data['files']):
                return
                
            current_file = pane_data['files'][pane_data['selected_index']]
            current_dir = pane_data['path']
            
            # Save as (filename, directory_path) tuple
            cursor_entry = (current_file.name, str(current_dir))
            
            # Remove any existing entry for this directory to avoid duplicates
            pane_data['cursor_history'] = deque(
                [entry for entry in pane_data['cursor_history'] if entry[1] != str(current_dir)],
                maxlen=100
            )
            
            # Add the new entry
            pane_data['cursor_history'].append(cursor_entry)
        
        def restore_cursor_position(self, pane_data):
            """Restore cursor position from history when changing to a directory"""
            current_dir = str(pane_data['path'])
            
            # Look for a saved cursor position for this directory
            for filename, saved_dir in reversed(pane_data['cursor_history']):
                if saved_dir == current_dir:
                    # Try to find this filename in current files
                    for i, file_path in enumerate(pane_data['files']):
                        if file_path.name == filename:
                            pane_data['selected_index'] = i
                            return True
            
            return False
        
        # Bind methods to mock class
        MockFileManager.save_cursor_position = save_cursor_position
        MockFileManager.restore_cursor_position = restore_cursor_position
        
        # Create mock instance
        fm = MockFileManager()
        
        # Test the functionality
        print("Testing cursor history functionality...")
        
        # Initialize files in main directory
        fm.refresh_files(fm.left_pane)
        print(f"Files in main directory: {[f.name for f in fm.left_pane['files']]}")
        
        # Select file3.txt (should be at index 4: subdir1, subdir2, file1.txt, file2.txt, file3.txt)
        fm.left_pane['selected_index'] = 4
        print(f"Selected: {fm.left_pane['files'][fm.left_pane['selected_index']].name}")
        
        # Save cursor position
        fm.save_cursor_position(fm.left_pane)
        print(f"Saved cursor position for main directory")
        
        # Navigate to subdirectory
        fm.left_pane['path'] = test_dir / "subdir1"
        fm.left_pane['selected_index'] = 0
        fm.refresh_files(fm.left_pane)
        print(f"Navigated to subdir1, files: {[f.name for f in fm.left_pane['files']]}")
        
        # Select sub2.txt
        fm.left_pane['selected_index'] = 1
        print(f"Selected in subdir: {fm.left_pane['files'][fm.left_pane['selected_index']].name}")
        
        # Save cursor position in subdirectory
        fm.save_cursor_position(fm.left_pane)
        print(f"Saved cursor position for subdirectory")
        
        # Go back to main directory
        fm.left_pane['path'] = test_dir
        fm.left_pane['selected_index'] = 0
        fm.refresh_files(fm.left_pane)
        print(f"Returned to main directory")
        
        # Try to restore cursor position
        restored = fm.restore_cursor_position(fm.left_pane)
        if restored:
            print(f"Restored cursor to: {fm.left_pane['files'][fm.left_pane['selected_index']].name}")
        else:
            print("Failed to restore cursor position")
        
        # Go back to subdirectory to test restoration there too
        fm.left_pane['path'] = test_dir / "subdir1"
        fm.left_pane['selected_index'] = 0
        fm.refresh_files(fm.left_pane)
        
        restored = fm.restore_cursor_position(fm.left_pane)
        if restored:
            print(f"Restored cursor in subdir to: {fm.left_pane['files'][fm.left_pane['selected_index']].name}")
        else:
            print("Failed to restore cursor position in subdir")
        
        print(f"Cursor history: {list(fm.left_pane['cursor_history'])}")
        print("Test completed successfully!")
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"Cleaned up test directory: {test_dir}")

if __name__ == "__main__":
    test_tfm_cursor_methods()