"""
Input compatibility utilities for TFM

Provides backward compatibility helpers for transitioning from integer key codes
to InputEvent objects.
"""

from ttk.input_event import InputEvent, KeyCode, ModifierKey


def ensure_input_event(event):
    """
    Ensure the input is an InputEvent object, converting from integer if needed.
    
    This provides backward compatibility for code that still passes integer key codes.
    
    Args:
        event: Either an InputEvent object or an integer key code
    
    Returns:
        InputEvent object
    """
    if isinstance(event, InputEvent):
        return event
    
    if isinstance(event, int):
        # Convert integer key code to InputEvent
        if 32 <= event <= 126:  # Printable ASCII character
            char = chr(event)
            return InputEvent(key_code=event, modifiers=ModifierKey.NONE, char=char)
        else:  # Special key or non-printable
            return InputEvent(key_code=event, modifiers=ModifierKey.NONE)
    
    # If it's neither InputEvent nor int, return as-is and let caller handle it
    return event
