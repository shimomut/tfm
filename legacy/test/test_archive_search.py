"""
Tests for archive search functionality

Run with: PYTHONPATH=.:src:ttk pytest test/test_archive_search.py -v
"""

import tempfile
import zipfile
import tarfile
from pathlib import Path as PathlibPath

import pytest
from tfm_path import Path
from tfm_search_dialog import SearchDialog


class MockConfig:
    """Mock configuration for testing"""
    MAX_SEARCH_RESULTS = 1000
    WIDE_CHAR_SUPPORT = False


@pytest.fixture
def test_archive_with_files(tmp_path):
    """Create a test archive with various files for searching"""
    # Create test files
    test_dir = tmp_path / "test_content"
    test_dir.mkdir()
    
    # Create files with different content
    (test_dir / "readme.txt").write_text("This is a readme file\nWith multiple lines")
    (test_dir / "config.json").write_text('{"name": "test", "value": 123}')
    (test_dir / "script.py").write_text("def hello():\n    print('Hello World')")
    
    # Create subdirectory with files
    sub_dir = test_dir / "docs"
    sub_dir.mkdir()
    (sub_dir / "guide.md").write_text("# User Guide\nThis is the guide")
    (sub_dir / "notes.txt").write_text("Important notes here")
    
    # Create ZIP archive
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file_path in test_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(test_dir)
                zf.write(file_path, arcname)
    
    return zip_path


@pytest.fixture
def search_dialog():
    """Create a search dialog instance for testing"""
    config = MockConfig()
    return SearchDialog(config)


def test_archive_filename_search(test_archive_with_files, search_dialog):
    """Test filename search within archive"""
    # Create archive path
    archive_path = Path(f"archive://{test_archive_with_files}")
    
    # Perform filename search for "*.txt" pattern
    search_dialog.show('filename')
    search_dialog.text_editor.text = "*.txt"
    
    # Run search synchronously for testing
    search_dialog._search_worker(archive_path, "*.txt", 'filename')
    
    # Verify results
    assert len(search_dialog.results) == 2  # readme.txt and notes.txt
    
    # Check that results have correct type
    for result in search_dialog.results:
        assert result['type'] in ['file', 'dir']
    
    # Verify specific files found
    result_names = [result['match_info'] for result in search_dialog.results]
    assert 'readme.txt' in result_names
    assert 'notes.txt' in result_names


def test_archive_content_search(test_archive_with_files, search_dialog):
    """Test content search within archive files"""
    # Create archive path
    archive_path = Path(f"archive://{test_archive_with_files}")
    
    # Perform content search for "guide" pattern
    search_dialog.show('content')
    search_dialog.text_editor.text = "guide"
    
    # Run search synchronously for testing
    search_dialog._search_worker(archive_path, "guide", 'content')
    
    # Verify results
    assert len(search_dialog.results) >= 1
    
    # Check that results contain the expected file
    found_guide = False
    for result in search_dialog.results:
        assert result['type'] == 'content'
        if 'guide.md' in result['relative_path']:
            found_guide = True
            assert 'line_num' in result
            assert 'match_info' in result
    
    assert found_guide, "Should find 'guide' in guide.md"


def test_archive_search_nested_directories(test_archive_with_files, search_dialog):
    """Test search finds files in nested directories within archive"""
    # Create archive path
    archive_path = Path(f"archive://{test_archive_with_files}")
    
    # Search for files in subdirectory
    search_dialog.show('filename')
    search_dialog.text_editor.text = "*.md"
    
    # Run search synchronously for testing
    search_dialog._search_worker(archive_path, "*.md", 'filename')
    
    # Verify results
    assert len(search_dialog.results) == 1
    result = search_dialog.results[0]
    
    # Check that nested path is shown correctly
    assert 'docs' in result['relative_path']
    assert 'guide.md' in result['relative_path']


