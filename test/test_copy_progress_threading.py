"""
Test: Enhanced Copy Progress with Threading

Tests the improved copy operation progress tracking system.

Run with: PYTHONPATH=.:src:ttk pytest test/test_copy_progress_threading.py -v
"""

import time
import tempfile
import unittest
import threading

from tfm_path import Path
from tfm_progress_manager import ProgressManager, OperationType
from tfm_progress_animator import ProgressAnimator


class TestProgressAnimator(unittest.TestCase):
    """Test the progress animator"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create minimal config for animator
        class MinimalConfig:
            PROGRESS_ANIMATION_PATTERN = 'spinner'
            PROGRESS_ANIMATION_SPEED = 0.08
        self.config = MinimalConfig()
    
    def test_animator_initialization(self):
        """Test animator initializes correctly"""
        animator = ProgressAnimator(self.config)
        self.assertEqual(animator.frame_index, 0)
        self.assertIn('spinner', animator.patterns)
    
    def test_animator_frame_cycling(self):
        """Test animator cycles through frames"""
        animator = ProgressAnimator(self.config)
        
        # Get first frame
        frame1 = animator.get_current_frame()
        pattern = animator.patterns['spinner']
        self.assertIn(frame1, pattern)
        
        # Force time to pass
        animator.last_update_time = 0
        
        # Get next frame
        frame2 = animator.get_current_frame()
        self.assertIn(frame2, pattern)
    
    def test_animator_reset(self):
        """Test animator reset"""
        animator = ProgressAnimator(self.config)
        
        # Advance a few frames
        for _ in range(5):
            animator.last_update_time = 0
            animator.get_current_frame()
        
        # Reset
        animator.reset()
        self.assertEqual(animator.frame_index, 0)
        self.assertEqual(animator.last_update_time, 0)


class TestProgressManager(unittest.TestCase):
    """Test the progress manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.progress_manager = ProgressManager()
        self.callback_count = 0
        self.last_progress_data = None
    
    def progress_callback(self, progress_data):
        """Test callback for progress updates"""
        self.callback_count += 1
        self.last_progress_data = progress_data
    
    def test_start_operation(self):
        """Test starting an operation"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            100,
            "test",
            self.progress_callback
        )
        
        self.assertTrue(self.progress_manager.is_operation_active())
        self.assertEqual(self.callback_count, 1)
        self.assertIsNotNone(self.last_progress_data)
        self.assertEqual(self.last_progress_data['total_items'], 100)
        self.assertEqual(self.last_progress_data['processed_items'], 0)
    
    def test_update_progress(self):
        """Test updating progress"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            10,
            "test",
            self.progress_callback
        )
        
        # Update progress
        self.progress_manager.update_progress("file1.txt", 1)
        
        self.assertEqual(self.last_progress_data['processed_items'], 1)
        self.assertEqual(self.last_progress_data['current_item'], "file1.txt")
        self.assertEqual(self.last_progress_data['file_bytes_copied'], 0)
        self.assertEqual(self.last_progress_data['file_bytes_total'], 0)
    
    def test_update_file_byte_progress(self):
        """Test updating byte-level progress"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            1,
            "test",
            self.progress_callback
        )
        
        self.progress_manager.update_progress("large_file.dat", 1)
        # Simulate copying 50MB of a 100MB file
        self.progress_manager.update_file_byte_progress(50 * 1024 * 1024, 100 * 1024 * 1024)
        
        self.assertEqual(self.last_progress_data['file_bytes_copied'], 50 * 1024 * 1024)
        self.assertEqual(self.last_progress_data['file_bytes_total'], 100 * 1024 * 1024)
    
    def test_increment_errors(self):
        """Test error counting"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            10,
            "test",
            self.progress_callback
        )
        
        self.progress_manager.increment_errors()
        self.progress_manager.increment_errors()
        
        self.assertEqual(self.last_progress_data['errors'], 2)
    
    def test_finish_operation(self):
        """Test finishing an operation"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            10,
            "test",
            self.progress_callback
        )
        
        self.progress_manager.finish_operation()
        
        self.assertFalse(self.progress_manager.is_operation_active())
        self.assertIsNone(self.last_progress_data)
    
    def test_get_progress_percentage(self):
        """Test progress percentage calculation"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            100,
            "test"
        )
        
        self.assertEqual(self.progress_manager.get_progress_percentage(), 0)
        
        self.progress_manager.update_progress("file1.txt", 25)
        self.assertEqual(self.progress_manager.get_progress_percentage(), 25)
        
        self.progress_manager.update_progress("file2.txt", 50)
        self.assertEqual(self.progress_manager.get_progress_percentage(), 50)
        
        self.progress_manager.update_progress("file3.txt", 100)
        self.assertEqual(self.progress_manager.get_progress_percentage(), 100)
    
    def test_get_progress_text(self):
        """Test progress text formatting"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            100,
            "to destination"
        )
        
        self.progress_manager.update_progress("file1.txt", 25)
        
        progress_text = self.progress_manager.get_progress_text(max_width=80)
        
        # Check that text contains expected components
        self.assertIn("Copying", progress_text)
        self.assertIn("25/100", progress_text)
        self.assertIn("file1.txt", progress_text)
        # Should NOT contain percentage anymore
        self.assertNotIn("%", progress_text)
    
    def test_get_progress_text_with_byte_progress(self):
        """Test progress text with byte-level progress"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            1,
            "to destination"
        )
        
        self.progress_manager.update_progress("large_file.dat", 1)
        # Simulate copying 15MB of a 32GB file
        self.progress_manager.update_file_byte_progress(15 * 1024 * 1024, 32 * 1024 * 1024 * 1024)
        
        progress_text = self.progress_manager.get_progress_text(max_width=80)
        
        # Check that text contains byte progress in human-readable format
        self.assertIn("[15M/32", progress_text)  # Should show "15M/32.0G" or similar
        self.assertIn("G]", progress_text)
    
    def test_progress_throttling(self):
        """Test that progress updates are throttled"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            100,
            "test",
            self.progress_callback
        )
        
        initial_count = self.callback_count
        
        # Rapid updates should be throttled
        for i in range(10):
            self.progress_manager.update_progress(f"file{i}.txt", i + 1)
        
        # Should have fewer callbacks than updates due to throttling
        self.assertLess(self.callback_count - initial_count, 10)


class TestCopyProgressIntegration(unittest.TestCase):
    """Integration tests for copy progress"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.temp_dir) / "source"
        self.dest_dir = Path(self.temp_dir) / "dest"
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.dest_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_files(self, count=10):
        """Create test files"""
        for i in range(count):
            file_path = self.source_dir / f"file_{i}.txt"
            with open(str(file_path), 'w') as f:
                f.write(f"Test file {i}\n" * 100)
    
    def test_file_counting(self):
        """Test recursive file counting"""
        self.create_test_files(5)
        
        # Create subdirectory with files
        subdir = self.source_dir / "subdir"
        subdir.mkdir(exist_ok=True)
        for i in range(3):
            file_path = subdir / f"sub_file_{i}.txt"
            with open(str(file_path), 'w') as f:
                f.write(f"Sub file {i}\n")
        
        # Count files
        from tfm_file_operation_ui import FileOperationUI
        
        # Create a mock file manager
        class MockFileManager:
            def __init__(self):
                self.progress_manager = ProgressManager()
                self.log_manager = None
                self.cache_manager = None
                self.config = None
        
        file_manager = MockFileManager()
        file_ops_ui = FileOperationUI(file_manager, None)
        
        total_files = file_ops_ui._count_files_recursively([self.source_dir])
        
        # Should count 5 files in root + 3 files in subdir = 8 files
        self.assertEqual(total_files, 8)
    
    def test_progress_updates_in_thread(self):
        """Test that progress updates work in background thread"""
        self.create_test_files(5)
        
        progress_manager = ProgressManager()
        updates_received = []
        
        def callback(progress_data):
            if progress_data:
                updates_received.append(progress_data.copy())
        
        # Start operation
        progress_manager.start_operation(
            OperationType.COPY,
            5,
            "test",
            callback
        )
        
        # Simulate updates from background thread
        def update_thread():
            for i in range(5):
                progress_manager.update_progress(f"file_{i}.txt", i + 1)
                time.sleep(0.01)
            progress_manager.finish_operation()
        
        thread = threading.Thread(target=update_thread)
        thread.start()
        thread.join(timeout=2)
        
        # Should have received multiple updates
        self.assertGreater(len(updates_received), 0)
        
        # Last update should show all files processed
        if updates_received:
            last_update = updates_received[-1]
            self.assertEqual(last_update['processed_items'], 5)


