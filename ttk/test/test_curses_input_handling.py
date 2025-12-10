"""
Unit tests for TTK CursesBackend input handling.

This module tests the input handling functionality of the CursesBackend,
including timeout support, key translation, special keys, and printable characters.
"""

import curses
import unittest
from unittest.mock import Mock, patch, MagicMock

from ttk.backends.curses_backend import CursesBackend
from ttk.input_event import InputEvent, KeyCode, ModifierKey


class TestCursesInputHandling(unittest.TestCase):
    """Test cases for CursesBackend input handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = CursesBackend()
        # Mock the stdscr to avoid actual curses initialization
        self.backend.stdscr = Mock()
    
    def test_get_input_blocking(self):
        """Test get_input with blocking mode (timeout=-1)."""
        # Mock getch to return a key code
        self.backend.stdscr.getch.return_value = ord('a')
        
        event = self.backend.get_input(timeout_ms=-1)
        
        # Verify timeout was set correctly
        self.backend.stdscr.timeout.assert_called_once_with(-1)
        
        # Verify event is correct
        self.assertIsNotNone(event)
        self.assertEqual(event.key_code, ord('a'))
        self.assertEqual(event.char, 'a')
    
    def test_get_input_non_blocking(self):
        """Test get_input with non-blocking mode (timeout=0)."""
        # Mock getch to return -1 (no input available)
        self.backend.stdscr.getch.return_value = -1
        
        event = self.backend.get_input(timeout_ms=0)
        
        # Verify timeout was set correctly
        self.backend.stdscr.timeout.assert_called_once_with(0)
        
        # Verify no event returned
        self.assertIsNone(event)
    
    def test_get_input_with_timeout(self):
        """Test get_input with specific timeout value."""
        # Mock getch to return a key code
        self.backend.stdscr.getch.return_value = ord('b')
        
        event = self.backend.get_input(timeout_ms=100)
        
        # Verify timeout was set correctly
        self.backend.stdscr.timeout.assert_called_once_with(100)
        
        # Verify event is correct
        self.assertIsNotNone(event)
        self.assertEqual(event.key_code, ord('b'))
    
    def test_get_input_curses_error(self):
        """Test get_input handles curses.error gracefully."""
        # Mock getch to raise curses.error
        self.backend.stdscr.getch.side_effect = curses.error
        
        event = self.backend.get_input()
        
        # Verify None is returned on error
        self.assertIsNone(event)
    
    def test_translate_printable_characters(self):
        """Test translation of printable ASCII characters."""
        # Test lowercase letters
        for char_code in range(ord('a'), ord('z') + 1):
            event = self.backend._translate_curses_key(char_code)
            self.assertEqual(event.key_code, char_code)
            self.assertEqual(event.char, chr(char_code))
            self.assertEqual(event.modifiers, ModifierKey.NONE)
        
        # Test uppercase letters
        for char_code in range(ord('A'), ord('Z') + 1):
            event = self.backend._translate_curses_key(char_code)
            self.assertEqual(event.key_code, char_code)
            self.assertEqual(event.char, chr(char_code))
        
        # Test digits
        for char_code in range(ord('0'), ord('9') + 1):
            event = self.backend._translate_curses_key(char_code)
            self.assertEqual(event.key_code, char_code)
            self.assertEqual(event.char, chr(char_code))
        
        # Test space
        event = self.backend._translate_curses_key(32)
        self.assertEqual(event.key_code, 32)
        self.assertEqual(event.char, ' ')
        
        # Test special printable characters
        for char in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`':
            char_code = ord(char)
            event = self.backend._translate_curses_key(char_code)
            self.assertEqual(event.key_code, char_code)
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
        event = self.backend._translate_curses_key(curses.KEY_RESIZE)
        self.assertEqual(event.key_code, KeyCode.RESIZE)
        self.assertIsNone(event.char)
    
    def test_translate_unknown_key(self):
        """Test translation of unknown key codes."""
        # Test with an arbitrary key code that's not mapped
        unknown_key = 999
        event = self.backend._translate_curses_key(unknown_key)
        
        # Should return an event with the key code as-is
        self.assertEqual(event.key_code, unknown_key)
        self.assertIsNone(event.char)
        self.assertEqual(event.modifiers, ModifierKey.NONE)
    
    def test_get_input_integration(self):
        """Test get_input with various key types."""
        test_cases = [
            (ord('x'), ord('x'), 'x'),  # Printable character
            (curses.KEY_UP, KeyCode.UP, None),  # Arrow key
            (curses.KEY_F5, KeyCode.F5, None),  # Function key
            (10, KeyCode.ENTER, None),  # Enter
            (27, KeyCode.ESCAPE, None),  # Escape
        ]
        
        for curses_key, expected_keycode, expected_char in test_cases:
            self.backend.stdscr.getch.return_value = curses_key
            
            event = self.backend.get_input()
            
            self.assertIsNotNone(event)
            self.assertEqual(event.key_code, expected_keycode)
            self.assertEqual(event.char, expected_char)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
