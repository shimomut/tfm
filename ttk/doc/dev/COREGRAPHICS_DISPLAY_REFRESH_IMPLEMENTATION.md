# CoreGraphics Backend Display Refresh Implementation

## Overview

This document describes the implementation of display refresh operations for the CoreGraphics backend. These operations control when and how the character grid is rendered to the screen, enabling efficient updates and proper integration with the Cocoa event loop.

## Requirements

This implementation satisfies the following requirements:
- **Requirement 8.4**: Display updates through setNeedsDisplay_
- **Requirement 10.3**: Full and regional refresh support

## Architecture

The display refresh system consists of two main operations:

1. **Full Display Refresh** (`refresh()`): Marks the entire view for redraw
2. **Regional Display Refresh** (`refresh_region()`): Marks only a specific region for redraw

Both operations integrate with Cocoa's display update mechanism through the `setNeedsDisplay_` family of methods.

## Implementation Details

### Full Display Refresh

The `refresh()` method marks the entire view as needing display:

```python
def refresh(self) -> None:
    """
    Refresh the entire window to display all pending changes.
    
    Marks the entire view as needing display, which triggers the Cocoa
    event loop to call drawRect_ on the next display cycle. This causes
    all pending changes to the character grid to be rendered to the screen.
    """
    if self.view:
        self.view.setNeedsDisplay_(True)
```

**Key Points:**
- Checks if view exists before calling (handles initialization edge cases)
- Uses `setNeedsDisplay_(True)` to mark entire view
- Does not immediately redraw - waits for next display cycle
- Efficient for full-screen updates

### Regional Display Refresh

The `refresh_region()` method marks only a specific rectangular region:

```python
def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
    """
    Refresh a specific region of the window.
    
    Marks a specific rectangular region of the view as needing display.
    This is more efficient than refreshing the entire window when only
    a small region has changed.
    
    Args:
        row: Starting row of the region
        col: Starting column of the region
        height: Height of the region in characters
        width: Width of the region in characters
    """
    if self.view:
        # Calculate pixel coordinates for the region
        x = col * self.char_width
        y = (self.rows - row - height) * self.char_height
        pixel_width = width * self.char_width
        pixel_height = height * self.char_height
        
        # Create NSRect for the region
        region_rect = Cocoa.NSMakeRect(x, y, pixel_width, pixel_height)
        
        # Mark the region as needing display
        self.view.setNeedsDisplayInRect_(region_rect)
```

**Key Points:**
- Converts character coordinates to pixel coordinates
- Applies coordinate system transformation (y-axis inversion)
- Uses `setNeedsDisplayInRect_()` for efficiency
- More efficient than full refresh for small updates

### Coordinate Transformation

The regional refresh requires coordinate transformation because:
- TTK uses top-left origin (row 0 at top)
- CoreGraphics uses bottom-left origin (y=0 at bottom)

**Transformation Formula:**
```python
x = col * char_width
y = (rows - row - height) * char_height
```

**Example:**
For a 24-row grid with 20-pixel character height:
- TTK region at row 2, height 5
- Pixel y = (24 - 2 - 5) * 20 = 17 * 20 = 340
- This places the region correctly in CoreGraphics coordinates

### Window Initialization

During initialization, the view is connected to the window and the window is shown:

```python
def _create_window(self) -> None:
    # ... window creation code ...
    
    # Create and set up the custom TTKView
    content_rect = self.window.contentView().frame()
    self.view = TTKView.alloc().initWithFrame_backend_(content_rect, self)
    self.window.setContentView_(self.view)
    
    # Show the window
    self.window.makeKeyAndOrderFront_(None)
```

**Key Points:**
- View is created with window's content rect dimensions
- View is set as window's content view with `setContentView_()`
- Window is shown with `makeKeyAndOrderFront_(None)`
- Window becomes key (receives keyboard input) and front (visible)

## Integration with Cocoa Event Loop

The refresh operations integrate with Cocoa's display update mechanism:

