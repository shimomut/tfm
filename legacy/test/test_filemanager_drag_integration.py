"""
Tests for FileManager drag-and-drop integration.

This module tests the integration of drag-and-drop components into the
FileManager class, including gesture detection, payload building, and
session management.

Run with: PYTHONPATH=.:src:ttk pytest test/test_filemanager_drag_integration.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton


class TestFileManagerDragIntegration:
    """Test FileManager drag-and-drop integration."""
    
    @pytest.fixture
    def mock_renderer(self):
        """Create a mock renderer for testing."""
        renderer = Mock()
        renderer.get_dimensions.return_value = (40, 120)
        renderer.is_desktop_mode.return_value = True
        renderer.supports_mouse.return_value = True
        renderer.get_supported_mouse_events.return_value = {
            MouseEventType.BUTTON_DOWN,
            MouseEventType.BUTTON_UP,
            MouseEventType.MOVE,
            MouseEventType.DOUBLE_CLICK,
            MouseEventType.WHEEL
        }
        renderer.enable_mouse_events.return_value = True
        renderer.supports_drag_and_drop.return_value = True
        renderer.start_drag_session.return_value = True
        renderer.clear.return_value = None
        renderer.draw_text.return_value = None
        renderer.set_cursor_visibility.return_value = None
        renderer.set_event_callback.return_value = None
        renderer.set_caret_position.return_value = None
        return renderer
    
    @pytest.fixture
    def file_manager(self, mock_renderer, tmp_path):
        """Create a FileManager instance for testing."""
        from tfm_main import FileManager
        
        # Create test directories
        left_dir = tmp_path / "left"
        right_dir = tmp_path / "right"
        left_dir.mkdir()
        right_dir.mkdir()
        
        # Create test files
        (left_dir / "file1.txt").write_text("test1")
        (left_dir / "file2.txt").write_text("test2")
        
        # Create FileManager with mocked renderer
        fm = FileManager(
            mock_renderer,
            left_dir=str(left_dir),
            right_dir=str(right_dir)
        )
        
        return fm
    
    def test_drag_components_initialized(self, file_manager):
        """Test that drag components are properly initialized."""
        assert hasattr(file_manager, 'drag_gesture_detector')
        assert hasattr(file_manager, 'drag_payload_builder')
        assert hasattr(file_manager, 'drag_session_manager')
        
        assert file_manager.drag_gesture_detector is not None
        assert file_manager.drag_payload_builder is not None
        assert file_manager.drag_session_manager is not None
    
    def test_drag_blocks_other_mouse_events(self, file_manager):
        """Test that mouse events are blocked during drag."""
        # Simulate drag in progress
        file_manager.drag_session_manager.state = file_manager.drag_session_manager.state.__class__.DRAGGING
        
        # Create a button down event
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=10,
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT
        )
        
        # Event should be blocked
        result = file_manager.handle_mouse_event(event)
        assert result is True
    
    def test_button_down_starts_gesture_tracking(self, file_manager):
        """Test that button down starts gesture tracking."""
        # Create a button down event in file pane area
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=10,
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT
        )
        
        # Handle the event
        file_manager.handle_mouse_event(event)
        
        # Gesture detector should have button_down state
        assert file_manager.drag_gesture_detector.state.button_down is True
    
    def test_initiate_drag_with_focused_item(self, file_manager, tmp_path):
        """Test drag initiation with focused item."""
        # Set up current pane with a focused file
        current_pane = file_manager.get_current_pane()
        test_file = tmp_path / "left" / "file1.txt"
        current_pane['files'] = [test_file]
        current_pane['focused_index'] = 0
        current_pane['selected_files'] = set()
        
        # Mock the backend to return success
        file_manager.renderer.start_drag_session.return_value = True
        
        # Initiate drag
        result = file_manager._initiate_drag()
        
        # Should succeed
        assert result is True
        
        # Backend should have been called
        file_manager.renderer.start_drag_session.assert_called_once()
        
        # Check the drag image text
        call_args = file_manager.renderer.start_drag_session.call_args
        assert call_args[0][1] == "file1.txt"
    
    def test_initiate_drag_with_selected_files(self, file_manager, tmp_path):
        """Test drag initiation with multiple selected files."""
        # Set up current pane with selected files
        current_pane = file_manager.get_current_pane()
        file1 = tmp_path / "left" / "file1.txt"
        file2 = tmp_path / "left" / "file2.txt"
        current_pane['files'] = [file1, file2]
        current_pane['focused_index'] = 0
        current_pane['selected_files'] = {file1, file2}
        
        # Mock the backend to return success
        file_manager.renderer.start_drag_session.return_value = True
        
        # Initiate drag
        result = file_manager._initiate_drag()
        
        # Should succeed
        assert result is True
        
        # Backend should have been called
        file_manager.renderer.start_drag_session.assert_called_once()
        
        # Check the drag image text shows count
        call_args = file_manager.renderer.start_drag_session.call_args
        assert call_args[0][1] == "2 files"
    
    def test_drag_completion_callback(self, file_manager):
        """Test drag completion callback."""
        # Call completion callback
        file_manager._on_drag_completed(completed=True)
        
        # Gesture detector should be reset
        assert file_manager.drag_gesture_detector.state.button_down is False
        assert file_manager.drag_gesture_detector.state.dragging is False
        
        # UI should be marked dirty
        assert file_manager.needs_redraw() is True
    
    def test_drag_cancellation_callback(self, file_manager):
        """Test drag cancellation callback."""
        # Call completion callback with cancelled
        file_manager._on_drag_completed(completed=False)
        
        # Gesture detector should be reset
        assert file_manager.drag_gesture_detector.state.button_down is False
        assert file_manager.drag_gesture_detector.state.dragging is False
        
        # UI should be marked dirty
        assert file_manager.needs_redraw() is True
    
    def test_button_up_after_drag_blocks_click(self, file_manager):
        """Test that button up after drag doesn't trigger click."""
        # Simulate drag gesture
        file_manager.drag_gesture_detector.state.button_down = True
        file_manager.drag_gesture_detector.state.dragging = True
        
        # Create button up event
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_UP,
            column=10,
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT
        )
        
        # Handle the event
        result = file_manager.handle_mouse_event(event)
        
        # Should return True (event handled, not processed as click)
        assert result is True
        
        # Gesture detector should be reset
        assert file_manager.drag_gesture_detector.state.button_down is False
        assert file_manager.drag_gesture_detector.state.dragging is False
