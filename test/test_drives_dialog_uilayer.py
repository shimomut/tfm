#!/usr/bin/env python3
"""
Test DrivesDialog UILayer interface implementation
"""

import sys
import os
import pytest
from unittest.mock import Mock, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ttk import KeyEvent, CharEvent, KeyCode
from tfm_drives_dialog import DrivesDialog, DriveEntry
from tfm_ui_layer import UILayer


class TestDrivesDialogUILayerInterface:
    """Test that DrivesDialog properly implements the UILayer interface"""
    
    def test_drives_dialog_inherits_from_uilayer(self):
        """Test that DrivesDialog inherits from UILayer"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        assert isinstance(dialog, UILayer)
    
    def test_handle_key_event_returns_bool(self):
        """Test that handle_key_event returns a boolean"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        dialog.show()
        
        event = KeyEvent(key_code=KeyCode.ESCAPE, char='', modifiers=0)
        result = dialog.handle_key_event(event)
        
        assert isinstance(result, bool)
    
    def test_handle_char_event_returns_bool(self):
        """Test that handle_char_event returns a boolean"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        dialog.show()
        
        event = CharEvent(char='a')
        result = dialog.handle_char_event(event)
        
        assert isinstance(result, bool)
    
    def test_render_calls_draw(self):
        """Test that render calls the draw method"""
        config = Mock()
        renderer = Mock()
        renderer.get_dimensions = Mock(return_value=(24, 80))
        renderer.draw_text = Mock()
        renderer.draw_box = Mock()
        
        dialog = DrivesDialog(config, renderer)
        dialog.show()
        
        # Mock the draw method to verify it's called
        dialog.draw = Mock()
        
        dialog.render(renderer)
        
        dialog.draw.assert_called_once()
    
    def test_is_full_screen_returns_false(self):
        """Test that is_full_screen returns False for dialogs"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        assert dialog.is_full_screen() is False
    
    def test_needs_redraw_returns_bool(self):
        """Test that needs_redraw returns a boolean"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        result = dialog.needs_redraw()
        
        assert isinstance(result, bool)
    
    def test_mark_dirty_sets_content_changed(self):
        """Test that mark_dirty sets content_changed flag"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        dialog.content_changed = False
        dialog.mark_dirty()
        
        assert dialog.content_changed is True
    
    def test_clear_dirty_clears_content_changed(self):
        """Test that clear_dirty clears content_changed flag"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        dialog.content_changed = True
        dialog.loading_s3 = False
        dialog.clear_dirty()
        
        assert dialog.content_changed is False
    
    def test_clear_dirty_preserves_flag_when_loading(self):
        """Test that clear_dirty preserves flag when loading S3"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        dialog.content_changed = True
        dialog.loading_s3 = True
        dialog.clear_dirty()
        
        # Should not clear when loading
        assert dialog.content_changed is True
    
    def test_should_close_returns_bool(self):
        """Test that should_close returns a boolean"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        result = dialog.should_close()
        
        assert isinstance(result, bool)
    
    def test_should_close_true_when_inactive(self):
        """Test that should_close returns True when dialog is inactive"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        dialog.is_active = False
        
        assert dialog.should_close() is True
    
    def test_should_close_false_when_active(self):
        """Test that should_close returns False when dialog is active"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        dialog.is_active = True
        
        assert dialog.should_close() is False
    
    def test_on_activate_marks_dirty(self):
        """Test that on_activate marks content as changed"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        dialog.content_changed = False
        dialog.on_activate()
        
        assert dialog.content_changed is True
    
    def test_on_deactivate_cancels_s3_scan(self):
        """Test that on_deactivate cancels S3 scan"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        # Mock the cancel method
        dialog._cancel_current_s3_scan = Mock()
        
        dialog.on_deactivate()
        
        dialog._cancel_current_s3_scan.assert_called_once()


class TestDrivesDialogUILayerEventHandling:
    """Test event handling through UILayer interface"""
    
    def test_handle_key_event_escape_closes_dialog(self):
        """Test that ESC key closes the dialog"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        dialog.show()
        
        event = KeyEvent(key_code=KeyCode.ESCAPE, char='', modifiers=0)
        result = dialog.handle_key_event(event)
        
        assert result is True
        assert dialog.is_active is False
    
    def test_handle_key_event_enter_selects_drive(self):
        """Test that Enter key selects a drive"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        dialog.show()
        
        # Add a test drive
        test_drive = DriveEntry("Test Drive", "/test", "local")
        dialog.drives = [test_drive]
        dialog.filtered_drives = [test_drive]
        dialog.selected = 0
        
        event = KeyEvent(key_code=KeyCode.ENTER, char='', modifiers=0)
        result = dialog.handle_key_event(event)
        
        assert result is True
        assert dialog.is_active is False
        assert dialog.get_selected_drive() == test_drive
    
    def test_handle_key_event_navigation_updates_selection(self):
        """Test that navigation keys update selection"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        dialog.show()
        
        # Add test drives
        drive1 = DriveEntry("Drive 1", "/test1", "local")
        drive2 = DriveEntry("Drive 2", "/test2", "local")
        dialog.drives = [drive1, drive2]
        dialog.filtered_drives = [drive1, drive2]
        dialog.selected = 0
        
        event = KeyEvent(key_code=KeyCode.DOWN, char='', modifiers=0)
        result = dialog.handle_key_event(event)
        
        assert result is True
        assert dialog.selected == 1
    
    def test_handle_char_event_filters_drives(self):
        """Test that character input filters drives"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        dialog.show()
        
        # Add test drives
        drive1 = DriveEntry("Apple Drive", "/apple", "local")
        drive2 = DriveEntry("Banana Drive", "/banana", "local")
        dialog.drives = [drive1, drive2]
        dialog.filtered_drives = [drive1, drive2]
        
        # Type 'p' which should only match "Apple Drive"
        event = CharEvent(char='p')
        result = dialog.handle_char_event(event)
        
        assert result is True
        assert len(dialog.filtered_drives) == 1
        assert dialog.filtered_drives[0] == drive1


class TestDrivesDialogUILayerRendering:
    """Test rendering through UILayer interface"""
    
    def test_needs_redraw_true_when_content_changed(self):
        """Test that needs_redraw returns True when content changed"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        dialog.content_changed = True
        dialog.loading_s3 = False
        
        assert dialog.needs_redraw() is True
    
    def test_needs_redraw_true_when_loading_s3(self):
        """Test that needs_redraw returns True when loading S3"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        dialog.content_changed = False
        dialog.loading_s3 = True
        
        assert dialog.needs_redraw() is True
    
    def test_needs_redraw_false_when_clean(self):
        """Test that needs_redraw returns False when clean"""
        config = Mock()
        renderer = Mock()
        dialog = DrivesDialog(config, renderer)
        
        dialog.content_changed = False
        dialog.loading_s3 = False
        
        assert dialog.needs_redraw() is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
