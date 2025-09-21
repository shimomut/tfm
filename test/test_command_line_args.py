#!/usr/bin/env python3
"""
Test command line argument parsing for TFM
"""

import sys
import subprocess
import unittest
from pathlib import Path

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class TestCommandLineArgs(unittest.TestCase):
    """Test command line argument handling"""
    
    def setUp(self):
        """Set up test environment"""
        self.tfm_script = Path(__file__).parent.parent / 'tfm.py'
        self.assertTrue(self.tfm_script.exists(), "tfm.py script not found")
    
    def test_help_option(self):
        """Test --help option displays help message"""
        result = subprocess.run(
            [sys.executable, str(self.tfm_script), '--help'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage: tfm', result.stdout)
        self.assertIn('A terminal-based file manager', result.stdout)
        self.assertIn('--version', result.stdout)
        self.assertIn('Examples:', result.stdout)
    
    def test_version_option(self):
        """Test --version option displays version information"""
        result = subprocess.run(
            [sys.executable, str(self.tfm_script), '--version'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('TUI File Manager', result.stdout)
        self.assertIn('1.00', result.stdout)
    
    def test_short_version_option(self):
        """Test -v option works as alias for --version"""
        result = subprocess.run(
            [sys.executable, str(self.tfm_script), '-v'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('TUI File Manager', result.stdout)
        self.assertIn('1.00', result.stdout)
    
    def test_invalid_option(self):
        """Test invalid option shows error and usage"""
        result = subprocess.run(
            [sys.executable, str(self.tfm_script), '--invalid-option'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 2)  # argparse error exit code
        self.assertIn('usage: tfm', result.stderr)
        self.assertIn('unrecognized arguments', result.stderr)
        self.assertIn('--invalid-option', result.stderr)
    
    def test_multiple_invalid_options(self):
        """Test multiple invalid options show error"""
        result = subprocess.run(
            [sys.executable, str(self.tfm_script), '--bad1', '--bad2'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 2)
        self.assertIn('usage: tfm', result.stderr)
        self.assertIn('unrecognized arguments', result.stderr)
    
    def test_short_help_option(self):
        """Test -h option works as alias for --help"""
        result = subprocess.run(
            [sys.executable, str(self.tfm_script), '-h'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage: tfm', result.stdout)
        self.assertIn('A terminal-based file manager', result.stdout)

if __name__ == '__main__':
    unittest.main()