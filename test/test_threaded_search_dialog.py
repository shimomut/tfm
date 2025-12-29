"""
Test file for threaded SearchDialog functionality

Run with: PYTHONPATH=.:src:ttk pytest test/test_threaded_search_dialog.py -v
"""

from pathlib import Path
import threading
import time
import tempfile
import shutil

from tfm_search_dialog import SearchDialog
from tfm_config import DefaultConfig


class MockConfig(DefaultConfig):
    """Mock configuration for testing"""
    MAX_SEARCH_RESULTS = 100  # Lower limit for testing


def create_test_directory_structure():
    """Create a temporary directory structure for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create test files and directories
    (temp_dir / "test_file.txt").write_text("This is a test file with some content\nLine 2 with more text")
    (temp_dir / "another_file.py").write_text("def test_function():\n    return 'hello world'")
    (temp_dir / "readme.md").write_text("# Test Project\nThis is a readme file")
    
    # Create subdirectories
    subdir1 = temp_dir / "subdir1"
    subdir1.mkdir()
    (subdir1 / "nested_file.txt").write_text("Nested file content\nWith multiple lines")
    
    subdir2 = temp_dir / "subdir2"
    subdir2.mkdir()
    (subdir2 / "config.json").write_text('{"key": "value", "test": true}')
    
    # Create many files to test result limiting
    for i in range(150):
        (temp_dir / f"file_{i:03d}.txt").write_text(f"File number {i}\nContent for file {i}")
    
    return temp_dir


def test_threaded_filename_search():
    """Test threaded filename search functionality"""
    print("Testing threaded filename search...")
    
    config = MockConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_test_directory_structure()
    
    try:
        # Test basic filename search
        search_dialog.show('filename')
        search_dialog.text_editor.text = "*.txt"
        
        # Start search
        search_dialog.perform_search(test_dir)
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Check results
        with search_dialog.search_lock:
            results = search_dialog.results.copy()
        
        print(f"Found {len(results)} results for '*.txt' pattern")
        assert len(results) > 0, "Should find some .txt files"
        
        # Verify result limit is respected
        assert len(results) <= config.MAX_SEARCH_RESULTS, f"Results should be limited to {config.MAX_SEARCH_RESULTS}"
        
        # Test search cancellation
        search_dialog.text_editor.text = "*"
        search_dialog.perform_search(test_dir)
        
        # Cancel immediately
        search_dialog._cancel_current_search()
        
        # Verify search was cancelled
        assert not search_dialog.searching, "Search should be cancelled"
        
        print("✓ Threaded filename search test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_threaded_content_search():
    """Test threaded content search functionality"""
    print("Testing threaded content search...")
    
    config = MockConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_test_directory_structure()
    
    try:
        # Test content search
        search_dialog.show('content')
        search_dialog.text_editor.text = "test"
        
        # Start search
        search_dialog.perform_search(test_dir)
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Check results
        with search_dialog.search_lock:
            results = search_dialog.results.copy()
        
        print(f"Found {len(results)} content matches for 'test' pattern")
        assert len(results) > 0, "Should find some content matches"
        
        # Verify content results have line numbers
        for result in results:
            if result['type'] == 'content':
                assert 'line_num' in result, "Content results should have line numbers"
                assert 'match_info' in result, "Content results should have match info"
        
        print("✓ Threaded content search test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_search_restart_on_pattern_change():
    """Test that search restarts when pattern changes"""
    print("Testing search restart on pattern change...")
    
    config = MockConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_test_directory_structure()
    
    try:
        search_dialog.show('filename')
        
        # Start first search
        search_dialog.text_editor.text = "*.txt"
        search_dialog.perform_search(test_dir)
        
        # Wait a bit for search to start
        time.sleep(0.1)
        first_thread = search_dialog.search_thread
        
        # Change pattern (should restart search)
        search_dialog.text_editor.text = "*.py"
        search_dialog.perform_search(test_dir)
        
        # Verify new thread was created
        second_thread = search_dialog.search_thread
        assert first_thread != second_thread, "New search thread should be created"
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Check that results match the new pattern
        with search_dialog.search_lock:
            results = search_dialog.results.copy()
        
        for result in results:
            assert result['relative_path'].endswith('.py'), "Results should match new pattern"
        
        print("✓ Search restart test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_thread_safety():
    """Test thread safety of search operations"""
    print("Testing thread safety...")
    
    config = MockConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_test_directory_structure()
    
    try:
        search_dialog.show('filename')
        search_dialog.text_editor.text = "*"
        
        # Start search
        search_dialog.perform_search(test_dir)
        
        # Simulate concurrent access to results
        def access_results():
            for _ in range(100):
                with search_dialog.search_lock:
                    result_count = len(search_dialog.results)
                    if result_count > 0:
                        selected = min(search_dialog.selected, result_count - 1)
                time.sleep(0.001)
        
        # Start multiple threads accessing results
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=access_results)
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 5:
            time.sleep(0.1)
        
        print("✓ Thread safety test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_navigation_during_search():
    """Test navigation while search is running"""
    print("Testing navigation during search...")
    
    config = MockConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_test_directory_structure()
    
    try:
        search_dialog.show('filename')
        search_dialog.text_editor.text = "*"
        
        # Start search
        search_dialog.perform_search(test_dir)
        
        # Wait for some results to appear
        time.sleep(0.2)
        
        # Try navigation while search is running
        with search_dialog.search_lock:
            if search_dialog.results:
                original_selected = search_dialog.selected
                # Move selection down
                if search_dialog.selected < len(search_dialog.results) - 1:
                    search_dialog.selected += 1
                    search_dialog._adjust_scroll()
                
                # Verify selection changed
                assert search_dialog.selected != original_selected or len(search_dialog.results) == 1
        
        print("✓ Navigation during search test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def main():
    """Run all tests"""
    print("Running threaded SearchDialog tests...")
    print("=" * 50)
    
    try:
        test_threaded_filename_search()
        test_threaded_content_search()
        test_search_restart_on_pattern_change()
        test_thread_safety()
        test_navigation_during_search()
        
        print("=" * 50)
        print("✓ All tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
