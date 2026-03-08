"""
Test suite for toggle_monitoring() method in FileManager.

This test verifies that the toggle_monitoring() method correctly enables
and disables file monitoring at runtime, updates configuration state,
and logs state changes appropriately.

Validates: Requirement 10.4
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil


class TestToggleMonitoring(unittest.TestCase):
    """Test suite for FileManager.toggle_monitoring() method."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.left_path = Path(self.temp_dir) / "left"
        self.right_path = Path(self.temp_dir) / "right"
        self.left_path.mkdir()
        self.right_path.mkdir()
        
        # Create mock configuration
        self.mock_config = Mock()
        self.mock_config.FILE_MONITORING_ENABLED = True
        self.mock_config.FILE_MONITORING_COALESCE_DELAY_MS = 200
        self.mock_config.FILE_MONITORING_MAX_RELOADS_PER_SECOND = 5
        
        # Create mock file manager with minimal setup
        self.mock_file_manager = Mock()
        self.mock_file_manager.config = self.mock_config
        self.mock_file_manager.reload_queue = Mock()
        
        # Create mock logger
        self.mock_logger = Mock()
        self.mock_file_manager.logger = self.mock_logger
        
        # Create mock pane manager with paths
        self.mock_pane_manager = Mock()
        self.mock_pane_manager.left_pane = {'path': self.left_path}
        self.mock_pane_manager.right_pane = {'path': self.right_path}
        self.mock_file_manager.pane_manager = self.mock_pane_manager
        
        # Create mock file monitor manager
        self.mock_monitor_manager = Mock()
        self.mock_file_manager.file_monitor_manager = self.mock_monitor_manager
        
        # Mock mark_dirty method
        self.mock_file_manager.mark_dirty = Mock()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_toggle_monitoring_disables_when_enabled(self):
        """Test that toggle_monitoring disables monitoring when currently enabled."""
        # Set up: monitoring is currently enabled
        self.mock_monitor_manager.is_monitoring_enabled.return_value = True
        
        # Import and bind the method to our mock
        from tfm_main import FileManager
        FileManager.toggle_monitoring(self.mock_file_manager)
        
        # Verify stop_monitoring was called
        self.mock_monitor_manager.stop_monitoring.assert_called_once()
        
        # Verify configuration was updated
        self.assertFalse(self.mock_config.FILE_MONITORING_ENABLED)
        
        # Verify log message
        self.mock_logger.info.assert_called_with("File monitoring disabled")
        
        # Verify UI was marked dirty
        self.mock_file_manager.mark_dirty.assert_called_once()
    
    def test_toggle_monitoring_enables_when_disabled(self):
        """Test that toggle_monitoring enables monitoring when currently disabled."""
        # Set up: monitoring is currently disabled
        self.mock_monitor_manager.is_monitoring_enabled.return_value = False
        
        # Import and bind the method to our mock
        from tfm_main import FileManager
        FileManager.toggle_monitoring(self.mock_file_manager)
        
        # Verify configuration was updated first
        self.assertTrue(self.mock_config.FILE_MONITORING_ENABLED)
        
        # Verify enabled flag was set on monitor manager
        self.assertTrue(self.mock_monitor_manager.enabled)
        
        # Verify start_monitoring was called with both pane paths
        self.mock_monitor_manager.start_monitoring.assert_called_once_with(
            self.left_path,
            self.right_path
        )
        
        # Verify log message
        self.mock_logger.info.assert_called_with("File monitoring enabled")
        
        # Verify UI was marked dirty
        self.mock_file_manager.mark_dirty.assert_called_once()
    
    def test_toggle_monitoring_twice_returns_to_original_state(self):
        """Test that toggling twice returns to the original state."""
        # Set up: monitoring is currently enabled
        self.mock_monitor_manager.is_monitoring_enabled.return_value = True
        
        # Import the method
        from tfm_main import FileManager
        
        # First toggle: disable
        FileManager.toggle_monitoring(self.mock_file_manager)
        self.assertFalse(self.mock_config.FILE_MONITORING_ENABLED)
        
        # Update mock to reflect new state
        self.mock_monitor_manager.is_monitoring_enabled.return_value = False
        
        # Second toggle: enable
        FileManager.toggle_monitoring(self.mock_file_manager)
        self.assertTrue(self.mock_config.FILE_MONITORING_ENABLED)
        
        # Verify both operations occurred
        self.mock_monitor_manager.stop_monitoring.assert_called_once()
        self.mock_monitor_manager.start_monitoring.assert_called_once()
    
    def test_toggle_monitoring_logs_correct_messages(self):
        """Test that toggle_monitoring logs appropriate messages for both states."""
        from tfm_main import FileManager
        
        # Test disabling
        self.mock_monitor_manager.is_monitoring_enabled.return_value = True
        FileManager.toggle_monitoring(self.mock_file_manager)
        self.mock_logger.info.assert_called_with("File monitoring disabled")
        
        # Reset mock
        self.mock_logger.reset_mock()
        
        # Test enabling
        self.mock_monitor_manager.is_monitoring_enabled.return_value = False
        FileManager.toggle_monitoring(self.mock_file_manager)
        self.mock_logger.info.assert_called_with("File monitoring enabled")
    
    def test_toggle_monitoring_updates_config_state(self):
        """Test that toggle_monitoring updates the configuration state correctly."""
        from tfm_main import FileManager
        
        # Test disabling updates config
        self.mock_monitor_manager.is_monitoring_enabled.return_value = True
        initial_state = self.mock_config.FILE_MONITORING_ENABLED
        FileManager.toggle_monitoring(self.mock_file_manager)
        self.assertNotEqual(self.mock_config.FILE_MONITORING_ENABLED, initial_state)
        self.assertFalse(self.mock_config.FILE_MONITORING_ENABLED)
        
        # Test enabling updates config
        self.mock_monitor_manager.is_monitoring_enabled.return_value = False
        FileManager.toggle_monitoring(self.mock_file_manager)
        self.assertTrue(self.mock_config.FILE_MONITORING_ENABLED)
    
    def test_toggle_monitoring_marks_ui_dirty(self):
        """Test that toggle_monitoring always marks the UI as dirty."""
        from tfm_main import FileManager
        
        # Test when disabling
        self.mock_monitor_manager.is_monitoring_enabled.return_value = True
        FileManager.toggle_monitoring(self.mock_file_manager)
        self.mock_file_manager.mark_dirty.assert_called()
        
        # Reset mock
        self.mock_file_manager.mark_dirty.reset_mock()
        
        # Test when enabling
        self.mock_monitor_manager.is_monitoring_enabled.return_value = False
        FileManager.toggle_monitoring(self.mock_file_manager)
        self.mock_file_manager.mark_dirty.assert_called()


if __name__ == '__main__':
    unittest.main()
