#!/usr/bin/env python3
"""
Demo: Toggle Hidden Files Refresh

This demo verifies that toggling hidden files properly refreshes
the file list to show/hide hidden files.

Test scenario:
1. Start with hidden files hidden
2. Get initial file count
3. Toggle hidden files to show them
4. Verify file list is refreshed and count increases
5. Toggle hidden files to hide them
6. Verify file list is refreshed and count decreases
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pathlib import Path
from unittest.mock import Mock
from src.tfm_file_operations import FileListManager


def test_toggle_hidden_files_refresh():
    """Test that toggling hidden files refreshes the file list"""
    print("\n" + "="*60)
    print("Testing Toggle Hidden Files Refresh")
    print("="*60)
    
    # Create file operations with proper config
    config = Mock()
    config.SHOW_HIDDEN_FILES = False  # Set default value
    file_ops = FileListManager(config)
    
    # Create a test pane with a directory that has hidden files
    test_dir = Path.home()  # Home directory typically has hidden files
    pane_data = {
        'path': test_dir,
        'focused_index': 0,
        'scroll_offset': 0,
        'files': [],
        'selected_files': set(),
        'sort_mode': 'name',
        'sort_reverse': False,
        'filter_pattern': ""
    }
    
    print(f"\nTest directory: {test_dir}")
    
    # Initial state - hidden files should be hidden by default
    print(f"\nInitial state:")
    print(f"  show_hidden: {file_ops.show_hidden}")
    
    # Refresh files with hidden files hidden
    file_ops.refresh_files(pane_data)
    initial_count = len(pane_data['files'])
    initial_files = [f.name for f in pane_data['files'][:5]]  # First 5 files
    
    print(f"  File count (hidden files hidden): {initial_count}")
    print(f"  First 5 files: {initial_files}")
    print(f"  Any hidden files shown: {any(f.name.startswith('.') for f in pane_data['files'])}")
    
    # Toggle to show hidden files
    print(f"\nToggling to SHOW hidden files...")
    file_ops.show_hidden = True
    file_ops.refresh_files(pane_data)
    
    shown_count = len(pane_data['files'])
    shown_files = [f.name for f in pane_data['files'][:5]]  # First 5 files
    hidden_files_shown = [f.name for f in pane_data['files'] if f.name.startswith('.')][:5]
    
    print(f"  show_hidden: {file_ops.show_hidden}")
    print(f"  File count (hidden files shown): {shown_count}")
    print(f"  First 5 files: {shown_files}")
    print(f"  First 5 hidden files: {hidden_files_shown}")
    
    # Verify more files are shown
    assert shown_count > initial_count, f"Should show more files when hidden files are visible ({shown_count} vs {initial_count})"
    assert any(f.name.startswith('.') for f in pane_data['files']), "Should have hidden files in the list"
    
    print(f"  ✓ File count increased from {initial_count} to {shown_count}")
    print(f"  ✓ Hidden files are now visible")
    
    # Toggle to hide hidden files again
    print(f"\nToggling to HIDE hidden files...")
    file_ops.show_hidden = False
    file_ops.refresh_files(pane_data)
    
    hidden_count = len(pane_data['files'])
    hidden_files_list = [f.name for f in pane_data['files'][:5]]  # First 5 files
    
    print(f"  show_hidden: {file_ops.show_hidden}")
    print(f"  File count (hidden files hidden): {hidden_count}")
    print(f"  First 5 files: {hidden_files_list}")
    print(f"  Any hidden files shown: {any(f.name.startswith('.') for f in pane_data['files'])}")
    
    # Verify fewer files are shown
    assert hidden_count == initial_count, f"Should show same count as initial ({hidden_count} vs {initial_count})"
    assert not any(f.name.startswith('.') for f in pane_data['files']), "Should not have hidden files in the list"
    
    print(f"  ✓ File count decreased from {shown_count} to {hidden_count}")
    print(f"  ✓ Hidden files are now hidden")
    
    print(f"\n✓ All checks passed!")
    print(f"✓ Toggle hidden files properly refreshes file list")


def test_toggle_hidden_files_method():
    """Test the toggle_hidden_files method"""
    print("\n" + "="*60)
    print("Testing toggle_hidden_files() Method")
    print("="*60)
    
    # Create file operations with proper config
    config = Mock()
    config.SHOW_HIDDEN_FILES = False  # Set default value
    file_ops = FileListManager(config)
    
    print(f"\nInitial state: show_hidden = {file_ops.show_hidden}")
    
    # Toggle to show
    new_state = file_ops.toggle_hidden_files()
    print(f"After toggle: show_hidden = {file_ops.show_hidden}")
    assert new_state == True, "Should return True after first toggle"
    assert file_ops.show_hidden == True, "show_hidden should be True"
    
    # Toggle to hide
    new_state = file_ops.toggle_hidden_files()
    print(f"After toggle: show_hidden = {file_ops.show_hidden}")
    assert new_state == False, "Should return False after second toggle"
    assert file_ops.show_hidden == False, "show_hidden should be False"
    
    print(f"\n✓ toggle_hidden_files() method works correctly")


if __name__ == '__main__':
    try:
        test_toggle_hidden_files_method()
        test_toggle_hidden_files_refresh()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print("✓ toggle_hidden_files() method toggles the state correctly")
        print("✓ refresh_files() respects the show_hidden setting")
        print("✓ File list updates when hidden files are toggled")
        print("✓ All tests passed successfully")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
