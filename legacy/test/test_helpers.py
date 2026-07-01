"""
Test helper utilities for TFM tests

This module provides helper functions for creating test fixtures and
converting between old curses-style key codes and new TTK KeyEvent objects.

Run with: PYTHONPATH=.:src:ttk pytest test/test_helpers.py -v
"""

from ttk import KeyEvent, KeyCode, ModifierKey


def create_input_event_from_key_code(key_code, modifiers=ModifierKey.NONE):
    """
    Create a KeyEvent from a key code (for backward compatibility with tests).
    
    Args:
        key_code: Integer key code (can be ord('x') for printable chars or KeyCode enum)
        modifiers: ModifierKey flags (default: NONE)
    
    Returns:
        KeyEvent object
    """
    # Check if it's a printable character (32-126 are printable ASCII)
    if isinstance(key_code, int) and 32 <= key_code <= 126:
        char = chr(key_code)
        return KeyEvent(key_code=key_code, modifiers=modifiers, char=char)
    
    # Otherwise treat as special key
    return KeyEvent(key_code=key_code, modifiers=modifiers)


def create_char_event(char, modifiers=ModifierKey.NONE):
    """
    Create a KeyEvent for a printable character.
    
    Args:
        char: Single character string
        modifiers: ModifierKey flags (default: NONE)
    
    Returns:
        KeyEvent object
    """
    return KeyEvent(key_code=ord(char), modifiers=modifiers, char=char)


def create_key_event(key_code, modifiers=ModifierKey.NONE):
    """
    Create a KeyEvent for a special key (arrow, function key, etc.).
    
    Args:
        key_code: KeyCode enum value
        modifiers: ModifierKey flags (default: NONE)
    
    Returns:
        KeyEvent object
    """
    return KeyEvent(key_code=key_code, modifiers=modifiers)
