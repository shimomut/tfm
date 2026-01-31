# Directory Diff Viewer Pane Focus Implementation

## Overview

This document describes the implementation of pane-level focus in DirectoryDiffViewer, which enables users to switch focus between the left and right panes. This feature prepares the viewer for future copy operations between directories.

## Implementation Details

### State Management

Added a new state variable to track which pane is currently active:

```python
# Pane focus state (for future copy operations)
self.active_pane = 'left'  # 'left' or 'right'
```

The active pane is initialized to `'left'` by default.

### Key Binding

The Left/Right arrow keys switch focus between panes (Tab also works as an alternate):

```python
elif event.key_code == KeyCode.RIGHT:
    # Check for Shift modifier for tree navigation
    if event.modifiers & ModifierKey.SHIFT:
        # Shift+Right: Expand directory or move to first child
        ...
    else:
        # Right arrow without modifier: Switch to right pane
        if self.active_pane != 'right':
            old_pane = self.active_pane
            self.active_pane = 'right'
            self.logger.info(f"Switched focus from {old_pane} to right pane")
            self.mark_dirty()
    return True

elif event.key_code == KeyCode.LEFT:
    # Check for Shift modifier for tree navigation
    if event.modifiers & ModifierKey.SHIFT:
        # Shift+Left: Collapse directory or move to parent
        ...
    else:
        # Left arrow without modifier: Switch to left pane
        if self.active_pane != 'left':
            old_pane = self.active_pane
            self.active_pane = 'left'
            self.logger.info(f"Switched focus from {old_pane} to left pane")
            self.mark_dirty()
    return True
```

Tree navigation (collapse/expand/parent/child) now requires the Shift modifier with Left/Right keys.

### Visual Indicator

The active pane is indicated by:
1. **Bold text** in the header for the active pane's directory path
2. **Different background color** for the focused item using existing color pairs:
   - **Active pane** (where focus is): Uses focused colors (blue background)
     - `COLOR_DIRECTORIES_FOCUSED` for directories
     - `COLOR_REGULAR_FILE_FOCUSED` for files
   - **Inactive pane** (where focus is not): Uses focused_inactive colors (gray background)
     - `COLOR_DIRECTORIES_FOCUSED_INACTIVE` for directories
     - `COLOR_REGULAR_FILE_FOCUSED_INACTIVE` for files

This means the focused item appears in both left and right columns, but with different background colors to indicate which pane is currently active.

```python
# Apply bold attribute to active pane
left_attrs = status_attrs | TextAttribute.BOLD if self.active_pane == 'left' else status_attrs
right_attrs = status_attrs | TextAttribute.BOLD if self.active_pane == 'right' else status_attrs

# Draw left pane header
left_text = left_label + left_padding
renderer.draw_text(0, 0, left_text, status_color_pair, left_attrs)
```

The focused item uses different colors based on which pane is active:
```python
def _get_node_colors(self, node: TreeNode, is_focused: bool, pane: str = 'left') -> tuple:
    if is_focused:
        # Focused nodes use focused/inactive color pairs based on which pane is active
        # Active pane uses focused colors (blue background)
        # Inactive pane uses focused_inactive colors (gray background)
        is_active_pane = (pane == self.active_pane)
        
        if node.is_directory:
            if is_active_pane:
                return get_color_with_attrs(COLOR_DIRECTORIES_FOCUSED)
            else:
                return get_color_with_attrs(COLOR_DIRECTORIES_FOCUSED_INACTIVE)
        else:
            if is_active_pane:
                return get_color_with_attrs(COLOR_REGULAR_FILE_FOCUSED)
            else:
                return get_color_with_attrs(COLOR_REGULAR_FILE_FOCUSED_INACTIVE)
```

### Status Bar Update

The status bar now includes a hint for the Left/Right keys:

```
?:help  q:quit  ←/→:switch-pane  i:toggle-identical
```

## Cursor Synchronization

The cursor position remains synchronized between panes. When switching focus with Tab:
- The cursor stays at the same position in the tree
- Navigation keys (up/down/page up/page down) work the same regardless of focused pane
- The focused item remains highlighted

This design ensures that:
1. Users can easily compare items at the same position in both panes
2. Future copy operations will work on the currently selected item
3. The interface remains intuitive and predictable

## Future Enhancements

This pane focus feature prepares for future copy operations:

1. **Copy from left to right**: When right pane is focused, copy selected item from left
2. **Copy from right to left**: When left pane is focused, copy selected item from right
3. **Visual feedback**: Show which direction the copy will occur based on focused pane
4. **Keyboard shortcuts**: Add keys like 'c' for copy operations

## Testing

Test coverage includes:
- Initial focus state (left pane)
- Tab key switching between panes
- Focus indicator display in header
- Cursor position synchronization
- Status bar hint display

See `test/test_directory_diff_pane_focus.py` for complete test suite.

## Demo

A demo script is available at `demo/demo_directory_diff_pane_focus.py` that showcases:
- Tab key switching between panes
- Focus indicator movement
- Synchronized cursor navigation
- Preparation for copy operations

## Design Rationale

### Why Left/Right Keys?

The Left/Right arrow keys are a natural choice for switching between panes because:
- They directly correspond to the spatial layout (left pane / right pane)
- They're easily accessible on all keyboards
- They provide intuitive directional navigation
- Tab is kept as an alternate for users who prefer it

### Why Shift+Left/Right for Tree Navigation?

Tree operations (collapse/expand/parent/child) are less frequent than pane switching, so:
- Shift modifier makes sense for these secondary operations
- Keeps the primary Left/Right keys available for the more common pane switching
- Still accessible but requires intentional use

### Why Synchronized Cursor?

Keeping the cursor synchronized between panes provides several benefits:
- Users can easily compare items at the same position
- Copy operations will work on corresponding items
- Navigation remains predictable and intuitive
- Reduces cognitive load when switching between panes

### Why Bold Header and Existing Color Pairs?

The combination of bold header text and existing focused/inactive color pairs provides several benefits:
- **Bold header text** clearly shows which pane is active without adding extra characters
- **Reuses existing color system**: No need for new color constants
  - Active pane uses standard focused colors (blue background)
  - Inactive pane uses focused_inactive colors (gray background)
- **Focused item appears in both columns** with different backgrounds to show which pane is active
- Consistent with the rest of TFM's dual-pane interface
- Doesn't clutter the interface with extra symbols
- Uses standard text attributes available in all terminals
- Color differentiation helps users quickly identify which pane they're working in

## Related Files

- `src/tfm_directory_diff_viewer.py` - Main implementation
- `test/test_directory_diff_pane_focus.py` - Test suite
- `demo/demo_directory_diff_pane_focus.py` - Demo script
- `doc/DIRECTORY_DIFF_VIEWER_FEATURE.md` - User documentation (to be updated)
