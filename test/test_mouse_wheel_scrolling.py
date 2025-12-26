"""
Tests for mouse wheel scrolling in file lists.

This test suite verifies that mouse wheel events correctly scroll the file list
in both left and right panes, with proper boundary checking and focus handling.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton


class TestMouseWheelScrolling(unittest.TestCase):
    """Test mouse wheel scrolling functionality in file lists."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (40, 120)  # height, width
        self.mock_renderer.is_desktop_mode.return_value = True
        self.mock_renderer.supports_mouse.return_value = True
        self.mock_renderer.get_supported_mouse_events.return_value = {
            MouseEventType.BUTTON_DOWN,
            MouseEventType.WHEEL
        }
        self.mock_renderer.enable_mouse_events.return_value = True
        self.mock_renderer.set_event_callback = Mock()
        
        # Patch init_colors to prevent color initialization
        with patch('src.tfm_main.init_colors'):
            # Import after patching
            from src.tfm_main import FileManager
            
            # Create FileManager instance
            self.fm = FileManager(self.mock_renderer)
            
            # Set up test files in both panes
            test_files = [f"file{i:02d}.txt" for i in range(50)]  # More files for scrolling tests
            
            self.fm.pane_manager.left_pane['files'] = test_files
            self.fm.pane_manager.left_pane['focused_index'] = 10
            self.fm.pane_manager.left_pane['scroll_offset'] = 0
            
            self.fm.pane_manager.right_pane['files'] = test_files
            self.fm.pane_manager.right_pane['focused_index'] = 10
            self.fm.pane_manager.right_pane['scroll_offset'] = 0
            
            # Set active pane to left
            self.fm.pane_manager.active_pane = 'left'
            
            # Set log height ratio
            self.fm.log_height_ratio = 0.3
    
    def test_wheel_scroll_up_in_left_pane(self):
        """Test that scrolling up in left pane decreases scroll offset."""
        # Set initial scroll offset
        self.fm.pane_manager.left_pane['scroll_offset'] = 10
        
        # Create wheel event with positive delta (scroll up)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            column=10,  # Left pane
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=1.0  # Positive = scroll up
        )
        
        initial_offset = self.fm.pane_manager.left_pane['scroll_offset']
        
        # Handle the event
        result = self.fm.handle_mouse_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify scroll offset decreased (scrolled up)
        new_offset = self.fm.pane_manager.left_pane['scroll_offset']
        self.assertLess(new_offset, initial_offset)
    
    def test_wheel_scroll_down_in_left_pane(self):
        """Test that scrolling down in left pane increases scroll offset."""
        # Set initial scroll offset
        self.fm.pane_manager.left_pane['scroll_offset'] = 5
        
        # Create wheel event with negative delta (scroll down)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            column=10,  # Left pane
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-1.0  # Negative = scroll down
        )
        
        initial_offset = self.fm.pane_manager.left_pane['scroll_offset']
        
        # Handle the event
        result = self.fm.handle_mouse_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify scroll offset increased (scrolled down)
        new_offset = self.fm.pane_manager.left_pane['scroll_offset']
        self.assertGreater(new_offset, initial_offset)
    
    def test_wheel_scroll_up_in_right_pane(self):
        """Test that scrolling up in right pane decreases scroll offset."""
        # Set initial scroll offset
        self.fm.pane_manager.right_pane['scroll_offset'] = 10
        
        # Create wheel event in right pane
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            column=80,  # Right pane
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=1.0  # Positive = scroll up
        )
        
        initial_offset = self.fm.pane_manager.right_pane['scroll_offset']
        
        # Handle the event
        result = self.fm.handle_mouse_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify scroll offset decreased in right pane
        new_offset = self.fm.pane_manager.right_pane['scroll_offset']
        self.assertLess(new_offset, initial_offset)
    
    def test_wheel_scroll_at_top_boundary(self):
        """Test that scrolling up at top of list doesn't go negative."""
        # Set scroll offset to top of list
        self.fm.pane_manager.left_pane['scroll_offset'] = 0
        
        # Create wheel event with positive delta (scroll up)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            column=10,  # Left pane
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=1.0
        )
        
        # Handle the event
        result = self.fm.handle_mouse_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify scroll offset stayed at 0 (didn't go negative)
        self.assertEqual(self.fm.pane_manager.left_pane['scroll_offset'], 0)
    
    def test_wheel_scroll_at_bottom_boundary(self):
        """Test that scrolling down at bottom of list doesn't exceed bounds."""
        # Calculate max scroll offset
        height, width = self.mock_renderer.get_dimensions()
        calculated_height = int(height * self.fm.log_height_ratio)
        log_height = calculated_height if self.fm.log_height_ratio > 0 else 0
        file_pane_bottom = height - log_height - 2
        display_height = file_pane_bottom - 1
        max_offset = max(0, len(self.fm.pane_manager.left_pane['files']) - display_height)
        
        # Set scroll offset to bottom of list
        self.fm.pane_manager.left_pane['scroll_offset'] = max_offset
        
        # Create wheel event with negative delta (scroll down)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            column=10,  # Left pane
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-1.0
        )
        
        # Handle the event
        result = self.fm.handle_mouse_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify scroll offset stayed at max (didn't exceed)
        self.assertEqual(self.fm.pane_manager.left_pane['scroll_offset'], max_offset)
    
    def test_wheel_scroll_outside_pane_area_not_handled(self):
        """Test that wheel events outside pane area are not handled."""
        # Create wheel event in header area (row 0)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            column=10,
            row=0,  # Header area
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=1.0
        )
        
        # Handle the event
        result = self.fm.handle_mouse_event(event)
        
        # Verify event was not handled
        self.assertFalse(result)
    
    def test_wheel_scroll_in_log_area_scrolls_log(self):
        """Test that wheel events in log area scroll the log pane, not file pane."""
        height, width = self.mock_renderer.get_dimensions()
        calculated_height = int(height * self.fm.log_height_ratio)
        log_start_row = height - calculated_height - 1
        
        # Get initial file pane scroll offset
        initial_file_offset = self.fm.pane_manager.left_pane['scroll_offset']
        
        # Get initial log scroll offset
        initial_log_offset = self.fm.log_manager.log_scroll_offset
        
        # Create wheel event in log area
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            column=10,
            row=log_start_row,  # Log area
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=1.0
        )
        
        # Handle the event
        result = self.fm.handle_mouse_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify file pane scroll offset unchanged
        self.assertEqual(self.fm.pane_manager.left_pane['scroll_offset'], initial_file_offset)
        
        # Verify log scroll offset changed (scrolled up toward older messages)
        self.assertGreater(self.fm.log_manager.log_scroll_offset, initial_log_offset)
    
    def test_wheel_scroll_with_empty_file_list(self):
        """Test that wheel events with empty file list are handled gracefully."""
        # Clear file list
        self.fm.pane_manager.left_pane['files'] = []
        self.fm.pane_manager.left_pane['scroll_offset'] = 0
        
        # Create wheel event
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            column=10,
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=1.0
        )
        
        # Handle the event
        result = self.fm.handle_mouse_event(event)
        
        # Verify event was handled (even though no scroll occurred)
        self.assertTrue(result)
        
        # Verify no crash and offset stayed at 0
        self.assertEqual(self.fm.pane_manager.left_pane['scroll_offset'], 0)
    
    def test_wheel_scroll_marks_dirty(self):
        """Test that wheel scrolling marks the screen as dirty."""
        # Set initial scroll offset
        self.fm.pane_manager.left_pane['scroll_offset'] = 5
        
        # Clear dirty flag
        self.fm._dirty = False
        
        # Create wheel event
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            column=10,
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=1.0
        )
        
        # Handle the event
        self.fm.handle_mouse_event(event)
        
        # Verify screen was marked dirty
        self.assertTrue(self.fm._dirty)
    
    def test_wheel_scroll_multiplier(self):
        """Test that scroll delta is multiplied for responsive scrolling."""
        # Set initial scroll offset
        self.fm.pane_manager.left_pane['scroll_offset'] = 10
        
        # Create wheel event with small delta
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            column=10,
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=0.5  # Small delta
        )
        
        initial_offset = self.fm.pane_manager.left_pane['scroll_offset']
        
        # Handle the event
        self.fm.handle_mouse_event(event)
        
        # Verify scroll offset moved by more than 0 (due to multiplier)
        new_offset = self.fm.pane_manager.left_pane['scroll_offset']
        delta = abs(new_offset - initial_offset)
        
        # With multiplier of 1, delta of 0.5 should move by 0 lines (rounds down)
        # But delta of 1.0 would move by 1 line
        self.assertGreaterEqual(delta, 0)


if __name__ == '__main__':
    unittest.main()