def test_archive_search_from_subdirectory(test_archive_with_files, search_dialog):
    """Test search from within archive subdirectory"""
    # Create archive path pointing to subdirectory
    archive_path = Path(f"archive://{test_archive_with_files}#docs")
    
    # Search for files from subdirectory
    search_dialog.show('filename')
    search_dialog.text_editor.text = "*.txt"
    
    # Run search synchronously for testing
    search_dialog._search_worker(archive_path, "*.txt", 'filename')
    
    # Verify results - should only find files in docs subdirectory
    assert len(search_dialog.results) == 1
    result = search_dialog.results[0]
    
    # Should find notes.txt but not readme.txt (which is in parent)
    assert 'notes.txt' in result['match_info']


def test_archive_search_case_insensitive(test_archive_with_files, search_dialog):
    """Test that archive search is case-insensitive"""
    # Create archive path
    archive_path = Path(f"archive://{test_archive_with_files}")
    
    # Search with different case
    search_dialog.show('filename')
    search_dialog.text_editor.text = "README*"
    
    # Run search synchronously for testing
    search_dialog._search_worker(archive_path, "README*", 'filename')
    
    # Should find readme.txt despite case difference
    assert len(search_dialog.results) == 1
    assert 'readme.txt' in search_dialog.results[0]['match_info']


def test_archive_search_no_matches(test_archive_with_files, search_dialog):
    """Test search with pattern that matches nothing"""
    # Create archive path
    archive_path = Path(f"archive://{test_archive_with_files}")
    
    # Search for non-existent pattern
    search_dialog.show('filename')
    search_dialog.text_editor.text = "*.nonexistent"
    
    # Run search synchronously for testing
    search_dialog._search_worker(archive_path, "*.nonexistent", 'filename')
    
    # Should return no results
    assert len(search_dialog.results) == 0


def test_archive_search_result_limit(tmp_path, search_dialog):
    """Test that search respects result limit"""
    # Create archive with many files
    test_dir = tmp_path / "many_files"
    test_dir.mkdir()
    
    # Create more files than the limit
    for i in range(1500):
        (test_dir / f"file_{i:04d}.txt").write_text(f"Content {i}")
    
    # Create ZIP archive
    zip_path = tmp_path / "many.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file_path in test_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(test_dir)
                zf.write(file_path, arcname)
    
    # Create archive path
    archive_path = Path(f"archive://{zip_path}")
    
    # Search for all txt files
    search_dialog.show('filename')
    search_dialog.text_editor.text = "*.txt"
    
    # Run search synchronously for testing
    search_dialog._search_worker(archive_path, "*.txt", 'filename')
    
    # Should respect the limit
    assert len(search_dialog.results) == search_dialog.max_search_results


def test_archive_content_search_multiple_matches(test_archive_with_files, search_dialog):
    """Test content search finds files with matching content"""
    # Create archive path
    archive_path = Path(f"archive://{test_archive_with_files}")
    
    # Search for common word that appears in multiple files
    search_dialog.show('content')
    search_dialog.text_editor.text = "is"
    
    # Run search synchronously for testing
    search_dialog._search_worker(archive_path, "is", 'content')
    
    # Should find multiple files containing "is"
    assert len(search_dialog.results) >= 2
    
    # All results should be content type
    for result in search_dialog.results:
        assert result['type'] == 'content'
        assert 'line_num' in result


def test_archive_search_tar_format(tmp_path, search_dialog):
    """Test search works with tar.gz archives"""
    # Create test files
    test_dir = tmp_path / "tar_content"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("Test content")
    (test_dir / "file2.log").write_text("Log entry")
    
    # Create tar.gz archive
    tar_path = tmp_path / "test.tar.gz"
    with tarfile.open(tar_path, 'w:gz') as tf:
        for file_path in test_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(test_dir)
                tf.add(file_path, arcname=arcname)
    
    # Create archive path
    archive_path = Path(f"archive://{tar_path}")
    
    # Search for txt files
    search_dialog.show('filename')
    search_dialog.text_editor.text = "*.txt"
    
    # Run search synchronously for testing
    search_dialog._search_worker(archive_path, "*.txt", 'filename')
    
    # Should find the txt file
    assert len(search_dialog.results) == 1
    assert 'file1.txt' in search_dialog.results[0]['match_info']
