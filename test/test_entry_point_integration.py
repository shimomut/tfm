#!/usr/bin/env python3
"""
Integration test for TFM entry point with TTK backend selection
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import argparse

# Add root directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestEntryPointIntegration(unittest.TestCase):
    """Integration tests for entry point with backend selection"""
    
    def test_import_backend_selector(self):
        """Test that backend selector can be imported"""
        try:
            from tfm_backend_selector import select_backend
            self.assertTrue(callable(select_backend))
        except ImportError as e:
            self.fail(f"Failed to import backend selector: {e}")
    
    def test_import_ttk_backends(self):
        """Test that TTK backends can be imported"""
        try:
            from ttk.backends.curses_backend import CursesBackend
            self.assertTrue(CursesBackend is not None)
        except ImportError as e:
            self.fail(f"Failed to import CursesBackend: {e}")
        
        # CoreGraphicsBackend may not be available on all platforms
        try:
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
            self.assertTrue(CoreGraphicsBackend is not None)
        except ImportError:
            # This is expected on non-macOS platforms
            pass
    
    def test_backend_selection_flow(self):
        """Test the complete backend selection flow"""
        from tfm_backend_selector import select_backend
        
        # Create mock args
        args = argparse.Namespace()
        args.backend = None
        args.desktop = False
        
        # Should default to curses
        backend_name, backend_options = select_backend(args)
        self.assertEqual(backend_name, 'curses')
        self.assertEqual(backend_options, {})
    
    def test_desktop_flag_flow(self):
        """Test backend selection with --desktop flag"""
        from tfm_backend_selector import select_backend
        
        # Create mock args with desktop flag
        args = argparse.Namespace()
        args.backend = None
        args.desktop = True
        
        # Should request coregraphics (may fall back to curses if not available)
        backend_name, backend_options = select_backend(args)
        self.assertIn(backend_name, ['curses', 'coregraphics'])
        
        # If coregraphics, should have options
        if backend_name == 'coregraphics':
            self.assertIn('window_title', backend_options)
            self.assertIn('font_name', backend_options)
            self.assertIn('font_size', backend_options)
    
    def test_explicit_backend_flow(self):
        """Test backend selection with explicit --backend argument"""
        from tfm_backend_selector import select_backend
        
        # Create mock args with explicit backend
        args = argparse.Namespace()
        args.backend = 'curses'
        args.desktop = False
        
        backend_name, backend_options = select_backend(args)
        self.assertEqual(backend_name, 'curses')
        self.assertEqual(backend_options, {})
    
    def test_main_function_structure(self):
        """Test that main function has correct structure"""
        from tfm import main
        import inspect
        
        source = inspect.getsource(main)
        
        # Verify key components are present
        self.assertIn('select_backend', source, "Backend selection should be integrated")
        self.assertIn('renderer.initialize()', source, "Renderer should be initialized")
        self.assertIn('renderer.shutdown()', source, "Renderer should be shut down")
        self.assertIn('tfm_main(renderer', source, "Renderer should be passed to tfm_main")
        
        # Verify curses.wrapper is NOT called (comment is OK)
        # Check that we're not actually calling curses.wrapper
        lines = source.split('\n')
        for line in lines:
            # Skip comments
            if '#' in line:
                code_part = line.split('#')[0]
            else:
                code_part = line
            
            # Check if curses.wrapper is actually called (not just mentioned in comment)
            if 'curses.wrapper(' in code_part:
                self.fail("Should not call curses.wrapper")
    
    def test_argument_parser_completeness(self):
        """Test that argument parser has all required arguments"""
        from tfm import create_parser
        
        parser = create_parser()
        
        # Test all arguments can be parsed
        test_cases = [
            (['--backend', 'curses'], {'backend': 'curses'}),
            (['--backend', 'coregraphics'], {'backend': 'coregraphics'}),
            (['--desktop'], {'desktop': True}),
            (['--remote-log-port', '8888'], {'remote_log_port': 8888}),
            (['--left', '/tmp'], {'left': '/tmp'}),
            (['--right', '/home'], {'right': '/home'}),
        ]
        
        for argv, expected_attrs in test_cases:
            args = parser.parse_args(argv)
            for attr, value in expected_attrs.items():
                self.assertEqual(getattr(args, attr), value,
                               f"Argument {attr} should be {value} for {argv}")

if __name__ == '__main__':
    unittest.main()
