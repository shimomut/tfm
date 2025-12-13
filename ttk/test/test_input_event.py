"""
Unit tests for TTK input event system.
"""

import sys
import os

# Add parent directory to path to allow importing ttk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ttk.input_event import KeyCode, ModifierKey, InputEvent


def test_keycode_values():
    """Test that KeyCode enum has expected values."""
    assert KeyCode.ENTER == 10
    assert KeyCode.ESCAPE == 27
    assert KeyCode.BACKSPACE == 127
    assert KeyCode.TAB == 9
    
    # Arrow keys
    assert KeyCode.UP == 1000
    assert KeyCode.DOWN == 1001
    assert KeyCode.LEFT == 1002
    assert KeyCode.RIGHT == 1003
    
    # Function keys
    assert KeyCode.F1 == 1100
    assert KeyCode.F12 == 1111
    
    # Editing keys
    assert KeyCode.INSERT == 1200
    assert KeyCode.DELETE == 1201
    assert KeyCode.HOME == 1202
    assert KeyCode.END == 1203
    assert KeyCode.PAGE_UP == 1204
    assert KeyCode.PAGE_DOWN == 1205
    
    # Special markers
    assert KeyCode.MOUSE == 2000
    assert KeyCode.RESIZE == 3000


def test_modifier_key_values():
    """Test that ModifierKey enum has expected values."""
    assert ModifierKey.NONE == 0
    assert ModifierKey.SHIFT == 1
    assert ModifierKey.CONTROL == 2
    assert ModifierKey.ALT == 4
    assert ModifierKey.COMMAND == 8


def test_modifier_key_combinations():
    """Test that modifier keys can be combined with bitwise OR."""
    combined = ModifierKey.SHIFT | ModifierKey.CONTROL
    assert combined == 3
    
    combined = ModifierKey.CONTROL | ModifierKey.ALT
    assert combined == 6
    
    combined = ModifierKey.SHIFT | ModifierKey.CONTROL | ModifierKey.ALT
    assert combined == 7


def test_input_event_creation():
    """Test creating InputEvent instances."""
    # Printable character
    event = InputEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert event.key_code == ord('a')
    assert event.modifiers == ModifierKey.NONE
    assert event.char == 'a'
    assert event.mouse_row is None
    assert event.mouse_col is None
    assert event.mouse_button is None
    
    # Special key
    event = InputEvent(key_code=KeyCode.UP, modifiers=ModifierKey.SHIFT)
    assert event.key_code == KeyCode.UP
    assert event.modifiers == ModifierKey.SHIFT
    assert event.char is None
    
    # Mouse event
    event = InputEvent(
        key_code=KeyCode.MOUSE,
        modifiers=ModifierKey.NONE,
        mouse_row=10,
        mouse_col=20,
        mouse_button=1
    )
    assert event.key_code == KeyCode.MOUSE
    assert event.mouse_row == 10
    assert event.mouse_col == 20
    assert event.mouse_button == 1


def test_is_printable():
    """Test is_printable() method."""
    # Printable character
    event = InputEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert event.is_printable() is True
    
    # Special key
    event = InputEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
    assert event.is_printable() is False
    
    # Empty char
    event = InputEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='')
    assert event.is_printable() is False
    
    # Multi-character string (shouldn't happen, but test it)
    event = InputEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='ab')
    assert event.is_printable() is False


def test_is_special_key():
    """Test is_special_key() method."""
    # Special keys (>= 1000)
    event = InputEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
    assert event.is_special_key() is True
    
    event = InputEvent(key_code=KeyCode.F1, modifiers=ModifierKey.NONE)
    assert event.is_special_key() is True
    
    event = InputEvent(key_code=KeyCode.DELETE, modifiers=ModifierKey.NONE)
    assert event.is_special_key() is True
    
    # Printable characters (< 1000)
    event = InputEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert event.is_special_key() is False
    
    event = InputEvent(key_code=KeyCode.ENTER, modifiers=ModifierKey.NONE)
    assert event.is_special_key() is False


def test_has_modifier():
    """Test has_modifier() method."""
    # Single modifier
    event = InputEvent(key_code=ord('a'), modifiers=ModifierKey.SHIFT, char='A')
    assert event.has_modifier(ModifierKey.SHIFT) is True
    assert event.has_modifier(ModifierKey.CONTROL) is False
    assert event.has_modifier(ModifierKey.ALT) is False
    
    # Multiple modifiers
    event = InputEvent(
        key_code=ord('a'),
        modifiers=ModifierKey.SHIFT | ModifierKey.CONTROL,
        char='A'
    )
    assert event.has_modifier(ModifierKey.SHIFT) is True
    assert event.has_modifier(ModifierKey.CONTROL) is True
    assert event.has_modifier(ModifierKey.ALT) is False
    
    # No modifiers
    event = InputEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert event.has_modifier(ModifierKey.SHIFT) is False
    assert event.has_modifier(ModifierKey.CONTROL) is False


def test_input_event_with_all_modifiers():
    """Test InputEvent with all modifier keys pressed."""
    event = InputEvent(
        key_code=ord('a'),
        modifiers=ModifierKey.SHIFT | ModifierKey.CONTROL | ModifierKey.ALT | ModifierKey.COMMAND,
        char='A'
    )
    assert event.has_modifier(ModifierKey.SHIFT) is True
    assert event.has_modifier(ModifierKey.CONTROL) is True
    assert event.has_modifier(ModifierKey.ALT) is True
    assert event.has_modifier(ModifierKey.COMMAND) is True


if __name__ == '__main__':
    # Run all tests
    test_keycode_values()
    test_modifier_key_values()
    test_modifier_key_combinations()
    test_input_event_creation()
    test_is_printable()
    test_is_special_key()
    test_has_modifier()
    test_input_event_with_all_modifiers()
    
    print("All tests passed!")
