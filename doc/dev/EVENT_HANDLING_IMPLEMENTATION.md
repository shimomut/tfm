# Event Handling Implementation

## Overview

This document describes the implementation of TFM's event handling system, including the separation of CharEvent and KeyEvent, the callback-based event delivery system, and how to integrate event handling into TFM components.

## Architecture

### Event Type Hierarchy

```
Event (base class)
├── KeyEvent (command keys, shortcuts)
├── CharEvent (text input) [NEW]
├── MouseEvent (mouse input)
└── SystemEvent (resize, close)
```

### Event Flow

#### Terminal Mode (Curses Backend)

```
User Input
    ↓
Curses Backend
    ├── getch() → KeyEvent
    └── Deliver via callback
    ↓
TFMEventCallback
    ├── on_key_event() → handle_command()
    │   ├── Command matched? → Return True
    │   └── Not matched? → Return False
    └── on_char_event() → active_text_widget.handle_key()
```

#### Desktop Mode (CoreGraphics Backend)

```
User Input
    ↓
macOS Event System
    ↓
CoreGraphics Backend
    ├── keyDown: → KeyEvent
    └── Deliver via callback
    ↓
TFMEventCallback
    ├── on_key_event() → handle_command()
    │   ├── Command matched? → Return True
    │   └── Not matched? → Return False
    ↓
macOS Text Input System
    ├── interpretKeyEvents:
    └── insertText: → CharEvent
    ↓
TFMEventCallback
    └── on_char_event() → active_text_widget.handle_key()
```

## Implementation Details

### CharEvent Class

**Location:** `ttk/input_event.py`

```python
@dataclass
class CharEvent:
    """Represents a character input event for text entry."""
    char: str  # Single Unicode character (required)
    
    def __post_init__(self):
        """Validate that char is non-empty."""
        if not self.char:
            raise ValueError("CharEvent.char must be non-empty")
```

**Key Points:**
- `char` is required and must be non-empty
- Validation in `__post_init__` ensures CharEvent is always valid
- Used exclusively for text input, not commands

### EventCallback Interface

**Location:** `ttk/renderer.py`

```python
class EventCallback:
    """Callback interface for event delivery."""
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle a key event. Return True if consumed."""
        return False
    
    def on_char_event(self, event: CharEvent) -> bool:
        """Handle a character event. Return True if consumed."""
        return False
    
    def on_system_event(self, event: SystemEvent) -> bool:
        """Handle a system event. Return True if consumed."""
        return False
```

**Key Points:**
- Return `True` if event is consumed (handled)
- Return `False` if event is not consumed
- Backends use return value to determine if further processing is needed

### Backend Implementation

#### Curses Backend

**Location:** `ttk/backends/curses_backend.py`

```python
class CursesBackend(Renderer):
    def get_event(self, timeout: int = -1) -> Optional[InputEvent]:
        """Get the next input event with callback support."""
        # Poll for input
        key = self.stdscr.getch()
        if key == -1:
            return None

        # Create KeyEvent
        event = KeyEvent(key_code=key)

        # Add char for printable characters
        if 32 <= key <= 126:
            char = chr(key)
            event.char = char
            
            # Create CharEvent and invoke callback
            char_event = CharEvent(char=char)
            if self.callback:
                self.callback.on_event(char_event)

        # Invoke callback with KeyEvent
        if self.callback:
            self.callback.on_event(event)

        return event
```

**Key Points:**
- Always generates KeyEvent for all input
- Creates CharEvent for printable characters
- Invokes callback with both CharEvent and KeyEvent
- Returns KeyEvent for backward compatibility

#### CoreGraphics Backend

**Location:** `ttk/backends/coregraphics_backend.py`

```python
class TTKView(Cocoa.NSView):
    def keyDown_(self, event):
        """Handle key down event from macOS."""
        key_event = self.backend._translate_event(event)
        
        if key_event and self.backend.event_callback:
            consumed = self.backend.event_callback.on_key_event(key_event)
            if consumed:
                return
        
        # Not consumed - pass to input system
        self.interpretKeyEvents_([event])
    
    def insertText_(self, string):
        """Handle character input from macOS."""
        for char in string:
            char_event = CharEvent(char=char)
            if self.backend.event_callback:
                self.backend.event_callback.on_char_event(char_event)
```

