#!/usr/bin/env python3
"""
Test script for log scrolling key bindings
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_log_scroll_constants():
    """Test that log scrolling key constants are defined"""
    print("Testing log scrolling key constants...")
    
    try:
        from tfm_const import (
            KEY_SHIFT_UP_1, KEY_SHIFT_DOWN_1,
            KEY_SHIFT_UP_2, KEY_SHIFT_DOWN_2,
            KEY_SHIFT_LEFT_1, KEY_SHIFT_RIGHT_1,
            KEY_SHIFT_LEFT_2, KEY_SHIFT_RIGHT_2
        )
        
        # Test that Shift key constants are defined and have expected values
        assert KEY_SHIFT_UP_1 == 337, f"KEY_SHIFT_UP_1 should be 337, got {KEY_SHIFT_UP_1}"
        assert KEY_SHIFT_DOWN_1 == 336, f"KEY_SHIFT_DOWN_1 should be 336, got {KEY_SHIFT_DOWN_1}"
        
        # Test new Shift+Left/Right constants
        assert KEY_SHIFT_LEFT_1 == 545, f"KEY_SHIFT_LEFT_1 should be 545, got {KEY_SHIFT_LEFT_1}"
        assert KEY_SHIFT_RIGHT_1 == 560, f"KEY_SHIFT_RIGHT_1 should be 560, got {KEY_SHIFT_RIGHT_1}"
        
        # Test alternative shift key constants
        assert KEY_SHIFT_UP_2 == 393, f"KEY_SHIFT_UP_2 should be 393, got {KEY_SHIFT_UP_2}"
        assert KEY_SHIFT_DOWN_2 == 402, f"KEY_SHIFT_DOWN_2 should be 402, got {KEY_SHIFT_DOWN_2}"
        
        print("✓ All log scrolling key constants defined correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error testing key constants: {e}")
        return False

def test_log_pane_height_method():
    """Test that the _get_log_pane_height method exists"""
    print("Testing _get_log_pane_height method...")
    
    try:
        from tfm_main import FileManager
        
        # Check that the method exists
        assert hasattr(FileManager, '_get_log_pane_height'), "_get_log_pane_height method not found"
        
        print("✓ _get_log_pane_height method exists")
        return True
        
    except Exception as e:
        print(f"✗ Error testing _get_log_pane_height method: {e}")
        return False

def test_log_manager_scroll_methods():
    """Test that log manager has scroll methods"""
    print("Testing log manager scroll methods...")
    
    try:
        from tfm_log_manager import LogManager
        from tfm_config import get_config
        
        config = get_config()
        log_manager = LogManager(config)
        
        # Test that scroll methods exist
        assert hasattr(log_manager, 'scroll_log_up'), "scroll_log_up method not found"
        assert hasattr(log_manager, 'scroll_log_down'), "scroll_log_down method not found"
        
        # Test that methods work (should return False when no scrolling possible)
        result_up = log_manager.scroll_log_up(1)
        result_down = log_manager.scroll_log_down(1)
        
        # Results should be boolean
        assert isinstance(result_up, bool), "scroll_log_up should return boolean"
        assert isinstance(result_down, bool), "scroll_log_down should return boolean"
        
        print("✓ Log manager scroll methods work correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error testing log manager scroll methods: {e}")
        return False

def test_help_content_updated():
    """Test that help content includes new key bindings"""
    print("Testing help content for new key bindings...")
    
    try:
        from test_help_content import generate_help_content
        
        help_lines = generate_help_content()
        help_text = '\n'.join(help_lines)
        
        # Check for new key bindings in help
        assert 'Shift+Up' in help_text, "Shift+Up not found in help content"
        assert 'Shift+Down' in help_text, "Shift+Down not found in help content"
        assert 'Shift+Left' in help_text, "Shift+Left not found in help content"
        assert 'Shift+Right' in help_text, "Shift+Right not found in help content"
        
        # Check for descriptions
        assert 'older messages' in help_text, "Scroll direction description not found"
        assert 'newer messages' in help_text, "Scroll direction description not found"
        
        print("✓ Help content includes new key bindings")
        return True
        
    except Exception as e:
        print(f"✗ Error testing help content: {e}")
        return False

def main():
    """Run all log scroll key tests"""
    print("=" * 60)
    print("TFM Log Scroll Keys Test")
    print("=" * 60)
    
    tests = [
        test_log_scroll_constants,
        test_log_pane_height_method,
        test_log_manager_scroll_methods,
        test_help_content_updated,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        if test():
            passed += 1
        else:
            print("Test failed!")
    
    print()
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All log scroll key tests passed!")
        return True
    else:
        print("✗ Some tests failed!")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)