1. **Application calls refresh()**: Marks view as needing display
2. **Cocoa event loop processes**: Schedules display update
3. **drawRect_ is called**: View renders the character grid
4. **Display updates**: User sees the changes

This deferred rendering approach:
- Prevents redundant redraws
- Batches multiple updates efficiently
- Integrates smoothly with macOS window management

## Usage Patterns

### Pattern 1: Full Screen Update
```python
backend.clear()
backend.draw_text(0, 0, "Hello, World!", 0, 0)
backend.refresh()  # Update entire display
```

### Pattern 2: Regional Update
```python
backend.draw_text(10, 20, "Status: OK", 0, 0)
backend.refresh_region(10, 20, 1, 11)  # Update only status line
```

### Pattern 3: Multiple Updates
```python
backend.draw_text(0, 0, "Line 1", 0, 0)
backend.draw_text(1, 0, "Line 2", 0, 0)
backend.draw_text(2, 0, "Line 3", 0, 0)
backend.refresh()  # Single refresh for all changes
```

### Pattern 4: Efficient Partial Updates
```python
# Update multiple small regions
backend.draw_text(5, 10, "Region 1", 0, 0)
backend.refresh_region(5, 10, 1, 8)

backend.draw_text(10, 40, "Region 2", 0, 0)
backend.refresh_region(10, 40, 1, 8)
```

## Performance Considerations

### When to Use Full Refresh
- Clearing the entire screen
- Drawing complex layouts
- Initial display setup
- When most of the screen changes

### When to Use Regional Refresh
- Updating status lines
- Cursor movement
- Small text changes
- Incremental updates

### Optimization Tips
1. **Batch updates**: Make multiple drawing calls, then one refresh
2. **Use regional refresh**: For small updates (< 10% of screen)
3. **Avoid redundant refreshes**: Don't call refresh after every draw
4. **Let Cocoa coalesce**: Multiple refresh calls in same event cycle are merged

## Testing

### Unit Tests
The implementation includes comprehensive unit tests:
- `test_refresh_marks_entire_view_for_display`: Verifies full refresh
- `test_refresh_handles_no_view`: Tests edge case handling
- `test_refresh_region_marks_specific_region`: Verifies regional refresh
- `test_refresh_region_calculates_correct_coordinates`: Tests coordinate transformation
- `test_view_connected_to_window_during_initialization`: Verifies view setup
- `test_window_shown_during_initialization`: Verifies window display

### Verification Script
Run `ttk/test/verify_coregraphics_display_refresh.py` to:
- Visually verify refresh operations
- Test full and regional refreshes
- Confirm window visibility
- Validate coordinate transformation

## Error Handling

The implementation handles edge cases gracefully:

1. **No View**: Both refresh methods check if view exists
2. **Invalid Coordinates**: Regional refresh uses calculated coordinates
3. **Initialization Order**: View is created before any refresh calls

## Comparison with Other Backends

### Curses Backend
- Uses `stdscr.refresh()` for full refresh
- Uses `stdscr.noutrefresh()` + `curses.doupdate()` for efficiency
- Similar deferred rendering model

### Metal Backend
- Uses `setNeedsDisplay()` on MTKView
- Similar Cocoa integration
- More complex due to GPU rendering pipeline

## Future Enhancements

Potential improvements:
1. **Dirty Region Tracking**: Track which cells changed, refresh only those
2. **Automatic Batching**: Automatically batch multiple small refreshes
3. **Refresh Throttling**: Limit refresh rate for performance
4. **Damage Rectangles**: Use multiple damage rectangles for complex updates

## References

- Apple Documentation: [NSView setNeedsDisplay:](https://developer.apple.com/documentation/appkit/nsview/1483360-setneedsdisplay)
- Apple Documentation: [NSView setNeedsDisplayInRect:](https://developer.apple.com/documentation/appkit/nsview/1483475-setneedsdisplayinrect)
- Apple Documentation: [NSWindow makeKeyAndOrderFront:](https://developer.apple.com/documentation/appkit/nswindow/1419208-makekeyandorderfront)
- Requirements: 8.4, 10.3
