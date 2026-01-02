"""
Test archive module TTK integration

This test verifies that tfm_archive.py works correctly with TTK renderer
instead of curses stdscr.

Run with: PYTHONPATH=.:src:ttk pytest test/test_archive_ttk_integration.py -v
"""

import tempfile
import zipfile
from pathlib import Path as PathlibPath

from tfm_archive import ArchiveOperations
from tfm_path import Path


def test_archive_operations_initialization():
    """Test that ArchiveOperations can be initialized"""
    print("Testing ArchiveOperations initialization...")
    
    archive_ops = ArchiveOperations()
    
    assert archive_ops is not None
    assert archive_ops.log_manager is None
    assert archive_ops.cache_manager is None
    assert archive_ops.progress_manager is None
    
    print("✓ ArchiveOperations initialized successfully")


def test_archive_format_detection():
    """Test archive format detection"""
    print("Testing archive format detection...")
    
    archive_ops = ArchiveOperations()
    
    # Test various archive formats
    assert archive_ops.get_archive_format('test.zip') is not None
    assert archive_ops.get_archive_format('test.tar.gz') is not None
    assert archive_ops.get_archive_format('test.tgz') is not None
    assert archive_ops.get_archive_format('test.tar.bz2') is not None
    assert archive_ops.get_archive_format('test.tar.xz') is not None
    
    # Test non-archive files
    assert archive_ops.get_archive_format('test.txt') is None
    assert archive_ops.get_archive_format('test.py') is None
    
    print("✓ Archive format detection works correctly")


def test_archive_operations_with_real_archive():
    """Test archive operations with a real archive file"""
    print("Testing archive operations with real archive...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = PathlibPath(tmpdir)
        
        # Create a test zip file
        zip_path = tmpdir_path / 'test.zip'
        with zipfile.ZipFile(str(zip_path), 'w') as zf:
            zf.writestr('file1.txt', 'Content 1')
            zf.writestr('file2.txt', 'Content 2')
            zf.writestr('dir1/file3.txt', 'Content 3')
        
        # Create archive operations
        archive_ops = ArchiveOperations()
        
        # Test is_archive
        assert archive_ops.is_archive(Path(str(zip_path)))
        
        # Test list_archive_contents
        contents = archive_ops.list_archive_contents(Path(str(zip_path)))
        assert len(contents) > 0
        
        # Verify we can see the files
        filenames = [name for name, size, type_ in contents]
        assert 'file1.txt' in filenames
        assert 'file2.txt' in filenames
        
        print("✓ Archive operations work with real archive file")


def test_no_curses_imports():
    """Verify that tfm_archive.py doesn't import curses"""
    print("Testing that tfm_archive.py doesn't import curses...")
    
    import tfm_archive
    
    # Check module's imports
    module_dict = vars(tfm_archive)
    
    # Verify curses is not imported
    assert 'curses' not in module_dict, "tfm_archive should not import curses"
    
    print("✓ tfm_archive.py does not import curses")


def run_all_tests():
    """Run all archive TTK integration tests"""
    print("\n" + "="*60)
    print("Archive TTK Integration Tests")
    print("="*60 + "\n")
    
    tests = [
        test_archive_operations_initialization,
        test_archive_format_detection,
        test_archive_operations_with_real_archive,
        test_no_curses_imports,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0
