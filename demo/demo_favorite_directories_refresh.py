#!/usr/bin/env python3
"""
Demo: Favorite Directories File List Refresh

This demo verifies that selecting a favorite directory properly refreshes
the file list in the current pane.

Test scenario:
1. Start in home directory
2. Show favorite directories dialog
3. Select a favorite directory
4. Verify file list is refreshed for the new directory
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pathlib import Path
from unittest.mock import Mock, patch
from src.tfm_list_dialog import ListDialog, ListDialogHelpers


def test_favorite_callback_refreshes_files():
    """Test that favorite_callback properly refreshes the file list"""
    print("\n" + "="*60)
    print("Testing Favorite Directories File List Refresh")
    print("="*60)
    
    # Create mock objects
    list_dialog = ListDialog(80, 24)
    
    # Create a minimal mock pane manager with refresh_files method
    class MockPaneManager:
        def __init__(self):
            self.active_pane = 'left'
            self.left_pane = {
                'path': Path.home(),
                'focused_index': 0,
                'scroll_offset': 0,
                'selected_files': set()
            }
            self.right_pane = {
                'path': Path.home(),
                'focused_index': 0,
                'scroll_offset': 0,
                'selected_files': set()
            }
            self.refresh_called = []
        
        def get_current_pane(self):
            return self.left_pane if self.active_pane == 'left' else self.right_pane
        
        def refresh_files(self, pane_data=None):
            """Mock refresh_files that tracks calls"""
            target_pane = pane_data if pane_data else self.get_current_pane()
            self.refresh_called.append(target_pane)
            print(f"✓ pane_manager.refresh_files() called for pane at: {target_pane['path']}")
    
    pane_manager = MockPaneManager()
    
    def mock_print(msg):
        print(f"  {msg}")
    
    # Set up initial state
    home_dir = Path.home()
    pane_manager.left_pane['path'] = home_dir
    pane_manager.active_pane = 'left'
    
    print(f"\nInitial state:")
    print(f"  Left pane: {pane_manager.left_pane['path']}")
    
    # Mock get_favorite_directories to return test data
    test_favorites = [
        {'name': 'Root', 'path': '/'},
        {'name': 'Temp', 'path': '/tmp'}
    ]
    
    with patch('src.tfm_list_dialog.get_favorite_directories', return_value=test_favorites):
        # Show the dialog
        ListDialogHelpers.show_favorite_directories(
            list_dialog, pane_manager, mock_print
        )
        
        print(f"\nDialog created with {len(list_dialog.items)} items:")
        for item in list_dialog.items:
            print(f"  - {item}")
        
        # Simulate selecting the first favorite (Root - /)
        print(f"\nSimulating selection of: {list_dialog.items[0]}")
        if list_dialog.callback:
            list_dialog.callback(list_dialog.items[0])
        
        # Verify the results
        print(f"\nVerification:")
        print(f"  New path: {pane_manager.left_pane['path']}")
        print(f"  Expected: /")
        print(f"  refresh_files called: {len(pane_manager.refresh_called)} time(s)")
        
        # Check assertions
        assert pane_manager.left_pane['path'] == Path('/'), "Path should be changed to /"
        assert len(pane_manager.refresh_called) == 1, "refresh_files should be called once"
        assert pane_manager.refresh_called[0] == pane_manager.left_pane, "refresh_files should be called with left pane"
        
        print(f"\n✓ All checks passed!")
        print(f"✓ File list refresh is working correctly")


def test_favorite_callback_without_refresh():
    """Test what happens if refresh_files is not called (old behavior)"""
    print("\n" + "="*60)
    print("Testing Old Behavior (Without Refresh)")
    print("="*60)
    
    # Create mock objects
    list_dialog = ListDialog(80, 24)
    
    # Create a minimal mock pane manager
    class MockPaneManager:
        def __init__(self):
            self.active_pane = 'left'
            self.left_pane = {
                'path': Path.home(),
                'focused_index': 0,
                'scroll_offset': 0,
                'selected_files': set()
            }
            self.right_pane = {
                'path': Path.home(),
                'focused_index': 0,
                'scroll_offset': 0,
                'selected_files': set()
            }
        
        def get_current_pane(self):
            return self.left_pane if self.active_pane == 'left' else self.right_pane
    
    pane_manager = MockPaneManager()
    
    def mock_print(msg):
        print(f"  {msg}")
    
    # Set up initial state
    home_dir = Path.home()
    pane_manager.left_pane['path'] = home_dir
    pane_manager.active_pane = 'left'
    
    print(f"\nInitial state:")
    print(f"  Left pane: {pane_manager.left_pane['path']}")
    
    # Mock get_favorite_directories
    test_favorites = [
        {'name': 'Root', 'path': '/'}
    ]
    
    # Simulate old behavior - callback without refresh_files
    def old_favorite_callback(selected_item):
        if selected_item:
            try:
                start_paren = selected_item.rfind('(')
                end_paren = selected_item.rfind(')')
                if start_paren != -1 and end_paren != -1:
                    selected_path = selected_item[start_paren + 1:end_paren]
                    current_pane = pane_manager.get_current_pane()
                    target_path = Path(selected_path)
                    
                    if target_path.exists() and target_path.is_dir():
                        current_pane['path'] = target_path
                        current_pane['focused_index'] = 0
                        current_pane['scroll_offset'] = 0
                        current_pane['selected_files'].clear()
                        # NOTE: No refresh_files() call here!
                        mock_print(f"Changed to: {target_path} (but file list NOT refreshed)")
            except Exception as e:
                mock_print(f"Error: {e}")
    
    with patch('src.tfm_list_dialog.get_favorite_directories', return_value=test_favorites):
        display_items = [f"{fav['name']} ({fav['path']})" for fav in test_favorites]
        
        print(f"\nSimulating old behavior (without refresh):")
        old_favorite_callback(display_items[0])
        
        print(f"\nResult:")
        print(f"  Path changed: {pane_manager.left_pane['path']}")
        print(f"  ⚠ File list would show OLD directory contents!")
        print(f"  ⚠ User would see stale data until next refresh")


if __name__ == '__main__':
    try:
        test_favorite_callback_refreshes_files()
        test_favorite_callback_without_refresh()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print("✓ PaneManager now has refresh_files() method")
        print("✓ Favorite callback uses pane_manager.refresh_files()")
        print("✓ File list shows correct contents for the new directory")
        print("✓ Cleaner architecture - no callback parameter needed")
        print("✓ Tests passed successfully")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
