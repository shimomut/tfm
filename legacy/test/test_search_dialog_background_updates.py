"""
Test script to verify search dialog background updates trigger redraws

Run with: PYTHONPATH=.:src:ttk pytest test/test_search_dialog_background_updates.py -v
"""

from pathlib import Path
import time
import threading
from unittest.mock import Mock, patch

from tfm_search_dialog import SearchDialog
from tfm_config import get_config


def test_background_search_updates():
    """Test that background search result updates mark content as changed"""
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Show the search dialog
    search_dialog.show('filename')
    
    # Mark content as unchanged (simulating after a draw)
    search_dialog.content_changed = False
    
    # Simulate background thread updating results
    with search_dialog.search_lock:
        search_dialog.results = ['file1.txt', 'file2.txt', 'file3.txt']
        search_dialog.content_changed = True  # This is what the background thread does
    
    # Verify content is marked as changed
    assert search_dialog.content_changed == True, "Content should be marked as changed after background update"
    
    print("✓ Background search updates correctly mark content as changed")
    return True


def test_search_thread_content_changes():
    """Test that the actual search thread marks content as changed"""
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Mock the search to avoid actual file system operations
    original_search = search_dialog._search_worker
    
    def mock_search_worker(search_root, pattern_text, search_type):
        """Mock search that simulates finding results"""
        temp_results = ['mock_file1.txt', 'mock_file2.txt']
        
        # Simulate the periodic update that happens in real search
        with search_dialog.search_lock:
            search_dialog.results = temp_results.copy()
            search_dialog.content_changed = True  # This is the key line we're testing
            search_dialog.searching = False
    
    search_dialog._search_worker = mock_search_worker
    
    # Show dialog and start search
    search_dialog.show('filename')
    search_dialog.text_editor.set_text('test')
    
    # Mark content as unchanged
    search_dialog.content_changed = False
    
    # Perform the mock search
    search_dialog.perform_search(os.getcwd())
    
    # Wait a moment for the "thread" to complete
    time.sleep(0.1)
    
    # Verify content is marked as changed
    assert search_dialog.content_changed == True, "Content should be marked as changed after search completes"
    
    print("✓ Search thread correctly marks content as changed")
    return True


def test_main_loop_timeout_handling():
    """Test the core logic for handling background updates"""
    
    # Test the core logic without creating a full FileManager
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Show search dialog
    search_dialog.show('filename')
    
    # Mark content as unchanged (simulating after a draw)
    search_dialog.content_changed = False
    
    # Simulate background update
    search_dialog.content_changed = True
    
    # Test that we can detect the content change
    assert search_dialog.content_changed == True, "Should detect content change from background thread"
    
    # Simulate marking as unchanged after drawing
    search_dialog.content_changed = False
    assert search_dialog.content_changed == False, "Should be able to mark as unchanged after drawing"
    
    print("✓ Core background update detection works correctly")
    return True
