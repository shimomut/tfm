"""
Tests for archive operation cancellation support.

This module tests that archive operations can be cancelled via ESC key
and that partial work is cleaned up properly.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import tempfile
import shutil

from src.tfm_archive_operation_task import ArchiveOperationTask, State
from src.tfm_archive_operation_executor import ArchiveOperationExecutor
from src.tfm_progress_manager import ProgressManager
from ttk.input_event import KeyEvent, KeyCode, ModifierKey


class TestArchiveCancellation(unittest.TestCase):
    """Test suite for archive operation cancellation"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock file manager
        self.file_manager = Mock()
        self.file_manager.operation_in_progress = False
        self.file_manager.operation_cancelled = False
        self.file_manager.mark_dirty = Mock()
        self.file_manager._clear_task = Mock()
        
        # Create mock UI
        self.ui = Mock()
        self.ui.config = Mock()
        self.ui.config.CONFIRM_ARCHIVE_CREATE = False
        self.ui.config.CONFIRM_ARCHIVE_EXTRACT = False
        
        # Create mock progress manager
        self.progress_manager = Mock(spec=ProgressManager)
        
        # Create executor
        self.executor = ArchiveOperationExecutor(
            self.file_manager,
            self.progress_manager,
            cache_manager=None
        )
        
        # Create task
        self.task = ArchiveOperationTask(
            self.file_manager,
            self.ui,
            self.executor
        )
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp(prefix='tfm_test_cancel_')
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary directory
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    def test_esc_key_sets_cancellation_flag_during_execution(self):
        """Test that ESC key sets operation_cancelled flag when executing"""
        # Set task to EXECUTING state
        self.task.state = State.EXECUTING
        
        # Create ESC key event
        esc_event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
        
        # Handle the key event
        result = self.task.handle_key_event(esc_event)
        
        # Verify ESC was handled
        self.assertTrue(result)
        
        # Verify cancellation flag was set
        self.assertTrue(self.file_manager.operation_cancelled)
    
    def test_esc_key_ignored_when_not_executing(self):
        """Test that ESC key is ignored when not in EXECUTING state"""
        # Set task to CONFIRMING state
        self.task.state = State.CONFIRMING
        
        # Create ESC key event
        esc_event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
        
        # Handle the key event
        result = self.task.handle_key_event(esc_event)
        
        # Verify ESC was not handled
        self.assertFalse(result)
        
        # Verify cancellation flag was not set
        self.assertFalse(self.file_manager.operation_cancelled)
    
    def test_cancel_method_sets_flag_during_execution(self):
        """Test that cancel() method sets cancellation flag when executing"""
        # Set task to EXECUTING state
        self.task.state = State.EXECUTING
        self.task.context = Mock()
        
        # Call cancel
        self.task.cancel()
        
        # Verify cancellation flag was set
        self.assertTrue(self.file_manager.operation_cancelled)
        
        # Verify task transitioned to IDLE
        self.assertEqual(self.task.state, State.IDLE)
        
        # Verify context was cleared
        self.assertIsNone(self.task.context)
    
    def test_completion_callback_invoked_on_cancellation(self):
        """Test that completion callback is invoked even when cancelled"""
        # Create test files
        test_file = self.temp_path / "test.txt"
        test_file.write_text("test content")
        
        archive_path = self.temp_path / "test.tar.gz"
        
        # Create callback mock
        callback = Mock()
        
        # Set cancellation flag before operation starts
        self.file_manager.operation_cancelled = True
        
        # Start create operation with callback
        self.executor.perform_create_operation(
            [test_file],
            archive_path,
            'tar.gz',
            completion_callback=callback
        )
        
        # Wait for thread to complete
        import time
        time.sleep(0.5)
        
        # Verify callback was invoked at least once
        # (It may be called multiple times due to early returns in the thread)
        self.assertGreaterEqual(callback.call_count, 1)
    
    def test_partial_archive_cleaned_up_on_cancellation(self):
        """Test that partial archive file is removed when cancelled"""
        # Create test files
        test_file1 = self.temp_path / "test1.txt"
        test_file1.write_text("test content 1")
        test_file2 = self.temp_path / "test2.txt"
        test_file2.write_text("test content 2")
        
        archive_path = self.temp_path / "test.tar.gz"
        
        # Mock to cancel after first file
        original_update = self.progress_manager.update_progress
        call_count = [0]
        
        def cancel_after_first(*args):
            call_count[0] += 1
            if call_count[0] >= 1:
                self.file_manager.operation_cancelled = True
            if hasattr(original_update, '__call__'):
                original_update(*args)
        
        self.progress_manager.update_progress = cancel_after_first
        
        # Start create operation
        self.executor.perform_create_operation(
            [test_file1, test_file2],
            archive_path,
            'tar.gz',
            completion_callback=None
        )
        
        # Wait for thread to complete
        import time
        time.sleep(0.5)
        
        # Verify partial archive was cleaned up
        self.assertFalse(archive_path.exists(), 
                        "Partial archive should be removed after cancellation")
    
    def test_task_transitions_to_idle_on_cancellation(self):
        """Test that task transitions to IDLE state after cancellation"""
        # Set up task with context
        self.task.state = State.EXECUTING
        self.task.context = Mock()
        self.task.context.operation_type = 'create'
        self.task.context.results = {'success': [], 'skipped': [], 'errors': []}
        
        # Set cancellation flag
        self.file_manager.operation_cancelled = True
        
        # Call completion handler
        self.task._on_operation_complete(0, 0)
        
        # Verify task transitioned to IDLE
        self.assertEqual(self.task.state, State.IDLE)
        
        # Verify context was cleared
        self.assertIsNone(self.task.context)
    
    def test_cancellation_message_in_completion_summary(self):
        """Test that cancellation is mentioned in completion summary"""
        # Set up task with context
        self.task.state = State.COMPLETED
        self.task.context = Mock()
        self.task.context.operation_type = 'create'
        self.task.context.results = {
            'success': [Path('file1.txt')],
            'skipped': [],
            'errors': []
        }
        
        # Set cancellation flag
        self.file_manager.operation_cancelled = True
        
        # Capture log messages
        with patch.object(self.task.logger, 'warning') as mock_warning:
            self.task._complete_operation()
            
            # Verify warning was logged with cancellation message
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0][0]
            self.assertIn('cancelled', call_args.lower())


if __name__ == '__main__':
    unittest.main()
