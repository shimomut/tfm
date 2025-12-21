#!/usr/bin/env python3
"""
Test archive module TTK integration

This test verifies that tfm_archive.py works correctly with TTK renderer
instead of curses stdscr.
"""

import sys
import os
import tempfile
import zipfile
from pathlib import Path as PathlibPath
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_archive import ArchiveOperations, ArchiveUI
from tfm_path import Path
from tfm_progress_manager import ProgressManager


class MockFileManager:
    """Mock file manager for testing ArchiveUI"""
    
    def __init__(self, renderer):
        self.renderer = renderer
        self.log_manager = None
        self.progress_manager = ProgressManager()
        self.cache_manager = None
        self.config = type('Config', (), {
            'CONFIRM_EXTRACT_ARCHIVE': False
        })()
        self.needs_full_redraw = False
        self.quick_edit_bar = type('Dialog', (), {
            'hide': lambda: None,
            'show_status_line_input': lambda *args, **kwargs: None
        })()
        
        # Mock panes
        self.left_pane = {
            'path': Path(tempfile.gettempdir()),
            'files': [],
            'selected_index': 0,
            'selected_files': []
        }
        self.right_pane = {
            'path': Path(tempfile.gettempdir()),
            'files': [],
            'selected_index': 0,
            'selected_files': []
        }
        self.active_pane = 'left'
    
    def get_current_pane(self):
        return self.left_pane if self.active_pane == 'left' else self.right_pane
    
    def get_inactive_pane(self):
        return self.right_pane if self.active_pane == 'left' else self.left_pane
    
    def draw_status(self):
        """Mock draw_status method"""
        pass
    
    def refresh_files(self, pane):
        """Mock refresh_files method"""
        pass
    
    def adjust_scroll_for_selection(self, pane):
        """Mock adjust_scroll_for_selection method"""
        pass


def test_archive_operations_initialization():
    """Test that ArchiveOperations can be initialized"""
    print("Testing ArchiveOperations initialization...")
    
    archive_ops = ArchiveOperations()
    
    assert archive_ops is not None
    assert archive_ops.log_manager is None
    assert archive_ops.cache_manager is None
    assert archive_ops.progress_manager is None
    
    print("✓ ArchiveOperations initialized successfully")


def test_archive_ui_initialization_with_renderer():
    """Test that ArchiveUI can be initialized with TTK renderer"""
    print("Testing ArchiveUI initialization with TTK renderer...")
    
    # Create mock renderer
    renderer = Mock()
    
    # Create mock file manager with renderer
    file_manager = MockFileManager(renderer)
    
    # Create archive operations
    archive_ops = ArchiveOperations(
        log_manager=file_manager.log_manager,
        cache_manager=file_manager.cache_manager,
        progress_manager=file_manager.progress_manager
    )
    
    # Create archive UI
    archive_ui = ArchiveUI(file_manager, archive_ops)
    
    assert archive_ui is not None
    assert archive_ui.file_manager == file_manager
    assert archive_ui.archive_operations == archive_ops
    
    print("✓ ArchiveUI initialized successfully with TTK renderer")


def test_archive_ui_progress_callback_uses_renderer():
    """Test that progress callback uses renderer.refresh() instead of stdscr.refresh()"""
    print("Testing ArchiveUI progress callback uses renderer...")
    
    # Create mock renderer
    renderer = Mock()
    
    # Create mock file manager with renderer
    file_manager = MockFileManager(renderer)
    
    # Create archive operations and UI
    archive_ops = ArchiveOperations(
        log_manager=file_manager.log_manager,
        cache_manager=file_manager.cache_manager,
        progress_manager=file_manager.progress_manager
    )
    archive_ui = ArchiveUI(file_manager, archive_ops)
    
    # Call progress callback
    archive_ui._progress_callback({})
    
    # Verify renderer.refresh() was called
    renderer.refresh.assert_called_once()
    
    print("✓ Progress callback correctly uses renderer.refresh()")


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
        test_archive_ui_initialization_with_renderer,
        test_archive_ui_progress_callback_uses_renderer,
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


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
