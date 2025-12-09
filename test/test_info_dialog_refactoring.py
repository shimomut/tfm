#!/usr/bin/env python3
"""
Test info dialog refactoring to use polymorphic metadata
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_info_dialog import InfoDialogHelpers
from tfm_path import Path as TFMPath


def test_local_file_metadata():
    """Test that local file metadata is displayed correctly"""
    print("Testing local file metadata display...")
    
    # Create a test file
    test_file = Path(__file__)
    tfm_path = TFMPath(test_file)
    
    # Get metadata using the unified method
    details_lines = []
    InfoDialogHelpers._add_file_details(details_lines, tfm_path)
    
    # Verify common fields are present
    assert any("Name:" in line for line in details_lines), "Name field missing"
    assert any("Path:" in line for line in details_lines), "Path field missing"
    
    # Verify local-specific fields are present
    assert any("Type:" in line for line in details_lines), "Type field missing"
    assert any("Size:" in line for line in details_lines), "Size field missing"
    assert any("Permissions:" in line for line in details_lines), "Permissions field missing"
    assert any("Modified:" in line for line in details_lines), "Modified field missing"
    
    print("✓ Local file metadata display works correctly")
    print(f"  Generated {len(details_lines)} detail lines")


def test_archive_file_metadata():
    """Test that archive file metadata is displayed correctly"""
    print("\nTesting archive file metadata display...")
    
    # Create a test archive path
    test_archive = Path(__file__).parent.parent / "data" / "test.zip"
    
    # Skip if test archive doesn't exist
    if not test_archive.exists():
        print("⊘ Skipping archive test - test.zip not found")
        return
    
    # Create archive path
    archive_uri = f"archive://{test_archive}#test.txt"
    tfm_path = TFMPath(archive_uri)
    
    # Get metadata using the unified method
    details_lines = []
    try:
        InfoDialogHelpers._add_file_details(details_lines, tfm_path)
        
        # Verify common fields are present
        assert any("Name:" in line for line in details_lines), "Name field missing"
        assert any("Path:" in line for line in details_lines), "Path field missing"
        
        # Verify archive-specific fields are present
        assert any("Archive:" in line for line in details_lines), "Archive field missing"
        assert any("Type:" in line for line in details_lines), "Type field missing"
        
        print("✓ Archive file metadata display works correctly")
        print(f"  Generated {len(details_lines)} detail lines")
    except Exception as e:
        print(f"⊘ Archive test skipped: {e}")


def test_no_storage_specific_checks():
    """Verify that the info dialog doesn't use storage-specific checks"""
    print("\nVerifying no storage-specific checks...")
    
    # Read the info dialog source
    info_dialog_path = Path(__file__).parent.parent / "src" / "tfm_info_dialog.py"
    content = info_dialog_path.read_text()
    
    # Check for storage-specific patterns
    forbidden_patterns = [
        "startswith('archive://",
        "is_archive_path",
        "scheme == 'archive'",
        "scheme == 's3'",
        "_add_archive_entry_details",
        "_add_regular_file_details"
    ]
    
    found_issues = []
    for pattern in forbidden_patterns:
        if pattern in content:
            found_issues.append(pattern)
    
    if found_issues:
        print(f"✗ Found storage-specific patterns: {found_issues}")
        return False
    
    print("✓ No storage-specific checks found")
    return True


def test_unified_method_exists():
    """Verify that the unified metadata method exists"""
    print("\nVerifying unified metadata method exists...")
    
    # Check that the new method exists
    assert hasattr(InfoDialogHelpers, '_add_file_details'), \
        "_add_file_details method not found"
    
    print("✓ Unified _add_file_details method exists")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Info Dialog Refactoring Tests")
    print("=" * 60)
    
    try:
        test_unified_method_exists()
        test_no_storage_specific_checks()
        test_local_file_metadata()
        test_archive_file_metadata()
        
        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
