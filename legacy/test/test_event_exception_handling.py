"""
Tests for exception handling in event callbacks.

This test verifies that TFM catches exceptions in key, char, and menu event
handlers to prevent application shutdown.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from ttk import KeyEvent, KeyCode, ModifierKey, CharEvent, MenuEvent
from src.tfm_main import TFMEventCallback


class TestEventExceptionHandling:
    """Test exception handling in TFMEventCallback."""
    
    @pytest.fixture
    def mock_file_manager(self):
        """Create a mock FileManager with necessary attributes."""
        fm = Mock()
        fm.adaptive_fps = Mock()
        fm.adaptive_fps.mark_activity = Mock()
        fm.logger = Mock()
        fm.ui_layer_stack = Mock()
        fm.is_desktop_mode = Mock(return_value=False)
        return fm
    
    @pytest.fixture
    def callback(self, mock_file_manager):
        """Create a TFMEventCallback instance."""
        return TFMEventCallback(mock_file_manager)
    
    def test_key_event_exception_without_debug(self, callback, mock_file_manager):
        """Test that key event exceptions are caught without debug mode."""
        # Set up environment without debug mode
        os.environ.pop('TFM_DEBUG', None)
        
        # Make handle_key_event raise an exception
        mock_file_manager.ui_layer_stack.handle_key_event.side_effect = ValueError("Test error")
        
        # Create a key event
        event = KeyEvent(key_code=KeyCode.A, modifiers=ModifierKey.NONE, char='a')
        
        # Call should not raise exception
        result = callback.on_key_event(event)
        
        # Should return True (event consumed)
        assert result is True
        
        # Should log error message
        mock_file_manager.logger.error.assert_called_once()
        error_msg = mock_file_manager.logger.error.call_args[0][0]
        assert "Error handling key event: Test error" in error_msg
    
    def test_key_event_exception_with_debug(self, callback, mock_file_manager, capsys):
        """Test that key event exceptions print stack trace to stderr in debug mode."""
        # Set up environment with debug mode
        os.environ['TFM_DEBUG'] = '1'
        
        try:
            # Make handle_key_event raise an exception
            mock_file_manager.ui_layer_stack.handle_key_event.side_effect = ValueError("Test error")
            
            # Create a key event
            event = KeyEvent(key_code=KeyCode.A, modifiers=ModifierKey.NONE, char='a')
            
            # Call should not raise exception
            result = callback.on_key_event(event)
            
            # Should return True (event consumed)
            assert result is True
            
            # Should log error message
            mock_file_manager.logger.error.assert_called_once()
            error_msg = mock_file_manager.logger.error.call_args[0][0]
            assert "Error handling key event: Test error" in error_msg
            
            # Should print stack trace to stderr
            captured = capsys.readouterr()
            assert "Traceback" in captured.err
            assert "ValueError: Test error" in captured.err
        finally:
            # Clean up environment
            os.environ.pop('TFM_DEBUG', None)
    
    def test_char_event_exception_without_debug(self, callback, mock_file_manager):
        """Test that char event exceptions are caught without debug mode."""
        # Set up environment without debug mode
        os.environ.pop('TFM_DEBUG', None)
        
        # Make handle_char_event raise an exception
        mock_file_manager.ui_layer_stack.handle_char_event.side_effect = RuntimeError("Test error")
        
        # Create a char event
        event = CharEvent('x')
        
        # Call should not raise exception
        result = callback.on_char_event(event)
        
        # Should return True (event consumed)
        assert result is True
        
        # Should log error message
        mock_file_manager.logger.error.assert_called_once()
        error_msg = mock_file_manager.logger.error.call_args[0][0]
        assert "Error handling char event: Test error" in error_msg
    
    def test_char_event_exception_with_debug(self, callback, mock_file_manager, capsys):
        """Test that char event exceptions print stack trace to stderr in debug mode."""
        # Set up environment with debug mode
        os.environ['TFM_DEBUG'] = '1'
        
        try:
            # Make handle_char_event raise an exception
            mock_file_manager.ui_layer_stack.handle_char_event.side_effect = RuntimeError("Test error")
            
            # Create a char event
            event = CharEvent('x')
            
            # Call should not raise exception
            result = callback.on_char_event(event)
            
            # Should return True (event consumed)
            assert result is True
            
            # Should log error message
            mock_file_manager.logger.error.assert_called_once()
            error_msg = mock_file_manager.logger.error.call_args[0][0]
            assert "Error handling char event: Test error" in error_msg
            
            # Should print stack trace to stderr
            captured = capsys.readouterr()
            assert "Traceback" in captured.err
            assert "RuntimeError: Test error" in captured.err
        finally:
            # Clean up environment
            os.environ.pop('TFM_DEBUG', None)
    
    def test_menu_event_exception_without_debug(self, callback, mock_file_manager):
        """Test that menu event exceptions are caught without debug mode."""
        # Set up environment without debug mode
        os.environ.pop('TFM_DEBUG', None)
        
        # Make _handle_menu_event raise an exception
        mock_file_manager._handle_menu_event.side_effect = KeyError("Test error")
        
        # Create a menu event
        event = MenuEvent('file.open')
        
        # Call should not raise exception
        result = callback.on_menu_event(event)
        
        # Should return True (event consumed)
        assert result is True
        
        # Should log error message
        mock_file_manager.logger.error.assert_called_once()
        error_msg = mock_file_manager.logger.error.call_args[0][0]
        assert "Error handling menu event:" in error_msg
        assert "Test error" in error_msg
    
    def test_menu_event_exception_with_debug(self, callback, mock_file_manager, capsys):
        """Test that menu event exceptions print stack trace to stderr in debug mode."""
        # Set up environment with debug mode
        os.environ['TFM_DEBUG'] = '1'
        
        try:
            # Make _handle_menu_event raise an exception
            mock_file_manager._handle_menu_event.side_effect = KeyError("Test error")
            
            # Create a menu event
            event = MenuEvent('file.open')
            
            # Call should not raise exception
            result = callback.on_menu_event(event)
            
            # Should return True (event consumed)
            assert result is True
            
            # Should log error message
            mock_file_manager.logger.error.assert_called_once()
            error_msg = mock_file_manager.logger.error.call_args[0][0]
            assert "Error handling menu event:" in error_msg
            assert "Test error" in error_msg
            
            # Should print stack trace to stderr
            captured = capsys.readouterr()
            assert "Traceback" in captured.err
            assert "KeyError: 'Test error'" in captured.err
        finally:
            # Clean up environment
            os.environ.pop('TFM_DEBUG', None)
    
    def test_key_event_normal_operation(self, callback, mock_file_manager):
        """Test that normal key events work without exceptions."""
        # Make handle_key_event return True
        mock_file_manager.ui_layer_stack.handle_key_event.return_value = True
        
        # Create a key event
        event = KeyEvent(key_code=KeyCode.A, modifiers=ModifierKey.NONE, char='a')
        
        # Call should work normally
        result = callback.on_key_event(event)
        
        # Should return True
        assert result is True
        
        # Should not log any errors
        mock_file_manager.logger.error.assert_not_called()
    
    def test_char_event_normal_operation(self, callback, mock_file_manager):
        """Test that normal char events work without exceptions."""
        # Make handle_char_event return True
        mock_file_manager.ui_layer_stack.handle_char_event.return_value = True
        
        # Create a char event
        event = CharEvent('x')
        
        # Call should work normally
        result = callback.on_char_event(event)
        
        # Should return True
        assert result is True
        
        # Should not log any errors
        mock_file_manager.logger.error.assert_not_called()
    
    def test_menu_event_normal_operation(self, callback, mock_file_manager):
        """Test that normal menu events work without exceptions."""
        # Make _handle_menu_event return True
        mock_file_manager._handle_menu_event.return_value = True
        
        # Create a menu event
        event = MenuEvent('file.open')
        
        # Call should work normally
        result = callback.on_menu_event(event)
        
        # Should return True
        assert result is True
        
        # Should not log any errors
        mock_file_manager.logger.error.assert_not_called()
