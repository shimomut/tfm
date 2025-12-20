# TTK Event System

This document describes the TTK event system, including event types, callback-based event delivery, and how to handle keyboard input for both commands and text entry.

## Table of Contents

- [Overview](#overview)
- [Event Types](#event-types)
  - [KeyEvent](#keyevent)
  - [CharEvent](#charevent)
  - [MouseEvent](#mouseevent)
  - [SystemEvent](#systemevent)
- [Event Callback Interface](#event-callback-interface)
- [Backend Event Delivery](#backend-event-delivery)
- [Backward Compatibility](#backward-compatibility)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Overview

TTK provides a callback-based event system that distinguishes between different types of input:

- **KeyEvent**: Command keys and keyboard shortcuts (Q to quit, arrows for navigation, etc.)
- **CharEvent**: Character input for text entry (typing in text fields)
- **MouseEvent**: Mouse clicks and movements (future)
- **SystemEvent**: Window resize, close, and other system events (future)

The callback system allows applications to:
1. Handle commands immediately via `on_key_event()` callback
2. Receive text input via `on_char_event()` callback
3. Distinguish between command keys and text input
4. Support IME (Input Method Editor) for international text input

## Event Types

### KeyEvent

Represents a keyboard command or shortcut.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class KeyEvent:
    """
    Represents a keyboard command event.
    
    KeyEvent is generated for:
    - Special keys (arrows, function keys, etc.)
    - Printable keys with command modifiers (Ctrl, Alt, Cmd)
    - Command shortcuts (Q to quit, A to select all, etc.)
    """
    key_code: int  # KeyCode value or Unicode code point
    modifiers: int  # Bitwise OR of ModifierKey values
    char: Optional[str] = None  # Character for printable keys (legacy)
```

**Attributes:**
- `key_code`: The key code (KeyCode enum value or Unicode code point)
- `modifiers`: Bitwise OR of ModifierKey values (SHIFT, CONTROL, ALT, COMMAND)
- `char`: Optional character representation (for printable keys, legacy compatibility)

**Methods:**
- `is_printable() -> bool`: Check if this is a printable character
- `is_special_key() -> bool`: Check if this is a special key (arrow, function, etc.)
- `has_modifier(modifier: ModifierKey) -> bool`: Check if a specific modifier is pressed

**Example:**
```python
from ttk import KeyEvent, KeyCode, ModifierKey

# Arrow key
event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)

# Ctrl+C
event = KeyEvent(key_code=ord('c'), modifiers=ModifierKey.CONTROL, char='c')

# Function key
event = KeyEvent(key_code=KeyCode.F1, modifiers=ModifierKey.NONE)
```

### CharEvent

Represents a character intended for text input.

```python
from dataclasses import dataclass

@dataclass
class CharEvent:
    """
    Represents a character input event for text entry.
    
    CharEvent is generated when the user types a printable character
    without command modifiers (Ctrl, Alt, Cmd). It is used by text
    input widgets to insert characters into text fields.
    """
    char: str  # The character to insert (single Unicode character)
    
    def __post_init__(self):
        """Validate that char is non-empty."""
        if not self.char:
            raise ValueError("CharEvent.char must be non-empty")
```

**Attributes:**
- `char`: A single Unicode character string (required, must be non-empty)

**When CharEvent is Generated:**
- User types a printable character without command modifiers
- Shift+character for uppercase letters (e.g., Shift+A → 'A')
- Printable characters with Shift for symbols (e.g., Shift+1 → '!')
- Unicode characters from IME input (future)

**When CharEvent is NOT Generated:**
- Ctrl+character (generates KeyEvent)
- Alt+character (generates KeyEvent)
- Cmd+character on macOS (generates KeyEvent)
- Special keys like arrows, function keys (generate KeyEvent)

**Example:**
```python
from ttk import CharEvent

# Lowercase letter
event = CharEvent(char='a')

# Uppercase letter (Shift+A)
event = CharEvent(char='A')

# Symbol (Shift+1)
event = CharEvent(char='!')

# Unicode character
event = CharEvent(char='é')
```

### MouseEvent

Represents a mouse event (future implementation).

```python
@dataclass
class MouseEvent:
    """Represents a mouse event."""
    x: int  # X coordinate
    y: int  # Y coordinate
    button: int  # Mouse button (1=left, 2=middle, 3=right)
    action: str  # Action type ('press', 'release', 'move')
```

### SystemEvent

Represents a system event like window resize or close (future implementation).

```python
@dataclass
class SystemEvent:
    """Represents a system event."""
    event_type: str  # Event type ('resize', 'close', etc.)
    data: dict  # Event-specific data
```

## Event Callback Interface

The `EventCallback` interface defines methods that backends call to deliver events to the application.

```python
from ttk.renderer import EventCallback
from ttk.input_event import KeyEvent, CharEvent

class EventCallback:
    """
    Callback interface for event delivery.
    
    Backends call these methods to deliver events to the application.
    The application implements these methods to handle events.
    """
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """
        Handle a key event.
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed (handled), False otherwise
        """
        return False
    
    def on_char_event(self, event: CharEvent) -> bool:
        """
        Handle a character event.
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if the event was consumed (handled), False otherwise
        """
        return False
    
    def on_system_event(self, event: SystemEvent) -> bool:
        """
        Handle a system event (resize, close, etc.).
        
        Args:
            event: SystemEvent to handle
        
        Returns:
            True if the event was consumed (handled), False otherwise
        """
        return False
```

**Key Concepts:**

1. **Event Consumption**: Return `True` if the event was handled, `False` if not
2. **Event Flow**: KeyEvent → (if not consumed) → CharEvent
3. **Callback Registration**: Use `renderer.set_event_callback(callback)` to register

## Backend Event Delivery

### Terminal Mode (Curses Backend)

In terminal mode, the curses backend delivers events via callbacks:

```
User Input
    ↓
Curses Backend Event Loop
    ├── Poll via getch()
    ├── Generate KeyEvent
    └── Deliver via on_key_event() callback
    ↓
Application Event Handler
    ├── Command matched? → Return True (consumed)
    └── Not matched? → Return False (not consumed)
    ↓
Curses Backend
    ├── KeyEvent consumed? → Done
    └── Not consumed? → Translate to CharEvent
        ↓
        Deliver via on_char_event() callback
        ↓
        Text Input Widget
        └── Handle CharEvent (insert character)
```

**Implementation:**
```python
class CursesBackend(Renderer):
    def run_event_loop_iteration(self, timeout_ms=-1):
        """Process one iteration of events."""
        if self.event_callback is None:
            raise RuntimeError("Event callback not set")
        
        # Set timeout
        if timeout_ms >= 0:
            self.stdscr.timeout(timeout_ms)
        else:
            self.stdscr.timeout(-1)

        try:
            key = self.stdscr.getch()
            if key == -1:  # Timeout
                return

            # Create KeyEvent
            event = KeyEvent(key_code=key)

            # Add char for printable characters
            if 32 <= key <= 126:  # Printable ASCII
                char = chr(key)
                event.char = char

            # Deliver to application
            consumed = self.event_callback.on_key_event(event)
            
            # If not consumed and printable, deliver as CharEvent
            if not consumed and event.char:
                char_event = CharEvent(char=event.char)
                self.event_callback.on_char_event(char_event)

        except curses.error:
            pass
```

### Desktop Mode (CoreGraphics Backend)

In desktop mode, macOS provides native text input translation via NSTextInputClient:

```
User Input
    ↓
macOS Event System
    ↓
CoreGraphics Backend (NSTextInputClient)
    ├── keyDown: → Generate KeyEvent
    └── Deliver via on_key_event() callback
    ↓
Application Event Handler
    ├── Command matched? → Return True (consumed) → Done
    └── Not matched? → Return False (not consumed)
    ↓
macOS Text Input System
    ├── interpretKeyEvents:
    └── insertText: → Generate CharEvent
        ↓
        Deliver via on_char_event() callback
        ↓
        Text Input Widget
        └── Handle CharEvent (insert character)
```

**Implementation:**
```python
class TTKView(Cocoa.NSView):
    """Custom NSView that implements NSTextInputClient protocol."""
    
    def keyDown_(self, event):
        """Handle key down event from macOS."""
        # Translate NSEvent to KeyEvent
        key_event = self.backend._translate_event(event)
        
        if key_event and self.backend.event_callback:
            # Deliver KeyEvent via callback
            consumed = self.backend.event_callback.on_key_event(key_event)
            
            if consumed:
                # Application consumed the event
                return
        
        # Not consumed - pass to input system for character translation
        self.interpretKeyEvents_([event])
    
    def insertText_(self, string):
        """Handle character input from macOS text input system."""
        if not string or len(string) == 0:
            return
        
        # Create CharEvent for each character
        for char in string:
            char_event = CharEvent(char=char)
            
            if self.backend.event_callback:
                self.backend.event_callback.on_char_event(char_event)
```

## Best Practices

### 1. Use isinstance() to Distinguish Event Types

Always use `isinstance()` checks to distinguish between event types:

```python
def handle_event(event):
    if isinstance(event, CharEvent):
        # Handle text input
        insert_character(event.char)
        return True
    elif isinstance(event, KeyEvent):
        # Handle commands
        if event.key_code == KeyCode.UP:
            move_cursor_up()
            return True
    return False
```

### 2. Return True When Event is Consumed

Return `True` from callbacks when the event is handled:

```python
def on_key_event(self, event: KeyEvent) -> bool:
    if event.char == 'q':
        self.quit()
        return True  # Consumed
    return False  # Not consumed
```

### 3. Handle CharEvent in Text Input Widgets

Text input widgets should handle CharEvent for text entry:

```python
class TextEdit:
    def handle_key(self, event):
        if isinstance(event, CharEvent):
            # Insert character at cursor
            self.insert_char(event.char)
            return True
        elif isinstance(event, KeyEvent):
            # Handle navigation commands
            if event.key_code == KeyCode.LEFT:
                self.move_cursor_left()
                return True
        return False
```

### 4. Implement EventCallback for Application

Create an EventCallback implementation for your application:

```python
class MyAppCallback(EventCallback):
    def __init__(self, app):
        self.app = app
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle commands."""
        return self.app.handle_command(event)
    
    def on_char_event(self, event: CharEvent) -> bool:
        """Handle text input."""
        if self.app.active_text_widget:
            return self.app.active_text_widget.handle_key(event)
        return False
    
    def should_close(self) -> bool:
        """Check if application should quit."""
        return self.app.should_quit
```

### 5. Register Callback with Backend

Register your callback with the backend before running the event loop:

```python
# Create backend
backend = CursesBackend()
backend.initialize()

# Create and register callback
callback = MyAppCallback(app)
backend.set_event_callback(callback)

# Run event loop
while not callback.should_close():
    backend.run_event_loop_iteration(timeout_ms=16)
```

## Examples

### Example 1: Simple Text Editor

```python
from ttk import CursesBackend, KeyEvent, CharEvent, KeyCode
from ttk.renderer import EventCallback

class SimpleEditor:
    def __init__(self):
        self.text = ""
        self.cursor = 0
        self.running = True
    
    def insert_char(self, char: str):
        """Insert character at cursor."""
        self.text = self.text[:self.cursor] + char + self.text[self.cursor:]
        self.cursor += 1
    
    def handle_command(self, event: KeyEvent) -> bool:
        """Handle command keys."""
        if event.char == 'q':
            self.running = False
            return True
        elif event.key_code == KeyCode.LEFT and self.cursor > 0:
            self.cursor -= 1
            return True
        elif event.key_code == KeyCode.RIGHT and self.cursor < len(self.text):
            self.cursor += 1
            return True
        elif event.key_code == KeyCode.BACKSPACE and self.cursor > 0:
            self.text = self.text[:self.cursor-1] + self.text[self.cursor:]
            self.cursor -= 1
            return True
        return False

class EditorCallback(EventCallback):
    def __init__(self, editor):
        self.editor = editor
    
    def on_key_event(self, event: KeyEvent) -> bool:
        return self.editor.handle_command(event)
    
    def on_char_event(self, event: CharEvent) -> bool:
        self.editor.insert_char(event.char)
        return True

# Main program
backend = CursesBackend()
backend.initialize()

try:
    editor = SimpleEditor()
    callback = EditorCallback(editor)
    backend.set_event_callback(callback)
    
    while editor.running:
        # Clear and redraw
        backend.clear()
        backend.draw_text(0, 0, editor.text)
        backend.draw_text(0, editor.cursor, "_")  # Cursor
        backend.refresh()
        
        # Get event (delivered via callbacks)
        backend.get_event()

finally:
    backend.shutdown()
```

### Example 2: Command Handler with Text Input

```python
from ttk import KeyEvent, CharEvent, KeyCode
from ttk.renderer import EventCallback

class FileManager:
    def __init__(self):
        self.mode = "command"  # "command" or "search"
        self.search_text = ""
    
    def handle_command(self, event: KeyEvent) -> bool:
        """Handle command mode keys."""
        if self.mode == "command":
            if event.char == '/':
                self.mode = "search"
                self.search_text = ""
                return True
            elif event.char == 'q':
                self.quit()
                return True
        elif self.mode == "search":
            if event.key_code == KeyCode.ENTER:
                self.execute_search()
                self.mode = "command"
                return True
            elif event.key_code == KeyCode.ESCAPE:
                self.mode = "command"
                return True
            elif event.key_code == KeyCode.BACKSPACE:
                if self.search_text:
                    self.search_text = self.search_text[:-1]
                return True
        return False
    
    def handle_text_input(self, event: CharEvent) -> bool:
        """Handle text input in search mode."""
        if self.mode == "search":
            self.search_text += event.char
            return True
        return False

class FileManagerCallback(EventCallback):
    def __init__(self, fm):
        self.fm = fm
    
    def on_key_event(self, event: KeyEvent) -> bool:
        return self.fm.handle_command(event)
    
    def on_char_event(self, event: CharEvent) -> bool:
        return self.fm.handle_text_input(event)
```

### Example 3: Mixed Command and Text Input

```python
from ttk import KeyEvent, CharEvent, KeyCode, ModifierKey

class Dialog:
    def __init__(self):
        self.text = ""
        self.cursor = 0
    
    def handle_event(self, event):
        """Handle both KeyEvent and CharEvent."""
        if isinstance(event, CharEvent):
            # Text input
            self.text = self.text[:self.cursor] + event.char + self.text[self.cursor:]
            self.cursor += 1
            return True
        
        elif isinstance(event, KeyEvent):
            # Commands
            if event.key_code == KeyCode.LEFT:
                if self.cursor > 0:
                    self.cursor -= 1
                return True
            elif event.key_code == KeyCode.RIGHT:
                if self.cursor < len(self.text):
                    self.cursor += 1
                return True
            elif event.key_code == KeyCode.HOME:
                self.cursor = 0
                return True
            elif event.key_code == KeyCode.END:
                self.cursor = len(self.text)
                return True
            elif event.key_code == KeyCode.BACKSPACE:
                if self.cursor > 0:
                    self.text = self.text[:self.cursor-1] + self.text[self.cursor:]
                    self.cursor -= 1
                return True
            elif event.char == 'a' and event.has_modifier(ModifierKey.CONTROL):
                # Ctrl+A: Select all (move to start)
                self.cursor = 0
                return True
            elif event.char == 'e' and event.has_modifier(ModifierKey.CONTROL):
                # Ctrl+E: Move to end
                self.cursor = len(self.text)
                return True
        
        return False
```

## See Also

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Backend Implementation Guide](BACKEND_IMPLEMENTATION_GUIDE.md) - How to implement backends
- [User Guide](USER_GUIDE.md) - Getting started with TTK
