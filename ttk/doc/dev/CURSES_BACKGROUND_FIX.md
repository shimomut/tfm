# Curses Backend Black Background Fix

## Problem

When running the TTK demo with the curses backend (`make demo-ttk BACKEND=curses`), the terminal displayed text with black backgrounds in the text areas, but other areas showed white or the terminal's default background color. This created an inconsistent appearance where only the explicitly colored text had black backgrounds.

## Root Cause

The issue was caused by the use of `curses.use_default_colors()` in the `initialize()` method. This function tells curses to use the terminal's default foreground and background colors, which can vary by terminal configuration. In many terminals, the default background is white or light-colored.

When `clear()` was called, it used color pair 0 which was initialized with `-1, -1` (terminal defaults), resulting in the terminal's default background color being used for cleared areas.

## Solution

The fix involved three changes to `ttk/backends/curses_backend.py`:

### 1. Removed `curses.use_default_colors()`

```python
# Before
curses.use_default_colors()

# After
# Removed - we want explicit black background, not terminal defaults
```

### 2. Explicitly Initialize Color Pair 1 with Black Background

```python
# Initialize color pair 1 with white on black for default background
curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
self.color_pairs_initialized.add(1)
```

### 3. Set Window Background to Black

```python
# Set black background for the entire terminal window
# This ensures all areas have black background, not terminal default
self.stdscr.bkgd(' ', curses.color_pair(1))
```

The `bkgd()` function sets the background character and attributes for the entire window. By setting it to use color pair 1 (white on black), all cleared areas and empty spaces now display with a black background.

## Implementation Details

### Modified Method: `initialize()`

The `initialize()` method now:
1. Initializes curses without `use_default_colors()`
2. Creates color pair 1 with white foreground and black background
3. Sets the window background using `bkgd()` with color pair 1

### Unchanged Method: `clear()`

The `clear()` method continues to use `stdscr.clear()` as before. Since the window background is now set to black via `bkgd()`, the cleared areas automatically use the black background.

## Testing

To verify the fix works correctly:

```bash
# Run the verification script
python ttk/test/verify_curses_black_background.py

# Or run the full demo
cd ttk && make demo-ttk BACKEND=curses
```

You should see:
- Black background throughout the entire terminal
- Colored text on black backgrounds
- No white or light-colored areas

## Compatibility

This fix ensures consistent black backgrounds across different terminal emulators:
- macOS Terminal
- iTerm2
- GNOME Terminal
- xterm
- And other curses-compatible terminals

The fix uses standard curses color pairs, so it's compatible with all terminals that support basic 8-color mode.

## Related Files

- `ttk/backends/curses_backend.py` - Main implementation
- `ttk/test/verify_curses_black_background.py` - Verification script
- `ttk/demo/demo_ttk.py` - Demo application that uses the backend

## References

- Python curses documentation: https://docs.python.org/3/library/curses.html
- curses `bkgd()` function: Sets the background character and attributes
- curses `use_default_colors()`: Allows terminal default colors (removed in fix)
