# Wide Character Dialog Overlap Fix

## Overview

This document describes the fix for issues where zenkaku (full-width) characters in the file list pane were improperly rendered when a dialog frame overlapped them. The fix addresses different issues in both desktop mode (CoreGraphics backend) and terminal mode (curses backend).

## Problem Statement

### Desktop Mode (CoreGraphics Backend)

When a dialog frame is drawn in desktop mode and overlaps the right half of a zenkaku character in the file list pane, the character was still being rendered. This occurred because:

1. Wide characters occupy 2 grid cells: the left cell contains the character with `is_wide=True`, and the right cell contains an empty placeholder `''`
2. When the dialog frame used `draw_hline()` to draw its background over the right cell (placeholder), it only overwrote that cell
3. The left cell still had the wide character with `is_wide=True`, causing it to render across both cells during the next refresh
4. This resulted in the wide character appearing to "bleed through" the dialog frame

### Terminal Mode (Curses Backend)

In curses mode, when a dialog frame overlaps the right half of a zenkaku character:

1. The right half gets filled with the dialog's background color instead of the original character's background color
2. After the dialog closes, the wide character is broken and doesn't render properly
3. Following characters shift left by one hankaku (half-width) position, breaking the layout

The curses backend didn't track wide characters, so it couldn't detect when it was overwriting part of a wide character.

## Solution

### CoreGraphics Backend Fix

The fix adds logic to both `draw_hline()` and `draw_text()` methods to detect when they're overwriting a placeholder cell and clear the corresponding wide character in the previous cell.

**Implementation in `draw_hline()` (ttk/backends/coregraphics_backend.py):**

```python
for c in range(start_col, end_col):
    # Check if overwriting a placeholder
    current_char, current_color, current_attrs, current_is_wide = self.grid[row][c]
    
    if c > 0 and current_char == '':
        prev_char, prev_color, prev_attrs, prev_is_wide = self.grid[row][c - 1]
        if prev_is_wide and prev_char != '':
            # Clear the wide character by replacing with space
            self.grid[row][c - 1] = (' ', prev_color, prev_attrs, False)
    
    # Write the new character
    self.grid[row][c] = (char, color_pair, 0, is_wide)
```

**Implementation in `draw_text()` (ttk/backends/coregraphics_backend.py):**

```python
# Check if starting position overwrites a placeholder
if col > 0:
    current_char, current_color, current_attrs, current_is_wide = self.grid[row][col]
    
    if current_char == '':
        prev_char, prev_color, prev_attrs, prev_is_wide = self.grid[row][col - 1]
        if prev_is_wide and prev_char != '':
            # Clear the wide character
            self.grid[row][col - 1] = (' ', prev_color, prev_attrs, False)
```

### Curses Backend Fix

The curses backend now uses grid-based tracking to detect when it's about to overwrite part of a wide character. When `draw_text()` detects it's about to overwrite a placeholder cell (the right half of a wide character), it clears both halves using the original background color before drawing the new content.

**Why Grid Tracking is Necessary:**

Initially, we attempted to use curses' `inch()` API to read back what's currently on the screen. However, `inch()` has a critical limitation: it only returns 8-bit characters (the bottom 8 bits of the character code). This means:

```python
prev_ch_attr = self.stdscr.inch(row, col - 1)
prev_char = chr(prev_ch_attr & 0xFF)  # Only gets bottom 8 bits!
```

For Unicode wide characters like Japanese text (code points > 255), `chr(prev_ch_attr & 0xFF)` cannot represent the actual character. For example:
- "あ" (U+3042) becomes chr(0x42) = "B"
- "日" (U+65E5) becomes chr(0xE5) = "å"

This causes `_is_wide_character(prev_char)` to always return False, making it impossible to detect wide characters using `inch()`.

Therefore, we must maintain a grid to track what characters are on screen, including their wide character status.

**Key changes in `ttk/backends/curses_backend.py`:**

**Added grid tracking in `__init__()`:**
```python
# Grid for tracking wide characters
# Each cell stores: (char, color_pair, attributes, is_wide)
# This is necessary because curses inch() only returns 8-bit characters,
# which cannot represent Unicode wide characters (e.g., Japanese text)
self.grid = None  # Will be initialized in initialize()
self.rows = 0
self.cols = 0
```

**Initialize grid in `initialize()`:**
```python
# Initialize grid for tracking wide characters
self.rows, self.cols = self.stdscr.getmaxyx()
self.grid = [[(' ', 0, 0, False) for _ in range(self.cols)] for _ in range(self.rows)]
```

**Update grid on resize in `run_event_loop_iteration()`:**
```python
# Handle resize event separately (it's a system event, not a key event)
if key == curses.KEY_RESIZE:
    # Update grid dimensions on resize
    new_rows, new_cols = self.stdscr.getmaxyx()
    if new_rows != self.rows or new_cols != self.cols:
        self.rows = new_rows
        self.cols = new_cols
        self.grid = [[(' ', 0, 0, False) for _ in range(self.cols)] for _ in range(self.rows)]
    
    event = SystemEvent(event_type=SystemEventType.RESIZE)
    self.event_callback.on_system_event(event)
    return
```

