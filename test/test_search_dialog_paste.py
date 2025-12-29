"""
Tests for SearchDialog clipboard paste functionality
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from ttk import KeyEvent, ModifierKey
from tfm_search_dialog import SearchDialog


class TestSearchDialogPaste(unittest.TestCase):
    """Test clipboard paste functionality in SearchDialog"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock config
        self.mock_config = Mock()
        self.mock_config.MAX_SEARCH_RESULTS = 10000
        
        # Create mock renderer with clipboard support
        self.mock_renderer = Mock()
        self.mock_renderer.supports_clipboard.return_value = True
        self.mock_renderer.get_clipboard_text.return_value = "test search"
        
    def test_paste_in_search_dialog(self):
        """Test that paste works in SearchDialog text input"""
        dialog = SearchDialog(self.mock_config, self.mock_renderer)
        
        # Verify text_editor has renderer
        self.assertIsNotNone(dialog.text_editor.renderer)
        self.assertEqual(dialog.text_editor.renderer, self.mock_renderer)
        
        # Create Cmd+V event
        event = Mock(spec=KeyEvent)
        event.char = 'v'
        event.key_code = None
        event.modifiers = ModifierKey.COMMAND
        event.has_modifier = Mock(side_effect=lambda m: m == ModifierKey.COMMAND)
        
        # Paste should work
        result = dialog.text_editor.handle_key(event)
        
        self.assertTrue(result)
        self.assertEqual(dialog.text_editor.get_text(), "test search")
    
    def test_paste_through_handle_key_event(self):
        """Test that Cmd+V is passed through handle_key_event to text editor"""
        dialog = SearchDialog(self.mock_config, self.mock_renderer)
        dialog.show('filename', search_root=Mock())
        
        # Create Cmd+V event
        event = Mock(spec=KeyEvent)
        event.char = 'v'
        event.key_code = None
        event.modifiers = ModifierKey.COMMAND
        event.has_modifier = Mock(side_effect=lambda m: m == ModifierKey.COMMAND)
        
        # Mock perform_search to avoid actual search
        dialog.perform_search = Mock()
        
        # Handle the event through the dialog
        result = dialog.handle_key_event(event)
        
        # Should be handled and text should be pasted
        self.assertTrue(result)
        self.assertEqual(dialog.text_editor.get_text(), "test search")
        # Search should be triggered since text changed
        self.assertTrue(dialog.perform_search.called)


if __name__ == '__main__':
    unittest.main()
