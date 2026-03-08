"""
Test that file monitoring is updated when application state is restored.

This test verifies that when TFM restores saved pane paths during startup,
the file monitoring is updated to watch the restored directories instead of
the initial directories.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import tempfile
import shutil


class TestStateRestorationMonitoringUpdate(unittest.TestCase):
    """Test file monitoring updates during state restoration"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.initial_left = Path(self.temp_dir) / "initial_left"
        self.initial_right = Path(self.temp_dir) / "initial_right"
        self.restored_left = Path(self.temp_dir) / "restored_left"
        self.restored_right = Path(self.temp_dir) / "restored_right"
        
        # Create all directories
        self.initial_left.mkdir()
        self.initial_right.mkdir()
        self.restored_left.mkdir()
        self.restored_right.mkdir()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.tfm_main.FileMonitorManager')
    @patch('src.tfm_main.get_state_manager')
    @patch('src.tfm_main.get_config')
    def test_monitoring_updated_after_state_restoration(self, mock_get_config, mock_get_state_manager, mock_monitor_class):
        """Test that monitoring is updated to watch restored directories"""
        # Set up mocks
        mock_config = Mock()
        mock_config.FILE_MONITORING = {
            'enabled': True,
            'coalesce_delay_ms': 200,
            'max_reloads_per_second': 5,
            'suppress_after_action_ms': 1000,
            'fallback_poll_interval_s': 5
        }
        mock_get_config.return_value = mock_config
        
        # Mock state manager to return restored paths
        mock_state_manager = Mock()
        mock_get_state_manager.return_value = mock_state_manager
        mock_state_manager.load_window_layout.return_value = None
        mock_state_manager.load_pane_state.side_effect = [
            {'path': str(self.restored_left), 'sort_mode': 'name', 'sort_reverse': False, 'filter_pattern': ''},
            {'path': str(self.restored_right), 'sort_mode': 'name', 'sort_reverse': False, 'filter_pattern': ''}
        ]
        
        # Mock file monitor manager
        mock_monitor = Mock()
        mock_monitor.is_monitoring_enabled.return_value = True
        mock_monitor_class.return_value = mock_monitor
        
        # Import and create FileManager with initial directories
        from src.tfm_main import FileManager
        
        # Mock renderer
        mock_renderer = Mock()
        mock_renderer.is_desktop_mode.return_value = False
        mock_renderer.get_dimensions.return_value = (24, 80)
        
        # Create FileManager (this will call load_application_state)
        with patch('src.tfm_main.LogManager'), \
             patch('tfm_log_manager.set_log_manager'), \
             patch('src.tfm_main.init_colors'), \
             patch('src.tfm_main.PaneManager'), \
             patch('src.tfm_main.FileListManager'), \
             patch('src.tfm_main.ListDialog'), \
             patch('src.tfm_main.InfoDialog'), \
             patch('src.tfm_main.AboutDialog'), \
             patch('src.tfm_main.SearchDialog'), \
             patch('src.tfm_main.DrivesDialog'), \
             patch('src.tfm_main.BatchRenameDialog'), \
             patch('src.tfm_main.QuickChoiceBar'), \
             patch('src.tfm_main.QuickEditBar'), \
             patch('src.tfm_main.ExternalProgramManager'), \
             patch('src.tfm_main.AdaptiveFPSManager'), \
             patch('src.tfm_main.UILayerStack'), \
             patch.object(FileManager, 'refresh_files'), \
             patch.object(FileManager, 'restore_startup_cursor_positions'), \
             patch.object(FileManager, '_create_user_directories'):
            
            fm = FileManager(
                mock_renderer,
                left_dir=str(self.initial_left),
                right_dir=str(self.initial_right)
            )
        
        # Verify that start_monitoring was called with initial directories
        mock_monitor.start_monitoring.assert_called_once()
        
        # Verify that update_monitored_directory was called for both panes
        # This should happen during load_application_state
        assert mock_monitor.update_monitored_directory.call_count == 2
        
        # Verify the calls were made with 'left' and 'right' pane names
        calls = mock_monitor.update_monitored_directory.call_args_list
        assert calls[0][0][0] == 'left'  # First call with 'left'
        assert calls[1][0][0] == 'right'  # Second call with 'right'
        
        # Verify is_monitoring_enabled was checked before updating
        mock_monitor.is_monitoring_enabled.assert_called()
    
    @patch('src.tfm_main.FileMonitorManager')
    @patch('src.tfm_main.get_state_manager')
    @patch('src.tfm_main.get_config')
    def test_monitoring_not_updated_when_disabled(self, mock_get_config, mock_get_state_manager, mock_monitor_class):
        """Test that monitoring is not updated when disabled"""
        # Set up mocks
        mock_config = Mock()
        mock_config.FILE_MONITORING = {
            'enabled': False,
            'coalesce_delay_ms': 200,
            'max_reloads_per_second': 5,
            'suppress_after_action_ms': 1000,
            'fallback_poll_interval_s': 5
        }
        mock_get_config.return_value = mock_config
        
        # Mock state manager to return restored paths
        mock_state_manager = Mock()
        mock_get_state_manager.return_value = mock_state_manager
        mock_state_manager.load_window_layout.return_value = None
        mock_state_manager.load_pane_state.side_effect = [
            {'path': str(self.restored_left), 'sort_mode': 'name', 'sort_reverse': False, 'filter_pattern': ''},
            {'path': str(self.restored_right), 'sort_mode': 'name', 'sort_reverse': False, 'filter_pattern': ''}
        ]
        
        # Mock file monitor manager (disabled)
        mock_monitor = Mock()
        mock_monitor.is_monitoring_enabled.return_value = False
        mock_monitor_class.return_value = mock_monitor
        
        # Import and create FileManager
        from src.tfm_main import FileManager
        
        # Mock renderer
        mock_renderer = Mock()
        mock_renderer.is_desktop_mode.return_value = False
        mock_renderer.get_dimensions.return_value = (24, 80)
        
        # Create FileManager
        with patch('src.tfm_main.LogManager'), \
             patch('tfm_log_manager.set_log_manager'), \
             patch('src.tfm_main.init_colors'), \
             patch('src.tfm_main.PaneManager'), \
             patch('src.tfm_main.FileListManager'), \
             patch('src.tfm_main.ListDialog'), \
             patch('src.tfm_main.InfoDialog'), \
             patch('src.tfm_main.AboutDialog'), \
             patch('src.tfm_main.SearchDialog'), \
             patch('src.tfm_main.DrivesDialog'), \
             patch('src.tfm_main.BatchRenameDialog'), \
             patch('src.tfm_main.QuickChoiceBar'), \
             patch('src.tfm_main.QuickEditBar'), \
             patch('src.tfm_main.ExternalProgramManager'), \
             patch('src.tfm_main.AdaptiveFPSManager'), \
             patch('src.tfm_main.UILayerStack'), \
             patch.object(FileManager, 'refresh_files'), \
             patch.object(FileManager, 'restore_startup_cursor_positions'), \
             patch.object(FileManager, '_create_user_directories'):
            
            fm = FileManager(
                mock_renderer,
                left_dir=str(self.initial_left),
                right_dir=str(self.initial_right)
            )
        
        # Verify that update_monitored_directory was NOT called when monitoring is disabled
        mock_monitor.update_monitored_directory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
