"""
TFM Input Event Utilities

This module provides helper functions for working with TTK KeyEvent objects
in the context of TFM's key binding system.
"""

from ttk import KeyEvent, KeyCode, ModifierKey, CharEvent


def input_event_to_key_char(event):
    """
    Convert a KeyEvent to a key character string for TFM key binding lookup.
    
    Args:
        event: KeyEvent from TTK renderer
        
    Returns:
        str: Key character string, or None if event cannot be converted
        
    Examples:
        - Printable character: 'a', 'A', '1', '/'
        - Special keys: 'KEY_UP', 'KEY_DOWN', 'KEY_ENTER'
        - Modified keys: 'CTRL_A', 'ALT_X'
    """
    if not event:
        return None
    
    # CharEvent should not be used for key bindings (it's for text input only)
    if isinstance(event, CharEvent):
        return None
    
    # Only handle KeyEvent for key bindings
    if not isinstance(event, KeyEvent):
        return None
    
    # Handle printable characters
    if event.char:
        # Check for modifier keys
        if event.modifiers & ModifierKey.CONTROL:
            # Ctrl+key combinations
            return f'CTRL_{event.char.upper()}'
        elif event.modifiers & ModifierKey.ALT:
            # Alt+key combinations
            return f'ALT_{event.char.upper()}'
        else:
            # Plain character
            # For alphabet characters, normalize to uppercase for case-insensitive matching
            if event.char.isalpha():
                return event.char.upper()
            else:
                return event.char
    
    # Handle special keys
    if event.key_code:
        # Map KeyCode to TFM key binding names
        # Use short form for keys that have them (HOME, END, etc.)
        # Use KEY_ prefix for others for curses compatibility
        key_name_map = {
            KeyCode.UP: 'KEY_UP',
            KeyCode.DOWN: 'KEY_DOWN',
            KeyCode.LEFT: 'KEY_LEFT',
            KeyCode.RIGHT: 'KEY_RIGHT',
            KeyCode.ENTER: 'KEY_ENTER',
            KeyCode.ESCAPE: 'KEY_ESCAPE',
            KeyCode.BACKSPACE: 'KEY_BACKSPACE',
            KeyCode.DELETE: 'KEY_DC',
            KeyCode.INSERT: 'KEY_IC',
            KeyCode.HOME: 'HOME',  # Use short form for compatibility with TFM config
            KeyCode.END: 'END',    # Use short form for compatibility with TFM config
            KeyCode.PAGE_UP: 'KEY_PPAGE',
            KeyCode.PAGE_DOWN: 'KEY_NPAGE',
            KeyCode.TAB: 'KEY_TAB',
            KeyCode.F1: 'KEY_F1',
            KeyCode.F2: 'KEY_F2',
            KeyCode.F3: 'KEY_F3',
            KeyCode.F4: 'KEY_F4',
            KeyCode.F5: 'KEY_F5',
            KeyCode.F6: 'KEY_F6',
            KeyCode.F7: 'KEY_F7',
            KeyCode.F8: 'KEY_F8',
            KeyCode.F9: 'KEY_F9',
            KeyCode.F10: 'KEY_F10',
            KeyCode.F11: 'KEY_F11',
            KeyCode.F12: 'KEY_F12',
        }
        
        key_name = key_name_map.get(event.key_code)
        if key_name:
            # Check for modifier keys with special keys
            if event.modifiers & ModifierKey.CONTROL:
                return f'CTRL_{key_name}'
            elif event.modifiers & ModifierKey.ALT:
                return f'ALT_{key_name}'
            elif event.modifiers & ModifierKey.SHIFT:
                # Shift with special keys
                return f'SHIFT_{key_name}'
            else:
                return key_name
    
    return None