**Key Points:**
- `keyDown:` delivers KeyEvent via callback
- If not consumed, calls `interpretKeyEvents:`
- macOS translates to character via `insertText:`
- `insertText:` delivers CharEvent via callback

### TFM Application Layer

#### TFMEventCallback

**Location:** `src/tfm_main.py`

```python
class TFMEventCallback(EventCallback):
    """Event callback implementation for TFM."""
    
    def __init__(self, app):
        self.app = app
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle KeyEvent - return True if consumed."""
        return self.app.handle_command(event)
    
    def on_char_event(self, event: CharEvent) -> bool:
        """Handle CharEvent - pass to active text widget."""
        if self.app.active_text_widget:
            return self.app.active_text_widget.handle_key(event)
        return False
    
    def on_system_event(self, event: SystemEvent) -> bool:
        """Handle SystemEvent (resize, close, etc.)."""
        if event.is_resize():
            self.app.handle_resize()
            return True
        elif event.is_close():
            self.app.quit()
            return True
        return False
```

**Key Points:**
- Implements EventCallback interface
- Routes KeyEvent to command handler
- Routes CharEvent to active text widget
- Routes SystemEvent to appropriate handlers

#### Command Handler

**Location:** `src/tfm_main.py`

```python
def handle_command(self, event: KeyEvent) -> bool:
    """Handle command keys. Return True if consumed."""
    # Only handle KeyEvent
    if not isinstance(event, KeyEvent):
        return False
    
    # Handle commands
    if event.char == 'q' or event.char == 'Q':
        self.quit()
        return True
    elif event.char == 'a' or event.char == 'A':
        self.select_all()
        return True
    elif event.key_code == KeyCode.UP:
        self.move_cursor_up()
        return True
    # ... other commands
    
    return False  # Not consumed
```

**Key Points:**
- Only handles KeyEvent (isinstance check)
- Returns True when command is executed
- Returns False when command is not recognized
- Unconsumed KeyEvent can be translated to CharEvent

#### Text Input Widget

**Location:** `src/tfm_single_line_text_edit.py`

```python
def handle_key(self, event, handle_vertical_nav=False) -> bool:
    """Handle both KeyEvent and CharEvent."""
    if not event:
        return False
    
    # Handle CharEvent - text input
    if isinstance(event, CharEvent):
        return self.insert_char(event.char)
    
    # Handle KeyEvent - navigation and editing commands
    if isinstance(event, KeyEvent):
        if event.key_code == KeyCode.LEFT:
            return self.move_cursor_left()
        elif event.key_code == KeyCode.RIGHT:
            return self.move_cursor_right()
        elif event.key_code == KeyCode.HOME:
            return self.move_cursor_home()
        elif event.key_code == KeyCode.END:
            return self.move_cursor_end()
        elif event.key_code == KeyCode.BACKSPACE:
            return self.backspace()
        elif event.key_code == KeyCode.DELETE:
            return self.delete_char_at_cursor()
    
    return False
```

**Key Points:**
- Handles both CharEvent and KeyEvent
- CharEvent → insert character
- KeyEvent → navigation and editing commands
- No longer handles printable characters in KeyEvent branch

## Migration Guide

### From Polling to Callbacks

**Old Code (Polling):**
```python
while running:
    event = backend.get_event()
    if event:
        if event.char == 'q':
            quit()
        elif event.is_printable():
            insert_char(event.char)
```

**New Code (Callbacks):**
```python
class MyCallback(EventCallback):
    def on_key_event(self, event: KeyEvent) -> bool:
        if event.char == 'q':
            quit()
            return True
        return False
    
    def on_char_event(self, event: CharEvent) -> bool:
        insert_char(event.char)
        return True

callback = MyCallback()
backend.set_event_callback(callback)
while running:
    backend.get_event()  # Events delivered via callbacks
```

### Adding isinstance Checks

**Old Code:**
```python
def handle_key(self, event):
    if event.char == 'q':
        quit()
    elif event.is_printable():
        insert_char(event.char)
```

**New Code:**
```python
def handle_key(self, event):
    if isinstance(event, CharEvent):
        insert_char(event.char)
    elif isinstance(event, KeyEvent):
        if event.char == 'q':
            quit()
```

### Updating Command Handlers

**Old Code:**
```python
def handle_command(self, event):
    if event.char == 'q':
        quit()
    elif event.char == 'a':
        select_all()
```

