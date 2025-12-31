"""
Test ESC key cancellation during conflict resolution.

This test verifies that pressing ESC during conflict resolution
cancels the entire file operation task.

Run with: PYTHONPATH=.:src:ttk pytest test/test_conflict_cancellation.py -v
"""

import unittest
from pathlib import Path as StdPath
import tempfile
import shutil

from tfm_file_operation_task import FileOperationTask, State
from tfm_path import Path as TFMPath


class MockConfig:
    """Mock configuration for testing"""
    CONFIRM_COPY = False
    CONFIRM_MOVE = False
    CONFIRM_DELETE = False


class MockFileManager:
    """Mock FileManager for testing"""
    def __init__(self):
        self.operation_in_progress = False
        self.operation_cancelled = False
        self.task_cleared = False
        
    def _clear_task(self):
        """Mock task clearing"""
        self.task_cleared = True


class MockUI:
    """Mock UI for testing"""
    def __init__(self):
        self.config = MockConfig()
        self.last_conflict_callback = None
        
    def show_conflict_dialog(self, source_file, dest_file, conflict_num, total_conflicts, callback):
        """Mock conflict dialog - store callback for testing"""
        self.last_conflict_callback = callback


class TestConflictCancellation(unittest.TestCase):
    """Test ESC key cancellation during conflict resolution"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = StdPath(self.test_dir) / "source"
        self.dest_dir = StdPath(self.test_dir) / "dest"
        self.source_dir.mkdir()
        self.dest_dir.mkdir()
        
        # Create test files
        self.source_file = self.source_dir / "test.txt"
        self.source_file.write_text("source content")
        
        # Create conflicting file in destination
        self.dest_file = self.dest_dir / "test.txt"
        self.dest_file.write_text("dest content")
        
        # Create mock components
        self.mock_fm = MockFileManager()
        self.mock_ui = MockUI()
        
        # Create task
        self.task = FileOperationTask(self.mock_fm, self.mock_ui, executor=None)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    
    def test_esc_cancels_during_conflict_resolution(self):
        """Test that ESC key cancels the entire operation during conflict resolution"""
        # Start a copy operation that will have conflicts
        files = [TFMPath(self.source_file)]
        destination = TFMPath(self.dest_dir)
        
        self.task.start_operation('copy', files, destination)
        
        # Task should be in RESOLVING_CONFLICT state
        self.assertEqual(self.task.state, State.RESOLVING_CONFLICT)
        self.assertIsNotNone(self.task.context)
        self.assertEqual(len(self.task.context.conflicts), 1)
        
        # Verify conflict dialog was shown
        self.assertIsNotNone(self.mock_ui.last_conflict_callback)
        
        # Simulate ESC key press (callback called with None)
        self.mock_ui.last_conflict_callback(None, False)
        
        # Task should be cancelled and in IDLE state
        self.assertEqual(self.task.state, State.IDLE)
        self.assertIsNone(self.task.context)
        self.assertTrue(self.mock_fm.task_cleared)
    
    def test_esc_cancels_with_multiple_conflicts(self):
        """Test that ESC cancels even when there are multiple conflicts"""
        # Create multiple source files
        source_file2 = self.source_dir / "test2.txt"
        source_file2.write_text("source content 2")
        dest_file2 = self.dest_dir / "test2.txt"
        dest_file2.write_text("dest content 2")
        
        # Start operation with multiple conflicts
        files = [TFMPath(self.source_file), TFMPath(source_file2)]
        destination = TFMPath(self.dest_dir)
        
        self.task.start_operation('copy', files, destination)
        
        # Task should be in RESOLVING_CONFLICT state with 2 conflicts
        self.assertEqual(self.task.state, State.RESOLVING_CONFLICT)
        self.assertEqual(len(self.task.context.conflicts), 2)
        self.assertEqual(self.task.context.current_conflict_index, 0)
        
        # Simulate ESC key press on first conflict
        self.mock_ui.last_conflict_callback(None, False)
        
        # Task should be cancelled immediately (not proceed to second conflict)
        self.assertEqual(self.task.state, State.IDLE)
        self.assertIsNone(self.task.context)
        self.assertTrue(self.mock_fm.task_cleared)
    
    def test_normal_choices_still_work(self):
        """Test that normal conflict resolution choices still work after adding ESC support"""
        # Start a copy operation with conflict
        files = [TFMPath(self.source_file)]
        destination = TFMPath(self.dest_dir)
        
        self.task.start_operation('copy', files, destination)
        
        # Task should be in RESOLVING_CONFLICT state
        self.assertEqual(self.task.state, State.RESOLVING_CONFLICT)
        initial_context = self.task.context
        
        # Simulate choosing "skip"
        self.mock_ui.last_conflict_callback('skip', False)
        
        # Verify the skip was recorded (check before execution clears context)
        # The task will have moved to next state, but we verified skip was processed
        self.assertEqual(len(initial_context.results['skipped']), 1)


if __name__ == '__main__':
    unittest.main()
