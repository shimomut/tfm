# Callback Mode Architecture

## Overview

TTK uses a callback-only event delivery architecture. This document explains the design, rationale, and implementation of the callback-only system.

**Historical Note**: TTK previously supported both polling mode (synchronous `get_event()`) and callback mode (asynchronous event delivery). Polling mode was removed in a major version update to simplify the codebase and fully support IME (Input Method Editor) functionality.

## Architecture

### Callback-Only Event Flow

```
┌─────────────────┐
│   Application   │
│  (implements    │
│ EventCallback)  │
└────────┬────────┘
         │
         │ set_event_callback()
         v
┌─────────────────┐
│   Renderer      │
│ (CoreGraphics)  │
└────────┬────────┘
         │
         │ run_event_loop_iteration()
         v
┌─────────────────┐
│   OS Events     │
│  (NSEvent)      │
└────────┬────────┘
         │
         │ Callbacks
         v
┌─────────────────┐
│ EventCallback   │
│  - on_key_event │
│  - on_char_event│
│  - on_resize    │
└─────────────────┘
```

**Key Characteristics:**
- Single event delivery path
- No event queue management
- No conditional logic for mode selection
- Direct callback invocation from OS event handlers
- Mandatory callback setup before event loop

### Event Delivery Sequence

1. **Setup Phase**:
   ```python
   backend = CoreGraphicsBackend()
   callback = MyEventCallback()
   backend.set_event_callback(callback)  # Required
   ```

2. **Event Loop Phase**:
   ```python
   while running:
       backend.run_event_loop_iteration()  # Process OS events
       # Events delivered via callback.on_key_event(), etc.
       update_display()
   ```

3. **Event Handling Phase**:
   ```python
   class MyEventCallback(EventCallback):
       def on_key_event(self, event: KeyEvent) -> bool:
           # Handle key event
           return True  # Consumed
       
       def on_char_event(self, event: CharEvent) -> bool:
           # Handle character input
           return True  # Consumed
   ```

## EventCallback Interface

### Required Methods

```python
class EventCallback(ABC):
    """Interface for receiving events from the renderer."""
    
    @abstractmethod
    def on_key_event(self, event: KeyEvent) -> bool:
        """
        Handle key event.
        
        Args:
            event: Key event to handle
        
        Returns:
            True if event was consumed, False otherwise
        """
        pass
    
    @abstractmethod
    def on_char_event(self, event: CharEvent) -> bool:
        """
        Handle character event (from IME or direct input).
        
        Args:
            event: Character event to handle
        
        Returns:
            True if event was consumed
        """
        pass
    
    @abstractmethod
    def on_resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        pass
    
    @abstractmethod
    def should_close(self) -> bool:
        """Check if application should quit."""
        pass
```

### Event Consumption

The return value from `on_key_event()` and `on_char_event()` indicates whether the event was consumed:

- **True**: Event was handled by the application, no further processing needed
- **False**: Event was not handled, backend may perform additional processing (e.g., IME)

**Example**:
```python
def on_key_event(self, event: KeyEvent) -> bool:
    if event.char == 'q':
        self.quit()
        return True  # Consumed - don't pass to IME
    elif event.key_code == KeyCode.UP:
        self.move_cursor_up()
        return True  # Consumed
    else:
        return False  # Not consumed - may trigger IME
```

## Renderer API

### Required Setup

```python
@abstractmethod
def set_event_callback(self, callback: EventCallback) -> None:
    """
    Set the event callback for event delivery (REQUIRED).
    
    Must be called before run_event_loop() or run_event_loop_iteration().
    All events are delivered via callback methods.
    
    Args:
        callback: EventCallback instance (required, not optional)
    
    Raises:
        ValueError: If callback is None
    """
    pass
```

### Event Loop Methods

```python
@abstractmethod
def run_event_loop(self) -> None:
    """
    Run the main event loop until application quits.
    
    Blocks until the application terminates. Events are delivered
    via the EventCallback set with set_event_callback().
    
    Raises:
        RuntimeError: If event callback not set
    """
    pass

@abstractmethod
def run_event_loop_iteration(self, timeout_ms: int = -1) -> None:
    """
    Process one iteration of the event loop.
    
    Processes pending OS events and delivers them via callbacks.
    Returns after processing events or timeout.
    
    Args:
        timeout_ms: Maximum time to wait for events (-1 = indefinite)
    
    Raises:
        RuntimeError: If event callback not set
    """
    pass
```

### Validation

Both backends validate that the event callback is set:

```python
def run_event_loop_iteration(self, timeout_ms=-1):
    """Process one iteration of events."""
    if self.event_callback is None:
        raise RuntimeError("Event callback not set. Call set_event_callback() first.")
    
    # Process OS events
    self._process_os_events(timeout_ms)
```

## Backend Implementation

### CoreGraphics Backend

The CoreGraphics backend delivers events directly from macOS event handlers:

