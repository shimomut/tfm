"""
Test BatchRenameDialog UILayer interface implementation

Run with: PYTHONPATH=.:src:ttk pytest test/test_batch_rename_uilayer.py -v
"""

from pathlib import Path as PathLib
import pytest
from unittest.mock import Mock
from ttk import KeyEvent, CharEvent, KeyCode
from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path


class MockRenderer:
    """Mock renderer for testing"""
    def __init__(self):
        self.dimensions = (40, 120)
        self.drawn_text = []
    
    def get_dimensions(self):
        return self.dimensions
    
    def draw_text(self, y, x, text, color_pair=None, attributes=None):
        self.drawn_text.append((y, x, text))
    
    def draw_hline(self, y, x, char, count, color_pair=None):
        pass
    
    def set_caret_position(self, x, y):
        """Mock caret position setting"""
        pass
    
    def refresh(self):
        pass


class TestBatchRenameDialogUILayer:
    """Test BatchRenameDialog UILayer interface implementation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = Mock()
        self.renderer = MockRenderer()
        self.dialog = BatchRenameDialog(self.config, self.renderer)
    
    def test_implements_uilayer_interface(self):
        """Test that BatchRenameDialog implements UILayer interface"""
        from tfm_ui_layer import UILayer
        assert isinstance(self.dialog, UILayer)
    
    def test_handle_key_event_returns_bool(self):
        """Test that handle_key_event returns boolean"""
        # Show dialog first
        self.dialog.show([Path("test.txt")])
        
        # Test with ESC key (should return True)
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=0)
        result = self.dialog.handle_key_event(event)
        assert isinstance(result, bool)
        assert result is True
    
    def test_handle_char_event_returns_bool(self):
        """Test that handle_char_event returns boolean"""
        # Show dialog first
        self.dialog.show([Path("test.txt")])
        
        # Test with character input
        event = CharEvent(char='a')
        result = self.dialog.handle_char_event(event)
        assert isinstance(result, bool)
    
    def test_render_calls_draw(self):
        """Test that render() calls draw()"""
        # Show dialog first
        self.dialog.show([Path("test.txt")])
        
        # Clear any previous draws
        self.renderer.drawn_text = []
        
        # Call render
        self.dialog.render(self.renderer)
        
        # Verify something was drawn
        assert len(self.renderer.drawn_text) > 0
    
    def test_is_full_screen_returns_false(self):
        """Test that is_full_screen returns False for dialogs"""
        result = self.dialog.is_full_screen()
        assert result is False
    
    def test_needs_redraw_tracks_dirty_state(self):
        """Test that needs_redraw tracks dirty state"""
        # Initially should need redraw
        assert self.dialog.needs_redraw() is True
        
        # Clear dirty flag
        self.dialog.clear_dirty()
        assert self.dialog.needs_redraw() is False
        
        # Mark dirty
        self.dialog.mark_dirty()
        assert self.dialog.needs_redraw() is True
    
    def test_should_close_when_inactive(self):
        """Test that should_close returns True when dialog is inactive"""
        # Initially inactive
        assert self.dialog.should_close() is True
        
        # Show dialog
        self.dialog.show([Path("test.txt")])
        assert self.dialog.should_close() is False
        
        # Exit dialog
        self.dialog.exit()
        assert self.dialog.should_close() is True
    
    def test_on_activate_marks_dirty(self):
        """Test that on_activate marks dialog as dirty"""
        # Clear dirty flag
        self.dialog.clear_dirty()
        assert self.dialog.needs_redraw() is False
        
        # Activate
        self.dialog.on_activate()
        assert self.dialog.needs_redraw() is True
    
    def test_on_deactivate_does_not_crash(self):
        """Test that on_deactivate can be called without error"""
        # Should not raise any exception
        self.dialog.on_deactivate()
    
    def test_mark_dirty_sets_content_changed(self):
        """Test that mark_dirty sets content_changed flag"""
        self.dialog.content_changed = False
        self.dialog.mark_dirty()
        assert self.dialog.content_changed is True
    
    def test_clear_dirty_clears_content_changed(self):
        """Test that clear_dirty clears content_changed flag"""
        self.dialog.content_changed = True
        self.dialog.clear_dirty()
        assert self.dialog.content_changed is False
    
    def test_handle_key_event_with_tab_switches_field(self):
        """Test that Tab key switches between fields"""
        # Show dialog first
        self.dialog.show([Path("test.txt")])
        
        # Initially on regex field
        assert self.dialog.active_field == 'regex'
        
        # Press Tab
        event = KeyEvent(key_code=KeyCode.TAB, modifiers=0)
        result = self.dialog.handle_key_event(event)
        
        # Should switch to destination field
        assert result is True
        assert self.dialog.active_field == 'destination'
    
    def test_handle_key_event_with_escape_closes_dialog(self):
        """Test that ESC key closes the dialog"""
        # Show dialog first
        self.dialog.show([Path("test.txt")])
        assert self.dialog.is_active is True
        
        # Press ESC
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=0)
        result = self.dialog.handle_key_event(event)
        
        # Should close dialog
        assert result is True
        assert self.dialog.is_active is False
    
    def test_handle_char_event_updates_text_editor(self):
        """Test that character events update the active text editor"""
        # Show dialog first
        self.dialog.show([Path("test.txt")])
        
        # Initially regex editor should be empty
        assert self.dialog.regex_editor.get_text() == ""
        
        # Type a character
        event = CharEvent(char='a')
        result = self.dialog.handle_char_event(event)
        
        # Should update regex editor
        assert result is True
        assert self.dialog.regex_editor.get_text() == "a"
