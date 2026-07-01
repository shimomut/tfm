#!/usr/bin/env python3
"""Unit tests for reveal in OS feature."""

import unittest
from unittest.mock import Mock, patch, call
from pathlib import Path
import sys

# Add src and ttk to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'ttk'))

from tfm_main import FileManager


class TestRevealInOS(unittest.TestCase):
    """Test cases for reveal in OS action."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_renderer = Mock()
        self.mock_renderer.get_size.return_value = (80, 24)
        self.mock_renderer.is_desktop_mode.return_value = False
        
        # Create mock files
        self.test_file = Path('/tmp/test_file.txt')
        self.test_dir = Path('/tmp/test_dir')
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_reveal_file_macos(self, mock_run, mock_system):
        """Test revealing a file on macOS."""
        mock_system.return_value = 'Darwin'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        fm.pane_manager.left_pane['files'] = [self.test_file, self.test_dir]
        fm.pane_manager.left_pane['focused_index'] = 0
        
        result = fm._action_reveal_in_os()
        
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ['open', '-R', str(self.test_file)],
            check=True
        )
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_reveal_directory_macos(self, mock_run, mock_system):
        """Test revealing a directory on macOS."""
        mock_system.return_value = 'Darwin'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        fm.pane_manager.left_pane['files'] = [self.test_file, self.test_dir]
        fm.pane_manager.left_pane['focused_index'] = 1  # Focus on directory
        
        result = fm._action_reveal_in_os()
        
        self.assertTrue(result)
        # Should use 'open -R' for directories too (reveals in parent)
        mock_run.assert_called_once_with(
            ['open', '-R', str(self.test_dir)],
            check=True
        )
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_reveal_file_windows(self, mock_run, mock_system):
        """Test revealing a file on Windows."""
        mock_system.return_value = 'Windows'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        fm.pane_manager.left_pane['files'] = [self.test_file, self.test_dir]
        fm.pane_manager.left_pane['focused_index'] = 0
        
        result = fm._action_reveal_in_os()
        
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ['explorer', '/select,', str(self.test_file)],
            check=True
        )
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_reveal_directory_windows(self, mock_run, mock_system):
        """Test revealing a directory on Windows."""
        mock_system.return_value = 'Windows'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        fm.pane_manager.left_pane['files'] = [self.test_file, self.test_dir]
        fm.pane_manager.left_pane['focused_index'] = 1  # Focus on directory
        
        result = fm._action_reveal_in_os()
        
        self.assertTrue(result)
        # Should use '/select,' for directories too (reveals in parent)
        mock_run.assert_called_once_with(
            ['explorer', '/select,', str(self.test_dir)],
            check=True
        )
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_reveal_file_linux_nautilus(self, mock_run, mock_system):
        """Test revealing a file on Linux with nautilus."""
        mock_system.return_value = 'Linux'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        fm.pane_manager.left_pane['files'] = [self.test_file, self.test_dir]
        fm.pane_manager.left_pane['focused_index'] = 0
        
        # Mock 'which' command to find nautilus
        def run_side_effect(cmd, **kwargs):
            if cmd[0] == 'which' and cmd[1] == 'nautilus':
                result = Mock()
                result.returncode = 0
                return result
            return Mock()
        
        mock_run.side_effect = run_side_effect
        
        result = fm._action_reveal_in_os()
        
        self.assertTrue(result)
        # Should call 'which nautilus' and then 'nautilus --select'
        calls = mock_run.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0][0], ['which', 'nautilus'])
        self.assertEqual(calls[1][0][0], ['nautilus', '--select', str(self.test_file)])
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_reveal_file_linux_fallback(self, mock_run, mock_system):
        """Test revealing a file on Linux with fallback to xdg-open."""
        mock_system.return_value = 'Linux'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        fm.pane_manager.left_pane['files'] = [self.test_file, self.test_dir]
        fm.pane_manager.left_pane['focused_index'] = 0
        
        # Mock 'which' command to not find any file managers
        def run_side_effect(cmd, **kwargs):
            if cmd[0] == 'which':
                result = Mock()
                result.returncode = 1  # Not found
                return result
            return Mock()
        
        mock_run.side_effect = run_side_effect
        
        result = fm._action_reveal_in_os()
        
        self.assertTrue(result)
        # Should eventually call xdg-open with parent directory
        final_call = mock_run.call_args_list[-1]
        self.assertEqual(final_call[0][0][0], 'xdg-open')
        self.assertEqual(final_call[0][0][1], str(self.test_file.parent))
    
    def test_reveal_empty_pane(self):
        """Test revealing when pane is empty."""
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        fm.pane_manager.left_pane['files'] = []
        
        result = fm._action_reveal_in_os()
        
        self.assertTrue(result)
    
    def test_reveal_uses_focused_not_selection(self):
        """Test that reveal uses focused file, not selection."""
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        fm.pane_manager.left_pane['files'] = [self.test_file, self.test_dir]
        fm.pane_manager.left_pane['focused_index'] = 0  # Focus on file
        fm.pane_manager.left_pane['selected_files'] = {1}  # Select directory
        
        with patch('platform.system', return_value='Darwin'), \
             patch('subprocess.run') as mock_run:
            
            result = fm._action_reveal_in_os()
            
            self.assertTrue(result)
            # Should use focused file, not selected directory
            mock_run.assert_called_once_with(
                ['open', '-R', str(self.test_file)],
                check=True
            )
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_reveal_command_failure(self, mock_run, mock_system):
        """Test handling of command failure."""
        mock_system.return_value = 'Darwin'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        fm.pane_manager.left_pane['files'] = [self.test_file, self.test_dir]
        fm.pane_manager.left_pane['focused_index'] = 0
        
        mock_run.side_effect = Exception("Command failed")
        
        result = fm._action_reveal_in_os()
        
        # Should return True even on error (graceful handling)
        self.assertTrue(result)
    
    @patch('platform.system')
    def test_reveal_unsupported_platform(self, mock_system):
        """Test handling of unsupported platform."""
        mock_system.return_value = 'UnknownOS'
        
        # Create FileManager instance
        fm = FileManager(self.mock_renderer)
        fm.pane_manager.left_pane['files'] = [self.test_file, self.test_dir]
        fm.pane_manager.left_pane['focused_index'] = 0
        
        result = fm._action_reveal_in_os()
        
        # Should return True even on unsupported platform (graceful handling)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
