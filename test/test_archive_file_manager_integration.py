"""
Tests for archive operation file manager integration.

This module tests that archive operations properly integrate with the file manager,
including refreshing the file list, marking the UI as dirty, and clearing operation flags.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path as PathlibPath

from tfm_archive_operation_task import ArchiveOperationTask, State
from tfm_path import Path


class TestArchiveFileManagerIntegration(unittest.TestCase):
    """Test file manager integration for archive operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock file manager
        self.file_manager = Mock()
        self.file_manager.operation_in_progress = False
        self.file_manager.operation_cancelled = False
        self.file_manager.refresh = Mock()
        self.file_manager.mark_dirty = Mock()
        self.file_manager._clear_task = Mock()
        
        # Create mock UI
        self.ui = Mock()
        self.ui.config = Mock()
        self.ui.config.CONFIRM_ARCHIVE_CREATE = False
        self.ui.config.CONFIRM_ARCHIVE_EXTRACT = False
        
        # Create mock executor
        self.executor = Mock()
        self.executor._check_conflicts = Mock(return_value=[])
        
        # Create task
        self.task = ArchiveOperationTask(self.file_manager, self.ui, self.executor)
    
    def test_refresh_called_after_successful_creation(self):
        """Test that file_manager.refresh() is called after successful archive creation."""
        # Setup
        source_paths = [Path('/tmp/file1.txt'), Path('/tmp/file2.txt')]
        archive_path = Path('/tmp/archive.tar.gz')
        
        # Start operation (skip confirmation)
        self.task.start_operation('create', source_paths, archive_path, 'tar.gz')
        
        # Verify we're in EXECUTING state (no conflicts)
        self.assertEqual(self.task.state, State.EXECUTING)
        
        # Simulate successful completion
        self.task._on_operation_complete(success_count=2, error_count=0)
        
        # Verify refresh was called
        self.file_manager.refresh.assert_called_once()
    
    def test_refresh_called_after_successful_extraction(self):
        """Test that file_manager.refresh() is called after successful archive extraction."""
        # Setup
        archive_path = Path('/tmp/archive.tar.gz')
        destination_dir = Path('/tmp/extract')
        
        # Start operation (skip confirmation)
        self.task.start_operation('extract', [archive_path], destination_dir, 'tar.gz')
        
        # Verify we're in EXECUTING state (no conflicts)
        self.assertEqual(self.task.state, State.EXECUTING)
        
        # Simulate successful completion
        self.task._on_operation_complete(success_count=5, error_count=0)
        
        # Verify refresh was called
        self.file_manager.refresh.assert_called_once()
    
    def test_refresh_not_called_when_cancelled(self):
        """Test that file_manager.refresh() is NOT called when operation is cancelled."""
        # Setup
        source_paths = [Path('/tmp/file1.txt')]
        archive_path = Path('/tmp/archive.tar.gz')
        
        # Start operation
        self.task.start_operation('create', source_paths, archive_path, 'tar.gz')
        
        # Set cancellation flag
        self.file_manager.operation_cancelled = True
        
        # Simulate completion with some success (before cancellation)
        self.task._on_operation_complete(success_count=1, error_count=0)
        
        # Verify refresh was NOT called (operation was cancelled)
        self.file_manager.refresh.assert_not_called()
    
    def test_refresh_not_called_when_no_success(self):
        """Test that file_manager.refresh() is NOT called when no files were processed successfully."""
        # Setup
        source_paths = [Path('/tmp/file1.txt')]
        archive_path = Path('/tmp/archive.tar.gz')
        
        # Start operation
        self.task.start_operation('create', source_paths, archive_path, 'tar.gz')
        
        # Simulate completion with no success (all errors)
        self.task._on_operation_complete(success_count=0, error_count=5)
        
        # Verify refresh was NOT called (no successful operations)
        self.file_manager.refresh.assert_not_called()
    
    def test_mark_dirty_called_on_completion(self):
        """Test that file_manager.mark_dirty() is called when operation completes."""
        # Setup
        source_paths = [Path('/tmp/file1.txt')]
        archive_path = Path('/tmp/archive.tar.gz')
        
        # Start operation
        self.task.start_operation('create', source_paths, archive_path, 'tar.gz')
        
        # Simulate completion
        self.task._on_operation_complete(success_count=1, error_count=0)
        
        # Verify mark_dirty was called
        self.file_manager.mark_dirty.assert_called_once()
    
    def test_mark_dirty_called_even_on_failure(self):
        """Test that file_manager.mark_dirty() is called even when operation fails."""
        # Setup
        source_paths = [Path('/tmp/file1.txt')]
        archive_path = Path('/tmp/archive.tar.gz')
        
        # Start operation
        self.task.start_operation('create', source_paths, archive_path, 'tar.gz')
        
        # Simulate completion with errors
        self.task._on_operation_complete(success_count=0, error_count=5)
        
        # Verify mark_dirty was called (UI needs to update even on failure)
        self.file_manager.mark_dirty.assert_called_once()
    
    def test_operation_in_progress_cleared_on_completion(self):
        """Test that operation_in_progress flag is cleared when operation completes."""
        # Setup
        source_paths = [Path('/tmp/file1.txt')]
        archive_path = Path('/tmp/archive.tar.gz')
        
        # Start operation
        self.task.start_operation('create', source_paths, archive_path, 'tar.gz')
        
        # Set operation_in_progress flag (simulating executor setting it)
        self.file_manager.operation_in_progress = True
        
        # Simulate completion
        self.task._on_operation_complete(success_count=1, error_count=0)
        
        # Verify operation_in_progress was cleared
        self.assertFalse(self.file_manager.operation_in_progress)
    
    def test_state_transition_to_completed_then_idle(self):
        """Test that task transitions from EXECUTING to COMPLETED to IDLE."""
        # Setup
        source_paths = [Path('/tmp/file1.txt')]
        archive_path = Path('/tmp/archive.tar.gz')
        
        # Start operation
        self.task.start_operation('create', source_paths, archive_path, 'tar.gz')
        
        # Verify we're in EXECUTING state
        self.assertEqual(self.task.state, State.EXECUTING)
        
        # Simulate completion - this should transition to COMPLETED then IDLE
        self.task._on_operation_complete(success_count=1, error_count=0)
        
        # Verify we're in IDLE state (after transitioning through COMPLETED)
        self.assertEqual(self.task.state, State.IDLE)
    
    def test_clear_task_called_on_completion(self):
        """Test that file_manager._clear_task() is called when operation completes."""
        # Setup
        source_paths = [Path('/tmp/file1.txt')]
        archive_path = Path('/tmp/archive.tar.gz')
        
        # Start operation
        self.task.start_operation('create', source_paths, archive_path, 'tar.gz')
        
        # Simulate completion
        self.task._on_operation_complete(success_count=1, error_count=0)
        
        # Verify _clear_task was called
        self.file_manager._clear_task.assert_called_once()
    
    def test_integration_full_workflow(self):
        """Test complete workflow: start → execute → complete with all integrations."""
        # Setup
        source_paths = [Path('/tmp/file1.txt'), Path('/tmp/file2.txt')]
        archive_path = Path('/tmp/archive.tar.gz')
        
        # Start operation
        self.task.start_operation('create', source_paths, archive_path, 'tar.gz')
        
        # Verify initial state
        self.assertEqual(self.task.state, State.EXECUTING)
        
        # Set operation_in_progress (simulating executor)
        self.file_manager.operation_in_progress = True
        
        # Simulate successful completion
        self.task._on_operation_complete(success_count=2, error_count=0)
        
        # Verify all integrations:
        # 1. File list refreshed
        self.file_manager.refresh.assert_called_once()
        
        # 2. UI marked as dirty
        self.file_manager.mark_dirty.assert_called_once()
        
        # 3. Operation flag cleared
        self.assertFalse(self.file_manager.operation_in_progress)
        
        # 4. State transitioned to IDLE
        self.assertEqual(self.task.state, State.IDLE)
        
        # 5. Task cleared from file manager
        self.file_manager._clear_task.assert_called_once()


if __name__ == '__main__':
    unittest.main()
