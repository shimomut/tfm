#!/usr/bin/env python3
"""
Test script to verify log scroll direction fix
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_log_scroll_direction():
    """Test that log scroll directions work correctly"""
    print("Testing log scroll direction logic...")
    
    try:
        from tfm_log_manager import LogManager
        from tfm_config import get_config
        
        config = get_config()
        log_manager = LogManager(config)
        
        # Restore stdout/stderr for test output
        import sys
        sys.stdout = log_manager.original_stdout
        sys.stderr = log_manager.original_stderr
        
        # Add some test messages
        log_manager.log_messages.clear()
        for i in range(10):
            log_manager.log_messages.append((f"2024-01-01 12:00:{i:02d}", "TEST", f"Message {i}"))
        
        # Initial state: offset should be 0 (showing newest messages)
        initial_offset = log_manager.log_scroll_offset
        assert initial_offset == 0, f"Initial offset should be 0, got {initial_offset}"
        
        # Test scroll_log_up (should go toward older messages, increase offset)
        result_up = log_manager.scroll_log_up(2)
        assert result_up == True, "scroll_log_up should return True when messages exist"
        assert log_manager.log_scroll_offset == 2, f"After scroll_log_up(2), offset should be 2, got {log_manager.log_scroll_offset}"
        
        # Test scroll_log_down (should go toward newer messages, decrease offset)
        result_down = log_manager.scroll_log_down(1)
        assert result_down == True, "scroll_log_down should return True when scrolling is possible"
        assert log_manager.log_scroll_offset == 1, f"After scroll_log_down(1), offset should be 1, got {log_manager.log_scroll_offset}"
        
        # Test scroll_log_down to bottom (offset should become 0)
        result_down = log_manager.scroll_log_down(5)  # More than needed
        assert result_down == True, "scroll_log_down should return True when scrolling is possible"
        assert log_manager.log_scroll_offset == 0, f"After scrolling to bottom, offset should be 0, got {log_manager.log_scroll_offset}"
        
        # Test scroll_log_down when already at bottom (should return False)
        result_down = log_manager.scroll_log_down(1)
        assert result_down == False, "scroll_log_down should return False when already at bottom"
        assert log_manager.log_scroll_offset == 0, f"Offset should remain 0, got {log_manager.log_scroll_offset}"
        
        # Test scroll_log_up - it should always work when messages exist
        result_up = log_manager.scroll_log_up(5)
        assert result_up == True, "scroll_log_up should return True when messages exist"
        assert log_manager.log_scroll_offset == 5, f"After scroll_log_up(5), offset should be 5, got {log_manager.log_scroll_offset}"
        
        # Note: scroll_log_up no longer does boundary checking - that's handled in draw_log_pane
        
        print("✓ Log scroll direction logic works correctly")
        print(f"  - scroll_log_up increases offset (toward older messages)")
        print(f"  - scroll_log_down decreases offset (toward newer messages)")
        print(f"  - Boundary checking handled in draw_log_pane method")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing log scroll direction: {e}")
        return False

def test_scroll_method_comments():
    """Test that scroll method docstrings are correct"""
    print("Testing scroll method documentation...")
    
    try:
        from tfm_log_manager import LogManager
        
        # Check that method docstrings mention the correct direction
        scroll_up_doc = LogManager.scroll_log_up.__doc__
        scroll_down_doc = LogManager.scroll_log_down.__doc__
        
        assert "older messages" in scroll_up_doc, "scroll_log_up docstring should mention 'older messages'"
        assert "newer messages" in scroll_down_doc, "scroll_log_down docstring should mention 'newer messages'"
        
        print("✓ Scroll method documentation is correct")
        return True
        
    except Exception as e:
        print(f"✗ Error testing scroll method documentation: {e}")
        return False

def main():
    """Run log scroll direction tests"""
    print("=" * 60)
    print("TFM Log Scroll Direction Fix Test")
    print("=" * 60)
    
    tests = [
        test_log_scroll_direction,
        test_scroll_method_comments,
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
        print("✓ All log scroll direction tests passed!")
        print("✓ Log scrolling now works intuitively:")
        print("  - Up keys scroll toward older messages")
        print("  - Down keys scroll toward newer messages")
        return True
    else:
        print("✗ Some tests failed!")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)