"""
TTK Event Module

This module defines the event system for TTK, providing a unified
representation of user input, system events, and mouse events across all backends.
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional


class KeyCode(IntEnum):
    """Standard key codes for special keys."""
    # Printable characters use their Unicode code points
    
    # Special keys
    ENTER = 10
    ESCAPE = 27
    BACKSPACE = 127
    TAB = 9
    
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
    Represents a keyboard input event.
    
    This class captures keyboard events including regular key presses,
    special keys (arrows, function keys, etc.), and modifier key states.
    """
    key_code: int  # KeyCode value or Unicode code point
    modifiers: int  # Bitwise OR of ModifierKey values
    char: Optional[str] = None  # Character for printable keys
    
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
    
    @property
    def key_code(self) -> int:
        """Backward compatibility: return event_type as key_code."""
        return self.event_type
    
    @property
    def modifiers(self) -> int:
        """Backward compatibility: system events have no modifiers."""
        return ModifierKey.NONE
    
    @property
    def char(self) -> Optional[str]:
        """Backward compatibility: system events have no character."""
        return None
    
    def is_resize(self) -> bool:
        """Check if this is a window resize event."""
        return self.event_type == SystemEventType.RESIZE
    
    def is_close(self) -> bool:
        """Check if this is a window close event."""
        return self.event_type == SystemEventType.CLOSE
