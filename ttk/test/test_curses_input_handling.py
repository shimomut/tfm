"""
Unit tests for TTK CursesBackend input handling.

This module tests the input handling functionality of the CursesBackend,
including callback mode, key translation, special keys, and printable characters.
"""

import curses
import unittest
from unittest.mock import Mock, patch, MagicMock

from ttk.backends.curses_backend import CursesBackend
from ttk import KeyEvent, KeyCode, ModifierKey
from ttk.test.test_utils import EventCapture


class TestCursesInputHandling(unittest.TestCase):
    """Test cases for CursesBackend input handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = CursesBackend()
        # Mock the stdscr to avoid actual curses initialization
        self.backend.stdscr = Mock()
        
        # Set up event capture
        self.capture = EventCapture()
        self.backend.set_event_callback(self.capture)
    
    def test_callback_mode_required(self):
        """Test that callback must be set before processing events."""
        backend = CursesBackend()
        backend.stdscr = Mock()
        
        # Should raise error if callback not set
        with self.assertRaises(RuntimeError):
            backend.run_event_loop_iteration(timeout_ms=0)
    
    def test_event_delivered_via_callback(self):
        """Test that events are delivered via callback."""
        # Mock getch to return a key code
        self.backend.stdscr.getch.return_value = ord('a')
        
        # Process event
        self.backend.run_event_loop_iteration(timeout_ms=0)
        
        # Verify event was delivered via callback
        self.assertTrue(len(self.capture.events) > 0)
        event_type, event = self.capture.events[0]
        self.assertEqual(event_type, 'key')
        self.assertEqual(event.key_code, KeyCode.KEY_A)
        self.assertEqual(event.char, 'a')
    
    def test_translate_printable_characters(self):
        """Test translation of printable ASCII characters."""
        # Test lowercase letters - now map to KEY_A through KEY_Z
        for char_code in range(ord('a'), ord('z') + 1):
            event = self.backend._translate_curses_key(char_code)
            expected_keycode = KeyCode.KEY_A + (char_code - ord('a'))
            self.assertEqual(event.key_code, expected_keycode)
            self.assertEqual(event.char, chr(char_code))
            self.assertEqual(event.modifiers, ModifierKey.NONE)
        
        # Test uppercase letters - also map to KEY_A through KEY_Z with SHIFT
        for char_code in range(ord('A'), ord('Z') + 1):
            event = self.backend._translate_curses_key(char_code)
            expected_keycode = KeyCode.KEY_A + (char_code - ord('A'))
            self.assertEqual(event.key_code, expected_keycode)
            self.assertEqual(event.char, chr(char_code))
            self.assertEqual(event.modifiers, ModifierKey.SHIFT)
        
        # Test digits - now map to KEY_0 through KEY_9
        for char_code in range(ord('0'), ord('9') + 1):
            event = self.backend._translate_curses_key(char_code)
            expected_keycode = KeyCode.KEY_0 + (char_code - ord('0'))
            self.assertEqual(event.key_code, expected_keycode)
            self.assertEqual(event.char, chr(char_code))
        
        # Test space - now maps to KeyCode.SPACE
        event = self.backend._translate_curses_key(32)
        self.assertEqual(event.key_code, KeyCode.SPACE)
        self.assertEqual(event.char, ' ')
        
        # Test special printable characters - map to their respective KEY_* values
        symbol_tests = [
            ('-', KeyCode.KEY_MINUS),
            ('=', KeyCode.KEY_EQUAL),
            ('[', KeyCode.KEY_LEFT_BRACKET),
            (']', KeyCode.KEY_RIGHT_BRACKET),
            ('\\', KeyCode.KEY_BACKSLASH),
            (';', KeyCode.KEY_SEMICOLON),
            ("'", KeyCode.KEY_QUOTE),
            (',', KeyCode.KEY_COMMA),
            ('.', KeyCode.KEY_PERIOD),
            ('/', KeyCode.KEY_SLASH),
            ('`', KeyCode.KEY_GRAVE),
        ]
        for char, expected_keycode in symbol_tests:
            char_code = ord(char)
            event = self.backend._translate_curses_key(char_code)
            self.assertEqual(event.key_code, expected_keycode)
            self.assertEqual(event.char, char)
    
    def test_translate_arrow_keys(self):
        """Test translation of arrow keys."""
        arrow_keys = [
            (curses.KEY_UP, KeyCode.UP),
            (curses.KEY_DOWN, KeyCode.DOWN),
            (curses.KEY_LEFT, KeyCode.LEFT),
            (curses.KEY_RIGHT, KeyCode.RIGHT),
        ]
        
        for curses_key, expected_keycode in arrow_keys:
            event = self.backend._translate_curses_key(curses_key)
            self.assertEqual(event.key_code, expected_keycode)
            self.assertIsNone(event.char)
            self.assertEqual(event.modifiers, ModifierKey.NONE)
    
    def test_translate_function_keys(self):
        """Test translation of function keys F1-F12."""
        for i in range(12):
            curses_key = curses.KEY_F1 + i
            expected_keycode = KeyCode.F1 + i
            
            event = self.backend._translate_curses_key(curses_key)
            self.assertEqual(event.key_code, expected_keycode)
            self.assertIsNone(event.char)
            self.assertEqual(event.modifiers, ModifierKey.NONE)
    
    def test_translate_navigation_keys(self):
        """Test translation of navigation keys."""
        nav_keys = [
            (curses.KEY_HOME, KeyCode.HOME),
            (curses.KEY_END, KeyCode.END),
            (curses.KEY_PPAGE, KeyCode.PAGE_UP),
            (curses.KEY_NPAGE, KeyCode.PAGE_DOWN),
        ]
        
        for curses_key, expected_keycode in nav_keys:
            event = self.backend._translate_curses_key(curses_key)
            self.assertEqual(event.key_code, expected_keycode)
            self.assertIsNone(event.char)
    
    def test_translate_editing_keys(self):
        """Test translation of editing keys."""
        edit_keys = [
            (curses.KEY_DC, KeyCode.DELETE),
            (curses.KEY_IC, KeyCode.INSERT),
            (curses.KEY_BACKSPACE, KeyCode.BACKSPACE),
        ]
        
        for curses_key, expected_keycode in edit_keys:
            event = self.backend._translate_curses_key(curses_key)
            self.assertEqual(event.key_code, expected_keycode)
            self.assertIsNone(event.char)
    
    def test_translate_special_characters(self):
        """Test translation of special control characters."""
        # Enter (both line feed and carriage return)
        event = self.backend._translate_curses_key(10)
        self.assertEqual(event.key_code, KeyCode.ENTER)
        
        event = self.backend._translate_curses_key(13)
        self.assertEqual(event.key_code, KeyCode.ENTER)
        
        # Escape
        event = self.backend._translate_curses_key(27)
        self.assertEqual(event.key_code, KeyCode.ESCAPE)
        
        # Tab
        event = self.backend._translate_curses_key(9)
        self.assertEqual(event.key_code, KeyCode.TAB)
        
        # Backspace (ASCII 127)
        event = self.backend._translate_curses_key(127)
        self.assertEqual(event.key_code, KeyCode.BACKSPACE)
    
    def test_translate_resize_event(self):
        """Test translation of window resize event."""
        from ttk import SystemEvent, SystemEventType
        event = self.backend._translate_curses_key(curses.KEY_RESIZE)
        # Resize events are SystemEvents, not KeyEvents
        self.assertIsInstance(event, SystemEvent)
        self.assertEqual(event.event_type, SystemEventType.RESIZE)
    
    def test_translate_unknown_key(self):
        """Test translation of unknown key codes."""
        # Test with an arbitrary key code that's not mapped
        unknown_key = 999
        event = self.backend._translate_curses_key(unknown_key)
        
        # Should return an event with the key code as-is
        self.assertEqual(event.key_code, unknown_key)
        self.assertIsNone(event.char)
        self.assertEqual(event.modifiers, ModifierKey.NONE)
    
    def test_callback_integration(self):
        """Test event delivery via callback with various key types."""
        test_cases = [
            (ord('x'), KeyCode.KEY_X, 'x'),  # Printable character - now maps to KEY_X
            (curses.KEY_UP, KeyCode.UP, None),  # Arrow key
            (curses.KEY_F5, KeyCode.F5, None),  # Function key
            (10, KeyCode.ENTER, None),  # Enter
            (27, KeyCode.ESCAPE, None),  # Escape
        ]
        
        for curses_key, expected_keycode, expected_char in test_cases:
            self.backend.stdscr.getch.return_value = curses_key
            self.capture.clear_events()
            
            self.backend.run_event_loop_iteration(timeout_ms=0)
            
            self.assertTrue(len(self.capture.events) > 0)
            event_type, event = self.capture.events[0]
            self.assertEqual(event_type, 'key')
            self.assertEqual(event.key_code, expected_keycode)
            self.assertEqual(event.char, expected_char)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
