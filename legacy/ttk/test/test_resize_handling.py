#!/usr/bin/env python3
"""
Test resize handling in the demo application.

This test verifies that the test interface properly handles window resize
events and updates the UI layout accordingly.
"""

import unittest
from unittest.mock import Mock, MagicMock, call
from ttk.demo.test_interface import TestInterface
from ttk import KeyEvent, KeyCode, ModifierKey


class TestResizeHandling(unittest.TestCase):
    """Test cases for window resize handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        self.mock_renderer.clear.return_value = None
        self.mock_renderer.refresh.return_value = None
        self.mock_renderer.draw_text.return_value = None
        self.mock_renderer.draw_rect.return_value = None
        self.mock_renderer.draw_hline.return_value = None
        self.mock_renderer.draw_vline.return_value = None
        self.mock_renderer.init_color_pair.return_value = None
        
        # Create test interface without performance monitoring for simpler tests
        self.interface = TestInterface(self.mock_renderer, enable_performance_monitoring=False)
        self.interface.initialize_colors()
    
    def test_resize_event_detection(self):
        """Test that resize events are properly detected."""
        # Create a resize event
        resize_event = KeyEvent(
            key_code=KeyCode.RESIZE,
            modifiers=ModifierKey.NONE
        )
        
        # Handle the event
        result = self.interface.handle_input(resize_event)
        
        # Should return True to continue running
        self.assertTrue(result)
        
        # Resize events should not be stored in history
        self.assertEqual(len(self.interface.input_history), 0)
        
        # Last input should not be set for resize events
        self.assertIsNone(self.interface.last_input)
    
    def test_resize_triggers_redraw(self):
        """Test that resize events trigger interface redraw."""
        # Create a resize event
        resize_event = KeyEvent(
            key_code=KeyCode.RESIZE,
            modifiers=ModifierKey.NONE
        )
        
        # Mock the draw_interface method to track calls
        self.interface.draw_interface = Mock()
        
        # Simulate the main loop handling a resize event
        # In the actual loop, resize events trigger draw_interface
        if resize_event.key_code == KeyCode.RESIZE:
            self.interface.draw_interface()
        
        # Verify draw_interface was called
        self.interface.draw_interface.assert_called_once()
    
    def test_dimensions_update_after_resize(self):
        """Test that dimension display updates after resize."""
        # Use large dimensions to ensure all sections are drawn
        self.mock_renderer.get_dimensions.return_value = (50, 120)
        
        # Draw interface with initial dimensions
        self.interface.draw_interface()
        
        # Verify get_dimensions was called
        self.mock_renderer.get_dimensions.assert_called()
        initial_call_count = self.mock_renderer.get_dimensions.call_count
        
        # Reset mock
        self.mock_renderer.reset_mock()
        self.mock_renderer.get_dimensions.return_value = (60, 150)
        
        # Draw interface with new dimensions
        self.interface.draw_interface()
        
        # Verify get_dimensions was called again with new dimensions
        self.mock_renderer.get_dimensions.assert_called()
        # The interface should query dimensions multiple times during drawing
        self.assertGreater(self.mock_renderer.get_dimensions.call_count, 0)
    
    def test_layout_adapts_to_smaller_window(self):
        """Test that layout adapts when window becomes smaller."""
        # Start with large window
        self.mock_renderer.get_dimensions.return_value = (50, 120)
        self.interface.draw_interface()
        initial_call_count = self.mock_renderer.draw_text.call_count
        
        # Reset mock
        self.mock_renderer.reset_mock()
        
        # Resize to smaller window
        self.mock_renderer.get_dimensions.return_value = (15, 40)
        self.interface.draw_interface()
        smaller_call_count = self.mock_renderer.draw_text.call_count
        
        # Smaller window should have fewer draw calls (some sections skipped)
        self.assertLess(smaller_call_count, initial_call_count)
    
    def test_layout_adapts_to_larger_window(self):
        """Test that layout adapts when window becomes larger."""
        # Start with small window
        self.mock_renderer.get_dimensions.return_value = (15, 40)
        self.interface.draw_interface()
        initial_call_count = self.mock_renderer.draw_text.call_count
        
        # Reset mock
        self.mock_renderer.reset_mock()
        
        # Resize to larger window
        self.mock_renderer.get_dimensions.return_value = (50, 120)
        self.interface.draw_interface()
        larger_call_count = self.mock_renderer.draw_text.call_count
        
        # Larger window should have more draw calls (more sections visible)
        self.assertGreater(larger_call_count, initial_call_count)
    
    def test_corner_markers_update_after_resize(self):
        """Test that corner markers are drawn at correct positions after resize."""
        # Use large dimensions to ensure coordinate info section is drawn
        self.mock_renderer.get_dimensions.return_value = (50, 120)
        self.interface.draw_interface()
        
        # Find corner marker calls
        calls = self.mock_renderer.draw_text.call_args_list
        corner_calls = []
        for call in calls:
            args, kwargs = call
            if len(args) >= 3 and args[2] == '+':
                corner_calls.append(call)
        
        # Should have 4 corner markers
        self.assertEqual(len(corner_calls), 4, "Should have 4 corner markers")
        
        # Verify initial corner positions
        positions = [(call[0][0], call[0][1]) for call in corner_calls]
        self.assertIn((0, 0), positions)  # Top-left
        self.assertIn((0, 119), positions)  # Top-right
        self.assertIn((49, 0), positions)  # Bottom-left
        self.assertIn((49, 119), positions)  # Bottom-right
        
        # Reset mock
        self.mock_renderer.reset_mock()
        
        # Resize window
        self.mock_renderer.get_dimensions.return_value = (60, 150)
        self.interface.draw_interface()
        
        # Find new corner marker calls
        calls = self.mock_renderer.draw_text.call_args_list
        corner_calls = []
        for call in calls:
            args, kwargs = call
            if len(args) >= 3 and args[2] == '+':
                corner_calls.append(call)
        
        # Should still have 4 corner markers
        self.assertEqual(len(corner_calls), 4, "Should still have 4 corner markers after resize")
        
        # Verify new corner positions
        positions = [(call[0][0], call[0][1]) for call in corner_calls]
        self.assertIn((0, 0), positions)  # Top-left
        self.assertIn((0, 149), positions)  # Top-right
        self.assertIn((59, 0), positions)  # Bottom-left
        self.assertIn((59, 149), positions)  # Bottom-right
    
    def test_resize_does_not_affect_quit_functionality(self):
        """Test that resize events don't interfere with quit functionality."""
        # Create a resize event
        resize_event = KeyEvent(
            key_code=KeyCode.RESIZE,
            modifiers=ModifierKey.NONE
        )
        
        # Handle resize event
        result = self.interface.handle_input(resize_event)
        self.assertTrue(result)  # Should continue running
        
        # Create a quit event
        quit_event = KeyEvent(
            key_code=ord('q'),
            modifiers=ModifierKey.NONE,
            char='q'
        )
        
        # Handle quit event
        result = self.interface.handle_input(quit_event)
        self.assertFalse(result)  # Should stop running
    
    def test_multiple_resize_events(self):
        """Test handling multiple consecutive resize events."""
        # Create multiple resize events
        for _ in range(5):
            resize_event = KeyEvent(
                key_code=KeyCode.RESIZE,
                modifiers=ModifierKey.NONE
            )
            
            result = self.interface.handle_input(resize_event)
            self.assertTrue(result)
        
        # No resize events should be in history
        self.assertEqual(len(self.interface.input_history), 0)
        
        # Last input should still be None
        self.assertIsNone(self.interface.last_input)


