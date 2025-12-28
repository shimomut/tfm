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
from tfm_input_utils import input_event_to_key_char


def test_input_event_to_key_char_printable():
    """Test converting printable character events to key chars."""
    print("Testing input_event_to_key_char with printable characters...")
    
    # Lowercase letter (normalized to uppercase)
    event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
    assert input_event_to_key_char(event) == 'A'
    
    # Uppercase letter
    event = KeyEvent(key_code=ord('A'), modifiers=ModifierKey.NONE, char='A')
    assert input_event_to_key_char(event) == 'A'
    
    # Number (not normalized)
    event = KeyEvent(key_code=ord('1'), modifiers=ModifierKey.NONE, char='1')
    assert input_event_to_key_char(event) == '1'
    
    # Special character (not normalized)
    event = KeyEvent(key_code=ord('/'), modifiers=ModifierKey.NONE, char='/')
    assert input_event_to_key_char(event) == '/'
    
    # Space (not normalized)
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
    
    print()
    print("=" * 60)
    print("All TFM Input Utils Tests Passed! ✓")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
