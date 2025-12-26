# Double-Click Support Implementation

This document describes the technical implementation of double-click support in TFM.

## Architecture Overview

Double-click support is implemented across three layers:

1. **Backend Layer** (TTK CoreGraphics): Detects double-clicks from native OS events
2. **Event Routing Layer** (TFMEventCallback, UILayerStack): Routes events to UI components
3. **UI Component Layer** (FileManager, DirectoryDiffViewer): Handles double-click actions

## Backend Implementation

### Double-Click Detection

Location: `ttk/backends/coregraphics_backend.py`

The CoreGraphics backend detects double-clicks using macOS NSEvent's `clickCount()` method:

```python
# In _handle_mouse_event()
if ns_event_type in button_event_types and event.clickCount() == 2:
    mouse_event_type = MouseEventType.DOUBLE_CLICK
```

Key points:
- Only button down events can be double-clicks (not wheel events)
- The OS determines the timing threshold (typically 0.5 seconds)
- Click count is automatically tracked by the native event system
- No manual timing logic needed in TFM

### Event Type

Location: `ttk/ttk_mouse_event.py`

Double-click is a distinct event type in the MouseEventType enum:

```python
class MouseEventType(Enum):
    BUTTON_DOWN = "button_down"
    BUTTON_UP = "button_up"
    DOUBLE_CLICK = "double_click"  # Separate from BUTTON_DOWN
    MOVE = "move"
    WHEEL = "wheel"
    DRAG = "drag"
```

This allows components to distinguish between single clicks and double-clicks.

## Event Routing

Double-click events follow the same routing path as other mouse events:

1. Backend creates `MouseEvent` with `event_type=MouseEventType.DOUBLE_CLICK`
2. `TFMEventCallback.on_mouse_event()` receives the event
3. `UILayerStack.handle_mouse_event()` routes to topmost layer
4. Top layer's `handle_mouse_event()` processes the event

No special routing logic is needed for double-clicks.

## UI Component Implementation

### FileManager

Location: `src/tfm_main.py`, method `handle_mouse_event()`

Double-click handling in FileManager:

```python
if event.event_type == MouseEventType.DOUBLE_CLICK:
    # Check if double-click is on header (row 0) - go to parent directory
    if event.row == 0:
        # Determine which pane header was clicked
        if event.column < left_pane_width:
            target_pane = 'left'
        else:
            target_pane = 'right'
        
        # Switch to the clicked pane if not already active
        if self.pane_manager.active_pane != target_pane:
            self.pane_manager.active_pane = target_pane
        
        # Navigate to parent directory (same as Backspace key)
        self._action_go_parent()
        return True
    
    # Check if event is within file pane area
    if event.row < 1 or event.row >= file_pane_bottom:
        return False
    
    # Determine which pane was double-clicked
    if event.column < left_pane_width:
        pane_data = self.pane_manager.left_pane
        target_pane = 'left'
    else:
        pane_data = self.pane_manager.right_pane
        target_pane = 'right'
    
    # Calculate clicked file index
    clicked_file_index = event.row - 1 + pane_data['scroll_offset']
    
    # Validate and handle
    if pane_data['files'] and 0 <= clicked_file_index < len(pane_data['files']):
        # Switch pane if needed
        if self.pane_manager.active_pane != target_pane:
            self.pane_manager.active_pane = target_pane
        
        # Move cursor to clicked item
        pane_data['focused_index'] = clicked_file_index
        
        # Trigger same action as Enter key
        self.handle_enter()
        self.mark_dirty()
        
        return True
```

Key implementation details:
- Header detection: `event.row == 0` identifies header clicks
- Parent navigation: Calls `_action_go_parent()` for header double-clicks
- Bounds checking ensures clicks are within file pane area
- Pane detection uses column position and `left_pane_width`
- File index calculation accounts for scroll offset
- Pane focus switches automatically if needed
- Cursor moves to clicked item before action
- `handle_enter()` performs the actual open/navigate action
- No code duplication - reuses existing Enter key and Backspace logic

