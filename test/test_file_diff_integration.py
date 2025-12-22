"""
Tests for file diff viewer integration in DirectoryDiffViewer.

This module tests the functionality of opening a file diff viewer from the
directory diff viewer when the cursor is on a content-different file node.
"""

import unittest
import tempfile
import shutil
from pathlib import Path as StdPath
from unittest.mock import Mock, MagicMock, patch

from src.tfm_directory_diff_viewer import DirectoryDiffViewer, DifferenceType, TreeNode
from tfm_path import Path
from ttk import KeyEvent, KeyCode, ModifierKey


class TestFileDiffIntegration(unittest.TestCase):
    """Test file diff viewer integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp(prefix="tfm_test_file_diff_")
        self.left_dir = StdPath(self.temp_dir) / "left"
        self.right_dir = StdPath(self.temp_dir) / "right"
        self.left_dir.mkdir()
        self.right_dir.mkdir()
        
        # Create test files
        (self.left_dir / "different.txt").write_text("Left content")
        (self.right_dir / "different.txt").write_text("Right content")
        
        (self.left_dir / "identical.txt").write_text("Same content")
        (self.right_dir / "identical.txt").write_text("Same content")
        
        (self.left_dir / "only_left.txt").write_text("Only left")
        
        # Create mock renderer
        self.renderer = Mock()
        self.renderer.get_size.return_value = (80, 24)
        
        # Create mock layer stack
        self.layer_stack = Mock()
        self.layer_stack.push = Mock()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_open_file_diff_on_content_different_file(self):
        """Test opening file diff viewer on a content-different file."""
        # Create viewer with layer_stack
        with patch('src.tfm_directory_diff_viewer.DirectoryDiffViewer.start_scan'):
            viewer = DirectoryDiffViewer(
                self.renderer,
                Path(str(self.left_dir)),
                Path(str(self.right_dir)),
                self.layer_stack
            )
        
        # Set up test tree with a content-different file
        left_path = Path(str(self.left_dir / "different.txt"))
        right_path = Path(str(self.right_dir / "different.txt"))
        
        node = TreeNode(
            name="different.txt",
            left_path=left_path,
            right_path=right_path,
            is_directory=False,
            difference_type=DifferenceType.CONTENT_DIFFERENT,
            depth=1,
            is_expanded=False,
            children=[],
            parent=None
        )
        
        viewer.visible_nodes = [node]
        viewer.cursor_position = 0
        
        # Call open_file_diff
        viewer.open_file_diff(0)
        
        # Verify DiffViewer was pushed onto layer stack
        self.layer_stack.push.assert_called_once()
        
        # Verify the pushed layer is a DiffViewer with correct paths
        pushed_viewer = self.layer_stack.push.call_args[0][0]
        self.assertEqual(pushed_viewer.file1_path, left_path)
        self.assertEqual(pushed_viewer.file2_path, right_path)
    
    def test_open_file_diff_ignores_directory_nodes(self):
        """Test that open_file_diff ignores directory nodes."""
        # Create viewer with layer_stack
        with patch('src.tfm_directory_diff_viewer.DirectoryDiffViewer.start_scan'):
            viewer = DirectoryDiffViewer(
                self.renderer,
                Path(str(self.left_dir)),
                Path(str(self.right_dir)),
                self.layer_stack
            )
        
        # Set up test tree with a directory node
        node = TreeNode(
            name="subdir",
            left_path=Path(str(self.left_dir / "subdir")),
            right_path=Path(str(self.right_dir / "subdir")),
            is_directory=True,
            difference_type=DifferenceType.CONTAINS_DIFFERENCE,
            depth=1,
            is_expanded=False,
            children=[],
            parent=None
        )
        
        viewer.visible_nodes = [node]
        viewer.cursor_position = 0
        
        # Call open_file_diff
        viewer.open_file_diff(0)
        
        # Verify DiffViewer was NOT pushed
        self.layer_stack.push.assert_not_called()
    
    def test_open_file_diff_ignores_non_content_different_files(self):
        """Test that open_file_diff ignores files that are not content-different."""
        # Create viewer with layer_stack
        with patch('src.tfm_directory_diff_viewer.DirectoryDiffViewer.start_scan'):
            viewer = DirectoryDiffViewer(
                self.renderer,
                Path(str(self.left_dir)),
                Path(str(self.right_dir)),
                self.layer_stack
            )
        
        # Test with identical file
        node = TreeNode(
            name="identical.txt",
            left_path=Path(str(self.left_dir / "identical.txt")),
            right_path=Path(str(self.right_dir / "identical.txt")),
            is_directory=False,
            difference_type=DifferenceType.IDENTICAL,
            depth=1,
            is_expanded=False,
            children=[],
            parent=None
        )
        
        viewer.visible_nodes = [node]
        viewer.cursor_position = 0
        
        # Call open_file_diff
        viewer.open_file_diff(0)
        
        # Verify DiffViewer was NOT pushed
        self.layer_stack.push.assert_not_called()
    
    def test_open_file_diff_ignores_only_left_files(self):
        """Test that open_file_diff ignores files that exist only on one side."""
        # Create viewer with layer_stack
        with patch('src.tfm_directory_diff_viewer.DirectoryDiffViewer.start_scan'):
            viewer = DirectoryDiffViewer(
                self.renderer,
                Path(str(self.left_dir)),
                Path(str(self.right_dir)),
                self.layer_stack
            )
        
        # Test with only-left file
        node = TreeNode(
            name="only_left.txt",
            left_path=Path(str(self.left_dir / "only_left.txt")),
            right_path=None,
            is_directory=False,
            difference_type=DifferenceType.ONLY_LEFT,
            depth=1,
            is_expanded=False,
            children=[],
            parent=None
        )
        
        viewer.visible_nodes = [node]
        viewer.cursor_position = 0
        
        # Call open_file_diff
        viewer.open_file_diff(0)
        
        # Verify DiffViewer was NOT pushed
        self.layer_stack.push.assert_not_called()
    
    def test_open_file_diff_without_layer_stack(self):
        """Test that open_file_diff handles missing layer_stack gracefully."""
        # Create viewer WITHOUT layer_stack
        with patch('src.tfm_directory_diff_viewer.DirectoryDiffViewer.start_scan'):
            viewer = DirectoryDiffViewer(
                self.renderer,
                Path(str(self.left_dir)),
                Path(str(self.right_dir)),
                None  # No layer_stack
            )
        
        # Set up test tree with a content-different file
        node = TreeNode(
            name="different.txt",
            left_path=Path(str(self.left_dir / "different.txt")),
            right_path=Path(str(self.right_dir / "different.txt")),
            is_directory=False,
            difference_type=DifferenceType.CONTENT_DIFFERENT,
            depth=1,
            is_expanded=False,
            children=[],
            parent=None
        )
        
        viewer.visible_nodes = [node]
        viewer.cursor_position = 0
        
        # Call open_file_diff - should not raise exception
        viewer.open_file_diff(0)
        
        # No assertion needed - just verify it doesn't crash
    
    def test_ctrl_enter_key_binding_opens_file_diff(self):
        """Test that Ctrl+Enter key binding triggers file diff opening."""
        # Create viewer with layer_stack
        with patch('src.tfm_directory_diff_viewer.DirectoryDiffViewer.start_scan'):
            viewer = DirectoryDiffViewer(
                self.renderer,
                Path(str(self.left_dir)),
                Path(str(self.right_dir)),
                self.layer_stack
            )
        
        # Set up test tree with a content-different file
        left_path = Path(str(self.left_dir / "different.txt"))
        right_path = Path(str(self.right_dir / "different.txt"))
        
        node = TreeNode(
            name="different.txt",
            left_path=left_path,
            right_path=right_path,
            is_directory=False,
            difference_type=DifferenceType.CONTENT_DIFFERENT,
            depth=1,
            is_expanded=False,
            children=[],
            parent=None
        )
        
        viewer.visible_nodes = [node]
        viewer.cursor_position = 0
        viewer.scan_in_progress = False
        
        # Create Ctrl+Enter key event
        event = KeyEvent(
            key_code=KeyCode.ENTER,
            char='\r',
            modifiers=ModifierKey.CONTROL
        )
        
        # Handle the event
        result = viewer.handle_key_event(event)
        
        # Verify event was consumed
        self.assertTrue(result)
        
        # Verify DiffViewer was pushed onto layer stack
        self.layer_stack.push.assert_called_once()
    
    def test_invalid_node_index_handled_gracefully(self):
        """Test that invalid node indices are handled gracefully."""
        # Create viewer with layer_stack
        with patch('src.tfm_directory_diff_viewer.DirectoryDiffViewer.start_scan'):
            viewer = DirectoryDiffViewer(
                self.renderer,
                Path(str(self.left_dir)),
                Path(str(self.right_dir)),
                self.layer_stack
            )
        
        viewer.visible_nodes = []
        
        # Call open_file_diff with invalid indices
        viewer.open_file_diff(-1)  # Negative index
        viewer.open_file_diff(0)   # Out of bounds
        viewer.open_file_diff(100) # Way out of bounds
        
        # Verify DiffViewer was NOT pushed
        self.layer_stack.push.assert_not_called()


if __name__ == '__main__':
    unittest.main()
