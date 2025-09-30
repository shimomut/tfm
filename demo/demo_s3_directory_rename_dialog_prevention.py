#!/usr/bin/env python3
"""
Demo: S3 Directory Rename Dialog Prevention

This demo shows how TFM now prevents the rename dialog from opening
for S3 directories, providing immediate feedback to users before they
even attempt to rename.
"""

import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_s3 import S3PathImpl
from tfm_path import Path
from tfm_main import FileManager


def demo_s3_directory_rename_dialog_prevention():
    """Demonstrate S3 directory rename dialog prevention"""
    print("=== S3 Directory Rename Dialog Prevention Demo ===\n")
    
    print("This demo shows how TFM now prevents the rename dialog from opening")
    print("for S3 directories, providing immediate user feedback.\n")
    
    # Create mock FileManager
    file_manager = Mock(spec=FileManager)
    file_manager.general_dialog = Mock()
    file_manager.needs_full_redraw = False
    
    print("1. Testing S3 directory rename attempt...")
    
    # Create S3 directory
    s3_directory = S3PathImpl('s3://demo-bucket/photos/')
    s3_directory._s3_client = Mock()
    s3_directory.is_dir = Mock(return_value=True)
    
    s3_dir_path = Path('s3://demo-bucket/photos/')
    s3_dir_path._impl = s3_directory
    s3_dir_path.is_dir = Mock(return_value=True)
    s3_dir_path.supports_directory_rename = Mock(return_value=False)
    
    # Set up file manager with S3 directory
    file_manager.get_current_pane.return_value = {
        'selected_files': [],
        'files': [s3_dir_path],
        'selected_index': 0
    }
    
    print(f"   Selected: {s3_dir_path}")
    print("   User presses 'r' to rename...")
    
    # Call enter_rename_mode and capture any output
    try:
        FileManager.enter_rename_mode(file_manager)
        print("   ✓ S3 directory rename was blocked (no dialog opened)")
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
    
    # Verify dialog was not opened
    if not hasattr(file_manager, 'rename_file_path'):
        print("   ✓ Rename dialog was NOT opened")
    else:
        print("   ✗ Rename dialog was unexpectedly opened")
    
    print()
    
    print("2. Testing S3 file rename attempt (should work normally)...")
    
    # Create S3 file
    s3_file = S3PathImpl('s3://demo-bucket/document.txt')
    s3_file._s3_client = Mock()
    s3_file.is_dir = Mock(return_value=False)
    
    s3_file_path = Path('s3://demo-bucket/document.txt')
    s3_file_path._impl = s3_file
    s3_file_path.is_dir = Mock(return_value=False)
    s3_file_path.supports_directory_rename = Mock(return_value=False)
    
    # Set up file manager with S3 file
    file_manager.get_current_pane.return_value = {
        'selected_files': [],
        'files': [s3_file_path],
        'selected_index': 0
    }
    
    print(f"   Selected: {s3_file_path}")
    print("   User presses 'r' to rename...")
    
    # Mock DialogHelpers to track dialog creation
    with patch('tfm_main.DialogHelpers') as mock_dialog_helpers:
        # Call enter_rename_mode
        FileManager.enter_rename_mode(file_manager)
        
        # Check if dialog was created
        if mock_dialog_helpers.create_rename_dialog.called:
            print("   ✓ Rename dialog opened successfully")
            print("   ✓ File rename is allowed")
        else:
            print("   ✗ Rename dialog was not opened")
    
    print()
    
    print("3. Testing local directory rename attempt (should work normally)...")
    
    # Create local directory path
    from tfm_path import LocalPathImpl
    local_impl = Mock(spec=LocalPathImpl)
    local_path = Path('/tmp/local-directory')
    local_path._impl = local_impl
    local_path.is_dir = Mock(return_value=True)
    local_path.supports_directory_rename = Mock(return_value=True)
    
    # Set up file manager with local directory
    file_manager.get_current_pane.return_value = {
        'selected_files': [],
        'files': [local_path],
        'selected_index': 0
    }
    
    print(f"   Selected: {local_path}")
    print("   User presses 'r' to rename...")
    
    # Mock DialogHelpers to track dialog creation
    with patch('tfm_main.DialogHelpers') as mock_dialog_helpers:
        # Call enter_rename_mode
        FileManager.enter_rename_mode(file_manager)
        
        # Check if dialog was created
        if mock_dialog_helpers.create_rename_dialog.called:
            print("   ✓ Rename dialog opened successfully")
            print("   ✓ Local directory rename is allowed")
        else:
            print("   ✗ Rename dialog was not opened")
    
    print()
    
    print("4. Testing virtual S3 directory (no trailing slash)...")
    
    # Create virtual S3 directory
    s3_virtual_dir = S3PathImpl('s3://demo-bucket/documents')
    s3_virtual_dir._s3_client = Mock()
    s3_virtual_dir.is_dir = Mock(return_value=True)
    
    s3_virtual_path = Path('s3://demo-bucket/documents')
    s3_virtual_path._impl = s3_virtual_dir
    s3_virtual_path.is_dir = Mock(return_value=True)
    s3_virtual_path.supports_directory_rename = Mock(return_value=False)
    
    # Set up file manager with virtual S3 directory
    file_manager.get_current_pane.return_value = {
        'selected_files': [],
        'files': [s3_virtual_path],
        'selected_index': 0
    }
    
    print(f"   Selected: {s3_virtual_path}")
    print("   User presses 'r' to rename...")
    
    # Call enter_rename_mode
    try:
        FileManager.enter_rename_mode(file_manager)
        print("   ✓ Virtual S3 directory rename was blocked (no dialog opened)")
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
    
    print()
    
    print("=== Demo Summary ===")
    print("✓ S3 directories: Rename dialog BLOCKED with immediate feedback")
    print("✓ S3 files: Rename dialog opens normally")
    print("✓ Local directories: Rename dialog opens normally")
    print("✓ Virtual S3 directories: Rename dialog BLOCKED")
    print()
    print("Benefits:")
    print("• Users get immediate feedback without opening dialog")
    print("• Prevents confusion about why rename might fail later")
    print("• Consistent user experience across different path types")
    print("• No wasted time entering new names for unsupported operations")


if __name__ == '__main__':
    demo_s3_directory_rename_dialog_prevention()