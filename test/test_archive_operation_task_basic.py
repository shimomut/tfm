"""Basic tests for ArchiveOperationTask to verify implementation."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from tfm_archive_operation_task import (
    ArchiveOperationTask,
    ArchiveOperationContext,
    State
)


class TestArchiveOperationTaskBasic:
    """Basic tests for ArchiveOperationTask."""
    
    def test_task_initialization(self):
        """Test that task initializes correctly."""
        file_manager = Mock()
        ui = Mock()
        executor = Mock()
        
        task = ArchiveOperationTask(file_manager, ui, executor)
        
        assert task.file_manager is file_manager
        assert task.ui is ui
        assert task.executor is executor
        assert task.state == State.IDLE
        assert task.context is None
        assert task.logger is not None
    
    def test_is_active_when_idle(self):
        """Test that task is not active when in IDLE state."""
        file_manager = Mock()
        ui = Mock()
        executor = Mock()
        
        task = ArchiveOperationTask(file_manager, ui, executor)
        
        assert not task.is_active()
    
    def test_is_active_when_confirming(self):
        """Test that task is active when in CONFIRMING state."""
        file_manager = Mock()
        ui = Mock()
        executor = Mock()
        
        task = ArchiveOperationTask(file_manager, ui, executor)
        task.state = State.CONFIRMING
        
        assert task.is_active()
    
    def test_get_state(self):
        """Test that get_state returns correct state string."""
        file_manager = Mock()
        ui = Mock()
        executor = Mock()
        
        task = ArchiveOperationTask(file_manager, ui, executor)
        
        assert task.get_state() == "idle"
        
        task.state = State.CONFIRMING
        assert task.get_state() == "confirming"
    
    def test_cancel_when_active(self):
        """Test that cancel transitions to IDLE and clears context."""
        file_manager = Mock()
        ui = Mock()
        executor = Mock()
        
        task = ArchiveOperationTask(file_manager, ui, executor)
        task.state = State.CONFIRMING
        task.context = Mock()
        
        task.cancel()
        
        assert task.state == State.IDLE
        assert task.context is None
        file_manager._clear_task.assert_called_once()
    
    def test_start_operation_create_with_confirmation(self):
        """Test starting a create operation with confirmation enabled."""
        file_manager = Mock()
        ui = Mock()
        ui.config = Mock()
        ui.config.CONFIRM_ARCHIVE_CREATE = True
        executor = Mock()
        
        task = ArchiveOperationTask(file_manager, ui, executor)
        
        source_paths = [Path("/tmp/file1.txt"), Path("/tmp/file2.txt")]
        destination = Path("/tmp/archive.tar.gz")
        
        task.start_operation('create', source_paths, destination, 'tar.gz')
        
        assert task.state == State.CONFIRMING
        assert task.context is not None
        assert task.context.operation_type == 'create'
        assert task.context.source_paths == source_paths
        assert task.context.destination == destination
        assert task.context.format_type == 'tar.gz'
        ui.show_confirmation_dialog.assert_called_once()
    
    def test_start_operation_extract_without_confirmation(self):
        """Test starting an extract operation with confirmation disabled."""
        file_manager = Mock()
        ui = Mock()
        ui.config = Mock()
        ui.config.CONFIRM_ARCHIVE_EXTRACT = False
        executor = Mock()
        
        task = ArchiveOperationTask(file_manager, ui, executor)
        
        # Mock _check_conflicts to prevent actual execution
        task._check_conflicts = Mock()
        
        source_paths = [Path("/tmp/archive.tar.gz")]
        destination = Path("/tmp/extract_dir")
        
        task.start_operation('extract', source_paths, destination, 'tar.gz')
        
        assert task.state == State.CHECKING_CONFLICTS
        assert task.context is not None
        assert task.context.operation_type == 'extract'
        task._check_conflicts.assert_called_once()
    
    def test_start_operation_invalid_type(self):
        """Test that invalid operation type raises ValueError."""
        file_manager = Mock()
        ui = Mock()
        executor = Mock()
        
        task = ArchiveOperationTask(file_manager, ui, executor)
        
        with pytest.raises(ValueError, match="Invalid operation type"):
            task.start_operation('invalid', [], Path("/tmp/dest"))
    
    def test_on_confirmed_true(self):
        """Test that confirming proceeds to conflict checking."""
        file_manager = Mock()
        ui = Mock()
        executor = Mock()
        
        task = ArchiveOperationTask(file_manager, ui, executor)
        task.context = ArchiveOperationContext(
            operation_type='create',
            source_paths=[Path("/tmp/file.txt")],
            destination=Path("/tmp/archive.tar.gz")
        )
        task.state = State.CONFIRMING
        
        # Mock _check_conflicts to prevent actual execution
        task._check_conflicts = Mock()
        
        task.on_confirmed(True)
        
        assert task.state == State.CHECKING_CONFLICTS
        task._check_conflicts.assert_called_once()
    
    def test_on_confirmed_false(self):
        """Test that cancelling confirmation returns to IDLE."""
        file_manager = Mock()
        ui = Mock()
        executor = Mock()
        
        task = ArchiveOperationTask(file_manager, ui, executor)
        task.context = ArchiveOperationContext(
            operation_type='create',
            source_paths=[Path("/tmp/file.txt")],
            destination=Path("/tmp/archive.tar.gz")
        )
        task.state = State.CONFIRMING
        
        task.on_confirmed(False)
        
        assert task.state == State.IDLE
        assert task.context is None
        file_manager._clear_task.assert_called_once()
    
    def test_archive_operation_context_defaults(self):
        """Test that ArchiveOperationContext has correct defaults."""
        context = ArchiveOperationContext(
            operation_type='create',
            source_paths=[Path("/tmp/file.txt")],
            destination=Path("/tmp/archive.tar.gz")
        )
        
        assert context.operation_type == 'create'
        assert context.format_type == 'tar.gz'
        assert context.conflicts == []
        assert context.current_conflict_index == 0
        assert 'success' in context.results
        assert 'skipped' in context.results
        assert 'errors' in context.results
        assert context.options['overwrite_all'] is False
        assert context.options['skip_all'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
