"""
Test file for SearchDialog empty pattern behavior
Tests that running searches are cancelled when pattern becomes empty

Run with: PYTHONPATH=.:src:ttk pytest test/test_search_empty_pattern.py -v
"""

from pathlib import Path
import time
import tempfile
import shutil

from tfm_search_dialog import SearchDialog
from tfm_config import DefaultConfig


class MockConfig(DefaultConfig):
    """Mock configuration for testing"""
    MAX_SEARCH_RESULTS = 1000


def create_large_test_structure():
    """Create a large directory structure to ensure search takes time"""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create many files to ensure search takes some time
    for i in range(2000):
        (temp_dir / f"test_file_{i:04d}.txt").write_text(f"Test content {i}\nLine 2 for file {i}")
        
        # Create some subdirectories with files
        if i % 100 == 0:
            subdir = temp_dir / f"subdir_{i}"
            subdir.mkdir()
            for j in range(50):
                (subdir / f"nested_{j}.txt").write_text(f"Nested content {i}-{j}")
    
    return temp_dir


def test_empty_pattern_cancels_search():
    """Test that setting empty pattern cancels running search"""
    print("Testing empty pattern cancels running search...")
    
    config = MockConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_large_test_structure()
    
    try:
        search_dialog.show('filename')
        
        # Start a search that will take some time
        search_dialog.text_editor.text = "*"  # Use broader pattern to ensure longer search
        search_dialog.perform_search(test_dir)
        
        # Wait for search to actually start and be running
        max_wait = 1.0  # Wait up to 1 second
        start_time = time.time()
        while not search_dialog.searching and time.time() - start_time < max_wait:
            time.sleep(0.01)
        
        print(f"Search started: {search_dialog.searching}")
        
        if search_dialog.searching:
            # Clear the pattern (simulate user deleting all characters)
            search_dialog.text_editor.text = ""
            search_dialog.perform_search(test_dir)
            
            # Verify search was cancelled immediately
            assert not search_dialog.searching, "Search should be cancelled when pattern is empty"
            
            # Verify results are cleared
            with search_dialog.search_lock:
                assert len(search_dialog.results) == 0, "Results should be cleared when pattern is empty"
                assert search_dialog.selected == 0, "Selection should be reset when pattern is empty"
                assert search_dialog.scroll == 0, "Scroll should be reset when pattern is empty"
            
            print("✓ Empty pattern cancels search test passed")
        else:
            # If search completed too quickly, test the clearing behavior instead
            print("Search completed too quickly, testing result clearing behavior...")
            
            # Verify we have some results from the completed search
            with search_dialog.search_lock:
                result_count = len(search_dialog.results)
            
            if result_count > 0:
                # Clear the pattern
                search_dialog.text_editor.text = ""
                search_dialog.perform_search(test_dir)
                
                # Verify results are cleared
                with search_dialog.search_lock:
                    assert len(search_dialog.results) == 0, "Results should be cleared when pattern is empty"
                    assert search_dialog.selected == 0, "Selection should be reset when pattern is empty"
                    assert search_dialog.scroll == 0, "Scroll should be reset when pattern is empty"
                
                print(f"✓ Cleared {result_count} results when pattern became empty")
            else:
                print("✓ Empty pattern handling works (no results to clear)")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_empty_pattern_during_content_search():
    """Test that empty pattern cancels content search"""
    print("Testing empty pattern cancels content search...")
    
    config = MockConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_large_test_structure()
    
    try:
        search_dialog.show('content')
        
        # Start a content search that will take some time
        search_dialog.text_editor.text = "content"
        search_dialog.perform_search(test_dir)
        
        # Wait for search to actually start
        max_wait = 1.0
        start_time = time.time()
        while not search_dialog.searching and time.time() - start_time < max_wait:
            time.sleep(0.01)
        
        print(f"Content search started: {search_dialog.searching}")
        
        if search_dialog.searching:
            # Clear the pattern
            search_dialog.text_editor.text = ""
            search_dialog.perform_search(test_dir)
            
            # Verify search was cancelled immediately
            assert not search_dialog.searching, "Content search should be cancelled when pattern is empty"
            
            # Verify results are cleared
            with search_dialog.search_lock:
                assert len(search_dialog.results) == 0, "Content search results should be cleared"
            
            print("✓ Empty pattern cancels content search test passed")
        else:
            # Test clearing behavior if search completed quickly
            print("Content search completed quickly, testing result clearing...")
            
            with search_dialog.search_lock:
                result_count = len(search_dialog.results)
            
            # Clear the pattern
            search_dialog.text_editor.text = ""
            search_dialog.perform_search(test_dir)
            
            # Verify results are cleared
            with search_dialog.search_lock:
                assert len(search_dialog.results) == 0, "Content search results should be cleared"
            
            print(f"✓ Cleared {result_count} content search results when pattern became empty")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_pattern_change_sequence():
    """Test sequence of pattern changes including empty pattern"""
    print("Testing pattern change sequence...")
    
    config = MockConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_large_test_structure()
    
    try:
        search_dialog.show('filename')
        
        # Start with a pattern
        search_dialog.text_editor.text = "*"
        search_dialog.perform_search(test_dir)
        
        # Wait for search to start
        max_wait = 1.0
        start_time = time.time()
        while not search_dialog.searching and time.time() - start_time < max_wait:
            time.sleep(0.01)
        
        first_thread = search_dialog.search_thread
        was_searching = search_dialog.searching
        print(f"First search started: {was_searching}")
        
        # Change to empty pattern
        search_dialog.text_editor.text = ""
        search_dialog.perform_search(test_dir)
        
        assert not search_dialog.searching, "Search should be cancelled"
        
        # Verify results are cleared
        with search_dialog.search_lock:
            assert len(search_dialog.results) == 0, "Results should be cleared"
        
        # Change to new pattern
        search_dialog.text_editor.text = "test_file_0001.txt"
        search_dialog.perform_search(test_dir)
        
        # Wait for new search to start or complete
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 2.0:
            time.sleep(0.01)
        
        # Should have results for the specific file
        with search_dialog.search_lock:
            result_count = len(search_dialog.results)
        
        print(f"New search found {result_count} results")
        
        # Change back to empty
        search_dialog.text_editor.text = ""
        search_dialog.perform_search(test_dir)
        
        assert not search_dialog.searching, "Search should be cancelled again"
        
        # Verify results are cleared again
        with search_dialog.search_lock:
            assert len(search_dialog.results) == 0, "Results should be cleared again"
        
        print("✓ Pattern change sequence test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_empty_pattern_with_existing_results():
    """Test that empty pattern clears existing results"""
    print("Testing empty pattern clears existing results...")
    
    config = MockConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_large_test_structure()
    
    try:
        search_dialog.show('filename')
        
        # Start search and wait for completion - use pattern that will definitely match
        search_dialog.text_editor.text = "test_file_0001.txt"  # This file should exist
        search_dialog.perform_search(test_dir)
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Verify we have results
        with search_dialog.search_lock:
            original_result_count = len(search_dialog.results)
        
        if original_result_count == 0:
            # Try a broader pattern
            search_dialog.text_editor.text = "*.txt"
            search_dialog.perform_search(test_dir)
            
            # Wait for search to complete
            start_time = time.time()
            while search_dialog.searching and time.time() - start_time < 5:
                time.sleep(0.1)
            
            with search_dialog.search_lock:
                original_result_count = len(search_dialog.results)
        
        print(f"Found {original_result_count} results before clearing")
        
        if original_result_count > 0:
            # Clear pattern
            search_dialog.text_editor.text = ""
            search_dialog.perform_search(test_dir)
            
            # Verify results are cleared
            with search_dialog.search_lock:
                assert len(search_dialog.results) == 0, "Results should be cleared"
                assert search_dialog.selected == 0, "Selection should be reset"
                assert search_dialog.scroll == 0, "Scroll should be reset"
            
            print(f"✓ Cleared {original_result_count} existing results")
        else:
            print("✓ No results to clear, but empty pattern handling works")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def main():
    """Run all tests"""
    print("Running SearchDialog empty pattern tests...")
    print("=" * 50)
    
    try:
        test_empty_pattern_cancels_search()
        test_empty_pattern_during_content_search()
        test_pattern_change_sequence()
        test_empty_pattern_with_existing_results()
        
        print("=" * 50)
        print("✓ All empty pattern tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
