#!/usr/bin/env python3
"""
Simple tests for archive search functionality
"""

import os
import sys
import tempfile
import zipfile
import tarfile
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_search_dialog import SearchDialog
from tfm_config import DefaultConfig


def create_test_zip(temp_dir, filename, files):
    """Create a test ZIP archive with specified files"""
    zip_path = os.path.join(temp_dir, filename)
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for internal_path, content in files.items():
            zf.writestr(internal_path, content)
    return zip_path


def test_is_archive_path_detection():
    """Test detection of archive paths"""
    print("Testing archive path detection...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        config = DefaultConfig()
        search_dialog = SearchDialog(config)
        
        # Create a test archive
        zip_path = create_test_zip(temp_dir, 'test.zip', {
            'file1.txt': 'content1',
            'dir/file2.txt': 'content2'
        })
        
        # Create archive path
        archive_uri = f"archive://{zip_path}#"
        archive_path = Path(archive_uri)
        
        # Test detection
        assert search_dialog._is_archive_path(archive_path) == True, "Should detect archive path"
        
        # Test regular path
        regular_path = Path(temp_dir)
        assert search_dialog._is_archive_path(regular_path) == False, "Should not detect regular path as archive"
        
        print("✓ Archive path detection works")
        return True
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def test_filename_search_in_archive():
    """Test filename search within an archive"""
    print("Testing filename search in archive...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        config = DefaultConfig()
        search_dialog = SearchDialog(config)
        
        # Create a test archive with multiple files
        zip_path = create_test_zip(temp_dir, 'test.zip', {
            'readme.txt': 'This is a readme',
            'docs/guide.txt': 'This is a guide',
            'docs/tutorial.txt': 'This is a tutorial',
            'src/main.py': 'print("hello")',
            'src/utils.py': 'def helper(): pass'
        })
        
        # Create archive path
        archive_uri = f"archive://{zip_path}#"
        archive_path = Path(archive_uri)
        
        # Show search dialog
        search_dialog.show('filename')
        
        # Set search pattern
        search_dialog.text_editor.text = '*.txt'
        
        # Perform search
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        timeout = 5
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Check results
        assert len(search_dialog.results) == 3, f"Expected 3 results, got {len(search_dialog.results)}"
        
        # Verify all results are marked as archive
        for result in search_dialog.results:
            assert result.get('is_archive') == True, "Result should be marked as archive"
        
        # Verify result paths
        result_names = [r['match_info'] for r in search_dialog.results]
        assert 'readme.txt' in result_names, "Should find readme.txt"
        assert 'guide.txt' in result_names, "Should find guide.txt"
        assert 'tutorial.txt' in result_names, "Should find tutorial.txt"
        
        print("✓ Filename search in archive works")
        return True
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def test_content_search_in_archive():
    """Test content search within an archive"""
    print("Testing content search in archive...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        config = DefaultConfig()
        search_dialog = SearchDialog(config)
        
        # Create a test archive with text files
        zip_path = create_test_zip(temp_dir, 'test.zip', {
            'file1.txt': 'This file contains the word apple',
            'file2.txt': 'This file contains the word banana',
            'file3.txt': 'This file contains the word apple and banana',
            'file4.txt': 'This file has no fruit'
        })
        
        # Create archive path
        archive_uri = f"archive://{zip_path}#"
        archive_path = Path(archive_uri)
        
        # Show search dialog
        search_dialog.show('content')
        
        # Set search pattern
        search_dialog.text_editor.text = 'apple'
        
        # Perform search
        search_dialog.perform_search(archive_path)
        
        # Wait for search to complete
        timeout = 5
        start_time = time.time()
        while search_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Check results - should find file1.txt and file3.txt
        assert len(search_dialog.results) == 2, f"Expected 2 results, got {len(search_dialog.results)}"
        
        # Verify all results are marked as archive
        for result in search_dialog.results:
            assert result.get('is_archive') == True, "Result should be marked as archive"
            assert result['type'] == 'content', "Result type should be content"
        
        # Verify result paths contain the matching files
        result_paths = [r['relative_path'] for r in search_dialog.results]
        assert any('file1.txt' in p for p in result_paths), "Should find file1.txt"
        assert any('file3.txt' in p for p in result_paths), "Should find file3.txt"
        
        print("✓ Content search in archive works")
        return True
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def run_all_tests():
    """Run all tests"""
    tests = [
        test_is_archive_path_detection,
        test_filename_search_in_archive,
        test_content_search_in_archive,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
