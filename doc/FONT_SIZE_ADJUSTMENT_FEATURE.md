# Font Size Adjustment Feature

## Overview

TFM's Desktop mode supports dynamic font size adjustment using keyboard shortcuts. You can increase or decrease the font size in real-time without restarting the application or editing configuration files.

## Availability

- **Desktop Mode Only**: This feature is only available when running TFM in Desktop mode (CoreGraphics backend on macOS)
- **Terminal Mode**: Font size adjustment is not available in terminal mode (curses backend)

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
2. **Window resizes automatically** to maintain the same number of rows and columns
3. **Grid dimensions remain constant** (e.g., 80 columns × 24 rows stays the same)
4. **Log message displays** the new font size in the log pane
5. **Change persists** for the current session only (not saved to configuration)

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

### More Content

Decrease font size when:
- Working on a small laptop screen
- Needing to see more files at once
- Comparing many items side-by-side
- Working with long filenames

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

### Window Resizing

When font size changes:
- Character width and height are recalculated
- Window dimensions are adjusted: `width = cols × char_width + padding`
- Window position remains the same (top-left corner doesn't move)
- Content redraws immediately with new font metrics

### Grid Preservation

The character grid dimensions (rows and columns) remain constant:
- File pane layouts stay the same
- Log pane height ratio is preserved
- Status bar and headers maintain their positions
- Cursor position remains at the same logical location

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

**Problem**: Window becomes too large or too small after adjusting

**Solutions**:
1. Adjust font size in the opposite direction
2. Restart TFM to use default font size from configuration
3. Edit `~/.tfm/config.py` to change `DESKTOP_FONT_SIZE`

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
