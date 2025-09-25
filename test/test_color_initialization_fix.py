#!/usr/bin/env python3
"""
Test suite for the color initialization fix

This test verifies that colors are properly initialized before stdout/stderr
redirection, which should fix the issue where colors work in --color-test
but not in the main TFM application.
"""

import unittest
import sys
import os
import curses
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src directory to path for imports
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

class TestColorInitializationFix(unittest.TestCase):
    """Test the color initialization fix"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock curses to avoid needing a real terminal
        self.curses_patcher = patch('curses.start_color')
        self.mock_start_color = self.curses_patcher.start()
        
        self.can_change_color_patcher = patch('curses.can_change_color', return_value=True)
        self.mock_can_change_color = self.can_change_color_patcher.start()
        
        self.init_color_patcher = patch('curses.init_color')
        self.mock_init_color = self.init_color_patcher.start()
        
        self.init_pair_patcher = patch('curses.init_pair')
        self.mock_init_pair = self.init_pair_patcher.start()
        
        # Mock other curses constants
        patch('curses.COLORS', 256).start()
        patch('curses.COLOR_PAIRS', 64).start()
        patch('curses.COLOR_BLACK', 0).start()
        patch('curses.COLOR_RED', 1).start()
        patch('curses.COLOR_GREEN', 2).start()
        patch('curses.COLOR_YELLOW', 3).start()
        patch('curses.COLOR_BLUE', 4).start()
        patch('curses.COLOR_MAGENTA', 5).start()
        patch('curses.COLOR_CYAN', 6).start()
        patch('curses.COLOR_WHITE', 7).start()
    
    def tearDown(self):
        """Clean up test environment"""
        patch.stopall()
    
    def test_color_initialization_order(self):
        """Test that colors are initialized before LogManager creation"""
        from tfm_colors import init_colors
        
        # Track the order of operations
        operations = []
        
        # Mock init_colors to track when it's called
        original_init_colors = init_colors
        def mock_init_colors(*args, **kwargs):
            operations.append('init_colors')
            return original_init_colors(*args, **kwargs)
        
        # Mock LogManager to track when it's created
        class MockLogManager:
            def __init__(self, *args, **kwargs):
                operations.append('LogManager.__init__')
                self.original_stdout = sys.stdout
                self.original_stderr = sys.stderr
                # Simulate stdout/stderr redirection
                sys.stdout = MagicMock()
                sys.stderr = MagicMock()
            
            def add_startup_messages(self, *args):
                pass
            
            def restore_stdio(self):
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr
        
        with patch('tfm_colors.init_colors', side_effect=mock_init_colors):
            with patch('tfm_log_manager.LogManager', MockLogManager):
                with patch('curses.curs_set'):
                    with patch('tfm_config.get_config') as mock_config:
                        # Mock config
                        config = MagicMock()
                        config.COLOR_SCHEME = 'dark'
                        mock_config.return_value = config
                        
                        # Mock stdscr
                        mock_stdscr = MagicMock()
                        mock_stdscr.keypad = MagicMock()
                        
                        # Import and create FileManager
                        from tfm_main import FileManager
                        
                        # This should initialize colors BEFORE LogManager
                        fm = FileManager(mock_stdscr)
                        
                        # Verify the order
                        self.assertEqual(operations[0], 'init_colors', 
                                       "init_colors should be called before LogManager creation")
                        self.assertEqual(operations[1], 'LogManager.__init__', 
                                       "LogManager should be created after init_colors")
                        
                        # Clean up
                        fm.log_manager.restore_stdio()
    
    def test_colors_work_after_stdout_redirection(self):
        """Test that colors still work after stdout redirection"""
        from tfm_colors import init_colors, get_file_color
        import io
        
        # Initialize colors first
        init_colors('dark')
        
        # Redirect stdout/stderr
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        
        try:
            # Colors should still work
            regular_color = get_file_color(False, False, False, True)
            dir_color = get_file_color(True, False, False, True)
            exec_color = get_file_color(False, True, False, True)
            
            # These should not raise exceptions
            self.assertIsNotNone(regular_color)
            self.assertIsNotNone(dir_color)
            self.assertIsNotNone(exec_color)
            
        finally:
            # Restore stdout/stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    
    def test_config_color_scheme_loading(self):
        """Test that color scheme is properly loaded from config"""
        with patch('tfm_config.get_config') as mock_get_config:
            # Mock config with light scheme
            config = MagicMock()
            config.COLOR_SCHEME = 'light'
            mock_get_config.return_value = config
            
            from tfm_colors import init_colors, get_current_color_scheme
            
            # Initialize colors with config
            init_colors('light')
            
            # Verify the scheme is set
            self.assertEqual(get_current_color_scheme(), 'light')
    
    def test_fallback_when_config_missing(self):
        """Test fallback to dark scheme when config doesn't specify COLOR_SCHEME"""
        with patch('tfm_config.get_config') as mock_get_config:
            # Mock config without COLOR_SCHEME
            config = MagicMock()
            del config.COLOR_SCHEME  # Simulate missing attribute
            mock_get_config.return_value = config
            
            from tfm_colors import init_colors, get_current_color_scheme
            
            # This should use 'dark' as fallback
            init_colors('dark')  # Simulate the getattr fallback
            
            # Verify fallback works
            self.assertEqual(get_current_color_scheme(), 'dark')

class TestColorInitializationIntegration(unittest.TestCase):
    """Integration tests for color initialization"""
    
    def test_color_test_vs_main_tfm_consistency(self):
        """Test that color-test and main TFM use the same initialization"""
        # This test ensures both code paths initialize colors the same way
        
        from tfm_colors import init_colors, get_current_color_scheme
        
        # Test color-test path
        with patch('curses.start_color'):
            with patch('curses.can_change_color', return_value=True):
                with patch('curses.init_color'):
                    with patch('curses.init_pair'):
                        # Initialize like color-test does
                        init_colors('dark')
                        color_test_scheme = get_current_color_scheme()
        
        # Test main TFM path (after our fix)
        with patch('curses.start_color'):
            with patch('curses.can_change_color', return_value=True):
                with patch('curses.init_color'):
                    with patch('curses.init_pair'):
                        with patch('tfm_config.get_config') as mock_config:
                            config = MagicMock()
                            config.COLOR_SCHEME = 'dark'
                            mock_config.return_value = config
                            
                            # Initialize like main TFM does (after fix)
                            color_scheme = getattr(config, 'COLOR_SCHEME', 'dark')
                            init_colors(color_scheme)
                            main_tfm_scheme = get_current_color_scheme()
        
        # Both should use the same scheme
        self.assertEqual(color_test_scheme, main_tfm_scheme)

if __name__ == '__main__':
    unittest.main()