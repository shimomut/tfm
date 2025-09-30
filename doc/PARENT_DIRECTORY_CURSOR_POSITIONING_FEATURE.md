# Parent Directory Cursor Positioning Feature

## Overview

This feature improves the user experience when navigating between parent and child directories in TFM by automatically positioning the cursor on the child directory when navigating to the parent directory using the Backspace key.

## Problem Statement

Previously, when users navigated from a child directory to its parent directory using the Backspace key, the cursor would be positioned based on the saved cursor history or default to the first item. This made it difficult for users to quickly navigate back to the child directory they just came from, as they had to manually locate and select it.

## Solution

The enhanced parent directory navigation behavior now:

1. **Remembers the child directory name** when navigating to parent
2. **Automatically positions the cursor** on the child directory in the parent directory listing
3. **Allows easy return navigation** by simply pressing Enter to go back to the child directory

## Implementation Details

### Key Changes

The main change is in the Backspace key handling logic in `src/tfm_main.py`:

```python
elif key == curses.KEY_BACKSPACE or key == KEY_BACKSPACE_2 or key == KEY_BACKSPACE_1:  # Backspace - go to parent directory
    if current_pane['path'] != current_pane['path'].parent:
        try:
            # Save current cursor position before changing directory
            self.save_cursor_position(current_pane)
            
            # Remember the child directory name we're leaving
            child_directory_name = current_pane['path'].name
            
            current_pane['path'] = current_pane['path'].parent
            current_pane['selected_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()  # Clear selections when changing directory
            self.refresh_files(current_pane)
            
            # Try to set cursor to the child directory we just came from
            cursor_set = False
            for i, file_path in enumerate(current_pane['files']):
                if file_path.name == child_directory_name and file_path.is_dir():
                    current_pane['selected_index'] = i
                    # Adjust scroll offset to keep selection visible
                    self.adjust_scroll_for_selection(current_pane)
                    cursor_set = True
                    break
            
            # If we couldn't find the child directory, try to restore cursor position from history
            if not cursor_set and not self.restore_cursor_position(current_pane):
                # If no history found, default to first item
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
            
            self.needs_full_redraw = True
        except PermissionError:
            self.show_error("Permission denied")
            self.needs_full_redraw = True
```

### Behavior Flow

1. **User presses Backspace** while in a child directory
2. **System remembers** the current directory name (`child_directory_name`)
3. **Navigation occurs** to the parent directory
4. **Files are refreshed** in the parent directory
5. **Cursor positioning logic**:
   - First, try to find the child directory we came from
   - If found, position cursor on that directory
   - If not found (e.g., directory was deleted), fall back to cursor history
   - If no history available, default to first item
6. **Scroll adjustment** ensures the selected directory is visible

### Fallback Mechanisms

The implementation includes robust fallback mechanisms:

1. **Primary**: Position cursor on child directory we came from
2. **Secondary**: Restore cursor position from saved history
3. **Tertiary**: Default to first item (index 0)

## User Experience Benefits

### Before Enhancement
```
/home/user/projects/myproject/src/
├── main.py
├── utils.py
└── tests/
    ├── test_main.py
    └── test_utils.py

User in /home/user/projects/myproject/src/tests/
Presses Backspace → Goes to /home/user/projects/myproject/src/
Cursor position: main.py (first item or from history)
To return to tests/: User must navigate to find "tests/" directory
```

### After Enhancement
```
/home/user/projects/myproject/src/
├── main.py
├── utils.py
└── tests/          ← Cursor automatically positioned here
    ├── test_main.py
    └── test_utils.py

User in /home/user/projects/myproject/src/tests/
Presses Backspace → Goes to /home/user/projects/myproject/src/
Cursor position: tests/ (automatically positioned)
To return to tests/: User simply presses Enter
```

## Edge Cases Handled

### 1. Child Directory No Longer Exists
If the child directory is deleted while the user is in it, the fallback mechanisms ensure graceful handling:
- Attempts to find the child directory (fails)
- Falls back to cursor history restoration
- If no history, defaults to first item

### 2. Root Directory Navigation
When already at the root directory, the condition `current_pane['path'] != current_pane['path'].parent` prevents unnecessary processing.

### 3. Permission Errors
Permission errors during navigation are caught and displayed to the user with appropriate error messages.

### 4. Scroll Adjustment
The `adjust_scroll_for_selection()` method ensures that when the cursor is positioned on the child directory, it remains visible even if it's outside the current scroll view.

## Testing

### Unit Tests
The feature includes comprehensive unit tests in `test/test_parent_directory_navigation.py`:

- **Basic cursor positioning**: Verifies cursor is set to child directory
- **Nonexistent child handling**: Tests fallback when child directory doesn't exist
- **Root directory navigation**: Ensures proper handling at filesystem root

### Demo Script
A demonstration script `demo/demo_parent_directory_cursor_positioning.py` showcases the feature with:
- Interactive navigation demonstration
- Visual feedback showing cursor positioning
- Test directory structure for exploration

## Configuration

This feature works with existing TFM configuration:
- **History settings**: Uses `MAX_HISTORY_ENTRIES` for fallback cursor history
- **Scroll behavior**: Integrates with existing scroll adjustment logic
- **Pane management**: Works with both left and right panes independently

## Compatibility

### Backward Compatibility
- Fully backward compatible with existing TFM installations
- No configuration changes required
- Existing cursor history functionality remains intact

### Storage Support
- Works with all supported storage types (local filesystem, S3, etc.)
- Uses TFMPath abstraction for cross-platform compatibility

## Performance Considerations

### Minimal Overhead
- Single directory name string storage (minimal memory impact)
- Linear search through parent directory files (typically small lists)
- No additional file system operations beyond normal navigation

### Optimization
- Early termination when child directory is found
- Efficient fallback chain prevents unnecessary operations
- Reuses existing scroll adjustment and cursor positioning logic

## Future Enhancements

### Potential Improvements
1. **Multi-level navigation memory**: Remember cursor positions for multiple directory levels
2. **Smart positioning**: Consider file modification times or access patterns
3. **Visual indicators**: Highlight the directory we came from temporarily
4. **Configuration options**: Allow users to disable this behavior if desired

### Integration Opportunities
- **Breadcrumb navigation**: Could integrate with breadcrumb-style navigation
- **Quick navigation**: Could support quick jump-back functionality
- **History visualization**: Could show navigation history in status bar

## Conclusion

The Parent Directory Cursor Positioning feature significantly improves the navigation experience in TFM by making it easier and more intuitive to move between parent and child directories. The implementation is robust, handles edge cases gracefully, and maintains full backward compatibility while providing immediate user experience benefits.