#!/usr/bin/env python3
"""
Test TextViewer UILayer interface implementation
"""

import unittest
import sys
import os
from pathlib import Path as StdPath
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_text_viewer import TextViewer
from tfm_path import Path
from tfm_ui_layer import UILayer
from ttk import KeyEvent, KeyCode, ModifierKey, CharEvent


class TestTextViewerUILayer(unittest.TestCase):
    """Test TextViewer UILayer interface implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        self.mock_renderer.set_cursor_visibility = Mock()
        self.mock_renderer.draw_text = Mock()
        self.mock_renderer.refresh = Mock()
        
        # Create test file with enough lines to allow scrolling
        self.test_dir = StdPath('/tmp/test_text_viewer_uilayer')
        self.test_dir.mkdir(exist_ok=True)
        self.test_file = self.test_dir / 'test.txt'
        # Create 50 lines to ensure scrolling is possible
        lines = [f"Line {i}\n" for i in range(1, 51)]
        self.test_file.write_text(''.join(lines))
        self.test_path = Path(str(self.test_file))
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_file.exists():
            self.test_file.unlink()
        if self.test_dir.exists():
            self.test_dir.rmdir()
    
    def test_text_viewer_inherits_from_uilayer(self):
        """Test that TextViewer inherits from UILayer"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        self.assertIsInstance(viewer, UILayer)
    
    def test_handle_key_event_returns_bool(self):
        """Test that handle_key_event returns bool"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        event = KeyEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.NONE)
        result = viewer.handle_key_event(event)
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
    
    def test_handle_char_event_returns_false(self):
        """Test that handle_char_event returns False (no text input in viewer)"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        event = CharEvent(char='a')
        result = viewer.handle_char_event(event)
        self.assertFalse(result)
    
    def test_render_calls_draw(self):
        """Test that render() calls draw()"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.render(self.mock_renderer)
        # Verify that renderer methods were called
        self.assertTrue(self.mock_renderer.draw_text.called)
    
    def test_is_full_screen_returns_true(self):
        """Test that is_full_screen() returns True"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        self.assertTrue(viewer.is_full_screen())
    
    def test_needs_redraw_initially_true(self):
        """Test that needs_redraw() is initially True"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        self.assertTrue(viewer.needs_redraw())
    
    def test_mark_dirty_sets_dirty_flag(self):
        """Test that mark_dirty() sets the dirty flag"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.clear_dirty()
        self.assertFalse(viewer.needs_redraw())
        viewer.mark_dirty()
        self.assertTrue(viewer.needs_redraw())
    
    def test_clear_dirty_clears_dirty_flag(self):
        """Test that clear_dirty() clears the dirty flag"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.mark_dirty()
        self.assertTrue(viewer.needs_redraw())
        viewer.clear_dirty()
        self.assertFalse(viewer.needs_redraw())
    
    def test_should_close_initially_false(self):
        """Test that should_close() is initially False"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        self.assertFalse(viewer.should_close())
    
    def test_should_close_true_after_quit_key(self):
        """Test that should_close() returns True after quit key"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        event = KeyEvent(key_code=0, modifiers=ModifierKey.NONE, char='q')
        viewer.handle_key_event(event)
        self.assertTrue(viewer.should_close())
    
    def test_should_close_true_after_escape(self):
        """Test that should_close() returns True after ESC key"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
        viewer.handle_key_event(event)
        self.assertTrue(viewer.should_close())
    
    def test_should_close_true_after_enter(self):
        """Test that should_close() returns True after ENTER key"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        event = KeyEvent(key_code=KeyCode.ENTER, modifiers=ModifierKey.NONE)
        viewer.handle_key_event(event)
        self.assertTrue(viewer.should_close())
    
    def test_on_activate_hides_cursor(self):
        """Test that on_activate() hides cursor"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.on_activate()
        self.mock_renderer.set_cursor_visibility.assert_called_with(False)
    
    def test_on_activate_marks_dirty(self):
        """Test that on_activate() marks layer as dirty"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.clear_dirty()
        viewer.on_activate()
        self.assertTrue(viewer.needs_redraw())
    
    def test_on_deactivate_does_not_raise(self):
        """Test that on_deactivate() can be called without error"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.on_deactivate()  # Should not raise
    
    def test_handle_input_delegates_to_handle_key_event(self):
        """Test that handle_input() delegates to handle_key_event() for backward compatibility"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        event = KeyEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.NONE)
        result = viewer.handle_input(event)
        self.assertTrue(result)
    
    def test_key_events_mark_dirty(self):
        """Test that key events mark the layer as dirty"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.clear_dirty()
        
        # Ensure we're at the top so scrolling down is possible
        viewer.scroll_offset = 0
        
        # Test scroll down
        event = KeyEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.NONE)
        viewer.handle_key_event(event)
        self.assertTrue(viewer.needs_redraw())
        
        # Test toggle line numbers
        viewer.clear_dirty()
        event = KeyEvent(key_code=0, modifiers=ModifierKey.NONE, char='n')
        viewer.handle_key_event(event)
        self.assertTrue(viewer.needs_redraw())


if __name__ == '__main__':
    unittest.main()
