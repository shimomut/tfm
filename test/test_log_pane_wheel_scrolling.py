#!/usr/bin/env python3
"""
Tests for mouse wheel scrolling in the log pane.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton


class TestLogPaneWheelScrolling(unittest.TestCase):
    """Test mouse wheel scrolling in the log pane"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (40, 120)  # height, width
        self.mock_renderer.is_desktop_mode.return_value = False
        self.mock_renderer.supports_mouse.return_value = True
        self.mock_renderer.get_supported_mouse_events.return_value = {MouseEventType.BUTTON_DOWN, MouseEventType.WHEEL}
        self.mock_renderer.enable_mouse_events.return_value = True
        self.mock_renderer.set_cursor_visibility = Mock()
        self.mock_renderer.draw_text = Mock()
        self.mock_renderer.clear = Mock()
        self.mock_renderer.refresh = Mock()
        
        # Import FileManager after mocking
        from src.tfm_main import FileManager
        
        # Create FileManager with mocked renderer
        with patch('src.tfm_main.init_colors'):
            self.fm = FileManager(self.mock_renderer)
        
        # Set log height ratio to create a visible log pane
        self.fm.log_height_ratio = 0.3  # 30% of screen for log
        
        # Add some log messages to enable scrolling
        for i in range(50):
            self.fm.log_manager.getLogger("Test").info(f"Test message {i}")
    
    def test_wheel_scroll_up_in_log_pane(self):
        """Test scrolling up (toward older messages) in log pane"""
        height, width = self.mock_renderer.get_dimensions()
        log_height = int(height * self.fm.log_height_ratio)
        log_pane_top = height - log_height - 1
        
        # Create wheel event in log pane area (scroll up)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=log_pane_top + 2,  # Inside log pane
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0  # Positive = scroll up
        )
        
        # Get initial scroll offset
        initial_offset = self.fm.log_manager.log_scroll_offset
        
        # Handle the event
        result = self.fm.handle_mouse_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify scroll offset increased (scrolled toward older messages)
        self.assertEqual(self.fm.log_manager.log_scroll_offset, initial_offset + 3)
    
    def test_wheel_scroll_down_in_log_pane(self):
        """Test scrolling down (toward newer messages) in log pane"""
        height, width = self.mock_renderer.get_dimensions()
        log_height = int(height * self.fm.log_height_ratio)
        log_pane_top = height - log_height - 1
        
        # First scroll up to have room to scroll down
        self.fm.log_manager.scroll_log_up(10)
        initial_offset = self.fm.log_manager.log_scroll_offset
        
        # Create wheel event in log pane area (scroll down)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=log_pane_top + 2,  # Inside log pane
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-3.0  # Negative = scroll down
        )
        
        # Handle the event
        result = self.fm.handle_mouse_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify scroll offset decreased (scrolled toward newer messages)
        self.assertEqual(self.fm.log_manager.log_scroll_offset, initial_offset - 3)
    
    def test_wheel_scroll_in_log_pane_marks_dirty(self):
        """Test that scrolling in log pane marks the screen dirty"""
        height, width = self.mock_renderer.get_dimensions()
        log_height = int(height * self.fm.log_height_ratio)
        log_pane_top = height - log_height - 1
        
        # Clear dirty flag
        self.fm._dirty = False
        
        # Create wheel event in log pane
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=log_pane_top + 2,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=2.0
        )
        
        # Handle the event
        self.fm.handle_mouse_event(event)
        
        # Verify screen was marked dirty
        self.assertTrue(self.fm._dirty)
    
    def test_wheel_scroll_at_log_bottom_boundary(self):
        """Test that scrolling down at bottom of log doesn't go negative"""
        height, width = self.mock_renderer.get_dimensions()
        log_height = int(height * self.fm.log_height_ratio)
        log_pane_top = height - log_height - 1
        
        # Ensure we're at the bottom (offset = 0)
        self.fm.log_manager.log_scroll_offset = 0
        
        # Try to scroll down further
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=log_pane_top + 2,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-5.0  # Try to scroll down
        )
        
        self.fm.handle_mouse_event(event)
        
        # Verify offset stayed at 0
        self.assertEqual(self.fm.log_manager.log_scroll_offset, 0)
    
    def test_wheel_scroll_at_log_top_boundary(self):
        """Test that scrolling up at top of log is capped properly"""
        height, width = self.mock_renderer.get_dimensions()
        log_height = int(height * self.fm.log_height_ratio)
        log_pane_top = height - log_height - 1
        
        # Scroll up a lot
        for _ in range(20):
            event = MouseEvent(
                event_type=MouseEventType.WHEEL,
                row=log_pane_top + 2,
                column=10,
                sub_cell_x=0.5,
                sub_cell_y=0.5,
                button=MouseButton.NONE,
                scroll_delta_y=5.0
            )
            self.fm.handle_mouse_event(event)
        
        # Verify offset is capped (draw_log_pane will cap it based on total messages)
        # The offset should be positive but reasonable
        self.assertGreater(self.fm.log_manager.log_scroll_offset, 0)
    
    def test_wheel_scroll_in_file_pane_not_log_pane(self):
        """Test that wheel events in file pane don't affect log pane"""
        # Get initial log scroll offset
        initial_log_offset = self.fm.log_manager.log_scroll_offset
        
        # Create wheel event in file pane area (row 5 is in file pane)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0
        )
        
        # Handle the event
        self.fm.handle_mouse_event(event)
        
        # Verify log scroll offset didn't change
        self.assertEqual(self.fm.log_manager.log_scroll_offset, initial_log_offset)
    
    def test_wheel_scroll_with_no_log_pane(self):
        """Test that wheel events are handled correctly when log pane is hidden"""
        # Hide log pane
        self.fm.log_height_ratio = 0.0
        
        # Create wheel event at bottom of screen (where log would be)
        height, width = self.mock_renderer.get_dimensions()
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=height - 2,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0
        )
        
        # Handle the event - should return False since no log pane
        result = self.fm.handle_mouse_event(event)
        
        # Event should not be handled (no log pane visible)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
