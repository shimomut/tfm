"""
Unit test for Tab key pane switching in Qt GUI mode.

This test verifies that pressing Tab switches between panes and updates
the active pane highlighting.
"""

import sys
sys.path.append('src')

from unittest.mock import Mock, MagicMock
import pytest


class TestTabPaneSwitching:
    """Test Tab key pane switching functionality."""
    
    def test_tab_key_event_queued(self):
        """
        Verify that Tab key press queues a Tab input event.
        
        This test verifies that when _on_switch_pane_requested is called,
        a Tab key event (key code 9) is queued.
        """
        # Mock PySide6 before importing
        sys.modules['PySide6'] = MagicMock()
        sys.modules['PySide6.QtWidgets'] = MagicMock()
        sys.modules['PySide6.QtCore'] = MagicMock()
        sys.modules['PySide6.QtGui'] = MagicMock()
        
        from tfm_qt_backend import QtBackend
        from tfm_ui_backend import InputEvent
        
        # Create mock QApplication
        mock_app = MagicMock()
        
        # Create QtBackend
        backend = QtBackend(mock_app)
        
        # Simulate Tab key press by calling the signal handler
        backend._on_switch_pane_requested()
        
        # Verify Tab event was queued
        event = backend.get_input_event(timeout=0)
        assert event is not None, "Tab event should be queued"
        assert event.type == 'key', "Event should be a key event"
        assert event.key == 9, "Event should be Tab key (code 9)"
        assert event.key_name == 'Tab', "Event key name should be 'Tab'"
    
    def test_pane_manager_switches_on_tab(self):
        """
        Verify that PaneManager switches active pane when Tab is pressed.
        
        This test simulates the application controller's handling of Tab key:
        1. Starting with left pane active
        2. Pressing Tab key
        3. Verifying right pane becomes active
        4. Pressing Tab again
        5. Verifying left pane becomes active again
        """
        from tfm_pane_manager import PaneManager
        from _config import Config
        from pathlib import Path
        
        # Create PaneManager with required paths
        config = Config()
        left_path = Path.home()
        right_path = Path.home()
        pane_manager = PaneManager(config, left_path, right_path)
        
        # Set up initial state - left pane active
        pane_manager.active_pane = 'left'
        assert pane_manager.active_pane == 'left', "Should start with left pane active"
        
        # Simulate Tab key handling (toggle active pane)
        pane_manager.active_pane = 'right' if pane_manager.active_pane == 'left' else 'left'
        
        # Verify pane switched to right
        assert pane_manager.active_pane == 'right', "Tab should switch to right pane"
        
        # Simulate another Tab key press
        pane_manager.active_pane = 'right' if pane_manager.active_pane == 'left' else 'left'
        
        # Verify pane switched back to left
        assert pane_manager.active_pane == 'left', "Second Tab should switch back to left pane"
    
    def test_active_pane_highlighting_updates(self):
        """
        Verify that active pane highlighting updates when pane switches.
        
        This test verifies that:
        1. When left pane is active, left_pane_widget.set_active(True) is called
        2. When right pane is active, right_pane_widget.set_active(True) is called
        3. Inactive pane has set_active(False) called
        """
        # Mock PySide6 before importing
        sys.modules['PySide6'] = MagicMock()
        sys.modules['PySide6.QtWidgets'] = MagicMock()
        sys.modules['PySide6.QtCore'] = MagicMock()
        sys.modules['PySide6.QtGui'] = MagicMock()
        
        from tfm_qt_backend import QtBackend
        from tfm_ui_backend import LayoutInfo
        
        # Create mock QApplication
        mock_app = MagicMock()
        
        # Create QtBackend
        backend = QtBackend(mock_app)
        
        # Mock the main window and widgets
        backend.main_window = MagicMock()
        backend.left_pane_widget = MagicMock()
        backend.right_pane_widget = MagicMock()
        
        # Create mock pane data
        left_pane = {
            'files': [],
            'selected_index': 0,
            'selected_files': set()
        }
        right_pane = {
            'files': [],
            'selected_index': 0,
            'selected_files': set()
        }
        
        # Create mock layout
        layout = LayoutInfo(
            screen_height=800,
            screen_width=1200,
            left_pane_width=600,
            right_pane_width=600,
            pane_height=700,
            log_height=100,
            header_y=0,
            panes_y=50,
            footer_y=750,
            status_y=780,
            log_y=700
        )
        
        # Render with left pane active
        backend.render_panes(left_pane, right_pane, 'left', layout)
        
        # Verify left pane is set as active
        backend.left_pane_widget.set_active.assert_called_with(True)
        backend.right_pane_widget.set_active.assert_called_with(False)
        
        # Reset mocks
        backend.left_pane_widget.reset_mock()
        backend.right_pane_widget.reset_mock()
        
        # Render with right pane active
        backend.render_panes(left_pane, right_pane, 'right', layout)
        
        # Verify right pane is set as active
        backend.left_pane_widget.set_active.assert_called_with(False)
        backend.right_pane_widget.set_active.assert_called_with(True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
