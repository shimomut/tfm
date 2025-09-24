# Dialog Rendering Optimization

## Overview

This document describes the optimization implemented to reduce unnecessary dialog rendering in TFM (Terminal File Manager). Previously, dialogs were being rendered constantly on every frame, even when their content hadn't changed. This optimization introduces content change tracking to only trigger redraws when necessary.

## Problem

The original implementation in the main loop (`src/tfm_main.py`) was rendering all active dialogs on every iteration:

```python
# Always draw dialog overlays on top (they need to update every frame for cursor/text changes)
dialog_drawn = False
if self.general_dialog.is_active:
    self.general_dialog.draw(self.stdscr, self.safe_addstr)
    dialog_drawn = True
elif self.list_dialog.mode:
    self.list_dialog.draw(self.stdscr, self.safe_addstr)
    dialog_drawn = True
# ... etc for all dialog types
```

This caused unnecessary CPU usage and potential screen flicker, especially noticeable on slower systems or when running over network connections.

## Solution

### Content Change Tracking

Added a `content_changed` boolean flag to all dialog classes:

- `GeneralPurposeDialog`
- `ListDialog` 
- `InfoDialog`
- `SearchDialog`
- `JumpDialog`
- `BatchRenameDialog`

### Main Loop Optimization

Modified the main rendering loop to only draw dialogs when their content has actually changed:

```python
# Only draw dialog overlays when content has changed or full redraw is needed
dialog_drawn = False
dialog_content_changed = self._check_dialog_content_changed()

if dialog_content_changed or self.needs_full_redraw:
    if self.general_dialog.is_active:
        self.general_dialog.draw(self.stdscr, self.safe_addstr)
        dialog_drawn = True
    # ... etc for all dialog types
    
    # Mark dialog content as unchanged after drawing
    if dialog_drawn:
        self._mark_dialog_content_unchanged()
```

### Content Change Detection

Added helper methods to track and manage content changes:

- `_check_dialog_content_changed()`: Checks if any active dialog has changed content
- `_mark_dialog_content_unchanged()`: Marks all active dialogs as having unchanged content

### When Content Changes Are Triggered

Content is marked as changed in the following scenarios:

1. **Dialog Show/Hide**: When dialogs are shown or hidden
2. **Text Input**: When users type in text fields
3. **Navigation**: When users navigate through lists or scroll content
4. **Search Results**: When search results are updated (threaded operations)
5. **Directory Scanning**: When directory lists are updated (threaded operations)
6. **Field Switching**: When switching between input fields in batch rename dialog

## Implementation Details

### Dialog Classes Modified

#### GeneralPurposeDialog (`src/tfm_general_purpose_dialog.py`)
- Added `content_changed = True` in `__init__`
- Mark content changed in `show_status_line_input()`, `hide()`, and text input handling

#### ListDialog (`src/tfm_list_dialog.py`)
- Added `content_changed = True` in `__init__`
- Mark content changed in `show()`, `exit()`, navigation, and filtering

#### InfoDialog (`src/tfm_info_dialog.py`)
- Added `content_changed = True` in `__init__`
- Mark content changed in `show()`, `exit()`, and all scroll operations

#### SearchDialog (`src/tfm_search_dialog.py`)
- Added `content_changed = True` in `__init__`
- Mark content changed in `show()`, `exit()`, search type switching, navigation, and result updates

#### JumpDialog (`src/tfm_jump_dialog.py`)
- Added `content_changed = True` in `__init__`
- Mark content changed in `show()`, `exit()`, navigation, filtering, and directory updates

#### BatchRenameDialog (`src/tfm_batch_rename_dialog.py`)
- Added `content_changed = True` in `__init__`
- Mark content changed in `show()`, `exit()`, field switching, scrolling, and text input

### Threading Considerations

Special attention was paid to threaded operations in `SearchDialog` and `JumpDialog`:

- Search result updates in background threads mark content as changed
- Directory scanning updates mark content as changed
- Thread-safe access to the `content_changed` flag using existing locks

## Performance Impact

### Measured Improvements

The demo script (`demo/demo_dialog_rendering_optimization.py`) shows:

- **77.8% reduction** in draw calls for typical usage scenarios
- Only 2 draws instead of 9 in a common interaction sequence
- Significant reduction in CPU usage during dialog interactions

### Benefits

1. **Reduced CPU Usage**: Eliminates unnecessary rendering operations
2. **Better Responsiveness**: Less time spent on redundant drawing
3. **Reduced Screen Flicker**: Fewer screen updates mean smoother visual experience
4. **Network Efficiency**: Important for remote terminal sessions
5. **Battery Life**: Lower CPU usage on laptops

## Testing

### Test Coverage

Created comprehensive tests to verify the optimization:

- `test/test_simple_dialog_optimization.py`: Basic content change tracking verification
- `demo/demo_dialog_rendering_optimization.py`: Performance demonstration

### Test Results

All tests pass, confirming:
- Content change flags are properly initialized
- Content changes are detected correctly
- Optimization reduces rendering calls as expected
- All dialog types support the optimization

## Backward Compatibility

This optimization is fully backward compatible:
- No changes to public APIs
- No changes to user-visible behavior
- Only internal rendering logic is optimized
- All existing functionality remains intact

## Future Enhancements

Potential future improvements:
1. **Granular Change Tracking**: Track which specific parts of dialogs changed
2. **Dirty Rectangle Optimization**: Only redraw changed regions
3. **Animation Optimization**: Special handling for animated elements
4. **Metrics Collection**: Track rendering performance in production

## Conclusion

This optimization significantly improves TFM's performance by eliminating unnecessary dialog rendering. The implementation is clean, maintainable, and provides substantial performance benefits while maintaining full backward compatibility.

The optimization is particularly beneficial for:
- Users on slower systems
- Remote terminal sessions over network
- Battery-powered devices
- High-frequency dialog interactions

The change demonstrates how targeted optimizations can provide significant performance improvements with minimal code complexity.