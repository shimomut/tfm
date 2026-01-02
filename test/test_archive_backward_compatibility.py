"""
Tests for Task 12: Archive Operations Backward Compatibility

This test suite verifies that the ArchiveOperations class maintains backward
compatibility while delegating to the new task-based system.

Requirements tested:
- 12.1: ArchiveOperations maintains existing public API
- 12.2: create_archive returns boolean indicating success
- 12.3: extract_archive returns boolean indicating success
- 12.4: Migration doesn't break existing callers
- 12.5: Gradual transition from synchronous to asynchronous usage
"""

import pytest
import tempfile
import tarfile
import zipfile
from pathlib import Path as PathlibPath
from unittest.mock import Mock, MagicMock, patch, call

# Add src to path for imports
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'ttk')

from tfm_path import Path
from tfm_archive import ArchiveOperations


class TestBackwardCompatibilityAPI:
    """Test that public API is maintained (Requirement 12.1)"""
    
    def test_create_archive_method_exists(self):
        """Verify create_archive method exists with expected signature"""
        archive_ops = ArchiveOperations()
        
        # Method should exist
        assert hasattr(archive_ops, 'create_archive')
        
        # Check method signature includes use_task parameter
        import inspect
        sig = inspect.signature(archive_ops.create_archive)
        assert 'source_paths' in sig.parameters
        assert 'archive_path' in sig.parameters
        assert 'format_type' in sig.parameters
        assert 'use_task' in sig.parameters
        
        # use_task should default to True
        assert sig.parameters['use_task'].default is True
    
    def test_extract_archive_method_exists(self):
        """Verify extract_archive method exists with expected signature"""
        archive_ops = ArchiveOperations()
        
        # Method should exist
        assert hasattr(archive_ops, 'extract_archive')
        
        # Check method signature includes use_task parameter
        import inspect
        sig = inspect.signature(archive_ops.extract_archive)
        assert 'archive_path' in sig.parameters
        assert 'destination_dir' in sig.parameters
        assert 'overwrite' in sig.parameters
        assert 'use_task' in sig.parameters
        
        # use_task should default to True
        assert sig.parameters['use_task'].default is True


class TestBooleanReturnValues:
    """Test that methods return boolean values (Requirements 12.2, 12.3)"""
    
    def test_create_archive_returns_boolean_with_task(self, tmp_path):
        """Verify create_archive returns boolean when using task (Requirement 12.2)"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Create mock file_manager
        mock_file_manager = Mock()
        mock_file_manager.operation_in_progress = False
        mock_file_manager.operation_cancelled = False
        
        # Create mock progress_manager with file_manager
        mock_progress_manager = Mock()
        mock_progress_manager.file_manager = mock_file_manager
        
        archive_ops = ArchiveOperations(progress_manager=mock_progress_manager)
        
        # Call with use_task=True
        source_paths = [Path(test_file)]
        archive_path = Path(tmp_path / "test.tar.gz")
        
        result = archive_ops.create_archive(source_paths, archive_path, use_task=True)
        
        # Should return boolean
        assert isinstance(result, bool)
        # Should return True to indicate task was started
        assert result is True
    
    def test_create_archive_returns_boolean_without_task(self, tmp_path):
        """Verify create_archive returns boolean when not using task (Requirement 12.2)"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        archive_ops = ArchiveOperations()
        
        # Call with use_task=False
        source_paths = [Path(test_file)]
        archive_path = Path(tmp_path / "test.tar.gz")
        
        result = archive_ops.create_archive(source_paths, archive_path, use_task=False)
        
        # Should return boolean
        assert isinstance(result, bool)
        # Should return True for successful creation
        assert result is True
        # Archive should exist
        assert archive_path.exists()
    
    def test_extract_archive_returns_boolean_with_task(self, tmp_path):
        """Verify extract_archive returns boolean when using task (Requirement 12.3)"""
        # Create test archive
        archive_path = tmp_path / "test.tar.gz"
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")
            tar.add(str(test_file), arcname="test.txt")
        
        # Create mock file_manager
        mock_file_manager = Mock()
        mock_file_manager.operation_in_progress = False
        mock_file_manager.operation_cancelled = False
        
        # Create mock progress_manager with file_manager
        mock_progress_manager = Mock()
        mock_progress_manager.file_manager = mock_file_manager
        
        archive_ops = ArchiveOperations(progress_manager=mock_progress_manager)
        
        # Call with use_task=True
        extract_dir = Path(tmp_path / "extracted")
        
        result = archive_ops.extract_archive(Path(archive_path), extract_dir, use_task=True)
        
        # Should return boolean
        assert isinstance(result, bool)
        # Should return True to indicate task was started
        assert result is True
    
    def test_extract_archive_returns_boolean_without_task(self, tmp_path):
        """Verify extract_archive returns boolean when not using task (Requirement 12.3)"""
        # Create test archive
        archive_path = tmp_path / "test.tar.gz"
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")
            tar.add(str(test_file), arcname="test.txt")
        
        archive_ops = ArchiveOperations()
        
        # Call with use_task=False
        extract_dir = Path(tmp_path / "extracted")
        
        result = archive_ops.extract_archive(Path(archive_path), extract_dir, use_task=False)
        
        # Should return boolean
        assert isinstance(result, bool)
        # Should return True for successful extraction
        assert result is True
        # Extracted file should exist
        assert (extract_dir / "test.txt").exists()


