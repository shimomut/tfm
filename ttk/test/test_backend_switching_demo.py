#!/usr/bin/env python3
"""
Tests for Backend Switching Demo

This test suite verifies that the backend switching demo works correctly
and demonstrates that the same application code works with both curses
and CoreGraphics backends.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from ttk.demo.backend_switching import (
    BackendSwitchingDemo,
    create_backend,
    parse_arguments
)
from ttk.renderer import Renderer, TextAttribute
from ttk.input_event import InputEvent, KeyCode


class TestBackendSwitchingDemo(unittest.TestCase):
    """Test the BackendSwitchingDemo class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock renderer
        self.mock_renderer = Mock(spec=Renderer)
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        
        # Create demo instance
        self.demo = BackendSwitchingDemo(self.mock_renderer)
    
    def test_initialization(self):
        """Test demo initialization."""
        self.assertIsNotNone(self.demo.renderer)
        self.assertFalse(self.demo.running)
        self.assertEqual(self.demo.frame_count, 0)
    
    def test_initialize_colors(self):
        """Test color initialization."""
        self.demo.initialize_colors()
        
        # Verify color pairs were initialized
        self.assertEqual(self.mock_renderer.init_color_pair.call_count, 8)
        
        # Verify specific color pairs
        calls = self.mock_renderer.init_color_pair.call_args_list
        
        # Color pair 1: White on black
        self.assertEqual(calls[0][0], (1, (255, 255, 255), (0, 0, 0)))
        
        # Color pair 2: Red on black
        self.assertEqual(calls[1][0], (2, (255, 0, 0), (0, 0, 0)))
        
        # Color pair 3: Green on black
        self.assertEqual(calls[2][0], (3, (0, 255, 0), (0, 0, 0)))
    
    def test_draw_screen(self):
        """Test screen drawing."""
        self.demo.draw_screen()
        
        # Verify clear was called
        self.mock_renderer.clear.assert_called_once()
        
        # Verify get_dimensions was called
        self.mock_renderer.get_dimensions.assert_called()
        
        # Verify text was drawn (multiple calls)
        self.assertGreater(self.mock_renderer.draw_text.call_count, 0)
        
        # Verify refresh was called
        self.mock_renderer.refresh.assert_called_once()
        
        # Verify frame count incremented
        self.assertEqual(self.demo.frame_count, 1)
    
    def test_draw_screen_with_shapes(self):
        """Test screen drawing includes shapes."""
        # Set dimensions that allow shapes to be drawn
        self.mock_renderer.get_dimensions.return_value = (30, 80)
        
        self.demo.draw_screen()
        
        # Verify shapes were drawn
        self.mock_renderer.draw_rect.assert_called()
        self.mock_renderer.draw_hline.assert_called()
    
    def test_handle_input_quit_lowercase(self):
        """Test handling quit command with lowercase 'q'."""
        event = InputEvent(key_code=ord('q'), char='q', modifiers=0)
        
        result = self.demo.handle_input(event)
        
        self.assertFalse(result)
    
    def test_handle_input_quit_uppercase(self):
        """Test handling quit command with uppercase 'Q'."""
        event = InputEvent(key_code=ord('Q'), char='Q', modifiers=0)
        
        result = self.demo.handle_input(event)
        
        self.assertFalse(result)
    
    def test_handle_input_escape(self):
        """Test handling ESC key."""
        event = InputEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=0)
        
        result = self.demo.handle_input(event)
        
        self.assertFalse(result)
    
    def test_handle_input_resize(self):
        """Test handling resize event."""
        event = InputEvent(key_code=KeyCode.RESIZE, char=None, modifiers=0)
        
        result = self.demo.handle_input(event)
        
        self.assertTrue(result)
    
    def test_handle_input_regular_key(self):
        """Test handling regular key press."""
        event = InputEvent(key_code=ord('a'), char='a', modifiers=0)
        
        result = self.demo.handle_input(event)
        
        self.assertTrue(result)
    
    def test_run_with_quit(self):
        """Test running demo and quitting."""
        # Mock get_input to return quit event
        quit_event = InputEvent(key_code=ord('q'), char='q', modifiers=0)
        self.mock_renderer.get_input.return_value = quit_event
        
        self.demo.run()
        
        # Verify demo stopped
        self.assertFalse(self.demo.running)
        
        # Verify colors were initialized
        self.mock_renderer.init_color_pair.assert_called()
        
        # Verify screen was drawn
        self.mock_renderer.draw_text.assert_called()
    
    def test_run_with_keyboard_interrupt(self):
        """Test handling keyboard interrupt."""
        # Mock get_input to raise KeyboardInterrupt
        self.mock_renderer.get_input.side_effect = KeyboardInterrupt()
        
        self.demo.run()
        
        # Verify demo stopped gracefully
        self.assertFalse(self.demo.running)


