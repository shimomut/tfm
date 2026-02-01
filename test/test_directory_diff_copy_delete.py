#!/usr/bin/env python3
"""
Test: Directory Diff Viewer Copy and Delete Operations

This test verifies that the Directory Diff Viewer correctly handles
copy and delete operations using configured keybindings.
"""

import unittest
import tempfile
import shutil
import os
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_path import Path
from tfm_directory_diff_viewer import DirectoryDiffViewer, TreeNode, DifferenceType
from tfm_config import ConfigManager
from ttk import KeyEvent, KeyCode, ModifierKey


class TestDirectoryDiffCopyDelete(unittest.TestCase):
    """Test copy and delete operations in Directory Diff Viewer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp(prefix="test_diff_")
        self.left_dir = os.path.join(self.temp_dir, "left")
        self.right_dir = os.path.join(self.temp_dir, "right")
        
        os.makedirs(self.left_dir)
        os.makedirs(self.right_dir)
        
        # Create test files
        with open(os.path.join(self.left_dir, "file1.txt"), "w") as f:
            f.write("Left file content")
        
        with open(os.path.join(self.right_dir, "file2.txt"), "w") as f:
            f.write("Right file content")
        
        # Create mocks
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (40, 120)
        
        self.layer_stack = Mock()
        self.file_list_manager = Mock()
        self.file_list_manager.show_hidden = False
        
        # Mock file_manager and its dependencies
        self.file_manager = Mock()
        self.executor = Mock()
        
        # Set up the mock chain: file_manager -> executor
        self.file_manager.file_operations_executor = self.executor
        
        self.config_manager = Mock()
        
        # Mock key bindings
        key_bindings = Mock()
        key_bindings.find_action_for_event = Mock(return_value=None)
        key_bindings.get_keys_for_action = Mock(return_value=([], 'any'))
        key_bindings.format_key_for_display = Mock(side_effect=lambda x: x)
        self.config_manager.get_key_bindings.return_value = key_bindings
        
        # Create viewer
        self.viewer = DirectoryDiffViewer(
            self.renderer,
            Path(self.left_dir),
            Path(self.right_dir),
            self.layer_stack,
            self.file_list_manager,
            self.file_manager,  # Pass file_manager directly
            self.config_manager
        )
        
        # Wait for initial scan to complete
        import time
        time.sleep(0.5)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Stop worker threads
        self.viewer._stop_worker_threads()
        
        # Remove temporary directory
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_copy_file_from_left_pane(self):
        """Test copying a file from left pane to right pane."""
        # Set up viewer state
        self.viewer.active_pane = 'left'
        self.viewer.cursor_position = 0
        
        # Create a mock node with proper attributes
        mock_node = Mock()
        mock_node.left_path = Path(os.path.join(self.left_dir, "file1.txt"))
        mock_node.right_path = None
        mock_node.name = "file1.txt"
        mock_node.depth = 1
        mock_node.parent = Mock()
        mock_node.parent.depth = 0  # Root node
        
        self.viewer.visible_nodes = [mock_node]
        
        # Mock quick_choice_bar.show to capture the callback and simulate confirmation
        def mock_show(message, choices, callback):
            # Simulate user confirming with "Yes"
            callback(True)
        
        self.viewer.quick_choice_bar.show = mock_show
        
        # Call copy method
        self.viewer._copy_focused_file()
        
        # Verify executor.perform_copy_operation was called
        self.executor.perform_copy_operation.assert_called_once()
        args, kwargs = self.executor.perform_copy_operation.call_args
        
        # Check that the correct file and destination were passed
        self.assertEqual(len(args[0]), 1)
        self.assertEqual(args[0][0], mock_node.left_path)
        self.assertEqual(args[1], Path(self.right_dir))  # Should be root since parent.depth == 0
        self.assertTrue(kwargs.get('overwrite', False))  # Should be True for diff viewer
        self.assertIsNotNone(kwargs.get('completion_callback'))  # Should have callback
    
    def test_copy_file_from_right_pane(self):
        """Test copying a file from right pane to left pane."""
        # Set up viewer state
        self.viewer.active_pane = 'right'
        self.viewer.cursor_position = 0
        
        # Create a mock node with proper attributes
        mock_node = Mock()
        mock_node.left_path = None
        mock_node.right_path = Path(os.path.join(self.right_dir, "file2.txt"))
        mock_node.name = "file2.txt"
        mock_node.depth = 1
        mock_node.parent = Mock()
        mock_node.parent.depth = 0  # Root node
        
        self.viewer.visible_nodes = [mock_node]
        
        # Mock quick_choice_bar.show to capture the callback and simulate confirmation
        def mock_show(message, choices, callback):
            # Simulate user confirming with "Yes"
            callback(True)
        
        self.viewer.quick_choice_bar.show = mock_show
        
        # Call copy method
        self.viewer._copy_focused_file()
        
        # Verify executor.perform_copy_operation was called
        self.executor.perform_copy_operation.assert_called_once()
        args, kwargs = self.executor.perform_copy_operation.call_args
        
        # Check that the correct file and destination were passed
        self.assertEqual(len(args[0]), 1)
        self.assertEqual(args[0][0], mock_node.right_path)
        self.assertEqual(args[1], Path(self.left_dir))
    
    def test_copy_file_not_exists_on_active_pane(self):
        """Test that copy does nothing when file doesn't exist on active pane."""
        # Set up viewer state
        self.viewer.active_pane = 'left'
        self.viewer.cursor_position = 0
        
        # Create a mock node with no left_path
        mock_node = Mock()
        mock_node.left_path = None
        mock_node.right_path = Path(os.path.join(self.right_dir, "file2.txt"))
        mock_node.name = "file2.txt"
        mock_node.depth = 1
        mock_node.parent = Mock()
        mock_node.parent.depth = 0  # Root node
        
        self.viewer.visible_nodes = [mock_node]
        
        # Call copy method
        self.viewer._copy_focused_file()
        
        # Verify executor.perform_copy_operation was NOT called
        self.executor.perform_copy_operation.assert_not_called()
    
    def test_delete_file_from_left_pane(self):
        """Test deleting a file from left pane."""
        # Set up viewer state
        self.viewer.active_pane = 'left'
        self.viewer.cursor_position = 0
        
        # Create a mock node
        mock_node = Mock()
        mock_node.left_path = Path(os.path.join(self.left_dir, "file1.txt"))
        mock_node.right_path = None
        mock_node.name = "file1.txt"
        mock_node.depth = 1
        mock_node.parent = Mock()
        mock_node.parent.depth = 0  # Root node
        
        self.viewer.visible_nodes = [mock_node]
        
        # Mock quick_choice_bar.show to capture the callback and simulate confirmation
        def mock_show(message, choices, callback):
            # Simulate user confirming with "Yes"
            callback(True)
        
        self.viewer.quick_choice_bar.show = mock_show
        
        # Call delete method
        self.viewer._delete_focused_file()
        
        # Verify executor.perform_delete_operation was called
        self.executor.perform_delete_operation.assert_called_once()
        args, kwargs = self.executor.perform_delete_operation.call_args
        
        # Check that the correct file was passed
        self.assertEqual(len(args[0]), 1)
        self.assertEqual(args[0][0], mock_node.left_path)
        self.assertIsNotNone(kwargs.get('completion_callback'))  # Should have callback
    
    def test_delete_file_from_right_pane(self):
        """Test deleting a file from right pane."""
        # Set up viewer state
        self.viewer.active_pane = 'right'
        self.viewer.cursor_position = 0
        
        # Create a mock node
        mock_node = Mock()
        mock_node.left_path = None
        mock_node.right_path = Path(os.path.join(self.right_dir, "file2.txt"))
        mock_node.name = "file2.txt"
        mock_node.depth = 1
        mock_node.parent = Mock()
        mock_node.parent.depth = 0  # Root node
        
        self.viewer.visible_nodes = [mock_node]
        
        # Mock quick_choice_bar.show to capture the callback and simulate confirmation
        def mock_show(message, choices, callback):
            # Simulate user confirming with "Yes"
            callback(True)
        
        self.viewer.quick_choice_bar.show = mock_show
        
        # Call delete method
        self.viewer._delete_focused_file()
        
        # Verify executor.perform_delete_operation was called
        self.executor.perform_delete_operation.assert_called_once()
        args, kwargs = self.executor.perform_delete_operation.call_args
        
        # Check that the correct file was passed
        self.assertEqual(len(args[0]), 1)
        self.assertEqual(args[0][0], mock_node.right_path)
    
    def test_delete_file_not_exists_on_active_pane(self):
        """Test that delete does nothing when file doesn't exist on active pane."""
        # Set up viewer state
        self.viewer.active_pane = 'left'
        self.viewer.cursor_position = 0
        
        # Create a mock node with no left_path
        mock_node = Mock()
        mock_node.left_path = None
        mock_node.right_path = Path(os.path.join(self.right_dir, "file2.txt"))
        mock_node.name = "file2.txt"
        mock_node.depth = 1
        mock_node.parent = Mock()
        mock_node.parent.depth = 0  # Root node
        
        self.viewer.visible_nodes = [mock_node]
        
        # Call delete method
        self.viewer._delete_focused_file()
        
        # Verify executor.perform_delete_operation was NOT called
        self.executor.perform_delete_operation.assert_not_called()
    
    def test_copy_keybinding_triggers_copy(self):
        """Test that pressing the copy key triggers copy operation."""
        # Set up viewer state
        self.viewer.active_pane = 'left'
        self.viewer.cursor_position = 0
        
        # Create a mock node
        mock_node = Mock()
        mock_node.left_path = Path(os.path.join(self.left_dir, "file1.txt"))
        mock_node.right_path = None
        mock_node.name = "file1.txt"
        mock_node.depth = 1
        mock_node.parent = Mock()
        mock_node.parent.depth = 0  # Root node
        
        self.viewer.visible_nodes = [mock_node]
        
        # Mock quick_choice_bar.show to capture the callback and simulate confirmation
        def mock_show(message, choices, callback):
            # Simulate user confirming with "Yes"
            callback(True)
        
        self.viewer.quick_choice_bar.show = mock_show
        
        # Mock key bindings to return 'copy_files' action
        key_bindings = self.config_manager.get_key_bindings.return_value
        key_bindings.find_action_for_event.return_value = 'copy_files'
        
        # Create KeyEvent for 'C' key
        event = KeyEvent(key_code=KeyCode.C, modifiers=ModifierKey.NONE, char='c')
        
        # Handle the key event
        result = self.viewer.handle_key_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify copy was called
        self.executor.perform_copy_operation.assert_called_once()
    
    def test_delete_keybinding_triggers_delete(self):
        """Test that pressing the delete key triggers delete operation."""
        # Set up viewer state
        self.viewer.active_pane = 'left'
        self.viewer.cursor_position = 0
        
        # Create a mock node
        mock_node = Mock()
        mock_node.left_path = Path(os.path.join(self.left_dir, "file1.txt"))
        mock_node.right_path = None
        mock_node.name = "file1.txt"
        mock_node.depth = 1
        mock_node.parent = Mock()
        mock_node.parent.depth = 0  # Root node
        
        self.viewer.visible_nodes = [mock_node]
        
        # Mock quick_choice_bar.show to capture the callback and simulate confirmation
        def mock_show(message, choices, callback):
            # Simulate user confirming with "Yes"
            callback(True)
        
        self.viewer.quick_choice_bar.show = mock_show
        
        # Mock key bindings to return 'delete_files' action
        key_bindings = self.config_manager.get_key_bindings.return_value
        key_bindings.find_action_for_event.return_value = 'delete_files'
        
        # Create KeyEvent for 'K' key
        event = KeyEvent(key_code=KeyCode.K, modifiers=ModifierKey.NONE, char='k')
        
        # Handle the key event
        result = self.viewer.handle_key_event(event)
        
        # Verify event was handled
        self.assertTrue(result)
        
        # Verify delete was called
        self.executor.perform_delete_operation.assert_called_once()
    
    def test_copy_without_file_operations_ui(self):
        """Test that copy logs warning when file_operations_ui is not available."""
        # Create viewer without file_operations_ui
        viewer = DirectoryDiffViewer(
            self.renderer,
            Path(self.left_dir),
            Path(self.right_dir),
            self.layer_stack,
            self.file_list_manager,
            None,  # No file_operations_ui
            self.config_manager
        )
        
        # Set up viewer state
        viewer.active_pane = 'left'
        viewer.cursor_position = 0
        
        # Create a mock node
        mock_node = Mock()
        mock_node.left_path = Path(os.path.join(self.left_dir, "file1.txt"))
        mock_node.right_path = None
        mock_node.name = "file1.txt"
        mock_node.depth = 1
        mock_node.parent = Mock()
        mock_node.parent.depth = 0  # Root node
        
        viewer.visible_nodes = [mock_node]
        
        # Call copy method - should log warning and return
        viewer._copy_focused_file()
        
        # No exception should be raised
        # (Logger warning is tested separately)
    
    def test_delete_without_file_operations_ui(self):
        """Test that delete logs warning when file_operations_ui is not available."""
        # Create viewer without file_operations_ui
        viewer = DirectoryDiffViewer(
            self.renderer,
            Path(self.left_dir),
            Path(self.right_dir),
            self.layer_stack,
            self.file_list_manager,
            None,  # No file_operations_ui
            self.config_manager
        )
        
        # Set up viewer state
        viewer.active_pane = 'left'
        viewer.cursor_position = 0
        
        # Create a mock node
        mock_node = Mock()
        mock_node.left_path = Path(os.path.join(self.left_dir, "file1.txt"))
        mock_node.right_path = None
        mock_node.name = "file1.txt"
        mock_node.depth = 1
        mock_node.parent = Mock()
        mock_node.parent.depth = 0  # Root node
        
        viewer.visible_nodes = [mock_node]
        
        # Call delete method - should log warning and return
        viewer._delete_focused_file()
        
        # No exception should be raised
        # (Logger warning is tested separately)


if __name__ == '__main__':
    unittest.main()
