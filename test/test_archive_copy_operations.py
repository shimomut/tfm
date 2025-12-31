"""
Test archive copy operations - copying files from archive virtual directories

Run with: PYTHONPATH=.:src:ttk pytest test/test_archive_copy_operations.py -v
"""

import tempfile
import zipfile
import tarfile
from pathlib import Path as PathlibPath

from tfm_path import Path
from tfm_file_operations import FileListManager, FileOperationsUI
from tfm_progress_manager import ProgressManager
from tfm_cache_manager import CacheManager


class MockConfig:
    """Mock configuration for testing"""
    SHOW_HIDDEN_FILES = False
    CONFIRM_COPY = False
    CONFIRM_MOVE = False
    CONFIRM_DELETE = False
    MAX_EXTENSION_LENGTH = 5


class MockFileManager:
    """Mock file manager for testing"""
    def __init__(self):
        self.config = MockConfig()
        self.log_manager = None
        self.progress_manager = ProgressManager()
        self.cache_manager = CacheManager()
        self.operation_in_progress = False
        self.operation_cancelled = False
        self.needs_full_redraw = False
        
        # Pane data
        self.left_pane = {
            'path': Path.cwd(),
            'files': [],
            'selected_index': 0,
            'scroll_offset': 0,
            'selected_files': set(),
            'sort_mode': 'name',
            'sort_reverse': False,
            'filter_pattern': ''
        }
        self.right_pane = {
            'path': Path.cwd(),
            'files': [],
            'selected_index': 0,
            'scroll_offset': 0,
            'selected_files': set(),
            'sort_mode': 'name',
            'sort_reverse': False,
            'filter_pattern': ''
        }
        self.active_pane = 'left'
    
    def get_current_pane(self):
        return self.left_pane if self.active_pane == 'left' else self.right_pane
    
    def get_inactive_pane(self):
        return self.right_pane if self.active_pane == 'left' else self.left_pane
    
    def refresh_files(self, pane=None):
        pass


