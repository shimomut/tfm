"""
Test SearchDialog UILayer interface implementation

Run with: PYTHONPATH=.:src:ttk pytest test/test_search_dialog_uilayer.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock
from ttk import KeyEvent, CharEvent, KeyCode
from tfm_search_dialog import SearchDialog
from tfm_ui_layer import UILayer


class TestSearchDialogUILayer:
    """Test SearchDialog UILayer interface implementation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.config.MAX_SEARCH_RESULTS = 10000
        self.renderer = Mock()
        self.renderer.get_dimensions = Mock(return_value=(24, 80))
        self.search_dialog = SearchDialog(self.config, self.renderer)
    
    def test_search_dialog_inherits_from_uilayer(self):
        """Test that SearchDialog inherits from UILayer"""
        assert isinstance(self.search_dialog, UILayer)
    
    def test_handle_key_event_returns_bool(self):
        """Test that handle_key_event returns a boolean"""
        event = KeyEvent(key_code=KeyCode.ESCAPE, char='', modifiers=0)
        result = self.search_dialog.handle_key_event(event)
        assert isinstance(result, bool)
    
    def test_handle_char_event_returns_bool(self):
        """Test that handle_char_event returns a boolean"""
        event = CharEvent(char='a')
        result = self.search_dialog.handle_char_event(event)
        assert isinstance(result, bool)
    
    def test_render_calls_draw(self):
        """Test that render calls draw method"""
        self.search_dialog.draw = Mock()
        self.search_dialog.render(self.renderer)
        self.search_dialog.draw.assert_called_once()
    
    def test_is_full_screen_returns_false(self):
        """Test that is_full_screen returns False for dialogs"""
        assert self.search_dialog.is_full_screen() is False
    
    def test_needs_redraw_returns_bool(self):
        """Test that needs_redraw returns a boolean"""
        result = self.search_dialog.needs_redraw()
        assert isinstance(result, bool)
    
    def test_mark_dirty_sets_content_changed(self):
        """Test that mark_dirty sets content_changed flag"""
        self.search_dialog.content_changed = False
        self.search_dialog.mark_dirty()
        assert self.search_dialog.content_changed is True
    
    def test_clear_dirty_clears_content_changed_when_not_searching(self):
        """Test that clear_dirty clears content_changed when not searching"""
        self.search_dialog.content_changed = True
        self.search_dialog.searching = False
        self.search_dialog.clear_dirty()
        assert self.search_dialog.content_changed is False
    
    def test_clear_dirty_preserves_content_changed_when_searching(self):
        """Test that clear_dirty preserves content_changed when searching"""
        self.search_dialog.content_changed = True
        self.search_dialog.searching = True
        self.search_dialog.clear_dirty()
        # Should remain True when searching for animation
        assert self.search_dialog.content_changed is True
    
    def test_should_close_returns_true_when_inactive(self):
        """Test that should_close returns True when dialog is inactive"""
        self.search_dialog.is_active = False
        assert self.search_dialog.should_close() is True
    
    def test_should_close_returns_false_when_active(self):
        """Test that should_close returns False when dialog is active"""
        self.search_dialog.is_active = True
        assert self.search_dialog.should_close() is False
    
    def test_on_activate_marks_dirty(self):
        """Test that on_activate marks content as changed"""
        self.search_dialog.content_changed = False
        self.search_dialog.on_activate()
        assert self.search_dialog.content_changed is True
    
    def test_on_deactivate_does_nothing(self):
        """Test that on_deactivate is a no-op"""
        # Should not raise any exceptions
        self.search_dialog.on_deactivate()
    
    def test_handle_key_event_tab_switches_search_type(self):
        """Test that Tab key switches search type"""
        self.search_dialog.show('filename')
        assert self.search_dialog.search_type == 'filename'
        
        event = KeyEvent(key_code=KeyCode.TAB, char='', modifiers=0)
        result = self.search_dialog.handle_key_event(event)
        
        assert result is True
        assert self.search_dialog.search_type == 'content'
        assert self.search_dialog.content_changed is True
    
    def test_handle_key_event_escape_closes_dialog(self):
        """Test that Escape key closes the dialog"""
        self.search_dialog.show('filename')
        assert self.search_dialog.is_active is True
        
        event = KeyEvent(key_code=KeyCode.ESCAPE, char='', modifiers=0)
        result = self.search_dialog.handle_key_event(event)
        
        assert result is True
        assert self.search_dialog.is_active is False
    
    def test_handle_char_event_updates_text_editor(self):
        """Test that character events update the text editor"""
        self.search_dialog.show('filename')
        
        event = CharEvent(char='t')
        result = self.search_dialog.handle_char_event(event)
        
        assert result is True
        assert self.search_dialog.content_changed is True
        assert 't' in self.search_dialog.text_editor.text
    
    def test_needs_redraw_true_when_searching(self):
        """Test that needs_redraw returns True when searching"""
        self.search_dialog.content_changed = False
        self.search_dialog.searching = True
        assert self.search_dialog.needs_redraw() is True
    
    def test_needs_redraw_true_when_content_changed(self):
        """Test that needs_redraw returns True when content changed"""
        self.search_dialog.content_changed = True
        self.search_dialog.searching = False
        assert self.search_dialog.needs_redraw() is True
    
    def test_needs_redraw_false_when_clean_and_not_searching(self):
        """Test that needs_redraw returns False when clean and not searching"""
        self.search_dialog.content_changed = False
        self.search_dialog.searching = False
        assert self.search_dialog.needs_redraw() is False
