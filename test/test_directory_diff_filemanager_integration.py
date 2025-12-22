#!/usr/bin/env python3
"""
Test FileManager integration with DirectoryDiffViewer.

This test verifies that the directory diff viewer can be invoked from
FileManager and properly integrates with the UI layer stack.
"""

import unittest
import tempfile
import shutil
from pathlib import Path as StdPath
from unittest.mock import Mock, MagicMock, patch

# Import from src for test modules
import sys
sys.path.insert(0, 'src')

from tfm_path import Path
from tfm_main import FileManager
from tfm_directory_diff_viewer import DirectoryDiffViewer
from ttk import KeyEvent, KeyCode, ModifierKey


class TestDirectoryDiffFileManagerIntegration(unittest.TestCase):
    """Test FileManager integration with DirectoryDiffViewer"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.left_dir = StdPath(self.temp_dir) / "left"
        self.right_dir = StdPath(self.temp_dir) / "right"
        self.left_dir.mkdir()
        self.right_dir.mkdir()
        
        # Create some test files
        (self.left_dir / "file1.txt").write_text("content1")
        (self.left_dir / "file2.txt").write_text("content2")
        (self.right_dir / "file2.txt").write_text("content2")
        (self.right_dir / "file3.txt").write_text("content3")
        
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (40, 120)
        self.mock_renderer.set_cursor_visibility = Mock()
        self.mock_renderer.set_event_callback = Mock()
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_show_directory_diff_with_valid_directories(self):
        """Test invoking directory diff viewer with valid directories"""
        # Create FileManager with test directories
        fm = FileManager(
            self.mock_renderer,
            left_dir=str(self.left_dir),
            right_dir=str(self.right_dir)
        )
        
        # Verify initial state (use string comparison to avoid Path object comparison issues)
        self.assertEqual(str(fm.pane_manager.left_pane['path']), str(self.left_dir))
        self.assertEqual(str(fm.pane_manager.right_pane['path']), str(self.right_dir))
        
        # Call show_directory_diff
        fm.show_directory_diff()
        
        # Verify that a layer was pushed onto the stack
        self.assertEqual(len(fm.ui_layer_stack._layers), 2)  # FileManager + DirectoryDiffViewer
        
        # Verify the top layer is a DirectoryDiffViewer
        top_layer = fm.ui_layer_stack.get_top_layer()
        self.assertIsInstance(top_layer, DirectoryDiffViewer)
        
        # Verify the viewer has the correct paths (use string comparison)
        self.assertEqual(str(top_layer.left_path), str(self.left_dir))
        self.assertEqual(str(top_layer.right_path), str(self.right_dir))
    
    def test_show_directory_diff_with_nonexistent_left_directory(self):
        """Test invoking directory diff viewer with nonexistent left directory"""
        # Create FileManager with nonexistent left directory
        nonexistent_dir = StdPath(self.temp_dir) / "nonexistent"
        
        fm = FileManager(
            self.mock_renderer,
            left_dir=str(nonexistent_dir),
            right_dir=str(self.right_dir)
        )
        
        # The FileManager should fall back to current directory for nonexistent paths
        # So we need to manually set an invalid path
        fm.pane_manager.left_pane['path'] = Path(nonexistent_dir)
        
        # Call show_directory_diff
        fm.show_directory_diff()
        
        # Verify that no layer was pushed (error case)
        self.assertEqual(len(fm.ui_layer_stack._layers), 1)  # Only FileManager
    
    def test_show_directory_diff_with_file_instead_of_directory(self):
        """Test invoking directory diff viewer with file instead of directory"""
        # Create a file in the temp directory
        test_file = StdPath(self.temp_dir) / "test_file.txt"
        test_file.write_text("test content")
        
        fm = FileManager(
            self.mock_renderer,
            left_dir=str(test_file),  # Pass file instead of directory
            right_dir=str(self.right_dir)
        )
        
        # The FileManager should fall back to current directory for invalid paths
        # So we need to manually set a file path
        fm.pane_manager.left_pane['path'] = Path(test_file)
        
        # Call show_directory_diff
        fm.show_directory_diff()
        
        # Verify that no layer was pushed (error case)
        self.assertEqual(len(fm.ui_layer_stack._layers), 1)  # Only FileManager
    
    def test_directory_diff_key_binding(self):
        """Test that the directory diff action can be invoked"""
        fm = FileManager(
            self.mock_renderer,
            left_dir=str(self.left_dir),
            right_dir=str(self.right_dir)
        )
        
        # Directly call the show_directory_diff method (simulating key binding)
        fm.show_directory_diff()
        
        # Verify that a layer was pushed onto the stack
        self.assertEqual(len(fm.ui_layer_stack._layers), 2)  # FileManager + DirectoryDiffViewer
        
        # Verify the top layer is a DirectoryDiffViewer
        top_layer = fm.ui_layer_stack.get_top_layer()
        self.assertIsInstance(top_layer, DirectoryDiffViewer)
    
    def test_directory_diff_viewer_closes_properly(self):
        """Test that directory diff viewer can be closed and returns to FileManager"""
        fm = FileManager(
            self.mock_renderer,
            left_dir=str(self.left_dir),
            right_dir=str(self.right_dir)
        )
        
        # Open directory diff viewer
        fm.show_directory_diff()
        
        # Verify viewer is open
        self.assertEqual(len(fm.ui_layer_stack._layers), 2)
        
        # Get the viewer
        viewer = fm.ui_layer_stack.get_top_layer()
        
        # Close the viewer by setting should_close flag
        viewer._should_close = True
        
        # Pop the layer using the correct method
        fm.ui_layer_stack.pop()
        
        # Verify we're back to FileManager only
        self.assertEqual(len(fm.ui_layer_stack._layers), 1)
        self.assertIsInstance(fm.ui_layer_stack.get_top_layer(), FileManager)


if __name__ == '__main__':
    unittest.main()
