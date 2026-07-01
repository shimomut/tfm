# TTK Migration Guide: v0.1.0 to v0.2.0

## Overview

TTK v0.2.0 removes polling mode support and requires callback-only event delivery. This is a **breaking change** that simplifies the architecture and improves maintainability.

**Key Changes:**
- ✅ Callback mode is now the only supported event delivery mechanism
- ❌ Polling mode has been removed (`get_event()` and `get_input()` methods)
- ✅ Event callbacks are now mandatory (not optional)
- ✅ Simpler, more consistent API
- ✅ Full IME (Input Method Editor) support maintained

## Why This Change?

1. **Simplification**: Removes ~450 lines of code and dual code paths
2. **IME Compatibility**: Polling mode was incompatible with IME support
3. **Consistency**: Single event delivery mechanism is easier to understand
4. **Maintenance**: Fewer code paths means fewer bugs and easier maintenance

## Breaking Changes

### 1. Removed Methods

The following methods have been removed from the `Renderer` interface:

```python
# ❌ REMOVED - No longer available
renderer.get_event(timeout_ms=100)
renderer.get_input(timeout_ms=100)
```

### 2. Mandatory Event Callback

Event callbacks are now **required** (not optional):

```python
# ❌ OLD - Callback was optional
renderer.set_event_callback(None)  # This was allowed

# ✅ NEW - Callback is required
renderer.set_event_callback(callback)  # Must provide valid callback
renderer.set_event_callback(None)      # Raises ValueError
```

### 3. Event Loop Changes

The event loop no longer returns events directly:

```python
# ❌ OLD - Polling mode
event = renderer.get_event(timeout_ms=16)
if event:
    handle_event(event)

# ✅ NEW - Callback mode
# Events are delivered via callback methods
renderer.run_event_loop_iteration(timeout_ms=16)
```

## Migration Steps

### Step 1: Create an EventCallback Implementation

Replace polling-based event handling with an `EventCallback` implementation:

**Before (v0.1.0):**
```python
from ttk.backends.curses_backend import CursesBackend
from ttk import KeyCode

renderer = CursesBackend()
renderer.initialize()

# Polling mode
while True:
    event = renderer.get_event(timeout_ms=16)
    
    if event and event.key_code == KeyCode.ESCAPE:
        break
    
    # Draw interface
    renderer.draw_text(0, 0, "Hello")
    renderer.refresh()

renderer.shutdown()
```

**After (v0.2.0):**
```python
from ttk.backends.curses_backend import CursesBackend
from ttk import KeyCode
from ttk.renderer import EventCallback

class MyAppCallback(EventCallback):
    """Event callback for my application."""
    
    def __init__(self):
        self.should_quit = False
    
    def on_key_event(self, event):
        """Handle key events."""
        if event.key_code == KeyCode.ESCAPE:
            self.should_quit = True
            return True  # Event consumed
        return False  # Event not consumed
    
    def on_char_event(self, event):
        """Handle character events (from IME or direct input)."""
        # Handle text input here
        return False
    
    def on_resize(self, width, height):
        """Handle window resize."""
        pass
    
    def should_close(self):
        """Check if application should quit."""
        return self.should_quit

# Create renderer
renderer = CursesBackend()
renderer.initialize()

# Set up callback (REQUIRED)
callback = MyAppCallback()
renderer.set_event_callback(callback)

# Event loop
while not callback.should_quit:
    # Events delivered via callback
    renderer.run_event_loop_iteration(timeout_ms=16)
    
    # Draw interface
    renderer.draw_text(0, 0, "Hello")
    renderer.refresh()

renderer.shutdown()
```

### Step 2: Implement All EventCallback Methods

The `EventCallback` interface requires four methods:

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
            True if event was consumed, False to pass to IME
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

### Step 3: Update Event Loop

Replace `get_event()` calls with `run_event_loop_iteration()`:

**Before (v0.1.0):**
```python
while running:
    event = renderer.get_event(timeout_ms=16)
    
    if event:
        if event.key_code == KeyCode.UP:
            cursor_up()
        elif event.key_code == KeyCode.DOWN:
            cursor_down()
    
    draw_interface()
    renderer.refresh()
```

**After (v0.2.0):**
```python
class MyCallback(EventCallback):
    def __init__(self, app):
        self.app = app
    
    def on_key_event(self, event):
        if event.key_code == KeyCode.UP:
            self.app.cursor_up()
            return True
        elif event.key_code == KeyCode.DOWN:
            self.app.cursor_down()
            return True
        return False
    
    # ... other methods ...

callback = MyCallback(app)
renderer.set_event_callback(callback)

while not callback.should_close():
    renderer.run_event_loop_iteration(timeout_ms=16)
    app.draw_interface()
    renderer.refresh()
```

### Step 4: Handle IME Input

Character events from IME are delivered via `on_char_event()`:

