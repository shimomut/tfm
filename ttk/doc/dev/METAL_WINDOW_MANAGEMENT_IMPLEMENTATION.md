# Metal Backend Window Management Implementation

## Overview

This document describes the implementation of window management functionality for the Metal backend in the TTK library. Window management includes dimension queries, display refresh operations, cursor control, and window resize handling.

## Implementation Date

December 10, 2025

## Requirements Addressed

- **Requirement 3.5**: Metal backend window management
- **Requirement 4.6**: Full window refresh and partial region updates
- **Requirement 8.3**: Dimension query consistency
- **Requirement 8.4**: Handle window resize events and cursor control

## Components Implemented

### 1. Dimension Queries

**Method**: `get_dimensions() -> Tuple[int, int]`

Returns the current character grid dimensions as a tuple of (rows, columns).

**Implementation**:
```python
def get_dimensions(self) -> Tuple[int, int]:
    return (self.rows, self.cols)
```

**Features**:
- Simple accessor for grid dimensions
- Returns dimensions in character cells (not pixels)
- Always returns current grid size

### 2. Display Refresh Operations

**Methods**:
- `refresh() -> None` - Refresh entire window
- `refresh_region(row, col, height, width) -> None` - Refresh specific region

**Implementation**:
- `refresh()` calls `_render_grid()` to render the entire character grid
- `refresh_region()` calls `_render_grid_region()` for optimized partial updates
- Both methods use Metal command buffers to submit rendering commands

**Features**:
- Full window refresh for complete updates
- Partial region refresh for optimization
- GPU-accelerated rendering via Metal

### 3. Cursor Control

**Methods**:
- `set_cursor_visibility(visible: bool) -> None` - Show/hide cursor
- `move_cursor(row: int, col: int) -> None` - Position cursor

**Implementation**:

**Cursor Visibility**:
```python
def set_cursor_visibility(self, visible: bool) -> None:
    self.cursor_visible = visible
```

**Cursor Movement**:
```python
def move_cursor(self, row: int, col: int) -> None:
    # Clamp cursor position to valid grid coordinates
    self.cursor_row = max(0, min(row, self.rows - 1)) if self.rows > 0 else 0
    self.cursor_col = max(0, min(col, self.cols - 1)) if self.cols > 0 else 0
```

**Features**:
- Cursor visibility state stored in `cursor_visible` attribute
- Cursor position stored in `cursor_row` and `cursor_col` attributes
- Automatic clamping to valid grid bounds
- Handles zero-dimension grids gracefully

### 4. Window Resize Handling

**Method**: `_handle_window_resize() -> None`

Handles window resize events by:
1. Recalculating grid dimensions based on new window size
2. Preserving existing grid content where possible
3. Filling new areas with spaces
4. Clamping cursor position to new bounds

**Implementation**:
```python
def _handle_window_resize(self) -> None:
    if self.window is None or self.metal_view is None:
        return
    
    # Get new window content size
    try:
        content_rect = self.window.contentView().frame()
        window_width = int(content_rect.size.width)
        window_height = int(content_rect.size.height)
    except Exception:
        return
    
    # Calculate new grid dimensions
    new_cols = max(1, window_width // self.char_width) if self.char_width > 0 else 80
    new_rows = max(1, window_height // self.char_height) if self.char_height > 0 else 40
    
    # Check if dimensions actually changed
    if new_rows == self.rows and new_cols == self.cols:
        return
    
    # Create new grid with new dimensions
    new_grid = [
        [(' ', 0, 0) for _ in range(new_cols)]
        for _ in range(new_rows)
    ]
    
    # Copy existing content to new grid (preserve what fits)
    for row in range(min(self.rows, new_rows)):
        for col in range(min(self.cols, new_cols)):
            new_grid[row][col] = self.grid[row][col]
    
    # Update grid and dimensions
    self.grid = new_grid
    self.rows = new_rows
    self.cols = new_cols
    
    # Clamp cursor position to new bounds
    if self.cursor_row >= self.rows:
        self.cursor_row = max(0, self.rows - 1)
    if self.cursor_col >= self.cols:
        self.cursor_col = max(0, self.cols - 1)
```

**Features**:
- Automatic grid resizing based on window size
- Content preservation during resize
- Cursor position clamping to new bounds
- Graceful handling of errors

**Resize Detection**:

Resize events are detected in `_translate_macos_event()` by checking if the window size has changed:

```python
# Check if window size has changed (simple resize detection)
if self.window and self.metal_view:
    try:
        content_rect = self.window.contentView().frame()
        window_width = int(content_rect.size.width)
        window_height = int(content_rect.size.height)
        
        # Calculate what the grid dimensions should be
        expected_cols = max(1, window_width // self.char_width) if self.char_width > 0 else self.cols
        expected_rows = max(1, window_height // self.char_height) if self.char_height > 0 else self.rows
        
        # If dimensions don't match, we have a resize
        if expected_rows != self.rows or expected_cols != self.cols:
            # Handle the resize
            self._handle_window_resize()
            
            # Return a RESIZE event
            return InputEvent(
                key_code=KeyCode.RESIZE,
                modifiers=ModifierKey.NONE,
                char=None
            )
    except Exception:
        pass  # Ignore errors during resize detection
```

