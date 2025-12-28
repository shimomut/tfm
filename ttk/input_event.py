"""
TTK Event Module

This module defines the event system for TTK, providing a unified
representation of user input, system events, and mouse events across all backends.
"""

from enum import IntEnum, StrEnum, auto
from dataclasses import dataclass
from typing import Optional


class KeyCode(StrEnum):
    """Standard key codes for keyboard keys."""
    
    # Special keys
    ENTER = auto()
    ESCAPE = auto()
    BACKSPACE = auto()
    TAB = auto()
    
    # Space key
    SPACE = auto()
    
    # Arrow keys
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    
    # Function keys
    F1 = auto()
    F2 = auto()
    F3 = auto()
    F4 = auto()
    F5 = auto()
    F6 = auto()
    F7 = auto()
    F8 = auto()
    F9 = auto()
    F10 = auto()
    F11 = auto()
    F12 = auto()
    
    # Editing keys
    INSERT = auto()
    DELETE = auto()
    HOME = auto()
    END = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()
    
    # Letter keys (physical keys, case handled by Shift modifier)
    A = auto()
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    F = auto()
    G = auto()
    H = auto()
    I = auto()
    J = auto()
    K = auto()
    L = auto()
    M = auto()
    N = auto()
    O = auto()
    P = auto()
    Q = auto()
    R = auto()
    S = auto()
    T = auto()
    U = auto()
    V = auto()
    W = auto()
    X = auto()
    Y = auto()
    Z = auto()
    
    # Digit keys (physical keys, symbols handled by Shift modifier)
    DIGIT_0 = '0'
    DIGIT_1 = '1'
    DIGIT_2 = '2'
    DIGIT_3 = '3'
    DIGIT_4 = '4'
    DIGIT_5 = '5'
    DIGIT_6 = '6'
    DIGIT_7 = '7'
    DIGIT_8 = '8'
    DIGIT_9 = '9'
    
    # Symbol/Punctuation keys (physical keys)
    MINUS = auto()          # - and _
    EQUAL = auto()          # = and +
    LEFT_BRACKET = auto()   # [ and {
    RIGHT_BRACKET = auto()  # ] and }
    BACKSLASH = auto()      # \ and |
    SEMICOLON = auto()      # ; and :
    QUOTE = auto()          # ' and "
    COMMA = auto()          # , and <
    PERIOD = auto()         # . and >
    SLASH = auto()          # / and ?
    GRAVE = auto()          # ` and ~
    


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
    key_code: str  # KeyCode value (string)
    modifiers: int  # Bitwise OR of ModifierKey values
    char: Optional[str] = None  # Character for printable keys (legacy)
    
    def is_printable(self) -> bool:
        """Check if this is a printable character."""
        return self.char is not None and len(self.char) == 1
    
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
