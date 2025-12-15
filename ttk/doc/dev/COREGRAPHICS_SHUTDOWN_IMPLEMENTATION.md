# CoreGraphics Backend Shutdown Implementation

## Overview

This document describes the implementation of the `shutdown()` method for the CoreGraphics backend. The shutdown method is responsible for properly cleaning up all resources and closing the window when the backend is no longer needed.

## Implementation Details

### Shutdown Method

The `shutdown()` method performs cleanup in a specific order to ensure all resources are properly released:

```python
def shutdown(self) -> None:
    """
    Clean up resources and close the window.
    
    This method performs cleanup in the following order:
    1. Close the native window
    2. Clear the view reference
    3. Clear the font reference
    4. Clear the character grid
    5. Clear color pair storage
    6. Reset dimensions
    7. Reset cursor state
    """
```

### Cleanup Order

The cleanup is performed in the following order:

1. **Window Closure**: Close the NSWindow and handle any errors that may occur
2. **View Reference**: Clear the TTKView reference
3. **Font Reference**: Clear the NSFont reference
4. **Character Grid**: Clear the 2D character grid array
5. **Color Pairs**: Clear the color pair dictionary
6. **Dimensions**: Reset rows, cols, char_width, and char_height to 0
7. **Cursor State**: Reset cursor visibility and position

### Error Handling

The shutdown method implements comprehensive error handling to ensure cleanup continues even if errors occur:

```python
# Close the native window
if self.window is not None:
    try:
        self.window.close()
    except (AttributeError, RuntimeError) as e:
        # Window may already be closed or in invalid state
        print(f"Warning: Error closing window during shutdown: {e}")
    except Exception as e:
        # Catch any other unexpected errors during cleanup
        print(f"Warning: Unexpected error closing window: {e}")
    finally:
        self.window = None
```

Key error handling features:

- **Specific Exception Handling**: Catches `AttributeError` and `RuntimeError` specifically for window-related errors
- **Broad Exception Handling**: Catches all other exceptions to prevent shutdown from failing
- **Warning Messages**: Prints warnings for errors but continues cleanup
- **Finally Block**: Ensures window reference is cleared even if errors occur

### Resource Cleanup

After handling the window, the method clears all other resources:

```python
# Clear view reference
self.view = None

# Clear font reference
self.font = None

# Clear character grid
self.grid = []

# Clear color pair storage
self.color_pairs = {}

# Reset dimensions
self.rows = 0
self.cols = 0
self.char_width = 0
self.char_height = 0

# Reset cursor state
self.cursor_visible = False
self.cursor_row = 0
self.cursor_col = 0
```

### Safety Features

The shutdown implementation includes several safety features:

1. **Multiple Calls**: Safe to call multiple times - subsequent calls are no-ops
2. **Partial Initialization**: Works even if only some resources were initialized
3. **No Initialization**: Works even if `initialize()` was never called
4. **Configuration Preservation**: Preserves initial configuration parameters (window_title, font_name, font_size)

## Requirements Validation

This implementation satisfies **Requirement 7.5**:

> WHEN the backend shuts down THEN the system SHALL close the window and release all resources

The implementation:
- ✓ Closes the window using `window.close()`
- ✓ Releases all resource references (window, view, font)
- ✓ Clears all data structures (grid, color_pairs)
- ✓ Resets all state variables (dimensions, cursor state)
- ✓ Handles errors gracefully without crashing

## Testing

### Unit Tests

The implementation is tested by `test_coregraphics_shutdown.py` with the following test cases:

1. **test_shutdown_closes_window**: Verifies window.close() is called
2. **test_shutdown_handles_window_close_error**: Verifies error handling for RuntimeError
3. **test_shutdown_handles_attribute_error**: Verifies error handling for AttributeError
4. **test_shutdown_clears_view**: Verifies view reference is cleared
5. **test_shutdown_clears_font**: Verifies font reference is cleared
6. **test_shutdown_clears_character_grid**: Verifies grid is cleared
7. **test_shutdown_clears_color_pairs**: Verifies color pairs are cleared
8. **test_shutdown_resets_dimensions**: Verifies dimensions are reset to 0
9. **test_shutdown_resets_cursor_state**: Verifies cursor state is reset
10. **test_shutdown_without_initialization**: Verifies works without initialize()
11. **test_shutdown_multiple_times**: Verifies multiple calls are safe
12. **test_shutdown_clears_all_resources_together**: Verifies all resources cleared in one call
13. **test_shutdown_with_partial_initialization**: Verifies works with partial initialization
14. **test_shutdown_preserves_configuration**: Verifies configuration parameters preserved
15. **test_shutdown_handles_unexpected_exception**: Verifies handles unexpected exceptions

All tests pass successfully.

### Verification Script

The `verify_coregraphics_shutdown.py` script provides additional verification:

- Basic shutdown functionality
- Error handling during shutdown
- Multiple shutdown calls
- Shutdown without initialization
- Configuration preservation

## Usage Example

```python
from ttk.backends.coregraphics_backend import CoreGraphicsBackend

# Create and initialize backend
backend = CoreGraphicsBackend(
    window_title="My Application",
    font_name="Menlo",
    font_size=14
)
backend.initialize()

# Use the backend...
backend.draw_text(0, 0, "Hello, World!")
backend.refresh()

# Clean up when done
backend.shutdown()

# Safe to call multiple times
backend.shutdown()  # No-op, no errors
```

## Comparison with Metal Backend

The CoreGraphics shutdown implementation follows the same pattern as the Metal backend:

| Feature | CoreGraphics | Metal |
|---------|-------------|-------|
| Window closure | ✓ | ✓ |
| Error handling | ✓ | ✓ |
| View cleanup | ✓ | ✓ |
| Resource cleanup | ✓ | ✓ |
| Dimension reset | ✓ | ✓ |
| Cursor reset | ✓ | ✓ |
| Multiple calls safe | ✓ | ✓ |
| Configuration preserved | ✓ | ✓ |

The main differences:

- **CoreGraphics**: Clears font reference (NSFont)
- **Metal**: Clears Metal-specific resources (device, pipeline, command queue)

## Implementation Notes

### PyObjC Memory Management

PyObjC handles memory management automatically through reference counting. Setting references to `None` allows PyObjC to properly release the underlying Objective-C objects:

```python
self.window = None  # Releases NSWindow
self.view = None    # Releases TTKView (NSView subclass)
self.font = None    # Releases NSFont
```

### Thread Safety

The shutdown method assumes it's called from the main thread, which is appropriate for Cocoa applications. All Cocoa operations must occur on the main thread.

### Resource Ordering

The cleanup order is important:

1. **Window first**: Close the window before clearing other resources to ensure proper cleanup
2. **View second**: Clear view reference after window is closed
3. **Font third**: Clear font after view (view may reference font)
4. **Data structures last**: Clear grid and color pairs after UI resources

## Future Enhancements

Potential future enhancements to the shutdown implementation:

1. **Event Loop Integration**: Ensure proper integration with NSApplication event loop
2. **Animation Cleanup**: If animations are added, ensure they're stopped during shutdown
3. **Resource Tracking**: Add debug mode to track resource cleanup
4. **Shutdown Callbacks**: Allow applications to register cleanup callbacks

## Related Documentation

- [CoreGraphics Window Creation Implementation](COREGRAPHICS_WINDOW_CREATION_IMPLEMENTATION.md)
<!-- CoreGraphics Initialization documentation not yet created -->
<!-- Metal Shutdown Implementation documentation not yet created -->
<!-- CoreGraphics backend spec files not included in repository -->
<!-- CoreGraphics backend spec files not included in repository -->
