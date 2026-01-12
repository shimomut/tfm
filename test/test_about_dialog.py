#!/usr/bin/env python3
"""
Test suite for AboutDialog component
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_about_dialog import AboutDialog, MatrixColumn
from tfm_config import get_config
from ttk import KeyCode, KeyEvent, CharEvent, SystemEvent, SystemEventType


class TestMatrixColumn(unittest.TestCase):
    """Test MatrixColumn animation component"""
    
    def test_initialization(self):
        """Test MatrixColumn initialization"""
        column = MatrixColumn(x=10, height=24)
        
        self.assertEqual(column.x, 10)
        self.assertEqual(column.height, 24)
        self.assertIsNotNone(column.chars)
        self.assertGreater(len(column.chars), 0)
        self.assertGreater(column.speed, 0)
        self.assertGreater(column.length, 0)
    
    def test_update(self):
        """Test column position update"""
        column = MatrixColumn(x=10, height=24)
        initial_y = column.y
        
        # Update with time delta
        column.update(dt=1.0)
        
        # Y position should have changed
        self.assertNotEqual(column.y, initial_y)
    
    def test_get_visible_chars(self):
        """Test getting visible characters"""
        column = MatrixColumn(x=10, height=24)
        column.y = 10  # Set to visible position
        
        visible = column.get_visible_chars()
        
        # Should return list of tuples
        self.assertIsInstance(visible, list)
        for item in visible:
            self.assertEqual(len(item), 3)  # (y, char, brightness)
            y, char, brightness = item
            self.assertIsInstance(y, int)
            self.assertIsInstance(char, str)
            self.assertIsInstance(brightness, float)
            self.assertGreaterEqual(brightness, 0.0)
            self.assertLessEqual(brightness, 1.0)


class TestAboutDialog(unittest.TestCase):
    """Test AboutDialog functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = get_config()
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (24, 80)
        self.dialog = AboutDialog(self.config, self.renderer)
    
    def test_initialization(self):
        """Test AboutDialog initialization"""
        self.assertIsNotNone(self.dialog)
        self.assertFalse(self.dialog.is_active)
        self.assertEqual(len(self.dialog.matrix_columns), 0)
    
    def test_show(self):
        """Test showing the dialog"""
        self.dialog.show()
        
        self.assertTrue(self.dialog.is_active)
        self.assertTrue(self.dialog.content_changed)
        self.assertGreater(len(self.dialog.matrix_columns), 0)
    
    def test_exit(self):
        """Test exiting the dialog"""
        self.dialog.show()
        self.assertTrue(self.dialog.is_active)
        
        self.dialog.exit()
        
        self.assertFalse(self.dialog.is_active)
        self.assertEqual(len(self.dialog.matrix_columns), 0)
    
    def test_needs_redraw_when_active(self):
        """Test that dialog needs redraw when active"""
        self.dialog.show()
        
        # Should always need redraw when active (for animation)
        self.assertTrue(self.dialog.needs_redraw())
    
    def test_handle_key_event_closes_dialog(self):
        """Test that any key event closes the dialog"""
        self.dialog.show()
        
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=set())
        consumed = self.dialog.handle_key_event(event)
        
        self.assertTrue(consumed)
        self.assertFalse(self.dialog.is_active)
    
    def test_handle_char_event_closes_dialog(self):
        """Test that any character event closes the dialog"""
        self.dialog.show()
        
        event = CharEvent(char='a')
        consumed = self.dialog.handle_char_event(event)
        
        self.assertTrue(consumed)
        self.assertFalse(self.dialog.is_active)
    
    def test_handle_system_event_resize(self):
        """Test handling resize event"""
        self.dialog.show()
        initial_columns = len(self.dialog.matrix_columns)
        
        # Change dimensions
        self.renderer.get_dimensions.return_value = (30, 100)
        
        event = SystemEvent(SystemEventType.RESIZE)
        consumed = self.dialog.handle_system_event(event)
        
        self.assertTrue(consumed)
        self.assertTrue(self.dialog.content_changed)
        # Should have recreated columns for new width
        self.assertGreater(len(self.dialog.matrix_columns), 0)
    
    def test_handle_system_event_close(self):
        """Test handling close event"""
        self.dialog.show()
        
        event = SystemEvent(SystemEventType.CLOSE)
        consumed = self.dialog.handle_system_event(event)
        
        self.assertTrue(consumed)
        self.assertFalse(self.dialog.is_active)
    
    def test_handle_mouse_event_closes_dialog(self):
        """Test that mouse button down closes the dialog"""
        from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton
        
        self.dialog.show()
        
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=10,
            row=10,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT
        )
        consumed = self.dialog.handle_mouse_event(event)
        
        self.assertTrue(consumed)
        self.assertFalse(self.dialog.is_active)
    
    def test_is_full_screen(self):
        """Test that dialog reports as full screen"""
        self.assertTrue(self.dialog.is_full_screen())
    
    def test_should_close(self):
        """Test should_close returns correct state"""
        self.dialog.show()
        self.assertFalse(self.dialog.should_close())
        
        self.dialog.exit()
        self.assertTrue(self.dialog.should_close())
    
    def test_mark_dirty(self):
        """Test marking dialog as dirty"""
        self.dialog.content_changed = False
        self.dialog.mark_dirty()
        self.assertTrue(self.dialog.content_changed)
    
    def test_clear_dirty(self):
        """Test clearing dirty flag"""
        self.dialog.content_changed = True
        self.dialog.clear_dirty()
        self.assertFalse(self.dialog.content_changed)
    
    def test_on_activate(self):
        """Test on_activate callback"""
        self.dialog.content_changed = False
        self.dialog.on_activate()
        self.assertTrue(self.dialog.content_changed)
    
    def test_draw_creates_matrix_effect(self):
        """Test that draw method creates Matrix animation"""
        self.dialog.show()
        
        # Mock renderer methods
        self.renderer.draw_text = Mock()
        self.renderer.draw_hline = Mock()
        
        # Draw the dialog
        self.dialog.draw()
        
        # Should have called draw methods
        self.assertTrue(self.renderer.draw_text.called)
        
        # Content should be marked as not changed after draw
        self.assertFalse(self.dialog.content_changed)
    
    def test_matrix_animation_updates(self):
        """Test that Matrix columns update over time"""
        self.dialog.show()
        
        # Get initial positions
        initial_positions = [col.y for col in self.dialog.matrix_columns]
        
        # Update animation
        for col in self.dialog.matrix_columns:
            col.update(dt=1.0)
        
        # Positions should have changed
        new_positions = [col.y for col in self.dialog.matrix_columns]
        self.assertNotEqual(initial_positions, new_positions)


