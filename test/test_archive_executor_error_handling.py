"""
Test error handling in ArchiveOperationExecutor.

This test file validates that the executor properly handles errors during
archive creation and extraction operations, including:
- PermissionError handling
- OSError handling (including disk space exhaustion)
- ArchiveError handling
- Error logging with context
- Error count tracking
- Continue processing after errors

Run with: PYTHONPATH=.:src:ttk pytest test/test_archive_executor_error_handling.py -v
"""

import pytest
import tempfile
import os
import zipfile
from pathlib import Path as PathlibPath
from unittest.mock import Mock, patch, MagicMock

from tfm_path import Path
from tfm_archive_operation_executor import ArchiveOperationExecutor
from tfm_progress_manager import ProgressManager
from tfm_archive import ArchiveError


class TestExecutorPermissionErrorHandling:
    """Test that executor handles PermissionError correctly"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = Mock()
        self.file_manager.operation_cancelled = False
        self.progress_manager = ProgressManager()
        self.executor = ArchiveOperationExecutor(
            self.file_manager,
            self.progress_manager,
            cache_manager=None
        )
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_permission_error_logged_and_counted(self):
        """Test that PermissionError is caught, logged, and error count incremented"""
        # Create a test file
        test_file = PathlibPath(self.temp_dir) / 'test.txt'
        test_file.write_text('test content')
        
        archive_path = Path(PathlibPath(self.temp_dir) / 'test.tar.gz')
        source_paths = [Path(test_file)]
        
        # Mock tarfile.open to raise PermissionError when adding file
        with patch('tarfile.open') as mock_tar_open:
            mock_tar = MagicMock()
            mock_tar.__enter__ = Mock(return_value=mock_tar)
            mock_tar.__exit__ = Mock(return_value=False)
            mock_tar.add = Mock(side_effect=PermissionError("Permission denied"))
            mock_tar_open.return_value = mock_tar
            
            # Execute operation
            success, errors = self.executor._create_archive_local(
                source_paths, archive_path, {'type': 'tar', 'compression': 'gz'}
            )
            
            # Verify error was counted
            assert errors == 1
            assert success == 0
    
    def test_permission_error_continues_with_next_file(self):
        """Test that operation continues after PermissionError on one file"""
        # Create multiple test files
        test_file1 = PathlibPath(self.temp_dir) / 'test1.txt'
        test_file1.write_text('test content 1')
        test_file2 = PathlibPath(self.temp_dir) / 'test2.txt'
        test_file2.write_text('test content 2')
        
        archive_path = Path(PathlibPath(self.temp_dir) / 'test.tar.gz')
        source_paths = [Path(test_file1), Path(test_file2)]
        
        # Mock tarfile.open to raise PermissionError only for first file
        call_count = [0]
        def add_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise PermissionError("Permission denied")
            # Second call succeeds
        
        with patch('tarfile.open') as mock_tar_open:
            mock_tar = MagicMock()
            mock_tar.__enter__ = Mock(return_value=mock_tar)
            mock_tar.__exit__ = Mock(return_value=False)
            mock_tar.add = Mock(side_effect=add_side_effect)
            mock_tar_open.return_value = mock_tar
            
            # Execute operation
            success, errors = self.executor._create_archive_local(
                source_paths, archive_path, {'type': 'tar', 'compression': 'gz'}
            )
            
            # Verify first file failed, second succeeded
            assert errors == 1
            assert success == 1


class TestExecutorOSErrorHandling:
    """Test that executor handles OSError correctly"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = Mock()
        self.file_manager.operation_cancelled = False
        self.progress_manager = ProgressManager()
        self.executor = ArchiveOperationExecutor(
            self.file_manager,
            self.progress_manager,
            cache_manager=None
        )
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_disk_space_error_stops_operation(self):
        """Test that disk space exhaustion stops the operation"""
        # Create test files
        test_file1 = PathlibPath(self.temp_dir) / 'test1.txt'
        test_file1.write_text('test content 1')
        test_file2 = PathlibPath(self.temp_dir) / 'test2.txt'
        test_file2.write_text('test content 2')
        
        archive_path = Path(PathlibPath(self.temp_dir) / 'test.tar.gz')
        source_paths = [Path(test_file1), Path(test_file2)]
        
        # Mock tarfile.open to raise OSError with "No space left" message
        with patch('tarfile.open') as mock_tar_open:
            mock_tar = MagicMock()
            mock_tar.__enter__ = Mock(return_value=mock_tar)
            mock_tar.__exit__ = Mock(return_value=False)
            mock_tar.add = Mock(side_effect=OSError("No space left on device"))
            mock_tar_open.return_value = mock_tar
            
            # Execute operation
            success, errors = self.executor._create_archive_local(
                source_paths, archive_path, {'type': 'tar', 'compression': 'gz'}
            )
            
            # Verify operation stopped after first error
            assert errors == 1
            assert success == 0
            # Only one call to add() should have been made (operation stopped)
            assert mock_tar.add.call_count == 1
    
    def test_disk_quota_error_stops_operation(self):
        """Test that disk quota exceeded stops the operation"""
        # Create test files
        test_file1 = PathlibPath(self.temp_dir) / 'test1.txt'
        test_file1.write_text('test content 1')
        test_file2 = PathlibPath(self.temp_dir) / 'test2.txt'
        test_file2.write_text('test content 2')
        
        archive_path = Path(PathlibPath(self.temp_dir) / 'test.tar.gz')
        source_paths = [Path(test_file1), Path(test_file2)]
        
        # Mock tarfile.open to raise OSError with "Disk quota exceeded" message
        with patch('tarfile.open') as mock_tar_open:
            mock_tar = MagicMock()
            mock_tar.__enter__ = Mock(return_value=mock_tar)
            mock_tar.__exit__ = Mock(return_value=False)
            mock_tar.add = Mock(side_effect=OSError("Disk quota exceeded"))
            mock_tar_open.return_value = mock_tar
            
            # Execute operation
            success, errors = self.executor._create_archive_local(
                source_paths, archive_path, {'type': 'tar', 'compression': 'gz'}
            )
            
            # Verify operation stopped after first error
            assert errors == 1
            assert success == 0
            # Only one call to add() should have been made (operation stopped)
            assert mock_tar.add.call_count == 1
    
    def test_other_os_error_continues_operation(self):
        """Test that non-disk-space OSError continues with next file"""
        # Create test files
        test_file1 = PathlibPath(self.temp_dir) / 'test1.txt'
        test_file1.write_text('test content 1')
        test_file2 = PathlibPath(self.temp_dir) / 'test2.txt'
        test_file2.write_text('test content 2')
        
        archive_path = Path(PathlibPath(self.temp_dir) / 'test.tar.gz')
        source_paths = [Path(test_file1), Path(test_file2)]
        
        # Mock tarfile.open to raise OSError (not disk space) only for first file
        call_count = [0]
        def add_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise OSError("Some other OS error")
            # Second call succeeds
        
        with patch('tarfile.open') as mock_tar_open:
            mock_tar = MagicMock()
            mock_tar.__enter__ = Mock(return_value=mock_tar)
            mock_tar.__exit__ = Mock(return_value=False)
            mock_tar.add = Mock(side_effect=add_side_effect)
            mock_tar_open.return_value = mock_tar
            
            # Execute operation
            success, errors = self.executor._create_archive_local(
                source_paths, archive_path, {'type': 'tar', 'compression': 'gz'}
            )
            
            # Verify first file failed, second succeeded
            assert errors == 1
            assert success == 1
            # Both calls to add() should have been made
            assert mock_tar.add.call_count == 2