class TestExistingCallersCompatibility:
    """Test that existing callers continue to work (Requirement 12.4)"""
    
    def test_create_archive_without_use_task_parameter(self, tmp_path):
        """Verify create_archive works when called without use_task parameter"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Create mock file_manager
        mock_file_manager = Mock()
        mock_file_manager.operation_in_progress = False
        mock_file_manager.operation_cancelled = False
        
        # Create mock progress_manager with file_manager
        mock_progress_manager = Mock()
        mock_progress_manager.file_manager = mock_file_manager
        
        archive_ops = ArchiveOperations(progress_manager=mock_progress_manager)
        
        # Call without use_task parameter (should default to True)
        source_paths = [Path(test_file)]
        archive_path = Path(tmp_path / "test.tar.gz")
        
        result = archive_ops.create_archive(source_paths, archive_path)
        
        # Should work and return boolean
        assert isinstance(result, bool)
        assert result is True
    
    def test_extract_archive_without_use_task_parameter(self, tmp_path):
        """Verify extract_archive works when called without use_task parameter"""
        # Create test archive
        archive_path = tmp_path / "test.tar.gz"
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")
            tar.add(str(test_file), arcname="test.txt")
        
        # Create mock file_manager
        mock_file_manager = Mock()
        mock_file_manager.operation_in_progress = False
        mock_file_manager.operation_cancelled = False
        
        # Create mock progress_manager with file_manager
        mock_progress_manager = Mock()
        mock_progress_manager.file_manager = mock_file_manager
        
        archive_ops = ArchiveOperations(progress_manager=mock_progress_manager)
        
        # Call without use_task parameter (should default to True)
        extract_dir = Path(tmp_path / "extracted")
        
        result = archive_ops.extract_archive(Path(archive_path), extract_dir)
        
        # Should work and return boolean
        assert isinstance(result, bool)
        assert result is True
    
    def test_legacy_synchronous_usage_still_works(self, tmp_path):
        """Verify legacy synchronous usage pattern still works"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        archive_ops = ArchiveOperations()
        
        # Legacy usage: create archive synchronously
        source_paths = [Path(test_file)]
        archive_path = Path(tmp_path / "test.tar.gz")
        
        success = archive_ops.create_archive(source_paths, archive_path, use_task=False)
        assert success is True
        assert archive_path.exists()
        
        # Legacy usage: extract archive synchronously
        extract_dir = Path(tmp_path / "extracted")
        
        success = archive_ops.extract_archive(Path(archive_path), extract_dir, use_task=False)
        assert success is True
        assert (extract_dir / "test.txt").exists()


