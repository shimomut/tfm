#!/usr/bin/env python3
"""
Test cursor visibility in DirectoryDiffViewer after wheel scrolling.

This test verifies that when the cursor becomes invisible due to wheel scrolling,
keyboard navigation (UP/DOWN keys) properly adjusts the scroll position to make
the cursor visible again.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from unittest.mock import Mock, MagicMock
from tfm_directory_diff_viewer import DirectoryDiffViewer, TreeNode, DifferenceType
from ttk.input_event import KeyEvent, KeyCode, ModifierKey
from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton


class TestDirectoryDiffCursorVisibility(unittest.TestCase):
    """Test cursor visibility after wheel scrolling in DirectoryDiffViewer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock renderer
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (32, 80)  # height=32, width=80
        # display_height = 32 - 7 = 25
        
        # Create viewer
        self.viewer = DirectoryDiffViewer(
            renderer=self.renderer,
            left_path="/tmp/left",
            right_path="/tmp/right"
        )
        
        # Create 50 visible nodes
        self.viewer.visible_nodes = []
        for i in range(50):
            node = TreeNode(
                name=f"file{i:02d}.txt",
                left_path=f"/tmp/left/file{i:02d}.txt",
                right_path=f"/tmp/right/file{i:02d}.txt",
                is_directory=False,
                depth=0,
                difference_type=DifferenceType.CONTENT_DIFFERENT,
                is_expanded=False,
                children=[]
            )
            self.viewer.visible_nodes.append(node)
        
        # Start with cursor at top
        self.viewer.cursor_position = 0
        self.viewer.scroll_offset = 0
    
    def test_cursor_visibility_after_wheel_scroll_then_down_key(self):
        """Test that DOWN key makes cursor visible after wheel scrolling."""
        # Initial state: cursor at 0, scroll at 0
        self.assertEqual(self.viewer.cursor_position, 0)
        self.assertEqual(self.viewer.scroll_offset, 0)
        
        # Wheel scroll down to move visible range away from cursor
        # Scroll down by 15 lines (visible range becomes 15-39, cursor still at 0)
        for _ in range(15):
            wheel_event = MouseEvent(
                event_type=MouseEventType.WHEEL,
                row=10,
                column=10,
                sub_cell_x=0.0,
                sub_cell_y=0.0,
                button=MouseButton.NONE,
                scroll_delta_x=0.0,
                scroll_delta_y=-1.0  # Negative = scroll down
            )
            self.viewer.handle_mouse_event(wheel_event)
        
        # Verify cursor is now above visible range
        self.assertEqual(self.viewer.cursor_position, 0)
        self.assertEqual(self.viewer.scroll_offset, 15)
        self.assertLess(self.viewer.cursor_position, self.viewer.scroll_offset,
                       "Cursor should be above visible range after wheel scroll")
        
        # Press DOWN key
        down_event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0, char='')
        self.viewer.handle_key_event(down_event)
        
        # Verify cursor moved and is now visible
        self.assertEqual(self.viewer.cursor_position, 1)
        display_height = 25
        self.assertGreaterEqual(self.viewer.cursor_position, self.viewer.scroll_offset,
                               "Cursor should be at or after scroll_offset")
        self.assertLess(self.viewer.cursor_position, self.viewer.scroll_offset + display_height,
                       "Cursor should be before end of visible range")
    
    def test_cursor_visibility_after_wheel_scroll_then_up_key(self):
        """Test that UP key makes cursor visible after wheel scrolling."""
        # Start with cursor at bottom
        self.viewer.cursor_position = 49
        self.viewer.scroll_offset = 25  # Visible range: 25-49
        
        # Wheel scroll up to move visible range away from cursor
        # Scroll up by 15 lines (visible range becomes 10-34, cursor still at 49)
        for _ in range(15):
            wheel_event = MouseEvent(
                event_type=MouseEventType.WHEEL,
                row=10,
                column=10,
                sub_cell_x=0.0,
                sub_cell_y=0.0,
                button=MouseButton.NONE,
                scroll_delta_x=0.0,
                scroll_delta_y=1.0  # Positive = scroll up
            )
            self.viewer.handle_mouse_event(wheel_event)
        
        # Verify cursor is now below visible range
        self.assertEqual(self.viewer.cursor_position, 49)
        self.assertEqual(self.viewer.scroll_offset, 10)
        display_height = 25
        self.assertGreaterEqual(self.viewer.cursor_position, self.viewer.scroll_offset + display_height,
                               "Cursor should be below visible range after wheel scroll")
        
        # Press UP key
        up_event = KeyEvent(key_code=KeyCode.UP, modifiers=0, char='')
        self.viewer.handle_key_event(up_event)
        
        # Verify cursor moved and is now visible
        self.assertEqual(self.viewer.cursor_position, 48)
        self.assertGreaterEqual(self.viewer.cursor_position, self.viewer.scroll_offset,
                               "Cursor should be at or after scroll_offset")
        self.assertLess(self.viewer.cursor_position, self.viewer.scroll_offset + display_height,
                       "Cursor should be before end of visible range")
    
    def test_multiple_down_presses_when_cursor_above_visible_range(self):
        """Test pressing DOWN multiple times when cursor starts above visible range."""
        # Set cursor above visible range
        self.viewer.cursor_position = 0
        self.viewer.scroll_offset = 10  # Visible range: 10-34
        
        display_height = 25
        
        # Press DOWN 5 times
        for i in range(5):
            down_event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0, char='')
            self.viewer.handle_key_event(down_event)
            
            # After each press, cursor should be visible
            self.assertGreaterEqual(self.viewer.cursor_position, self.viewer.scroll_offset,
                                   f"After DOWN press {i+1}: cursor should be at or after scroll_offset")
            self.assertLess(self.viewer.cursor_position, self.viewer.scroll_offset + display_height,
                           f"After DOWN press {i+1}: cursor should be before end of visible range")


if __name__ == '__main__':
    unittest.main()