```python
class MyCallback(EventCallback):
    def __init__(self, text_buffer):
        self.text_buffer = text_buffer
    
    def on_key_event(self, event):
        """Handle key events."""
        # Handle special keys (arrows, function keys, etc.)
        if event.key_code == KeyCode.BACKSPACE:
            self.text_buffer.delete_char()
            return True
        
        # Return False to allow IME processing
        return False
    
    def on_char_event(self, event):
        """Handle character events (including IME)."""
        # Insert text from IME or direct input
        self.text_buffer.insert(event.char)
        return True
    
    # ... other methods ...
```

## Common Migration Patterns

### Pattern 1: Simple Key Handler

**Before:**
```python
while True:
    event = renderer.get_event()
    if event and event.key_code == KeyCode.Q:
        break
```

**After:**
```python
class QuitCallback(EventCallback):
    def __init__(self):
        self.quit = False
    
    def on_key_event(self, event):
        if event.key_code == KeyCode.Q:
            self.quit = True
            return True
        return False
    
    def on_char_event(self, event):
        return False
    
    def on_resize(self, width, height):
        pass
    
    def should_close(self):
        return self.quit

callback = QuitCallback()
renderer.set_event_callback(callback)

while not callback.should_close():
    renderer.run_event_loop_iteration()
```

### Pattern 2: Text Input

**Before:**
```python
text = ""
while True:
    event = renderer.get_event()
    if event and event.is_printable():
        text += event.char
```

**After:**
```python
class TextInputCallback(EventCallback):
    def __init__(self):
        self.text = ""
        self.quit = False
    
    def on_key_event(self, event):
        if event.key_code == KeyCode.ESCAPE:
            self.quit = True
            return True
        return False
    
    def on_char_event(self, event):
        # Handles both direct input and IME
        self.text += event.char
        return True
    
    def on_resize(self, width, height):
        pass
    
    def should_close(self):
        return self.quit

callback = TextInputCallback()
renderer.set_event_callback(callback)

while not callback.should_close():
    renderer.run_event_loop_iteration()
    renderer.draw_text(0, 0, callback.text)
    renderer.refresh()
```

### Pattern 3: Menu Navigation

**Before:**
```python
selected = 0
items = ["Option 1", "Option 2", "Option 3"]

while True:
    event = renderer.get_event()
    if event:
        if event.key_code == KeyCode.UP:
            selected = max(0, selected - 1)
        elif event.key_code == KeyCode.DOWN:
            selected = min(len(items) - 1, selected + 1)
        elif event.key_code == KeyCode.ENTER:
            return items[selected]
```

**After:**
```python
class MenuCallback(EventCallback):
    def __init__(self, items):
        self.items = items
        self.selected = 0
        self.result = None
        self.quit = False
    
    def on_key_event(self, event):
        if event.key_code == KeyCode.UP:
            self.selected = max(0, self.selected - 1)
            return True
        elif event.key_code == KeyCode.DOWN:
            self.selected = min(len(self.items) - 1, self.selected + 1)
            return True
        elif event.key_code == KeyCode.ENTER:
            self.result = self.items[self.selected]
            self.quit = True
            return True
        return False
    
    def on_char_event(self, event):
        return False
    
    def on_resize(self, width, height):
        pass
    
    def should_close(self):
        return self.quit

items = ["Option 1", "Option 2", "Option 3"]
callback = MenuCallback(items)
renderer.set_event_callback(callback)

while not callback.should_close():
    renderer.run_event_loop_iteration()
    # Draw menu with callback.selected
    renderer.refresh()

selected_item = callback.result
```

## Testing Your Migration

### Unit Tests

Update your tests to use callback mode:

**Before:**
```python
def test_key_handling():
    renderer = CursesBackend()
    renderer.initialize()
    
    # Simulate key press
    simulate_key(renderer, 'a')
    
    # Get event
    event = renderer.get_event()
    assert event.char == 'a'
```

**After:**
```python
class TestCallback(EventCallback):
    def __init__(self):
        self.events = []
    
    def on_key_event(self, event):
        self.events.append(('key', event))
        return False
    
    def on_char_event(self, event):
        self.events.append(('char', event))
        return False
    
    def on_resize(self, width, height):
        pass
    
    def should_close(self):
        return False

def test_key_handling():
    renderer = CursesBackend()
    renderer.initialize()
    
    callback = TestCallback()
    renderer.set_event_callback(callback)
    
    # Simulate key press
    simulate_key(renderer, 'a')
    
    # Process events
    renderer.run_event_loop_iteration()
    
    # Check callback received event
    assert len(callback.events) > 0
    assert callback.events[0][0] == 'key'
    assert callback.events[0][1].char == 'a'
```

### Integration Tests

Test your full application with callback mode:

