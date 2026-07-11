# Font Size Adjustment Implementation

## Overview

This document describes the implementation of dynamic font size adjustment in TFM's Desktop mode (CoreGraphics backend).

## Architecture

### Components

1. **CoreGraphicsBackend.change_font_size()** - Backend method that handles font size changes
2. **FileManager.handle_key_event()** - Intercepts Cmd-Plus/Cmd-Minus keyboard shortcuts
3. **TTKWindowDelegate.windowDidResize_()** - Handles window resize events and grid recalculation

### Key Challenge: Preserving Window Size

The main challenge is keeping the window size constant when font size changes. The grid dimensions (rows, columns) must adjust to fit more or fewer characters in the same window size.

This is the standard behavior users expect from font size changes - the window stays the same size, and you see more or less content.

## Implementation Details

### Font Size Change Flow

```
User presses Cmd-Plus/Cmd-Minus (anywhere in the app)
    ↓
TFMEventCallback.on_key_event() intercepts (global handler)
    ↓
Checks if desktop mode and Cmd modifier
    ↓
CoreGraphicsBackend.change_font_size(delta)
    ↓
1. Update self.font_size
2. Reload font with new size
3. Recalculate char_width, char_height
4. Get current window content size (keep constant!)
5. Calculate new grid dimensions from window size
6. Resize grid to new dimensions
7. Set resize_pending flag
    ↓
Next render cycle
    ↓
Application receives resize event
    ↓
UI adjusts to new grid dimensions
```

### Why TFMEventCallback?

The font size shortcuts are handled in `TFMEventCallback.on_key_event()` rather than in `FileManager.handle_key_event()` because:

1. **Global availability**: Works in all contexts (main screen, dialogs, text viewer, etc.)
2. **Early interception**: Processed before routing to UI layers
3. **Consistent behavior**: Same shortcuts work everywhere in the application

This is similar to how system-wide shortcuts work in macOS applications.

### Critical Implementation Detail: Keep Window Size Constant

**The Approach:**

When font size changes, we keep the window size constant and adjust the grid:

```python
# CORRECT APPROACH
# Get current window size (keep constant)
content_rect = window.contentView().frame()
content_width = int(content_rect.size.width)
content_height = int(content_rect.size.height)

# Calculate how many characters fit with new font size
padding = WINDOW_PADDING_MULTIPLIER * char_height
new_cols = max(1, int((content_width - padding) / char_width))
new_rows = max(1, int((content_height - padding) / char_height))

# Update grid dimensions
self.cols = new_cols
self.rows = new_rows

# Resize grid to new dimensions
# (copy old content as much as fits)
```

**Why This Works:**