class TestProgressTextFormatting(unittest.TestCase):
    """Test progress text formatting edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.progress_manager = ProgressManager()
    
    def test_long_filename_truncation(self):
        """Test that long filenames are truncated"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            1,
            "test"
        )
        
        long_filename = "a" * 200 + ".txt"
        self.progress_manager.update_progress(long_filename, 1)
        
        progress_text = self.progress_manager.get_progress_text(max_width=80)
        
        # Text should fit within max width
        self.assertLessEqual(len(progress_text), 80)
        
        # Should contain truncation indicator
        self.assertIn("...", progress_text)
    
    def test_empty_description(self):
        """Test progress text with empty description"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            10,
            ""
        )
        
        self.progress_manager.update_progress("file.txt", 5)
        
        progress_text = self.progress_manager.get_progress_text(max_width=80)
        
        # Should still format correctly
        self.assertIn("Copying", progress_text)
        self.assertIn("5/10", progress_text)
    
    def test_zero_total_items(self):
        """Test progress with zero total items"""
        self.progress_manager.start_operation(
            OperationType.COPY,
            0,
            "test"
        )
        
        percentage = self.progress_manager.get_progress_percentage()
        self.assertEqual(percentage, 0)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestProgressAnimator))
    suite.addTests(loader.loadTestsFromTestCase(TestProgressManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCopyProgressIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestProgressTextFormatting))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()
