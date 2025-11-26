#!/usr/bin/env python3
"""
Integration test for DrivesDialog with TFM main application
"""

import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_drives_dialog import DrivesDialog, DriveEntry, DrivesDialogHelpers
from tfm_path import Path


def test_drives_dialog_integration():
    """Test DrivesDialog integration with TFM components"""
    print("Testing DrivesDialog integration...")
    
    # Create mock config
    config = Mock()
    config.PROGRESS_ANIMATION_PATTERN = 'spinner'
    config.PROGRESS_ANIMATION_SPEED = 0.2
    
    # Create drives dialog
    dialog = DrivesDialog(config)
    
    # Test initialization
    assert dialog.is_active == False
    assert len(dialog.drives) == 0
    assert len(dialog.filtered_drives) == 0
    assert dialog.loading_s3 == False
    
    # Test show method (without actually running S3 scan)
    with patch.object(dialog, '_start_s3_bucket_scan'):
        dialog.show()
        assert dialog.is_active == True
        assert len(dialog.drives) >= 3  # Should have at least home, root, current
    
    # Test local drives loading
    dialog._load_local_drives()
    local_drives = [drive for drive in dialog.drives if drive.drive_type == 'local']
    assert len(local_drives) >= 3  # home, root, current
    
    # Verify home directory is included
    home_drives = [drive for drive in local_drives if "Home" in drive.name]
    assert len(home_drives) >= 1
    
    # Test filtering
    dialog.text_editor.text = "home"
    dialog._filter_drives()
    filtered_home = [drive for drive in dialog.filtered_drives if "home" in drive.name.lower()]
    assert len(filtered_home) >= 1
    
    # Test navigation helpers
    mock_pane_manager = Mock()
    current_pane = {
        'path': Path.cwd(),
        'selected_index': 0,
        'scroll_offset': 0,
        'selected_files': set()
    }
    mock_pane_manager.get_current_pane.return_value = current_pane
    mock_pane_manager.active_pane = 'left'
    
    messages = []
    def mock_print(msg):
        messages.append(msg)
    
    # Test navigation to home directory
    home_drive = DriveEntry("Home", str(Path.home()), "local", "Home directory")
    DrivesDialogHelpers.navigate_to_drive(home_drive, mock_pane_manager, mock_print)
    
    # Verify pane was updated
    assert current_pane['path'] == Path.home()
    assert current_pane['selected_index'] == 0
    assert current_pane['scroll_offset'] == 0
    assert len(messages) > 0
    assert "Home" in messages[0]
    
    print("✓ DrivesDialog integration tests passed")


def test_drive_entry_display():
    """Test DriveEntry display formatting"""
    print("Testing DriveEntry display formatting...")
    
    # Test local drive entry
    local_drive = DriveEntry("Home Directory", "/home/user", "local", "User home")
    display_text = local_drive.get_display_text()
    assert "🏠" in display_text or "📁" in display_text
    assert "Home Directory" in display_text
    assert "User home" in display_text
    
    # Test S3 drive entry
    s3_drive = DriveEntry("my-bucket", "s3://my-bucket/", "s3", "S3 Bucket")
    s3_display_text = s3_drive.get_display_text()
    assert "☁️" in s3_display_text
    assert "my-bucket" in s3_display_text
    assert "S3 Bucket" in s3_display_text
    
    print("✓ DriveEntry display tests passed")


def test_drives_dialog_key_binding():
    """Test that drives dialog key binding is properly configured"""
    print("Testing drives dialog key binding...")
    
    # Import config to check key bindings
    try:
        from _config import Config
        config = Config()
        
        # Check that drives_dialog key binding exists
        assert hasattr(config, 'KEY_BINDINGS')
        assert 'drives_dialog' in config.KEY_BINDINGS
        
        # Check that it's bound to 'd' or 'D'
        drives_keys = config.KEY_BINDINGS['drives_dialog']
        assert 'd' in drives_keys or 'D' in drives_keys
        
        print("✓ Drives dialog key binding tests passed")
        
    except ImportError:
        print("⚠ Could not test key bindings (config not available)")


def main():
    """Run all integration tests"""
    print("Running DrivesDialog integration tests...")
    print("=" * 50)
    
    try:
        test_drives_dialog_integration()
        test_drive_entry_display()
        test_drives_dialog_key_binding()
        
        print("=" * 50)
        print("✓ All DrivesDialog integration tests passed!")
        return 0
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())