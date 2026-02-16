#!/usr/bin/env python3
"""
Test: Open with OS Default Application

Tests the "Open with OS" feature that opens files using the OS's
default file association.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_main import FileManager
from tfm_path import Path as TFMPath


class TestOpenWithOS(unittest.TestCase):
    """Test cases for opening files with OS default application."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_renderer = Mock()
        self.mock_renderer.get_size.return_value = (80, 24)
        self.mock_renderer.is_desktop_mode.return_value = False
        
    @patch('tfm_main.platform.system')
    @patch('tfm_main.subprocess.run')
    def test_open_with_os_macos(self, mock_subprocess, mock_platform):
        """Test opening file with OS default app on macOS."""
        mock_platform.return_value = 'Darwin'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        
        # Set up test file
        test_file = TFMPath('/tmp/test.txt')
        fm.pane_manager.left_pane['files'] = [test_file]
        fm.pane_manager.left_pane['focused_index'] = 0
        fm.pane_manager.left_pane['selected_files'] = set()
        
        # Call action
        result = fm._action_open_with_os()
        
        # Verify
        self.assertTrue(result)
        mock_subprocess.assert_called_once_with(['open', str(test_file)], check=True)
    
    @patch('tfm_main.platform.system')
    @patch('tfm_main.subprocess.run')
    def test_open_with_os_linux(self, mock_subprocess, mock_platform):
        """Test opening file with OS default app on Linux."""
        mock_platform.return_value = 'Linux'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        
        # Set up test file
        test_file = TFMPath('/tmp/test.txt')
        fm.pane_manager.left_pane['files'] = [test_file]
        fm.pane_manager.left_pane['focused_index'] = 0
        fm.pane_manager.left_pane['selected_files'] = set()
        
        # Call action
        result = fm._action_open_with_os()
        
        # Verify
        self.assertTrue(result)
        mock_subprocess.assert_called_once_with(['xdg-open', str(test_file)], check=True)
    
    @patch('tfm_main.platform.system')
    @patch('tfm_main.subprocess.run')
    def test_open_with_os_windows(self, mock_subprocess, mock_platform):
        """Test opening file with OS default app on Windows."""
        mock_platform.return_value = 'Windows'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        
        # Set up test file
        test_file = TFMPath('C:\\temp\\test.txt')
        fm.pane_manager.left_pane['files'] = [test_file]
        fm.pane_manager.left_pane['focused_index'] = 0
        fm.pane_manager.left_pane['selected_files'] = set()
        
        # Call action
        result = fm._action_open_with_os()
        
        # Verify
        self.assertTrue(result)
        mock_subprocess.assert_called_once_with(['start', '', str(test_file)], shell=True, check=True)
    
    @patch('tfm_main.platform.system')
    @patch('tfm_main.subprocess.run')
    def test_open_multiple_files(self, mock_subprocess, mock_platform):
        """Test opening multiple selected files."""
        mock_platform.return_value = 'Darwin'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        
        # Set up multiple test files
        test_file1 = TFMPath('/tmp/test1.txt')
        test_file2 = TFMPath('/tmp/test2.txt')
        fm.pane_manager.left_pane['files'] = [test_file1, test_file2]
        fm.pane_manager.left_pane['focused_index'] = 0
        fm.pane_manager.left_pane['selected_files'] = {test_file1, test_file2}
        
        # Call action
        result = fm._action_open_with_os()
        
        # Verify both files were opened
        self.assertTrue(result)
        self.assertEqual(mock_subprocess.call_count, 2)
        mock_subprocess.assert_any_call(['open', str(test_file1)], check=True)
        mock_subprocess.assert_any_call(['open', str(test_file2)], check=True)
    
    @patch('tfm_main.platform.system')
    @patch('tfm_main.subprocess.run')
    def test_open_with_os_error_handling(self, mock_subprocess, mock_platform):
        """Test error handling when opening fails."""
        mock_platform.return_value = 'Darwin'
        mock_subprocess.side_effect = Exception("Command failed")
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        
        # Set up test file
        test_file = TFMPath('/tmp/test.txt')
        fm.pane_manager.left_pane['files'] = [test_file]
        fm.pane_manager.left_pane['focused_index'] = 0
        fm.pane_manager.left_pane['selected_files'] = set()
        
        # Call action - should not raise exception
        result = fm._action_open_with_os()
        
        # Verify it handled the error gracefully
        self.assertTrue(result)
    
    @patch('tfm_main.platform.system')
    def test_open_with_os_unsupported_platform(self, mock_platform):
        """Test behavior on unsupported platform."""
        mock_platform.return_value = 'UnknownOS'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        
        # Set up test file
        test_file = TFMPath('/tmp/test.txt')
        fm.pane_manager.left_pane['files'] = [test_file]
        fm.pane_manager.left_pane['focused_index'] = 0
        fm.pane_manager.left_pane['selected_files'] = set()
        
        # Call action
        result = fm._action_open_with_os()
        
        # Verify it returns True but doesn't crash
        self.assertTrue(result)
    
    def test_open_with_os_empty_pane(self):
        """Test behavior when pane has no files."""
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        
        # Set up empty pane
        fm.pane_manager.left_pane['files'] = []
        
        # Call action
        result = fm._action_open_with_os()
        
        # Verify it returns True without error
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
