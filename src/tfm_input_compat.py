"""
Input compatibility utilities for TFM

Provides backward compatibility helpers for transitioning from integer key codes
to KeyEvent objects.
"""

from ttk import KeyEvent, KeyCode, ModifierKey


def ensure_input_event(event):
    """
    Ensure the input is a KeyEvent object, converting from integer if needed.
    
    This provides backward compatibility for code that still passes integer key codes.
    
    Args:
        event: Either a KeyEvent object or an integer key code
    
    Returns:
        KeyEvent object
    """
    if isinstance(event, KeyEvent):
        return event
    
    if isinstance(event, int):
        # Convert integer key code to KeyEvent
        if 32 <= event <= 126:  # Printable ASCII character
            char = chr(event)
            return KeyEvent(key_code=event, modifiers=ModifierKey.NONE, char=char)
        else:  # Special key or non-printable
            return KeyEvent(key_code=event, modifiers=ModifierKey.NONE)
    
    # If it's neither KeyEvent nor int, return as-is and let caller handle it
    return event
