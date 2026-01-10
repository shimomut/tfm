#!/usr/bin/env python3
"""
Test SSH Content Search Fix

Verifies that content search works correctly for SSH paths by using
file_path.open() instead of open(file_path).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from unittest.mock import Mock, MagicMock, patch, mock_open
from tfm_search_dialog import SearchDialog
from tfm_path import Path


def test_is_text_file_uses_path_open():
    """Test that _is_text_file uses file_path.open() instead of open()"""
    print("\n=== Test 1: _is_text_file uses Path.open() ===")
    
    # Create a mock config
    config = Mock()
    config.MAX_SEARCH_RESULTS = 10000
    
    # Create search dialog
    dialog = SearchDialog(config)
    
    # Create a mock SSH path with no extension
    mock_path = Mock(spec=Path)
    mock_path.suffix = ''  # No extension, will trigger binary check
    mock_path.__str__ = Mock(return_value='ssh://test/file')
    
    # Mock the open method to return binary data
    mock_file = MagicMock()
    mock_file.__enter__ = Mock(return_value=mock_file)
    mock_file.__exit__ = Mock(return_value=False)
    mock_file.read = Mock(return_value=b'Hello World\n')  # Text content
    mock_path.open = Mock(return_value=mock_file)
    
    # Call _is_text_file
    result = dialog._is_text_file(mock_path)
    
    # Verify that path.open() was called (not built-in open())
    mock_path.open.assert_called_once_with('rb')
    print(f"✓ Path.open('rb') was called correctly")
    
    # Verify result is True (text file)
    assert result == True, f"Expected True, got {result}"
    print(f"✓ Correctly identified as text file")
    
    print("✓ Test 1 passed\n")


def test_is_text_file_with_extension():
    """Test that _is_text_file correctly identifies files with text extensions"""
    print("=== Test 2: Text file with extension ===")
    
    config = Mock()
    config.MAX_SEARCH_RESULTS = 10000
    dialog = SearchDialog(config)
    
    # Create a mock path with .py extension
    mock_path = Mock(spec=Path)
    mock_path.suffix = '.py'
    mock_path.__str__ = Mock(return_value='ssh://test/script.py')
    
    # Call _is_text_file
    result = dialog._is_text_file(mock_path)
    
    # Should return True without opening the file
    assert result == True, f"Expected True, got {result}"
    print(f"✓ Correctly identified .py file as text")
    
    print("✓ Test 2 passed\n")


def test_is_text_file_binary_content():
    """Test that _is_text_file correctly identifies binary files"""
    print("=== Test 3: Binary file detection ===")
    
    config = Mock()
    config.MAX_SEARCH_RESULTS = 10000
    dialog = SearchDialog(config)
    
    # Create a mock path with no extension
    mock_path = Mock(spec=Path)
    mock_path.suffix = ''
    mock_path.__str__ = Mock(return_value='ssh://test/binary_file')
    
    # Mock the open method to return binary data
    mock_file = MagicMock()
    mock_file.__enter__ = Mock(return_value=mock_file)
    mock_file.__exit__ = Mock(return_value=False)
    # Binary content (mostly non-printable bytes)
    mock_file.read = Mock(return_value=b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09')
    mock_path.open = Mock(return_value=mock_file)
    
    # Call _is_text_file
    result = dialog._is_text_file(mock_path)
    
    # Verify that path.open() was called
    mock_path.open.assert_called_once_with('rb')
    print(f"✓ Path.open('rb') was called correctly")
    
    # Verify result is False (binary file)
    assert result == False, f"Expected False, got {result}"
    print(f"✓ Correctly identified as binary file")
    
    print("✓ Test 3 passed\n")


def test_is_text_file_handles_errors():
    """Test that _is_text_file handles errors gracefully"""
    print("=== Test 4: Error handling ===")
    
    config = Mock()
    config.MAX_SEARCH_RESULTS = 10000
    dialog = SearchDialog(config)
    
    # Create a mock path that raises an error
    mock_path = Mock(spec=Path)
    mock_path.suffix = ''
    mock_path.__str__ = Mock(return_value='ssh://test/error_file')
    mock_path.open = Mock(side_effect=OSError("Permission denied"))
    
    # Call _is_text_file - should handle error gracefully
    result = dialog._is_text_file(mock_path)
    
    # Should return False when error occurs
    assert result == False, f"Expected False on error, got {result}"
    print(f"✓ Correctly handled OSError")
    
    print("✓ Test 4 passed\n")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("SSH Content Search Fix - Test Suite")
    print("="*60)
    
    try:
        test_is_text_file_uses_path_open()
        test_is_text_file_with_extension()
        test_is_text_file_binary_content()
        test_is_text_file_handles_errors()
        
        print("="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
