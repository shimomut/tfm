#!/usr/bin/env python3
"""
Tests for TTK Test Interface

This module tests the test_interface module to ensure it correctly
demonstrates TTK rendering capabilities.
"""

import unittest
from unittest.mock import Mock, MagicMock, call
from ttk.demo.test_interface import TestInterface, create_test_interface
from ttk.input_event import InputEvent, KeyCode, ModifierKey
from ttk.renderer import TextAttribute


class TestTestInterface(unittest.TestCase):
    """Test cases for the TestInterface class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (40, 80)
        
        # Create test interface
        self.interface = TestInterface(self.mock_renderer)
    
    def test_initialization(self):
        """Test that TestInterface initializes correctly."""
        self.assertEqual(self.interface.renderer, self.mock_renderer)
        self.assertFalse(self.interface.running)
        self.assertIsNone(self.interface.last_input)
        self.assertEqual(self.interface.input_history, [])
        self.assertEqual(self.interface.max_history, 5)
    
    def test_initialize_colors(self):
        """Test that color pairs are initialized correctly."""
        self.interface.initialize_colors()
        
        # Verify init_color_pair was called for all color pairs
        self.assertEqual(self.mock_renderer.init_color_pair.call_count, 10)
        
        # Check some specific color pairs
        calls = self.mock_renderer.init_color_pair.call_args_list
        
        # Color pair 1: White on black
        self.assertIn(call(1, (255, 255, 255), (0, 0, 0)), calls)
        
        # Color pair 2: Red on black
        self.assertIn(call(2, (255, 0, 0), (0, 0, 0)), calls)
        
        # Color pair 8: White on blue
        self.assertIn(call(8, (255, 255, 255), (0, 0, 128)), calls)
    
    def test_draw_header(self):
        """Test that header is drawn correctly."""
        row = self.interface.draw_header(0)
        
        # Verify draw_text was called for title and instructions
        self.assertTrue(self.mock_renderer.draw_text.called)
        
        # Check that title bar was drawn
        title_calls = [c for c in self.mock_renderer.draw_text.call_args_list
                      if "TTK Test Interface" in str(c)]
        self.assertTrue(len(title_calls) > 0)
        
        # Verify row is advanced
        self.assertGreater(row, 0)
    
    def test_draw_color_test(self):
        """Test that color test section is drawn."""
        row = self.interface.draw_color_test(5)
        
        # Verify colors are drawn
        self.assertTrue(self.mock_renderer.draw_text.called)
        
        # Check that color names are drawn
        calls_str = str(self.mock_renderer.draw_text.call_args_list)
        self.assertIn("Red", calls_str)
        self.assertIn("Green", calls_str)
        self.assertIn("Blue", calls_str)
        
        # Verify row is advanced
        self.assertGreater(row, 5)
    
    def test_draw_attribute_test(self):
        """Test that attribute test section is drawn."""
        row = self.interface.draw_attribute_test(10)
        
        # Verify attributes are drawn
        self.assertTrue(self.mock_renderer.draw_text.called)
        
        # Check that attribute descriptions are drawn
        calls_str = str(self.mock_renderer.draw_text.call_args_list)
        self.assertIn("Bold", calls_str)
        self.assertIn("Underline", calls_str)
        self.assertIn("Reverse", calls_str)
        
        # Verify row is advanced
        self.assertGreater(row, 10)
    
    def test_draw_shape_test(self):
        """Test that shape test section is drawn."""
        row = self.interface.draw_shape_test(15)
        
        # Verify shapes are drawn
        self.assertTrue(self.mock_renderer.draw_rect.called or 
                       self.mock_renderer.draw_hline.called or
                       self.mock_renderer.draw_vline.called)
        
        # Verify row is advanced
        self.assertGreaterEqual(row, 15)
    
    def test_draw_coordinate_info(self):
        """Test that coordinate information is drawn."""
        row = self.interface.draw_coordinate_info(20)
        
        # Verify coordinate info is drawn
        self.assertTrue(self.mock_renderer.draw_text.called)
        
        # Check that dimension info is included
        calls_str = str(self.mock_renderer.draw_text.call_args_list)
        self.assertIn("40", calls_str)  # rows
        self.assertIn("80", calls_str)  # cols
        
        # Verify corner markers are drawn
        self.assertTrue(self.mock_renderer.draw_text.called)
        
        # Verify row is advanced
        self.assertGreater(row, 20)
    
    def test_draw_input_echo_no_input(self):
        """Test input echo area with no input."""
        row = self.interface.draw_input_echo(25)
        
        # Verify section is drawn
        self.assertTrue(self.mock_renderer.draw_text.called)
        
        # Check for "No input yet" message
        calls_str = str(self.mock_renderer.draw_text.call_args_list)
        self.assertIn("No input", calls_str)
        
        # Verify row is advanced
        self.assertGreaterEqual(row, 25)
    
    def test_draw_input_echo_with_input(self):
        """Test input echo area with input."""
        # Set up some input
        event = InputEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
        self.interface.last_input = event
        self.interface.input_history = [event]
        
        row = self.interface.draw_input_echo(25)
        
        # Verify input is displayed
        self.assertTrue(self.mock_renderer.draw_text.called)
        
        # Check that input info is shown
        calls_str = str(self.mock_renderer.draw_text.call_args_list)
        self.assertIn("'a'", calls_str)
        
        # Verify row is advanced
        self.assertGreaterEqual(row, 25)
    
    def test_draw_input_echo_with_modifiers(self):
        """Test input echo displays modifiers correctly."""
        # Set up input with modifiers
        event = InputEvent(
            key_code=ord('A'),
            modifiers=ModifierKey.SHIFT | ModifierKey.CONTROL,
            char='A'
        )
        self.interface.last_input = event
        
        self.interface.draw_input_echo(25)
        
        # Check that modifiers are shown
        calls_str = str(self.mock_renderer.draw_text.call_args_list)
        self.assertIn("Shift", calls_str)
        self.assertIn("Ctrl", calls_str)
    
    def test_draw_interface(self):
        """Test that complete interface is drawn."""
        self.interface.draw_interface()
        
        # Verify clear was called
        self.mock_renderer.clear.assert_called_once()
        
        # Verify refresh was called
        self.mock_renderer.refresh.assert_called_once()
        
        # Verify various sections were drawn
        self.assertTrue(self.mock_renderer.draw_text.called)
    
    def test_handle_input_printable(self):
        """Test handling printable character input."""
        event = InputEvent(key_code=ord('x'), modifiers=ModifierKey.NONE, char='x')
        
        result = self.interface.handle_input(event)
        
        # Should continue running
        self.assertTrue(result)
        
        # Input should be stored
        self.assertEqual(self.interface.last_input, event)
        self.assertIn(event, self.interface.input_history)
    
    def test_handle_input_quit_lowercase(self):
        """Test handling 'q' to quit."""
        event = InputEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
        
        result = self.interface.handle_input(event)
        
        # Should stop running
        self.assertFalse(result)
    
    def test_handle_input_quit_uppercase(self):
        """Test handling 'Q' to quit."""
        event = InputEvent(key_code=ord('Q'), modifiers=ModifierKey.NONE, char='Q')
        
        result = self.interface.handle_input(event)
        
        # Should stop running
        self.assertFalse(result)
    
    def test_handle_input_escape(self):
        """Test handling ESC key to quit."""
        event = InputEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
        
        result = self.interface.handle_input(event)
        
        # Should stop running
        self.assertFalse(result)
    
    def test_handle_input_special_key(self):
        """Test handling special keys."""
        event = InputEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
        
        result = self.interface.handle_input(event)
        
        # Should continue running
        self.assertTrue(result)
        
        # Input should be stored
        self.assertEqual(self.interface.last_input, event)
    
    def test_input_history_limit(self):
        """Test that input history is limited."""
        # Add more than 20 inputs
        for i in range(25):
            event = InputEvent(key_code=ord('a') + i, modifiers=ModifierKey.NONE, char=chr(ord('a') + i))
            self.interface.handle_input(event)
        
        # History should be limited to 20
        self.assertEqual(len(self.interface.input_history), 20)
    
    def test_run_basic_flow(self):
        """Test basic run flow."""
        # Set up mock to return quit event after one iteration
        quit_event = InputEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
        self.mock_renderer.get_input.return_value = quit_event
        
        # Run the interface
        self.interface.run()
        
        # Verify initialization happened
        self.mock_renderer.init_color_pair.assert_called()
        
        # Verify interface was drawn
        self.mock_renderer.clear.assert_called()
        self.mock_renderer.refresh.assert_called()
        
        # Verify running flag is set correctly
        self.assertFalse(self.interface.running)
    
    def test_run_with_timeout(self):
        """Test run handles timeout correctly."""
        # Set up mock to return None (timeout) then quit
        self.mock_renderer.get_input.side_effect = [
            None,  # Timeout
            None,  # Timeout
            InputEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')  # Quit
        ]
        
        # Run the interface
        self.interface.run()
        
        # Should have handled timeouts gracefully
        self.assertFalse(self.interface.running)
    
    def test_create_test_interface(self):
        """Test factory function creates interface correctly."""
        interface = create_test_interface(self.mock_renderer)
        
        self.assertIsInstance(interface, TestInterface)
        self.assertEqual(interface.renderer, self.mock_renderer)


class TestTestInterfaceEdgeCases(unittest.TestCase):
    """Test edge cases for TestInterface."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_renderer = Mock()
        self.interface = TestInterface(self.mock_renderer)
    
    def test_draw_with_small_window(self):
        """Test drawing with very small window dimensions."""
        # Set small dimensions
        self.mock_renderer.get_dimensions.return_value = (10, 20)
        
        # Should not crash
        self.interface.draw_interface()
        
        # Verify clear and refresh were called
        self.mock_renderer.clear.assert_called_once()
        self.mock_renderer.refresh.assert_called_once()
    
    def test_draw_with_large_window(self):
        """Test drawing with large window dimensions."""
        # Set large dimensions
        self.mock_renderer.get_dimensions.return_value = (100, 200)
        
        # Should not crash
        self.interface.draw_interface()
        
        # Verify clear and refresh were called
        self.mock_renderer.clear.assert_called_once()
        self.mock_renderer.refresh.assert_called_once()
    
    def test_handle_input_with_mouse_event(self):
        """Test handling mouse events."""
        event = InputEvent(
            key_code=KeyCode.MOUSE,
            modifiers=ModifierKey.NONE,
            mouse_row=10,
            mouse_col=20,
            mouse_button=1
        )
        
        result = self.interface.handle_input(event)
        
        # Should continue running
        self.assertTrue(result)
        
        # Input should be stored
        self.assertEqual(self.interface.last_input, event)


if __name__ == '__main__':
    unittest.main()
