"""
Test helper utilities for TFM tests

This module provides helper functions for creating test fixtures and
converting between old curses-style key codes and new TTK InputEvent objects.
"""

from ttk.input_event import InputEvent, KeyCode, ModifierKey


def create_input_event_from_key_code(key_code, modifiers=ModifierKey.NONE):
    """
    Create an InputEvent from a key code (for backward compatibility with tests).
    
    Args:
        key_code: Integer key code (can be ord('x') for printable chars or KeyCode enum)
        modifiers: ModifierKey flags (default: NONE)
    
    Returns:
        InputEvent object
    """
    # Check if it's a printable character (32-126 are printable ASCII)
    if isinstance(key_code, int) and 32 <= key_code <= 126:
        char = chr(key_code)
        return InputEvent(key_code=key_code, modifiers=modifiers, char=char)
    
    # Otherwise treat as special key
    return InputEvent(key_code=key_code, modifiers=modifiers)


def create_char_event(char, modifiers=ModifierKey.NONE):
    """
    Create an InputEvent for a printable character.
    
    Args:
        char: Single character string
        modifiers: ModifierKey flags (default: NONE)
    
    Returns:
        InputEvent object
    """
    return InputEvent(key_code=ord(char), modifiers=modifiers, char=char)


def create_key_event(key_code, modifiers=ModifierKey.NONE):
    """
    Create an InputEvent for a special key (arrow, function key, etc.).
    
    Args:
        key_code: KeyCode enum value
        modifiers: ModifierKey flags (default: NONE)
    
    Returns:
        InputEvent object
    """
    return InputEvent(key_code=key_code, modifiers=modifiers)
