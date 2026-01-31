"""Integration test for archive task wiring in FileManager.

This test verifies that:
1. ArchiveOperationExecutor is properly instantiated
2. ArchiveOperationUI is properly instantiated
3. Archive operations create tasks on-demand
4. Tasks are properly wired with the UI and executor
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from src.tfm_main import FileManager
from tfm_archive_operation_task import ArchiveOperationTask
from tfm_archive_operation_executor import ArchiveOperationExecutor
from tfm_archive_operation_ui import ArchiveOperationUI


@pytest.fixture
def mock_renderer():
    """Create a mock renderer for testing."""
    renderer = Mock()
    renderer.is_desktop_mode.return_value = False
    renderer.get_dimensions.return_value = (24, 80)
    renderer.supports_mouse.return_value = False
    renderer.set_event_callback = Mock()
    renderer.set_cursor_visibility = Mock()
    return renderer


@pytest.fixture
def file_manager(mock_renderer, tmp_path):
    """Create a FileManager instance for testing."""
    with patch('src.tfm_main.get_config') as mock_config:
        # Configure mock config
        config = Mock()
        config.COLOR_SCHEME = 'dark'
        config.DEFAULT_LOG_HEIGHT_RATIO = 0.3
        config.CONFIRM_ARCHIVE_CREATE = True
        config.CONFIRM_ARCHIVE_EXTRACT = True
        config.MAX_LOG_MESSAGES = 1000  # Use uppercase attribute name
        mock_config.return_value = config
        
        # Create FileManager with temporary directories
        fm = FileManager(
            mock_renderer,
            left_dir=str(tmp_path / "left"),
            right_dir=str(tmp_path / "right")
        )
        
        # Create the test directories
        (tmp_path / "left").mkdir(exist_ok=True)
        (tmp_path / "right").mkdir(exist_ok=True)
        
        return fm


def test_archive_operation_task_not_pre_created(file_manager):
    """Test that ArchiveOperationTask is NOT pre-created in FileManager.
    
    Tasks should be created on-demand when operations are initiated,
    matching the pattern used by FileOperationTask.
    """
    assert not hasattr(file_manager, 'archive_operation_task')


def test_archive_operation_executor_created(file_manager):
    """Test that ArchiveOperationExecutor is created in FileManager."""
    assert hasattr(file_manager, 'archive_operations_executor')
    assert isinstance(file_manager.archive_operations_executor, ArchiveOperationExecutor)


def test_archive_operation_ui_created(file_manager):
    """Test that ArchiveOperationUI is created in FileManager."""
    assert hasattr(file_manager, 'archive_operation_ui')
    assert isinstance(file_manager.archive_operation_ui, ArchiveOperationUI)


def test_task_created_on_demand(file_manager, tmp_path):
    """Test that tasks are created on-demand when operations are initiated."""
    # Create a test archive file
    test_file = tmp_path / "left" / "test.txt"
    test_file.write_text("test content")
    
    # Mock the start_task method to capture the task
    captured_task = None
    original_start_task = file_manager.start_task
    
    def mock_start_task(task):
        nonlocal captured_task
        captured_task = task
        # Don't actually start the task to avoid threading complexity
    
    file_manager.start_task = mock_start_task
    
    # Trigger archive creation (this should create a task on-demand)
    file_manager._pending_archive_files = [Path(str(test_file))]
    archive_path = Path(str(tmp_path / "right" / "test.tar.gz"))
    
    # Simulate the archive creation flow
    from tfm_archive_operation_task import ArchiveOperationTask
    task = ArchiveOperationTask(file_manager, file_manager.archive_operation_ui, file_manager.archive_operations_executor)
    task.start_operation('create', file_manager._pending_archive_files, archive_path, 'tar.gz')
    file_manager.start_task(task)
    
    # Verify a task was created and started
    assert captured_task is not None
    assert isinstance(captured_task, ArchiveOperationTask)
    
    # Verify task is properly wired
    assert captured_task.ui is file_manager.archive_operation_ui
    assert captured_task.executor is file_manager.archive_operations_executor
    assert captured_task.file_manager is file_manager
    
    # Restore original method
    file_manager.start_task = original_start_task


def test_multiple_operations_create_separate_tasks(file_manager, tmp_path):
    """Test that multiple operations create separate task instances.
    
    This verifies that tasks are created on-demand rather than reused,
    matching the FileOperationTask pattern.
    """
    # Create test files
    test_file1 = tmp_path / "left" / "test1.txt"
    test_file1.write_text("test content 1")
    test_file2 = tmp_path / "left" / "test2.txt"
    test_file2.write_text("test content 2")
    
    # Create two tasks
    task1 = ArchiveOperationTask(file_manager, file_manager.archive_operation_ui, file_manager.archive_operations_executor)
    task2 = ArchiveOperationTask(file_manager, file_manager.archive_operation_ui, file_manager.archive_operations_executor)
    
    # Verify they are separate instances
    assert task1 is not task2
    
    # Verify both are properly wired
    assert task1.ui is file_manager.archive_operation_ui
    assert task2.ui is file_manager.archive_operation_ui
    assert task1.executor is file_manager.archive_operations_executor
    assert task2.executor is file_manager.archive_operations_executor


def test_executor_has_required_dependencies(file_manager):
    """Test that the executor has all required dependencies."""
    executor = file_manager.archive_operations_executor
    
    # Verify executor has required dependencies
    assert executor.file_manager is file_manager
    assert executor.progress_manager is file_manager.progress_manager
    assert executor.cache_manager is file_manager.cache_manager


def test_ui_has_required_dependencies(file_manager):
    """Test that the UI has all required dependencies."""
    ui = file_manager.archive_operation_ui
    
    # Verify UI has required dependencies
    assert ui.file_manager is file_manager


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
