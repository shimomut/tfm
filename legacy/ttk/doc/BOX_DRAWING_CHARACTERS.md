# Box-Drawing Characters in TTK

## Overview

TTK uses Unicode box-drawing characters for rendering rectangles and lines, providing a professional appearance consistent with modern terminal applications like TFM (TUI File Manager).

## Character Set

### Rectangle Components

| Component | Character | Unicode | Description |
|-----------|-----------|---------|-------------|
| Top-left corner | `┌` | U+250C | Box Drawings Light Down and Right |
| Top-right corner | `┐` | U+2510 | Box Drawings Light Down and Left |
| Bottom-left corner | `└` | U+2514 | Box Drawings Light Up and Right |
| Bottom-right corner | `┘` | U+2518 | Box Drawings Light Up and Left |
| Horizontal edge | `─` | U+2500 | Box Drawings Light Horizontal |
| Vertical edge | `│` | U+2502 | Box Drawings Light Vertical |

### Additional Characters (for reference)

| Component | Character | Unicode | Description |
|-----------|-----------|---------|-------------|
| Left T-junction | `├` | U+251C | Box Drawings Light Vertical and Right |
| Right T-junction | `┤` | U+2524 | Box Drawings Light Vertical and Left |
| Top T-junction | `┬` | U+252C | Box Drawings Light Down and Horizontal |
| Bottom T-junction | `┴` | U+2534 | Box Drawings Light Up and Horizontal |
| Cross | `┼` | U+253C | Box Drawings Light Vertical and Horizontal |

## Usage in TTK

### Rectangles

The `draw_rect()` method automatically uses box-drawing characters for outlined rectangles:

```python
# Draw an outlined rectangle
renderer.draw_rect(5, 10, 8, 30, color_pair=1, filled=False)
```

This produces:
```
┌────────────────────────────┐
│                            │
│                            │
│                            │
│                            │
│                            │
│                            │
└────────────────────────────┘
```

### Lines

For consistency with rectangles, use box-drawing characters for lines:

```python
# Horizontal line (matches rectangle top/bottom edges)
renderer.draw_hline(5, 0, '─', 40, color_pair=1)

# Vertical line (matches rectangle left/right edges)
renderer.draw_vline(0, 10, '│', 20, color_pair=1)
```

### ASCII Alternatives

For compatibility with terminals that don't support Unicode, ASCII alternatives can be used:

```python
# ASCII horizontal line
renderer.draw_hline(5, 0, '-', 40)

# ASCII vertical line
renderer.draw_vline(0, 10, '|', 20)
```

However, these will not match the appearance of rectangles drawn with `draw_rect()`.

## Implementation Details

### Curses Backend

The curses backend (`CursesBackend`) uses box-drawing characters in `draw_rect()`:

```python
# Top edge
top_line = '┌' + '─' * (width - 2) + '┐'
self.draw_text(row, col, top_line, color_pair)

# Middle rows with left and right edges
for r in range(row + 1, row + height - 1):
    self.draw_text(r, col, '│', color_pair)
    self.draw_text(r, col + width - 1, '│', color_pair)

# Bottom edge
bottom_line = '└' + '─' * (width - 2) + '┘'
self.draw_text(row + height - 1, col, bottom_line, color_pair)
```

### CoreGraphics Backend

The CoreGraphics backend (`CoreGraphicsBackend`) also uses box-drawing characters, storing them in the character grid for rendering.

## Best Practices

### Consistency

**Always use the same characters for lines and rectangle edges:**

✅ **Recommended:**
```python
# Use box-drawing characters consistently
renderer.draw_hline(5, 0, '─', 40)  # Horizontal line
renderer.draw_vline(0, 10, '│', 20)  # Vertical line
renderer.draw_rect(5, 10, 8, 30, filled=False)  # Rectangle
```

❌ **Avoid mixing:**
```python
# Don't mix ASCII and box-drawing characters
renderer.draw_hline(5, 0, '-', 40)  # ASCII
renderer.draw_rect(5, 10, 8, 30, filled=False)  # Box-drawing
```

### Visual Hierarchy

Use different line styles for different purposes:

```python
# Primary borders - box-drawing characters
renderer.draw_rect(0, 0, 24, 80, color_pair=1, filled=False)

# Separators - double lines or different characters
renderer.draw_hline(10, 0, '═', 80, color_pair=2)

# Emphasis - bold or colored
renderer.draw_hline(5, 0, '─', 80, color_pair=3)
```

## Terminal Compatibility

### Modern Terminals

Most modern terminals support Unicode box-drawing characters:
- iTerm2 (macOS)
- Terminal.app (macOS)
- GNOME Terminal (Linux)
- Konsole (Linux)
- Windows Terminal (Windows 10+)
- Alacritty
- Kitty

### Legacy Terminals

For legacy terminals without Unicode support, consider:
1. Detecting terminal capabilities
2. Falling back to ASCII characters
3. Providing a configuration option

Example fallback:
```python
# Check if terminal supports Unicode
if supports_unicode():
    HLINE_CHAR = '─'
    VLINE_CHAR = '│'
else:
    HLINE_CHAR = '-'
    VLINE_CHAR = '|'
```

## Examples

### Simple Dialog Box

```python
# Draw dialog box with title
renderer.draw_rect(5, 10, 10, 40, color_pair=1, filled=False)
renderer.draw_text(5, 12, " Dialog Title ", color_pair=1)
renderer.draw_hline(6, 10, '─', 40, color_pair=1)
```

Result:
```
          ┌ Dialog Title ──────────────────┐
          │                                │
          │                                │
          │                                │
          │                                │
          │                                │
          │                                │
          │                                │
          └────────────────────────────────┘
```

### Split Pane Layout

```python
rows, cols = renderer.get_dimensions()
split_col = cols // 2

# Draw vertical separator
renderer.draw_vline(0, split_col, '│', rows, color_pair=1)

# Draw borders around each pane
renderer.draw_rect(0, 0, rows, split_col, color_pair=2, filled=False)
renderer.draw_rect(0, split_col + 1, rows, cols - split_col - 1, color_pair=2, filled=False)
```

## References

- [Unicode Box Drawing Characters](https://en.wikipedia.org/wiki/Box-drawing_character)
- [Unicode Standard - Box Drawing Range](https://www.unicode.org/charts/PDF/U2500.pdf)
- TFM (TUI File Manager) - Reference implementation

## Migration Guide

If you have existing code using ASCII characters, update it to use box-drawing characters:

### Before
```python
renderer.draw_hline(5, 0, '-', 40)
renderer.draw_vline(0, 10, '|', 20)
```

### After
```python
renderer.draw_hline(5, 0, '─', 40)
renderer.draw_vline(0, 10, '│', 20)
```

This ensures visual consistency with rectangles drawn using `draw_rect()`.
