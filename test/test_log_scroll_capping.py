#!/usr/bin/env python3
"""
Test script to verify log scroll capping works correctly
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_log_scroll_capping():
    """Test that log scroll offset is capped correctly based on display height"""
    print("Testing log scroll capping logic...")
    
    try:
        from tfm_log_manager import LogManager
        from tfm_config import get_config
        from ttk.input_event import InputEvent, KeyCode, ModifierKey
        
        config = get_config()
        log_manager = LogManager(config)
        
        # Restore stdout/stderr for test output
        import sys
        sys.stdout = log_manager.original_stdout
        sys.stderr = log_manager.original_stderr
        
        # Add test messages
        log_manager.log_messages.clear()
        for i in range(20):  # 20 messages
            log_manager.log_messages.append((f"2024-01-01 12:00:{i:02d}", "TEST", f"Message {i}"))
        
        # Test with different display heights
        test_cases = [
            {"display_height": 5, "expected_max_scroll": 15},   # 20 - 5 = 15
            {"display_height": 10, "expected_max_scroll": 10},  # 20 - 10 = 10
            {"display_height": 20, "expected_max_scroll": 0},   # 20 - 20 = 0 (all messages fit)
            {"display_height": 25, "expected_max_scroll": 0},   # 20 - 25 = 0 (more space than messages)
        ]
        
        for case in test_cases:
            display_height = case["display_height"]
            expected_max_scroll = case["expected_max_scroll"]
            
            # Reset scroll offset
            log_manager.log_scroll_offset = 0
            
            # Try to scroll way beyond the limit
            log_manager.scroll_log_up(1000)  # Scroll way more than should be possible
            
            # Simulate drawing (which should cap the offset)
            # We'll create a mock stdscr for this test
            class MockStdscr:
                def addstr(self, *args): pass
                def getmaxyx(self): return (50, 100)
            
            mock_stdscr = MockStdscr()
            
            # Call draw_log_pane which should cap the scroll offset
            log_manager.draw_log_pane(mock_stdscr, 0, display_height, 80)
            
            # Check that scroll offset is properly capped
            actual_offset = log_manager.log_scroll_offset
            assert actual_offset <= expected_max_scroll, \
                f"Display height {display_height}: offset {actual_offset} > max {expected_max_scroll}"
            
            print(f"✓ Display height {display_height}: max scroll {expected_max_scroll}, actual offset {actual_offset}")
        
        print("✓ Log scroll capping works correctly for all display heights")
        return True
        
    except Exception as e:
        print(f"✗ Error testing log scroll capping: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scroll_percentage_with_display_height():
    """Test that scroll percentage calculation uses display height correctly"""
    print("Testing scroll percentage calculation with display height...")
    
    try:
        from tfm_log_manager import LogManager
        from tfm_config import get_config
        
        config = get_config()
        log_manager = LogManager(config)
        
        # Restore stdout/stderr for test output
        import sys
        sys.stdout = log_manager.original_stdout
        sys.stderr = log_manager.original_stderr
        
        # Add test messages
        log_manager.log_messages.clear()
        for i in range(10):
            log_manager.log_messages.append((f"2024-01-01 12:00:{i:02d}", "TEST", f"Message {i}"))
        
        # Test with display height of 5 (so max scroll is 5)
        display_height = 5
        
        # Test different scroll positions
        test_cases = [
            {"offset": 0, "expected_percentage": 0},    # At bottom (newest)
            {"offset": 2, "expected_percentage": 40},   # 2/5 = 40%
            {"offset": 5, "expected_percentage": 100},  # At top (oldest)
        ]
        
        for case in test_cases:
            log_manager.log_scroll_offset = case["offset"]
            percentage = log_manager.get_log_scroll_percentage(display_height)
            expected = case["expected_percentage"]
            
            assert abs(percentage - expected) < 1, \
                f"Offset {case['offset']}: expected {expected}%, got {percentage}%"
            
            print(f"✓ Offset {case['offset']}: {percentage}% (expected {expected}%)")
        
        print("✓ Scroll percentage calculation works correctly with display height")
        return True
        
    except Exception as e:
        print(f"✗ Error testing scroll percentage: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scroll_boundary_conditions():
    """Test scroll boundary conditions"""
    print("Testing scroll boundary conditions...")
    
    try:
        from tfm_log_manager import LogManager
        from tfm_config import get_config
        
        config = get_config()
        log_manager = LogManager(config)
        
        # Restore stdout/stderr for test output
        import sys
        sys.stdout = log_manager.original_stdout
        sys.stderr = log_manager.original_stderr
        
        # Test with empty log
        log_manager.log_messages.clear()
        result = log_manager.scroll_log_up(1)
        assert result == False, "Should not be able to scroll empty log"
        assert log_manager.log_scroll_offset == 0, "Offset should remain 0 for empty log"
        
        # Test with single message
        log_manager.log_messages.append(("2024-01-01 12:00:00", "TEST", "Single message"))
        
        # With display height >= 1, there should be no scrolling possible
        class MockStdscr:
            def addstr(self, *args): pass
            def getmaxyx(self): return (50, 100)
        
        mock_stdscr = MockStdscr()
        
        # Try to scroll
        log_manager.scroll_log_up(1)
        
        # Draw with display height 5 (more than messages)
        log_manager.draw_log_pane(mock_stdscr, 0, 5, 80)
        
        # Offset should be capped to 0 since all messages fit
        assert log_manager.log_scroll_offset == 0, \
            f"Single message should not allow scrolling, offset: {log_manager.log_scroll_offset}"
        
        print("✓ Boundary conditions handled correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error testing boundary conditions: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all log scroll capping tests"""
    print("=" * 60)
    print("TFM Log Scroll Capping Test")
    print("=" * 60)
    
    tests = [
        test_log_scroll_capping,
        test_scroll_percentage_with_display_height,
        test_scroll_boundary_conditions,
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
        print("✓ All log scroll capping tests passed!")
        print("✓ Log scroll offset is now properly capped based on display height")
        return True
    else:
        print("✗ Some tests failed!")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)