def create_test_zip(zip_path, files):
    """Create a test ZIP archive with specified files"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path, content in files.items():
            zf.writestr(file_path, content)


def create_test_tar(tar_path, files, compression=''):
    """Create a test TAR archive with specified files"""
    mode = 'w'
    if compression == 'gz':
        mode = 'w:gz'
    elif compression == 'bz2':
        mode = 'w:bz2'
    elif compression == 'xz':
        mode = 'w:xz'
    
    with tarfile.open(tar_path, mode) as tf:
        for file_path, content in files.items():
            import io
            data = content.encode('utf-8')
            tarinfo = tarfile.TarInfo(name=file_path)
            tarinfo.size = len(data)
            tf.addfile(tarinfo, io.BytesIO(data))


def test_copy_single_file_from_zip():
    """Test copying a single file from a ZIP archive"""
    print("\n=== Test: Copy single file from ZIP archive ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test ZIP archive
        zip_path = PathlibPath(tmpdir) / 'test.zip'
        test_files = {
            'file1.txt': 'Content of file 1',
            'file2.txt': 'Content of file 2',
            'dir1/file3.txt': 'Content of file 3'
        }
        create_test_zip(zip_path, test_files)
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'dest'
        dest_dir.mkdir()
        
        # Create archive path for file1.txt
        archive_file = Path(f"archive://{zip_path}#file1.txt")
        dest_file = Path(dest_dir / 'file1.txt')
        
        # Verify archive file exists and can be read
        assert archive_file.exists(), "Archive file should exist"
        assert archive_file.is_file(), "Archive file should be a file"
        content = archive_file.read_text()
        assert content == 'Content of file 1', f"Expected 'Content of file 1', got '{content}'"
        
        # Copy the file
        success = archive_file.copy_to(dest_file)
        assert success, "Copy should succeed"
        
        # Verify destination file
        assert dest_file.exists(), "Destination file should exist"
        dest_content = dest_file.read_text()
        assert dest_content == 'Content of file 1', f"Expected 'Content of file 1', got '{dest_content}'"
        
        print("✓ Single file copy from ZIP successful")


def test_copy_directory_from_zip():
    """Test copying a directory from a ZIP archive"""
    print("\n=== Test: Copy directory from ZIP archive ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test ZIP archive with nested structure
        zip_path = PathlibPath(tmpdir) / 'test.zip'
        test_files = {
            'dir1/file1.txt': 'Content 1',
            'dir1/file2.txt': 'Content 2',
            'dir1/subdir/file3.txt': 'Content 3',
            'dir1/subdir/file4.txt': 'Content 4'
        }
        create_test_zip(zip_path, test_files)
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'dest'
        dest_dir.mkdir()
        
        # Create archive path for dir1 (without trailing slash)
        archive_dir = Path(f"archive://{zip_path}#dir1")
        dest_path = Path(dest_dir / 'dir1')
        
        # Verify archive directory exists
        assert archive_dir.exists(), "Archive directory should exist"
        assert archive_dir.is_dir(), "Archive directory should be a directory"
        
        # Copy the directory
        success = archive_dir.copy_to(dest_path)
        assert success, "Copy should succeed"
        
        # Verify all files were copied
        assert (dest_dir / 'dir1' / 'file1.txt').exists(), "file1.txt should exist"
        assert (dest_dir / 'dir1' / 'file2.txt').exists(), "file2.txt should exist"
        assert (dest_dir / 'dir1' / 'subdir' / 'file3.txt').exists(), "file3.txt should exist"
        assert (dest_dir / 'dir1' / 'subdir' / 'file4.txt').exists(), "file4.txt should exist"
        
        # Verify content
        content1 = (dest_dir / 'dir1' / 'file1.txt').read_text()
        assert content1 == 'Content 1', f"Expected 'Content 1', got '{content1}'"
        
        content3 = (dest_dir / 'dir1' / 'subdir' / 'file3.txt').read_text()
        assert content3 == 'Content 3', f"Expected 'Content 3', got '{content3}'"
        
        print("✓ Directory copy from ZIP successful")


def test_copy_from_tar_gz():
    """Test copying files from a TAR.GZ archive"""
    print("\n=== Test: Copy files from TAR.GZ archive ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test TAR.GZ archive
        tar_path = PathlibPath(tmpdir) / 'test.tar.gz'
        test_files = {
            'file1.txt': 'TAR content 1',
            'dir1/file2.txt': 'TAR content 2'
        }
        create_test_tar(tar_path, test_files, compression='gz')
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'dest'
        dest_dir.mkdir()
        
        # Copy file from archive
        archive_file = Path(f"archive://{tar_path}#file1.txt")
        dest_file = Path(dest_dir / 'file1.txt')
        
        success = archive_file.copy_to(dest_file)
        assert success, "Copy should succeed"
        
        # Verify content
        content = dest_file.read_text()
        assert content == 'TAR content 1', f"Expected 'TAR content 1', got '{content}'"
        
        print("✓ File copy from TAR.GZ successful")


def test_copy_with_file_operations():
    """Test copying using FileOperations class"""
    print("\n=== Test: Copy using FileOperations class ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test ZIP archive
        zip_path = PathlibPath(tmpdir) / 'test.zip'
        test_files = {
            'file1.txt': 'Test content',
            'dir1/file2.txt': 'Nested content'
        }
        create_test_zip(zip_path, test_files)
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'dest'
        dest_dir.mkdir()
        
        # Set up file manager and operations
        file_manager = MockFileManager()
        file_ops = FileListManager(file_manager.config)
        file_ops_ui = FileOperationsUI(file_manager, file_ops)
        
        # Set up panes
        file_manager.left_pane['path'] = Path(f"archive://{zip_path}#")
        file_manager.right_pane['path'] = Path(dest_dir)
        
        # Refresh files in left pane (archive)
        file_ops.refresh_files(file_manager.left_pane)
        
        # Verify we can see files in the archive
        assert len(file_manager.left_pane['files']) > 0, "Should see files in archive"
        
        # Select a file to copy
        archive_file = None
        for f in file_manager.left_pane['files']:
            if f.name == 'file1.txt':
                archive_file = f
                break
        
        assert archive_file is not None, "Should find file1.txt in archive"
        
        # Copy the file
        files_to_copy = [archive_file]
        file_ops_ui.copy_files_to_directory(files_to_copy, file_manager.right_pane['path'])
        
        # Wait for background thread to complete
        import time
        max_wait = 5
        waited = 0
        while file_manager.operation_in_progress and waited < max_wait:
            time.sleep(0.1)
            waited += 0.1
        
        # Verify file was copied
        dest_file = dest_dir / 'file1.txt'
        assert dest_file.exists(), "Destination file should exist"
        content = dest_file.read_text()
        assert content == 'Test content', f"Expected 'Test content', got '{content}'"
        
        print("✓ Copy using FileOperations successful")


def test_cross_storage_copy_archive_to_local():
    """Test cross-storage copy from archive to local filesystem"""
    print("\n=== Test: Cross-storage copy (archive to local) ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test archive
        zip_path = PathlibPath(tmpdir) / 'test.zip'
        test_files = {
            'data/file1.txt': 'Data 1',
            'data/file2.txt': 'Data 2',
            'data/subdir/file3.txt': 'Data 3'
        }
        create_test_zip(zip_path, test_files)
        
        # Create destination
        dest_dir = PathlibPath(tmpdir) / 'extracted'
        dest_dir.mkdir()
        
        # Copy entire data directory from archive (without trailing slash)
        archive_dir = Path(f"archive://{zip_path}#data")
        dest_path = Path(dest_dir / 'data')
        
        # Verify source exists
        assert archive_dir.exists(), "Archive directory should exist"
        assert archive_dir.is_dir(), "Should be a directory"
        
        # Perform copy
        success = archive_dir.copy_to(dest_path)
        assert success, "Copy should succeed"
        
        # Verify all files copied
        assert (dest_dir / 'data' / 'file1.txt').exists(), "file1.txt should exist"
        assert (dest_dir / 'data' / 'file2.txt').exists(), "file2.txt should exist"
        assert (dest_dir / 'data' / 'subdir' / 'file3.txt').exists(), "file3.txt should exist"
        
        # Verify content
        content = (dest_dir / 'data' / 'subdir' / 'file3.txt').read_text()
        assert content == 'Data 3', f"Expected 'Data 3', got '{content}'"
        
        print("✓ Cross-storage copy successful")


def run_all_tests():
    """Run all archive copy operation tests"""
    print("=" * 60)
    print("Archive Copy Operations Tests")
    print("=" * 60)
    
    try:
        test_copy_single_file_from_zip()
        test_copy_directory_from_zip()
        test_copy_from_tar_gz()
        test_copy_with_file_operations()
        test_cross_storage_copy_archive_to_local()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
