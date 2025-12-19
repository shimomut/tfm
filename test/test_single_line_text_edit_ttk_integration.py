#!/usr/bin/env python3
"""
Test SingleLineTextEdit TTK integration

This test verifies that SingleLineTextEdit has been successfully migrated
to use TTK's Renderer API instead of curses.
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_single_line_text_edit import SingleLineTextEdit
from ttk import KeyEvent, KeyCode, TextAttribute
from ttk.input_event import CharEvent


class TestSingleLineTextEditTTKIntegration(unittest.TestCase):
    """Test SingleLineTextEdit TTK integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (24, 80)
        self.editor = SingleLineTextEdit()
    
    def test_basic_text_operations(self):
        """Test basic text operations work without curses"""
        # Test initialization
        self.assertEqual(self.editor.get_text(), "")
        self.assertEqual(self.editor.get_cursor_pos(), 0)
        
        # Test set_text
        self.editor.set_text("Hello")
        self.assertEqual(self.editor.get_text(), "Hello")
        
        # Test cursor positioning
        self.editor.set_cursor_pos(3)
        self.assertEqual(self.editor.get_cursor_pos(), 3)
        
        # Test clear
        self.editor.clear()
        self.assertEqual(self.editor.get_text(), "")
        self.assertEqual(self.editor.get_cursor_pos(), 0)
    
    def test_cursor_movement(self):
        """Test cursor movement operations"""
        self.editor.set_text("Hello World")
        self.editor.set_cursor_pos(0)
        
        # Test move right
        self.assertTrue(self.editor.move_cursor_right())
        self.assertEqual(self.editor.get_cursor_pos(), 1)
        
        # Test move left
        self.assertTrue(self.editor.move_cursor_left())
        self.assertEqual(self.editor.get_cursor_pos(), 0)
        
        # Test move home
        self.editor.set_cursor_pos(5)
        self.assertTrue(self.editor.move_cursor_home())
        self.assertEqual(self.editor.get_cursor_pos(), 0)
        
        # Test move end
        self.assertTrue(self.editor.move_cursor_end())
        self.assertEqual(self.editor.get_cursor_pos(), 11)
    
    def test_text_editing(self):
        """Test text editing operations"""
        self.editor.set_text("Hello")
        self.editor.set_cursor_pos(5)
        
        # Test insert
        self.assertTrue(self.editor.insert_char(" "))
        self.assertEqual(self.editor.get_text(), "Hello ")
        
        # Test backspace
        self.assertTrue(self.editor.backspace())
        self.assertEqual(self.editor.get_text(), "Hello")
        
        # Test delete
        self.editor.set_cursor_pos(0)
        self.assertTrue(self.editor.delete_char_at_cursor())
        self.assertEqual(self.editor.get_text(), "ello")
    
    def test_handle_key_with_input_event(self):
        """Test handle_key uses KeyEvent instead of curses key codes"""
        self.editor.set_text("Test")
        self.editor.set_cursor_pos(4)
        
        # Test LEFT arrow
        event = KeyEvent(key_code=KeyCode.LEFT, modifiers=0)
        self.assertTrue(self.editor.handle_key(event))
        self.assertEqual(self.editor.get_cursor_pos(), 3)
        
        # Test RIGHT arrow
        event = KeyEvent(key_code=KeyCode.RIGHT, modifiers=0)
        self.assertTrue(self.editor.handle_key(event))
        self.assertEqual(self.editor.get_cursor_pos(), 4)
        
        # Test HOME
        event = KeyEvent(key_code=KeyCode.HOME, modifiers=0)
        self.assertTrue(self.editor.handle_key(event))
        self.assertEqual(self.editor.get_cursor_pos(), 0)
        
        # Test END
        event = KeyEvent(key_code=KeyCode.END, modifiers=0)
        self.assertTrue(self.editor.handle_key(event))
        self.assertEqual(self.editor.get_cursor_pos(), 4)
        
        # Test BACKSPACE
        event = KeyEvent(key_code=KeyCode.BACKSPACE, modifiers=0)
        self.assertTrue(self.editor.handle_key(event))
        self.assertEqual(self.editor.get_text(), "Tes")
        
        # Test DELETE
        self.editor.set_cursor_pos(0)
        event = KeyEvent(key_code=KeyCode.DELETE, modifiers=0)
        self.assertTrue(self.editor.handle_key(event))
        self.assertEqual(self.editor.get_text(), "es")
        
        # Test printable character using CharEvent
        event = CharEvent(char='X')
        self.assertTrue(self.editor.handle_key(event))
        self.assertEqual(self.editor.get_text(), "Xes")
    
    def test_handle_key_vertical_nav(self):
        """Test handle_key with vertical navigation enabled"""
        self.editor.set_text("Test")
        self.editor.set_cursor_pos(2)
        
        # Test UP arrow moves to home when vertical nav enabled
        event = KeyEvent(key_code=KeyCode.UP, modifiers=0)
        self.assertTrue(self.editor.handle_key(event, handle_vertical_nav=True))
        self.assertEqual(self.editor.get_cursor_pos(), 0)
        
        # Test DOWN arrow moves to end when vertical nav enabled
        event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0)
        self.assertTrue(self.editor.handle_key(event, handle_vertical_nav=True))
        self.assertEqual(self.editor.get_cursor_pos(), 4)
        
        # Test UP/DOWN don't work when vertical nav disabled
        self.editor.set_cursor_pos(2)
        event = KeyEvent(key_code=KeyCode.UP, modifiers=0)
        self.assertFalse(self.editor.handle_key(event, handle_vertical_nav=False))
        self.assertEqual(self.editor.get_cursor_pos(), 2)
    
    def test_draw_uses_renderer(self):
        """Test that draw() uses renderer instead of stdscr"""
        self.editor.set_text("Hello")
        
        # Draw should use renderer.draw_text, not stdscr.addstr
        self.editor.draw(self.renderer, 0, 0, 80, label="Test: ")
        
        # Verify renderer methods were called
        self.assertTrue(self.renderer.get_dimensions.called)
        self.assertTrue(self.renderer.draw_text.called)
        
        # Verify no stdscr parameter is needed
        # (This would fail if draw still expected stdscr)
    
    def test_draw_with_empty_text(self):
        """Test drawing with empty text"""
        self.editor.clear()
        
        # Should draw cursor at beginning when active
        self.editor.draw(self.renderer, 0, 0, 80, label="Input: ", is_active=True)
        
        # Verify renderer was called
        self.assertTrue(self.renderer.draw_text.called)
        
        # Check that cursor space was drawn (reversed attributes)
        calls = self.renderer.draw_text.call_args_list
        # Check if any call has attributes parameter with REVERSE flag
        has_reverse = False
        for call in calls:
            # call is a tuple of (args, kwargs)
            if len(call) > 1 and 'attributes' in call[1]:
                attrs = call[1]['attributes']
                if attrs & TextAttribute.REVERSE:
                    has_reverse = True
                    break
        self.assertTrue(has_reverse, "Should draw cursor with REVERSE attribute")
    
    def test_draw_with_cursor_highlighting(self):
        """Test that cursor is highlighted correctly"""
        self.editor.set_text("Test")
        self.editor.set_cursor_pos(2)
        
        # Draw with cursor active
        self.editor.draw(self.renderer, 0, 0, 80, label="", is_active=True)
        
        # Verify renderer was called multiple times (once per character)
        self.assertTrue(self.renderer.draw_text.call_count >= 4)
        
        # Check that at least one call has REVERSE attribute (cursor)
        calls = self.renderer.draw_text.call_args_list
        # Check if any call has attributes parameter with REVERSE flag
        has_reverse = False
        for call in calls:
            # call is a tuple of (args, kwargs)
            if len(call) > 1 and 'attributes' in call[1]:
                attrs = call[1]['attributes']
                if attrs & TextAttribute.REVERSE:
                    has_reverse = True
                    break
        self.assertTrue(has_reverse, "Should highlight cursor character")
    
    def test_draw_without_cursor(self):
        """Test drawing without cursor (inactive)"""
        self.editor.set_text("Test")
        self.editor.set_cursor_pos(2)
        
        # Draw with cursor inactive
        self.renderer.reset_mock()
        self.editor.draw(self.renderer, 0, 0, 80, label="", is_active=False)
        
        # Verify renderer was called
        self.assertTrue(self.renderer.draw_text.called)
        
        # When inactive, should not use REVERSE attribute
        calls = self.renderer.draw_text.call_args_list
        # Check if any call has attributes parameter with REVERSE flag
        has_reverse = False
        for call in calls:
            # call is a tuple of (args, kwargs)
            if len(call) > 1 and 'attributes' in call[1]:
                attrs = call[1]['attributes']
                if attrs & TextAttribute.REVERSE:
                    has_reverse = True
                    break
        self.assertFalse(has_reverse, "Should not highlight cursor when inactive")
    
    def test_draw_with_label(self):
        """Test drawing with label"""
        self.editor.set_text("Value")
        
        # Draw with label
        self.editor.draw(self.renderer, 5, 10, 80, label="Name: ", is_active=True)
        
        # Verify renderer was called
        self.assertTrue(self.renderer.draw_text.called)
        
        # Check that label was drawn
        calls = self.renderer.draw_text.call_args_list
        label_drawn = any(
            "Name: " in str(call)
            for call in calls
        )
        self.assertTrue(label_drawn, "Should draw label")
    
    def test_max_length_constraint(self):
        """Test maximum length constraint"""
        editor = SingleLineTextEdit("", max_length=5)
        
        # Should allow up to max_length using CharEvent
        for char in "Hello":
            event = CharEvent(char=char)
            self.assertTrue(editor.handle_key(event))
        
        self.assertEqual(editor.get_text(), "Hello")
        
        # Should reject beyond max_length
        event = CharEvent(char='!')
        self.assertFalse(editor.handle_key(event))
        self.assertEqual(editor.get_text(), "Hello")
    
    def test_wide_character_support(self):
        """Test wide character support"""
        # Test with wide characters (e.g., Japanese)
        self.editor.set_text("こんにちは")
        self.assertEqual(self.editor.get_text(), "こんにちは")
        
        # Test cursor movement with wide characters
        self.editor.set_cursor_pos(0)
        self.assertTrue(self.editor.move_cursor_right())
        self.assertEqual(self.editor.get_cursor_pos(), 1)
        
        # Test drawing with wide characters
        self.editor.draw(self.renderer, 0, 0, 80, label="", is_active=True)
        self.assertTrue(self.renderer.draw_text.called)
    
    def test_no_curses_imports(self):
        """Test that SingleLineTextEdit doesn't import curses"""
        import tfm_single_line_text_edit
        
        # Check module source for curses imports
        source = open(tfm_single_line_text_edit.__file__).read()
        
        # Should not have "import curses" or "from curses"
        self.assertNotIn("import curses", source, 
                        "Should not import curses directly")
        self.assertNotIn("from curses", source,
                        "Should not import from curses")


if __name__ == '__main__':
    unittest.main()
