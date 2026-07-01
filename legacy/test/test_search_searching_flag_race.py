#!/usr/bin/env python3
"""
Test SearchDialog self.searching flag race condition fix

Tests that old search threads don't overwrite self.searching flag when a new
search has already started.

Run with: PYTHONPATH=.:src:ttk pytest test/test_search_searching_flag_race.py -v
"""

import threading
import time
import pytest
from unittest.mock import Mock
from tfm_search_dialog import SearchDialog
from tfm_config import get_config


def test_searching_flag_not_overwritten_by_old_thread():
    """Test that old threads don't overwrite self.searching when new search starts"""
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Track when threads finish
    thread_finish_times = []
    
    # Create a mock path
    mock_path = Mock()
    mock_path.name = "test_dir"
    
    def mock_rglob(pattern):
        """Mock rglob that simulates slow iteration"""
        # Get the cancel event from the current thread
        import inspect
        frame = inspect.currentframe()
        cancel_event = None
        try:
            while frame:
                if 'cancel_event' in frame.f_locals:
                    cancel_event = frame.f_locals['cancel_event']
                    break
                frame = frame.f_back
        finally:
            del frame
        
        # Simulate slow iteration
        for i in range(20):
            if cancel_event and cancel_event.is_set():
                thread_finish_times.append(('cancelled', time.time()))
                return
            
            mock_file = Mock()
            mock_file.name = f"file_{i}.txt"
            mock_file.is_dir = Mock(return_value=False)
            mock_file.is_file = Mock(return_value=True)
            mock_file.relative_to = Mock(return_value=Mock(__str__=lambda self: f"file_{i}.txt"))
            yield mock_file
            time.sleep(0.02)  # Simulate slow SFTP
        
        thread_finish_times.append(('completed', time.time()))
    
    mock_path.rglob = mock_rglob
    
    # Start first search
    search_dialog.show('filename', mock_path)
    search_dialog.text_editor.text = "*.txt"
    search_dialog.perform_search(mock_path)
    
    # Verify searching is True
    assert search_dialog.search_thread and search_dialog.search_thread.searching, "First search should set searching=True"
    
    time.sleep(0.05)  # Let first search start
    
    # Start second search (should cancel first)
    search_dialog.text_editor.text = "*.log"
    search_dialog.perform_search(mock_path)
    
    # Verify searching is still True (new search is running)
    assert search_dialog.search_thread and search_dialog.search_thread.searching, "Second search should keep searching=True"
    
    # Wait for first thread to finish (it should be cancelled)
    time.sleep(0.3)
    
    # Verify searching is STILL True (second search still running)
    # This is the key test - old thread should NOT have set it to False
    assert search_dialog.search_thread and search_dialog.search_thread.searching, "Old thread should not overwrite searching flag"
    
    # Clean up
    search_dialog._cancel_current_search()
    time.sleep(0.2)
    
    # Verify searching is now False after cancellation
    assert not (search_dialog.search_thread and search_dialog.search_thread.searching), "Searching should be False after cancellation"


def test_searching_flag_set_false_by_current_thread_only():
    """Test that only the current thread can set searching=False"""
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Create a mock path
    mock_path = Mock()
    mock_path.name = "test_dir"
    
    # Track which threads tried to set searching=False
    threads_that_finished = []
    
    def mock_rglob(pattern):
        """Mock rglob that completes quickly"""
        # Get the cancel event from the current thread
        import inspect
        frame = inspect.currentframe()
        cancel_event = None
        try:
            while frame:
                if 'cancel_event' in frame.f_locals:
                    cancel_event = frame.f_locals['cancel_event']
                    break
                frame = frame.f_back
        finally:
            del frame
        
        # Yield a few files
        for i in range(5):
            mock_file = Mock()
            mock_file.name = f"file_{i}.txt"
            mock_file.is_dir = Mock(return_value=False)
            mock_file.is_file = Mock(return_value=True)
            mock_file.relative_to = Mock(return_value=Mock(__str__=lambda self: f"file_{i}.txt"))
            yield mock_file
        
        threads_that_finished.append(cancel_event)
    
    mock_path.rglob = mock_rglob
    
    # Start first search
    search_dialog.show('filename', mock_path)
    search_dialog.text_editor.text = "*.txt"
    search_dialog.perform_search(mock_path)
    
    first_thread = search_dialog.search_thread
    
    time.sleep(0.05)
    
    # Start second search
    search_dialog.text_editor.text = "*.log"
    search_dialog.perform_search(mock_path)
    
    second_thread = search_dialog.search_thread
    
    # Wait for both threads to finish
    time.sleep(0.3)
    
    # Verify both threads finished
    assert len(threads_that_finished) >= 1, "At least one thread should have finished"
    
    # The second thread should be the current one, so searching should be False
    # (assuming it completed)
    if second_thread and not second_thread.is_alive():
        assert not second_thread.searching, "Searching should be False when current thread completes"
    
    # Clean up
    search_dialog._cancel_current_search()


def test_searching_flag_remains_true_during_rapid_searches():
    """Test that searching flag remains True during rapid consecutive searches"""
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Create a mock path
    mock_path = Mock()
    mock_path.name = "test_dir"
    
    def mock_rglob(pattern):
        """Mock rglob that simulates slow iteration"""
        for i in range(50):
            mock_file = Mock()
            mock_file.name = f"file_{i}.txt"
            mock_file.is_dir = Mock(return_value=False)
            mock_file.is_file = Mock(return_value=True)
            mock_file.relative_to = Mock(return_value=Mock(__str__=lambda self: f"file_{i}.txt"))
            yield mock_file
            time.sleep(0.01)
    
    mock_path.rglob = mock_rglob
    
    # Start multiple rapid searches
    search_dialog.show('filename', mock_path)
    
    patterns = ["*.txt", "*.log", "*.py", "*.md"]
    for pattern in patterns:
        search_dialog.text_editor.text = pattern
        search_dialog.perform_search(mock_path)
        time.sleep(0.02)  # Very short delay between searches
        
        # Verify searching remains True
        assert search_dialog.search_thread and search_dialog.search_thread.searching, f"Searching should remain True during rapid searches (pattern: {pattern})"
    
    # Clean up
    search_dialog._cancel_current_search()
    time.sleep(0.2)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