class TestAboutDialogIntegration(unittest.TestCase):
    """Integration tests for AboutDialog"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = get_config()
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (24, 80)
        self.dialog = AboutDialog(self.config, self.renderer)
    
    def test_full_lifecycle(self):
        """Test complete dialog lifecycle"""
        # Start inactive
        self.assertFalse(self.dialog.is_active)
        
        # Show dialog
        self.dialog.show()
        self.assertTrue(self.dialog.is_active)
        self.assertGreater(len(self.dialog.matrix_columns), 0)
        
        # Simulate some animation frames
        for _ in range(5):
            for col in self.dialog.matrix_columns:
                col.update(dt=0.1)
        
        # Close dialog
        event = KeyEvent(key_code=KeyCode.ENTER, modifiers=set())
        self.dialog.handle_key_event(event)
        
        self.assertFalse(self.dialog.is_active)
        self.assertEqual(len(self.dialog.matrix_columns), 0)
    
    def test_resize_during_display(self):
        """Test resizing while dialog is displayed"""
        self.dialog.show()
        initial_width = 80
        
        # Resize to wider screen
        self.renderer.get_dimensions.return_value = (24, 120)
        event = SystemEvent(SystemEventType.RESIZE)
        self.dialog.handle_system_event(event)
        
        # Should have more columns for wider screen
        self.assertGreater(len(self.dialog.matrix_columns), 0)


if __name__ == '__main__':
    unittest.main()
