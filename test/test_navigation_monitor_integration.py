"""
Tests for directory navigation integration with file monitoring.

This test suite verifies that directory navigation properly notifies
the FileMonitorManager and suppresses automatic reloads.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import tempfile
import shutil


class TestNavigationMonitorIntegration:
    """Test that directory navigation integrates with file monitoring"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        temp_root = tempfile.mkdtemp()
        dir1 = Path(temp_root) / "dir1"
        dir2 = Path(temp_root) / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        
        yield {
            'root': Path(temp_root),
            'dir1': dir1,
            'dir2': dir2
        }
        
        # Cleanup
        shutil.rmtree(temp_root)
    
    @pytest.fixture
    def mock_file_manager(self, temp_dirs):
        """Create a mock FileManager with necessary components"""
        from tfm_pane_manager import PaneManager
        from tfm_config import get_config
        
        # Create mock renderer
        mock_renderer = Mock()
        mock_renderer.get_dimensions.return_value = (40, 120)
        
        # Get real config
        config = get_config()
        
        # Create real pane manager with temp directories
        pane_manager = PaneManager(config, temp_dirs['dir1'], temp_dirs['dir2'])
        
        # Create mock file manager
        file_manager = Mock()
        file_manager.pane_manager = pane_manager
        file_manager.config = config
        file_manager.renderer = mock_renderer
        
        # Create mock file monitor manager
        mock_monitor = Mock()
        mock_monitor.update_monitored_directory = Mock()
        mock_monitor.suppress_reloads = Mock()
        file_manager.file_monitor_manager = mock_monitor
        
        return file_manager
    
    def test_navigate_to_dir_updates_path(self, mock_file_manager, temp_dirs):
        """Test that navigate_to_dir updates the pane path"""
        from tfm_main import FileManager
        
        pane_data = mock_file_manager.pane_manager.left_pane
        original_path = pane_data['path']
        new_path = temp_dirs['dir2']
        
        # Call the real navigate_to_dir method
        FileManager.navigate_to_dir(mock_file_manager, pane_data, new_path)
        
        # Verify path was updated
        assert pane_data['path'] == new_path
        assert pane_data['path'] != original_path
    
    def test_navigate_to_dir_notifies_monitor_left_pane(self, mock_file_manager, temp_dirs):
        """Test that navigate_to_dir notifies monitor for left pane"""
        from tfm_main import FileManager
        
        pane_data = mock_file_manager.pane_manager.left_pane
        new_path = temp_dirs['dir2']
        
        # Call the real navigate_to_dir method
        FileManager.navigate_to_dir(mock_file_manager, pane_data, new_path)
        
        # Verify monitor was notified with correct pane name
        mock_file_manager.file_monitor_manager.update_monitored_directory.assert_called_once_with(
            "left", new_path
        )
    
    def test_navigate_to_dir_notifies_monitor_right_pane(self, mock_file_manager, temp_dirs):
        """Test that navigate_to_dir notifies monitor for right pane"""
        from tfm_main import FileManager
        
        pane_data = mock_file_manager.pane_manager.right_pane
        new_path = temp_dirs['dir1']
        
        # Call the real navigate_to_dir method
        FileManager.navigate_to_dir(mock_file_manager, pane_data, new_path)
        
        # Verify monitor was notified with correct pane name
        mock_file_manager.file_monitor_manager.update_monitored_directory.assert_called_once_with(
            "right", new_path
        )
    
    def test_navigate_to_dir_suppresses_reloads(self, mock_file_manager, temp_dirs):
        """Test that navigate_to_dir suppresses automatic reloads for 1 second"""
        from tfm_main import FileManager
        
        pane_data = mock_file_manager.pane_manager.left_pane
        new_path = temp_dirs['dir2']
        
        # Call the real navigate_to_dir method
        FileManager.navigate_to_dir(mock_file_manager, pane_data, new_path)
        
        # Verify reloads were suppressed for 1000ms (1 second)
        mock_file_manager.file_monitor_manager.suppress_reloads.assert_called_once_with(1000)
    
    def test_navigate_to_dir_without_monitor(self, mock_file_manager, temp_dirs):
        """Test that navigate_to_dir works even without file_monitor_manager"""
        from tfm_main import FileManager
        
        # Remove file_monitor_manager attribute
        delattr(mock_file_manager, 'file_monitor_manager')
        
        pane_data = mock_file_manager.pane_manager.left_pane
        new_path = temp_dirs['dir2']
        
        # Should not raise an exception
        FileManager.navigate_to_dir(mock_file_manager, pane_data, new_path)
        
        # Verify path was still updated
        assert pane_data['path'] == new_path
    
    def test_navigate_to_dir_call_order(self, mock_file_manager, temp_dirs):
        """Test that navigate_to_dir calls methods in correct order"""
        from tfm_main import FileManager
        
        pane_data = mock_file_manager.pane_manager.left_pane
        new_path = temp_dirs['dir2']
        
        # Track call order
        call_order = []
        
        def track_update(*args):
            call_order.append('update_monitored_directory')
        
        def track_suppress(*args):
            call_order.append('suppress_reloads')
        
        mock_file_manager.file_monitor_manager.update_monitored_directory.side_effect = track_update
        mock_file_manager.file_monitor_manager.suppress_reloads.side_effect = track_suppress
        
        # Call navigate_to_dir
        FileManager.navigate_to_dir(mock_file_manager, pane_data, new_path)
        
        # Verify both methods were called
        assert len(call_order) == 2
        # Verify update_monitored_directory was called before suppress_reloads
        assert call_order[0] == 'update_monitored_directory'
        assert call_order[1] == 'suppress_reloads'
