#!/usr/bin/env python3
"""
Test script for DrivesDialog functionality
"""

import sys
import os
from ttk import KeyEvent, KeyCode, ModifierKey
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_drives_dialog import DrivesDialog, DriveEntry, DrivesDialogHelpers
from tfm_path import Path


def test_drive_entry():
    """Test DriveEntry functionality"""
    print("Testing DriveEntry...")
    
    # Test local drive entry
    local_drive = DriveEntry("Home", "/home/user", "local", "User home directory")
    assert local_drive.name == "Home"
    assert local_drive.path == "/home/user"
    assert local_drive.drive_type == "local"
    assert local_drive.description == "User home directory"
    
    display_text = local_drive.get_display_text()
    assert "🏠" in display_text or "📁" in display_text
    assert "Home" in display_text
    assert "User home directory" in display_text
    
    # Test S3 drive entry
    s3_drive = DriveEntry("my-bucket", "s3://my-bucket/", "s3", "S3 Bucket")
    assert s3_drive.name == "my-bucket"
    assert s3_drive.path == "s3://my-bucket/"
    assert s3_drive.drive_type == "s3"
    
    s3_display_text = s3_drive.get_display_text()
    assert "☁️" in s3_display_text
    assert "my-bucket" in s3_display_text
    
    print("✓ DriveEntry tests passed")


def test_drives_dialog_basic():
    """Test basic DrivesDialog functionality"""
    print("Testing DrivesDialog basic functionality...")
    
    # Create mock config
    config = Mock()
    config.PROGRESS_ANIMATION_PATTERN = 'spinner'
    config.PROGRESS_ANIMATION_SPEED = 0.2
    
    # Create drives dialog
    dialog = DrivesDialog(config)
    
    # Test initial state
    assert dialog.is_active == False
    assert len(dialog.drives) == 0
    assert len(dialog.filtered_drives) == 0
    assert dialog.loading_s3 == False
    
    print("✓ DrivesDialog basic tests passed")


def test_drives_dialog_helpers():
    """Test DrivesDialogHelpers functionality"""
    print("Testing DrivesDialogHelpers...")
    
    # Create mock pane manager
    pane_manager = Mock()
    current_pane = {
        'path': Path.cwd(),
        'selected_index': 0,
        'scroll_offset': 0,
        'selected_files': set()
    }
    pane_manager.get_current_pane.return_value = current_pane
    pane_manager.active_pane = 'left'
    
    # Create mock print function
    messages = []
    def mock_print(msg):
        messages.append(msg)
    
    # Test navigation to local drive
    local_drive = DriveEntry("Home", str(Path.home()), "local", "Home directory")
    DrivesDialogHelpers.navigate_to_drive(local_drive, pane_manager, mock_print)
    
    # Check that pane was updated
    assert current_pane['path'] == Path.home()
    assert current_pane['selected_index'] == 0
    assert current_pane['scroll_offset'] == 0
    assert len(current_pane['selected_files']) == 0
    assert len(messages) > 0
    assert "Home" in messages[0]
    
    print("✓ DrivesDialogHelpers tests passed")


def main():
    """Run all tests"""
    print("Running DrivesDialog tests...")
    print("=" * 50)
    
    try:
        test_drive_entry()
        test_drives_dialog_basic()
        test_drives_dialog_helpers()
        
        print("=" * 50)
        print("✓ All DrivesDialog tests passed!")
        return 0
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())