```python
def keyDown_(self, event):
    """Handle key down event from macOS."""
    # Check if IME composition is active
    if self.hasMarkedText():
        self.interpretKeyEvents_([event])
        return
    
    # Translate to KeyEvent
    key_event = self._translate_event(event)
    
    # Deliver to application (callback always set)
    consumed = self.event_callback.on_key_event(key_event)
    
    if consumed:
        return
    
    # Not consumed - invoke IME
    self.interpretKeyEvents_([event])

def insertText_(self, string):
    """Handle character input from macOS."""
    for char in string:
        char_event = CharEvent(char=char)
        self.event_callback.on_char_event(char_event)
```

**Key Points:**
- No conditional checks for callback existence
- Direct callback invocation
- Event consumption determines further processing
- IME integration via `interpretKeyEvents_()`

### Curses Backend

The Curses backend delivers events from the terminal:

```python
def run_event_loop_iteration(self, timeout_ms=-1):
    """Process one iteration of the event loop."""
    if self.event_callback is None:
        raise RuntimeError("Event callback not set")
    
    # Poll for input
    key = self.stdscr.getch()
    if key == -1:
        return

    # Create and deliver KeyEvent
    event = KeyEvent(key_code=key)
    consumed = self.event_callback.on_key_event(event)
    
    # If not consumed and printable, generate CharEvent
    if not consumed and 32 <= key <= 126:
        char = chr(key)
        char_event = CharEvent(char=char)
        self.event_callback.on_char_event(char_event)
```

**Key Points:**
- Validates callback before processing
- Delivers KeyEvent first
- Generates CharEvent for printable characters if not consumed
- No event queue management

## Why Callback-Only?

### 1. IME Compatibility

**Problem with Polling Mode**: IME (Input Method Editor) requires the application to call `interpretKeyEvents_()` for unconsumed key events. In polling mode, events are queued and returned later, making it impossible to determine if an event was consumed before calling `interpretKeyEvents_()`.

**Callback Solution**: The callback's return value immediately indicates consumption, allowing the backend to call `interpretKeyEvents_()` for unconsumed events.

```python
# Callback mode - IME works correctly
consumed = self.event_callback.on_key_event(key_event)
if not consumed:
    self.interpretKeyEvents_([event])  # Allow IME processing

# Polling mode - IME broken
self.event_queue.append(key_event)  # Can't call interpretKeyEvents_() yet!
return key_event
```

### 2. Code Simplification

**Polling Mode Complexity**:
- Event queue management
- Dual code paths (polling vs callback)
- Conditional logic throughout
- Mode tracking variables
- ~450 lines of code

**Callback-Only Simplicity**:
- Single event delivery path
- No event queue
- No conditional logic
- No mode tracking
- Direct callback invocation

### 3. Architectural Clarity

**Polling Mode Issues**:
- Unclear event ownership (queue vs application)
- Timing ambiguity (when is event consumed?)
- State management complexity
- Testing difficulty (multiple paths)

**Callback-Only Benefits**:
- Clear event ownership (application handles immediately)
- Immediate consumption feedback
- Simple state management
- Easy to test (single path)

### 4. Performance

**Polling Mode Overhead**:
- Event queue allocation and management
- Event copying to/from queue
- Conditional checks on every event
- Mode state checks

**Callback-Only Efficiency**:
- Direct callback invocation
- No intermediate storage
- No conditional overhead
- Minimal state tracking

## Migration from Polling Mode

### Breaking Changes

The following APIs were removed:

1. **`Renderer.get_event()`** - Removed
2. **`Renderer.get_input()`** - Removed (was alias for get_event)
3. **Optional callback parameter** - Now required

### Migration Steps

**Old Code (Polling)**:
```python
backend = CoreGraphicsBackend()

while running:
    event = backend.get_event(timeout_ms=16)
    if event:
        if event.char == 'q':
            quit()
        elif event.is_printable():
            insert_char(event.char)
```

**New Code (Callback)**:
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

backend = CoreGraphicsBackend()
backend.set_event_callback(MyCallback())  # Required

while running:
    backend.run_event_loop_iteration(timeout_ms=16)
```

### Migration Checklist

- [ ] Remove all `get_event()` calls
- [ ] Remove all `get_input()` calls
- [ ] Create EventCallback implementation
- [ ] Call `set_event_callback()` during initialization
- [ ] Update event loop to use `run_event_loop_iteration()`
- [ ] Handle KeyEvent and CharEvent separately
- [ ] Return consumption status from event handlers
- [ ] Test IME functionality (Japanese, Chinese, Korean)

## Testing

### Unit Tests

```python
def test_callback_required():
    """Test that callback is required before event loop."""
    backend = CoreGraphicsBackend()
    
    with pytest.raises(RuntimeError, match="Event callback not set"):
        backend.run_event_loop_iteration()

def test_callback_none_rejected():
    """Test that None callback is rejected."""
    backend = CoreGraphicsBackend()
    
    with pytest.raises(ValueError, match="Event callback cannot be None"):
        backend.set_event_callback(None)

def test_event_delivery():
    """Test that events are delivered via callback."""
    backend = CoreGraphicsBackend()
    capture = EventCapture()
    backend.set_event_callback(capture)
    
    # Simulate key press
    simulate_key_press(backend, 'a')
    
    # Verify delivered via callback
    assert len(capture.events) > 0
    assert capture.events[0][0] == 'key'
