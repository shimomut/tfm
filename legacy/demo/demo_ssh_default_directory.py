"""
Demo: SSH Default Directory Navigation

This demo shows how TFM now starts SSH browsing in the default directory
(typically home directory or current working directory) instead of always
starting at the root directory.

This provides a more natural browsing experience when connecting to remote
servers via SFTP.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


def demo_default_directory_detection():
    """Demo: Connection detects and stores default directory"""
    print("=" * 70)
    print("Demo: SSH Default Directory Detection")
    print("=" * 70)
    print()
    
    print("When connecting to an SSH server, TFM now captures the default")
    print("directory (typically your home directory) instead of always")
    print("starting at root.")
    print()
    
    # Mock the SSH connection behavior
    with patch('src.tfm_ssh_connection.subprocess') as mock_subprocess:
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            "Remote working directory: /home/alice\n",
            ""
        )
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.run.return_value = Mock(returncode=0)
        
        with patch('os.path.exists', return_value=True):
            from src.tfm_ssh_connection import SSHConnection
            
            print("Connecting to ssh://devserver...")
            config = {'HostName': 'devserver.example.com', 'User': 'alice'}
            conn = SSHConnection('devserver', config)
            conn.connect()
            
            print(f"✓ Connected successfully")
            print(f"✓ Default directory detected: {conn.default_directory}")
            print()
            print("This directory will be used as the starting point when")
            print("browsing this server through the drives dialog.")
    
    print()


def demo_drives_dialog_navigation():
    """Demo: Drives dialog uses default directory"""
    print("=" * 70)
    print("Demo: Drives Dialog Navigation")
    print("=" * 70)
    print()
    
    print("When selecting an SSH server from the drives dialog (Alt+F1/F2),")
    print("TFM now navigates to the default directory instead of root.")
    print()
    
    print("The navigate_to_drive() function now includes logic to:")
    print("  1. Extract hostname from ssh://hostname/ path")
    print("  2. Get SSH configuration for the host")
    print("  3. Establish connection (or reuse existing)")
    print("  4. Retrieve default_directory from connection")
    print("  5. Navigate to ssh://hostname/default_directory")
    print()
    
    print("Example flow:")
    print("  Drive entry: ssh://devserver/")
    print("  → Connect to devserver")
    print("  → Detect default directory: /home/alice/projects")
    print("  → Navigate to: ssh://devserver/home/alice/projects")
    print()
    
    print("If connection fails or default directory is root:")
    print("  → Falls back to: ssh://devserver/")
    print()


def demo_comparison():
    """Demo: Before vs After comparison"""
    print("=" * 70)
    print("Demo: Before vs After Comparison")
    print("=" * 70)
    print()
    
    print("BEFORE (old behavior):")
    print("  User selects 'devserver' from drives dialog")
    print("  → Navigates to: ssh://devserver/")
    print("  → Shows root directory: /, /bin, /etc, /home, /usr, ...")
    print("  → User must navigate: / → home → alice → projects")
    print()
    
    print("AFTER (new behavior):")
    print("  User selects 'devserver' from drives dialog")
    print("  → Connects and detects default directory: /home/alice/projects")
    print("  → Navigates to: ssh://devserver/home/alice/projects")
    print("  → Shows project directory immediately")
    print("  → User can start working right away!")
    print()
    
    print("Benefits:")
    print("  ✓ More natural starting point")
    print("  ✓ Fewer navigation steps required")
    print("  ✓ Consistent with local file browsing expectations")
    print("  ✓ Respects server's default directory configuration")
    print()


def demo_fallback_behavior():
    """Demo: Fallback to root on error"""
    print("=" * 70)
    print("Demo: Fallback Behavior")
    print("=" * 70)
    print()
    
    print("If the default directory cannot be detected (connection error,")
    print("parsing failure, etc.), TFM gracefully falls back to root.")
    print()
    
    with patch('src.tfm_ssh_connection.subprocess') as mock_subprocess:
        mock_process = Mock()
        mock_process.returncode = 0
        # Unparseable output
        mock_process.communicate.return_value = (
            "Unexpected output format\n",
            ""
        )
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.run.return_value = Mock(returncode=0)
        
        with patch('os.path.exists', return_value=True):
            from src.tfm_ssh_connection import SSHConnection
            
            print("Connecting to ssh://oldserver (with unparseable pwd output)...")
            config = {'HostName': 'oldserver.example.com', 'User': 'bob'}
            conn = SSHConnection('oldserver', config)
            conn.connect()
            
            print(f"✓ Connected successfully")
            print(f"✓ Default directory: {conn.default_directory} (fallback)")
            print()
            print("The connection still works, just starts at root as before.")
    
    print()


def main():
    """Run all demos"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "SSH Default Directory Navigation Demo" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    demo_default_directory_detection()
    demo_drives_dialog_navigation()
    demo_comparison()
    demo_fallback_behavior()
    
    print("=" * 70)
    print("Demo Complete")
    print("=" * 70)
    print()
    print("To test this feature manually:")
    print("  1. Configure an SSH host in ~/.ssh/config")
    print("  2. Launch TFM")
    print("  3. Press Alt+F1 or Alt+F2 to open drives dialog")
    print("  4. Select your SSH host")
    print("  5. Notice you start in your home/current directory, not root!")
    print()


if __name__ == '__main__':
    main()
