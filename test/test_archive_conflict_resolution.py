#!/usr/bin/env python3
"""
Tests for archive operation conflict resolution.

This module tests the conflict resolution functionality for archive operations,
including overwrite, skip, and apply-to-all options.
"""

import tempfile
import tarfile
import zipfile
from pathlib import Path as PathlibPath
from unittest.mock import Mock, MagicMock, patch

import pytest

from tfm_path import Path
from tfm_archive_operation_task import ArchiveOperationTask, State, ArchiveOperationContext
from tfm_archive_operation_executor import ArchiveOperationExecutor
from tfm_archive_operation_ui import ArchiveOperationUI
from tfm_progress_manager import ProgressManager


class TestConflictResolution:
    """Test conflict resolution for archive operations"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield PathlibPath(tmpdir)
    
    @pytest.fixture
    def mock_file_manager(self):
        """Create mock file manager"""
        fm = Mock()
        fm.operation_in_progress = False
        fm.operation_cancelled = False
        fm.config = Mock()
        fm.config.CONFIRM_ARCHIVE_CREATE = False
        fm.config.CONFIRM_ARCHIVE_EXTRACT = False
        return fm
    
    @pytest.fixture
    def mock_progress_manager(self):
        """Create mock progress manager"""
        pm = Mock(spec=ProgressManager)
        pm.start_operation = Mock()
        pm.update_progress = Mock()
        pm.increment_errors = Mock()
        pm.finish_operation = Mock()
        return pm
    
    @pytest.fixture
    def executor(self, mock_file_manager, mock_progress_manager):
        """Create executor instance"""
        return ArchiveOperationExecutor(mock_file_manager, mock_progress_manager)
    
    @pytest.fixture
    def ui(self, mock_file_manager):
        """Create UI instance"""
        return ArchiveOperationUI(mock_file_manager)
    
    @pytest.fixture
    def task(self, mock_file_manager, ui, executor):
        """Create task instance"""
        return ArchiveOperationTask(mock_file_manager, ui, executor)
    
    def test_overwrite_choice_proceeds_to_execution(self, task, temp_dir):
        """Test that overwrite choice proceeds to execution"""
        # Create a conflict scenario
        archive_path = Path(temp_dir / "test.tar.gz")
        archive_path.touch()  # Create existing archive
        
        source_files = [Path(temp_dir / "file1.txt")]
        source_files[0].touch()
        
        # Start operation (should detect conflict)
        task.start_operation('create', source_files, archive_path, 'tar.gz')
        
        # Verify we're in RESOLVING_CONFLICT state
        assert task.state == State.RESOLVING_CONFLICT
        assert len(task.context.conflicts) == 1
        
        # Resolve conflict with overwrite
        task.on_conflict_resolved('overwrite', apply_to_all=False)
        
        # Verify we transitioned to EXECUTING state
        assert task.state == State.EXECUTING
        
        # Verify the file was marked for overwrite
        assert archive_path in task.context.results['success']
    
    def test_skip_choice_marks_file_as_skipped(self, task, temp_dir):
        """Test that skip choice marks file as skipped"""
        # Create archive with files
        archive_path = Path(temp_dir / "test.tar.gz")
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            file1 = temp_dir / "file1.txt"
            file1.write_text("content1")
            tar.add(str(file1), arcname="file1.txt")
            
            file2 = temp_dir / "file2.txt"
            file2.write_text("content2")
            tar.add(str(file2), arcname="file2.txt")
        
        # Create destination with existing file
        dest_dir = Path(temp_dir / "extract")
        dest_dir.mkdir()
        existing_file = dest_dir / "file1.txt"
        existing_file.write_text("existing")
        
        # Start extraction (should detect conflict)
        task.start_operation('extract', [archive_path], dest_dir, 'tar.gz')
        
        # Verify we're in RESOLVING_CONFLICT state
        assert task.state == State.RESOLVING_CONFLICT
        assert len(task.context.conflicts) == 1
        
        # Resolve conflict with skip
        task.on_conflict_resolved('skip', apply_to_all=False)
        
        # Verify the file was marked as skipped
        assert existing_file in task.context.results['skipped']
    
    def test_overwrite_all_applies_to_remaining_conflicts(self, task, temp_dir):
        """Test that overwrite with apply_to_all sets overwrite_all flag"""
        # Create archive with multiple files
        archive_path = Path(temp_dir / "test.tar.gz")
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            for i in range(3):
                file = temp_dir / f"file{i}.txt"
                file.write_text(f"content{i}")
                tar.add(str(file), arcname=f"file{i}.txt")
        
        # Create destination with existing files
        dest_dir = Path(temp_dir / "extract")
        dest_dir.mkdir()
        for i in range(3):
            existing = dest_dir / f"file{i}.txt"
            existing.write_text(f"existing{i}")
        
        # Start extraction (should detect conflicts)
        task.start_operation('extract', [archive_path], dest_dir, 'tar.gz')
        
        # Verify we're in RESOLVING_CONFLICT state
        assert task.state == State.RESOLVING_CONFLICT
        assert len(task.context.conflicts) == 3
        
        # Resolve first conflict with overwrite_all
        task.on_conflict_resolved('overwrite', apply_to_all=True)
        
        # Verify overwrite_all flag is set
        assert task.context.options['overwrite_all'] is True
        
        # Verify we moved to next conflict (or execution if auto-applied)
        assert task.context.current_conflict_index >= 1
    
    def test_skip_all_applies_to_remaining_conflicts(self, task, temp_dir):
        """Test that skip with apply_to_all sets skip_all flag"""
        # Create archive with multiple files
        archive_path = Path(temp_dir / "test.tar.gz")
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            for i in range(3):
                file = temp_dir / f"file{i}.txt"
                file.write_text(f"content{i}")
                tar.add(str(file), arcname=f"file{i}.txt")
        
        # Create destination with existing files
        dest_dir = Path(temp_dir / "extract")
        dest_dir.mkdir()
        for i in range(3):
            existing = dest_dir / f"file{i}.txt"
            existing.write_text(f"existing{i}")
        
        # Start extraction (should detect conflicts)
        task.start_operation('extract', [archive_path], dest_dir, 'tar.gz')
        
        # Verify we're in RESOLVING_CONFLICT state
        assert task.state == State.RESOLVING_CONFLICT
        assert len(task.context.conflicts) == 3
        
        # Resolve first conflict with skip_all
        task.on_conflict_resolved('skip', apply_to_all=True)
        
        # Verify skip_all flag is set
        assert task.context.options['skip_all'] is True
        
        # Verify we moved to next conflict (or execution if auto-applied)
        assert task.context.current_conflict_index >= 1
    
    def test_esc_key_cancels_operation(self, task, temp_dir):
        """Test that ESC key (None choice) cancels operation"""
        # Create a conflict scenario
        archive_path = Path(temp_dir / "test.tar.gz")
        archive_path.touch()
        
        source_files = [Path(temp_dir / "file1.txt")]
        source_files[0].touch()
        
        # Start operation (should detect conflict)
        task.start_operation('create', source_files, archive_path, 'tar.gz')
        
        # Verify we're in RESOLVING_CONFLICT state
        assert task.state == State.RESOLVING_CONFLICT
        
        # Cancel with ESC (None choice)
        task.on_conflict_resolved(None, apply_to_all=False)
        
        # Verify we transitioned to IDLE state
        assert task.state == State.IDLE
        assert task.context is None
    
    def test_executor_respects_skip_files_list(self, executor, temp_dir, mock_file_manager):
        """Test that executor respects skip_files list during extraction"""
        # Create archive with multiple files
        archive_path = Path(temp_dir / "test.tar.gz")
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            file1 = temp_dir / "file1.txt"
            file1.write_text("content1")
            tar.add(str(file1), arcname="file1.txt")
            
            file2 = temp_dir / "file2.txt"
            file2.write_text("content2")
            tar.add(str(file2), arcname="file2.txt")
            
            file3 = temp_dir / "file3.txt"
            file3.write_text("content3")
            tar.add(str(file3), arcname="file3.txt")
        
        # Create destination directory
        dest_dir = Path(temp_dir / "extract")
        dest_dir.mkdir()
        
        # Extract with skip list
        skip_files = ["file2.txt"]
        
        # Mock completion callback
        completion_called = []
        def completion_callback(success, errors):
            completion_called.append((success, errors))
        
        # Perform extraction
        executor.perform_extract_operation(
            archive_path,
            dest_dir,
            overwrite=True,
            skip_files=skip_files,
            completion_callback=completion_callback
        )
        
        # Wait for thread to complete
        if executor._current_thread:
            executor._current_thread.join(timeout=5)
        
        # Verify file1 and file3 were extracted, but not file2
        assert (dest_dir / "file1.txt").exists()
        assert not (dest_dir / "file2.txt").exists()
        assert (dest_dir / "file3.txt").exists()
        
        # Verify completion callback was called
        assert len(completion_called) == 1
        success_count, error_count = completion_called[0]
        assert success_count == 2  # file1 and file3
        assert error_count == 0
    
    def test_executor_respects_overwrite_flag(self, executor, temp_dir, mock_file_manager):
        """Test that executor respects overwrite flag"""
        # Create archive
        archive_path = Path(temp_dir / "test.tar.gz")
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            file1 = temp_dir / "file1.txt"
            file1.write_text("new content")
            tar.add(str(file1), arcname="file1.txt")
        
        # Create destination with existing file
        dest_dir = Path(temp_dir / "extract")
        dest_dir.mkdir()
        existing_file = dest_dir / "file1.txt"
        existing_file.write_text("old content")
        
        # Mock completion callback
        completion_called = []
        def completion_callback(success, errors):
            completion_called.append((success, errors))
        
        # Extract with overwrite=True
        executor.perform_extract_operation(
            archive_path,
            dest_dir,
            overwrite=True,
            skip_files=[],
            completion_callback=completion_callback
        )
        
        # Wait for thread to complete
        if executor._current_thread:
            executor._current_thread.join(timeout=5)
        
        # Verify file was overwritten
        assert existing_file.read_text() == "new content"
        
        # Verify completion callback was called
        assert len(completion_called) == 1
        success_count, error_count = completion_called[0]
        assert success_count == 1
        assert error_count == 0
    
    def test_executor_skips_without_overwrite_flag(self, executor, temp_dir, mock_file_manager):
        """Test that executor skips existing files when overwrite=False"""
        # Create archive
        archive_path = Path(temp_dir / "test.tar.gz")
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            file1 = temp_dir / "file1.txt"
            file1.write_text("new content")
            tar.add(str(file1), arcname="file1.txt")
        
        # Create destination with existing file
        dest_dir = Path(temp_dir / "extract")
        dest_dir.mkdir()
        existing_file = dest_dir / "file1.txt"
        existing_file.write_text("old content")
        
        # Mock completion callback
        completion_called = []
        def completion_callback(success, errors):
            completion_called.append((success, errors))
        
        # Extract with overwrite=False
        executor.perform_extract_operation(
            archive_path,
            dest_dir,
            overwrite=False,
            skip_files=[],
            completion_callback=completion_callback
        )
        
        # Wait for thread to complete
        if executor._current_thread:
            executor._current_thread.join(timeout=5)
        
        # Verify file was NOT overwritten
        assert existing_file.read_text() == "old content"
        
        # Verify completion callback was called
        assert len(completion_called) == 1
        success_count, error_count = completion_called[0]
        assert success_count == 0  # File was skipped
        assert error_count == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
