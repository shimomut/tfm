"""
Tests for FileManagerLayer wrapper class.

This test suite verifies that the FileManagerLayer correctly wraps
FileManager functionality and implements the UILayer interface.

Run with: PYTHONPATH=.:src:ttk pytest test/test_file_manager_layer.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.tfm_ui_layer import FileManagerLayer


class TestFileManagerLayerBasics:
    """Test basic FileManagerLayer functionality."""
    
    def test_initialization(self):
        """Test FileManagerLayer initialization."""
        # Create mock FileManager
        mock_fm = Mock()
        
        # Create layer
        layer = FileManagerLayer(mock_fm)
        
        # Verify initialization
        assert layer.file_manager is mock_fm
        assert layer._close_requested is False
        assert layer._dirty is True  # Should start dirty for initial render
    
    def test_is_full_screen(self):
        """Test that FileManagerLayer is always full-screen."""
        mock_fm = Mock()
        layer = FileManagerLayer(mock_fm)
        
        assert layer.is_full_screen() is True
    
    def test_handle_key_event_delegates_to_file_manager(self):
        """Test that key events are delegated to FileManager's main screen handler."""
        mock_fm = Mock()
        mock_fm.handle_main_screen_key_event = Mock(return_value=True)
        layer = FileManagerLayer(mock_fm)
        
        # Create mock event
        mock_event = Mock()
        
        # Handle event
        result = layer.handle_key_event(mock_event)
        
        # Verify delegation to handle_main_screen_key_event (not handle_input)
        mock_fm.handle_main_screen_key_event.assert_called_once_with(mock_event)
        assert result is True
        assert layer._dirty is True  # Should mark dirty when event consumed
        assert layer._dirty is True  # Should mark dirty when event consumed
    
    def test_handle_key_event_no_dirty_when_not_consumed(self):
        """Test that layer doesn't mark dirty when event not consumed."""
        mock_fm = Mock()
        mock_fm.handle_main_screen_key_event = Mock(return_value=False)
        layer = FileManagerLayer(mock_fm)
        layer._dirty = False  # Clear initial dirty flag
        
        # Create mock event
        mock_event = Mock()
        
        # Handle event
        result = layer.handle_key_event(mock_event)
        
        # Verify no dirty marking when event not consumed
        assert result is False
        assert layer._dirty is False
    
    def test_handle_char_event_returns_false(self):
        """Test that char events are not handled by main screen."""
        mock_fm = Mock()
        layer = FileManagerLayer(mock_fm)
        
        # Create mock event
        mock_event = Mock()
        
        # Handle event
        result = layer.handle_char_event(mock_event)
        
        # Verify char events are not handled
        assert result is False
    
    def test_render_delegates_to_file_manager(self):
        """Test that rendering is delegated to FileManager."""
        mock_fm = Mock()
        mock_fm.needs_full_redraw = True
        mock_fm.refresh_files = Mock()
        mock_fm.clear_screen_with_background = Mock()
        mock_fm.draw_header = Mock()
        mock_fm.draw_files = Mock()
        mock_fm.draw_log_pane = Mock()
        mock_fm.draw_status = Mock()
        
        # Mock quick_edit_bar and quick_choice_bar
        mock_fm.quick_edit_bar = Mock()
        mock_fm.quick_edit_bar.is_active = False
        mock_fm.quick_choice_bar = Mock()
        mock_fm.quick_choice_bar.is_active = False
        
        # Create mock renderer with get_dimensions method
        mock_renderer = Mock()
        mock_renderer.get_dimensions = Mock(return_value=(24, 80))
        mock_fm.renderer = mock_renderer
        
        layer = FileManagerLayer(mock_fm)
        
        # Render
        layer.render(mock_renderer)
        
        # Verify delegation to individual draw methods
        mock_fm.refresh_files.assert_called_once()
        mock_fm.clear_screen_with_background.assert_called_once()
        mock_fm.draw_header.assert_called_once()
        mock_fm.draw_files.assert_called_once()
        mock_fm.draw_log_pane.assert_called_once()
        mock_fm.draw_status.assert_called_once()
    
    def test_needs_redraw_checks_both_flags(self):
        """Test that needs_redraw checks both layer and FileManager flags."""
        mock_fm = Mock()
        layer = FileManagerLayer(mock_fm)
        
        # Test with layer dirty
        layer._dirty = True
        mock_fm.needs_full_redraw = False
        assert layer.needs_redraw() is True
        
        # Test with FileManager dirty
        layer._dirty = False
        mock_fm.needs_full_redraw = True
        assert layer.needs_redraw() is True
        
        # Test with both dirty
        layer._dirty = True
        mock_fm.needs_full_redraw = True
        assert layer.needs_redraw() is True
        
        # Test with neither dirty
        layer._dirty = False
        mock_fm.needs_full_redraw = False
        assert layer.needs_redraw() is False
    
    def test_mark_dirty(self):
        """Test marking layer as dirty."""
        mock_fm = Mock()
        layer = FileManagerLayer(mock_fm)
        layer._dirty = False
        
        layer.mark_dirty()
        
        assert layer._dirty is True
    
    def test_clear_dirty(self):
        """Test clearing dirty flags."""
        mock_fm = Mock()
        mock_fm.needs_full_redraw = True
        layer = FileManagerLayer(mock_fm)
        layer._dirty = True
        
        layer.clear_dirty()
        
        assert layer._dirty is False
        assert mock_fm.needs_full_redraw is False
    
    def test_should_close_returns_close_requested(self):
        """Test that should_close returns the close request flag."""
        mock_fm = Mock()
        layer = FileManagerLayer(mock_fm)
        
        # Initially should not close
        assert layer.should_close() is False
        
        # After requesting close
        layer.request_close()
        assert layer.should_close() is True
    
    def test_request_close(self):
        """Test requesting application quit."""
        mock_fm = Mock()
        layer = FileManagerLayer(mock_fm)
        
        layer.request_close()
        
        assert layer._close_requested is True
    
    def test_on_activate_marks_dirty(self):
        """Test that activation marks layer dirty."""
        mock_fm = Mock()
        layer = FileManagerLayer(mock_fm)
        layer._dirty = False
        
        layer.on_activate()
        
        assert layer._dirty is True
    
    def test_on_deactivate_does_nothing(self):
        """Test that deactivation doesn't change state."""
        mock_fm = Mock()
        layer = FileManagerLayer(mock_fm)
        layer._dirty = True
        
        layer.on_deactivate()
        
        # State should remain unchanged
        assert layer._dirty is True


class TestFileManagerLayerLifecycle:
    """Test FileManagerLayer lifecycle behavior."""
    
    def test_initial_state_is_dirty(self):
        """Test that layer starts in dirty state for initial render."""
        mock_fm = Mock()
        layer = FileManagerLayer(mock_fm)
        
        assert layer.needs_redraw() is True
    
    def test_activation_after_deactivation_marks_dirty(self):
        """Test that reactivation marks layer dirty."""
        mock_fm = Mock()
        mock_fm.needs_full_redraw = False
        layer = FileManagerLayer(mock_fm)
        
        # Clear dirty state
        layer._dirty = False
        
        # Deactivate (should do nothing)
        layer.on_deactivate()
        assert layer._dirty is False
        
        # Reactivate (should mark dirty)
        layer.on_activate()
        assert layer._dirty is True
