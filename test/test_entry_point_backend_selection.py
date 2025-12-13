#!/usr/bin/env python3
"""
Test backend selection functionality in TFM entry point
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import argparse

# Add root directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestBackendSelection(unittest.TestCase):
    """Test backend selection in entry point"""
    
    def test_parser_has_backend_argument(self):
        """Test that parser includes --backend argument"""
        from tfm import create_parser
        parser = create_parser()
        
        # Parse with backend argument
        args = parser.parse_args(['--backend', 'curses'])
        self.assertEqual(args.backend, 'curses')
        
        args = parser.parse_args(['--backend', 'coregraphics'])
        self.assertEqual(args.backend, 'coregraphics')
    
    def test_parser_has_desktop_argument(self):
        """Test that parser includes --desktop argument"""
        from tfm import create_parser
        parser = create_parser()
        
        # Parse with desktop flag
        args = parser.parse_args(['--desktop'])
        self.assertTrue(args.desktop)
        
        # Parse without desktop flag
        args = parser.parse_args([])
        self.assertFalse(args.desktop)
    
    def test_backend_argument_choices(self):
        """Test that --backend only accepts valid choices"""
        from tfm import create_parser
        parser = create_parser()
        
        # Valid choices should work
        args = parser.parse_args(['--backend', 'curses'])
        self.assertEqual(args.backend, 'curses')
        
        # Invalid choice should raise error
        with self.assertRaises(SystemExit):
            parser.parse_args(['--backend', 'invalid'])
    
    def test_backend_selection_integration(self):
        """Test that backend selection is integrated into main"""
        from tfm import main
        import inspect
        
        # Get the source code of main function
        source = inspect.getsource(main)
        
        # Verify that backend selection is present
        self.assertIn('select_backend', source)
        self.assertIn('CursesBackend', source)
        self.assertIn('CoreGraphicsBackend', source)
        self.assertIn('renderer.initialize()', source)
        self.assertIn('renderer.shutdown()', source)
    
    def test_backend_and_desktop_arguments_together(self):
        """Test that both --backend and --desktop can be specified"""
        from tfm import create_parser
        parser = create_parser()
        
        # Both arguments should be accepted
        args = parser.parse_args(['--backend', 'curses', '--desktop'])
        self.assertEqual(args.backend, 'curses')
        self.assertTrue(args.desktop)
    
    def test_existing_arguments_preserved(self):
        """Test that existing arguments still work"""
        from tfm import create_parser
        parser = create_parser()
        
        # Test remote log port
        args = parser.parse_args(['--remote-log-port', '8888'])
        self.assertEqual(args.remote_log_port, 8888)
        
        # Test left directory
        args = parser.parse_args(['--left', '/tmp'])
        self.assertEqual(args.left, '/tmp')
        
        # Test right directory
        args = parser.parse_args(['--right', '/home'])
        self.assertEqual(args.right, '/home')
        
        # Test color test
        args = parser.parse_args(['--color-test', 'info'])
        self.assertEqual(args.color_test, 'info')
    
    def test_combined_arguments(self):
        """Test that new backend arguments work with existing arguments"""
        from tfm import create_parser
        parser = create_parser()
        
        # Combine backend with other arguments
        args = parser.parse_args([
            '--backend', 'curses',
            '--remote-log-port', '8888',
            '--left', '/tmp',
            '--right', '/home'
        ])
        
        self.assertEqual(args.backend, 'curses')
        self.assertEqual(args.remote_log_port, 8888)
        self.assertEqual(args.left, '/tmp')
        self.assertEqual(args.right, '/home')

if __name__ == '__main__':
    unittest.main()
