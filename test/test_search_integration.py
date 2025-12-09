#!/usr/bin/env python3
"""
Integration test for SearchDialog with main TFM components
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_search_dialog import SearchDialog, SearchDialogHelpers
from tfm_config import DefaultConfig
from tfm_pane_manager import PaneManager
from tfm_file_operations import FileOperations
from tfm_path import Path as TFMPath


class TestConfig(DefaultConfig):
    """Test configuration"""
    MAX_SEARCH_RESULTS = 50


def create_test_structure():
    """Create test directory structure"""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create test files
    (temp_dir / "test.txt").write_text("Test content")
    (temp_dir / "script.py").write_text("def test(): pass")
    
    # Create subdirectory
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.log").write_text("Log entry with test data")
    
    return temp_dir


def test_search_integration():
    """Test SearchDialog integration with other TFM components"""
    print("Testing SearchDialog integration...")
    
    config = TestConfig()
    test_dir = create_test_structure()
    
    try:
        # Initialize components
        search_dialog = SearchDialog(config)
        pane_manager = PaneManager(config, test_dir, test_dir, None)
        file_operations = FileOperations(config)
        
        # Test filename search
        search_dialog.show('filename')
        search_dialog.text_editor.text = "*.txt"
        search_dialog.perform_search(TFMPath(test_dir))
        
        # Wait for search to complete
        import time
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 3:
            time.sleep(0.1)
        
        # Check results
        with search_dialog.search_lock:
            results = search_dialog.results.copy()
        
        assert len(results) > 0, "Should find .txt files"
        
        # Test navigation to result
        if results:
            result = results[0]
            
            # Mock print function
            messages = []
            def mock_print(msg):
                messages.append(msg)
            
            # Test navigation
            SearchDialogHelpers.navigate_to_result(
                result, pane_manager, file_operations, mock_print
            )
            
            # Verify navigation message was printed
            assert len(messages) > 0, "Navigation should produce a message"
            print(f"Navigation message: {messages[0]}")
        
        # Test content search
        search_dialog.show('content')
        search_dialog.text_editor.text = "test"
        search_dialog.perform_search(TFMPath(test_dir))
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 3:
            time.sleep(0.1)
        
        # Check content results
        with search_dialog.search_lock:
            content_results = search_dialog.results.copy()
        
        assert len(content_results) > 0, "Should find content matches"
        
        # Verify content results have proper structure
        for result in content_results:
            if result['type'] == 'content':
                assert 'line_num' in result, "Content results should have line numbers"
                assert 'match_info' in result, "Content results should have match info"
        
        print("✓ SearchDialog integration test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_config_integration():
    """Test configuration integration"""
    print("Testing configuration integration...")
    
    config = TestConfig()
    search_dialog = SearchDialog(config)
    
    # Verify config values are used
    assert search_dialog.max_search_results == config.MAX_SEARCH_RESULTS
    
    print("✓ Configuration integration test passed")


def main():
    """Run integration tests"""
    print("Running SearchDialog integration tests...")
    print("=" * 50)
    
    try:
        test_search_integration()
        test_config_integration()
        
        print("=" * 50)
        print("✓ All integration tests passed!")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()