"""
TTK Event Module

This module defines the event system for TTK, providing a unified
representation of user input, system events, and mouse events across all backends.
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional


class KeyCode(IntEnum):
    """Standard key codes for keyboard keys."""
    
    # Special keys
    ENTER = 10
    ESCAPE = 27
    BACKSPACE = 127
    TAB = 9
    
    # Space key (using Unicode code point)
    SPACE = 32
    
    # Arrow keys
    UP = 1000
    DOWN = 1001
    LEFT = 1002
    RIGHT = 1003
    
    # Function keys
    F1 = 1100
    F2 = 1101
    F3 = 1102
    F4 = 1103
    F5 = 1104
    F6 = 1105
    F7 = 1106
    F8 = 1107
    F9 = 1108
    F10 = 1109
    F11 = 1110
    F12 = 1111
    
    # Editing keys
    INSERT = 1200
    DELETE = 1201
    HOME = 1202
    END = 1203
    PAGE_UP = 1204
    PAGE_DOWN = 1205
    
    # Letter keys (physical keys, case handled by Shift modifier)
    # Range: 2000-2025
    A = 2000
    B = 2001
    C = 2002
    D = 2003
    E = 2004
    F = 2005
    G = 2006
    H = 2007
    I = 2008
    J = 2009
    K = 2010
    L = 2011
    M = 2012
    N = 2013
    O = 2014
    P = 2015
    Q = 2016
    R = 2017
    S = 2018
    T = 2019
    U = 2020
    V = 2021
    W = 2022
    X = 2023
    Y = 2024
    Z = 2025
    
    # Digit keys (physical keys, symbols handled by Shift modifier)
    # Range: 2100-2109
    DIGIT_0 = 2100
    DIGIT_1 = 2101
    DIGIT_2 = 2102
    DIGIT_3 = 2103
    DIGIT_4 = 2104
    DIGIT_5 = 2105
    DIGIT_6 = 2106
    DIGIT_7 = 2107
    DIGIT_8 = 2108
    DIGIT_9 = 2109
    
    # Symbol/Punctuation keys (physical keys)
    # Range: 2200-2299
    MINUS = 2200          # - and _
    EQUAL = 2201          # = and +
    LEFT_BRACKET = 2202   # [ and {
    RIGHT_BRACKET = 2203  # ] and }
    BACKSLASH = 2204      # \ and |
    SEMICOLON = 2205      # ; and :
    QUOTE = 2206          # ' and "
    COMMA = 2207          # , and <
    PERIOD = 2208         # . and >
    SLASH = 2209          # / and ?
    GRAVE = 2210          # ` and ~
    


class SystemEventType(IntEnum):
    """Event types for system events."""
    RESIZE = 3000
    CLOSE = 3001


class ModifierKey(IntEnum):
    """Modifier key flags (can be combined with bitwise OR)."""
    NONE = 0
    SHIFT = 1
    CONTROL = 2
    ALT = 4
    COMMAND = 8  # macOS Command key


@dataclass
class Event:
    """
    Base class for all events (keyboard, mouse, system).
    
    This is the abstract base for all event types in TTK. Specific event types
    like KeyEvent, MouseEvent, and SystemEvent inherit from this class.
    """
    pass


@dataclass
class KeyEvent(Event):
    """
    Represents a keyboard command event.
    
    KeyEvent is generated for:
    - Special keys (arrows, function keys, etc.)
    - Printable keys with command modifiers (Ctrl, Alt, Cmd)
    - Command shortcuts (Q to quit, A to select all, etc.)
    
    This class captures keyboard events including regular key presses,
    special keys (arrows, function keys, etc.), and modifier key states.
    
    Examples:
        Letter keys without Shift:
            KeyEvent(key_code=KeyCode.A, modifiers=ModifierKey.NONE, char='a')
            KeyEvent(key_code=KeyCode.Z, modifiers=ModifierKey.NONE, char='z')
        
        Letter keys with Shift:
            KeyEvent(key_code=KeyCode.A, modifiers=ModifierKey.SHIFT, char='A')
            KeyEvent(key_code=KeyCode.Z, modifiers=ModifierKey.SHIFT, char='Z')
        
        Digit keys without Shift:
            KeyEvent(key_code=KeyCode.DIGIT_5, modifiers=ModifierKey.NONE, char='5')
            KeyEvent(key_code=KeyCode.DIGIT_0, modifiers=ModifierKey.NONE, char='0')
        
        Digit keys with Shift (symbols):
            KeyEvent(key_code=KeyCode.DIGIT_5, modifiers=ModifierKey.SHIFT, char='%')
            KeyEvent(key_code=KeyCode.DIGIT_1, modifiers=ModifierKey.SHIFT, char='!')
        
        Symbol keys without Shift:
            KeyEvent(key_code=KeyCode.MINUS, modifiers=ModifierKey.NONE, char='-')
            KeyEvent(key_code=KeyCode.EQUAL, modifiers=ModifierKey.NONE, char='=')
            KeyEvent(key_code=KeyCode.SEMICOLON, modifiers=ModifierKey.NONE, char=';')
        
        Symbol keys with Shift:
            KeyEvent(key_code=KeyCode.MINUS, modifiers=ModifierKey.SHIFT, char='_')
            KeyEvent(key_code=KeyCode.EQUAL, modifiers=ModifierKey.SHIFT, char='+')
            KeyEvent(key_code=KeyCode.SEMICOLON, modifiers=ModifierKey.SHIFT, char=':')
        
        Space key:
            KeyEvent(key_code=KeyCode.SPACE, modifiers=ModifierKey.NONE, char=' ')
        
        Control combinations:
            KeyEvent(key_code=KeyCode.A, modifiers=ModifierKey.CONTROL, char='\x01')
            KeyEvent(key_code=KeyCode.C, modifiers=ModifierKey.CONTROL, char='\x03')
        
        Special keys:
            KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE, char=None)
            KeyEvent(key_code=KeyCode.F1, modifiers=ModifierKey.NONE, char=None)
            KeyEvent(key_code=KeyCode.ENTER, modifiers=ModifierKey.NONE, char='\n')
    """
    key_code: int  # KeyCode value or Unicode code point
    modifiers: int  # Bitwise OR of ModifierKey values
    char: Optional[str] = None  # Character for printable keys (legacy)
    
    def is_printable(self) -> bool:
        """Check if this is a printable character."""
        return self.char is not None and len(self.char) == 1
    
    def is_special_key(self) -> bool:
        """Check if this is a special key (arrow, function, etc.)."""
        return self.key_code >= 1000
    
    def has_modifier(self, modifier: ModifierKey) -> bool:
        """Check if a specific modifier key is pressed."""
        return (self.modifiers & modifier) != 0


@dataclass
class CharEvent(Event):
    """
    Represents a character input event for text entry.
    
    CharEvent is generated when the user types a printable character
    without command modifiers (Ctrl, Alt, Cmd). It is used by text
    input widgets to insert characters into text fields.
    """
    char: str  # The character to insert (single Unicode character)
    
    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"CharEvent(char={repr(self.char)})"


@dataclass
class MouseEvent(Event):
    """
    Represents a mouse input event.
    
    This class captures mouse events including clicks, movement, and scrolling.
    """
    mouse_row: int  # Row position of mouse event
    mouse_col: int  # Column position of mouse event
    mouse_button: Optional[int] = None  # 1=left, 2=middle, 3=right, None=movement


@dataclass
class SystemEvent(Event):
    """
    Represents a system event.
    
    This class captures system-level events like window resize, window close,
    and other system notifications.
    """
    event_type: int  # SystemEventType value for system events (e.g., SystemEventType.RESIZE)
    
    def is_resize(self) -> bool:
        """Check if this is a window resize event."""
        return self.event_type == SystemEventType.RESIZE
    
    def is_close(self) -> bool:
        """Check if this is a window close event."""
        return self.event_type == SystemEventType.CLOSE


@dataclass
class MenuEvent(Event):
    """
    Represents a menu selection event.
    
    This class captures menu item selection events from the native menu bar
    in desktop mode. Menu events are generated when a user selects a menu item
    from the application's menu bar.
    """
    item_id: str  # Unique identifier for the selected menu item
    
    def __repr__(self):
        return f"MenuEvent(item_id='{self.item_id}')"
