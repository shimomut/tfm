"""Tests for FileOperationTask UI interface integration.

This test module verifies that FileOperationTask correctly delegates UI
interactions to FileOperationsUI instead of calling file_manager directly.
"""

import unittest
from unittest.mock import Mock, MagicMock, call
from pathlib import Path

from src.tfm_file_operation_task import FileOperationTask, State
from src.tfm_path import Path as TFMPath


class TestFileOperationTaskUIInterface(unittest.TestCase):
    """Test FileOperationTask UI delegation to FileOperationUI."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock file_manager
        self.file_manager = Mock()
        self.file_manager.operation_in_progress = False
        self.file_manager.operation_cancelled = False
        
        # Create mock UI
        self.ui = Mock()
        self.ui.config = Mock()
        self.ui.config.CONFIRM_COPY = True
        self.ui.config.CONFIRM_MOVE = True
        self.ui.config.CONFIRM_DELETE = True
        
        # Create mock executor
        self.executor = Mock()
        
        # Create task
        self.task = FileOperationTask(self.file_manager, self.ui, self.executor)
    
    def test_constructor_accepts_ui_parameter(self):
        """Test that constructor accepts ui and executor parameters."""
        # Verify ui is stored
        self.assertEqual(self.task.ui, self.ui)
        
        # Verify executor is stored
        self.assertEqual(self.task.executor, self.executor)
        
        # Verify backward compatibility
        self.assertEqual(self.task.file_operations_ui, self.ui)
    
    def test_confirmation_dialog_delegates_to_ui(self):
        """Test that confirmation dialog is shown via UI."""
        # Create test files
        test_files = [TFMPath('/tmp/test.txt')]
        destination = TFMPath('/tmp/dest')
        
        # Start copy operation
        self.task.start_operation('copy', test_files, destination)
        
        # Verify UI method was called
        self.ui.show_confirmation_dialog.assert_called_once()
        
        # Verify arguments
        call_args = self.ui.show_confirmation_dialog.call_args
        self.assertEqual(call_args[0][0], 'copy')  # operation_type
        self.assertEqual(call_args[0][1], test_files)  # files
        self.assertEqual(call_args[0][2], destination)  # destination
        self.assertIsNotNone(call_args[0][3])  # callback
    
    def test_conflict_dialog_delegates_to_ui(self):
        """Test that conflict dialog is shown via UI."""
        # Create test files with conflicts
        source_file = Mock(spec=TFMPath)
        source_file.name = 'test.txt'
        source_file.exists = Mock(return_value=True)
        
        destination = Mock(spec=TFMPath)
        destination.__truediv__ = Mock(return_value=Mock(spec=TFMPath))
        dest_file = destination / 'test.txt'
        dest_file.name = 'test.txt'
        dest_file.exists = Mock(return_value=True)
        
        test_files = [source_file]
        
        # Start operation and skip confirmation
        self.task.start_operation('copy', test_files, destination)
        self.task.on_confirmed(True)
        
        # Verify UI method was called
        self.ui.show_conflict_dialog.assert_called_once()
        
        # Verify arguments
        call_args = self.ui.show_conflict_dialog.call_args
        self.assertEqual(call_args[0][0], source_file)  # source_file
        self.assertEqual(call_args[0][2], 1)  # conflict_num
        self.assertEqual(call_args[0][3], 1)  # total_conflicts
        self.assertIsNotNone(call_args[0][4])  # callback
    
    def test_rename_dialog_delegates_to_ui(self):
        """Test that rename dialog is shown via UI."""
        # Create test files with conflicts
        source_file = Mock(spec=TFMPath)
        source_file.name = 'test.txt'
        source_file.exists = Mock(return_value=True)
        
        destination = Mock(spec=TFMPath)
        destination.__truediv__ = Mock(return_value=Mock(spec=TFMPath))
        dest_file = destination / 'test.txt'
        dest_file.name = 'test.txt'
        dest_file.exists = Mock(return_value=True)
        
        test_files = [source_file]
        
        # Start operation and skip confirmation
        self.task.start_operation('copy', test_files, destination)
        self.task.on_confirmed(True)
        
        # Resolve conflict with rename
        self.task.on_conflict_resolved('rename', apply_to_all=False)
        
        # Verify UI method was called
        self.ui.show_rename_dialog.assert_called_once()
        
        # Verify arguments
        call_args = self.ui.show_rename_dialog.call_args
        self.assertEqual(call_args[0][0], source_file)  # source_file
        self.assertEqual(call_args[0][1], destination)  # destination
        self.assertIsNotNone(call_args[0][2])  # callback
        self.assertIsNotNone(call_args[0][3])  # cancel_callback
    
    def test_state_transitions_work_correctly(self):
        """Test that state transitions work with new UI interface."""
        # Create test files
        source_file = Mock(spec=TFMPath)
        source_file.name = 'test.txt'
        source_file.exists = Mock(return_value=True)
        
        destination = Mock(spec=TFMPath)
        destination.__truediv__ = Mock(return_value=Mock(spec=TFMPath))
        dest_file = destination / 'test.txt'
        dest_file.name = 'test.txt'
        dest_file.exists = Mock(return_value=False)
        
        test_files = [source_file]
        
        # Start operation
        self.assertEqual(self.task.state, State.IDLE)
        
        self.task.start_operation('copy', test_files, destination)
        self.assertEqual(self.task.state, State.CONFIRMING)
        
        # Confirm operation
        self.task.on_confirmed(True)
        
        # After confirmation with no conflicts, should transition to EXECUTING
        self.assertEqual(self.task.state, State.EXECUTING)
    
    def test_no_file_manager_ui_calls_for_standard_dialogs(self):
        """Test that file_manager UI methods are not called for standard dialogs."""
        # Create test files
        test_files = [TFMPath('/tmp/test.txt')]
        destination = TFMPath('/tmp/dest')
        
        # Start operation
        self.task.start_operation('copy', test_files, destination)
        
        # Verify file_manager.show_confirmation was NOT called
        self.file_manager.show_confirmation.assert_not_called()
        
        # Verify UI method WAS called
        self.ui.show_confirmation_dialog.assert_called_once()
    
    def test_copy_operation_delegates_to_executor(self):
        """Test that copy operation delegates to executor."""
        # Create test files with no conflicts
        source_file = Mock(spec=TFMPath)
        source_file.name = 'test.txt'
        source_file.exists = Mock(return_value=True)
        
        destination = Mock(spec=TFMPath)
        destination.__truediv__ = Mock(return_value=Mock(spec=TFMPath))
        dest_file = destination / 'test.txt'
        dest_file.name = 'test.txt'
        dest_file.exists = Mock(return_value=False)
        dest_file.parent = destination
        
        test_files = [source_file]
        
        # Disable confirmation
        self.ui.config.CONFIRM_COPY = False
        
        # Start operation
        self.task.start_operation('copy', test_files, destination)
        
        # Give the background thread time to execute
        import time
        time.sleep(0.1)
        
        # Verify executor method was called
        self.executor.perform_copy_operation.assert_called()
    
    def test_move_operation_delegates_to_executor(self):
        """Test that move operation delegates to executor."""
        # Create test files with no conflicts
        source_file = Mock(spec=TFMPath)
        source_file.name = 'test.txt'
        source_file.exists = Mock(return_value=True)
        
        destination = Mock(spec=TFMPath)
        destination.__truediv__ = Mock(return_value=Mock(spec=TFMPath))
        dest_file = destination / 'test.txt'
        dest_file.name = 'test.txt'
        dest_file.exists = Mock(return_value=False)
        dest_file.parent = destination
        
        test_files = [source_file]
        
        # Disable confirmation
        self.ui.config.CONFIRM_MOVE = False
        
        # Start operation
        self.task.start_operation('move', test_files, destination)
        
        # Give the background thread time to execute
        import time
        time.sleep(0.1)
        
        # Verify executor method was called
        self.executor.perform_move_operation.assert_called()
    
    def test_delete_operation_delegates_to_executor(self):
        """Test that delete operation delegates to executor."""
        # Create test files
        source_file = Mock(spec=TFMPath)
        source_file.name = 'test.txt'
        source_file.exists = Mock(return_value=True)
        
        test_files = [source_file]
        
        # Disable confirmation
        self.ui.config.CONFIRM_DELETE = False
        
        # Start operation
        self.task.start_operation('delete', test_files)
        
        # Give the background thread time to execute
        import time
        time.sleep(0.1)
        
        # Verify executor method was called
        self.executor.perform_delete_operation.assert_called_once()
        
        # Verify arguments
        call_args = self.executor.perform_delete_operation.call_args
        self.assertEqual(call_args[0][0], test_files)  # files_to_delete
        self.assertIsNotNone(call_args[1]['completion_callback'])  # completion_callback


if __name__ == '__main__':
    unittest.main()
