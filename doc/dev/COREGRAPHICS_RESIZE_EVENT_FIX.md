# CoreGraphics Backend Resize Event Handling Fix

## Overview

This document describes the fix for window resize event handling in the CoreGraphics backend. Previously, the backend handled window resizes internally but did not generate `KeyCode.RESIZE` events for applications to respond to, unlike the curses backend which automatically generates these events.

## Problem

The CoreGraphics backend's `windowDidResize_` delegate method properly handled window resizes by:
- Recalculating grid dimensions
- Updating the character grid
- Clearing caches
- Triggering a redraw

However, it did not generate a `KeyCode.RESIZE` event that applications could receive through `get_input()`. This meant applications couldn't respond to resize events (e.g., redraw their UI, update layouts, etc.).

## Solution

The fix implements a resize event generation mechanism similar to how the curses backend handles `curses.KEY_RESIZE`:

### 1. Added Resize Flag

Added a `resize_pending` flag to track when a resize has occurred:

```python
# In __init__
self.resize_pending = False
```

### 2. Set Flag in Window Delegate

Modified `windowDidResize_` to set the flag when dimensions change:

```python
def windowDidResize_(self, notification):
    # ... existing resize handling ...
    
    if new_cols != self.backend.cols or new_rows != self.backend.rows:
        # ... update grid and clear caches ...
        
        # Set flag to generate resize event in get_input()
        self.backend.resize_pending = True
        
        # Trigger redraw
        self.backend.view.setNeedsDisplay_(True)
```

### 3. Generate Event in get_input()

Modified `get_input()` to check the flag and generate a `KeyCode.RESIZE` event:

```python
def get_input(self, timeout_ms: int = -1) -> Optional[InputEvent]:
    # Check if window was resized
    if self.resize_pending:
        self.resize_pending = False
        return InputEvent(
            key_code=KeyCode.RESIZE,
            modifiers=ModifierKey.NONE,
            char=None
        )
    
    # ... rest of input handling ...
```

## Event Priority

The resize event has priority over other events:
1. Resize events (checked first)
2. Window close events
3. Keyboard/mouse events

This ensures applications receive resize notifications immediately.

## Behavior

### When Window is Resized

1. User drags window edge/corner to resize
2. macOS calls `windowDidResize_` delegate method
3. Backend updates grid dimensions and clears caches
4. Backend sets `resize_pending = True`
5. Next call to `get_input()` returns `KeyCode.RESIZE` event
6. Application receives event and can respond (redraw UI, etc.)

### Consistency with Curses Backend

The behavior now matches the curses backend:
- Both backends generate `KeyCode.RESIZE` events
- Applications use the same code to handle resizes
- `get_dimensions()` returns updated dimensions after resize

## Testing

### Unit Tests

Created `test/test_coregraphics_resize_event.py` with tests for:
- Resize flag initialization
- Resize event generation
- Event priority
- Window delegate behavior
- Cache clearing on resize

### Demo Application

Created `demo/demo_coregraphics_resize.py` to demonstrate:
- Real-time resize event detection
- Dynamic UI updates on resize
- Dimension display updates
- Resize event counter

## Usage Example

Applications can now handle resize events consistently across backends:

```python
# Main event loop
while True:
    event = backend.get_input(timeout_ms=100)
    
    if event is None:
        continue
    
    # Handle resize event
    if event.key_code == KeyCode.RESIZE:
        rows, cols = backend.get_dimensions()
        print(f"Window resized to {rows}x{cols}")
        redraw_interface()
        continue
    
    # Handle other events...
```

## Benefits

1. **Consistent API**: Both backends now generate resize events
2. **Application Control**: Applications can respond to resizes appropriately
3. **Better UX**: Applications can update layouts dynamically
4. **Backend Transparency**: Same code works with both backends

## Files Modified

- `ttk/backends/coregraphics_backend.py`: Added resize event generation
- `test/test_coregraphics_resize_event.py`: Unit tests for resize handling
- `demo/demo_coregraphics_resize.py`: Interactive demo application

## Related Documentation

- `ttk/doc/API_REFERENCE.md`: Documents `KeyCode.RESIZE` event
- `ttk/doc/COREGRAPHICS_BACKEND.md`: CoreGraphics backend documentation
- `ttk/doc/dev/RESIZE_HANDLING_IMPLEMENTATION.md`: Resize handling details
