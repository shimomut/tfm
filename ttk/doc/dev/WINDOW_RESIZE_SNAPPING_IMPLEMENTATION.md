# Window Resize Snapping Implementation

## Overview

The CoreGraphics backend implements window resize snapping to ensure the window content area is always an exact multiple of the character cell size. This prevents partial character cells from appearing at the edges of the window and maintains proper grid alignment.

## Problem Statement

While `setResizeIncrements_()` ensures the window resizes in character cell increments during dragging, it doesn't handle cases where:
1. The window starts at a size that's not aligned to the character grid
2. The window is restored from saved geometry with misaligned dimensions
3. The window is programmatically resized to a non-aligned size

Without snapping at the start and end of resize operations, users could end up with windows that have partial character cells, leading to rendering artifacts and inconsistent behavior.

## Solution

The implementation dynamically enables and disables resize increments to balance grid alignment with macOS window management:

### 1. `windowWillStartLiveResize_`

Called when the user starts dragging the resize handle. This method:
- Snaps the window to the character grid for proper initial alignment
- Enables resize increments to maintain alignment during manual dragging

### 2. `windowDidEndLiveResize_`

Called when the user finishes dragging the resize handle. This method:
- Disables resize increments (sets to 1x1) to allow macOS window management features to work properly
- Allows maximizing, split view, and edge snapping to function without constraint

### 3. `_snap_window_to_grid` (Helper Method)

Performs the actual snapping logic:
1. Gets the current window frame and content rect
2. Calculates the snapped content size (rounded down to nearest cell)
3. Checks if snapping is needed (within 0.5px tolerance)
4. Calculates the new window frame accounting for decorations
5. Sets the new frame without animation

**Important**: This method is only called at the start of resize operations (`windowWillStartLiveResize_`).

### 4. Dynamic Resize Increment Management

The key innovation is dynamically enabling/disabling resize increments:
- **During initialization**: No resize increments set (allows free resizing)
- **At resize start**: Resize increments enabled (maintains grid alignment during drag)
- **At resize end**: Resize increments disabled (allows macOS window management)

## Implementation Details

### Coordinate System

The implementation must account for:
- **Content rect**: The drawable area inside the window (excludes title bar and borders)
- **Window frame**: The entire window including decorations
- **Frame difference**: The size difference between window frame and content rect

### Snapping Algorithm

The snapping algorithm is simple and only runs at the start of resize operations:

```python
# Calculate snapped dimensions (round down to nearest cell)
snapped_cols = max(1, int(current_width / char_width))
snapped_rows = max(1, int(current_height / char_height))
snapped_width = snapped_cols * char_width
snapped_height = snapped_rows * char_height

# Calculate new window frame size
new_frame_width = snapped_width + frame_width_diff
new_frame_height = snapped_height + frame_height_diff
```

**Why only at start?** By snapping only at the start of resize and dynamically managing resize increments, we respect macOS window management features (maximized, split view, tiled windows) while ensuring proper alignment during manual resizing.

### Dynamic Resize Increment Management

```python
# At resize start - enable increments
resize_increment = NSMakeSize(char_width, char_height)
window.setResizeIncrements_(resize_increment)

# At resize end - disable increments
window.setResizeIncrements_(NSMakeSize(1.0, 1.0))
```

This approach allows:
- **Manual resizing**: Grid-aligned with character cell increments
- **Maximizing**: Works without constraint
- **Split view**: Works without constraint
- **Edge snapping**: Works without constraint

### Tolerance Check

A tolerance of 0.5 pixels is used to avoid unnecessary snapping when the window is already aligned:

```python
if abs(current_width - snapped_width) < 0.5 and abs(current_height - snapped_height) < 0.5:
    return  # Already aligned
```

## Integration with Existing Features

### Resize Increments

Resize increments are now managed dynamically rather than set once at initialization:

```python
# At initialization - no resize increments set
# (allows macOS window management to work)

# At resize start - enable increments
resize_increment = Cocoa.NSMakeSize(self.char_width, self.char_height)
self.window.setResizeIncrements_(resize_increment)

# At resize end - disable increments
self.window.setResizeIncrements_(Cocoa.NSMakeSize(1.0, 1.0))
```

This dynamic approach:
- Enables grid alignment during manual resize operations
- Disables constraints for macOS window management features
- Allows maximizing, split view, and edge snapping to work properly

### Window Geometry Persistence

The snapping logic works seamlessly with the window geometry persistence feature (`setFrameAutosaveName_`). When a window is restored from saved geometry:
1. The saved frame is applied
2. If the user resizes the window, snapping ensures proper alignment
3. The new aligned size is saved for future sessions

### Grid Dimension Updates

The `windowDidResize_` method handles grid dimension updates after any resize:
1. Calculates new grid dimensions based on content size
2. Creates a new grid with the updated dimensions
3. Copies old content to the new grid
4. Clears attribute caches
5. Triggers a redraw

## Testing

### Demo Script

The `ttk/demo/demo_window_resize_snapping.py` script demonstrates the feature:
- Visual grid pattern showing character cell alignment
- Real-time display of grid dimensions and content size
- Status bar indicating snapping is active

### Manual Testing

To verify the implementation:
1. Run any TTK application with CoreGraphics backend
2. Resize the window by dragging the resize handle
3. Observe that the window snaps to grid alignment at start and end
4. Verify that no partial character cells appear at the edges
5. Check that the grid dimensions update correctly

### Edge Cases

The implementation handles:
- **Minimum size**: Ensures at least 1 row and 1 column
- **Already aligned**: Skips snapping if within tolerance
- **Window decorations**: Correctly accounts for title bar and borders
- **Floating-point precision**: Uses tolerance for comparison
- **macOS window management**: Respects maximized, split view, and tiled windows by not snapping at resize end

## Performance Considerations

### Minimal Overhead

The snapping operations are lightweight:
- Only triggered at start and end of resize (not during drag)
- Simple arithmetic calculations
- No memory allocations
- Single `setFrame_display_()` call

### No Animation

The `setFrame_display_(frame, True)` call uses `display=True` but no animation, ensuring instant snapping without visual delay.

## Future Enhancements

Potential improvements:
1. **Configurable snapping**: Allow applications to disable snapping if needed
2. **Minimum window size**: Enforce minimum rows/cols constraints
3. **Aspect ratio**: Maintain aspect ratio during resize
4. **Snap to specific sizes**: Support snapping to predefined window sizes

## References

- **NSWindowDelegate Protocol**: Apple's documentation on window delegate methods
- **setResizeIncrements_**: NSWindow method for resize increment control
- **Character Grid System**: TTK's coordinate system and grid management
- **Window Geometry Persistence**: Frame autosave feature integration
