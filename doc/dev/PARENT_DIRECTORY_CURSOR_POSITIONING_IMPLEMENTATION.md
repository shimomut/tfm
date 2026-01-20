# Parent Directory Cursor Positioning Implementation

## Overview

This document describes the implementation of improved cursor positioning when navigating to parent directories in TFM. When the user navigates to a parent directory, the cursor automatically focuses on the child directory they just came from, making navigation more intuitive.

## Affected Actions

Three navigation actions were updated to implement this behavior:

1. **`go_parent`** - Triggered by Backspace key or menu command
2. **`nav_left`** - Triggered by LEFT arrow key (when in left pane)
3. **`nav_right`** - Triggered by RIGHT arrow key (when in right pane)

## Implementation Details

### Previous Behavior

Before this change, when navigating to a parent directory:
- The cursor position was restored from history (if available)
- If no history existed, the cursor defaulted to the first item (index 0)
- This could be disorienting as the user lost track of which directory they came from

### New Behavior

After this change, when navigating to a parent directory:
1. The child directory name is remembered before navigation
2. After refreshing the parent directory's file list, the code searches for the child directory
3. If found, the cursor is positioned on that directory
4. The scroll offset is adjusted to ensure the focused item is visible
5. If the child directory is not found (e.g., it was deleted), the cursor stays at index 0

### Code Changes

All three actions now follow this pattern:

```python
# Remember the child directory name we're leaving
child_dir_name = current_pane['path'].name

# Navigate to parent
current_pane['path'] = current_pane['path'].parent
current_pane['focused_index'] = 0
current_pane['scroll_offset'] = 0
current_pane['selected_files'].clear()
self.refresh_files(current_pane)

# Focus on the child directory we just came from
for i, file_path in enumerate(current_pane['files']):
    if file_path.name == child_dir_name:
        current_pane['focused_index'] = i
        
        # Adjust scroll offset to keep focused item visible
        height, width = self.renderer.get_dimensions()
        display_height = height - 4  # Account for header, status bar, etc.
        
        if current_pane['focused_index'] < current_pane['scroll_offset']:
            current_pane['scroll_offset'] = current_pane['focused_index']
        elif current_pane['focused_index'] >= current_pane['scroll_offset'] + display_height:
            current_pane['scroll_offset'] = current_pane['focused_index'] - display_height + 1
        
        break
```

### Scroll Offset Adjustment

The scroll offset adjustment ensures the focused item is visible:
- If the focused item is above the visible area, scroll up to show it
- If the focused item is below the visible area, scroll down to show it
- The calculation accounts for the display height (terminal height minus UI elements)

## Edge Cases

### Child Directory Not Found

If the child directory is not found in the parent (e.g., it was deleted or renamed):
- The cursor remains at index 0 (first item)
- No error is raised
- This is the same fallback behavior as before

### At Root Directory

When already at the root directory:
- The navigation is skipped entirely
- No changes are made to cursor position or scroll offset
- This behavior is unchanged from before

### Permission Errors

For `nav_left` and `nav_right` actions:
- Permission errors are caught and logged
- The navigation is aborted
- The cursor position remains unchanged

## Files Modified

- `src/tfm_main.py` - Updated three action handlers:
  - `_action_go_parent()` (line ~1515)
  - `nav_left` action handler (line ~4532)
  - `nav_right` action handler (line ~4555)

## Testing

### Manual Testing

Use the demo script to verify the behavior:
```bash
python demo/demo_parent_directory_cursor_positioning.py
```

Test scenarios:
1. Navigate into a subdirectory and press Backspace
2. Navigate into a subdirectory and use LEFT arrow (in left pane)
3. Navigate into a subdirectory and use RIGHT arrow (in right pane)
4. Navigate into a deeply nested directory that would be off-screen
5. Navigate to parent when at root (should do nothing)

### Automated Testing

Test file: `test/test_parent_directory_cursor_positioning.py`

Test cases:
- Cursor focuses on child directory after go_parent
- Scroll offset adjusts for visibility
- At root directory does nothing
- Child directory not found keeps default position

## User Experience Impact

### Benefits

1. **Improved orientation** - Users always know which directory they came from
2. **Faster navigation** - No need to search for the previous directory
3. **Consistent behavior** - Works the same for all three navigation methods
4. **Better for deep hierarchies** - Especially helpful when navigating complex directory structures

### Backward Compatibility

This change is fully backward compatible:
- No configuration changes required
- No API changes
- Existing key bindings work the same way
- The behavior is a pure enhancement with no breaking changes

## Related Features

- **Cursor History** - The existing cursor history system (`save_cursor_position`/`restore_cursor_position`) is still used for other navigation scenarios
- **Directory Navigation** - This complements the existing directory navigation features
- **Dual Pane Mode** - Works correctly in both single and dual pane modes

## Future Enhancements

Potential improvements for future consideration:
1. Make this behavior configurable (some users might prefer the old behavior)
2. Extend to other navigation scenarios (e.g., after creating a new directory)
3. Add visual indication when the cursor is positioned on the "previous" directory
