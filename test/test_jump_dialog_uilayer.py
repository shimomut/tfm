#!/usr/bin/env python3
"""
Test JumpDialog UILayer interface implementation
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ttk import KeyEvent, CharEvent, KeyCode
from tfm_jump_dialog import JumpDialog
from tfm_ui_layer import UILayer
from tfm_path import Path as TFMPath


class TestJumpDialogUILayer(unittest.TestCase):
    """Test JumpDialog UILayer interface implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.config.MAX_JUMP_DIRECTORIES = 5000
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (40, 120)
        
        self.dialog = JumpDialog(self.config, self.renderer)
    
    def test_jump_dialog_inherits_from_uilayer(self):
        """Test that JumpDialog inherits from UILayer"""
        self.assertIsInstance(self.dialog, UILayer)
    
    def test_handle_key_event_returns_bool(self):
        """Test that handle_key_event returns a boolean"""
        event = KeyEvent(key_code=KeyCode.ESCAPE, char='', modifiers=0)
        result = self.dialog.handle_key_event(event)
        self.assertIsInstance(result, bool)
    
    def test_handle_char_event_returns_bool(self):
        """Test that handle_char_event returns a boolean"""
        event = CharEvent(char='a')
        result = self.dialog.handle_char_event(event)
        self.assertIsInstance(result, bool)
    
    def test_render_calls_draw(self):
        """Test that render calls the draw method"""
        with patch.object(self.dialog, 'draw') as mock_draw:
            self.dialog.render(self.renderer)
            mock_draw.assert_called_once()
    
    def test_is_full_screen_returns_false(self):
        """Test that is_full_screen returns False for dialogs"""
        self.assertFalse(self.dialog.is_full_screen())
    
    def test_needs_redraw_returns_bool(self):
        """Test that needs_redraw returns a boolean"""
        result = self.dialog.needs_redraw()
        self.assertIsInstance(result, bool)
    
    def test_mark_dirty_sets_content_changed(self):
        """Test that mark_dirty sets content_changed flag"""
        self.dialog.content_changed = False
        self.dialog.mark_dirty()
        self.assertTrue(self.dialog.content_changed)
    
    def test_clear_dirty_clears_content_changed(self):
        """Test that clear_dirty clears content_changed flag"""
        self.dialog.content_changed = True
        self.dialog.clear_dirty()
        self.assertFalse(self.dialog.content_changed)
    
    def test_should_close_when_inactive(self):
        """Test that should_close returns True when dialog is inactive"""
        self.dialog.is_active = False
        self.assertTrue(self.dialog.should_close())
    
    def test_should_not_close_when_active(self):
        """Test that should_close returns False when dialog is active"""
        self.dialog.is_active = True
        self.assertFalse(self.dialog.should_close())
    
    def test_on_activate_marks_dirty(self):
        """Test that on_activate marks the dialog as dirty"""
        self.dialog.content_changed = False
        self.dialog.on_activate()
        self.assertTrue(self.dialog.content_changed)
    
    def test_on_deactivate_does_not_raise(self):
        """Test that on_deactivate can be called without error"""
        try:
            self.dialog.on_deactivate()
        except Exception as e:
            self.fail(f"on_deactivate raised an exception: {e}")
    
    def test_handle_key_event_escape_closes_dialog(self):
        """Test that ESC key closes the dialog"""
        self.dialog.is_active = True
        event = KeyEvent(key_code=KeyCode.ESCAPE, char='', modifiers=0)
        
        result = self.dialog.handle_key_event(event)
        
        self.assertTrue(result)
        self.assertFalse(self.dialog.is_active)
    
    def test_handle_char_event_updates_filter(self):
        """Test that character events update the filter"""
        # Show the dialog first
        with patch('tfm_jump_dialog.Path') as mock_path:
            mock_root = Mock()
            mock_root.iterdir.return_value = []
            self.dialog.show(mock_root)
        
        # Type a character
        event = CharEvent(char='a')
        result = self.dialog.handle_char_event(event)
        
        self.assertTrue(result)
        self.assertTrue(self.dialog.content_changed)
    
    def test_get_selected_directory_returns_none_initially(self):
        """Test that get_selected_directory returns None initially"""
        result = self.dialog.get_selected_directory()
        self.assertIsNone(result)
    
    def test_lifecycle_methods_exist(self):
        """Test that all UILayer lifecycle methods exist"""
        self.assertTrue(hasattr(self.dialog, 'handle_key_event'))
        self.assertTrue(hasattr(self.dialog, 'handle_char_event'))
        self.assertTrue(hasattr(self.dialog, 'render'))
        self.assertTrue(hasattr(self.dialog, 'is_full_screen'))
        self.assertTrue(hasattr(self.dialog, 'needs_redraw'))
        self.assertTrue(hasattr(self.dialog, 'mark_dirty'))
        self.assertTrue(hasattr(self.dialog, 'clear_dirty'))
        self.assertTrue(hasattr(self.dialog, 'should_close'))
        self.assertTrue(hasattr(self.dialog, 'on_activate'))
        self.assertTrue(hasattr(self.dialog, 'on_deactivate'))


if __name__ == '__main__':
    unittest.main()
