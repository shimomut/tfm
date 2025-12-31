"""
Integration test for archive copy operations within FileManager

Run with: PYTHONPATH=.:src:ttk pytest test/test_archive_copy_integration.py -v
"""

import os
import tempfile
import zipfile
from pathlib import Path as PathlibPath

from tfm_path import Path
from tfm_file_list_manager import FileListManager
from tfm_file_operation_ui import FileOperationUI
from tfm_progress_manager import ProgressManager
from tfm_cache_manager import CacheManager


class MockConfig:
    """Mock configuration"""
    SHOW_HIDDEN_FILES = False
    CONFIRM_COPY = False
    CONFIRM_MOVE = False
    CONFIRM_DELETE = False
    MAX_EXTENSION_LENGTH = 5


class MockFileManager:
    """Mock file manager"""
    def __init__(self):
        self.config = MockConfig()
        self.log_manager = None
        self.progress_manager = ProgressManager()
        self.cache_manager = CacheManager()
        self.operation_in_progress = False
        self.operation_cancelled = False
        self.needs_full_redraw = False
        
        self.left_pane = {
            'path': Path.cwd(),
            'files': [],
            'focused_index': 0,
            'scroll_offset': 0,
            'selected_files': set(),
            'sort_mode': 'name',
            'sort_reverse': False,
            'filter_pattern': ''
        }
        self.right_pane = {
            'path': Path.cwd(),
            'files': [],
            'focused_index': 0,
            'scroll_offset': 0,
            'selected_files': set(),
            'sort_mode': 'name',
            'sort_reverse': False,
            'filter_pattern': ''
        }
        self.active_pane = 'left'
    
    def mark_dirty(self):
        """Mark the UI as needing a redraw"""
        self.needs_full_redraw = True
    
    def get_current_pane(self):
        return self.left_pane if self.active_pane == 'left' else self.right_pane
    
    def get_inactive_pane(self):
        return self.right_pane if self.active_pane == 'left' else self.left_pane
    
    def refresh_files(self, pane=None):
        if pane:
            self.file_ops.refresh_files(pane)
        else:
            self.file_ops.refresh_files(self.left_pane)
            self.file_ops.refresh_files(self.right_pane)


