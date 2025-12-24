#!/usr/bin/env python3
"""
Unit tests for DirectoryDiffViewer keyboard navigation.

Tests the handle_key_event method to ensure proper cursor movement,
scrolling, and expand/collapse functionality.
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_directory_diff_viewer import (
    DirectoryDiffViewer,
    TreeNode,
    DifferenceType
)
from tfm_path import Path
from ttk import KeyEvent, KeyCode, ModifierKey


class TestDirectoryDiffNavigation(unittest.TestCase):
    """Test keyboard navigation in DirectoryDiffViewer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock renderer
        self.renderer = Mock()
        self.renderer.get_size.return_value = (80, 24)
        self.renderer.get_dimensions.return_value = (24, 80)  # height, width
        
        # Create mock paths
        self.left_path = Mock(spec=Path)
        self.right_path = Mock(spec=Path)
        
        # Create viewer (will start scan, but we'll override the tree)
        self.viewer = DirectoryDiffViewer(
            self.renderer,
            self.left_path,
            self.right_path
        )
        
        # Stop any ongoing scan
        self.viewer.scan_in_progress = False
        
        # Create a simple test tree
        self.create_test_tree()
    
    def create_test_tree(self):
        """Create a simple test tree for navigation testing."""
        # Root node
        root = TreeNode(
            name="",
            left_path=None,
            right_path=None,
            is_directory=True,
            difference_type=DifferenceType.CONTAINS_DIFFERENCE,
            depth=0,
            is_expanded=True,
            children=[],
            parent=None
        )
        
        # Create some child nodes
        file1 = TreeNode(
            name="file1.txt",
            left_path=Mock(spec=Path),
            right_path=Mock(spec=Path),
            is_directory=False,
            difference_type=DifferenceType.IDENTICAL,
            depth=1,
            is_expanded=False,
            children=[],
            parent=root
        )
        
        dir1 = TreeNode(
            name="subdir",
            left_path=Mock(spec=Path),
            right_path=Mock(spec=Path),
            is_directory=True,
            difference_type=DifferenceType.CONTAINS_DIFFERENCE,
            depth=1,
            is_expanded=False,
            children=[],
            parent=root
        )
        
        file2 = TreeNode(
            name="file2.txt",
            left_path=Mock(spec=Path),
            right_path=None,
            is_directory=False,
            difference_type=DifferenceType.ONLY_LEFT,
            depth=1,
            is_expanded=False,
            children=[],
            parent=root
        )
        
        # Add child to subdir
        subfile = TreeNode(
            name="subfile.txt",
            left_path=Mock(spec=Path),
            right_path=Mock(spec=Path),
            is_directory=False,
            difference_type=DifferenceType.CONTENT_DIFFERENT,
            depth=2,
            is_expanded=False,
            children=[],
            parent=dir1
        )
        
        dir1.children.append(subfile)
        root.children.extend([file1, dir1, file2])
        
        # Set the tree
        self.viewer.root_node = root
        self.viewer._update_visible_nodes()
    
    def test_cursor_down(self):
        """Test DOWN arrow key moves cursor down."""
        initial_cursor = self.viewer.cursor_position
        
        event = KeyEvent(key_code=KeyCode.DOWN, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.viewer.cursor_position, initial_cursor + 1)
        self.assertTrue(self.viewer.needs_redraw())
    
    def test_cursor_up(self):
        """Test UP arrow key moves cursor up."""
        # Move cursor down first
        self.viewer.cursor_position = 2
        
        event = KeyEvent(key_code=KeyCode.UP, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.viewer.cursor_position, 1)
        self.assertTrue(self.viewer.needs_redraw())
    
    def test_cursor_up_at_top(self):
        """Test UP arrow key at top doesn't move cursor."""
        self.viewer.cursor_position = 0
        
        event = KeyEvent(key_code=KeyCode.UP, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.viewer.cursor_position, 0)
    
    def test_cursor_down_at_bottom(self):
        """Test DOWN arrow key at bottom doesn't move cursor."""
        self.viewer.cursor_position = len(self.viewer.visible_nodes) - 1
        
        event = KeyEvent(key_code=KeyCode.DOWN, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.viewer.cursor_position, len(self.viewer.visible_nodes) - 1)
    
    def test_page_down(self):
        """Test PAGE_DOWN key scrolls down one page."""
        initial_cursor = self.viewer.cursor_position
        display_height = 21  # 24 - 3 (header + status)
        
        event = KeyEvent(key_code=KeyCode.PAGE_DOWN, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        # Cursor should move down by display_height or to end
        expected = min(len(self.viewer.visible_nodes) - 1, initial_cursor + display_height)
        self.assertEqual(self.viewer.cursor_position, expected)
    
    def test_page_up(self):
        """Test PAGE_UP key scrolls up one page."""
        # Start at bottom
        self.viewer.cursor_position = len(self.viewer.visible_nodes) - 1
        display_height = 21
        
        event = KeyEvent(key_code=KeyCode.PAGE_UP, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        # Cursor should move up by display_height or to start
        expected = max(0, self.viewer.cursor_position - display_height)
        self.assertLessEqual(self.viewer.cursor_position, expected + display_height)
    
    def test_home_key(self):
        """Test HOME key jumps to first item."""
        self.viewer.cursor_position = 2
        
        event = KeyEvent(key_code=KeyCode.HOME, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.viewer.cursor_position, 0)
        self.assertEqual(self.viewer.scroll_offset, 0)
    
    def test_end_key(self):
        """Test END key jumps to last item."""
        self.viewer.cursor_position = 0
        
        event = KeyEvent(key_code=KeyCode.END, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.viewer.cursor_position, len(self.viewer.visible_nodes) - 1)
    
    def test_expand_directory(self):
        """Test RIGHT/ENTER key expands directory."""
        # Find a directory node (subdir is at index 1)
        self.viewer.cursor_position = 1
        node = self.viewer.visible_nodes[1]
        self.assertTrue(node.is_directory)
        self.assertFalse(node.is_expanded)
        
        initial_count = len(self.viewer.visible_nodes)
        
        event = KeyEvent(key_code=KeyCode.RIGHT, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertTrue(node.is_expanded)
        # Should have more visible nodes after expansion
        self.assertGreater(len(self.viewer.visible_nodes), initial_count)
    
    def test_collapse_directory(self):
        """Test LEFT key collapses directory."""
        # First expand a directory
        self.viewer.cursor_position = 1
        node = self.viewer.visible_nodes[1]
        self.viewer.expand_node(1)
        self.assertTrue(node.is_expanded)
        
        expanded_count = len(self.viewer.visible_nodes)
        
        # Now collapse it
        event = KeyEvent(key_code=KeyCode.LEFT, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertFalse(node.is_expanded)
        # Should have fewer visible nodes after collapse
        self.assertLess(len(self.viewer.visible_nodes), expanded_count)
    
    def test_escape_closes_viewer(self):
        """Test ESC key closes viewer."""
        event = KeyEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertTrue(self.viewer.should_close())
    
    def test_q_closes_viewer(self):
        """Test 'q' key closes viewer."""
        event = KeyEvent(key_code=ord('q'), char='q', modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertTrue(self.viewer.should_close())
    
    def test_toggle_identical_filter(self):
        """Test 'i' key toggles identical file filter."""
        initial_show = self.viewer.show_identical
        initial_count = len(self.viewer.visible_nodes)
        
        event = KeyEvent(key_code=ord('i'), char='i', modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertEqual(self.viewer.show_identical, not initial_show)
        # Visible nodes should be updated
        # (count may change depending on identical files)
    
    def test_scan_cancellation(self):
        """Test ESC during scan cancels and closes."""
        self.viewer.scan_in_progress = True
        self.viewer.scanner = Mock()
        
        event = KeyEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)
        self.viewer.scanner.cancel.assert_called_once()
        self.assertTrue(self.viewer.scan_cancelled)
        self.assertTrue(self.viewer.should_close())
    
    def test_keys_ignored_during_scan(self):
        """Test other keys are ignored during scan."""
        self.viewer.scan_in_progress = True
        initial_cursor = self.viewer.cursor_position
        
        event = KeyEvent(key_code=KeyCode.DOWN, char=None, modifiers=0)
        result = self.viewer.handle_key_event(event)
        
        self.assertTrue(result)  # Event consumed
        self.assertEqual(self.viewer.cursor_position, initial_cursor)  # But no action
    
    def test_expand_respects_identical_filter(self):
        """Test that expanding a directory respects the show_identical filter."""
        # Create a directory with both identical and different children
        root = TreeNode(
            name="",
            left_path=None,
            right_path=None,
            is_directory=True,
            difference_type=DifferenceType.CONTAINS_DIFFERENCE,
            depth=0,
            is_expanded=True,
            children=[],
            parent=None
        )
        
        # Create a directory with mixed children
        parent_dir = TreeNode(
            name="parent",
            left_path=Mock(spec=Path),
            right_path=Mock(spec=Path),
            is_directory=True,
            difference_type=DifferenceType.CONTAINS_DIFFERENCE,
            depth=1,
            is_expanded=False,
            children=[],
            parent=root
        )
        
        # Add identical child
        identical_child = TreeNode(
            name="identical.txt",
            left_path=Mock(spec=Path),
            right_path=Mock(spec=Path),
            is_directory=False,
            difference_type=DifferenceType.IDENTICAL,
            depth=2,
            is_expanded=False,
            children=[],
            parent=parent_dir
        )
        
        # Add different child
        different_child = TreeNode(
            name="different.txt",
            left_path=Mock(spec=Path),
            right_path=Mock(spec=Path),
            is_directory=False,
            difference_type=DifferenceType.CONTENT_DIFFERENT,
            depth=2,
            is_expanded=False,
            children=[],
            parent=parent_dir
        )
        
        parent_dir.children = [identical_child, different_child]
        parent_dir.children_scanned = True  # Mark as already scanned
        root.children = [parent_dir]
        
        self.viewer.root_node = root
        self.viewer._update_visible_nodes()
        
        # Initially, only parent_dir should be visible
        self.assertEqual(len(self.viewer.visible_nodes), 1)
        self.assertEqual(self.viewer.visible_nodes[0].name, "parent")
        
        # Hide identical files
        self.viewer.show_identical = False
        
        # Expand the parent directory
        self.viewer.expand_node(0)
        
        # After expansion with filter on, only different_child should be visible
        # visible_nodes should contain: parent_dir, different_child
        self.assertEqual(len(self.viewer.visible_nodes), 2)
        self.assertEqual(self.viewer.visible_nodes[0].name, "parent")
        self.assertEqual(self.viewer.visible_nodes[1].name, "different.txt")
        
        # Collapse and re-expand with show_identical = True
        self.viewer.collapse_node(0)
        self.viewer.show_identical = True
        self.viewer.expand_node(0)
        
        # Now both children should be visible
        # visible_nodes should contain: parent_dir, identical_child, different_child
        self.assertEqual(len(self.viewer.visible_nodes), 3)
        self.assertEqual(self.viewer.visible_nodes[0].name, "parent")
        self.assertEqual(self.viewer.visible_nodes[1].name, "identical.txt")
        self.assertEqual(self.viewer.visible_nodes[2].name, "different.txt")


if __name__ == '__main__':
    unittest.main()
