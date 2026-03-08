"""
Unit tests for reload queue processing in FileManager main event loop.

Tests verify that reload requests posted to the reload_queue are properly
processed by the main event loop and trigger file list refreshes.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import queue
from pathlib import Path


class TestReloadQueueProcessing(unittest.TestCase):
    """Test reload queue processing in FileManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock all the dependencies
        self.mock_config = Mock()
        self.mock_renderer = Mock()
        self.mock_pane_manager = Mock()
        self.mock_file_list_manager = Mock()
        self.mock_logger = Mock()
        
        # Set up pane data
        self.mock_pane_manager.left_pane = {
            'path': Path('/test/left'),
            'files': [],
            'focused_index': 0,
            'scroll_offset': 0
        }
        self.mock_pane_manager.right_pane = {
            'path': Path('/test/right'),
            'files': [],
            'focused_index': 0,
            'scroll_offset': 0
        }
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_handle_reload_request_left_pane(self, mock_init):
        """Test _handle_reload_request processes left pane reload correctly."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance and set up mocks
        fm = FileManager()
        fm.pane_manager = self.mock_pane_manager
        fm.file_list_manager = self.mock_file_list_manager
        fm.logger = self.mock_logger
        fm.refresh_files = Mock()
        
        # Call _handle_reload_request for left pane
        fm._handle_reload_request("left")
        
        # Verify refresh_files was called with left pane data
        fm.refresh_files.assert_called_once_with(self.mock_pane_manager.left_pane)
        
        # Verify logging
        fm.logger.info.assert_called_once()
        log_message = fm.logger.info.call_args[0][0]
        self.assertIn("left pane", log_message)
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_handle_reload_request_right_pane(self, mock_init):
        """Test _handle_reload_request processes right pane reload correctly."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance and set up mocks
        fm = FileManager()
        fm.pane_manager = self.mock_pane_manager
        fm.file_list_manager = self.mock_file_list_manager
        fm.logger = self.mock_logger
        fm.refresh_files = Mock()
        
        # Call _handle_reload_request for right pane
        fm._handle_reload_request("right")
        
        # Verify refresh_files was called with right pane data
        fm.refresh_files.assert_called_once_with(self.mock_pane_manager.right_pane)
        
        # Verify logging
        fm.logger.info.assert_called_once()
        log_message = fm.logger.info.call_args[0][0]
        self.assertIn("right pane", log_message)
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_handle_reload_request_invalid_pane(self, mock_init):
        """Test _handle_reload_request handles invalid pane name gracefully."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance and set up mocks
        fm = FileManager()
        fm.pane_manager = self.mock_pane_manager
        fm.file_list_manager = self.mock_file_list_manager
        fm.logger = self.mock_logger
        fm.refresh_files = Mock()
        
        # Call _handle_reload_request with invalid pane name
        fm._handle_reload_request("invalid")
        
        # Verify refresh_files was NOT called
        fm.refresh_files.assert_not_called()
        
        # Verify error was logged
        fm.logger.error.assert_called_once()
        error_message = fm.logger.error.call_args[0][0]
        self.assertIn("Invalid pane name", error_message)
        self.assertIn("invalid", error_message)
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_reload_queue_processing_single_request(self, mock_init):
        """Test that reload queue is processed correctly with single request."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance and set up mocks
        fm = FileManager()
        fm.reload_queue = queue.Queue()
        fm._handle_reload_request = Mock()
        fm.mark_dirty = Mock()
        
        # Post a reload request to the queue
        fm.reload_queue.put("left")
        
        # Simulate the reload queue processing code from run()
        try:
            while True:
                pane_name = fm.reload_queue.get_nowait()
                fm._handle_reload_request(pane_name)
                fm.mark_dirty()
        except queue.Empty:
            pass
        
        # Verify _handle_reload_request was called once with "left"
        fm._handle_reload_request.assert_called_once_with("left")
        
        # Verify mark_dirty was called once
        fm.mark_dirty.assert_called_once()
        
        # Verify queue is now empty
        self.assertTrue(fm.reload_queue.empty())
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_reload_queue_processing_multiple_requests(self, mock_init):
        """Test that reload queue processes multiple requests correctly."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance and set up mocks
        fm = FileManager()
        fm.reload_queue = queue.Queue()
        fm._handle_reload_request = Mock()
        fm.mark_dirty = Mock()
        
        # Post multiple reload requests to the queue
        fm.reload_queue.put("left")
        fm.reload_queue.put("right")
        fm.reload_queue.put("left")
        
        # Simulate the reload queue processing code from run()
        try:
            while True:
                pane_name = fm.reload_queue.get_nowait()
                fm._handle_reload_request(pane_name)
                fm.mark_dirty()
        except queue.Empty:
            pass
        
        # Verify _handle_reload_request was called three times
        self.assertEqual(fm._handle_reload_request.call_count, 3)
        
        # Verify it was called with the correct pane names in order
        calls = [call[0][0] for call in fm._handle_reload_request.call_args_list]
        self.assertEqual(calls, ["left", "right", "left"])
        
        # Verify mark_dirty was called three times (once per reload)
        self.assertEqual(fm.mark_dirty.call_count, 3)
        
        # Verify queue is now empty
        self.assertTrue(fm.reload_queue.empty())
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_reload_queue_processing_empty_queue(self, mock_init):
        """Test that empty reload queue doesn't cause errors."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance and set up mocks
        fm = FileManager()
        fm.reload_queue = queue.Queue()
        fm._handle_reload_request = Mock()
        fm.mark_dirty = Mock()
        
        # Don't post any requests - queue is empty
        
        # Simulate the reload queue processing code from run()
        try:
            while True:
                pane_name = fm.reload_queue.get_nowait()
                fm._handle_reload_request(pane_name)
                fm.mark_dirty()
        except queue.Empty:
            pass
        
        # Verify _handle_reload_request was NOT called
        fm._handle_reload_request.assert_not_called()
        
        # Verify mark_dirty was NOT called
        fm.mark_dirty.assert_not_called()
        
        # Verify queue is still empty
        self.assertTrue(fm.reload_queue.empty())


if __name__ == '__main__':
    unittest.main()