### 5. Resource Cleanup

**Method**: `shutdown() -> None`

Cleans up all Metal resources and closes the window.

**Implementation**:
```python
def shutdown(self) -> None:
    # Close the native window
    if self.window is not None:
        try:
            self.window.close()
        except Exception:
            pass  # Ignore errors during cleanup
        self.window = None
    
    # Clear Metal view reference
    if hasattr(self, 'metal_view'):
        self.metal_view = None
    
    # Release rendering pipeline
    self.render_pipeline = None
    
    # Release command queue
    self.command_queue = None
    
    # Release Metal device
    self.metal_device = None
    
    # Clear character grid buffer
    self.grid = []
    
    # Clear color pair storage
    self.color_pairs = {}
    
    # Reset dimensions
    self.rows = 0
    self.cols = 0
    self.char_width = 0
    self.char_height = 0
```

**Features**:
- Graceful cleanup of all resources
- Safe to call multiple times
- Handles errors during cleanup
- Resets all state variables

## Testing

Comprehensive unit tests were created in `ttk/test/test_metal_window_management.py`:

### Test Coverage

1. **Dimension Queries**:
   - `test_get_dimensions_returns_grid_size` - Verify correct dimensions returned
   - `test_get_dimensions_with_different_sizes` - Test various grid sizes

2. **Cursor Control**:
   - `test_set_cursor_visibility_true` - Show cursor
   - `test_set_cursor_visibility_false` - Hide cursor
   - `test_move_cursor_within_bounds` - Valid cursor positions
   - `test_move_cursor_clamps_to_bounds` - Out-of-bounds clamping
   - `test_move_cursor_with_zero_dimensions` - Edge case handling

3. **Display Refresh**:
   - `test_refresh_calls_render_grid` - Full window refresh
   - `test_refresh_region_calls_render_grid_region` - Partial refresh

4. **Window Resize**:
   - `test_handle_window_resize_updates_dimensions` - Dimension updates
   - `test_handle_window_resize_preserves_content` - Content preservation
   - `test_handle_window_resize_clamps_cursor` - Cursor clamping
   - `test_handle_window_resize_no_change` - No-op when size unchanged

5. **Resource Cleanup**:
   - `test_shutdown_clears_resources` - All resources cleared
   - `test_shutdown_handles_none_window` - Handles None window
   - `test_shutdown_handles_window_close_error` - Error handling

6. **Resize Detection**:
   - `test_translate_event_no_resize_when_size_unchanged` - No false positives

### Test Results

All 17 tests pass successfully:
```
============================= 17 passed in 0.55s ==============================
```

## Design Decisions

### 1. Cursor State Storage

The cursor state (visibility and position) is stored in instance variables rather than being rendered immediately. This allows for efficient batch updates where multiple cursor operations can be performed before a single refresh.

### 2. Resize Detection

Window resize is detected by comparing the current window size with the expected grid dimensions on each event. This simple approach works well for the Metal backend where we have direct access to window dimensions.

### 3. Content Preservation

During resize, existing grid content is preserved by copying it to the new grid. This ensures that users don't lose their display content when resizing the window.

### 4. Cursor Clamping

Cursor positions are automatically clamped to valid grid bounds. This prevents errors and ensures the cursor is always at a valid position, even after window resize.

### 5. Error Handling

All methods that interact with macOS frameworks use try/except blocks to handle potential errors gracefully. This ensures the backend remains stable even if PyObjC is not available or if there are issues with the window system.

## Integration with Renderer API

The Metal backend now fully implements all window management methods defined in the abstract `Renderer` base class:

- ✅ `get_dimensions()` - Returns grid dimensions
- ✅ `refresh()` - Refreshes entire window
- ✅ `refresh_region()` - Refreshes specific region
- ✅ `set_cursor_visibility()` - Controls cursor visibility
- ✅ `move_cursor()` - Positions cursor
- ✅ `shutdown()` - Cleans up resources

## Future Enhancements

1. **Cursor Rendering**: Currently, cursor state is stored but not rendered. Future work will add actual cursor rendering in the `_render_grid()` method.

2. **Optimized Resize**: The current resize implementation recreates the entire grid. This could be optimized to only allocate new rows/columns as needed.

3. **Resize Events**: Currently, resize detection happens on every event. A more efficient approach would be to use NSWindow delegate methods to receive resize notifications directly.

4. **Cursor Styles**: Support for different cursor styles (block, underline, vertical bar) could be added.

## Related Documentation

- [Metal Backend Implementation](METAL_BACKEND_IMPLEMENTATION.md)
- [Metal Initialization](METAL_INITIALIZATION_IMPLEMENTATION.md)
- [Metal Input Handling](METAL_INPUT_HANDLING_IMPLEMENTATION.md)
- [Metal Rendering Pipeline](METAL_RENDERING_PIPELINE_IMPLEMENTATION.md)

## Conclusion

The Metal backend window management implementation provides a complete set of window control operations that match the abstract Renderer API. The implementation is well-tested, handles edge cases gracefully, and provides a solid foundation for building character-grid-based applications on macOS.
