#!/usr/bin/env python3
"""
Test TFM main input handling migration to TTK API.

This test verifies that tfm_main.py correctly uses TTK's KeyEvent
for input handling instead of curses key codes.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import Mock, MagicMock, patch
from ttk import KeyEvent, KeyCode, ModifierKey
from tfm_main import FileManager


def test_input_event_handling():
    """Test that FileManager handles KeyEvent correctly"""
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    mock_renderer.clear = Mock()
    mock_renderer.refresh = Mock()
    mock_renderer.draw_text = Mock()
    mock_renderer.draw_hline = Mock()
    mock_renderer.draw_vline = Mock()
    mock_renderer.set_cursor_visibility = Mock()
    mock_renderer.get_input = Mock()
    
    # Create FileManager with mock renderer
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'):
        
        fm = FileManager(mock_renderer)
        fm.log_height_ratio = 0.25  # Set required attribute
        
        # Test that handle_input accepts KeyEvent
        # Test UP arrow key
        up_event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
        result = fm.handle_input(up_event)
        assert result is True, "UP arrow should be handled"
        
        # Test DOWN arrow key
        down_event = KeyEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.NONE)
        result = fm.handle_input(down_event)
        assert result is True, "DOWN arrow should be handled"
        
        # Test PAGE_UP key
        page_up_event = KeyEvent(key_code=KeyCode.PAGE_UP, modifiers=ModifierKey.NONE)
        result = fm.handle_input(page_up_event)
        assert result is True, "PAGE_UP should be handled"
        
        # Test PAGE_DOWN key
        page_down_event = KeyEvent(key_code=KeyCode.PAGE_DOWN, modifiers=ModifierKey.NONE)
        result = fm.handle_input(page_down_event)
        assert result is True, "PAGE_DOWN should be handled"
        
        print("✓ Input event handling test passed")


def test_is_key_for_action_with_input_event():
    """Test that is_key_for_action works with KeyEvent"""
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    mock_renderer.clear = Mock()
    mock_renderer.refresh = Mock()
    mock_renderer.draw_text = Mock()
    mock_renderer.set_cursor_visibility = Mock()
    
    # Create FileManager with mock renderer
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'), \
         patch('tfm_main.is_input_event_bound_to_with_selection') as mock_is_bound:
        
        fm = FileManager(mock_renderer)
        
        # Test with printable character
        mock_is_bound.return_value = True
        char_event = KeyEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
        result = fm.is_key_for_action(char_event, 'quit')
        assert result is True, "Printable character should be checked"
        mock_is_bound.assert_called()
        
        # Reset mock for next test
        mock_is_bound.reset_mock()
        
        # Test with special key
        mock_is_bound.return_value = True
        special_event = KeyEvent(key_code=KeyCode.F1, modifiers=ModifierKey.NONE)
        result = fm.is_key_for_action(special_event, 'help')
        assert result is True, "Special key should be checked"
        mock_is_bound.assert_called()
        
        print("✓ is_key_for_action test passed")


def test_handle_isearch_input_with_input_event():
    """Test that handle_isearch_input works with KeyEvent"""
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    mock_renderer.clear = Mock()
    mock_renderer.refresh = Mock()
    mock_renderer.draw_text = Mock()
    mock_renderer.set_cursor_visibility = Mock()
    
    # Create FileManager with mock renderer
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'):
        
        fm = FileManager(mock_renderer)
        fm.log_height_ratio = 0.25  # Set required attribute
        fm.isearch_mode = True
        fm.isearch_pattern = ""
        fm.isearch_matches = []
        
        # Test ESC key
        esc_event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
        result = fm.handle_isearch_input(esc_event)
        assert result is True, "ESC should exit isearch mode"
        assert fm.isearch_mode is False, "Isearch mode should be disabled"
        
        # Reset for next test
        fm.isearch_mode = True
        fm.isearch_pattern = ""
        
        # Test printable character
        char_event = KeyEvent(key_code=ord('t'), modifiers=ModifierKey.NONE, char='t')
        result = fm.handle_isearch_input(char_event)
        assert result is True, "Printable character should be handled"
        assert fm.isearch_pattern == "t", "Pattern should be updated"
        
        # Test BACKSPACE
        backspace_event = KeyEvent(key_code=KeyCode.BACKSPACE, modifiers=ModifierKey.NONE)
        result = fm.handle_isearch_input(backspace_event)
        assert result is True, "BACKSPACE should be handled"
        assert fm.isearch_pattern == "", "Pattern should be cleared"
        
        print("✓ handle_isearch_input test passed")


def test_main_loop_uses_callback_mode():
    """Test that main loop uses callback mode via run_event_loop_iteration()"""
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    mock_renderer.clear = Mock()
    mock_renderer.refresh = Mock()
    mock_renderer.draw_text = Mock()
    mock_renderer.set_cursor_visibility = Mock()
    mock_renderer.set_event_callback = Mock()
    mock_renderer.run_event_loop_iteration = Mock()
    
    # Create FileManager with mock renderer
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'):
        
        fm = FileManager(mock_renderer)
        fm.log_height_ratio = 0.25  # Set required attribute
        fm.should_quit = False
        
        # Verify that set_event_callback was called during initialization
        mock_renderer.set_event_callback.assert_called_once()
        
        # Get the callback that was set
        callback = mock_renderer.set_event_callback.call_args[0][0]
        assert callback is not None, "Event callback should be set"
        
        # Simulate a key event being delivered via callback
        quit_event = KeyEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
        
        # Mock show_confirmation to immediately call callback with True
        def mock_show_confirmation(message, callback_fn):
            callback_fn(True)
        fm.show_confirmation = mock_show_confirmation
        
        # Mock is_key_bound_to_with_selection to return True for quit
        with patch('tfm_main.is_key_bound_to_with_selection', return_value=True):
            # Deliver event via callback
            callback.on_key_event(quit_event)
        
        # Verify should_quit was set
        assert fm.should_quit is True, "should_quit should be set to True"
        
        print("✓ Main loop callback mode test passed")


def test_special_keys_use_keycode_enum():
    """Test that special keys use KeyCode enum values"""
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    mock_renderer.clear = Mock()
    mock_renderer.refresh = Mock()
    mock_renderer.draw_text = Mock()
    mock_renderer.set_cursor_visibility = Mock()
    
    # Create FileManager with mock renderer
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'):
        
        fm = FileManager(mock_renderer)
        
        # Test various special keys (key_code >= 1000)
        special_keys = [
            (KeyCode.UP, "UP", True),
            (KeyCode.DOWN, "DOWN", True),
            (KeyCode.LEFT, "LEFT", True),
            (KeyCode.RIGHT, "RIGHT", True),
            (KeyCode.PAGE_UP, "PAGE_UP", True),
            (KeyCode.PAGE_DOWN, "PAGE_DOWN", True),
            (KeyCode.ENTER, "ENTER", False),  # ENTER is not >= 1000
            (KeyCode.ESCAPE, "ESCAPE", False),  # ESCAPE is a control key
            (KeyCode.BACKSPACE, "BACKSPACE", False),  # BACKSPACE is a control key
        ]
        
        for key_code, name, is_special in special_keys:
            event = KeyEvent(key_code=key_code, modifiers=ModifierKey.NONE)
            # Just verify the event can be created and has the right key_code
            assert event.key_code == key_code, f"{name} key_code should match"
            assert not event.is_printable(), f"{name} should not be printable"
        
        print("✓ Special keys KeyCode enum test passed")


if __name__ == '__main__':
    print("Testing TFM main input handling migration...")
    print()
    
    test_input_event_handling()
    test_is_key_for_action_with_input_event()
    test_handle_isearch_input_with_input_event()
    test_main_loop_uses_callback_mode()
    test_special_keys_use_keycode_enum()
    
    print()
    print("=" * 60)
    print("All input handling migration tests passed!")
    print("=" * 60)