class TestCreateBackend(unittest.TestCase):
    """Test backend creation function."""
    
    def test_create_curses_backend(self):
        """Test creating curses backend."""
        backend = create_backend('curses')
        
        self.assertIsNotNone(backend)
        # Verify it's a Renderer instance
        self.assertIsInstance(backend, Renderer)
    
    @patch('ttk.demo.backend_switching.platform.system')
    def test_create_coregraphics_backend_on_macos(self, mock_system):
        """Test creating CoreGraphics backend on macOS."""
        mock_system.return_value = 'Darwin'
        
        backend = create_backend('coregraphics')
        
        self.assertIsNotNone(backend)
        self.assertIsInstance(backend, Renderer)
    
    @patch('ttk.demo.backend_switching.platform.system')
    def test_create_coregraphics_backend_on_non_macos(self, mock_system):
        """Test creating CoreGraphics backend on non-macOS raises error."""
        mock_system.return_value = 'Linux'
        
        with self.assertRaises(ValueError) as context:
            create_backend('coregraphics')
        
        self.assertIn("only available on macOS", str(context.exception))
    
    def test_create_invalid_backend(self):
        """Test creating invalid backend raises error."""
        with self.assertRaises(ValueError) as context:
            create_backend('invalid')
        
        self.assertIn("Unknown backend", str(context.exception))


class TestParseArguments(unittest.TestCase):
    """Test command-line argument parsing."""
    
    def test_parse_curses_backend(self):
        """Test parsing curses backend argument."""
        with patch('sys.argv', ['backend_switching.py', '--backend', 'curses']):
            args = parse_arguments()
            self.assertEqual(args.backend, 'curses')
    
    def test_parse_coregraphics_backend(self):
        """Test parsing coregraphics backend argument."""
        with patch('sys.argv', ['backend_switching.py', '--backend', 'coregraphics']):
            args = parse_arguments()
            self.assertEqual(args.backend, 'coregraphics')
    
    def test_parse_missing_backend(self):
        """Test parsing without backend argument raises error."""
        with patch('sys.argv', ['backend_switching.py']):
            with self.assertRaises(SystemExit):
                parse_arguments()
    
    def test_parse_invalid_backend(self):
        """Test parsing invalid backend argument raises error."""
        with patch('sys.argv', ['backend_switching.py', '--backend', 'invalid']):
            with self.assertRaises(SystemExit):
                parse_arguments()


class TestBackendIndependence(unittest.TestCase):
    """Test that demo works identically with different backends."""
    
    def test_same_code_works_with_both_backends(self):
        """Test that the same demo code works with both backends."""
        # Create mock renderers for both backends
        curses_renderer = Mock(spec=Renderer)
        curses_renderer.get_dimensions.return_value = (24, 80)
        
        coregraphics_renderer = Mock(spec=Renderer)
        coregraphics_renderer.get_dimensions.return_value = (24, 80)
        
        # Create demo instances with different backends
        curses_demo = BackendSwitchingDemo(curses_renderer)
        coregraphics_demo = BackendSwitchingDemo(coregraphics_renderer)
        
        # Initialize colors for both
        curses_demo.initialize_colors()
        coregraphics_demo.initialize_colors()
        
        # Verify same number of color pairs initialized
        self.assertEqual(
            curses_renderer.init_color_pair.call_count,
            coregraphics_renderer.init_color_pair.call_count
        )
        
        # Draw screen for both
        curses_demo.draw_screen()
        coregraphics_demo.draw_screen()
        
        # Verify same number of draw operations
        self.assertEqual(
            curses_renderer.draw_text.call_count,
            coregraphics_renderer.draw_text.call_count
        )
        
        # Verify same refresh calls
        self.assertEqual(
            curses_renderer.refresh.call_count,
            coregraphics_renderer.refresh.call_count
        )
    
    def test_input_handling_identical(self):
        """Test that input handling is identical for both backends."""
        # Create mock renderers
        curses_renderer = Mock(spec=Renderer)
        coregraphics_renderer = Mock(spec=Renderer)
        
        # Create demo instances
        curses_demo = BackendSwitchingDemo(curses_renderer)
        coregraphics_demo = BackendSwitchingDemo(coregraphics_renderer)
        
        # Test same input events
        test_events = [
            InputEvent(key_code=ord('q'), char='q', modifiers=0),
            InputEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=0),
            InputEvent(key_code=KeyCode.RESIZE, char=None, modifiers=0),
            InputEvent(key_code=ord('a'), char='a', modifiers=0),
        ]
        
        for event in test_events:
            curses_result = curses_demo.handle_input(event)
            coregraphics_result = coregraphics_demo.handle_input(event)
            
            # Verify identical behavior
            self.assertEqual(curses_result, coregraphics_result)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
