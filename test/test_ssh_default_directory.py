"""
Test SSH default directory behavior

Verifies that SSH connections start in the default directory (home/current)
instead of always starting at root.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestSSHDefaultDirectory(unittest.TestCase):
    """Test SSH default directory detection and usage"""
    
    @patch('src.tfm_ssh_connection.subprocess')
    def test_connection_captures_default_directory(self, mock_subprocess):
        """Test that connection captures pwd output as default directory"""
        from src.tfm_ssh_connection import SSHConnection
        
        # Mock the subprocess calls
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            "Remote working directory: /home/testuser\n",
            ""
        )
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.run.return_value = Mock(returncode=0)
        
        # Mock os.path.exists to return True for control socket
        with patch('os.path.exists', return_value=True):
            # Create connection
            config = {'HostName': 'testhost', 'User': 'testuser'}
            conn = SSHConnection('testhost', config)
            
            # Connect
            conn.connect()
            
            # Verify default directory was captured
            self.assertEqual(conn.default_directory, '/home/testuser')
    
    @patch('src.tfm_ssh_connection.subprocess')
    def test_connection_fallback_to_root(self, mock_subprocess):
        """Test that connection falls back to root if pwd parsing fails"""
        from src.tfm_ssh_connection import SSHConnection
        
        # Mock the subprocess calls with unparseable output
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            "Some unexpected output\n",
            ""
        )
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.run.return_value = Mock(returncode=0)
        
        # Mock os.path.exists to return True for control socket
        with patch('os.path.exists', return_value=True):
            # Create connection
            config = {'HostName': 'testhost', 'User': 'testuser'}
            conn = SSHConnection('testhost', config)
            
            # Connect
            conn.connect()
            
            # Verify default directory falls back to root
            self.assertEqual(conn.default_directory, '/')
    
    def test_drives_dialog_ssh_handling(self):
        """Test that drives dialog has SSH handling code"""
        from src.tfm_drives_dialog import DrivesDialogHelpers
        import inspect
        
        # Get the source code of navigate_to_drive
        source = inspect.getsource(DrivesDialogHelpers.navigate_to_drive)
        
        # Verify it contains SSH-specific handling
        self.assertIn("drive_entry.drive_type == 'ssh'", source)
        self.assertIn('default_directory', source)
        self.assertIn('SSHConnectionManager', source)


if __name__ == '__main__':
    unittest.main()