- Window size stays constant (user's preferred size)
- Grid adjusts to fit more/fewer characters
- Larger font → Fewer characters → Smaller grid
- Smaller font → More characters → Larger grid
- Standard behavior users expect from font size changes

### Code Implementation

```python
def change_font_size(self, delta: int) -> bool:
    # Validate new size (8-72 points)
    new_font_size = self.font_size + delta
    if new_font_size < 8 or new_font_size > 72:
        return False
    
    try:
        # Update font size
        self.font_size = new_font_size
        
        # Reload font with new size
        self._load_font()
        
        # Recalculate character dimensions
        self._calculate_char_dimensions()
        
        # Get current window size (keep constant)
        content_rect = self.window.contentView().frame()
        content_width = int(content_rect.size.width)
        content_height = int(content_rect.size.height)
        
        # Calculate new grid dimensions
        padding = self.WINDOW_PADDING_MULTIPLIER * self.char_height
        new_cols = max(1, int((content_width - padding) / self.char_width))
        new_rows = max(1, int((content_height - padding) / self.char_height))
        
        # Update grid dimensions
        old_rows = self.rows
        old_cols = self.cols
        self.rows = new_rows
        self.cols = new_cols
        
        # Resize grid (copy old content as much as fits)
        old_grid = self.grid
        new_grid = [
            [(' ', 0, 0, False) for _ in range(new_cols)]
            for _ in range(new_rows)
        ]
        for row in range(min(old_rows, new_rows)):
            for col in range(min(old_cols, new_cols)):
                new_grid[row][col] = old_grid[row][col]
        self.grid = new_grid
        
        # Set flag to generate resize event
        self.resize_pending = True
        
        # Force redraw
        self.view.setNeedsDisplay_(True)
        
        return True
        
    except Exception as e:
        # Restore original font size on error
        self.font_size = new_font_size - delta
        self._load_font()
        self._calculate_char_dimensions()
        return False
```

### Window Resize Handler

The `windowDidResize_()` handler is **not triggered** by font size changes because we don't resize the window. It only triggers when the user manually resizes the window.

Font size changes directly update the grid dimensions without going through the window resize handler.

## C++ Renderer Integration

The C++ renderer (`ttk_coregraphics_render`) automatically detects font changes:

```cpp
static void initialize_caches(PyObject* font_names_obj, double font_size_val) {
    static std::vector<std::string> last_font_names;
    static double last_font_size = 0.0;
    
    // Check if font changed
    bool need_reinit = (last_font_names != font_names) ||
                       (std::abs(last_font_size - font_size_val) > 0.01);
    
    if (need_reinit) {
        // Clear caches
        // Rebuild font cascade
        // Update tracking variables
    }
}
```

This function is called by `render_frame()` on every frame. When it detects a font size change, it automatically:
1. Clears font cache
2. Clears color cache
3. Clears attribute cache
4. Rebuilds font cascade with new size
5. Updates tracking variables

No explicit cache invalidation needed from Python!

## Testing

### Unit Tests

```python
def test_window_size_unchanged():
    backend = CoreGraphicsBackend(font_size=12, rows=24, cols=80)
    backend.initialize()
    
    # Get initial window size
    content_rect = backend.window.contentView().frame()
    initial_width = int(content_rect.size.width)
    initial_height = int(content_rect.size.height)
    
    # Change font size
    backend.change_font_size(4)
    
    # Verify window size unchanged
    new_content_rect = backend.window.contentView().frame()
    new_width = int(new_content_rect.size.width)
    new_height = int(new_content_rect.size.height)
    assert new_width == initial_width
    assert new_height == initial_height
    
    # Verify grid dimensions changed (fewer characters fit)
    assert backend.rows < 24
    assert backend.cols < 80
```

### Manual Testing

1. Launch TFM in desktop mode
2. Note current window size and grid dimensions (e.g., 600×400px, 80×24 grid)
3. Press Cmd-Plus several times
4. Verify:
   - Window size unchanged (still 600×400px)
   - Text becomes larger
   - Fewer files visible (e.g., 68×20 grid)
   - Grid dimensions changed in status bar

## Edge Cases

### Minimum Font Size (8pt)

When at minimum:
```python
if new_font_size < 8:
    return False  # Don't change
```

User sees: "Font size at minimum (8pt)"

### Maximum Font Size (72pt)

When at maximum:
```python
if new_font_size > 72:
    return False  # Don't change
```

User sees: "Font size at maximum (72pt)"

### Font Load Failure

If font loading fails:
```python
except Exception as e:
    # Restore original font size
    self.font_size = new_font_size - delta
    self._load_font()
    self._calculate_char_dimensions()
    return False
```

Window stays at original size, no change visible to user.

### Window Too Large for Screen

This is no longer an issue since we don't resize the window. The window stays at the size the user set it to.

## Performance Considerations

### Font Reloading

Font reloading is fast (< 1ms) because:
- Font is already in system font cache
- Only creating new NSFont object with different size
- No file I/O involved

### Character Dimension Calculation

Character dimension calculation is fast (< 1ms):
- Creates single NSAttributedString with "M"
- Measures size
- No rendering involved

### Window Resizing

Window resizing is handled by macOS:
- GPU-accelerated
- Smooth animation
- No application code involved

### Grid Reallocation

Grid reallocation only happens if dimensions change:
- For font size changes with correct implementation: no reallocation
- For manual window resize: reallocation needed
- Grid is just a 2D list, very fast to allocate

## Future Enhancements

### Persistent Font Size

Currently font size changes are session-only. Could add:
```python
# Save to user defaults
user_defaults = Cocoa.NSUserDefaults.standardUserDefaults()
user_defaults.setInteger_forKey_(self.font_size, "TFMFontSize")
user_defaults.synchronize()
```

### Font Size Presets

Could add menu items or shortcuts for common sizes:
- Cmd-0: Reset to default
- Cmd-1: Small (10pt)
- Cmd-2: Medium (14pt)
- Cmd-3: Large (18pt)

### Zoom Percentage Display

Could show zoom percentage in status bar:
```
Font size: 14pt (117% of default)
```

## References

- **User Documentation**: `doc/FONT_SIZE_ADJUSTMENT_FEATURE.md`
- **CoreGraphics Backend**: `ttk/backends/coregraphics_backend.py`
- **C++ Renderer**: `ttk/backends/coregraphics_render.cpp`
- **FileManager**: `src/tfm_main.py`
