"""
Test mouse click-to-focus behavior in DirectoryDiffViewer.

This test verifies that:
1. Clicking on an item moves the cursor to that item
2. Clicking outside the tree view area doesn't change cursor
3. Clicking on invalid indices doesn't crash
"""

import sys
import os
# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import Mock, MagicMock, patch
from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton
import time


class TestDirectoryDiffClickToFocus:
    """Test click-to-focus behavior in DirectoryDiffViewer."""
    
    @patch('tfm_directory_diff_viewer.getLogger')
    def setup_viewer(self, mock_get_logger):
        """Helper to create a DirectoryDiffViewer instance for testing."""
        from tfm_directory_diff_viewer import DirectoryDiffViewer, TreeNode, DifferenceType
        
        # Create mock renderer
        mock_renderer = Mock()
        mock_renderer.get_dimensions = Mock(return_value=(40, 120))  # height, width
        
        # Mock logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Create mock paths
        mock_left_path = Mock()
        mock_left_path.__str__ = Mock(return_value="/left/path")
        mock_right_path = Mock()
        mock_right_path.__str__ = Mock(return_value="/right/path")
        
        # Create viewer
        viewer = DirectoryDiffViewer(mock_renderer, mock_left_path, mock_right_path)
        
        # Create some test nodes
        # TreeNode(name, left_path, right_path, is_directory, difference_type, depth, is_expanded, children, parent)
        root = TreeNode("root", mock_left_path, mock_right_path, True, DifferenceType.CONTAINS_DIFFERENCE, 0, True, [])
        child1 = TreeNode("file1.txt", mock_left_path, mock_right_path, False, DifferenceType.CONTENT_DIFFERENT, 1, False, [], root)
        child2 = TreeNode("file2.txt", None, mock_right_path, False, DifferenceType.ONLY_RIGHT, 1, False, [], root)
        child3 = TreeNode("file3.txt", mock_left_path, None, False, DifferenceType.ONLY_LEFT, 1, False, [], root)
        child4 = TreeNode("file4.txt", mock_left_path, mock_right_path, False, DifferenceType.IDENTICAL, 1, False, [], root)
        child5 = TreeNode("file5.txt", mock_left_path, mock_right_path, False, DifferenceType.CONTENT_DIFFERENT, 1, False, [], root)
        
        root.children = [child1, child2, child3, child4, child5]
        
        # Set up visible nodes
        viewer.root_node = root
        viewer.visible_nodes = [root, child1, child2, child3, child4, child5]
        viewer.cursor_position = 0
        viewer.scroll_offset = 0
        
        return viewer, mock_logger
    
    def test_click_on_item_moves_cursor(self):
        """Test that clicking on an item moves the cursor to that item."""
        viewer, mock_logger = self.setup_viewer()
        
        # Start with cursor at position 0
        assert viewer.cursor_position == 0
        
        # Click on row 3 (which is item index 2 in visible_nodes)
        # Tree view starts at row 1, so row 3 = item index 2
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=3,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify cursor moved to item 2
        assert viewer.cursor_position == 2
        assert result is True
        
        # Verify log message
        mock_logger.info.assert_any_call("Moved cursor to item 2")
    
    def test_click_on_different_item(self):
        """Test clicking on a different item."""
        viewer, mock_logger = self.setup_viewer()
        
        # Start with cursor at position 0
        viewer.cursor_position = 0
        
        # Click on row 5 (which is item index 4 in visible_nodes)
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=5,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify cursor moved to item 4
        assert viewer.cursor_position == 4
        assert result is True
    
    def test_click_with_scroll_offset(self):
        """Test clicking when scroll_offset is non-zero."""
        viewer, mock_logger = self.setup_viewer()
        
        # Set scroll offset to 2
        viewer.scroll_offset = 2
        viewer.cursor_position = 2
        
        # Click on row 2 (first visible row after header)
        # With scroll_offset=2, row 2 corresponds to item index 3
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=2,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify cursor moved to item 3 (row 2 - 1 + scroll_offset 2 = 3)
        assert viewer.cursor_position == 3
        assert result is True
    
    def test_click_above_tree_view_not_handled(self):
        """Test that clicking above tree view area doesn't change cursor."""
        viewer, mock_logger = self.setup_viewer()
        
        # Start with cursor at position 2
        viewer.cursor_position = 2
        
        # Click on row 0 (header area)
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=0,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify cursor unchanged
        assert viewer.cursor_position == 2
        assert result is False
    
    def test_click_below_tree_view_not_handled(self):
        """Test that clicking below tree view area doesn't change cursor."""
        viewer, mock_logger = self.setup_viewer()
        
        # Start with cursor at position 2
        viewer.cursor_position = 2
        
        # Click on row 36 (details/status area)
        # Tree view ends at row 35 (height 40 - 5 reserved)
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=36,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify cursor unchanged
        assert viewer.cursor_position == 2
        assert result is False
    
    def test_click_on_invalid_index_not_handled(self):
        """Test that clicking on invalid index doesn't crash."""
        viewer, mock_logger = self.setup_viewer()
        
        # Start with cursor at position 2
        viewer.cursor_position = 2
        
        # Click on row 30 (which would be item index 28, beyond visible_nodes)
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=30,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify cursor unchanged (invalid index)
        assert viewer.cursor_position == 2
        assert result is False
    
    def test_click_with_empty_visible_nodes(self):
        """Test that clicking with empty visible_nodes doesn't crash."""
        viewer, mock_logger = self.setup_viewer()
        
        # Clear visible nodes
        viewer.visible_nodes = []
        viewer.cursor_position = 0
        
        # Click on row 2
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=2,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify cursor unchanged
        assert viewer.cursor_position == 0
        assert result is False
    
    def test_non_button_down_event_not_handled(self):
        """Test that non-button-down events are not handled for cursor movement."""
        viewer, mock_logger = self.setup_viewer()
        
        # Start with cursor at position 0
        viewer.cursor_position = 0
        
        # Create mouse move event
        event = MouseEvent(
            event_type=MouseEventType.MOVE,
            column=30,
            row=3,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.NONE,
            timestamp=time.time()
        )
        
        # Handle the event
        result = viewer.handle_mouse_event(event)
        
        # Verify cursor unchanged (move events don't change cursor)
        assert viewer.cursor_position == 0
        # Note: result might be False (not handled) or True (handled by wheel scrolling check)
    
    def test_mark_dirty_called_on_cursor_change(self):
        """Test that _dirty flag is set when cursor changes."""
        viewer, mock_logger = self.setup_viewer()
        
        # Start with cursor at position 0 and clear dirty flag
        viewer.cursor_position = 0
        viewer._dirty = False
        
        # Click on row 3 (item index 2)
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=30,
            row=3,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=time.time()
        )
        
        # Handle the event
        viewer.handle_mouse_event(event)
        
        # Verify dirty flag was set
        assert viewer._dirty is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
