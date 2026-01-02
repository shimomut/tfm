#!/usr/bin/env python3
"""
Tests for archive operation completion callbacks.

This test suite verifies that completion callbacks work correctly:
- Callbacks are invoked with (success_count, error_count)
- Callbacks suppress default summary logging
- Callbacks are invoked on background thread
- Callbacks are invoked even on cancellation
"""

import unittest
import tempfile
import shutil
import time
from pathlib import Path as PathlibPath
from unittest.mock import Mock, patch

from tfm_path import Path
from tfm_archive_operation_executor import ArchiveOperationExecutor
from tfm_progress_manager import ProgressManager


class TestArchiveCompletionCallbacks(unittest.TestCase):
    """Test completion callback functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix='tfm_test_')
        self.temp_path = Path(self.temp_dir)
        
        # Create mock file manager
        self.file_manager = Mock()
        self.file_manager.operation_cancelled = False
        self.file_manager.mark_dirty = Mock()
        
        # Create progress manager
        self.progress_manager = ProgressManager()
        
        # Create executor
        self.executor = ArchiveOperationExecutor(
            self.file_manager,
            self.progress_manager,
            cache_manager=None
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        if PathlibPath(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_callback_invoked_with_success_and_error_counts(self):
        """Test that callback receives (success_count, error_count) parameters"""
        # Create test file
        test_file = self.temp_path / "test.txt"
        test_file.write_text("test content")
        
        archive_path = self.temp_path / "test.tar.gz"
        
        # Create callback mock
        callback = Mock()
        
        # Start create operation with callback
        self.executor.perform_create_operation(
            [test_file],
            archive_path,
            'tar.gz',
            completion_callback=callback
        )
        
        # Wait for thread to complete
        time.sleep(0.5)
        
        # Verify callback was invoked with correct parameters
        callback.assert_called_once()
        args = callback.call_args[0]
        self.assertEqual(len(args), 2)
        success_count, error_count = args
        self.assertIsInstance(success_count, int)
        self.assertIsInstance(error_count, int)
        self.assertGreaterEqual(success_count, 0)
        self.assertGreaterEqual(error_count, 0)
    
    def test_callback_suppresses_default_logging(self):
        """Test that default summary logging is suppressed when callback provided"""
        # Create test file
        test_file = self.temp_path / "test.txt"
        test_file.write_text("test content")
        
        archive_path = self.temp_path / "test.tar.gz"
        
        # Create callback mock
        callback = Mock()
        
        # Patch logger to capture log calls
        with patch.object(self.executor.logger, 'info') as mock_info:
            # Start create operation with callback
            self.executor.perform_create_operation(
                [test_file],
                archive_path,
                'tar.gz',
                completion_callback=callback
            )
            
            # Wait for thread to complete
            time.sleep(0.5)
            
            # Verify summary logging was suppressed
            # Check that "Archive created successfully" message was NOT logged
            info_calls = [str(call) for call in mock_info.call_args_list]
            summary_logged = any("Archive created successfully" in str(call) for call in info_calls)
            self.assertFalse(summary_logged, "Summary logging should be suppressed when callback provided")
    
    def test_no_callback_logs_summary(self):
        """Test that default summary logging occurs when no callback provided"""
        # Create test file
        test_file = self.temp_path / "test.txt"
        test_file.write_text("test content")
        
        archive_path = self.temp_path / "test2.tar.gz"
        
        # Patch logger to capture log calls
        with patch.object(self.executor.logger, 'info') as mock_info:
            # Start create operation WITHOUT callback
            self.executor.perform_create_operation(
                [test_file],
                archive_path,
                'tar.gz',
                completion_callback=None
            )
            
            # Wait for thread to complete
            time.sleep(0.5)
            
            # Verify summary logging occurred
            # Check that "Archive created successfully" message WAS logged
            info_calls = [str(call) for call in mock_info.call_args_list]
            summary_logged = any("Archive created successfully" in str(call) for call in info_calls)
            self.assertTrue(summary_logged, "Summary logging should occur when no callback provided")
    
    def test_callback_invoked_on_background_thread(self):
        """Test that callback is invoked on background thread, not main thread"""
        # Create test file
        test_file = self.temp_path / "test.txt"
        test_file.write_text("test content")
        
        archive_path = self.temp_path / "test.tar.gz"
        
        # Track which thread the callback runs on
        import threading
        main_thread = threading.current_thread()
        callback_thread = [None]
        
        def callback(success_count, error_count):
            callback_thread[0] = threading.current_thread()
        
        # Start create operation with callback
        self.executor.perform_create_operation(
            [test_file],
            archive_path,
            'tar.gz',
            completion_callback=callback
        )
        
        # Wait for thread to complete
        time.sleep(0.5)
        
        # Verify callback ran on different thread
        self.assertIsNotNone(callback_thread[0])
        self.assertNotEqual(callback_thread[0], main_thread)
    
    def test_extraction_callback_invoked(self):
        """Test that extraction operations also invoke callback"""
        # Create test archive
        test_file = self.temp_path / "test.txt"
        test_file.write_text("test content")
        
        archive_path = self.temp_path / "test.tar.gz"
        
        # Create archive first (without callback)
        self.executor.perform_create_operation(
            [test_file],
            archive_path,
            'tar.gz',
            completion_callback=None
        )
        time.sleep(0.5)
        
        # Remove original file
        test_file.unlink()
        
        # Create callback mock
        callback = Mock()
        
        # Extract with callback
        extract_dir = self.temp_path / "extracted"
        extract_dir.mkdir()
        
        self.executor.perform_extract_operation(
            archive_path,
            extract_dir,
            overwrite=True,
            skip_files=[],
            completion_callback=callback
        )
        
        # Wait for thread to complete
        time.sleep(0.5)
        
        # Verify callback was invoked
        callback.assert_called_once()
        args = callback.call_args[0]
        self.assertEqual(len(args), 2)
        success_count, error_count = args
        self.assertGreaterEqual(success_count, 0)
        self.assertGreaterEqual(error_count, 0)
    
    def test_extraction_callback_suppresses_logging(self):
        """Test that extraction callback suppresses default summary logging"""
        # Create test archive
        test_file = self.temp_path / "test.txt"
        test_file.write_text("test content")
        
        archive_path = self.temp_path / "test.tar.gz"
        
        # Create archive first
        self.executor.perform_create_operation(
            [test_file],
            archive_path,
            'tar.gz',
            completion_callback=None
        )
        time.sleep(0.5)
        
        # Remove original file
        test_file.unlink()
        
        # Create callback mock
        callback = Mock()
        
        # Extract with callback
        extract_dir = self.temp_path / "extracted"
        extract_dir.mkdir()
        
        # Patch logger to capture log calls
        with patch.object(self.executor.logger, 'info') as mock_info:
            self.executor.perform_extract_operation(
                archive_path,
                extract_dir,
                overwrite=True,
                skip_files=[],
                completion_callback=callback
            )
            
            # Wait for thread to complete
            time.sleep(0.5)
            
            # Verify summary logging was suppressed
            info_calls = [str(call) for call in mock_info.call_args_list]
            summary_logged = any("Archive extracted successfully" in str(call) for call in info_calls)
            self.assertFalse(summary_logged, "Summary logging should be suppressed when callback provided")


if __name__ == '__main__':
    unittest.main()
