#!/usr/bin/env python3
"""
Test wheel scrolling support for dialogs (InfoDialog and BaseListDialog)
"""

import unittest
from unittest.mock import Mock, MagicMock
from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton
from tfm_info_dialog import InfoDialog
from tfm_base_list_dialog import BaseListDialog


class TestInfoDialogWheelScrolling(unittest.TestCase):
    """Test wheel scrolling in InfoDialog"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (24, 80)
        
        self.dialog = InfoDialog(None, self.renderer)
        
        # Create test content with many lines
        self.lines = [f"Line {i}" for i in range(50)]
        self.dialog.show("Test Dialog", self.lines)
        self.dialog.cached_content_height = 10  # Simulate 10 visible lines
    
    def test_wheel_scroll_up(self):
        """Test scrolling up with mouse wheel"""
        # Start at scroll position 10
        self.dialog.scroll = 10
        self.dialog.content_changed = False
        
        # Create wheel up event (positive delta)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0  # Positive = scroll up
        )
        
        result = self.dialog.handle_mouse_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.scroll, 7)  # 10 - 3 = 7
        self.assertTrue(self.dialog.content_changed)
    
    def test_wheel_scroll_down(self):
        """Test scrolling down with mouse wheel"""
        # Start at scroll position 10
        self.dialog.scroll = 10
        self.dialog.content_changed = False
        
        # Create wheel down event (negative delta)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-3.0  # Negative = scroll down
        )
        
        result = self.dialog.handle_mouse_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.scroll, 13)  # 10 - (-3) = 13
        self.assertTrue(self.dialog.content_changed)
    
    def test_wheel_scroll_clamps_at_top(self):
        """Test that scrolling up stops at top"""
        # Start near top
        self.dialog.scroll = 2
        self.dialog.content_changed = False
        
        # Try to scroll up past top
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=5.0
        )
        
        result = self.dialog.handle_mouse_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.scroll, 0)  # Clamped to 0
        self.assertTrue(self.dialog.content_changed)
    
    def test_wheel_scroll_clamps_at_bottom(self):
        """Test that scrolling down stops at bottom"""
        # Start near bottom (max_scroll = 50 - 10 = 40)
        self.dialog.scroll = 38
        self.dialog.content_changed = False
        
        # Try to scroll down past bottom
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-5.0
        )
        
        result = self.dialog.handle_mouse_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.scroll, 40)  # Clamped to max_scroll
        self.assertTrue(self.dialog.content_changed)
    
    def test_wheel_scroll_no_change_when_at_boundary(self):
        """Test that scrolling at boundary doesn't mark as changed"""
        # Already at top
        self.dialog.scroll = 0
        self.dialog.content_changed = False
        
        # Try to scroll up
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0
        )
        
        result = self.dialog.handle_mouse_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.scroll, 0)
        self.assertFalse(self.dialog.content_changed)  # No change
    
    def test_non_wheel_event_not_handled(self):
        """Test that non-wheel events are not handled"""
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            scroll_delta_y=0.0
        )
        
        result = self.dialog.handle_mouse_event(event)
        
        self.assertFalse(result)


class TestBaseListDialogWheelScrolling(unittest.TestCase):
    """Test wheel scrolling in BaseListDialog"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (24, 80)
        
        self.dialog = BaseListDialog(None, self.renderer)
        
        # Create test items
        self.items = [f"Item {i}" for i in range(50)]
        self.dialog._last_content_height = 10  # Simulate 10 visible lines
    
    def test_wheel_scroll_up(self):
        """Test scrolling up with mouse wheel"""
        # Start at scroll position 10
        self.dialog.scroll = 10
        
        # Create wheel up event (positive delta)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0  # Positive = scroll up
        )
        
        result = self.dialog.handle_mouse_event(event, self.items)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.scroll, 7)  # 10 - 3 = 7
    
    def test_wheel_scroll_down(self):
        """Test scrolling down with mouse wheel"""
        # Start at scroll position 10
        self.dialog.scroll = 10
        
        # Create wheel down event (negative delta)
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-3.0  # Negative = scroll down
        )
        
        result = self.dialog.handle_mouse_event(event, self.items)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.scroll, 13)  # 10 - (-3) = 13
    
    def test_wheel_scroll_clamps_at_top(self):
        """Test that scrolling up stops at top"""
        # Start near top
        self.dialog.scroll = 2
        
        # Try to scroll up past top
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=5.0
        )
        
        result = self.dialog.handle_mouse_event(event, self.items)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.scroll, 0)  # Clamped to 0
    
    def test_wheel_scroll_clamps_at_bottom(self):
        """Test that scrolling down stops at bottom"""
        # Start near bottom (max_scroll = 50 - 10 = 40)
        self.dialog.scroll = 38
        
        # Try to scroll down past bottom
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=-5.0
        )
        
        result = self.dialog.handle_mouse_event(event, self.items)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.scroll, 40)  # Clamped to max_scroll
    
    def test_wheel_scroll_with_empty_list(self):
        """Test that wheel scrolling with empty list doesn't crash"""
        empty_items = []
        
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0
        )
        
        result = self.dialog.handle_mouse_event(event, empty_items)
        
        self.assertFalse(result)  # No items to scroll
    
    def test_wheel_scroll_uses_fallback_content_height(self):
        """Test that wheel scrolling works even without cached content height"""
        # Clear cached content height
        self.dialog._last_content_height = None
        self.dialog.scroll = 10
        
        event = MouseEvent(
            event_type=MouseEventType.WHEEL,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            scroll_delta_y=3.0
        )
        
        result = self.dialog.handle_mouse_event(event, self.items)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.scroll, 7)  # Still works with fallback
    
    def test_non_wheel_event_not_handled(self):
        """Test that non-wheel events are not handled"""
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            row=5,
            column=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            scroll_delta_y=0.0
        )
        
        result = self.dialog.handle_mouse_event(event, self.items)
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
