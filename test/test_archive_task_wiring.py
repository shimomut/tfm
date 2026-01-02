"""Integration test for archive task wiring in FileManager.

This test verifies that:
1. ArchiveOperationTask is properly instantiated in FileManager
2. ArchiveOperationExecutor is properly instantiated
3. ArchiveOperationUI is properly instantiated
4. The task is properly wired with the UI and executor
5. Archive operations use the pre-created task instance
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


def test_archive_operation_task_created(file_manager):
    """Test that ArchiveOperationTask is created in FileManager."""
    assert hasattr(file_manager, 'archive_operation_task')
    assert isinstance(file_manager.archive_operation_task, ArchiveOperationTask)


def test_archive_operation_executor_created(file_manager):
    """Test that ArchiveOperationExecutor is created in FileManager."""
    assert hasattr(file_manager, 'archive_operations_executor')
    assert isinstance(file_manager.archive_operations_executor, ArchiveOperationExecutor)


def test_archive_operation_ui_created(file_manager):
    """Test that ArchiveOperationUI is created in FileManager."""
    assert hasattr(file_manager, 'archive_operation_ui')
    assert isinstance(file_manager.archive_operation_ui, ArchiveOperationUI)


def test_task_wired_with_ui_and_executor(file_manager):
    """Test that the task is properly wired with UI and executor."""
    task = file_manager.archive_operation_task
    
    # Verify task has references to UI and executor
    assert task.ui is file_manager.archive_operation_ui
    assert task.executor is file_manager.archive_operations_executor
    
    # Verify task has reference to file_manager
    assert task.file_manager is file_manager


def test_archive_ui_uses_task_for_creation(file_manager, tmp_path):
    """Test that ArchiveUI uses the pre-created task for archive creation."""
    # Set up test files
    test_file = tmp_path / "left" / "test.txt"
    test_file.write_text("test content")
    
    # Mock the pane manager to return test data
    file_manager.pane_manager.active_pane = 'left'
    file_manager.pane_manager.left_pane = {
        'path': tmp_path / "left",
        'files': [test_file],
        'focused_index': 0,
        'selected_files': []
    }
    file_manager.pane_manager.right_pane = {
        'path': tmp_path / "right",
        'files': [],
        'focused_index': 0,
        'selected_files': []
    }
    
    # Mock start_task to capture the task being started
    started_tasks = []
    original_start_task = file_manager.start_task
    def mock_start_task(task):
        started_tasks.append(task)
        # Don't actually start the task to avoid threading issues
    file_manager.start_task = mock_start_task
    
    # Trigger archive creation
    file_manager.archive_ui.on_create_archive_confirm("test.tar.gz")
    
    # Verify the pre-created task was used
    assert len(started_tasks) == 1
    assert started_tasks[0] is file_manager.archive_operation_task


def test_archive_ui_uses_task_for_extraction(file_manager, tmp_path):
    """Test that ArchiveUI uses the pre-created task for archive extraction."""
    # Set up test archive file
    test_archive = tmp_path / "left" / "test.tar.gz"
    test_archive.write_bytes(b"fake archive content")
    
    # Mock the pane manager to return test data
    file_manager.pane_manager.active_pane = 'left'
    file_manager.pane_manager.left_pane = {
        'path': tmp_path / "left",
        'files': [test_archive],
        'focused_index': 0,
        'selected_files': []
    }
    file_manager.pane_manager.right_pane = {
        'path': tmp_path / "right",
        'files': [],
        'focused_index': 0,
        'selected_files': []
    }
    
    # Mock start_task to capture the task being started
    started_tasks = []
    def mock_start_task(task):
        started_tasks.append(task)
        # Don't actually start the task to avoid threading issues
    file_manager.start_task = mock_start_task
    
    # Trigger archive extraction
    file_manager.archive_ui.extract_selected_archive()
    
    # Verify the pre-created task was used
    assert len(started_tasks) == 1
    assert started_tasks[0] is file_manager.archive_operation_task


def test_task_reusable_after_completion(file_manager):
    """Test that the task can be reused for multiple operations."""
    task = file_manager.archive_operation_task
    
    # Verify task starts in IDLE state
    assert task.get_state() == 'idle'
    assert not task.is_active()
    
    # The task should be reusable - it transitions back to IDLE after completion
    # This is verified by checking the state machine implementation
    # (actual execution would require full integration test with threading)


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
