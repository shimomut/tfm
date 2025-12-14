#!/usr/bin/env python3
"""
Test command line arguments for --left and --right directory specification
"""

import unittest
import sys
import os
import tempfile
import argparse
from pathlib import Path

# Add src directory to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the create_parser function from tfm.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tfm import create_parser

class TestCommandLineArguments(unittest.TestCase):
    """Test command line argument parsing for --left and --right options"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = create_parser()
        
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.left_test_dir = os.path.join(self.temp_dir, 'left_test')
        self.right_test_dir = os.path.join(self.temp_dir, 'right_test')
        os.makedirs(self.left_test_dir)
        os.makedirs(self.right_test_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_no_directory_arguments(self):
        """Test that parser works without --left or --right arguments"""
        args = self.parser.parse_args([])
        self.assertIsNone(args.left)
        self.assertIsNone(args.right)
        self.assertIsNone(args.remote_log_port)
    
    def test_left_directory_argument(self):
        """Test --left argument parsing"""
        args = self.parser.parse_args(['--left', self.left_test_dir])
        self.assertEqual(args.left, self.left_test_dir)
        self.assertIsNone(args.right)
    
    def test_right_directory_argument(self):
        """Test --right argument parsing"""
        args = self.parser.parse_args(['--right', self.right_test_dir])
        self.assertIsNone(args.left)
        self.assertEqual(args.right, self.right_test_dir)
    
    def test_both_directory_arguments(self):
        """Test both --left and --right arguments together"""
        args = self.parser.parse_args(['--left', self.left_test_dir, '--right', self.right_test_dir])
        self.assertEqual(args.left, self.left_test_dir)
        self.assertEqual(args.right, self.right_test_dir)
    
    def test_directory_arguments_with_remote_log(self):
        """Test directory arguments combined with --remote-log-port"""
        args = self.parser.parse_args([
            '--left', self.left_test_dir,
            '--right', self.right_test_dir,
            '--remote-log-port', '8888'
        ])
        self.assertEqual(args.left, self.left_test_dir)
        self.assertEqual(args.right, self.right_test_dir)
        self.assertEqual(args.remote_log_port, 8888)
    
    def test_relative_paths(self):
        """Test that relative paths are accepted"""
        args = self.parser.parse_args(['--left', '.', '--right', '..'])
        self.assertEqual(args.left, '.')
        self.assertEqual(args.right, '..')
    
    def test_absolute_paths(self):
        """Test that absolute paths are accepted"""
        args = self.parser.parse_args(['--left', '/tmp', '--right', '/home'])
        self.assertEqual(args.left, '/tmp')
        self.assertEqual(args.right, '/home')
    
    def test_help_includes_new_options(self):
        """Test that help text includes the new options"""
        help_text = self.parser.format_help()
        self.assertIn('--left', help_text)
        self.assertIn('--right', help_text)
        self.assertIn('left pane', help_text)
        self.assertIn('right pane', help_text)
    
    def test_command_line_overrides_history(self):
        """Test that command line arguments should override history restoration"""
        # This is a documentation test - the actual behavior is tested in 
        # test_command_line_no_history_restore.py with proper mocking
        args = self.parser.parse_args(['--left', self.left_test_dir, '--right', self.right_test_dir])
        
        # Verify arguments are parsed correctly
        self.assertEqual(args.left, self.left_test_dir)
        self.assertEqual(args.right, self.right_test_dir)
        
        # The actual override behavior is tested in the integration test
        # This test just ensures the arguments are available for that logic
    
    def test_profile_flag_default(self):
        """Test that --profile flag defaults to False"""
        args = self.parser.parse_args([])
        self.assertFalse(args.profile)
    
    def test_profile_flag_enabled(self):
        """Test that --profile flag can be enabled"""
        args = self.parser.parse_args(['--profile'])
        self.assertTrue(args.profile)
    
    def test_profile_flag_with_other_options(self):
        """Test that --profile flag works with other options"""
        args = self.parser.parse_args([
            '--profile',
            '--left', self.left_test_dir,
            '--right', self.right_test_dir,
            '--remote-log-port', '8888'
        ])
        self.assertTrue(args.profile)
        self.assertEqual(args.left, self.left_test_dir)
        self.assertEqual(args.right, self.right_test_dir)
        self.assertEqual(args.remote_log_port, 8888)
    
    def test_help_includes_profile_option(self):
        """Test that help text includes the --profile option"""
        help_text = self.parser.format_help()
        self.assertIn('--profile', help_text)
        self.assertIn('profiling', help_text.lower())

if __name__ == '__main__':
    unittest.main()