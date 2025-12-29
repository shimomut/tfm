"""
Tests for SingleLineTextEdit clipboard paste functionality
"""

import unittest
from unittest.mock import Mock, MagicMock
from ttk import KeyEvent, KeyCode, ModifierKey
from tfm_single_line_text_edit import SingleLineTextEdit


class TestSingleLineTextEditPaste(unittest.TestCase):
    """Test clipboard paste functionality in SingleLineTextEdit"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer with clipboard support
        self.mock_renderer = Mock()
        self.mock_renderer.supports_clipboard.return_value = True
        self.mock_renderer.get_clipboard_text.return_value = "pasted text"
    
    def _create_paste_event(self):
        """Create a mock Cmd+V / Ctrl+V KeyEvent"""
        from ttk import ModifierKey
        event = Mock(spec=KeyEvent)
        event.char = 'v'
        event.key_code = None
        event.modifiers = ModifierKey.COMMAND
        return event
        
    def test_paste_simple_text(self):
        """Test pasting simple text at cursor position"""
        editor = SingleLineTextEdit("hello ", renderer=self.mock_renderer)
        editor.set_cursor_pos(6)  # After "hello "
        
        # Create Cmd+V event
        event = self._create_paste_event()
        
        # Paste
        result = editor.handle_key(event)
        
        self.assertTrue(result)
        self.assertEqual(editor.get_text(), "hello pasted text")
        self.assertEqual(editor.get_cursor_pos(), 17)  # After pasted text
    
    def test_paste_at_beginning(self):
        """Test pasting at the beginning of text"""
        editor = SingleLineTextEdit("world", renderer=self.mock_renderer)
        editor.set_cursor_pos(0)
        
        event = self._create_paste_event()
        
        result = editor.handle_key(event)
        
        self.assertTrue(result)
        self.assertEqual(editor.get_text(), "pasted textworld")
        self.assertEqual(editor.get_cursor_pos(), 11)
    
    def test_paste_in_middle(self):
        """Test pasting in the middle of text"""
        editor = SingleLineTextEdit("helloworld", renderer=self.mock_renderer)
        editor.set_cursor_pos(5)  # Between "hello" and "world"
        
        event = self._create_paste_event()
        
        result = editor.handle_key(event)
        
        self.assertTrue(result)
        self.assertEqual(editor.get_text(), "hellopasted textworld")
        self.assertEqual(editor.get_cursor_pos(), 16)
    
    def test_paste_multiline_text_converts_to_single_line(self):
        """Test that multiline clipboard text is converted to single line"""
        self.mock_renderer.get_clipboard_text.return_value = "line1\nline2\nline3"
        
        editor = SingleLineTextEdit("", renderer=self.mock_renderer)
        
        event = self._create_paste_event()
        
        result = editor.handle_key(event)
        
        self.assertTrue(result)
        # Newlines should be replaced with spaces
        self.assertEqual(editor.get_text(), "line1 line2 line3")
    
    def test_paste_respects_max_length(self):
        """Test that paste respects max_length constraint"""
        self.mock_renderer.get_clipboard_text.return_value = "very long pasted text"
        
        editor = SingleLineTextEdit("hello", max_length=15, renderer=self.mock_renderer)
        editor.set_cursor_pos(5)
        
        event = self._create_paste_event()
        
        result = editor.handle_key(event)
        
        self.assertTrue(result)
        # Should only paste what fits (15 - 5 = 10 chars available)
        self.assertEqual(len(editor.get_text()), 15)
        self.assertEqual(editor.get_text(), "hellovery long ")
    
    def test_paste_empty_clipboard(self):
        """Test pasting when clipboard is empty"""
        self.mock_renderer.get_clipboard_text.return_value = ""
        
        editor = SingleLineTextEdit("hello", renderer=self.mock_renderer)
        
        event = self._create_paste_event()
        
        result = editor.handle_key(event)
        
        self.assertFalse(result)
        self.assertEqual(editor.get_text(), "hello")  # Unchanged
    
    def test_paste_no_renderer(self):
        """Test paste fails gracefully when no renderer provided"""
        editor = SingleLineTextEdit("hello")  # No renderer
        
        event = self._create_paste_event()
        
        result = editor.handle_key(event)
        
        self.assertFalse(result)
        self.assertEqual(editor.get_text(), "hello")  # Unchanged
    
    def test_paste_no_clipboard_support(self):
        """Test paste fails gracefully when clipboard not supported"""
        self.mock_renderer.supports_clipboard.return_value = False
        
        editor = SingleLineTextEdit("hello", renderer=self.mock_renderer)
        
        event = self._create_paste_event()
        
        result = editor.handle_key(event)
        
        self.assertFalse(result)
        self.assertEqual(editor.get_text(), "hello")  # Unchanged
    
    def test_paste_at_max_length(self):
        """Test paste fails when already at max length"""
        self.mock_renderer.get_clipboard_text.return_value = "more text"
        
        editor = SingleLineTextEdit("hello", max_length=5, renderer=self.mock_renderer)
        
        event = self._create_paste_event()
        
        result = editor.handle_key(event)
        
        self.assertFalse(result)
        self.assertEqual(editor.get_text(), "hello")  # Unchanged
    
    def test_paste_with_carriage_returns(self):
        """Test that carriage returns are also converted to spaces"""
        self.mock_renderer.get_clipboard_text.return_value = "line1\r\nline2\rline3"
        
        editor = SingleLineTextEdit("", renderer=self.mock_renderer)
        
        event = self._create_paste_event()
        
        result = editor.handle_key(event)
        
        self.assertTrue(result)
        # Both \r and \n should be replaced with spaces
        self.assertEqual(editor.get_text(), "line1  line2 line3")
    
    def test_paste_without_modifier_key(self):
        """Test that 'v' without modifier key doesn't trigger paste"""
        editor = SingleLineTextEdit("hello", renderer=self.mock_renderer)
        
        # Regular 'v' key without modifier
        event = Mock(spec=KeyEvent)
        event.char = 'v'
        event.modifiers = ModifierKey.NONE
        event.key_code = None
        
        result = editor.handle_key(event)
        
        # Should not paste (returns False because KeyEvent with char but no modifier
        # is not handled by handle_key - it would be a CharEvent instead)
        self.assertFalse(result)
        self.assertEqual(editor.get_text(), "hello")


if __name__ == '__main__':
    unittest.main()
