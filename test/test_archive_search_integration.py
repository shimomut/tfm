#!/usr/bin/env python3
"""
Integration tests for archive search with FileManager
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path as PathlibPath

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from tfm_path import Path
from tfm_search_dialog import SearchDialog, SearchDialogHelpers


class MockConfig:
    """Mock configuration for testing"""
    MAX_SEARCH_RESULTS = 1000
    WIDE_CHAR_SUPPORT = False


class MockPaneManager:
    """Mock pane manager for testing"""
    def __init__(self, initial_path):
        self.panes = [
            {
                'path': initial_path,
                'selected_index': 0,
                'scroll_offset': 0,
                'selected_files': set(),
                'files': []
            }
        ]
        self.current_pane_index = 0
    
    def get_current_pane(self):
        return self.panes[self.current_pane_index]


class MockFileOperations:
    """Mock file operations for testing"""
    def refresh_files(self, pane):
        # Simulate refreshing files in pane
        try:
            pane['files'] = list(pane['path'].iterdir())
        except Exception:
            pane['files'] = []


@pytest.fixture
def test_archive_structure(tmp_path):
    """Create a test archive with directory structure"""
    # Create test directory structure
    test_dir = tmp_path / "project"
    test_dir.mkdir()
    
    # Create source files
    src_dir = test_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("def main():\n    print('Hello')")
    (src_dir / "utils.py").write_text("def helper():\n    return True")
    
    # Create docs
    docs_dir = test_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "README.md").write_text("# Project\nDocumentation here")
    (docs_dir / "API.md").write_text("# API Reference\nAPI docs")
    
    # Create tests
    tests_dir = test_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test_main():\n    assert True")
    
    # Create ZIP archive
    zip_path = tmp_path / "project.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file_path in test_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(test_dir)
                zf.write(file_path, arcname)
    
    return zip_path


def test_search_in_archive_root(test_archive_structure):
    """Test searching from archive root"""
    config = MockConfig()
    search_dialog = SearchDialog(config)
    
    # Navigate to archive root
    archive_path = Path(f"archive://{test_archive_structure}")
    
    # Perform search for Python files
    search_dialog.show('filename')
    search_dialog.text_editor.text = "*.py"
    search_dialog._search_worker(archive_path, "*.py", 'filename', is_archive_search=True)
    
    # Should find all Python files
    assert len(search_dialog.results) == 3
    
    # Verify all results are from archive
    for result in search_dialog.results:
        assert result['is_archive'] is True
        assert result['path'].get_scheme() == 'archive'


def test_search_in_archive_subdirectory(test_archive_structure):
    """Test searching from within archive subdirectory"""
    config = MockConfig()
    search_dialog = SearchDialog(config)
    
    # Navigate to src subdirectory in archive
    archive_path = Path(f"archive://{test_archive_structure}#src")
    
    # Perform search for Python files
    search_dialog.show('filename')
    search_dialog.text_editor.text = "*.py"
    search_dialog._search_worker(archive_path, "*.py", 'filename', is_archive_search=True)
    
    # Should only find Python files in src directory
    assert len(search_dialog.results) == 2
    
    # Verify results are from src directory
    for result in search_dialog.results:
        assert result['is_archive'] is True
        # Results should be relative to src directory
        assert 'tests' not in result['relative_path']


def test_navigate_to_search_result_in_archive(test_archive_structure):
    """Test navigation to search result within archive"""
    config = MockConfig()
    search_dialog = SearchDialog(config)
    
    # Set up archive path
    archive_path = Path(f"archive://{test_archive_structure}")
    
    # Perform search
    search_dialog.show('filename')
    search_dialog.text_editor.text = "README.md"
    search_dialog._search_worker(archive_path, "README.md", 'filename', is_archive_search=True)
    
    # Should find README.md
    assert len(search_dialog.results) == 1
    result = search_dialog.results[0]
    
    # Verify result path is correct
    assert result['path'].get_scheme() == 'archive'
    assert 'docs' in str(result['path'])
    assert 'README.md' in str(result['path'])
    
    # Test navigation helper
    pane_manager = MockPaneManager(archive_path)
    file_operations = MockFileOperations()
    messages = []
    
    def mock_print(msg):
        messages.append(msg)
    
    # Navigate to result
    SearchDialogHelpers.navigate_to_result(
        result, pane_manager, file_operations, mock_print
    )
    
    # Verify navigation occurred
    current_pane = pane_manager.get_current_pane()
    assert current_pane['path'].get_scheme() == 'archive'
    assert 'docs' in str(current_pane['path'])


def test_content_search_in_archive(test_archive_structure):
    """Test content search within archive files"""
    config = MockConfig()
    search_dialog = SearchDialog(config)
    
    # Set up archive path
    archive_path = Path(f"archive://{test_archive_structure}")
    
    # Perform content search
    search_dialog.show('content')
    search_dialog.text_editor.text = "def main"
    search_dialog._search_worker(archive_path, "def main", 'content', is_archive_search=True)
    
    # Should find files containing "def main"
    assert len(search_dialog.results) >= 1
    
    # Verify result details
    found_main = False
    for result in search_dialog.results:
        assert result['type'] == 'content'
        assert result['is_archive'] is True
        if 'main.py' in result['relative_path']:
            found_main = True
            assert result['line_num'] == 1
            assert 'def main' in result['match_info']
    
    assert found_main


def test_search_shows_full_archive_path(test_archive_structure):
    """Test that search results show full path within archive"""
    config = MockConfig()
    search_dialog = SearchDialog(config)
    
    # Set up archive path
    archive_path = Path(f"archive://{test_archive_structure}")
    
    # Search for files in nested directory
    search_dialog.show('filename')
    search_dialog.text_editor.text = "test_*.py"
    search_dialog._search_worker(archive_path, "test_*.py", 'filename', is_archive_search=True)
    
    # Should find test file
    assert len(search_dialog.results) == 1
    result = search_dialog.results[0]
    
    # Verify full path is shown
    assert 'tests' in result['relative_path']
    assert 'test_main.py' in result['relative_path']
    
    # Verify absolute path includes archive
    assert result['path'].get_scheme() == 'archive'
    assert str(test_archive_structure) in str(result['path'])


def test_search_multiple_archive_formats(tmp_path):
    """Test search works across different archive formats"""
    import tarfile
    
    config = MockConfig()
    search_dialog = SearchDialog(config)
    
    # Create test content
    test_dir = tmp_path / "content"
    test_dir.mkdir()
    (test_dir / "data.txt").write_text("Test data")
    
    # Test with tar.gz
    tar_path = tmp_path / "test.tar.gz"
    with tarfile.open(tar_path, 'w:gz') as tf:
        for file_path in test_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(test_dir)
                tf.add(file_path, arcname=arcname)
    
    # Search in tar.gz archive
    archive_path = Path(f"archive://{tar_path}")
    search_dialog.show('filename')
    search_dialog.text_editor.text = "*.txt"
    search_dialog._search_worker(archive_path, "*.txt", 'filename', is_archive_search=True)
    
    # Should find the file
    assert len(search_dialog.results) == 1
    assert search_dialog.results[0]['is_archive'] is True


def test_search_cancellation_in_archive(test_archive_structure):
    """Test that search can be cancelled in archives"""
    config = MockConfig()
    search_dialog = SearchDialog(config)
    
    # Set up archive path
    archive_path = Path(f"archive://{test_archive_structure}")
    
    # Start search
    search_dialog.show('filename')
    search_dialog.text_editor.text = "*.py"
    
    # Start search in thread
    import threading
    search_thread = threading.Thread(
        target=search_dialog._search_worker,
        args=(archive_path, "*.py", 'filename'),
        daemon=True
    )
    search_thread.start()
    
    # Cancel immediately
    search_dialog.cancel_search.set()
    
    # Wait for thread to finish
    search_thread.join(timeout=1.0)
    
    # Search should have been cancelled
    assert not search_dialog.searching or search_thread.is_alive() is False
