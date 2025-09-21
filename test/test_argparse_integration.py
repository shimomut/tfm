#!/usr/bin/env python3
"""
Integration tests for TFM command line argument parsing
"""

import sys
import subprocess
import unittest
from pathlib import Path

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class TestArgparseIntegration(unittest.TestCase):
    """Integration tests for command line argument parsing"""
    
    def setUp(self):
        """Set up test environment"""
        self.tfm_script = Path(__file__).parent.parent / 'tfm.py'
        self.assertTrue(self.tfm_script.exists(), "tfm.py script not found")
    
    def run_tfm_command(self, args):
        """Helper method to run TFM with given arguments"""
        cmd = [sys.executable, str(self.tfm_script)] + args
        return subprocess.run(cmd, capture_output=True, text=True)
    
    def test_version_displays_correct_info(self):
        """Test that --version displays the correct version information"""
        result = self.run_tfm_command(['--version'])
        
        self.assertEqual(result.returncode, 0)
        output = result.stdout.strip()
        
        # Should contain app name and version
        self.assertIn('TUI File Manager', output)
        self.assertIn('0.95', output)
        
        # Should be a single line
        lines = output.split('\n')
        self.assertEqual(len(lines), 1)
    
    def test_help_contains_all_expected_sections(self):
        """Test that --help contains all expected sections"""
        result = self.run_tfm_command(['--help'])
        
        self.assertEqual(result.returncode, 0)
        help_text = result.stdout
        
        # Check for main sections
        self.assertIn('usage:', help_text)
        self.assertIn('options:', help_text)
        
        # Check for specific options
        self.assertIn('-h, --help', help_text)
        self.assertIn('-v, --version', help_text)
        
        # Check for URL
        self.assertIn('github.com/shimomut/tfm', help_text)
    
    def test_error_handling_for_unknown_args(self):
        """Test error handling for various unknown arguments"""
        test_cases = [
            ['--unknown'],
            ['-x'],
            ['--bad-arg'],
            ['--version=something'],  # --version doesn't take arguments
            ['positional_arg'],  # No positional args expected
        ]
        
        for args in test_cases:
            with self.subTest(args=args):
                result = self.run_tfm_command(args)
                
                # Should exit with error code 2 (argparse error)
                self.assertEqual(result.returncode, 2)
                
                # Should show usage in stderr
                self.assertIn('usage: tfm', result.stderr)
                
                # Should mention the problematic argument
                error_text = result.stderr.lower()
                self.assertTrue(
                    'unrecognized' in error_text or 
                    'invalid' in error_text or
                    'error' in error_text
                )
    
    def test_help_and_version_exit_cleanly(self):
        """Test that help and version options exit cleanly without errors"""
        for args in [['--help'], ['-h'], ['--version'], ['-v']]:
            with self.subTest(args=args):
                result = self.run_tfm_command(args)
                
                # Should exit successfully
                self.assertEqual(result.returncode, 0)
                
                # Should have output in stdout, not stderr
                self.assertTrue(len(result.stdout) > 0)
                self.assertEqual(len(result.stderr), 0)
    
    def test_argument_precedence(self):
        """Test argument precedence when multiple are provided"""
        # When both --help and --version are provided, --help should take precedence
        result = self.run_tfm_command(['--help', '--version'])
        
        self.assertEqual(result.returncode, 0)
        # Should show help, not version
        self.assertIn('usage:', result.stdout)
        self.assertIn('options:', result.stdout)

if __name__ == '__main__':
    unittest.main()