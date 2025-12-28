"""
Tests for TFM Input Event Utilities

This test suite verifies the input event helper functions that bridge
TTK's KeyEvent system with TFM's key binding system.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ttk import KeyEvent, KeyCode, ModifierKey
from tfm_input_utils import (
    input_event_to_key_char,
    is_input_event_for_key,
    is_input_event_for_action,
    is_input_event_for_action_with_selection,
    has_modifier,
    is_ctrl_key,
    is_alt_key,
    is_shift_key,
    is_printable_char,
)


def test_input_event_to_key_char_printable():
    """Test converting printable character events to key chars."""
    print("Testing input_event_to_key_char with printable characters...")
    
    # Lowercase letter
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert input_event_to_key_char(event) == 'a'
    
    # Uppercase letter
    event = KeyEvent(key_code=ord('A'), modifiers=ModifierKey.NONE, char='A')
    assert input_event_to_key_char(event) == 'A'
    
    # Number
    event = KeyEvent(key_code=ord('1'), modifiers=ModifierKey.NONE, char='1')
    assert input_event_to_key_char(event) == '1'
    
    # Special character
    event = KeyEvent(key_code=ord('/'), modifiers=ModifierKey.NONE, char='/')
    assert input_event_to_key_char(event) == '/'
    
    # Space
    event = KeyEvent(key_code=ord(' '), modifiers=ModifierKey.NONE, char=' ')
    assert input_event_to_key_char(event) == ' '
    
    print("✓ Printable character conversion test passed")


def test_input_event_to_key_char_special_keys():
    """Test converting special key events to key chars."""
    print("Testing input_event_to_key_char with special keys...")
    
    # Arrow keys
    event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_UP'
    
    event = KeyEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_DOWN'
    
    event = KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_LEFT'
    
    event = KeyEvent(key_code=KeyCode.RIGHT, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_RIGHT'
    
    # Enter and Escape
    event = KeyEvent(key_code=KeyCode.ENTER, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_ENTER'
    
    event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_ESCAPE'
    
    # Backspace and Delete
    event = KeyEvent(key_code=KeyCode.BACKSPACE, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_BACKSPACE'
    
    event = KeyEvent(key_code=KeyCode.DELETE, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_DC'
    
    # Page Up/Down
    event = KeyEvent(key_code=KeyCode.PAGE_UP, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_PPAGE'
    
    event = KeyEvent(key_code=KeyCode.PAGE_DOWN, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_NPAGE'
    
    # Home and End (use short form for compatibility with TFM config)
    event = KeyEvent(key_code=KeyCode.HOME, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'HOME'
    
    event = KeyEvent(key_code=KeyCode.END, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'END'
    
    # Function keys
    event = KeyEvent(key_code=KeyCode.F1, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_F1'
    
    event = KeyEvent(key_code=KeyCode.F12, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) == 'KEY_F12'
    
    print("✓ Special key conversion test passed")


def test_input_event_to_key_char_with_modifiers():
    """Test converting events with modifier keys to key chars."""
    print("Testing input_event_to_key_char with modifiers...")
    
    # Ctrl+letter
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.CONTROL, char='a')
    assert input_event_to_key_char(event) == 'CTRL_A'
    
    event = KeyEvent(key_code=ord('x'), modifiers=ModifierKey.CONTROL, char='x')
    assert input_event_to_key_char(event) == 'CTRL_X'
    
    # Alt+letter
    event = KeyEvent(key_code=ord('f'), modifiers=ModifierKey.ALT, char='f')
    assert input_event_to_key_char(event) == 'ALT_F'
    
    # Ctrl+special key
    event = KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.CONTROL)
    assert input_event_to_key_char(event) == 'CTRL_KEY_LEFT'
    
    # Alt+special key
    event = KeyEvent(key_code=KeyCode.RIGHT, modifiers=ModifierKey.ALT)
    assert input_event_to_key_char(event) == 'ALT_KEY_RIGHT'
    
    # Shift+special key
    event = KeyEvent(key_code=KeyCode.TAB, modifiers=ModifierKey.SHIFT)
    assert input_event_to_key_char(event) == 'SHIFT_KEY_TAB'
    
    print("✓ Modifier key conversion test passed")


def test_input_event_to_key_char_edge_cases():
    """Test edge cases for input_event_to_key_char."""
    print("Testing input_event_to_key_char edge cases...")
    
    # None event
    assert input_event_to_key_char(None) is None
    
    # Event with no char (only key_code that's not in map)
    event = KeyEvent(key_code=999, modifiers=ModifierKey.NONE)
    assert input_event_to_key_char(event) is None
    
    print("✓ Edge case test passed")


def test_is_input_event_for_key():
    """Test checking if event matches a specific key."""
    print("Testing is_input_event_for_key...")
    
    # Exact match
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert is_input_event_for_key(event, 'a') is True
    assert is_input_event_for_key(event, 'A') is False
    assert is_input_event_for_key(event, 'b') is False
    
    # Special key match
    event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
    assert is_input_event_for_key(event, 'KEY_UP') is True
    assert is_input_event_for_key(event, 'KEY_DOWN') is False
    
    # Modifier key match
    event = KeyEvent(key_code=ord('c'), modifiers=ModifierKey.CONTROL, char='c')
    assert is_input_event_for_key(event, 'CTRL_C') is True
    assert is_input_event_for_key(event, 'c') is False
    
    # None cases
    assert is_input_event_for_key(None, 'a') is False
    assert is_input_event_for_key(event, None) is False
    
    print("✓ is_input_event_for_key test passed")


def test_is_input_event_for_action():
    """Test checking if event matches a configured action."""
    print("Testing is_input_event_for_action...")
    
    # Mock config manager
    class MockConfigManager:
        def is_key_bound_to_action(self, key_char, action):
            # Simple mock: 'q' is bound to 'quit', 'c' to 'copy_files'
            bindings = {
                'quit': ['q', 'Q'],
                'copy_files': ['c', 'C'],
            }
            return key_char in bindings.get(action, [])
    
    config_manager = MockConfigManager()
    
    # Test quit action
    event = KeyEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
    assert is_input_event_for_action(event, 'quit', config_manager) is True
    assert is_input_event_for_action(event, 'copy_files', config_manager) is False
    
    # Test copy action
    event = KeyEvent(key_code=ord('c'), modifiers=ModifierKey.NONE, char='c')
    assert is_input_event_for_action(event, 'copy_files', config_manager) is True
    assert is_input_event_for_action(event, 'quit', config_manager) is False
    
    # Test unbound key
    event = KeyEvent(key_code=ord('x'), modifiers=ModifierKey.NONE, char='x')
    assert is_input_event_for_action(event, 'quit', config_manager) is False
    
    # Test None event
    assert is_input_event_for_action(None, 'quit', config_manager) is False
    
    print("✓ is_input_event_for_action test passed")


def test_is_input_event_for_action_with_selection():
    """Test checking if event matches action with selection requirements."""
    print("Testing is_input_event_for_action_with_selection...")
    
    # Mock config manager
    class MockConfigManager:
        def is_key_bound_to_action_with_selection(self, key_char, action, has_selection):
            # Simple mock:
            # - 'copy_files' requires selection
            # - 'quit' works regardless of selection
            # - 'create_directory' requires no selection
            if action == 'copy_files':
                return key_char == 'c' and has_selection
            elif action == 'quit':
                return key_char == 'q'
            elif action == 'create_directory':
                return key_char == 'm' and not has_selection
            return False
    
    config_manager = MockConfigManager()
    
    # Test copy_files (requires selection)
    event = KeyEvent(key_code=ord('c'), modifiers=ModifierKey.NONE, char='c')
    assert is_input_event_for_action_with_selection(event, 'copy_files', True, config_manager) is True
    assert is_input_event_for_action_with_selection(event, 'copy_files', False, config_manager) is False
    
    # Test quit (works regardless)
    event = KeyEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
    assert is_input_event_for_action_with_selection(event, 'quit', True, config_manager) is True
    assert is_input_event_for_action_with_selection(event, 'quit', False, config_manager) is True
    
    # Test create_directory (requires no selection)
    event = KeyEvent(key_code=ord('m'), modifiers=ModifierKey.NONE, char='m')
    assert is_input_event_for_action_with_selection(event, 'create_directory', False, config_manager) is True
    assert is_input_event_for_action_with_selection(event, 'create_directory', True, config_manager) is False
    
    # Test None event
    assert is_input_event_for_action_with_selection(None, 'quit', False, config_manager) is False
    
    print("✓ is_input_event_for_action_with_selection test passed")


def test_modifier_checks():
    """Test modifier key checking functions."""
    print("Testing modifier key checks...")
    
    # Ctrl modifier
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.CONTROL, char='a')
    assert has_modifier(event, ModifierKey.CONTROL) is True
    assert has_modifier(event, ModifierKey.ALT) is False
    assert has_modifier(event, ModifierKey.SHIFT) is False
    assert is_ctrl_key(event) is True
    assert is_alt_key(event) is False
    assert is_shift_key(event) is False
    
    # Alt modifier
    event = KeyEvent(key_code=ord('b'), modifiers=ModifierKey.ALT, char='b')
    assert has_modifier(event, ModifierKey.ALT) is True
    assert has_modifier(event, ModifierKey.CONTROL) is False
    assert is_alt_key(event) is True
    assert is_ctrl_key(event) is False
    
    # Shift modifier
    event = KeyEvent(key_code=KeyCode.TAB, modifiers=ModifierKey.SHIFT)
    assert has_modifier(event, ModifierKey.SHIFT) is True
    assert has_modifier(event, ModifierKey.CONTROL) is False
    assert is_shift_key(event) is True
    assert is_ctrl_key(event) is False
    
    # Multiple modifiers (Ctrl+Alt)
    event = KeyEvent(key_code=ord('c'), modifiers=ModifierKey.CONTROL | ModifierKey.ALT, char='c')
    assert has_modifier(event, ModifierKey.CONTROL) is True
    assert has_modifier(event, ModifierKey.ALT) is True
    assert is_ctrl_key(event) is True
    assert is_alt_key(event) is True
    
    # No modifiers
    event = KeyEvent(key_code=ord('d'), modifiers=ModifierKey.NONE, char='d')
    assert has_modifier(event, ModifierKey.CONTROL) is False
    assert is_ctrl_key(event) is False
    
    # None event
    assert has_modifier(None, ModifierKey.CONTROL) is False
    assert is_ctrl_key(None) is False
    
    print("✓ Modifier check test passed")


def test_printable_checks():
    """Test printable key checking function."""
    print("Testing printable key checks...")
    
    # Printable character
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert is_printable_char(event) is True
    
    # Special key (not printable)
    event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
    assert is_printable_char(event) is False
    
    # Both char and key_code (printable takes precedence)
    event = KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE, char='x')
    assert is_printable_char(event) is True
    
    # Empty char
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='')
    assert is_printable_char(event) is False
    
    # None event
    assert is_printable_char(None) is False
    
    print("✓ Printable key check test passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 60)
    print("Running TFM Input Utils Tests")
    print("=" * 60)
    print()
    
    test_input_event_to_key_char_printable()
    test_input_event_to_key_char_special_keys()
    test_input_event_to_key_char_with_modifiers()
    test_input_event_to_key_char_edge_cases()
    test_is_input_event_for_key()
    test_is_input_event_for_action()
    test_is_input_event_for_action_with_selection()
    test_modifier_checks()
    test_printable_checks()
    
    print()
    print("=" * 60)
    print("All TFM Input Utils Tests Passed! ✓")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
