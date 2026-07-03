#!/usr/bin/env python3
"""
Demo: Archive Unsupported Operations

This demo shows how TFM handles unsupported write operations on archive files.
It demonstrates that error messages are shown BEFORE any operation attempts.

Unsupported operations:
1. Deleting files within archives
2. Moving files from archives
3. Moving files into archives
4. Copying files into archives

Supported operations:
- Copying files FROM archives (extraction)
- Viewing files within archives
- Browsing archive contents
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_file_operation_ui import FileOperationUI
from unittest.mock import Mock


def create_mock_file_manager():
    """Create a mock file manager for testing"""
    mock_fm = Mock()
    mock_fm.log_manager = Mock()
    mock_fm.progress_manager = Mock()
    mock_fm.cache_manager = Mock()
    mock_fm.config = Mock()
    mock_fm.config.CONFIRM_COPY = False
    mock_fm.config.CONFIRM_DELETE = False
    return mock_fm


def demo_validation_logic():
    """Demonstrate the validation logic for archive operations"""
    print("=" * 70)
    print("DEMO: Archive Unsupported Operations Validation")
    print("=" * 70)
    print()
    
    # Create FileOperationUI instance
    mock_fm = create_mock_file_manager()
    mock_fo = Mock()
    file_ops_ui = FileOperationUI(mock_fm, mock_fo)
    
    # Test cases
    test_cases = [
        {
            'name': 'Delete from archive',
            'operation': 'delete',
            'sources': [Path('archive:///home/user/data.zip#file.txt')],
            'dest': None,
            'expected': False
        },
        {
            'name': 'Delete from filesystem',
            'operation': 'delete',
            'sources': [Path('/home/user/file.txt')],
            'dest': None,
            'expected': True
        },
        {
            'name': 'Move from archive',
            'operation': 'move',
            'sources': [Path('archive:///home/user/data.zip#file.txt')],
            'dest': Path('/home/user/destination'),
            'expected': False
        },
        {
            'name': 'Move to archive',
            'operation': 'move',
            'sources': [Path('/home/user/file.txt')],
            'dest': Path('archive:///home/user/data.zip#'),
            'expected': False
        },
        {
            'name': 'Move filesystem to filesystem',
            'operation': 'move',
            'sources': [Path('/home/user/file.txt')],
            'dest': Path('/home/user/destination'),
            'expected': True
        },
        {
            'name': 'Copy to archive',
            'operation': 'copy',
            'sources': [Path('/home/user/file.txt')],
            'dest': Path('archive:///home/user/data.zip#'),
            'expected': False
        },
        {
            'name': 'Copy from archive (extraction)',
            'operation': 'copy',
            'sources': [Path('archive:///home/user/data.zip#file.txt')],
            'dest': Path('/home/user/destination'),
            'expected': True
        },
        {
            'name': 'Copy filesystem to filesystem',
            'operation': 'copy',
            'sources': [Path('/home/user/file.txt')],
            'dest': Path('/home/user/destination'),
            'expected': True
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        print(f"   Operation: {test['operation']}")
        print(f"   Source(s): {[str(s) for s in test['sources']]}")
        if test['dest']:
            print(f"   Destination: {test['dest']}")
        
        is_valid, error_msg = file_ops_ui._validate_operation_on_archives(
            test['operation'],
            test['sources'],
            test['dest']
        )
        
        if is_valid:
            print(f"   ✅ ALLOWED")
        else:
            print(f"   ❌ BLOCKED")
            print(f"   Error: {error_msg}")
        
        # Verify expectation
        if is_valid == test['expected']:
            print(f"   ✓ Result matches expectation")
        else:
            print(f"   ✗ UNEXPECTED RESULT!")
        
        print()


def demo_error_messages():
    """Demonstrate the error messages shown to users"""
    print("=" * 70)
    print("DEMO: Error Messages for Unsupported Operations")
    print("=" * 70)
    print()
    
    error_messages = {
        'delete': "Cannot delete files within archives. Archives are read-only.",
        'move_from': "Cannot move files from archives. Use copy instead. Archives are read-only.",
        'move_to': "Cannot move files into archives. Archives are read-only.",
        'copy_to': "Cannot copy files into archives. Archives are read-only."
    }
    
    print("When users attempt unsupported operations, they see these messages:")
    print()
    
    for operation, message in error_messages.items():
        print(f"Operation: {operation.replace('_', ' ').title()}")
        print(f"Message: \"{message}\"")
        print()


def demo_supported_operations():
    """Show which operations ARE supported"""
    print("=" * 70)
    print("DEMO: Supported Operations on Archives")
    print("=" * 70)
    print()
    
    supported = [
        ("Browse archive contents", "Navigate into archives with ENTER key"),
        ("Navigate within archives", "Use arrow keys, ENTER, and backspace"),
        ("View files in archives", "View text files with built-in viewer"),
        ("Search within archives", "Use search dialog to find files"),
        ("Copy FROM archives", "Extract files to local filesystem or S3"),
        ("View file metadata", "See file sizes, dates, permissions"),
        ("Sort archive contents", "Sort by name, size, date, type, extension"),
    ]
    
    print("These operations ARE supported:")
    print()
    
    for i, (operation, description) in enumerate(supported, 1):
        print(f"{i}. {operation}")
        print(f"   {description}")
        print()


def main():
    """Run all demos"""
    demo_validation_logic()
    print("\n")
    demo_error_messages()
    print("\n")
    demo_supported_operations()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Key Points:")
    print("1. Archives are READ-ONLY for browsing and extraction")
    print("2. Error messages are shown BEFORE any operation attempts")
    print("3. Users are clearly informed why operations cannot proceed")
    print("4. Copy FROM archives (extraction) IS supported")
    print("5. All browsing and viewing operations ARE supported")
    print()
    print("This design provides a clear, consistent user experience while")
    print("maintaining the integrity of archive files.")
    print()


if __name__ == '__main__':
    main()
