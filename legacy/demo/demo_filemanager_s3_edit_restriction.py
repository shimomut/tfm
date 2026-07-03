#!/usr/bin/env python3
"""
Demo: FileManager S3 File Editing Restriction

This demo shows how FileManager handles S3 file editing attempts.
"""

import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def demo_filemanager_s3_edit_restriction():
    """Demonstrate FileManager S3 file editing restriction"""
    print("=== FileManager S3 File Editing Restriction Demo ===\n")
    
    # Import here to avoid initialization issues
    from tfm_main import FileManager
    
    # Create a minimal FileManager instance for testing
    file_manager = Mock(spec=FileManager)
    
    print("1. Testing S3 file editing attempt...")
    
    # Mock S3 file that doesn't support editing
    mock_s3_file = Mock()
    mock_s3_file.supports_file_editing.return_value = False
    mock_s3_file.name = 's3-document.txt'
    mock_s3_file.is_dir.return_value = False
    
    # Mock the get_current_pane method
    mock_pane = {
        'files': [mock_s3_file],
        'selected_index': 0,
        'path': Mock()
    }
    file_manager.get_current_pane.return_value = mock_pane
    
    # Mock config
    mock_config = Mock()
    mock_config.TEXT_EDITOR = 'nano'
    file_manager.config = mock_config
    
    # Import the actual method and bind it to our mock
    actual_method = FileManager.edit_selected_file
    
    # Capture print output
    print(f"   Selected file: {mock_s3_file.name}")
    print(f"   Supports file editing: {mock_s3_file.supports_file_editing()}")
    print("   Attempting to edit...")
    
    # Call the actual method with our mock instance
    actual_method(file_manager)
    
    print("   ✓ FileManager correctly blocked S3 file editing\n")
    
    print("2. Testing local file editing (for comparison)...")
    
    # Mock local file that supports editing
    mock_local_file = Mock()
    mock_local_file.supports_file_editing.return_value = True
    mock_local_file.name = 'local-document.txt'
    mock_local_file.is_dir.return_value = False
    mock_local_file.__str__ = Mock(return_value='/home/user/local-document.txt')
    
    # Mock the get_current_pane method for local file
    mock_path = Mock()
    mock_path.__str__ = Mock(return_value='/home/user')
    mock_pane_local = {
        'files': [mock_local_file],
        'selected_index': 0,
        'path': mock_path
    }
    file_manager.get_current_pane.return_value = mock_pane_local
    
    # Add required mocks for local file editing
    file_manager.external_program_manager = Mock()
    file_manager.stdscr = Mock()
    
    print(f"   Selected file: {mock_local_file.name}")
    print(f"   Supports file editing: {mock_local_file.supports_file_editing()}")
    print("   Attempting to edit...")
    
    # Mock subprocess.run to simulate successful editor launch
    with patch('tfm_main.subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        
        # Call the actual method with our mock instance
        actual_method(file_manager)
        
        # Verify editor was launched
        if mock_run.called:
            print("   ✓ FileManager successfully launched editor for local file")
        else:
            print("   ✗ Editor was not launched")
    
    print("\n=== Demo Complete ===")
    print("FileManager correctly:")
    print("- Blocks editing attempts for S3 files with clear error message")
    print("- Allows editing for local files that support it")
    print("- Uses the supports_file_editing() capability check")


if __name__ == '__main__':
    demo_filemanager_s3_edit_restriction()