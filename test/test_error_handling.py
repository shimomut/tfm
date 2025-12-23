"""
Tests for error handling in DirectoryDiffViewer.

This module tests the error handling capabilities including:
- Permission errors during scanning
- I/O errors during file comparison
- Empty or identical directories
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path as StdPath
import tempfile
import os

from src.tfm_directory_diff_viewer import (
    DirectoryDiffViewer,
    DirectoryScanner,
    DiffEngine,
    FileInfo,
    TreeNode,
    DifferenceType
)
from tfm_path import Path


class TestPermissionErrorHandling(unittest.TestCase):
    """Test handling of permission errors during scanning."""
    
    def test_scanner_handles_permission_error_gracefully(self):
        """Test that scanner continues when encountering permission errors."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            left_dir = StdPath(tmpdir) / "left"
            right_dir = StdPath(tmpdir) / "right"
            left_dir.mkdir()
            right_dir.mkdir()
            
            # Create some accessible files
            (left_dir / "accessible.txt").write_text("content")
            (right_dir / "accessible.txt").write_text("content")
            
            # Create scanner
            scanner = DirectoryScanner(
                Path(str(left_dir)),
                Path(str(right_dir)),
                None  # No progress callback
            )
            
            # Scan should complete without raising exceptions
            left_files, right_files = scanner.scan()
            
            # Should have found the accessible files
            self.assertIn("accessible.txt", left_files)
            self.assertIn("accessible.txt", right_files)
    
    def test_inaccessible_files_marked_in_fileinfo(self):
        """Test that inaccessible files are marked with error information."""
        # Create FileInfo for an inaccessible file
        file_info = FileInfo(
            path=Path("/fake/path"),
            relative_path="test.txt",
            is_directory=False,
            size=0,
            mtime=0.0,
            is_accessible=False,
            error_message="Permission denied"
        )
        
        self.assertFalse(file_info.is_accessible)
        self.assertIsNotNone(file_info.error_message)
        self.assertIn("Permission denied", file_info.error_message)


class TestFileComparisonErrorHandling(unittest.TestCase):
    """Test handling of I/O errors during file comparison."""
    
    def test_comparison_error_stored_in_engine(self):
        """Test that file comparison errors are stored in DiffEngine."""
        # Create mock files
        left_files = {
            "test.txt": FileInfo(
                path=Path("/left/test.txt"),
                relative_path="test.txt",
                is_directory=False,
                size=100,
                mtime=1234567890.0,
                is_accessible=True
            )
        }
        right_files = {
            "test.txt": FileInfo(
                path=Path("/right/test.txt"),
                relative_path="test.txt",
                is_directory=False,
                size=100,
                mtime=1234567890.0,
                is_accessible=True
            )
        }
        
        engine = DiffEngine(left_files, right_files)
        
        # Mock the file paths to raise an error when opened
        with patch.object(Path, 'open', side_effect=PermissionError("Access denied")):
            with patch.object(Path, 'stat', return_value=Mock(st_size=100)):
                result = engine.compare_file_content(
                    Path("/left/test.txt"),
                    Path("/right/test.txt")
                )
                
                # Should return False (files considered different)
                self.assertFalse(result)
                
                # Should have stored the error
                error_key = f"{Path('/left/test.txt')}|{Path('/right/test.txt')}"
                self.assertIn(error_key, engine.comparison_errors)
    
    def test_comparison_error_logged(self):
        """Test that file comparison errors are logged."""
        left_files = {
            "test.txt": FileInfo(
                path=Path("/left/test.txt"),
                relative_path="test.txt",
                is_directory=False,
                size=100,
                mtime=1234567890.0,
                is_accessible=True
            )
        }
        right_files = {
            "test.txt": FileInfo(
                path=Path("/right/test.txt"),
                relative_path="test.txt",
                is_directory=False,
                size=100,
                mtime=1234567890.0,
                is_accessible=True
            )
        }
        
        engine = DiffEngine(left_files, right_files)
        
        # Mock the file operations to raise an error
        with patch.object(Path, 'open', side_effect=IOError("Read error")):
            with patch.object(Path, 'stat', return_value=Mock(st_size=100)):
                # Should not raise exception
                result = engine.compare_file_content(
                    Path("/left/test.txt"),
                    Path("/right/test.txt")
                )
                
                # Should return False
                self.assertFalse(result)


