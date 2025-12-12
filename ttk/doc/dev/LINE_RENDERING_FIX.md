# Line Rendering Fix for Unicode Box-Drawing Characters

## Problem

Horizontal and vertical lines were not visible when using Unicode box-drawing characters (─ and │) with the curses backend. The lines worked fine with ASCII characters (- and |) but failed with Unicode.

## Root Cause

The curses backend was using native curses functions `curses.hline()` and `curses.vline()` which don't properly handle Unicode characters. These functions use `ord()` internally which only works with single-byte ASCII characters.

## Solution

Modified `ttk/backends/curses_backend.py` to use `draw_text()` instead of native curses line functions:

### Horizontal Lines (`draw_hline`)

**Before:**
```python
def draw_hline(self, row: int, col: int, char: str,
               length: int, color_pair: int = 0) -> None:
    # Used curses.hline() which doesn't handle Unicode
    self.stdscr.hline(row, col, ord(char[0]), length, curses.color_pair(color_pair))
```

**After:**
```python
def draw_hline(self, row: int, col: int, char: str,
               length: int, color_pair: int = 0) -> None:
    # Use draw_text for Unicode characters (like box-drawing chars)
    # curses.hline() doesn't handle Unicode properly
    self.draw_text(row, col, char[0] * length, color_pair)
```

### Vertical Lines (`draw_vline`)

**Before:**
```python
def draw_vline(self, row: int, col: int, char: str,
               length: int, color_pair: int = 0) -> None:
    # Used curses.vline() which doesn't handle Unicode
    self.stdscr.vline(row, col, ord(char[0]), length, curses.color_pair(color_pair))
```

**After:**
```python
def draw_vline(self, row: int, col: int, char: str,
               length: int, color_pair: int = 0) -> None:
    # Draw vertical line by drawing character at each row
    # curses.vline() doesn't handle Unicode properly
    for i in range(length):
        self.draw_text(row + i, col, char[0], color_pair)
```

## Benefits

1. **Unicode Support**: Lines now properly render Unicode box-drawing characters
2. **Consistency**: All drawing operations use the same text rendering path
3. **Compatibility**: Works with both ASCII and Unicode characters
4. **Visual Quality**: Matches the appearance of rectangles which already used box-drawing characters

## Test Interface Updates

Also updated `ttk/demo/test_interface.py` to improve line visibility:

1. Simplified conditional logic for drawing lines
2. Increased vertical line height from 2 to 4 characters
3. Better spacing and labeling ("H line:" and "V line:")
4. Removed overly restrictive space checks

## Testing

Created test files to verify the fix:
- `ttk/test/test_lines_visibility.py` - Minimal test for line rendering
- `ttk/test/test_lines_simple.py` - Simple comparison test

## Related Changes

This fix completes the box-drawing character implementation:
- Rectangles already used box-drawing characters (┌┐└┘─│)
- Horizontal and vertical lines now use matching characters (─│)
- All shapes now have consistent visual appearance

## Technical Notes

- The `draw_text()` method properly handles Unicode through curses' `addstr()` function
- Native curses line functions (`hline()` and `vline()`) are limited to single-byte characters
- This approach has minimal performance impact as `draw_text()` is already optimized
- The fix works on all terminals that support Unicode (most modern terminals)
