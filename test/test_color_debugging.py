#!/usr/bin/env python3
"""
Test suite for TFM color debugging functionality
"""

import unittest
import sys
import os
import subprocess
from pathlib import Path

# Add src directory to path for imports
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

class TestColorDebugging(unittest.TestCase):
    """Test color debugging features"""
    
    def setUp(self):
        """Set up test environment"""
        self.tfm_script = Path(__file__).parent.parent / 'tfm.py'
        self.assertTrue(self.tfm_script.exists(), "tfm.py script not found")
    
    def test_color_test_argument_parsing(self):
        """Test that --color-test argument is properly parsed"""
        # Test help output includes color-test option
        result = subprocess.run([
            sys.executable, str(self.tfm_script), '--help'
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('--color-test', result.stdout)
        self.assertIn('info', result.stdout)
        self.assertIn('schemes', result.stdout)
        self.assertIn('capabilities', result.stdout)
        self.assertIn('rgb-test', result.stdout)
        # Handle line wrapping in help text
        self.assertTrue('fallback-test' in result.stdout or 'fallback-\n                        test' in result.stdout)
        self.assertIn('interactive', result.stdout)
    
    def test_color_test_info_mode(self):
        """Test color-test info mode"""
        result = subprocess.run([
            sys.executable, str(self.tfm_script), '--color-test', 'info'
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('TFM Color Testing', result.stdout)
        self.assertIn('Terminal Environment', result.stdout)
        self.assertIn('Available Color Schemes', result.stdout)
        self.assertIn('dark', result.stdout)
        self.assertIn('light', result.stdout)
    
    def test_color_test_schemes_mode(self):
        """Test color-test schemes mode"""
        result = subprocess.run([
            sys.executable, str(self.tfm_script), '--color-test', 'schemes'
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('DARK SCHEME', result.stdout)
        self.assertIn('LIGHT SCHEME', result.stdout)
        self.assertIn('RGB colors', result.stdout)
        self.assertIn('Fallback colors', result.stdout)
        self.assertIn('DIRECTORY_FG', result.stdout)
        self.assertIn('EXECUTABLE_FG', result.stdout)
    
    def test_color_test_invalid_mode(self):
        """Test color-test with invalid mode"""
        result = subprocess.run([
            sys.executable, str(self.tfm_script), '--color-test', 'invalid'
        ], capture_output=True, text=True)
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('invalid choice', result.stderr)
    
    def test_color_tester_module_import(self):
        """Test that color tester module can be imported"""
        try:
            from tfm_color_tester import run_color_test, print_basic_info
            # Test basic info function
            print_basic_info()  # Should not raise exception
        except ImportError as e:
            self.fail(f"Failed to import color tester module: {e}")
    
    def test_color_tester_functions(self):
        """Test individual color tester functions"""
        from tfm_color_tester import print_basic_info
        from tfm_colors import (
            get_available_color_schemes, get_current_color_scheme,
            COLOR_SCHEMES, FALLBACK_COLOR_SCHEMES
        )
        
        # Test that we have expected color schemes
        schemes = get_available_color_schemes()
        self.assertIn('dark', schemes)
        self.assertIn('light', schemes)
        
        # Test that current scheme is valid
        current = get_current_color_scheme()
        self.assertIn(current, schemes)
        
        # Test that color definitions exist
        self.assertIn('dark', COLOR_SCHEMES)
        self.assertIn('light', COLOR_SCHEMES)
        self.assertIn('dark', FALLBACK_COLOR_SCHEMES)
        self.assertIn('light', FALLBACK_COLOR_SCHEMES)
        
        # Test that key colors are defined
        for scheme in ['dark', 'light']:
            rgb_colors = COLOR_SCHEMES[scheme]
            fallback_colors = FALLBACK_COLOR_SCHEMES[scheme]
            
            key_colors = ['DIRECTORY_FG', 'EXECUTABLE_FG', 'REGULAR_FILE_FG', 'SELECTED_BG']
            for color_name in key_colors:
                self.assertIn(color_name, rgb_colors, 
                             f"{color_name} not found in {scheme} RGB colors")
                self.assertIn(color_name, fallback_colors, 
                             f"{color_name} not found in {scheme} fallback colors")
    
    def test_environment_detection(self):
        """Test terminal environment detection"""
        from tfm_color_tester import print_basic_info
        import io
        import contextlib
        
        # Capture output
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            print_basic_info()
        
        output = f.getvalue()
        
        # Should include environment information
        self.assertIn('Terminal Environment', output)
        self.assertIn('TERM:', output)
        self.assertIn('COLORTERM:', output)
        
        # Should include color scheme information
        self.assertIn('Available Color Schemes', output)
        self.assertIn('RGB Color Definitions', output)
        self.assertIn('Fallback Color Definitions', output)

class TestColorTestingIntegration(unittest.TestCase):
    """Integration tests for color testing with TFM"""
    
    def setUp(self):
        """Set up test environment"""
        self.tfm_script = Path(__file__).parent.parent / 'tfm.py'
    
    def test_color_test_does_not_start_main_tfm(self):
        """Test that color-test mode doesn't start the main TFM interface"""
        # This test ensures that when --color-test is used, 
        # the main TFM curses interface is not started
        
        # Run with a short timeout to ensure it doesn't hang waiting for input
        try:
            result = subprocess.run([
                sys.executable, str(self.tfm_script), '--color-test', 'info'
            ], capture_output=True, text=True, timeout=10)
            
            self.assertEqual(result.returncode, 0)
            # Should complete quickly without starting curses interface
            self.assertIn('TFM Color Testing', result.stdout)
            
        except subprocess.TimeoutExpired:
            self.fail("Color test mode took too long - may have started main TFM interface")
    
    def test_normal_tfm_still_works(self):
        """Test that normal TFM functionality is not broken by color testing additions"""
        # Test that TFM can still parse arguments normally
        result = subprocess.run([
            sys.executable, str(self.tfm_script), '--help'
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        
        # Should include both old and new arguments
        self.assertIn('--remote-log-port', result.stdout)
        self.assertIn('--left', result.stdout)
        self.assertIn('--right', result.stdout)
        self.assertIn('--color-test', result.stdout)

if __name__ == '__main__':
    unittest.main()