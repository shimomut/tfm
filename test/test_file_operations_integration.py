"""
Integration tests for file operations refactoring

This test module verifies that the complete file operations flow works correctly
with the new architecture: FileListManager, FileOperationsUI, FileOperationTask,
and FileOperationsExecutor.

Run with: PYTHONPATH=.:src:ttk pytest test/test_file_operations_integration.py -v
"""

import tempfile
import shutil
import time
from pathlib import Path as StdPath
from unittest.mock import Mock, MagicMock

from tfm_file_operations import FileListManager, FileOperationsUI
from tfm_file_operation_task import FileOperationTask, State
from tfm_file_operations_executor import FileOperationsExecutor
from tfm_path import Path as TFMPath
from tfm_progress_manager import ProgressManager
from tfm_cache_manager import CacheManager


class MockConfig:
    """Mock configuration for testing"""
    SHOW_HIDDEN_FILES = False
    MAX_EXTENSION_LENGTH = 5
    SEPARATE_EXTENSIONS = True
    CONFIRM_COPY = False
    CONFIRM_MOVE = False
    CONFIRM_DELETE = False


class MockFileManager:
    """Mock FileManager for integration testing"""
    
    def __init__(self):
        self.config = MockConfig()
        self.operation_in_progress = False
        self.operation_cancelled = False
        self.needs_full_redraw = False
        self.progress_manager = ProgressManager()
        self.cache_manager = CacheManager()
        self.log_manager = None
        
        # Create file list manager
        self.file_list_manager = FileListManager(self.config)
        
        # Create executor
        self.file_operations_executor = FileOperationsExecutor(self)
        
        # Create UI
        self.file_operations_ui = FileOperationsUI(self, self.file_list_manager)
        
        # Mock panes
        self.active_pane = 'left'
        self.panes = {
            'left': {
                'path': TFMPath('/tmp/left'),
                'files': [],
                'selected_files': set(),
                'selected_index': 0,
                'scroll_offset': 0,
                'filter_pattern': '',
                'sort_mode': 'name',
                'sort_reverse': False
            },
            'right': {
                'path': TFMPath('/tmp/right'),
                'files': [],
                'selected_files': set(),
                'selected_index': 0,
                'scroll_offset': 0,
                'filter_pattern': '',
                'sort_mode': 'name',
                'sort_reverse': False
            }
        }
        
        # Track task
        self.current_task = None
    
    def get_current_pane(self):
        return self.panes[self.active_pane]
    
    def get_inactive_pane(self):
        return self.panes['right' if self.active_pane == 'left' else 'left']
    
    def refresh_files(self, pane_data=None):
        """Mock refresh"""
        pass
    
    def show_confirmation(self, message, callback):
        """Auto-confirm for testing"""
        callback(True)
    
    def show_dialog(self, message, choices, callback):
        """Auto-select first choice for testing"""
        callback(choices[0]['value'])
    
    def mark_dirty(self):
        """Mock mark dirty"""
        self.needs_full_redraw = True
    
    def _clear_task(self):
        """Clear current task"""
        self.current_task = None
        self.operation_in_progress = False


