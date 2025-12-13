# CoreGraphics Backend Cursor Management Implementation

## Overview

This document describes the implementation of cursor management functionality in the CoreGraphics backend for TTK. The cursor management system provides control over cursor visibility and positioning, allowing applications to display a text cursor at any position in the character grid.

## Requirements Addressed

This implementation addresses the Renderer interface requirements for cursor management:
- **Cursor Visibility Control**: Ability to show or hide the text cursor
- **Cursor Positioning**: Ability to position the cursor at any valid grid location
- **Coordinate Clamping**: Graceful handling of out-of-bounds coordinates
- **State Persistence**: Cursor state persists across visibility changes

## Architecture

### State Management

The cursor state is managed through three instance variables in the `CoreGraphicsBackend` class:

```python
# Cursor state
self.cursor_visible = False  # Whether cursor is currently visible
self.cursor_row = 0          # Current cursor row position (0-based)
self.cursor_col = 0          # Current cursor column position (0-based)
```

### Key Components

1. **State Variables**: Track cursor visibility and position
2. **Control Methods**: `set_cursor_visibility()` and `move_cursor()`
3. **Rendering Integration**: Cursor drawing in `TTKView.drawRect_()`
4. **Coordinate Clamping**: Automatic bounds checking

## Implementation Details

### Cursor State Initialization

The cursor state is initialized in the `__init__` method:

```python
def __init__(self, window_title: str = "TTK Window",
             font_name: str = "Menlo", font_size: int = 12):
    # ... other initialization ...
    
    # Cursor state
    self.cursor_visible = False
    self.cursor_row = 0
    self.cursor_col = 0
```

**Initial State**:
- Cursor is hidden by default (`cursor_visible = False`)
- Cursor starts at origin position (0, 0)
- Applications must explicitly show the cursor if needed

### Cursor Visibility Control

The `set_cursor_visibility()` method controls whether the cursor is visible:

```python
def set_cursor_visibility(self, visible: bool) -> None:
    """
    Set cursor visibility.
    
    Controls whether the text cursor is visible in the window. When visible,
    the cursor is drawn as a block at the current cursor position during
    rendering. The cursor position is set using move_cursor().
    
    Args:
        visible: True to show the cursor, False to hide it.
    """
    self.cursor_visible = visible
    # Trigger a redraw to show/hide the cursor
    if self.view:
        self.view.setNeedsDisplay_(True)
```

**Behavior**:
- Updates the `cursor_visible` flag
- Triggers a view refresh to update the display
- Handles missing view gracefully (no exception if view is None)
- Cursor position is preserved when hiding/showing

### Cursor Positioning

The `move_cursor()` method sets the cursor position:

```python
def move_cursor(self, row: int, col: int) -> None:
    """
    Move the cursor to the specified position.
    
    Sets the cursor position in the character grid. The cursor is only
    visible if set_cursor_visibility(True) has been called. Coordinates
    are clamped to valid grid bounds to prevent out-of-bounds errors.
    
    Args:
        row: Row position (0-based, 0 is top)
        col: Column position (0-based, 0 is left)
    """
    # Clamp coordinates to valid grid bounds
    self.cursor_row = max(0, min(row, self.rows - 1))
    self.cursor_col = max(0, min(col, self.cols - 1))
    
    # Trigger a redraw if cursor is visible
    if self.cursor_visible and self.view:
        self.view.setNeedsDisplay_(True)
```

**Coordinate Clamping**:
- Row is clamped to range [0, rows-1]
- Column is clamped to range [0, cols-1]
- Out-of-bounds coordinates are automatically adjusted
- No exceptions are raised for invalid coordinates

**Refresh Optimization**:
- Only triggers refresh if cursor is visible
- Avoids unnecessary redraws when cursor is hidden
- Handles missing view gracefully

### Cursor Rendering

The cursor is rendered in the `TTKView.drawRect_()` method after all character cells are drawn:

```python
def drawRect_(self, rect):
    """Render the character grid."""
    # ... render all character cells ...
    
    # Draw cursor if visible
    if self.backend.cursor_visible:
        # Calculate cursor pixel position
        cursor_x = self.backend.cursor_col * self.backend.char_width
        cursor_y = (self.backend.rows - self.backend.cursor_row - 1) * self.backend.char_height
        
        # Draw cursor as a filled rectangle with inverted colors
        # Use white color for visibility
        cursor_color = Cocoa.NSColor.colorWithRed_green_blue_alpha_(
            1.0, 1.0, 1.0, 0.8  # White with slight transparency
        )
        cursor_color.setFill()
        
        # Create rectangle for the cursor
        cursor_rect = Cocoa.NSMakeRect(
            cursor_x,
            cursor_y,
            self.backend.char_width,
            self.backend.char_height
        )
        Cocoa.NSRectFill(cursor_rect)
```

**Rendering Details**:
- Cursor is drawn after all character cells (appears on top)
- Uses coordinate transformation (TTK top-left to CoreGraphics bottom-left)
- Rendered as a filled rectangle covering one character cell
- Uses white color with 80% opacity for visibility
- Only drawn when `cursor_visible` is True

### Coordinate Transformation

The cursor uses the same coordinate transformation as character rendering:

```
TTK Coordinates (top-left origin):
  (0, 0) = top-left corner
  (row, col) = row down from top, col right from left

CoreGraphics Coordinates (bottom-left origin):
  (0, 0) = bottom-left corner
  y = (rows - row - 1) * char_height
  x = col * char_width
```

