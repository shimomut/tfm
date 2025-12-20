# Window Resize Snap-to-Grid Fix

## Problem

Window resizing needed to:
1. Snap to character grid boundaries during resize (TFM is TUI-based)
2. Keep opposite edges fixed when dragging left/top edges

The original implementation tried to manually adjust the window frame during resize, which caused erratic behavior.

## Solution

**Use macOS's native `setResizeIncrements_` to constrain window resizing to character grid boundaries.**

This is the proper macOS way to handle grid-based window resizing. By setting resize increments to the character cell size, the OS automatically:
- Snaps window size to multiples of character dimensions
- Respects which edge the user is dragging
- Keeps opposite edges fixed

### Implementation

**In `initialize()` method:**
```python
# Set resize increments to snap to character grid
resize_increment = Cocoa.NSMakeSize(self.char_width, self.char_height)
self.window.setResizeIncrements_(resize_increment)
```

**In `windowDidResize_()` method:**
```python
# Simply update grid dimensions - no manual frame adjustment needed
# The OS handles snapping via setResizeIncrements_
new_cols = max(1, new_width // self.char_width)
new_rows = max(1, new_height // self.char_height)
```

This ensures:
- ✅ Window snaps to character grid during resize
- ✅ Only the dragged edge moves
- ✅ Opposite edge stays fixed
- ✅ Smooth, native macOS resize behavior
- ✅ Perfect for TUI applications

## Key Insight

The problem with manual frame adjustment was that `windowDidResize_` is called AFTER the window has already been resized. Trying to adjust the frame at that point causes both edges to move.

By using `setResizeIncrements_`, we tell the OS to constrain the resize DURING the drag operation, before `windowDidResize_` is called. This is the correct approach and provides native macOS behavior.

## Testing

### Unit Tests

All existing resize tests pass:
- `test/test_coregraphics_resize_event.py` - Resize event generation
- `test/test_coregraphics_resize_on_restore.py` - Window geometry persistence

### Manual Testing

Test the resize behavior manually:
1. Run any TFM demo (e.g., `python3 demo/demo_coregraphics_resize.py`)
2. Drag each edge (top, bottom, left, right) and corners
3. Verify window snaps to character grid during drag
4. Verify only the dragged edge moves (opposite edge stays fixed)
5. Window should have no gaps at edges

## Related Files

- `ttk/backends/coregraphics_backend.py` - Implementation
  - `initialize()` - Sets resize increments
  - `TTKWindowDelegate.windowDidResize_()` - Updates grid dimensions
- `test/test_coregraphics_resize_event.py` - Resize event tests
- `test/test_coregraphics_resize_on_restore.py` - Window persistence tests

## Benefits

**Pros:**
- Native macOS behavior using proper API
- Simple, clean implementation
- No complex edge detection needed
- OS handles all the hard work
- Perfect for TUI applications

**Cons:**
- None - this is the correct approach
