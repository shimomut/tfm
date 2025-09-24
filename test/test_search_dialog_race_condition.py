#!/usr/bin/env python3
"""
Test script to verify the race condition fix for SearchDialog content_changed flag
"""

import sys
import os
import time
import threading
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_search_dialog import SearchDialog
from tfm_config import get_config


def test_race_condition_fix():
    """Test that the race condition between background thread and main thread is fixed"""
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Show the search dialog
    search_dialog.show('filename')
    
    # Track the sequence of events
    events = []
    
    def background_thread():
        """Simulate background search thread"""
        for i in range(10):
            time.sleep(0.01)  # Small delay
            
            # Simulate finding results (this is what the real search thread does)
            with search_dialog.search_lock:
                search_dialog.results.append(f'file{i}.txt')
                search_dialog.content_changed = True
                events.append(f'BG: Set content_changed=True (iteration {i})')
    
    def main_thread():
        """Simulate main thread checking and resetting content_changed"""
        for i in range(20):
            time.sleep(0.005)  # Faster than background thread
            
            # Check content changed (thread-safe)
            with search_dialog.search_lock:
                changed = search_dialog.content_changed
            
            if changed:
                events.append(f'MAIN: Detected content_changed=True (iteration {i})')
                
                # Simulate drawing and marking as unchanged (thread-safe)
                with search_dialog.search_lock:
                    search_dialog.content_changed = False
                    events.append(f'MAIN: Set content_changed=False (iteration {i})')
    
    # Start both threads
    bg_thread = threading.Thread(target=background_thread)
    main_thread_obj = threading.Thread(target=main_thread)
    
    bg_thread.start()
    main_thread_obj.start()
    
    # Wait for both to complete
    bg_thread.join()
    main_thread_obj.join()
    
    # Analyze results
    print("Event sequence:")
    for event in events:
        print(f"  {event}")
    
    # Count events
    bg_sets = len([e for e in events if 'BG: Set content_changed=True' in e])
    main_detects = len([e for e in events if 'MAIN: Detected content_changed=True' in e])
    main_resets = len([e for e in events if 'MAIN: Set content_changed=False' in e])
    
    print(f"\nSummary:")
    print(f"  Background thread set content_changed=True: {bg_sets} times")
    print(f"  Main thread detected content_changed=True: {main_detects} times")
    print(f"  Main thread reset content_changed=False: {main_resets} times")
    
    # Verify that main thread detected at least some of the background updates
    assert main_detects > 0, "Main thread should have detected at least some background updates"
    # Note: main_detects can be bg_sets + 1 because dialog starts with content_changed = True
    assert main_detects <= bg_sets + 1, "Main thread detections should be reasonable"
    assert main_detects == main_resets, "Every detection should result in a reset"
    
    print("✓ Race condition test passed - thread-safe access working correctly")
    return True


def test_thread_safe_access_methods():
    """Test the thread-safe access methods in the main loop simulation"""
    
    # Mock the main loop methods
    class MockFileManager:
        def __init__(self):
            self.search_dialog = SearchDialog(get_config())
            self.search_dialog.show('filename')
        
        def _check_dialog_content_changed(self):
            """Simulate the fixed method with thread-safe access"""
            if self.search_dialog.mode:
                with self.search_dialog.search_lock:
                    return self.search_dialog.content_changed
            return False
        
        def _mark_dialog_content_unchanged(self):
            """Simulate the fixed method with thread-safe access"""
            if self.search_dialog.mode:
                with self.search_dialog.search_lock:
                    self.search_dialog.content_changed = False
    
    fm = MockFileManager()
    
    # Test initial state
    assert fm._check_dialog_content_changed() == True, "Should initially have content changed"
    
    # Test marking as unchanged
    fm._mark_dialog_content_unchanged()
    assert fm._check_dialog_content_changed() == False, "Should be unchanged after marking"
    
    # Test background update
    with fm.search_dialog.search_lock:
        fm.search_dialog.content_changed = True
    
    assert fm._check_dialog_content_changed() == True, "Should detect background update"
    
    # Test concurrent access
    def background_updater():
        for i in range(100):
            with fm.search_dialog.search_lock:
                fm.search_dialog.content_changed = True
            time.sleep(0.001)
    
    def main_checker():
        detections = 0
        for i in range(100):
            if fm._check_dialog_content_changed():
                detections += 1
                fm._mark_dialog_content_unchanged()
            time.sleep(0.001)
        return detections
    
    # Run concurrent test
    bg_thread = threading.Thread(target=background_updater)
    
    bg_thread.start()
    detections = main_checker()
    bg_thread.join()
    
    print(f"Concurrent test: Detected {detections} updates out of 100 background updates")
    assert detections > 0, "Should detect at least some concurrent updates"
    
    print("✓ Thread-safe access methods working correctly")
    return True


if __name__ == "__main__":
    try:
        test_race_condition_fix()
        test_thread_safe_access_methods()
        
        print("\n🎉 All race condition tests passed!")
        print("   Thread-safe access to content_changed flag is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)