class TestEmptyOrIdenticalDirectories(unittest.TestCase):
    """Test handling of empty or identical directories."""
    
    def test_empty_directories_handled(self):
        """Test that empty directories are handled gracefully."""
        # Create empty file dictionaries
        left_files = {}
        right_files = {}
        
        engine = DiffEngine(left_files, right_files)
        root = engine.build_tree()
        
        # Root should exist but have no children
        self.assertIsNotNone(root)
        self.assertEqual(len(root.children), 0)
        self.assertEqual(root.difference_type, DifferenceType.IDENTICAL)
    
    def test_identical_directories_classified_correctly(self):
        """Test that identical directories are classified as IDENTICAL."""
        # Create identical file dictionaries
        left_files = {
            "test.txt": FileInfo(
                path=Path("/left/test.txt"),
                relative_path="test.txt",
                is_directory=False,
                size=100,
                mtime=1234567890.0,
                is_accessible=True
            )
        }
        right_files = {
            "test.txt": FileInfo(
                path=Path("/right/test.txt"),
                relative_path="test.txt",
                is_directory=False,
                size=100,
                mtime=1234567890.0,
                is_accessible=True
            )
        }
        
        engine = DiffEngine(left_files, right_files)
        
        # Mock file comparison to return True (identical)
        with patch.object(engine, 'compare_file_content', return_value=True):
            root = engine.build_tree()
            
            # Root should have one child
            self.assertEqual(len(root.children), 1)
            
            # Child should be classified as IDENTICAL
            child = root.children[0]
            self.assertEqual(child.difference_type, DifferenceType.IDENTICAL)


class TestErrorCountInStatusBar(unittest.TestCase):
    """Test that error count is displayed in status bar."""
    
    def test_error_count_includes_permission_errors(self):
        """Test that permission errors are counted."""
        # Create a mock renderer
        renderer = Mock()
        renderer.get_size.return_value = (80, 24)
        
        # Create viewer with mock paths
        with patch('src.tfm_directory_diff_viewer.DirectoryDiffViewer.start_scan'):
            viewer = DirectoryDiffViewer(renderer, Path("/left"), Path("/right"))
            
            # Set up test data with permission error
            viewer.left_files = {
                "error.txt": FileInfo(
                    path=Path("/left/error.txt"),
                    relative_path="error.txt",
                    is_directory=False,
                    size=0,
                    mtime=0.0,
                    is_accessible=False,
                    error_message="Permission denied"
                )
            }
            viewer.right_files = {}
            viewer.comparison_errors = {}
            
            # Build tree
            engine = DiffEngine(viewer.left_files, viewer.right_files)
            viewer.root_node = engine.build_tree()
            viewer._update_visible_nodes()
            
            # Count errors
            only_left, only_right, different, identical, contains_diff, errors = \
                viewer._count_differences(viewer.root_node, 0, 0, 0, 0, 0, 0)
            
            # Should have counted the error
            self.assertEqual(errors, 1)
    
    def test_error_count_includes_comparison_errors(self):
        """Test that file comparison errors are counted."""
        # Create a mock renderer
        renderer = Mock()
        renderer.get_size.return_value = (80, 24)
        
        # Create viewer with mock paths
        with patch('src.tfm_directory_diff_viewer.DirectoryDiffViewer.start_scan'):
            viewer = DirectoryDiffViewer(renderer, Path("/left"), Path("/right"))
            
            # Set up test data with comparison error
            viewer.left_files = {
                "test.txt": FileInfo(
                    path=Path("/left/test.txt"),
                    relative_path="test.txt",
                    is_directory=False,
                    size=100,
                    mtime=1234567890.0,
                    is_accessible=True
                )
            }
            viewer.right_files = {
                "test.txt": FileInfo(
                    path=Path("/right/test.txt"),
                    relative_path="test.txt",
                    is_directory=False,
                    size=100,
                    mtime=1234567890.0,
                    is_accessible=True
                )
            }
            viewer.comparison_errors = {
                f"{Path('/left/test.txt')}|{Path('/right/test.txt')}": "Read error"
            }
            
            # Build tree
            engine = DiffEngine(viewer.left_files, viewer.right_files)
            viewer.root_node = engine.build_tree()
            viewer._update_visible_nodes()
            
            # Count errors
            only_left, only_right, different, identical, contains_diff, errors = \
                viewer._count_differences(viewer.root_node, 0, 0, 0, 0, 0, 0)
            
            # Should have counted the comparison error
            self.assertEqual(errors, 1)


if __name__ == '__main__':
    unittest.main()