def test_copy_from_archive_to_local():
    """Test copying files from archive to local filesystem using FileManager"""
    print("\nTesting copy from archive to local filesystem...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test archive
        archive_path = PathlibPath(tmpdir) / 'test.zip'
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr('file1.txt', 'Content 1')
            zf.writestr('file2.txt', 'Content 2')
            zf.writestr('dir1/file3.txt', 'Content 3')
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'dest'
        dest_dir.mkdir()
        
        # Set up file manager
        fm = MockFileManager()
        file_ops = FileListManager(fm.config)
        file_ops_ui = FileOperationUI(fm, file_ops)
        fm.file_ops = file_ops
        
        # Set left pane to archive root
        fm.left_pane['path'] = Path(f"archive://{archive_path}#")
        file_ops.refresh_files(fm.left_pane)
        
        # Set right pane to destination
        fm.right_pane['path'] = Path(dest_dir)
        
        # Find and copy file1.txt
        file1 = None
        for f in fm.left_pane['files']:
            if f.name == 'file1.txt':
                file1 = f
                break
        
        assert file1 is not None, "Should find file1.txt"
        
        # Copy the file
        file_ops_ui.copy_files_to_directory([file1], fm.right_pane['path'])
        
        # Wait for operation to complete
        import time
        max_wait = 5
        waited = 0
        while fm.operation_in_progress and waited < max_wait:
            time.sleep(0.1)
            waited += 0.1
        
        # Verify file was copied
        assert (dest_dir / 'file1.txt').exists(), "file1.txt should be copied"
        content = (dest_dir / 'file1.txt').read_text()
        assert content == 'Content 1', f"Expected 'Content 1', got '{content}'"
        
        print("  ✓ Single file copy successful")


def test_copy_directory_from_archive():
    """Test copying directory from archive using FileManager"""
    print("\nTesting copy directory from archive...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test archive
        archive_path = PathlibPath(tmpdir) / 'test.zip'
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr('dir1/file1.txt', 'Content 1')
            zf.writestr('dir1/file2.txt', 'Content 2')
            zf.writestr('dir1/subdir/file3.txt', 'Content 3')
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'dest'
        dest_dir.mkdir()
        
        # Set up file manager
        fm = MockFileManager()
        file_ops = FileListManager(fm.config)
        file_ops_ui = FileOperationUI(fm, file_ops)
        fm.file_ops = file_ops
        
        # Set left pane to archive root
        fm.left_pane['path'] = Path(f"archive://{archive_path}#")
        file_ops.refresh_files(fm.left_pane)
        
        # Set right pane to destination
        fm.right_pane['path'] = Path(dest_dir)
        
        # Find dir1
        dir1 = None
        for f in fm.left_pane['files']:
            if f.name == 'dir1' and f.is_dir():
                dir1 = f
                break
        
        assert dir1 is not None, "Should find dir1"
        
        # Copy the directory
        file_ops_ui.copy_files_to_directory([dir1], fm.right_pane['path'])
        
        # Wait for operation to complete
        import time
        max_wait = 10
        waited = 0
        while fm.operation_in_progress and waited < max_wait:
            time.sleep(0.2)
            waited += 0.2
        
        # Give a bit more time for filesystem to sync
        time.sleep(0.5)
        
        # Verify directory was copied
        # Debug: list what was actually created
        print(f"  Debug: Contents of {dest_dir}:")
        for item in dest_dir.rglob('*'):
            print(f"    {item.relative_to(dest_dir)}")
        
        assert (dest_dir / 'dir1').exists(), "dir1 should be copied"
        assert (dest_dir / 'dir1' / 'file1.txt').exists(), "file1.txt should exist"
        assert (dest_dir / 'dir1' / 'file2.txt').exists(), "file2.txt should exist"
        assert (dest_dir / 'dir1' / 'subdir' / 'file3.txt').exists(), "file3.txt should exist"
        
        # Verify content
        content = (dest_dir / 'dir1' / 'subdir' / 'file3.txt').read_text()
        assert content == 'Content 3', f"Expected 'Content 3', got '{content}'"
        
        print("  ✓ Directory copy successful")


def test_copy_multiple_files_from_archive():
    """Test copying multiple selected files from archive"""
    print("\nTesting copy multiple files from archive...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test archive
        archive_path = PathlibPath(tmpdir) / 'test.zip'
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr('file1.txt', 'Content 1')
            zf.writestr('file2.txt', 'Content 2')
            zf.writestr('file3.txt', 'Content 3')
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'dest'
        dest_dir.mkdir()
        
        # Set up file manager
        fm = MockFileManager()
        file_ops = FileListManager(fm.config)
        file_ops_ui = FileOperationUI(fm, file_ops)
        fm.file_ops = file_ops
        
        # Set left pane to archive root
        fm.left_pane['path'] = Path(f"archive://{archive_path}#")
        file_ops.refresh_files(fm.left_pane)
        
        # Set right pane to destination
        fm.right_pane['path'] = Path(dest_dir)
        
        # Select multiple files
        files_to_copy = []
        for f in fm.left_pane['files']:
            if f.name in ['file1.txt', 'file3.txt']:
                files_to_copy.append(f)
        
        assert len(files_to_copy) == 2, "Should find 2 files"
        
        # Copy the files
        file_ops_ui.copy_files_to_directory(files_to_copy, fm.right_pane['path'])
        
        # Wait for operation to complete
        import time
        max_wait = 5
        waited = 0
        while fm.operation_in_progress and waited < max_wait:
            time.sleep(0.1)
            waited += 0.1
        
        # Verify files were copied
        assert (dest_dir / 'file1.txt').exists(), "file1.txt should be copied"
        assert (dest_dir / 'file3.txt').exists(), "file3.txt should be copied"
        assert not (dest_dir / 'file2.txt').exists(), "file2.txt should not be copied"
        
        print("  ✓ Multiple file copy successful")


def main():
    """Run all integration tests"""
    print("=" * 60)
    print("Archive Copy Integration Tests")
    print("=" * 60)
    
    try:
        test_copy_from_archive_to_local()
        test_copy_directory_from_archive()
        test_copy_multiple_files_from_archive()
        
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