class TestGradualTransition:
    """Test gradual transition from synchronous to asynchronous (Requirement 12.5)"""
    
    def test_can_use_synchronous_mode_explicitly(self, tmp_path):
        """Verify synchronous mode can be explicitly requested"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        archive_ops = ArchiveOperations()
        
        # Explicitly request synchronous mode
        source_paths = [Path(test_file)]
        archive_path = Path(tmp_path / "test.tar.gz")
        
        result = archive_ops.create_archive(source_paths, archive_path, use_task=False)
        
        # Should complete synchronously
        assert result is True
        assert archive_path.exists()
    
    def test_can_use_asynchronous_mode_explicitly(self, tmp_path):
        """Verify asynchronous mode can be explicitly requested"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Create mock file_manager
        mock_file_manager = Mock()
        mock_file_manager.operation_in_progress = False
        mock_file_manager.operation_cancelled = False
        
        # Create mock progress_manager with file_manager
        mock_progress_manager = Mock()
        mock_progress_manager.file_manager = mock_file_manager
        
        archive_ops = ArchiveOperations(progress_manager=mock_progress_manager)
        
        # Explicitly request asynchronous mode
        source_paths = [Path(test_file)]
        archive_path = Path(tmp_path / "test.tar.gz")
        
        result = archive_ops.create_archive(source_paths, archive_path, use_task=True)
        
        # Should return True to indicate task started
        assert result is True
    
    def test_fallback_to_synchronous_when_no_file_manager(self, tmp_path):
        """Verify fallback to synchronous mode when file_manager not available"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Create archive_ops without file_manager
        archive_ops = ArchiveOperations()
        
        # Request asynchronous mode but no file_manager available
        source_paths = [Path(test_file)]
        archive_path = Path(tmp_path / "test.tar.gz")
        
        result = archive_ops.create_archive(source_paths, archive_path, use_task=True)
        
        # Should fallback to synchronous and complete successfully
        assert result is True
        assert archive_path.exists()


class TestTaskDelegation:
    """Test that task delegation works correctly"""
    
    def test_create_archive_delegates_to_task(self, tmp_path):
        """Verify create_archive delegates to ArchiveOperationTask"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Create mock file_manager
        mock_file_manager = Mock()
        mock_file_manager.operation_in_progress = False
        mock_file_manager.operation_cancelled = False
        
        # Create mock progress_manager with file_manager
        mock_progress_manager = Mock()
        mock_progress_manager.file_manager = mock_file_manager
        
        archive_ops = ArchiveOperations(progress_manager=mock_progress_manager)
        
        # Initialize task components first
        archive_ops._initialize_task_components(mock_file_manager)
        
        # Mock the task's start_operation method
        mock_start = Mock()
        archive_ops._task.start_operation = mock_start
        
        # Call create_archive with use_task=True
        source_paths = [Path(test_file)]
        archive_path = Path(tmp_path / "test.tar.gz")
        
        result = archive_ops.create_archive(source_paths, archive_path, use_task=True)
        
        # Should delegate to task
        mock_start.assert_called_once()
        call_args = mock_start.call_args
        assert call_args[0][0] == 'create'
        assert call_args[0][1] == source_paths
        assert call_args[0][2] == archive_path
        assert call_args[0][3] == 'tar.gz'
    
    def test_extract_archive_delegates_to_task(self, tmp_path):
        """Verify extract_archive delegates to ArchiveOperationTask"""
        # Create test archive
        archive_path = tmp_path / "test.tar.gz"
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")
            tar.add(str(test_file), arcname="test.txt")
        
        # Create mock file_manager
        mock_file_manager = Mock()
        mock_file_manager.operation_in_progress = False
        mock_file_manager.operation_cancelled = False
        
        # Create mock progress_manager with file_manager
        mock_progress_manager = Mock()
        mock_progress_manager.file_manager = mock_file_manager
        
        archive_ops = ArchiveOperations(progress_manager=mock_progress_manager)
        
        # Initialize task components first
        archive_ops._initialize_task_components(mock_file_manager)
        
        # Mock the task's start_operation method and context
        mock_start = Mock()
        archive_ops._task.start_operation = mock_start
        mock_context = Mock()
        mock_context.options = {}
        archive_ops._task.context = mock_context
        
        # Call extract_archive with use_task=True
        extract_dir = Path(tmp_path / "extracted")
        
        result = archive_ops.extract_archive(Path(archive_path), extract_dir, use_task=True)
        
        # Should delegate to task
        mock_start.assert_called_once()
        call_args = mock_start.call_args
        assert call_args[0][0] == 'extract'
        assert call_args[0][1] == [Path(archive_path)]
        assert call_args[0][2] == extract_dir
    
    def test_extract_archive_with_overwrite_parameter(self, tmp_path):
        """Verify extract_archive accepts overwrite parameter for backward compatibility"""
        # Create test archive
        archive_path = tmp_path / "test.tar.gz"
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")
            tar.add(str(test_file), arcname="test.txt")
        
        # Create mock file_manager
        mock_file_manager = Mock()
        mock_file_manager.operation_in_progress = False
        mock_file_manager.operation_cancelled = False
        
        # Create mock progress_manager with file_manager
        mock_progress_manager = Mock()
        mock_progress_manager.file_manager = mock_file_manager
        
        archive_ops = ArchiveOperations(progress_manager=mock_progress_manager)
        
        # Call extract_archive with overwrite=True - should not raise an error
        extract_dir = Path(tmp_path / "extracted")
        
        result = archive_ops.extract_archive(Path(archive_path), extract_dir, 
                                            overwrite=True, use_task=True)
        
        # Should return True to indicate task was started
        assert result is True
        
        # Call with overwrite=False - should also work
        result2 = archive_ops.extract_archive(Path(archive_path), extract_dir, 
                                             overwrite=False, use_task=True)
        assert result2 is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
