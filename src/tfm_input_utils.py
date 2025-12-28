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


def is_input_event_for_key(event, key_char):
    """
    Check if a KeyEvent matches a specific key character.
    
    Args:
        event: KeyEvent from TTK renderer
        key_char: Key character string to match against
        
    Returns:
        bool: True if event matches key_char
        
    Examples:
        >>> event = KeyEvent(char='a', key_code=ord('a'), modifiers=ModifierKey.NONE)
        >>> is_input_event_for_key(event, 'a')
        True
        >>> is_input_event_for_key(event, 'A')
        False
    """
    if not event or not key_char:
        return False
    
    event_key = input_event_to_key_char(event)
    return event_key == key_char


def is_input_event_for_action(event, action, config_manager):
    """
    Check if a KeyEvent matches a configured action.
    
    Args:
        event: KeyEvent from TTK renderer
        action: Action name to check
        config_manager: ConfigManager instance for key binding lookup
        
    Returns:
        bool: True if event is bound to the action
        
    Examples:
        >>> event = KeyEvent(char='q', key_code=ord('q'), modifiers=ModifierKey.NONE)
        >>> is_input_event_for_action(event, 'quit', config_manager)
        True
    """
    if not event:
        return False
    
    # Use new API: find_action_for_event with has_selection=True/False doesn't matter
    # since we're checking if the action matches regardless of selection
    key_bindings = config_manager.get_key_bindings()
    found_action = key_bindings.find_action_for_event(event, has_selection=True)
    if found_action == action:
        return True
    
    # Also check with has_selection=False in case selection requirement differs
    found_action = key_bindings.find_action_for_event(event, has_selection=False)
    return found_action == action


def is_input_event_for_action_with_selection(event, action, has_selection, config_manager):
    """
    Check if a KeyEvent matches a configured action and respects selection requirements.
    
    Args:
        event: KeyEvent from TTK renderer
        action: Action name to check
        has_selection: Whether files are currently selected
        config_manager: ConfigManager instance for key binding lookup
        
    Returns:
        bool: True if event is bound to the action and selection requirement is met
        
    Examples:
        >>> event = KeyEvent(char='c', key_code=ord('c'), modifiers=ModifierKey.NONE)
        >>> is_input_event_for_action_with_selection(event, 'copy_files', True, config_manager)
        True
        >>> is_input_event_for_action_with_selection(event, 'copy_files', False, config_manager)
        False
    """
    if not event:
        return False
    
    # Use new API: find_action_for_event respects selection requirements
    key_bindings = config_manager.get_key_bindings()
    found_action = key_bindings.find_action_for_event(event, has_selection)
    return found_action == action


def has_modifier(event, modifier):
    """
    Check if a KeyEvent has a specific modifier key pressed.
    
    Args:
        event: KeyEvent from TTK renderer
        modifier: ModifierKey flag to check
        
    Returns:
        bool: True if modifier is pressed
        
    Examples:
        >>> event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.CONTROL, char='a')
        >>> has_modifier(event, ModifierKey.CONTROL)
        True
        >>> has_modifier(event, ModifierKey.ALT)
        False
    """
    if not event:
        return False
    
    return bool(event.modifiers & modifier)


def is_ctrl_key(event):
    """
    Check if a KeyEvent has Ctrl modifier.
    
    Args:
        event: KeyEvent from TTK renderer
        
    Returns:
        bool: True if Ctrl is pressed
    """
    return has_modifier(event, ModifierKey.CONTROL)


def is_alt_key(event):
    """
    Check if a KeyEvent has Alt modifier.
    
    Args:
        event: KeyEvent from TTK renderer
        
    Returns:
        bool: True if Alt is pressed
    """
    return has_modifier(event, ModifierKey.ALT)


def is_shift_key(event):
    """
    Check if a KeyEvent has Shift modifier.
    
    Args:
        event: KeyEvent from TTK renderer
        
    Returns:
        bool: True if Shift is pressed
    """
    return has_modifier(event, ModifierKey.SHIFT)


def is_printable_char(event):
    """
    Check if a KeyEvent represents a printable character.
    
    Args:
        event: KeyEvent from TTK renderer
        
    Returns:
        bool: True if event has a printable character
    """
    if not event:
        return False
    # Only KeyEvent has is_printable() method
    if not isinstance(event, KeyEvent):
        return False
    return event.is_printable()
