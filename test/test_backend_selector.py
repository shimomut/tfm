#!/usr/bin/env python3
"""
Tests for TFM Backend Selector

Tests the backend selection logic including platform detection,
PyObjC availability checking, and graceful fallback behavior.
"""

import sys
import platform
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_backend_selector import (
    select_backend,
    _get_requested_backend,
    _validate_backend_availability,
    _get_backend_options
)


class TestBackendSelector(unittest.TestCase):
    """Test suite for backend selector module"""
    
    def test_select_backend_default_curses(self):
        """Test that default backend is curses"""
        args = Mock()
        args.backend = None
        args.desktop = False
        
        backend_name, options = select_backend(args)
        
        self.assertEqual(backend_name, 'curses')
        self.assertEqual(options, {})
    
    def test_select_backend_explicit_curses(self):
        """Test explicit curses backend selection"""
        args = Mock()
        args.backend = 'curses'
        args.desktop = False
        
        backend_name, options = select_backend(args)
        
        self.assertEqual(backend_name, 'curses')
        self.assertEqual(options, {})
    
    @patch('platform.system')
    def test_select_backend_coregraphics_on_macos(self, mock_platform):
        """Test CoreGraphics backend selection on macOS with PyObjC available"""
        mock_platform.return_value = 'Darwin'
        
        # Mock PyObjC import success
        with patch('builtins.__import__', return_value=MagicMock()):
            args = Mock()
            args.backend = 'coregraphics'
            args.desktop = False
            
            backend_name, options = select_backend(args)
            
            self.assertEqual(backend_name, 'coregraphics')
            self.assertIn('window_title', options)
            self.assertIn('font_name', options)
            self.assertIn('font_size', options)
    
    @patch('platform.system')
    def test_select_backend_coregraphics_fallback_non_macos(self, mock_platform):
        """Test CoreGraphics backend falls back to curses on non-macOS"""
        mock_platform.return_value = 'Linux'
        
        args = Mock()
        args.backend = 'coregraphics'
        args.desktop = False
        
        backend_name, options = select_backend(args)
        
        self.assertEqual(backend_name, 'curses')
        self.assertEqual(options, {})
    
    @patch('platform.system')
    def test_select_backend_coregraphics_fallback_no_pyobjc(self, mock_platform):
        """Test CoreGraphics backend falls back to curses when PyObjC is missing"""
        mock_platform.return_value = 'Darwin'
        
        # Mock PyObjC import failure
        with patch('builtins.__import__', side_effect=ImportError("No module named 'objc'")):
            args = Mock()
            args.backend = 'coregraphics'
            args.desktop = False
            
            backend_name, options = select_backend(args)
            
            self.assertEqual(backend_name, 'curses')
            self.assertEqual(options, {})
    
    def test_select_backend_desktop_flag(self):
        """Test --desktop flag selects CoreGraphics backend"""
        args = Mock()
        args.backend = None
        args.desktop = True
        
        # Will fall back to curses on non-macOS or without PyObjC
        backend_name, options = select_backend(args)
        
        # On non-macOS or without PyObjC, should fall back to curses
        if platform.system() != 'Darwin':
            self.assertEqual(backend_name, 'curses')
        else:
            # On macOS, depends on PyObjC availability
            self.assertIn(backend_name, ['curses', 'coregraphics'])
    
    def test_get_requested_backend_from_args(self):
        """Test backend request from command-line arguments"""
        args = Mock()
        args.backend = 'coregraphics'
        args.desktop = False
        
        backend_name = _get_requested_backend(args)
        
        self.assertEqual(backend_name, 'coregraphics')
    
    def test_get_requested_backend_from_desktop_flag(self):
        """Test backend request from --desktop flag"""
        args = Mock()
        args.backend = None
        args.desktop = True
        
        backend_name = _get_requested_backend(args)
        
        self.assertEqual(backend_name, 'coregraphics')
    
    def test_get_requested_backend_default(self):
        """Test default backend request"""
        args = Mock()
        args.backend = None
        args.desktop = False
        
        backend_name = _get_requested_backend(args)
        
        self.assertEqual(backend_name, 'curses')
    
    @patch('platform.system')
    def test_validate_backend_curses_always_available(self, mock_platform):
        """Test curses backend is always available"""
        mock_platform.return_value = 'Linux'
        
        backend_name = _validate_backend_availability('curses')
        
        self.assertEqual(backend_name, 'curses')
    
    @patch('platform.system')
    def test_validate_backend_coregraphics_requires_macos(self, mock_platform):
        """Test CoreGraphics backend requires macOS"""
        mock_platform.return_value = 'Linux'
        
        backend_name = _validate_backend_availability('coregraphics')
        
        self.assertEqual(backend_name, 'curses')
    
    @patch('platform.system')
    def test_validate_backend_coregraphics_requires_pyobjc(self, mock_platform):
        """Test CoreGraphics backend requires PyObjC"""
        mock_platform.return_value = 'Darwin'
        
        # Mock PyObjC import failure
        with patch('builtins.__import__', side_effect=ImportError("No module named 'objc'")):
            backend_name = _validate_backend_availability('coregraphics')
            
            self.assertEqual(backend_name, 'curses')
    
    def test_get_backend_options_curses(self):
        """Test curses backend options are empty"""
        args = Mock()
        
        options = _get_backend_options('curses', args)
        
        self.assertEqual(options, {})
    
    def test_get_backend_options_coregraphics_defaults(self):
        """Test CoreGraphics backend has default options"""
        args = Mock()
        
        options = _get_backend_options('coregraphics', args)
        
        self.assertIn('window_title', options)
        self.assertIn('font_name', options)
        self.assertIn('font_size', options)
        self.assertEqual(options['window_title'], 'TFM - TUI File Manager')
        self.assertEqual(options['font_name'], 'Menlo')
        self.assertEqual(options['font_size'], 14)


class TestBackendSelectorIntegration(unittest.TestCase):
    """Integration tests for backend selector"""
    
    def test_backend_selector_args_priority(self):
        """Test that command-line args take priority over config"""
        args = Mock()
        args.backend = 'curses'
        args.desktop = False
        
        backend_name, options = select_backend(args)
        
        # Should use curses regardless of config
        self.assertEqual(backend_name, 'curses')
    
    def test_backend_selector_desktop_flag_priority(self):
        """Test that --desktop flag takes priority"""
        args = Mock()
        args.backend = None
        args.desktop = True
        
        backend_name, options = select_backend(args)
        
        # Should request coregraphics (may fall back to curses)
        # On non-macOS or without PyObjC, will be curses
        self.assertIn(backend_name, ['curses', 'coregraphics'])


if __name__ == '__main__':
    unittest.main()
