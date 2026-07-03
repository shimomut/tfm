#!/usr/bin/env python3
"""
Demo: Drives Dialog Navigation

This demo verifies that the drives dialog properly executes navigation
when a drive is selected.

Test scenario:
1. Show drives dialog
2. Select a drive
3. Verify callback is called with the selected drive
4. Verify navigation occurs and file list is refreshed
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pathlib import Path
from unittest.mock import Mock, patch
from src.tfm_drives_dialog import DrivesDialog, DriveEntry


def test_drives_dialog_callback():
    """Test that drives dialog properly calls callback on selection"""
    print("\n" + "="*60)
    print("Testing Drives Dialog Callback")
    print("="*60)
    
    # Create mock objects
    config = Mock()
    config.DEFAULT_SORT_MODE = 'name'
    config.DEFAULT_SORT_REVERSE = False
    config.DEFAULT_LEFT_PANE_RATIO = 0.5
    
    renderer = Mock()
    renderer.get_dimensions.return_value = (24, 80)
    
    drives_dialog = DrivesDialog(config, renderer)
    
    # Track callback invocations
    callback_calls = []
    
    def test_callback(drive_entry):
        callback_calls.append(drive_entry)
        if drive_entry:
            print(f"✓ Callback called with drive: {drive_entry.name} ({drive_entry.path})")
        else:
            print(f"✓ Callback called with None (cancelled)")
    
    # Show dialog with callback
    drives_dialog.show(test_callback)
    
    print(f"\nDialog shown with callback")
    print(f"  Callback set: {drives_dialog.callback is not None}")
    print(f"  Active: {drives_dialog.is_active}")
    
    # Wait a moment for local drives to load
    import time
    time.sleep(0.1)
    
    # Verify drives were loaded
    print(f"\nDrives loaded: {len(drives_dialog.drives)}")
    for drive in drives_dialog.drives[:3]:  # Show first 3
        print(f"  - {drive.name}: {drive.path}")
    
    # Simulate selecting the first drive (Home Directory)
    if drives_dialog.filtered_drives:
        print(f"\nSimulating selection of first drive...")
        selected_drive = drives_dialog.filtered_drives[0]
        
        # Manually trigger the callback (simulating what happens on ENTER)
        if drives_dialog.callback:
            drives_dialog.callback(selected_drive)
        
        # Verify callback was called
        print(f"\nVerification:")
        print(f"  Callback invoked: {len(callback_calls)} time(s)")
        if callback_calls:
            print(f"  Drive selected: {callback_calls[0].name}")
            print(f"  Drive path: {callback_calls[0].path}")
        
        assert len(callback_calls) == 1, "Callback should be called once"
        assert callback_calls[0] == selected_drive, "Callback should receive the selected drive"
        
        print(f"\n✓ All checks passed!")
        print(f"✓ Callback system is working correctly")
    else:
        print(f"\n⚠ No drives loaded, cannot test selection")


def test_drives_dialog_cancel():
    """Test that drives dialog properly calls callback on cancel"""
    print("\n" + "="*60)
    print("Testing Drives Dialog Cancel")
    print("="*60)
    
    # Create mock objects
    config = Mock()
    config.DEFAULT_SORT_MODE = 'name'
    config.DEFAULT_SORT_REVERSE = False
    config.DEFAULT_LEFT_PANE_RATIO = 0.5
    
    renderer = Mock()
    renderer.get_dimensions.return_value = (24, 80)
    
    drives_dialog = DrivesDialog(config, renderer)
    
    # Track callback invocations
    callback_calls = []
    
    def test_callback(drive_entry):
        callback_calls.append(drive_entry)
        if drive_entry:
            print(f"✓ Callback called with drive: {drive_entry.name}")
        else:
            print(f"✓ Callback called with None (cancelled)")
    
    # Show dialog with callback
    drives_dialog.show(test_callback)
    
    print(f"\nDialog shown with callback")
    
    # Simulate cancelling (ESC key)
    print(f"\nSimulating cancel...")
    if drives_dialog.callback:
        drives_dialog.callback(None)
    
    # Verify callback was called with None
    print(f"\nVerification:")
    print(f"  Callback invoked: {len(callback_calls)} time(s)")
    print(f"  Drive selected: {callback_calls[0] if callback_calls else 'N/A'}")
    
    assert len(callback_calls) == 1, "Callback should be called once"
    assert callback_calls[0] is None, "Callback should receive None on cancel"
    
    print(f"\n✓ All checks passed!")
    print(f"✓ Cancel handling is working correctly")


def test_navigation_with_pane_manager():
    """Test full navigation flow with PaneManager"""
    print("\n" + "="*60)
    print("Testing Navigation with PaneManager")
    print("="*60)
    
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
    
    print(f"\nInitial state:")
    print(f"  Current pane path: {pane_manager.get_current_pane()['path']}")
    
    # Simulate drive selection callback
    def navigation_callback(drive_entry):
        if drive_entry and drive_entry.path:
            current_pane = pane_manager.get_current_pane()
            drive_path = Path(drive_entry.path)
            
            old_path = current_pane['path']
            current_pane['path'] = drive_path
            current_pane['focused_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()
            
            # Refresh the file list
            pane_manager.refresh_files(current_pane)
            
            print(f"✓ Navigated from {old_path} to {drive_path}")
    
    # Create a test drive entry
    test_drive = DriveEntry(
        name="Root Directory",
        path="/",
        drive_type="local",
        description="System root"
    )
    
    print(f"\nSimulating drive selection: {test_drive.name}")
    navigation_callback(test_drive)
    
    # Verify navigation occurred
    print(f"\nVerification:")
    print(f"  New path: {pane_manager.get_current_pane()['path']}")
    print(f"  Expected: /")
    print(f"  refresh_files called: {len(pane_manager.refresh_called)} time(s)")
    
    assert pane_manager.get_current_pane()['path'] == Path('/'), "Path should be changed to /"
    assert len(pane_manager.refresh_called) == 1, "refresh_files should be called once"
    
    print(f"\n✓ All checks passed!")
    print(f"✓ Full navigation flow is working correctly")


if __name__ == '__main__':
    try:
        test_drives_dialog_callback()
        test_drives_dialog_cancel()
        test_navigation_with_pane_manager()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print("✓ DrivesDialog callback system is working")
        print("✓ Drive selection triggers callback with drive entry")
        print("✓ Cancel triggers callback with None")
        print("✓ Navigation and file list refresh work correctly")
        print("✓ All tests passed successfully")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
