"""
Test mouse event handling for pane focus switching in FileManager.

This test verifies that:
1. Clicking in left pane switches focus to left pane
2. Clicking in right pane switches focus to right pane
3. Clicking outside pane area doesn't change focus
4. Visual indicators update when focus changes
"""

import sys
import os
# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import Mock, MagicMock, patch
from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton
import time


class TestPaneFocusSwitching:
    """Test pane focus switching via mouse clicks."""
    
    @patch('tfm_main.LogManager')
    @patch('tfm_main.get_state_manager')
    def setup_file_manager(self, mock_state_mgr, mock_log_mgr):
        """Helper to create a FileManager instance for testing."""
        from tfm_main import FileManager
        
        # Create mock renderer
        mock_renderer = Mock()
        mock_renderer.is_desktop_mode = Mock(return_value=False)
        mock_renderer.set_cursor_visibility = Mock()
        mock_renderer.set_event_callback = Mock()
        mock_renderer.supports_mouse = Mock(return_value=True)
        mock_renderer.get_supported_mouse_events = Mock(return_value=set())
        mock_renderer.enable_mouse_events = Mock(return_value=True)
        mock_renderer.get_dimensions = Mock(return_value=(40, 120))  # height, width
        
        # Mock state manager
        mock_state_mgr.return_value = Mock()
        
        # Mock log manager and logger
        mock_logger = Mock()
        mock_log_instance = Mock()
        mock_log_instance.getLogger = Mock(return_value=mock_logger)
        mock_log_instance.add_startup_messages = Mock()
        mock_log_mgr.return_value = mock_log_instance
        
        # Create FileManager
        with patch('tfm_main.get_config'), \
             patch('tfm_main.init_colors'), \
             patch('tfm_main.PaneManager') as mock_pane_mgr_class, \
             patch('tfm_main.FileOperations'), \
             patch('tfm_main.ListDialog'), \
             patch('tfm_main.InfoDialog'), \
             patch('tfm_main.SearchDialog'), \
             patch('tfm_main.DrivesDialog'), \
             patch('tfm_main.BatchRenameDialog'), \
             patch('tfm_main.QuickChoiceBar'), \
             patch('tfm_main.QuickEditBar'), \
             patch('tfm_main.ExternalProgramManager'), \
             patch('tfm_main.ProgressManager'), \
             patch('tfm_main.CacheManager'), \
             patch('tfm_main.ArchiveOperations'), \
             patch('tfm_main.ArchiveUI'), \
             patch('tfm_main.FileOperationsUI'), \
             patch('tfm_main.UILayerStack'), \
             patch('tfm_main.Path'):
            
            # Setup pane manager mock instance
            pane_mgr_instance = Mock()
            pane_mgr_instance.active_pane = 'left'
            pane_mgr_instance.left_pane_ratio = 0.5  # This will be a Mock, need to configure it
            mock_pane_mgr_class.return_value = pane_mgr_instance
            
            fm = FileManager(mock_renderer)
            
            # After FileManager is created, set the left_pane_ratio as a real float
            fm.pane_manager.left_pane_ratio = 0.5
            fm.log_height_ratio = 0.2  # 20% for log pane
            
            return fm, mock_logger
    
    def test_click_in_left_pane_switches_focus(self):
        """Test that clicking in left pane switches focus to left pane."""
        fm, mock_logger = self.setup_file_manager()
        
        # Start with right pane active
        fm.pane_manager.active_pane = 'right'
        
        # Create mouse event in left pane (column < left_pane_width)
        # With 120 width and 0.5 ratio, left pane is columns 0-59
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,  # Middle of left pane
            row=10,     # Within file pane area
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = fm.handle_mouse_event(event)
        
        # Verify focus switched to left pane
        assert fm.pane_manager.active_pane == 'left'
        assert result is True
        
        # Verify log message
        mock_logger.info.assert_any_call("Switched focus to left pane")
    
    def test_click_in_right_pane_switches_focus(self):
        """Test that clicking in right pane switches focus to right pane."""
        fm, mock_logger = self.setup_file_manager()
        
        # Start with left pane active
        fm.pane_manager.active_pane = 'left'
        
        # Create mouse event in right pane (column >= left_pane_width)
        # With 120 width and 0.5 ratio, right pane is columns 60-119
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=80,  # Middle of right pane
            row=10,     # Within file pane area
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = fm.handle_mouse_event(event)
        
        # Verify focus switched to right pane
        assert fm.pane_manager.active_pane == 'right'
        assert result is True
        
        # Verify log message
        mock_logger.info.assert_any_call("Switched focus to right pane")
    
    def test_click_in_same_pane_no_log_message(self):
        """Test that clicking in already active pane doesn't log a message."""
        fm, mock_logger = self.setup_file_manager()
        
        # Start with left pane active
        fm.pane_manager.active_pane = 'left'
        
        # Clear any previous log calls
        mock_logger.info.reset_mock()
        
        # Create mouse event in left pane
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = fm.handle_mouse_event(event)
        
        # Verify focus remains on left pane
        assert fm.pane_manager.active_pane == 'left'
        assert result is True
        
        # Verify no "Switched focus" message was logged
        for call in mock_logger.info.call_args_list:
            assert "Switched focus" not in str(call)
    
    def test_click_outside_pane_area_no_focus_change(self):
        """Test that clicking outside pane area doesn't change focus."""
        fm, mock_logger = self.setup_file_manager()
        
        # Start with left pane active
        fm.pane_manager.active_pane = 'left'
        
        # Create mouse event in header area (row 0)
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=0,  # Header row
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = fm.handle_mouse_event(event)
        
        # Verify focus unchanged
        assert fm.pane_manager.active_pane == 'left'
        assert result is False  # Event not handled
    
    def test_click_in_log_area_no_focus_change(self):
        """Test that clicking in log area doesn't change focus."""
        fm, mock_logger = self.setup_file_manager()
        
        # Start with left pane active
        fm.pane_manager.active_pane = 'left'
        
        # Calculate log area start (height=40, log_ratio=0.2 -> log_height=8)
        # file_pane_bottom = 40 - 8 - 2 = 30
        # Log area starts at row 30
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=35,  # In log area
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = fm.handle_mouse_event(event)
        
        # Verify focus unchanged
        assert fm.pane_manager.active_pane == 'left'
        assert result is False  # Event not handled
    
    def test_non_button_down_event_not_handled(self):
        """Test that non-button-down events are not handled."""
        fm, mock_logger = self.setup_file_manager()
        
        # Start with left pane active
        fm.pane_manager.active_pane = 'left'
        
        # Create mouse move event
        event = MouseEvent(
            event_type=MouseEventType.MOVE,
            column=30,
            row=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            timestamp=time.time()
        )
        
        # Handle the event
        result = fm.handle_mouse_event(event)
        
        # Verify event not handled
        assert result is False
        
        # Verify focus unchanged
        assert fm.pane_manager.active_pane == 'left'
    
    def test_click_on_separator_switches_to_right_pane(self):
        """Test that clicking on separator column switches to right pane."""
        fm, mock_logger = self.setup_file_manager()
        
        # Start with left pane active
        fm.pane_manager.active_pane = 'left'
        
        # Create mouse event on separator (column = left_pane_width)
        # With 120 width and 0.5 ratio, separator is at column 60
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=60,  # Separator column
            row=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = fm.handle_mouse_event(event)
        
        # Verify focus switched to right pane (separator belongs to right pane)
        assert fm.pane_manager.active_pane == 'right'
        assert result is True
    
    def test_mark_dirty_called_on_focus_change(self):
        """Test that mark_dirty is called when focus changes."""
        fm, mock_logger = self.setup_file_manager()
        
        # Start with right pane active
        fm.pane_manager.active_pane = 'right'
        
        # Mock mark_dirty to track calls
        fm.mark_dirty = Mock()
        
        # Create mouse event in left pane
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        fm.handle_mouse_event(event)
        
        # Verify mark_dirty was called
        fm.mark_dirty.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
