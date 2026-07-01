"""
Tests for menu-will-open callback mechanism.

This test suite verifies that the menu-will-open callback is properly
integrated and updates menu states before menus are displayed.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from tfm_main import TFMEventCallback


class TestMenuWillOpenCallback:
    """Test suite for menu-will-open callback mechanism."""
    
    def test_callback_has_on_menu_will_open_method(self):
        """Verify TFMEventCallback has on_menu_will_open method."""
        mock_fm = Mock()
        callback = TFMEventCallback(mock_fm)
        
        assert hasattr(callback, 'on_menu_will_open')
        assert callable(callback.on_menu_will_open)
    
    def test_on_menu_will_open_calls_update_menu_states(self):
        """Verify on_menu_will_open calls FileManager._update_menu_states."""
        mock_fm = Mock()
        mock_fm._update_menu_states = Mock()
        
        callback = TFMEventCallback(mock_fm)
        callback.on_menu_will_open()
        
        mock_fm._update_menu_states.assert_called_once()
    
    def test_on_menu_will_open_handles_exceptions(self):
        """Verify on_menu_will_open handles exceptions gracefully."""
        mock_fm = Mock()
        mock_fm._update_menu_states = Mock(side_effect=Exception("Test error"))
        mock_fm.logger = Mock()
        
        callback = TFMEventCallback(mock_fm)
        
        # Should not raise exception
        callback.on_menu_will_open()
        
        # Should log error
        mock_fm.logger.error.assert_called_once()
        assert "Error updating menu states" in str(mock_fm.logger.error.call_args)
    
    def test_on_menu_will_open_with_debug_mode(self):
        """Verify on_menu_will_open prints stack trace in debug mode."""
        mock_fm = Mock()
        mock_fm._update_menu_states = Mock(side_effect=Exception("Test error"))
        mock_fm.logger = Mock()
        
        callback = TFMEventCallback(mock_fm)
        
        # Enable debug mode
        import os
        old_debug = os.environ.get('TFM_DEBUG')
        try:
            os.environ['TFM_DEBUG'] = '1'
            
            # Should not raise exception even in debug mode
            with patch('traceback.print_exc') as mock_print_exc:
                callback.on_menu_will_open()
                mock_print_exc.assert_called_once()
        finally:
            # Restore debug mode
            if old_debug is None:
                os.environ.pop('TFM_DEBUG', None)
            else:
                os.environ['TFM_DEBUG'] = old_debug
    
    def test_callback_integration_with_file_manager(self):
        """Test callback integration with actual FileManager methods."""
        # Create mock FileManager with realistic structure
        mock_fm = Mock()
        mock_fm.is_desktop_mode = Mock(return_value=True)
        mock_fm.menu_manager = Mock()
        mock_fm.menu_manager.update_menu_states = Mock(return_value={
            'FILE_COPY': True,
            'FILE_MOVE': False,
            'EDIT_SELECT_ALL': True
        })
        mock_fm.renderer = Mock()
        mock_fm.logger = Mock()
        
        # Create callback
        callback = TFMEventCallback(mock_fm)
        
        # Mock _update_menu_states to call menu_manager
        def mock_update_menu_states():
            if mock_fm.is_desktop_mode() and mock_fm.menu_manager:
                states = mock_fm.menu_manager.update_menu_states()
                for item_id, enabled in states.items():
                    mock_fm.renderer.update_menu_item_state(item_id, enabled)
        
        mock_fm._update_menu_states = mock_update_menu_states
        
        # Trigger callback
        callback.on_menu_will_open()
        
        # Verify menu states were updated
        mock_fm.menu_manager.update_menu_states.assert_called_once()
        assert mock_fm.renderer.update_menu_item_state.call_count == 3
        
        # Verify correct states were set
        calls = mock_fm.renderer.update_menu_item_state.call_args_list
        assert ('FILE_COPY', True) in [call[0] for call in calls]
        assert ('FILE_MOVE', False) in [call[0] for call in calls]
        assert ('EDIT_SELECT_ALL', True) in [call[0] for call in calls]
