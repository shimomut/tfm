# Dialog Redraw Fix

## Problem Description

In the `FileManager.run()` method, there was a bug where dialogs would disappear after the main screen was redrawn, even when the dialogs should remain visible.

### Root Cause

The issue occurred in this sequence:

1. Main screen rendering sets `needs_full_redraw = True`
2. Main interface is drawn (header, files, log pane, status)
3. `needs_full_redraw` is set to `False` after main screen rendering
4. `_draw_dialogs_if_needed()` is called
5. Inside `_draw_dialogs_if_needed()`, the condition checks:
   ```python
   if dialog_content_changed or self.needs_full_redraw:
   ```
6. Since `needs_full_redraw` is now `False`, and if dialog content hasn't changed (`dialog_content_changed` is `False`), dialogs are not redrawn
7. This causes dialogs to disappear from the screen

## Solution

Fixed the timing of when `needs_full_redraw` is reset to `False`. Instead of resetting it immediately after drawing the main screen, it's now reset after both the main screen AND dialogs are rendered.

### Code Changes

**Before:**
```python
def run(self):
    if self.needs_full_redraw:
        # Draw main screen
        self.draw_header()
        self.draw_files()
        self.draw_log_pane()
        self.draw_status()
        self.stdscr.refresh()
        self.needs_full_redraw = False  # ← Problem: reset too early
    
    # Draw dialogs if needed
    self._draw_dialogs_if_needed()  # ← dialogs disappear because flag is False
```

**After:**
```python
def run(self):
    if self.needs_full_redraw:
        # Draw main screen
        self.draw_header()
        self.draw_files()
        self.draw_log_pane()
        self.draw_status()
        self.stdscr.refresh()
        # Don't reset flag yet
    
    # Draw dialogs if needed
    self._draw_dialogs_if_needed()  # ← dialogs are redrawn because flag is still True
    
    # Reset full redraw flag after both main screen and dialogs are rendered
    if self.needs_full_redraw:
        self.needs_full_redraw = False
```

## Benefits

1. **Fixes the disappearing dialog bug**: Dialogs remain visible after main screen redraws
2. **Optimal performance**: Dialogs are only redrawn when needed (content changed or full redraw)
3. **No constant redrawing**: Unlike the initial approach, dialogs aren't constantly redrawn
4. **Maintains existing behavior**: Content change detection still works as before
5. **Simple and clean**: Minimal code change with maximum effectiveness
6. **Comprehensive coverage**: Works for all dialog types:
   - General Purpose Dialog
   - List Dialog
   - Info Dialog
   - Search Dialog
   - Jump Dialog
   - Batch Rename Dialog

## Testing

The fix includes comprehensive unit tests that verify:

- ✅ Dialogs are redrawn when full redraw is needed
- ✅ Dialogs are redrawn when content changes
- ✅ Dialogs are NOT constantly redrawn (performance optimization)
- ✅ Inactive dialogs are not drawn when no redraw is needed
- ✅ Screen refresh occurs when dialogs are drawn
- ✅ Only one dialog is drawn when multiple could be active
- ✅ All dialog types are properly handled

### Running Tests

```bash
python -m pytest test/test_dialog_redraw_fix.py -v
```

### Demo

```bash
python demo/demo_dialog_redraw_fix.py
```

## Technical Details

### Flag Reset Timing

The fix changes when `needs_full_redraw` is reset from `True` to `False`:

- **Before**: Reset immediately after drawing main screen
- **After**: Reset after drawing both main screen AND dialogs

### Redraw Logic

The existing redraw condition remains unchanged and ensures dialogs are drawn in two scenarios:

1. **Content Changed**: Dialog content has been modified (`dialog_content_changed`)
2. **Full Redraw**: Main screen needs complete redraw (`self.needs_full_redraw`)

By delaying the flag reset, dialogs get the chance to be redrawn when a full redraw is needed, preventing them from disappearing.

## Files Modified

- `src/tfm_main.py`: Modified `_draw_dialogs_if_needed()` method
- `test/test_dialog_redraw_fix.py`: Added comprehensive unit tests
- `demo/demo_dialog_redraw_fix.py`: Added demonstration script
- `doc/DIALOG_REDRAW_FIX.md`: This documentation file

## Backward Compatibility

This fix is fully backward compatible and doesn't change any existing APIs or behavior. It only fixes the bug where dialogs would disappear inappropriately.