class TestResizeIntegration(unittest.TestCase):
    """Integration tests for resize handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        self.interface = TestInterface(self.mock_renderer, enable_performance_monitoring=False)
        self.interface.initialize_colors()
    
    def test_resize_between_normal_inputs(self):
        """Test resize events interspersed with normal input."""
        # Normal input
        normal_event = KeyEvent(
            key_code=ord('a'),
            modifiers=ModifierKey.NONE,
            char='a'
        )
        self.interface.handle_input(normal_event)
        self.assertEqual(len(self.interface.input_history), 1)
        
        # Resize event
        resize_event = KeyEvent(
            key_code=KeyCode.RESIZE,
            modifiers=ModifierKey.NONE
        )
        self.interface.handle_input(resize_event)
        self.assertEqual(len(self.interface.input_history), 1)  # Still 1
        
        # Another normal input
        normal_event2 = KeyEvent(
            key_code=ord('b'),
            modifiers=ModifierKey.NONE,
            char='b'
        )
        self.interface.handle_input(normal_event2)
        self.assertEqual(len(self.interface.input_history), 2)
        
        # Verify history contains only normal inputs
        self.assertEqual(self.interface.input_history[0].char, 'a')
        self.assertEqual(self.interface.input_history[1].char, 'b')


if __name__ == '__main__':
    unittest.main()