### DirectoryDiffViewer

Location: `src/tfm_directory_diff_viewer.py`, method `handle_mouse_event()`

Double-click handling in DirectoryDiffViewer:

```python
if event.event_type == MouseEventType.DOUBLE_CLICK:
    # Check if click is within tree view area
    tree_view_start = 1
    tree_view_end = height - 5
    
    if event.row < tree_view_start or event.row >= tree_view_end:
        return False
    
    # Calculate clicked item index
    clicked_item_index = event.row - tree_view_start + self.scroll_offset
    
    # Validate and handle
    if self.visible_nodes and 0 <= clicked_item_index < len(self.visible_nodes):
        # Move cursor to clicked item
        self.cursor_position = clicked_item_index
        
        # Trigger same action as Enter key
        node = self.visible_nodes[self.cursor_position]
        if node.is_directory:
            # Toggle expand/collapse
            if node.is_expanded:
                self.collapse_node(self.cursor_position)
            else:
                self.expand_node(self.cursor_position)
        else:
            # Open file diff
            self.open_file_diff(self.cursor_position)
        
        return True
```

Key implementation details:
- Tree view bounds calculated from display height
- Item index accounts for scroll offset
- Cursor moves to clicked item
- Directory nodes toggle expand/collapse state
- File nodes open diff viewer
- Reuses existing `expand_node()`, `collapse_node()`, and `open_file_diff()` methods

## Design Principles

### Code Reuse

Double-click handlers reuse existing Enter key logic:
- FileManager: Calls `handle_enter()`
- DirectoryDiffViewer: Calls `expand_node()`, `collapse_node()`, `open_file_diff()`

This ensures:
- Consistent behavior between keyboard and mouse
- No code duplication
- Single source of truth for action logic
- Easier maintenance

### Bounds Checking

All double-click handlers perform bounds checking:
- Vertical: Check if row is within component area
- Horizontal: Check if column is within pane (FileManager only)
- Index: Validate calculated index is within valid range

This prevents:
- Crashes from out-of-bounds access
- Unintended actions from clicks in wrong areas
- Interference with other UI elements

### Pane Focus Management

FileManager automatically switches pane focus on double-click:
- Detects which pane was clicked
- Switches focus if clicking inactive pane
- Moves cursor to clicked item
- Performs action in newly focused pane

This provides intuitive behavior:
- No need to manually switch panes first
- Single double-click navigates anywhere
- Consistent with modern file manager UX

## Testing

Test coverage: `test/test_double_click_support.py`

Tests verify:
- Double-click header goes to parent (FileManager)
- Double-click header switches pane focus (FileManager)
- Double-click opens directories (FileManager)
- Double-click opens files (FileManager)
- Double-click switches pane focus (FileManager)
- Double-click outside file area ignored (FileManager)
- Double-click expands directories (DirectoryDiffViewer)
- Double-click collapses directories (DirectoryDiffViewer)
- Double-click opens file diff (DirectoryDiffViewer)
- Double-click outside tree area ignored (DirectoryDiffViewer)

All tests use mocking to avoid filesystem dependencies.

## Future Enhancements

Potential improvements:
- Double-click in text viewer to select word
- Double-click in diff viewer to jump to next difference
- Configurable double-click actions
- Double-click on status bar elements for quick actions

## Related Components

- `ttk/backends/coregraphics_backend.py` - Double-click detection
- `ttk/ttk_mouse_event.py` - MouseEvent data structure
- `src/tfm_main.py` - FileManager double-click handling
- `src/tfm_directory_diff_viewer.py` - DirectoryDiffViewer double-click handling
- `src/tfm_ui_layer.py` - Event routing infrastructure

## References

- User documentation: `doc/DOUBLE_CLICK_FEATURE.md`
- Mouse support overview: `doc/dev/MOUSE_SUPPORT_IMPLEMENTATION.md`
- Event routing: `doc/dev/EVENT_ROUTING_SYSTEM.md`