**New Code:**
```python
def handle_command(self, event: KeyEvent) -> bool:
    if not isinstance(event, KeyEvent):
        return False
    
    if event.char == 'q':
        quit()
        return True
    elif event.char == 'a':
        select_all()
        return True
    
    return False
```

## Testing

### Unit Tests

**Test CharEvent Creation:**
```python
def test_char_event_creation():
    event = CharEvent(char='a')
    assert event.char == 'a'
    assert isinstance(event, CharEvent)

def test_char_event_requires_char():
    with pytest.raises(ValueError):
        CharEvent(char='')
```

**Test Event Handling:**
```python
def test_text_edit_handles_char_event():
    editor = SingleLineTextEdit()
    event = CharEvent(char='x')
    result = editor.handle_key(event)
    assert result == True
    assert editor.get_text() == 'x'

def test_text_edit_handles_key_event():
    editor = SingleLineTextEdit(initial_text='hello')
    editor.set_cursor_pos(5)
    event = KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE)
    result = editor.handle_key(event)
    assert result == True
    assert editor.get_cursor_pos() == 4
```

### Integration Tests

**Test Command Execution:**
```python
def test_command_workflow():
    backend = CursesBackend()
    file_manager = FileManager()
    
    # Simulate pressing 'q' to quit
    event = KeyEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
    file_manager.handle_command(event)
    
    assert file_manager.should_quit == True
```

**Test Text Input:**
```python
def test_text_input_workflow():
    editor = SingleLineTextEdit()
    
    # Type "hello"
    for char in "hello":
        event = CharEvent(char=char)
        editor.handle_key(event)
    
    assert editor.get_text() == "hello"
```

## Best Practices

### 1. Always Use isinstance Checks

```python
# ✅ Good
if isinstance(event, CharEvent):
    handle_char(event.char)
elif isinstance(event, KeyEvent):
    handle_key(event.key_code)

# ❌ Bad
if hasattr(event, 'char'):
    handle_char(event.char)
```

### 2. Return Consumption Status

```python
# ✅ Good
def handle_command(self, event: KeyEvent) -> bool:
    if event.char == 'q':
        self.quit()
        return True  # Consumed
    return False  # Not consumed

# ❌ Bad
def handle_command(self, event: KeyEvent):
    if event.char == 'q':
        self.quit()
    # No return value
```

### 3. Handle Both Event Types in Text Widgets

```python
# ✅ Good
def handle_key(self, event):
    if isinstance(event, CharEvent):
        return self.insert_char(event.char)
    elif isinstance(event, KeyEvent):
        if event.key_code == KeyCode.LEFT:
            return self.move_cursor_left()
    return False

# ❌ Bad
def handle_key(self, event):
    if event.is_printable():
        return self.insert_char(event.char)
    # Doesn't handle CharEvent explicitly
```

### 4. Validate CharEvent Creation

```python
# ✅ Good
if char and len(char) == 1 and char.isprintable():
    event = CharEvent(char=char)

# ❌ Bad
event = CharEvent(char='')  # Raises ValueError
```

### 5. Use Callbacks for New Code

```python
# ✅ Good (new code)
class MyCallback(EventCallback):
    def on_key_event(self, event: KeyEvent) -> bool:
        return self.handle_command(event)
    
    def on_char_event(self, event: CharEvent) -> bool:
        return self.handle_text_input(event)

backend.set_event_callback(MyCallback())

# ✅ OK (legacy code)
while running:
    event = backend.get_event()
    if event:
        handle_event(event)
```

## Troubleshooting

### Problem: CharEvent not generated

**Cause**: KeyEvent is being consumed by command handler

**Solution**: Ensure command handler returns False for unrecognized keys

### Problem: Text appears twice

**Cause**: Both KeyEvent and CharEvent are being handled

**Solution**: Remove printable character handling from KeyEvent branch

### Problem: Commands don't work in text fields

**Cause**: Text widget is consuming all KeyEvents

**Solution**: Text widget should only consume navigation keys, not command keys

### Problem: Modifier keys create CharEvent

**Cause**: Not checking for modifiers before creating CharEvent

**Solution**: Check for Ctrl, Alt, Cmd modifiers before creating CharEvent

## See Also

- [TTK Event System Documentation](../../ttk/doc/EVENT_SYSTEM.md) - TTK event system details
- [TTK API Reference](../../ttk/doc/API_REFERENCE.md) - Complete API documentation
- [Event Handling Feature](../EVENT_HANDLING_FEATURE.md) - User-facing documentation
