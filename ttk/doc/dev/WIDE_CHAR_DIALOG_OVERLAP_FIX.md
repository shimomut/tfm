# Wide Character Dialog Overlap Fix

## Overview

This document describes the fix for an issue where zenkaku (full-width) characters in the file list pane were still being rendered when a dialog frame overlapped their right half in desktop mode.

## Problem Statement

When a dialog frame is drawn in desktop mode and overlaps the right half of a zenkaku character in the file list pane, the character was still being rendered. This occurred because:

1. Wide characters occupy 2 grid cells: the left cell contains the character with `is_wide=True`, and the right cell contains an empty placeholder `''`
2. When the dialog frame used `draw_hline()` to draw its background over the right cell (placeholder), it only overwrote that cell
3. The left cell still had the wide character with `is_wide=True`, causing it to render across both cells during the next refresh
4. This resulted in the wide character appearing to "bleed through" the dialog frame

## Solution

The fix adds logic to both `draw_hline()` and `draw_text()` methods in the CoreGraphics backend to detect when they're overwriting a placeholder cell and clear the corresponding wide character in the previous cell.

### Implementation Details

**In `draw_hline()` (ttk/backends/coregraphics_backend.py):**

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

**In `draw_text()` (ttk/backends/coregraphics_backend.py):**

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

### Key Design Decisions

1. **Preserve original color**: When clearing a wide character, we replace it with a space but preserve its original color pair. This ensures the background color remains consistent.

2. **Check for empty placeholder**: We only clear the previous cell if the current cell is an empty string `''`, which indicates it's a placeholder for a wide character.

3. **Verify previous cell is wide**: We check that the previous cell has `is_wide=True` and a non-empty character before clearing it.

4. **Replace with space, not empty**: We replace the wide character with a space `' '` rather than an empty string, because empty strings are reserved for placeholders.

## Testing

Comprehensive unit tests were added in `ttk/test/test_wide_char_dialog_overlap.py` to verify:

1. `draw_hline()` clears wide characters when overwriting placeholders
2. `draw_text()` clears wide characters when overwriting placeholders
3. Multiple wide characters are handled correctly with partial overlap
4. Normal ASCII characters are not affected by the fix

All tests pass successfully.

## Visual Result

**Before fix:**
```
File list:          Dialog frame:
あいう              ┌────────┐
                    │        │
                    └────────┘
Result: あ bleeds through the dialog
```

**After fix:**
```
File list:          Dialog frame:
あいう              ┌────────┐
                    │        │
                    └────────┘
Result: Clean dialog, no bleeding
```

## Related Files

- `ttk/backends/coregraphics_backend.py` - Implementation
- `ttk/test/test_wide_char_dialog_overlap.py` - Unit tests
- `src/tfm_base_list_dialog.py` - Dialog frame drawing (uses `draw_hline()`)

## Future Considerations

This fix handles the most common case where dialogs overlap file list content. Similar issues could theoretically occur with other UI elements that use `draw_hline()` or `draw_text()` to overwrite wide characters, but those are now also protected by this fix.

The curses backend does not need this fix because it handles character rendering differently and doesn't use the same grid-based placeholder system.
