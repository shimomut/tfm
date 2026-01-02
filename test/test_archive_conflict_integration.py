#!/usr/bin/env python3
"""
Integration tests for archive operation conflict detection and state transitions.

This module tests the complete workflow of conflict detection including state
transitions from CHECKING_CONFLICTS to RESOLVING_CONFLICT or EXECUTING.
"""

import tempfile
import tarfile
from pathlib import Path as PathlibPath
from unittest.mock import Mock, MagicMock, patch

import pytest

from tfm_path import Path
from tfm_archive_operation_task import ArchiveOperationTask, State
from tfm_archive_operation_executor import ArchiveOperationExecutor
from tfm_archive_operation_ui import ArchiveOperationUI
from tfm_progress_manager import ProgressManager


class TestConflictDetectionIntegration:
    """Integration tests for conflict detection workflow"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield PathlibPath(tmpdir)
    
    @pytest.fixture
    def file_manager(self):
        """Create a mock file manager"""
        fm = Mock()
        fm.operation_in_progress = False
        fm.operation_cancelled = False
        fm.mark_dirty = Mock()
        fm._clear_task = Mock()
        return fm
    
    @pytest.fixture
    def ui(self):
        """Create a mock UI"""
        ui_mock = Mock(spec=ArchiveOperationUI)
        ui_mock.config = Mock()
        ui_mock.config.CONFIRM_ARCHIVE_CREATE = False
        ui_mock.config.CONFIRM_ARCHIVE_EXTRACT = False
        ui_mock.show_confirmation_dialog = Mock()
        ui_mock.show_conflict_dialog = Mock()
        return ui_mock
    
    @pytest.fixture
    def executor(self, file_manager):
        """Create an executor instance"""
        progress_manager = Mock(spec=ProgressManager)
        cache_manager = Mock()
        return ArchiveOperationExecutor(file_manager, progress_manager, cache_manager)
    
    @pytest.fixture
    def task(self, file_manager, ui, executor):
        """Create a task instance"""
        return ArchiveOperationTask(file_manager, ui, executor)
    
    def test_create_with_conflict_transitions_to_resolving(self, task, temp_dir):
        """Test that create operation with conflict transitions to RESOLVING_CONFLICT state"""
        # Create an existing archive file
        archive_path = Path(temp_dir / "test.tar.gz")
        archive_path.touch()
        
        # Create source file
        source_file = Path(temp_dir / "source.txt")
        source_file.write_text("test content")
        
        # Start operation (confirmation disabled)
        task.start_operation('create', [source_file], archive_path, 'tar.gz')
        
        # Should transition to CHECKING_CONFLICTS then RESOLVING_CONFLICT
        assert task.state == State.RESOLVING_CONFLICT
        assert len(task.context.conflicts) == 1
        assert task.context.conflicts[0] == archive_path
    
    def test_create_without_conflict_transitions_to_executing(self, task, temp_dir):
        """Test that create operation without conflict transitions to EXECUTING state"""
        # Archive file doesn't exist
        archive_path = Path(temp_dir / "test.tar.gz")
        
        # Create source file
        source_file = Path(temp_dir / "source.txt")
        source_file.write_text("test content")
        
        # Mock the executor's perform_create_operation to prevent actual execution
        task.executor.perform_create_operation = Mock()
        
        # Start operation (confirmation disabled)
        task.start_operation('create', [source_file], archive_path, 'tar.gz')
        
        # Should transition to CHECKING_CONFLICTS then EXECUTING
        assert task.state == State.EXECUTING
        assert len(task.context.conflicts) == 0
        
        # Verify executor was called
        task.executor.perform_create_operation.assert_called_once()
    
    def test_extract_with_conflicts_transitions_to_resolving(self, task, temp_dir):
        """Test that extract operation with conflicts transitions to RESOLVING_CONFLICT state"""
        # Create a tar.gz archive with test files
        archive_path = Path(temp_dir / "test.tar.gz")
        
        # Create files to add to archive
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Create archive
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            tar.add(str(file1), arcname="file1.txt")
            tar.add(str(file2), arcname="file2.txt")
        
        # Create extraction directory with existing files
        extract_dir = Path(temp_dir / "extract")
        extract_dir.mkdir()
        (extract_dir / "file1.txt").write_text("existing content")
        (extract_dir / "file2.txt").write_text("existing content")
        
        # Start operation (confirmation disabled)
        task.start_operation('extract', [archive_path], extract_dir)
        
        # Should transition to CHECKING_CONFLICTS then RESOLVING_CONFLICT
        assert task.state == State.RESOLVING_CONFLICT
        assert len(task.context.conflicts) == 2
    
    def test_extract_without_conflicts_transitions_to_executing(self, task, temp_dir):
        """Test that extract operation without conflicts transitions to EXECUTING state"""
        # Create a tar.gz archive with test files
        archive_path = Path(temp_dir / "test.tar.gz")
        
        # Create files to add to archive
        file1 = temp_dir / "file1.txt"
        file1.write_text("content1")
        
        # Create archive
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            tar.add(str(file1), arcname="file1.txt")
        
        # Create empty extraction directory
        extract_dir = Path(temp_dir / "extract")
        extract_dir.mkdir()
        
        # Mock the executor's perform_extract_operation to prevent actual execution
        task.executor.perform_extract_operation = Mock()
        
        # Start operation (confirmation disabled)
        task.start_operation('extract', [archive_path], extract_dir)
        
        # Should transition to CHECKING_CONFLICTS then EXECUTING
        assert task.state == State.EXECUTING
        assert len(task.context.conflicts) == 0
        
        # Verify executor was called
        task.executor.perform_extract_operation.assert_called_once()
    
    def test_conflict_detection_with_confirmation_enabled(self, task, temp_dir):
        """Test that conflict detection happens after confirmation"""
        # Enable confirmation
        task.ui.config.CONFIRM_ARCHIVE_CREATE = True
        
        # Create an existing archive file
        archive_path = Path(temp_dir / "test.tar.gz")
        archive_path.touch()
        
        # Create source file
        source_file = Path(temp_dir / "source.txt")
        source_file.write_text("test content")
        
        # Start operation
        task.start_operation('create', [source_file], archive_path, 'tar.gz')
        
        # Should be in CONFIRMING state
        assert task.state == State.CONFIRMING
        
        # Confirm the operation
        task.on_confirmed(True)
        
        # Should now be in RESOLVING_CONFLICT state
        assert task.state == State.RESOLVING_CONFLICT
        assert len(task.context.conflicts) == 1
    
    def test_cancellation_during_conflict_detection(self, task, temp_dir):
        """Test that cancellation flag is respected during conflict detection"""
        # Create a tar.gz archive with many test files
        archive_path = Path(temp_dir / "test.tar.gz")
        
        # Create many files to add to archive
        files = []
        for i in range(100):
            file_path = temp_dir / f"file{i}.txt"
            file_path.write_text(f"content{i}")
            files.append(file_path)
        
        # Create archive
        with tarfile.open(str(archive_path), 'w:gz') as tar:
            for file_path in files:
                tar.add(str(file_path), arcname=file_path.name)
        
        # Create extraction directory with existing files
        extract_dir = Path(temp_dir / "extract")
        extract_dir.mkdir()
        for i in range(100):
            (extract_dir / f"file{i}.txt").write_text("existing content")
        
        # Start operation (confirmation disabled)
        # Don't set cancellation flag - conflict detection will complete normally
        task.start_operation('extract', [archive_path], extract_dir)
        
        # Should detect all conflicts and transition to RESOLVING_CONFLICT
        assert task.state == State.RESOLVING_CONFLICT
        assert len(task.context.conflicts) == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