def test_complete_copy_flow():
    """Test complete copy operation flow through all layers"""
    print("\n=== Test: Complete Copy Flow ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = StdPath(temp_dir)
        
        # Create source directory with test files
        source_dir = temp_path / "source"
        source_dir.mkdir()
        
        test_file1 = source_dir / "test1.txt"
        test_file2 = source_dir / "test2.txt"
        test_file1.write_text("Test content 1")
        test_file2.write_text("Test content 2")
        
        # Create destination directory
        dest_dir = temp_path / "dest"
        dest_dir.mkdir()
        
        # Initialize mock file manager
        mock_fm = MockFileManager()
        
        # Set up panes
        mock_fm.panes['left']['path'] = TFMPath(source_dir)
        mock_fm.panes['left']['files'] = [TFMPath(test_file1), TFMPath(test_file2)]
        mock_fm.panes['left']['selected_files'] = {str(test_file1), str(test_file2)}
        mock_fm.panes['right']['path'] = TFMPath(dest_dir)
        
        # Create task
        task = FileOperationTask(
            mock_fm,
            mock_fm.file_operations_ui,
            mock_fm.file_operations_executor
        )
        
        # Start copy operation
        files_to_copy = [TFMPath(test_file1), TFMPath(test_file2)]
        destination = TFMPath(dest_dir)
        
        task.start_operation('copy', files_to_copy, destination)
        
        # Wait for operation to complete
        for _ in range(50):
            if task.state == State.IDLE:
                break
            time.sleep(0.1)
        
        # Verify files were copied
        assert (dest_dir / "test1.txt").exists()
        assert (dest_dir / "test2.txt").exists()
        assert (dest_dir / "test1.txt").read_text() == "Test content 1"
        assert (dest_dir / "test2.txt").read_text() == "Test content 2"
        
        # Verify task completed
        assert task.state == State.IDLE
        
        print("✓ Complete copy flow works correctly")


def test_complete_move_flow():
    """Test complete move operation flow through all layers"""
    print("\n=== Test: Complete Move Flow ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = StdPath(temp_dir)
        
        # Create source directory with test files
        source_dir = temp_path / "source"
        source_dir.mkdir()
        
        test_file1 = source_dir / "test1.txt"
        test_file2 = source_dir / "test2.txt"
        test_file1.write_text("Test content 1")
        test_file2.write_text("Test content 2")
        
        # Create destination directory
        dest_dir = temp_path / "dest"
        dest_dir.mkdir()
        
        # Initialize mock file manager
        mock_fm = MockFileManager()
        
        # Set up panes
        mock_fm.panes['left']['path'] = TFMPath(source_dir)
        mock_fm.panes['left']['files'] = [TFMPath(test_file1), TFMPath(test_file2)]
        mock_fm.panes['left']['selected_files'] = {str(test_file1), str(test_file2)}
        mock_fm.panes['right']['path'] = TFMPath(dest_dir)
        
        # Create task
        task = FileOperationTask(
            mock_fm,
            mock_fm.file_operations_ui,
            mock_fm.file_operations_executor
        )
        
        # Start move operation
        files_to_move = [TFMPath(test_file1), TFMPath(test_file2)]
        destination = TFMPath(dest_dir)
        
        task.start_operation('move', files_to_move, destination)
        
        # Wait for operation to complete
        for _ in range(50):
            if task.state == State.IDLE:
                break
            time.sleep(0.1)
        
        # Verify files were moved
        assert (dest_dir / "test1.txt").exists()
        assert (dest_dir / "test2.txt").exists()
        assert not test_file1.exists()
        assert not test_file2.exists()
        assert (dest_dir / "test1.txt").read_text() == "Test content 1"
        assert (dest_dir / "test2.txt").read_text() == "Test content 2"
        
        # Verify task completed
        assert task.state == State.IDLE
        
        print("✓ Complete move flow works correctly")


def test_complete_delete_flow():
    """Test complete delete operation flow through all layers"""
    print("\n=== Test: Complete Delete Flow ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = StdPath(temp_dir)
        
        # Create test files
        test_file1 = temp_path / "test1.txt"
        test_file2 = temp_path / "test2.txt"
        test_file1.write_text("Test content 1")
        test_file2.write_text("Test content 2")
        
        # Initialize mock file manager
        mock_fm = MockFileManager()
        
        # Set up panes
        mock_fm.panes['left']['path'] = TFMPath(temp_path)
        mock_fm.panes['left']['files'] = [TFMPath(test_file1), TFMPath(test_file2)]
        mock_fm.panes['left']['selected_files'] = {str(test_file1), str(test_file2)}
        mock_fm.panes['left']['focused_index'] = 0
        
        # Create task
        task = FileOperationTask(
            mock_fm,
            mock_fm.file_operations_ui,
            mock_fm.file_operations_executor
        )
        
        # Start delete operation
        files_to_delete = [TFMPath(test_file1), TFMPath(test_file2)]
        
        task.start_operation('delete', files_to_delete)
        
        # Wait for operation to complete
        for _ in range(50):
            if task.state == State.IDLE:
                break
            time.sleep(0.1)
        
        # Verify files were deleted
        assert not test_file1.exists()
        assert not test_file2.exists()
        
        # Verify task completed
        assert task.state == State.IDLE
        
        print("✓ Complete delete flow works correctly")


def test_conflict_resolution_flow():
    """Test conflict resolution flow through all layers"""
    print("\n=== Test: Conflict Resolution Flow ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = StdPath(temp_dir)
        
        # Create source directory with test file
        source_dir = temp_path / "source"
        source_dir.mkdir()
        
        test_file = source_dir / "test.txt"
        test_file.write_text("Source content")
        
        # Create destination directory with conflicting file
        dest_dir = temp_path / "dest"
        dest_dir.mkdir()
        
        dest_file = dest_dir / "test.txt"
        dest_file.write_text("Destination content")
        
        # Initialize mock file manager
        mock_fm = MockFileManager()
        
        # Override show_dialog to select "overwrite"
        def mock_show_dialog(message, choices, callback, enable_shift_modifier=False):
            # Find overwrite choice
            for choice in choices:
                if choice['value'] == 'overwrite':
                    callback('overwrite')
                    return
            callback(choices[0]['value'])
        
        mock_fm.show_dialog = mock_show_dialog
        
        # Set up panes
        mock_fm.panes['left']['path'] = TFMPath(source_dir)
        mock_fm.panes['left']['files'] = [TFMPath(test_file)]
        mock_fm.panes['left']['selected_files'] = {str(test_file)}
        mock_fm.panes['right']['path'] = TFMPath(dest_dir)
        
        # Create task
        task = FileOperationTask(
            mock_fm,
            mock_fm.file_operations_ui,
            mock_fm.file_operations_executor
        )
        
        # Start copy operation
        files_to_copy = [TFMPath(test_file)]
        destination = TFMPath(dest_dir)
        
        task.start_operation('copy', files_to_copy, destination)
        
        # Wait for operation to complete
        for _ in range(50):
            if task.state == State.IDLE:
                break
            time.sleep(0.1)
        
        # Verify file was overwritten
        assert dest_file.exists()
        assert dest_file.read_text() == "Source content"
        
        # Verify task completed
        assert task.state == State.IDLE
        
        print("✓ Conflict resolution flow works correctly")


def test_architecture_boundaries():
    """Test that architectural boundaries are respected"""
    print("\n=== Test: Architecture Boundaries ===")
    
    mock_fm = MockFileManager()
    
    # Verify FileListManager has no UI or I/O code
    file_list_manager = mock_fm.file_list_manager
    assert hasattr(file_list_manager, 'sort_entries')
    assert hasattr(file_list_manager, 'get_file_info')
    assert hasattr(file_list_manager, 'refresh_files')
    assert not hasattr(file_list_manager, 'perform_copy_operation')
    assert not hasattr(file_list_manager, 'show_dialog')
    
    # Verify FileOperationsUI has UI methods but no I/O code
    file_ops_ui = mock_fm.file_operations_ui
    assert hasattr(file_ops_ui, 'show_confirmation_dialog')
    assert hasattr(file_ops_ui, 'show_conflict_dialog')
    assert hasattr(file_ops_ui, 'show_rename_dialog')
    assert hasattr(file_ops_ui, 'copy_selected_files')
    
    # Verify FileOperationsExecutor has I/O methods but no UI code
    executor = mock_fm.file_operations_executor
    assert hasattr(executor, 'perform_copy_operation')
    assert hasattr(executor, 'perform_move_operation')
    assert hasattr(executor, 'perform_delete_operation')
    assert not hasattr(executor, 'show_dialog')
    assert not hasattr(executor, 'show_confirmation')
    
    # Verify FileOperationTask has orchestration but no UI or I/O code
    task = FileOperationTask(mock_fm, file_ops_ui, executor)
    assert hasattr(task, 'start_operation')
    assert hasattr(task, 'on_confirmed')
    assert hasattr(task, 'on_conflict_resolved')
    assert task.ui == file_ops_ui
    assert task.executor == executor
    
    print("✓ Architecture boundaries are respected")


def test_no_circular_dependencies():
    """Test that there are no circular dependencies"""
    print("\n=== Test: No Circular Dependencies ===")
    
    mock_fm = MockFileManager()
    
    # Verify dependency flow: UI → Task → Executor
    file_ops_ui = mock_fm.file_operations_ui
    executor = mock_fm.file_operations_executor
    
    # FileOperationsUI should not depend on FileOperationTask
    assert not hasattr(file_ops_ui, 'task')
    
    # FileOperationTask should depend on UI and Executor
    task = FileOperationTask(mock_fm, file_ops_ui, executor)
    assert task.ui == file_ops_ui
    assert task.executor == executor
    
    # FileOperationsExecutor should not depend on Task or UI
    assert not hasattr(executor, 'task')
    assert not hasattr(executor, 'ui')
    
    print("✓ No circular dependencies detected")


def main():
    """Run all integration tests"""
    print("Running file operations integration tests...\n")
    
    try:
        test_complete_copy_flow()
        test_complete_move_flow()
        test_complete_delete_flow()
        test_conflict_resolution_flow()
        test_architecture_boundaries()
        test_no_circular_dependencies()
        
        print("\n✅ All integration tests passed!")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
