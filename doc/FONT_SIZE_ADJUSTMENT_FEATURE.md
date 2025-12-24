# Font Size Adjustment Feature

## Overview

TFM's Desktop mode supports dynamic font size adjustment using keyboard shortcuts. You can increase or decrease the font size in real-time without restarting the application or editing configuration files.

## Availability

- **Desktop Mode Only**: This feature is only available when running TFM in Desktop mode (CoreGraphics backend on macOS)
- **Terminal Mode**: Font size adjustment is not available in terminal mode (curses backend)
- **Works Everywhere**: The shortcuts work in all contexts - main screen, dialogs, text viewer, etc.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd-Plus` or `Cmd-=` | Increase font size by 1 point |
| `Cmd-Minus` | Decrease font size by 1 point |

## Font Size Limits

- **Minimum**: 8 points
- **Maximum**: 72 points
- **Default**: Configured in `~/.tfm/config.py` (typically 12-14 points)

## Behavior

When you change the font size:

1. **Font renders immediately** with the new size
2. **Window size stays constant** - no resizing
3. **Grid dimensions adjust** to fit more/fewer characters:
   - Larger font → Fewer rows and columns visible
   - Smaller font → More rows and columns visible
4. **Log message displays** the new font size in the log pane
5. **Change persists** for the current session only (not saved to configuration)

This is the standard behavior users expect - the window stays the same size, and you see more or less content depending on the font size.

## Usage Examples

### Increase Font Size

Press `Cmd-Plus` (or `Cmd-=`) to make text larger:

```
Font size increased to 13pt
Font size increased to 14pt
Font size increased to 15pt
```

The window grows to accommodate the larger text while maintaining the same grid layout.

### Decrease Font Size

Press `Cmd-Minus` to make text smaller:

```
Font size decreased to 14pt
Font size decreased to 13pt
Font size decreased to 12pt
```

The window shrinks while maintaining the same grid layout.

### At Limits

When you reach the minimum or maximum font size:

```
Font size at minimum (8pt)
```

or

```
Font size at maximum (72pt)
```

## Use Cases

### Better Readability

Increase font size when:
- Working on a large external monitor
- Presenting or screen sharing
- Experiencing eye strain with small text
- Viewing from a distance

Note: With larger font, you'll see fewer files at once, but they'll be easier to read.

### More Content

Decrease font size when:
- Working on a small laptop screen
- Needing to see more files at once
- Comparing many items side-by-side
- Working with long filenames

Note: With smaller font, you'll see more files at once in the same window size.

### Quick Adjustments

Change font size on the fly:
- Switch between detailed work (larger) and overview (smaller)
- Adapt to different viewing distances
- Accommodate different lighting conditions
- Match personal preference for different tasks

## Configuration

### Default Font Size

Set your preferred default font size in `~/.tfm/config.py`:

```python
# Desktop mode settings
DESKTOP_FONT_SIZE = 14  # Your preferred default (8-72)
```

This sets the initial font size when TFM starts. You can then adjust it dynamically during the session.

### Font Family

The font size adjustment works with any configured font:

```python
# Single font
DESKTOP_FONT_NAME = 'Menlo'

# Multiple fonts with fallback
DESKTOP_FONT_NAME = ['SF Mono', 'Menlo', 'Monaco']
```

## Technical Details

### Window Sizing

When font size changes:
- Window size remains constant (no resizing)
- Character width and height are recalculated
- Grid dimensions are recalculated: `cols = window_width / char_width`
- Grid is resized to new dimensions
- Content redraws immediately with new font metrics

### Grid Adjustment

The character grid dimensions (rows and columns) adjust to fit the window:
- Larger font → Fewer characters fit → Smaller grid (e.g., 80×24 → 68×20)
- Smaller font → More characters fit → Larger grid (e.g., 80×24 → 95×28)
- File pane layouts adjust automatically
- Log pane height ratio is preserved
- Cursor position adjusts to stay visible

### Performance

Font size changes are efficient:
- Font metrics are recalculated once
- Rendering caches are updated
- Window resize is handled by the OS
- No file system operations or configuration writes

## Troubleshooting

### Shortcuts Not Working

**Problem**: Cmd-Plus or Cmd-Minus don't change font size

**Solutions**:
1. Verify you're running in Desktop mode (not terminal mode)
2. Check that the window has focus (click on it)
3. Ensure you're pressing the Command key (⌘), not Control
4. Try `Cmd-=` instead of `Cmd-Plus` (same key, no Shift needed)

### Window Too Large/Small

**Problem**: After adjusting font size, too few/many files are visible

**Solutions**:
1. Adjust font size in the opposite direction
2. Resize the window manually to see more/less content
3. Restart TFM to use default font size and window size from configuration

### Font Looks Blurry

**Problem**: Text appears blurry at certain font sizes

**Solutions**:
1. Try a different font size (some sizes render better than others)
2. Use a different font family in configuration
3. Check macOS display scaling settings (System Settings → Displays)

## Related Features

- **Window Geometry Persistence**: Window size and position are saved between sessions
- **Font Cascade**: Multiple fonts can be configured for character fallback
- **Color Schemes**: Work with both light and dark color schemes

## See Also

- [Desktop Mode Guide](DESKTOP_MODE_GUIDE.md) - Complete desktop mode documentation
- [Configuration Guide](CONFIGURATION_FEATURE.md) - All configuration options
- [Keyboard Shortcuts](../README.md#keyboard-shortcuts) - All available shortcuts
