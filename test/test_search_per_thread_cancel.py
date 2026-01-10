#!/usr/bin/env python3
"""
Test SearchDialog per-thread cancel event fix

Tests that each search thread gets its own cancel event, preventing the race
condition where old threads continue running with a cleared cancel event.

Run with: PYTHONPATH=.:src:ttk python3 test/test_search_per_thread_cancel.py
"""

import threading
import time
from unittest.mock import Mock
from tfm_search_dialog import SearchDialog
from tfm_config import get_config


def test_per_thread_cancel_events():
    """Test that each search thread gets its own cancel event"""
    print("\nTesting per-thread cancel events...")
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Create a mock path
    mock_path = Mock()
    mock_path.name = "test_dir"
    
    def mock_rglob(pattern):
        """Mock rglob that simulates slow iteration"""
        for i in range(100):
            mock_file = Mock()
            mock_file.name = f"file_{i}.txt"
            mock_file.is_dir = Mock(return_value=False)
            mock_file.is_file = Mock(return_value=True)
            mock_file.relative_to = Mock(return_value=Mock(__str__=lambda self: f"file_{i}.txt"))
            yield mock_file
            time.sleep(0.01)  # Simulate slow SFTP
    
    mock_path.rglob = mock_rglob
    
    # Start first search
    search_dialog.show('filename', mock_path)
    search_dialog.perform_search(mock_path)
    search_dialog.text_editor.text = "*.txt"
    search_dialog.perform_search(mock_path)
    
    first_cancel_event = search_dialog.current_cancel_event
    assert first_cancel_event is not None, "First search should have a cancel event"
    
    time.sleep(0.05)
    
    # Start second search (should cancel first)
    search_dialog.text_editor.text = "*.log"
    search_dialog.perform_search(mock_path)
    
    second_cancel_event = search_dialog.current_cancel_event
    assert second_cancel_event is not None, "Second search should have a cancel event"
    
    # Verify they are different events
    assert first_cancel_event is not second_cancel_event, "Each search should have its own cancel event"
    
    # Verify first search's cancel event is set
    assert first_cancel_event.is_set(), "First search's cancel event should be set when cancelled"
    
    # Verify second search's cancel event is NOT set
    assert not second_cancel_event.is_set(), "Second search's cancel event should not be set"
    
    print("✓ Each search has its own cancel event")
    print("✓ First search's cancel event was set when cancelled")
    print("✓ Second search's cancel event remains clear")
    
    # Clean up
    search_dialog._cancel_current_search()
    time.sleep(0.2)


def test_cancel_event_persists_after_timeout():
    """Test that old thread's cancel event remains set even after join timeout"""
    print("\nTesting cancel event persistence after timeout...")
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Track cancel events
    cancel_events_seen = []
    
    # Create a mock path
    mock_path = Mock()
    mock_path.name = "test_dir"
    
    def mock_rglob(pattern):
        """Mock rglob that tracks cancel events and simulates very slow iteration"""
        # Get the cancel event from the current thread's arguments
        import inspect
        frame = inspect.currentframe()
        try:
            # Walk up the stack to find the cancel_event parameter
            while frame:
                if 'cancel_event' in frame.f_locals:
                    cancel_event = frame.f_locals['cancel_event']
                    cancel_events_seen.append(cancel_event)
                    
                    # Simulate very slow iteration (longer than 0.1s timeout)
                    for i in range(50):
                        if cancel_event.is_set():
                            print(f"  Thread cancelled after {i} iterations")
                            return
                        
                        mock_file = Mock()
                        mock_file.name = f"file_{i}.txt"
                        mock_file.is_dir = Mock(return_value=False)
                        mock_file.is_file = Mock(return_value=True)
                        mock_file.relative_to = Mock(return_value=Mock(__str__=lambda self: f"file_{i}.txt"))
                        yield mock_file
                        time.sleep(0.02)  # 50 * 0.02 = 1 second total
                    return
                frame = frame.f_back
        finally:
            del frame
    
    mock_path.rglob = mock_rglob
    
    # Start first search
    search_dialog.show('filename', mock_path)
    search_dialog.text_editor.text = "*.txt"
    search_dialog.perform_search(mock_path)
    
    time.sleep(0.05)  # Let it start
    
    # Start second search (will timeout waiting for first)
    search_dialog.text_editor.text = "*.log"
    search_dialog.perform_search(mock_path)
    
    time.sleep(0.3)  # Wait for first thread to check its cancel event
    
    # Verify first thread's cancel event remained set
    if len(cancel_events_seen) > 0:
        first_event = cancel_events_seen[0]
        assert first_event.is_set(), "First thread's cancel event should still be set after timeout"
        print("✓ First thread's cancel event remained set after join timeout")
    
    # Clean up
    search_dialog._cancel_current_search()
    time.sleep(0.2)


if __name__ == '__main__':
    test_per_thread_cancel_events()
    test_cancel_event_persists_after_timeout()
    print("\n✅ All per-thread cancel event tests passed!")