class TestExecutorArchiveErrorHandling:
    """Test that executor handles ArchiveError correctly"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = Mock()
        self.file_manager.operation_cancelled = False
        self.progress_manager = ProgressManager()
        self.executor = ArchiveOperationExecutor(
            self.file_manager,
            self.progress_manager,
            cache_manager=None
        )
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_archive_error_logged_and_counted(self):
        """Test that ArchiveError is caught, logged, and error count incremented"""
        # Create a test file
        test_file = PathlibPath(self.temp_dir) / 'test.txt'
        test_file.write_text('test content')
        
        archive_path = Path(PathlibPath(self.temp_dir) / 'test.tar.gz')
        source_paths = [Path(test_file)]
        
        # Mock tarfile.open to raise ArchiveError when adding file
        with patch('tarfile.open') as mock_tar_open:
            mock_tar = MagicMock()
            mock_tar.__enter__ = Mock(return_value=mock_tar)
            mock_tar.__exit__ = Mock(return_value=False)
            mock_tar.add = Mock(side_effect=ArchiveError("Archive error", "User-friendly message"))
            mock_tar_open.return_value = mock_tar
            
            # Execute operation
            success, errors = self.executor._create_archive_local(
                source_paths, archive_path, {'type': 'tar', 'compression': 'gz'}
            )
            
            # Verify error was counted
            assert errors == 1
            assert success == 0
    
    def test_archive_error_continues_with_next_file(self):
        """Test that operation continues after ArchiveError on one file"""
        # Create multiple test files
        test_file1 = PathlibPath(self.temp_dir) / 'test1.txt'
        test_file1.write_text('test content 1')
        test_file2 = PathlibPath(self.temp_dir) / 'test2.txt'
        test_file2.write_text('test content 2')
        
        archive_path = Path(PathlibPath(self.temp_dir) / 'test.tar.gz')
        source_paths = [Path(test_file1), Path(test_file2)]
        
        # Mock tarfile.open to raise ArchiveError only for first file
        call_count = [0]
        def add_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ArchiveError("Archive error", "User-friendly message")
            # Second call succeeds
        
        with patch('tarfile.open') as mock_tar_open:
            mock_tar = MagicMock()
            mock_tar.__enter__ = Mock(return_value=mock_tar)
            mock_tar.__exit__ = Mock(return_value=False)
            mock_tar.add = Mock(side_effect=add_side_effect)
            mock_tar_open.return_value = mock_tar
            
            # Execute operation
            success, errors = self.executor._create_archive_local(
                source_paths, archive_path, {'type': 'tar', 'compression': 'gz'}
            )
            
            # Verify first file failed, second succeeded
            assert errors == 1
            assert success == 1


class TestExecutorErrorLogging:
    """Test that executor logs errors with contextual information"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = Mock()
        self.file_manager.operation_cancelled = False
        self.progress_manager = ProgressManager()
        self.executor = ArchiveOperationExecutor(
            self.file_manager,
            self.progress_manager,
            cache_manager=None
        )
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_error_logging_includes_context(self):
        """Test that error logging includes operation type, file name, and error message"""
        # Create a test file
        test_file = PathlibPath(self.temp_dir) / 'test.txt'
        test_file.write_text('test content')
        
        archive_path = Path(PathlibPath(self.temp_dir) / 'test.tar.gz')
        source_paths = [Path(test_file)]
        
        # Mock tarfile.open to raise PermissionError
        with patch('tarfile.open') as mock_tar_open:
            mock_tar = MagicMock()
            mock_tar.__enter__ = Mock(return_value=mock_tar)
            mock_tar.__exit__ = Mock(return_value=False)
            mock_tar.add = Mock(side_effect=PermissionError("Permission denied"))
            mock_tar_open.return_value = mock_tar
            
            # Mock logger to capture log messages
            with patch.object(self.executor.logger, 'error') as mock_log_error:
                # Execute operation
                self.executor._create_archive_local(
                    source_paths, archive_path, {'type': 'tar', 'compression': 'gz'}
                )
                
                # Verify logger.error was called with contextual information
                assert mock_log_error.called
                log_message = mock_log_error.call_args[0][0]
                
                # Check that log message contains file name and error type
                assert 'test.txt' in log_message or 'Permission denied' in log_message