```python
def test_application():
    app = MyApplication()
    callback = MyApplicationCallback(app)
    
    renderer = CursesBackend()
    renderer.initialize()
    renderer.set_event_callback(callback)
    
    # Simulate user interaction
    simulate_key_sequence(renderer, ['a', 'b', 'c'])
    
    # Process events
    for _ in range(3):
        renderer.run_event_loop_iteration()
    
    # Verify application state
    assert app.text == "abc"
```

## Error Handling

### Missing Callback Error

If you forget to set a callback, you'll get a clear error:

```python
renderer = CursesBackend()
renderer.initialize()

# ❌ Forgot to set callback
try:
    renderer.run_event_loop_iteration()
except RuntimeError as e:
    print(e)  # "Event callback not set. Call set_event_callback() first."
```

### None Callback Error

If you try to set None as the callback:

```python
renderer = CursesBackend()
renderer.initialize()

# ❌ Trying to set None
try:
    renderer.set_event_callback(None)
except ValueError as e:
    print(e)  # "Event callback cannot be None"
```

## Benefits of Callback Mode

### 1. IME Support

Callback mode enables full IME support for Japanese, Chinese, and Korean input:

```python
class IMECallback(EventCallback):
    def on_key_event(self, event):
        # Special keys handled here
        if event.key_code == KeyCode.BACKSPACE:
            self.delete_char()
            return True
        # Return False to allow IME processing
        return False
    
    def on_char_event(self, event):
        # IME-composed text delivered here
        self.insert_text(event.char)
        return True
```

### 2. Simpler Architecture

No need to manage event queues or check for events:

```python
# Callback mode is straightforward
while not callback.should_close():
    renderer.run_event_loop_iteration()
    draw_interface()
    renderer.refresh()
```

### 3. Better Separation of Concerns

Event handling logic is cleanly separated in the callback:

```python
class AppCallback(EventCallback):
    """All event handling in one place."""
    
    def on_key_event(self, event):
        # Key handling logic
        pass
    
    def on_char_event(self, event):
        # Text input logic
        pass
    
    def on_resize(self, width, height):
        # Resize handling logic
        pass
```

## Troubleshooting

### Problem: "Event callback not set" error

**Solution:** Call `set_event_callback()` before running the event loop:

```python
callback = MyCallback()
renderer.set_event_callback(callback)  # Must call this first
renderer.run_event_loop_iteration()
```

### Problem: Events not being received

**Solution:** Make sure your callback methods return the correct values:

```python
def on_key_event(self, event):
    # Return True if you handled the event
    if event.key_code == KeyCode.ESCAPE:
        self.quit = True
        return True  # ✅ Event consumed
    
    # Return False to allow IME processing
    return False  # ✅ Event not consumed
```

### Problem: IME not working

**Solution:** Return `False` from `on_key_event()` for keys you don't handle:

```python
def on_key_event(self, event):
    # Only handle special keys
    if event.key_code in [KeyCode.UP, KeyCode.DOWN, KeyCode.ESCAPE]:
        # Handle these keys
        return True
    
    # Return False for everything else to allow IME
    return False  # ✅ Allows IME to process the key
```

### Problem: Missing `get_event()` method

**Solution:** This method has been removed. Use callback mode instead:

```python
# ❌ OLD
event = renderer.get_event()

# ✅ NEW
class MyCallback(EventCallback):
    def on_key_event(self, event):
        # Handle event here
        pass

renderer.set_event_callback(MyCallback())
renderer.run_event_loop_iteration()
```

## Version Compatibility

| TTK Version | Polling Mode | Callback Mode | Migration Required |
|-------------|--------------|---------------|-------------------|
| v0.1.0      | ✅ Supported | ✅ Supported  | No                |
| v0.2.0      | ❌ Removed   | ✅ Required   | **Yes**           |

## Getting Help

If you encounter issues during migration:

1. **Check the examples**: Review the updated demo applications in `ttk/demo/`
2. **Read the documentation**: See [USER_GUIDE.md](USER_GUIDE.md) and [API_REFERENCE.md](API_REFERENCE.md)
3. **Report issues**: Open an issue on the project repository with:
   - Your TTK version
   - Code example showing the problem
   - Error messages or unexpected behavior

## Summary

**Key takeaways:**
- ✅ Implement `EventCallback` interface for your application
- ✅ Set callback with `set_event_callback()` before running event loop
- ✅ Use `run_event_loop_iteration()` instead of `get_event()` or `get_input()`
- ✅ Return `False` from `on_key_event()` to allow IME processing
- ✅ Handle text input in `on_char_event()` (includes IME)

**Migration checklist:**
- [ ] Create `EventCallback` implementation
- [ ] Implement all four required methods
- [ ] Replace `get_event()` calls with `run_event_loop_iteration()`
- [ ] Set callback before running event loop
- [ ] Update tests to use callback mode
- [ ] Test IME input (if applicable)
- [ ] Update documentation and examples

Welcome to TTK v0.2.0! The simpler, more consistent API will make your code easier to maintain and understand.