**Reset grid in `clear()`:**
```python
def clear(self) -> None:
    self.stdscr.erase()
    
    # Reset grid to empty state
    if self.grid:
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col] = (' ', 0, 0, False)
```

**Updated `draw_text()` to use grid-based detection:**
```python
# Check if starting position overwrites a wide character placeholder
if 0 <= row < self.rows and 0 < col < self.cols:
    current_char, current_color, current_attrs, current_is_wide = self.grid[row][col]
    
    # If current position is a placeholder (empty string), check if previous cell has a wide char
    if current_char == '':
        prev_char, prev_color, prev_attrs, prev_is_wide = self.grid[row][col - 1]
        
        # If previous character is wide, clear both cells with original background color
        if prev_is_wide and prev_char != '':
            # Build curses attributes for clearing
            prev_attr = curses.color_pair(prev_color)
            # ... apply attributes ...
            
            # Clear both cells with spaces using original background color
            self.stdscr.addstr(row, col - 1, '  ', prev_attr)
            
            # Update grid to reflect clearing
            self.grid[row][col - 1] = (' ', prev_color, prev_attrs, False)
            self.grid[row][col] = (' ', prev_color, prev_attrs, False)

# Draw the text and update grid
self.stdscr.addstr(row, col, text, attr)

# Update grid to track what we drew
current_col = col
for char in text:
    if current_col >= self.cols:
        break
    
    is_wide = _is_wide_character(char)
    self.grid[row][current_col] = (char, color_pair, attributes, is_wide)
    
    if is_wide:
        # Wide character occupies 2 cells
        current_col += 1
        if current_col < self.cols:
            # Mark the second cell as a placeholder
            self.grid[row][current_col] = ('', color_pair, attributes, False)
    
    current_col += 1
```

### Key Design Decisions

1. **Preserve original color**: When clearing a wide character, we replace it with a space but preserve its original color pair. This ensures the background color remains consistent and prevents the dialog's background color from bleeding into the file list area.

2. **Check for empty placeholder**: We only clear the previous cell if the current cell is an empty string `''`, which indicates it's a placeholder for a wide character.

3. **Verify previous cell is wide**: We check that the previous cell has `is_wide=True` and a non-empty character before clearing it.

4. **Replace with space, not empty**: We replace the wide character with a space `' '` rather than an empty string, because empty strings are reserved for placeholders.

5. **Clear before drawing (curses)**: In the curses backend, we clear both cells with the original background color before the dialog draws its content, preventing layout breakage.

## Testing

Comprehensive unit tests were added for both backends:

- `ttk/test/test_wide_char_dialog_overlap.py` - CoreGraphics backend tests
- `ttk/test/test_curses_wide_char_dialog_overlap.py` - Curses backend tests

Tests verify:
1. Wide characters are properly cleared when dialogs overwrite placeholders
2. Original background colors are preserved
3. Multiple wide characters are handled correctly with partial overlap
4. Normal ASCII characters are not affected by the fix
5. Layout doesn't break after dialog closes (curses)

All tests pass successfully.

## Visual Result

**Before fix (Desktop mode):**
```
File list:          Dialog frame:
あいう              ┌────────┐
                    │        │
                    └────────┘
Result: あ bleeds through the dialog
```

**Before fix (Terminal mode):**
```
File list:          Dialog frame:
あいう              ┌────────┐
                    │        │ (right half has dialog color)
                    └────────┘
After dialog closes: Layout broken, characters shifted
```

**After fix (Both modes):**
```
File list:          Dialog frame:
あいう              ┌────────┐
                    │        │
                    └────────┘
Result: Clean dialog, no bleeding, layout preserved
```

## Related Files

- `ttk/backends/coregraphics_backend.py` - CoreGraphics backend implementation
- `ttk/backends/curses_backend.py` - Curses backend implementation
- `ttk/test/test_wide_char_dialog_overlap.py` - CoreGraphics backend tests
- `ttk/test/test_curses_wide_char_dialog_overlap.py` - Curses backend tests
- `src/tfm_base_list_dialog.py` - Dialog frame drawing (uses `draw_hline()`)

## Future Considerations

This fix handles the most common case where dialogs overlap file list content. Similar issues could theoretically occur with other UI elements that use `draw_hline()` or `draw_text()` to overwrite wide characters, but those are now also protected by this fix.

The curses backend uses grid-based tracking to maintain information about wide characters. While this requires additional memory (approximately 16 bytes per cell for a typical 80x24 terminal = ~30KB), it's necessary because curses' `inch()` API cannot reliably detect Unicode wide characters due to its 8-bit limitation. This approach ensures correct rendering of wide characters across all scenarios.
