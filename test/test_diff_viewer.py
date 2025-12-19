#!/usr/bin/env python3
"""
Test suite for TFM Diff Viewer
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path as StdPath

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_diff_viewer import DiffViewer, view_diff
from ttk import KeyEvent, KeyCode


class TestDiffViewer(unittest.TestCase):
    """Test cases for DiffViewer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        self.mock_renderer.get_input.return_value = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=0, char='')
        
        # Create temporary test files
        self.test_dir = StdPath(__file__).parent / 'temp_diff_test'
        self.test_dir.mkdir(exist_ok=True)
        
        self.file1_path = self.test_dir / 'file1.txt'
        self.file2_path = self.test_dir / 'file2.txt'
        
        # Write test content
        self.file1_content = "Line 1\nLine 2\nLine 3\nLine 4\n"
        self.file2_content = "Line 1\nLine 2 modified\nLine 3\nLine 5\n"
        
        self.file1_path.write_text(self.file1_content)
        self.file2_path.write_text(self.file2_content)
    
    def tearDown(self):
        """Clean up test files"""
        if self.test_dir.exists():
            for file in self.test_dir.iterdir():
                file.unlink()
            self.test_dir.rmdir()
    
    def test_diff_viewer_initialization(self):
        """Test DiffViewer initialization"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        self.assertEqual(len(viewer.file1_lines), 4)
        self.assertEqual(len(viewer.file2_lines), 4)
        self.assertGreater(len(viewer.diff_lines), 0)
    
    def test_diff_computation(self):
        """Test diff computation"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Check that diff was computed
        self.assertGreater(len(viewer.diff_lines), 0)
        
        # Verify diff contains expected changes
        statuses = [status for _, _, status, _, _, _, _ in viewer.diff_lines]
        self.assertIn('equal', statuses)  # Some lines should be equal
        self.assertTrue(any(s in statuses for s in ['replace', 'delete', 'insert']))  # Some changes
    
    def test_load_file_error_handling(self):
        """Test file loading with non-existent file"""
        non_existent = Path('/non/existent/file.txt')
        viewer = DiffViewer(self.mock_renderer, non_existent, Path(self.file2_path))
        
        # Should handle error gracefully
        self.assertIn("File not found", viewer.file1_lines[0])
    
    def test_handle_input_navigation(self):
        """Test keyboard navigation"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Test scroll down
        initial_offset = viewer.scroll_offset
        event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0, char='')
        result = viewer.handle_input(event)
        self.assertTrue(result)
        self.assertGreaterEqual(viewer.scroll_offset, initial_offset)
        
        # Test quit
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=0, char='')
        result = viewer.handle_input(event)
        self.assertFalse(result)
    
    def test_handle_input_horizontal_scroll(self):
        """Test horizontal scrolling"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Test scroll right
        event = KeyEvent(key_code=KeyCode.RIGHT, modifiers=0, char='')
        viewer.handle_input(event)
        self.assertGreater(viewer.horizontal_offset, 0)
        
        # Test scroll left
        event = KeyEvent(key_code=KeyCode.LEFT, modifiers=0, char='')
        viewer.handle_input(event)
        self.assertEqual(viewer.horizontal_offset, 0)
    
    def test_view_diff_function(self):
        """Test view_diff function"""
        with patch.object(DiffViewer, 'run'):
            result = view_diff(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
            self.assertTrue(result)
    
    def test_view_diff_with_invalid_files(self):
        """Test view_diff with invalid files"""
        non_existent = Path('/non/existent/file.txt')
        result = view_diff(self.mock_renderer, non_existent, Path(self.file2_path))
        self.assertFalse(result)
    
    def test_binary_file_handling(self):
        """Test handling of binary files"""
        binary_file = self.test_dir / 'binary.bin'
        # Create a binary file with null bytes in first 1024 bytes
        binary_file.write_bytes(b'\x00' * 100 + b'some text' + b'\x00' * 100)
        
        viewer = DiffViewer(self.mock_renderer, Path(binary_file), Path(self.file2_path))
        
        # Should detect binary file
        self.assertIn("Binary file", viewer.file1_lines[0])


class TestDiffViewerIntegration(unittest.TestCase):
    """Integration tests for diff viewer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        
        # Create test files with more complex diffs
        self.test_dir = StdPath(__file__).parent / 'temp_diff_integration'
        self.test_dir.mkdir(exist_ok=True)
        
        self.file1_path = self.test_dir / 'original.py'
        self.file2_path = self.test_dir / 'modified.py'
        
        self.file1_content = """def hello():
    print("Hello")
    return True

def goodbye():
    print("Goodbye")
"""
        
        self.file2_content = """def hello():
    print("Hello World")
    return True

def farewell():
    print("Farewell")
    return False
"""
        
        self.file1_path.write_text(self.file1_content)
        self.file2_path.write_text(self.file2_content)
    
    def tearDown(self):
        """Clean up test files"""
        if self.test_dir.exists():
            for file in self.test_dir.iterdir():
                file.unlink()
            self.test_dir.rmdir()
    
    def test_complex_diff(self):
        """Test diff with complex changes"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Verify diff was computed
        self.assertGreater(len(viewer.diff_lines), 0)
        
        # Check for different types of changes
        statuses = [status for _, _, status, _, _, _, _ in viewer.diff_lines]
        self.assertIn('equal', statuses)
        self.assertTrue(any(s in ['replace', 'delete', 'insert'] for s in statuses))
    
    def test_identical_files(self):
        """Test diff with identical files"""
        identical_file = self.test_dir / 'identical.txt'
        identical_file.write_text(self.file1_content)
        
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(identical_file))
        
        # All lines should be equal
        statuses = [status for _, _, status, _, _, _, _ in viewer.diff_lines]
        self.assertTrue(all(s == 'equal' for s in statuses))
    
    def test_completely_different_files(self):
        """Test diff with completely different files"""
        different_file = self.test_dir / 'different.txt'
        different_file.write_text("Completely\nDifferent\nContent\n")
        
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(different_file))
        
        # Should have changes
        statuses = [status for _, _, status, _, _, _, _ in viewer.diff_lines]
        self.assertTrue(any(s != 'equal' for s in statuses))
    
    def test_whitespace_ignore_mode(self):
        """Test whitespace ignore mode"""
        # Create files with whitespace differences
        ws_file1 = self.test_dir / 'whitespace1.txt'
        ws_file2 = self.test_dir / 'whitespace2.txt'
        
        ws_file1.write_text("Line 1\nLine 2\nLine 3\n")
        ws_file2.write_text("Line 1\n  Line 2  \n\tLine 3\n")
        
        viewer = DiffViewer(self.mock_renderer, Path(ws_file1), Path(ws_file2))
        
        # Without whitespace ignore, should show differences
        statuses_normal = [status for _, _, status, _, _, _, _ in viewer.diff_lines]
        has_changes_normal = any(s != 'equal' for s in statuses_normal)
        
        # Enable whitespace ignore mode
        viewer.ignore_whitespace = True
        viewer.compute_diff()
        
        # With whitespace ignore, should be equal
        statuses_ignore = [status for _, _, status, _, _, _, _ in viewer.diff_lines]
        has_changes_ignore = any(s != 'equal' for s in statuses_ignore)
        
        # Verify that whitespace ignore mode reduces differences
        self.assertTrue(has_changes_normal)
        self.assertFalse(has_changes_ignore)
    
    def test_whitespace_ignore_toggle(self):
        """Test toggling whitespace ignore mode with 'w' key"""
        viewer = DiffViewer(self.mock_renderer, Path(self.file1_path), Path(self.file2_path))
        
        # Initially disabled
        self.assertFalse(viewer.ignore_whitespace)
        
        # Toggle on
        event = KeyEvent(key_code=None, modifiers=0, char='w')
        viewer.handle_input(event)
        self.assertTrue(viewer.ignore_whitespace)
        
        # Toggle off
        viewer.handle_input(event)
        self.assertFalse(viewer.ignore_whitespace)
    
    def test_whitespace_ignore_with_real_differences(self):
        """Test that whitespace ignore doesn't hide real differences"""
        # Create files with both whitespace and content differences
        ws_file1 = self.test_dir / 'mixed1.txt'
        ws_file2 = self.test_dir / 'mixed2.txt'
        
        ws_file1.write_text("Line 1\nLine 2\nLine 3\n")
        ws_file2.write_text("Line 1\n  Line 2 modified  \nLine 3\n")
        
        viewer = DiffViewer(self.mock_renderer, Path(ws_file1), Path(ws_file2))
        
        # Enable whitespace ignore mode
        viewer.ignore_whitespace = True
        viewer.compute_diff()
        
        # Should still show the content difference
        statuses = [status for _, _, status, _, _, _, _ in viewer.diff_lines]
        has_changes = any(s != 'equal' for s in statuses)
        self.assertTrue(has_changes)


if __name__ == '__main__':
    unittest.main()