```

### Integration Tests

```python
def test_ime_integration():
    """Test IME works with callback mode."""
    backend = CoreGraphicsBackend()
    capture = EventCapture()
    backend.set_event_callback(capture)
    
    # Simulate IME composition
    simulate_ime_composition(backend, "あああ")
    
    # Verify CharEvents delivered
    char_events = [e for e in capture.events if e[0] == 'char']
    assert len(char_events) == 3
    assert ''.join(e[1].char for e in char_events) == "あああ"
```

## Best Practices

### 1. Always Set Callback First

```python
# ✅ Correct
backend = CoreGraphicsBackend()
backend.set_event_callback(MyCallback())
backend.run_event_loop()

# ❌ Wrong - raises RuntimeError
backend = CoreGraphicsBackend()
backend.run_event_loop()  # Error: callback not set
```

### 2. Return Consumption Status

```python
# ✅ Correct
def on_key_event(self, event: KeyEvent) -> bool:
    if self.handle_command(event):
        return True  # Consumed
    return False  # Not consumed

# ❌ Wrong - no return value
def on_key_event(self, event: KeyEvent):
    self.handle_command(event)
    # Missing return statement
```

### 3. Handle Both Event Types

```python
# ✅ Correct
class MyCallback(EventCallback):
    def on_key_event(self, event: KeyEvent) -> bool:
        return self.handle_commands(event)
    
    def on_char_event(self, event: CharEvent) -> bool:
        return self.handle_text_input(event)

# ❌ Wrong - only handles one type
class MyCallback(EventCallback):
    def on_key_event(self, event: KeyEvent) -> bool:
        return self.handle_everything(event)
    
    def on_char_event(self, event: CharEvent) -> bool:
        return False  # Ignores text input!
```

### 4. Validate Callback Implementation

```python
# ✅ Correct - implements all required methods
class MyCallback(EventCallback):
    def on_key_event(self, event: KeyEvent) -> bool:
        return False
    
    def on_char_event(self, event: CharEvent) -> bool:
        return False
    
    def on_resize(self, width: int, height: int) -> None:
        pass
    
    def should_close(self) -> bool:
        return False

# ❌ Wrong - missing methods
class MyCallback(EventCallback):
    def on_key_event(self, event: KeyEvent) -> bool:
        return False
    # Missing other required methods
```

## Troubleshooting

### Problem: RuntimeError - Event callback not set

**Cause**: Calling `run_event_loop()` or `run_event_loop_iteration()` without setting callback.

**Solution**: Call `set_event_callback()` before running event loop:
```python
backend.set_event_callback(MyCallback())
backend.run_event_loop()
```

### Problem: ValueError - Event callback cannot be None

**Cause**: Calling `set_event_callback(None)`.

**Solution**: Provide valid EventCallback instance:
```python
backend.set_event_callback(MyCallback())  # Not None
```

### Problem: IME doesn't work

**Cause**: Event handler consuming all key events (returning True).

**Solution**: Return False for unconsumed events:
```python
def on_key_event(self, event: KeyEvent) -> bool:
    if self.is_command(event):
        self.handle_command(event)
        return True  # Consumed
    return False  # Not consumed - allow IME
```

### Problem: Events not delivered

**Cause**: EventCallback methods not implemented or returning wrong values.

**Solution**: Implement all required methods and return appropriate values:
```python
class MyCallback(EventCallback):
    def on_key_event(self, event: KeyEvent) -> bool:
        # Handle event
        return True  # or False
    
    def on_char_event(self, event: CharEvent) -> bool:
        # Handle event
        return True  # or False
    
    # ... implement other required methods
```

## Performance Considerations

### Event Delivery Overhead

Callback mode has minimal overhead:

1. **Direct invocation**: No queue allocation or management
2. **No copying**: Events passed by reference
3. **No conditionals**: Single code path
4. **Immediate feedback**: Consumption status returned immediately

### Memory Usage

Callback mode uses less memory:

- **No event queue**: Saves queue allocation and event storage
- **No mode tracking**: Saves state variables
- **Simpler backend**: Smaller code footprint

### Latency

Callback mode has lower latency:

- **Immediate delivery**: Events delivered as they occur
- **No queue delay**: No waiting for application to poll
- **Direct processing**: Application handles events immediately

## See Also

- [Event Handling Implementation](EVENT_HANDLING_IMPLEMENTATION.md) - Detailed event handling implementation
- [IME Support Implementation](IME_SUPPORT_IMPLEMENTATION.md) - IME integration details
- [TTK API Reference](../../ttk/doc/API_REFERENCE.md) - Complete API documentation
- [TTK Event System](../../ttk/doc/EVENT_SYSTEM.md) - Event system overview

## References

- TTK Renderer Interface: `ttk/renderer.py`
- CoreGraphics Backend: `ttk/backends/coregraphics_backend.py`
- Curses Backend: `ttk/backends/curses_backend.py`
- TFM Event Callback: `src/tfm_main.py` (TFMEventCallback class)
- Migration Specification: `.kiro/specs/callback-mode-migration/`
