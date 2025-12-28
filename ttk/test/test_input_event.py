"""
Unit tests for TTK input event system.
"""

import sys
import os

# Add parent directory to path to allow importing ttk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ttk import KeyCode, ModifierKey, KeyEvent, SystemEventType, MouseEvent


def test_keycode_values():
    """Test that KeyCode enum has expected values."""
    # With StrEnum, values are lowercase strings
    assert KeyCode.ENTER == 'enter'
    assert KeyCode.ESCAPE == 'escape'
    assert KeyCode.BACKSPACE == 'backspace'
    assert KeyCode.TAB == 'tab'
    
    # Space key
    assert KeyCode.SPACE == 'space'
    
    # Arrow keys
    assert KeyCode.UP == 'up'
    assert KeyCode.DOWN == 'down'
    assert KeyCode.LEFT == 'left'
    assert KeyCode.RIGHT == 'right'
    
    # Function keys
    assert KeyCode.F1 == 'f1'
    assert KeyCode.F12 == 'f12'
    
    # Editing keys
    assert KeyCode.INSERT == 'insert'
    assert KeyCode.DELETE == 'delete'
    assert KeyCode.HOME == 'home'
    assert KeyCode.END == 'end'
    assert KeyCode.PAGE_UP == 'page_up'
    assert KeyCode.PAGE_DOWN == 'page_down'
    
    # Letter keys
    assert KeyCode.A == 'a'
    assert KeyCode.Z == 'z'
    
    # Digit keys (explicit string values)
    assert KeyCode.DIGIT_0 == '0'
    assert KeyCode.DIGIT_9 == '9'
    
    # Symbol keys
    assert KeyCode.MINUS == 'minus'
    assert KeyCode.GRAVE == 'grave'
    
    # System event types (moved from KeyCode)
    assert SystemEventType.RESIZE == 3000
    assert SystemEventType.CLOSE == 3001


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
    """Test creating KeyEvent instances."""
    # Printable character
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert event.key_code == ord('a')
    assert event.modifiers == ModifierKey.NONE
    assert event.char == 'a'
    
    # Special key
    event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.SHIFT)
    assert event.key_code == KeyCode.UP
    assert event.modifiers == ModifierKey.SHIFT
    assert event.char is None
    
    # Mouse event (separate class now)
    event = MouseEvent(
        mouse_row=10,
        mouse_col=20,
        mouse_button=1
    )
    assert event.mouse_row == 10
    assert event.mouse_col == 20
    assert event.mouse_button == 1


def test_is_printable():
    """Test is_printable() method."""
    # Printable character
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert event.is_printable() is True
    
    # Special key
    event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
    assert event.is_printable() is False
    
    # Empty char
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='')
    assert event.is_printable() is False
    
    # Multi-character string (shouldn't happen, but test it)
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='ab')
    assert event.is_printable() is False


def test_has_modifier():
    """Test has_modifier() method."""
    # Single modifier
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.SHIFT, char='A')
    assert event.has_modifier(ModifierKey.SHIFT) is True
    assert event.has_modifier(ModifierKey.CONTROL) is False
    assert event.has_modifier(ModifierKey.ALT) is False
    
    # Multiple modifiers
    event = KeyEvent(
        key_code=ord('a'),
        modifiers=ModifierKey.SHIFT | ModifierKey.CONTROL,
        char='A'
    )
    assert event.has_modifier(ModifierKey.SHIFT) is True
    assert event.has_modifier(ModifierKey.CONTROL) is True
    assert event.has_modifier(ModifierKey.ALT) is False
    
    # No modifiers
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert event.has_modifier(ModifierKey.SHIFT) is False
    assert event.has_modifier(ModifierKey.CONTROL) is False


def test_input_event_with_all_modifiers():
    """Test KeyEvent with all modifier keys pressed."""
    event = KeyEvent(
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
    test_has_modifier()
    test_input_event_with_all_modifiers()
    
    print("All tests passed!")