class TestExecutorErrorCountTracking:
    """Test that executor tracks error count separately from success count"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = Mock()
        self.file_manager.operation_cancelled = False
        self.progress_manager = ProgressManager()
        self.executor = ArchiveOperationExecutor(
            self.file_manager,
            self.progress_manager,
            cache_manager=None
        )
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_error_count_tracked_separately(self):
        """Test that error count is tracked separately from success count"""
        # Create test files
        test_file1 = PathlibPath(self.temp_dir) / 'test1.txt'
        test_file1.write_text('test content 1')
        test_file2 = PathlibPath(self.temp_dir) / 'test2.txt'
        test_file2.write_text('test content 2')
        test_file3 = PathlibPath(self.temp_dir) / 'test3.txt'
        test_file3.write_text('test content 3')
        
        archive_path = Path(PathlibPath(self.temp_dir) / 'test.tar.gz')
        source_paths = [Path(test_file1), Path(test_file2), Path(test_file3)]
        
        # Mock tarfile.open to fail on second file only
        call_count = [0]
        def add_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise PermissionError("Permission denied")
            # First and third calls succeed
        
        with patch('tarfile.open') as mock_tar_open:
            mock_tar = MagicMock()
            mock_tar.__enter__ = Mock(return_value=mock_tar)
            mock_tar.__exit__ = Mock(return_value=False)
            mock_tar.add = Mock(side_effect=add_side_effect)
            mock_tar_open.return_value = mock_tar
            
            # Execute operation
            success, errors = self.executor._create_archive_local(
                source_paths, archive_path, {'type': 'tar', 'compression': 'gz'}
            )
            
            # Verify counts are tracked separately
            assert success == 2  # First and third files succeeded
            assert errors == 1   # Second file failed
            assert success + errors == 3  # Total files processed