**Example Transformations**:
- TTK (0, 0) → CoreGraphics (0, (rows-1) * char_height)
- TTK (rows-1, 0) → CoreGraphics (0, 0)
- TTK (row, col) → CoreGraphics (col * char_width, (rows-row-1) * char_height)

## Usage Examples

### Basic Cursor Display

```python
# Create backend
backend = CoreGraphicsBackend()
backend.initialize()

# Show cursor at origin
backend.set_cursor_visibility(True)
backend.move_cursor(0, 0)
backend.refresh()
```

### Moving the Cursor

```python
# Move cursor to middle of screen
backend.move_cursor(12, 40)
backend.refresh()

# Move cursor to bottom-right
backend.move_cursor(23, 79)
backend.refresh()
```

### Hiding the Cursor

```python
# Hide cursor (position is preserved)
backend.set_cursor_visibility(False)
backend.refresh()

# Move hidden cursor
backend.move_cursor(10, 20)

# Show cursor at new position
backend.set_cursor_visibility(True)
backend.refresh()
```

### Cursor Blinking Effect

```python
import time

# Blink cursor 5 times
for _ in range(5):
    backend.set_cursor_visibility(False)
    backend.refresh()
    time.sleep(0.3)
    
    backend.set_cursor_visibility(True)
    backend.refresh()
    time.sleep(0.3)
```

### Out-of-Bounds Handling

```python
# Coordinates are automatically clamped
backend.move_cursor(-5, 200)  # Clamped to (0, 79)
backend.move_cursor(100, -10)  # Clamped to (23, 0)
backend.refresh()
```

## Testing

### Unit Tests

The implementation includes comprehensive unit tests in `test_coregraphics_cursor_management.py`:

1. **Initial State Tests**:
   - Cursor initially hidden
   - Cursor starts at (0, 0)

2. **Visibility Control Tests**:
   - Show cursor
   - Hide cursor
   - Handle missing view

3. **Positioning Tests**:
   - Move to valid position
   - Clamp row upper bound
   - Clamp row lower bound
   - Clamp column upper bound
   - Clamp column lower bound
   - Clamp both coordinates

4. **Refresh Optimization Tests**:
   - Visible cursor triggers refresh
   - Hidden cursor doesn't trigger refresh

5. **State Persistence Tests**:
   - Position preserved when hiding/showing
   - State persists across operations

### Manual Verification

The `verify_coregraphics_cursor_management.py` script provides visual verification:

1. Shows cursor at origin
2. Moves cursor to various positions
3. Tests coordinate clamping
4. Demonstrates hide/show functionality
5. Shows rapid cursor movement
6. Demonstrates cursor blinking

## Performance Considerations

### Refresh Optimization

The implementation optimizes refresh behavior:

```python
# Only refresh if cursor is visible
if self.cursor_visible and self.view:
    self.view.setNeedsDisplay_(True)
```

**Benefits**:
- Avoids unnecessary redraws when cursor is hidden
- Reduces CPU usage for applications that don't use cursor
- Maintains responsiveness for cursor-heavy applications

### Rendering Efficiency

The cursor is rendered efficiently:
- Single rectangle fill operation
- No complex drawing operations
- Minimal overhead per frame
- Drawn after character cells (no overdraw)

## Compatibility

### Renderer Interface Compliance

The implementation fully complies with the `Renderer` abstract base class:

```python
@abstractmethod
def set_cursor_visibility(self, visible: bool) -> None:
    """Set cursor visibility."""
    pass

@abstractmethod
def move_cursor(self, row: int, col: int) -> None:
    """Move the cursor to the specified position."""
    pass
```

**Compliance Details**:
- Method signatures match exactly
- Behavior matches documentation
- Coordinate system matches TTK conventions
- Error handling matches expected behavior

### Cross-Backend Consistency

The cursor behavior is consistent with the curses backend:

| Feature | CoreGraphics | Curses | Match |
|---------|-------------|--------|-------|
| Initial visibility | Hidden | Hidden | ✓ |
| Initial position | (0, 0) | (0, 0) | ✓ |
| Coordinate clamping | Yes | Yes | ✓ |
| Out-of-bounds handling | Clamp | Ignore | Similar |
| Refresh on change | Yes | Implicit | ✓ |

## Limitations and Future Enhancements

### Current Limitations

1. **Fixed Cursor Style**: Cursor is always a filled block
2. **Fixed Cursor Color**: Cursor is always white with 80% opacity
3. **No Cursor Blinking**: Application must implement blinking manually
4. **No Cursor Shape Options**: Only block cursor is supported

### Potential Enhancements

1. **Cursor Styles**:
   - Block cursor (current)
   - Underline cursor
   - Vertical bar cursor
   - Custom cursor shapes

2. **Cursor Colors**:
   - Configurable cursor color
   - Automatic color inversion based on background
   - Color pair support for cursor

3. **Automatic Blinking**:
   - Built-in cursor blinking
   - Configurable blink rate
   - Blink enable/disable

4. **Cursor Attributes**:
   - Cursor size (half-height, full-height)
   - Cursor thickness (for underline/bar styles)
   - Cursor animation effects

## Conclusion

The cursor management implementation provides a complete and efficient solution for displaying and controlling a text cursor in the CoreGraphics backend. The implementation:

- ✓ Fully implements the Renderer interface
- ✓ Provides robust coordinate clamping
- ✓ Optimizes refresh behavior
- ✓ Maintains state consistency
- ✓ Handles edge cases gracefully
- ✓ Includes comprehensive tests
- ✓ Matches curses backend behavior

The cursor system is ready for use in TTK applications and provides a solid foundation for future enhancements.
