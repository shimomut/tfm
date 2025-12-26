# Mouse Event Support Implementation Guide

## Overview

This document provides comprehensive implementation details for the mouse event support system in TFM. It covers the MouseEvent API, coordinate system, backend implementations, and guidance for extending the system with future features like drag-and-drop.

**Target Audience**: Developers working on TFM internals, TTK backend implementations, or extending mouse event functionality.

**Related Documentation**:
- End-user guide: `doc/MOUSE_EVENT_SUPPORT_FEATURE.md`
- Design document: `.kiro/specs/mouse-event-support/design.md`
- Requirements: `.kiro/specs/mouse-event-support/requirements.md`

## Architecture Overview

The mouse event system follows a three-layer architecture:

```
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                      │
│  - TFM components (FilePane, dialogs, etc.)            │
│  - Implements handle_mouse_event() method              │
│  - Uses is_point_inside() for bounds checking          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                    TTK API Layer                        │
│  - MouseEvent data structure                            │
│  - Backend interface (supports_mouse, poll_mouse_event) │
│  - Coordinate transformation utilities                  │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────┴──────────┐   ┌────────┴──────────┐
│ CoreGraphics      │   │ Curses Backend    │
│ Backend           │   │                   │
│ - Full support    │   │ - Limited support │
└───────────────────┘   └───────────────────┘
```

### Design Principles

1. **Backend Abstraction**: Applications interact with a unified MouseEvent API regardless of backend
2. **Graceful Degradation**: System works seamlessly when mouse support is unavailable
3. **No Event Propagation**: Only the topmost UILayer receives mouse events (matches keyboard behavior)
4. **Future Extensibility**: Architecture supports adding drag-and-drop without major refactoring


## MouseEvent API Reference

### Core Data Structure

The `MouseEvent` class is defined in `ttk/ttk_mouse_event.py`:

```python
@dataclass
class MouseEvent:
    """
    Represents a mouse event with text grid coordinates.
    
    All coordinates are in text grid units (column, row) with sub-cell
    positioning expressed as fractional values from 0.0 to 1.0.
    """
    event_type: MouseEventType      # Type of mouse action
    column: int                     # Text grid column (0-based)
    row: int                        # Text grid row (0-based)
    sub_cell_x: float              # Horizontal position within cell [0.0, 1.0)
    sub_cell_y: float              # Vertical position within cell [0.0, 1.0)
    button: MouseButton            # Which button was involved
    scroll_delta_x: float = 0.0    # Horizontal scroll amount
    scroll_delta_y: float = 0.0    # Vertical scroll amount
    timestamp: float               # Unix timestamp for ordering
    shift: bool = False            # Modifier key states
    ctrl: bool = False
    alt: bool = False
    meta: bool = False
```

### Event Types

```python
class MouseEventType(Enum):
    BUTTON_DOWN = "button_down"    # Mouse button pressed
    BUTTON_UP = "button_up"        # Mouse button released
    DOUBLE_CLICK = "double_click"  # Rapid double press
    MOVE = "move"                  # Cursor movement
    WHEEL = "wheel"                # Scroll wheel
    DRAG = "drag"                  # Movement with button held (future)
```

### Mouse Buttons

```python
class MouseButton(Enum):
    LEFT = 1      # Primary button
    MIDDLE = 2    # Middle button/wheel click
    RIGHT = 3     # Secondary button
    NONE = 0      # For move events without button
```


## Coordinate System

### Text Grid Coordinates

The primary coordinate system uses character cell units:

- **Column**: Horizontal position, 0-based from left edge
- **Row**: Vertical position, 0-based from top edge

Example: `(column=5, row=10)` refers to the 6th column, 11th row.

### Sub-Cell Positioning

Sub-cell coordinates provide fractional positioning within a character cell:

- **sub_cell_x**: Horizontal position within cell, range [0.0, 1.0)
  - 0.0 = left edge of cell
  - 0.5 = center of cell
  - 0.99 = near right edge
  
- **sub_cell_y**: Vertical position within cell, range [0.0, 1.0)
  - 0.0 = top edge of cell
  - 0.5 = center of cell
  - 0.99 = near bottom edge

**Use Cases**:
- **Click detection**: Determine if click was on left/right half of cell
- **Drag operations**: Track precise cursor movement within cells
- **Visual feedback**: Show cursor position indicators

**Calculation Formula**:
```python
sub_cell_x = (screen_x % cell_width) / cell_width
sub_cell_y = (screen_y % cell_height) / cell_height
```

### Coordinate Transformation

Backends must transform native coordinates to text grid coordinates:

**CoreGraphics (window coordinates → text grid)**:
```python
def _transform_coordinates(self, window_x: float, window_y: float) -> tuple:
    """Transform window pixel coordinates to text grid coordinates."""
    column = int(window_x / self.cell_width)
    row = int(window_y / self.cell_height)
    sub_cell_x = (window_x % self.cell_width) / self.cell_width
    sub_cell_y = (window_y % self.cell_height) / self.cell_height
    return column, row, sub_cell_x, sub_cell_y
```

**Curses (already in text grid units)**:
```python
# Curses provides coordinates directly in text grid units
# Sub-cell positioning not available - use center (0.5, 0.5)
column = x  # From curses.getmouse()
row = y
sub_cell_x = 0.5
sub_cell_y = 0.5
```


## Backend Implementation

### Backend Interface

All backends must implement the mouse event interface defined in `ttk/ttk_backend.py`:

```python
class TtkBackend:
    """Base backend interface with mouse support."""
    
    def supports_mouse(self) -> bool:
        """Query whether this backend supports mouse events."""
        raise NotImplementedError
    
    def get_supported_mouse_events(self) -> set[MouseEventType]:
        """Query which mouse event types are supported."""
        raise NotImplementedError
    
    def enable_mouse_events(self) -> bool:
        """
        Enable mouse event capture.
        
        Mouse events are delivered via the event_callback.on_mouse_event() method,
        similar to how keyboard events use event_callback.on_key_event().
        
        Returns True if successful.
        """
        raise NotImplementedError
```

### CoreGraphics Backend Implementation

**File**: `ttk/backends/coregraphics_backend.py`

**Capabilities**: Full mouse support (all event types)

**Key Implementation Details**:

1. **Event Registration**: Registers for NSEvent mouse event types in C++ extension
2. **Event Delivery**: Delivers events via callback mechanism (no polling required)
3. **Coordinate Transformation**: Converts window coordinates to text grid
4. **Sub-Cell Calculation**: Provides precise fractional positioning
5. **Scroll Delta**: Calculates scroll wheel delta values

**Example Implementation**:
```python
def enable_mouse_events(self) -> bool:
    """Enable mouse event tracking in the native window."""
    if not self.window:
        return False
    
    # Register for mouse events via C++ extension
    # NSEventMask includes: mouseDown, mouseUp, mouseMoved, scrollWheel
    self.mouse_enabled = True
    return True

def _handle_mouse_event(self, native_event):
    """Handle a native mouse event and deliver via callback."""
    if not self.mouse_enabled:
        return
    
    # Transform coordinates
    col, row, sub_x, sub_y = self._transform_coordinates(
        native_event.x, native_event.y
    )
    
    # Create MouseEvent object
    mouse_event = MouseEvent(
        event_type=self._map_event_type(native_event.type),
        column=col,
        row=row,
        sub_cell_x=sub_x,
        sub_cell_y=sub_y,
        button=self._map_button(native_event.button),
        scroll_delta_x=native_event.scroll_x,
        scroll_delta_y=native_event.scroll_y,
        timestamp=time.time(),
        shift=native_event.shift,
        ctrl=native_event.ctrl,
        alt=native_event.alt,
        meta=native_event.meta
    )
    
    # Deliver event via callback
    try:
        self.event_callback.on_mouse_event(mouse_event)
    except Exception as e:
        self.logger.error(f"Error in mouse event callback: {e}")
```


### Curses Backend Implementation

**File**: `ttk/backends/curses_backend.py`

**Capabilities**: Limited mouse support (button clicks only)

**Key Implementation Details**:

1. **Capability Detection**: Checks terminal mouse support via `curses.has_key()`
2. **Graceful Degradation**: Returns False from `supports_mouse()` if unavailable
3. **Event Mapping**: Maps curses button states to MouseEventType
4. **No Sub-Cell**: Uses center position (0.5, 0.5) for all events

**Example Implementation**:
```python
def supports_mouse(self) -> bool:
    """Check if terminal supports mouse events."""
    try:
        import curses
        return curses.has_key(curses.KEY_MOUSE)
    except:
        return False

def enable_mouse_events(self) -> bool:
    """Enable mouse event capture in curses."""
    if not self.supports_mouse():
        return False
    
    try:
        import curses
        # Enable all mouse events
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        self.mouse_enabled = True
        return True
    except:
        return False

def poll_mouse_event(self) -> Optional[MouseEvent]:
    """Poll for mouse events from curses."""
    if not self.mouse_enabled:
        return None
    
    import curses
    
    # Check for KEY_MOUSE
    ch = self.stdscr.getch()
    if ch != curses.KEY_MOUSE:
        curses.ungetch(ch)  # Put it back
        return None
    
    try:
        _, x, y, _, bstate = curses.getmouse()
        
        return MouseEvent(
            event_type=self._map_curses_event(bstate),
            column=x,
            row=y,
            sub_cell_x=0.5,  # Center of cell
            sub_cell_y=0.5,
            button=self._map_curses_button(bstate),
            timestamp=time.time()
        )
    except:
        return None
```

**Terminal Compatibility**:
- **xterm**: Full support with `TERM=xterm-1003`
- **iTerm2**: Full support
- **Terminal.app**: Full support
- **tmux**: Requires `set -g mouse on`
- **screen**: Limited or no support


## Event Routing Architecture

### UI Layer Stack

Mouse events are routed through the UI layer stack via callback mechanism, similar to keyboard events:

```python
# In tfm_main.py
def on_mouse_event(self, event: MouseEvent):
    """
    Callback invoked by backend when mouse event occurs.
    
    Routes event to topmost UI layer only, matching keyboard event behavior.
    """
    if self.ui_layers:
        topmost_layer = self.ui_layers[-1]
        topmost_layer.handle_mouse_event(event)
```

**Key Principles**:
1. **Topmost Only**: Only the topmost UILayer receives events
2. **No Propagation**: Events do not propagate to lower layers
3. **Consistent Routing**: Same pattern as keyboard events
4. **Layer Responsibility**: Each layer decides how to handle events

### UILayer Mouse Event Handler

**File**: `src/tfm_ui_layer.py`

```python
class UILayer:
    """Base class for UI components in the layer stack."""
    
    def handle_mouse_event(self, event: MouseEvent) -> bool:
        """
        Handle a mouse event.
        
        Note: Only the topmost layer receives mouse events.
        No event propagation occurs.
        
        Args:
            event: The mouse event to handle
            
        Returns:
            True if handled, False otherwise (for future use)
        """
        return False  # Default: not handled
    
    def is_point_inside(self, column: int, row: int) -> bool:
        """
        Check if a point is inside this layer's bounds.
        
        Args:
            column: Text grid column
            row: Text grid row
            
        Returns:
            True if point is inside bounds
        """
        if not hasattr(self, 'x') or not hasattr(self, 'y'):
            return False
        if not hasattr(self, 'width') or not hasattr(self, 'height'):
            return False
        
        return (self.x <= column < self.x + self.width and
                self.y <= row < self.y + self.height)
```


## Application Integration

### Implementing Mouse Support in Components

To add mouse support to a TFM component:

1. **Inherit from UILayer**: Ensure component extends `UILayer`
2. **Implement handler**: Override `handle_mouse_event()`
3. **Bounds checking**: Use `is_point_inside()` for click detection
4. **Update state**: Modify component state based on event
5. **Request redraw**: Trigger UI update if needed

**Example: File Pane Focus Switching**

```python
class FilePane(UILayer):
    """File listing pane with mouse support."""
    
    def __init__(self, pane_manager, is_left_pane):
        super().__init__()
        self.pane_manager = pane_manager
        self.is_left_pane = is_left_pane
        self.logger = getLogger("FilePane")
    
    def handle_mouse_event(self, event: MouseEvent) -> bool:
        """Handle mouse events for pane focus switching."""
        # Only handle button down events
        if event.event_type != MouseEventType.BUTTON_DOWN:
            return False
        
        # Check if click is inside this pane
        if not self.is_point_inside(event.column, event.row):
            return False
        
        # Switch focus to this pane
        self.logger.info(f"Mouse click in {'left' if self.is_left_pane else 'right'} pane")
        self.pane_manager.set_active_pane(self.is_left_pane)
        
        return True
```

### Common Patterns

**Pattern 1: Click Detection**
```python
def handle_mouse_event(self, event: MouseEvent) -> bool:
    if event.event_type == MouseEventType.BUTTON_DOWN:
        if self.is_point_inside(event.column, event.row):
            # Handle click
            return True
    return False
```

**Pattern 2: Button-Specific Actions**
```python
def handle_mouse_event(self, event: MouseEvent) -> bool:
    if event.event_type == MouseEventType.BUTTON_DOWN:
        if event.button == MouseButton.LEFT:
            # Handle left click
            return True
        elif event.button == MouseButton.RIGHT:
            # Handle right click (context menu)
            return True
    return False
```

**Pattern 3: Scroll Wheel Handling**
```python
def handle_mouse_event(self, event: MouseEvent) -> bool:
    if event.event_type == MouseEventType.WHEEL:
        if event.scroll_delta_y > 0:
            self.scroll_up()
        elif event.scroll_delta_y < 0:
            self.scroll_down()
        return True
    return False
```


## Extending for Drag-and-Drop

The architecture is designed to support drag-and-drop operations in the future. Here's how to extend it:

### Drag Detection Pattern

```python
class DragAwareComponent(UILayer):
    """Component with drag-and-drop support."""
    
    def __init__(self):
        super().__init__()
        self.drag_state = None  # Tracks active drag operation
    
    def handle_mouse_event(self, event: MouseEvent) -> bool:
        """Handle mouse events including drag operations."""
        
        # Start drag on button down
        if event.event_type == MouseEventType.BUTTON_DOWN:
            if self.is_point_inside(event.column, event.row):
                self.drag_state = {
                    'start_col': event.column,
                    'start_row': event.row,
                    'button': event.button,
                    'item': self.get_item_at(event.column, event.row)
                }
                return True
        
        # Track drag movement
        elif event.event_type == MouseEventType.DRAG:
            if self.drag_state:
                self.update_drag_preview(event.column, event.row)
                return True
        
        # Complete drag on button up
        elif event.event_type == MouseEventType.BUTTON_UP:
            if self.drag_state:
                self.complete_drag(event.column, event.row)
                self.drag_state = None
                return True
        
        return False
    
    def update_drag_preview(self, column: int, row: int):
        """Update visual feedback during drag."""
        # Show drag cursor, highlight drop target, etc.
        pass
    
    def complete_drag(self, column: int, row: int):
        """Complete drag operation at drop location."""
        # Perform the actual drag-and-drop operation
        pass
```

### Gesture Recognition

For more complex gestures, implement a gesture recognizer:

```python
class GestureRecognizer:
    """Recognizes mouse gestures from event sequences."""
    
    def __init__(self):
        self.event_history = []
        self.max_history = 10
    
    def add_event(self, event: MouseEvent):
        """Add event to history for gesture detection."""
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
    
    def detect_drag(self) -> Optional[dict]:
        """Detect drag gesture from event history."""
        if len(self.event_history) < 2:
            return None
        
        # Check for button down followed by movement
        first = self.event_history[0]
        if first.event_type != MouseEventType.BUTTON_DOWN:
            return None
        
        # Check for movement while button held
        for event in self.event_history[1:]:
            if event.event_type == MouseEventType.MOVE:
                # Calculate drag distance
                dx = event.column - first.column
                dy = event.row - first.row
                distance = (dx**2 + dy**2) ** 0.5
                
                if distance > 1.0:  # Threshold for drag
                    return {
                        'start': (first.column, first.row),
                        'current': (event.column, event.row),
                        'distance': distance,
                        'button': first.button
                    }
        
        return None
```


### Future Drag-and-Drop Architecture

**Recommended approach for implementing drag-and-drop**:

1. **Add DRAG event type support**: Backends emit DRAG events for movement with button held
2. **Implement DragManager**: Central component to track drag state across layers
3. **Add drop target detection**: Components register as drop targets
4. **Visual feedback**: Show drag preview and highlight valid drop targets
5. **Validation**: Check if drop is valid before completing operation

**Example DragManager**:

```python
class DragManager:
    """Manages drag-and-drop operations across UI layers."""
    
    def __init__(self):
        self.active_drag = None
        self.drop_targets = []
    
    def start_drag(self, source_layer, item, start_col, start_row):
        """Start a drag operation."""
        self.active_drag = {
            'source': source_layer,
            'item': item,
            'start': (start_col, start_row),
            'current': (start_col, start_row)
        }
    
    def update_drag(self, column: int, row: int):
        """Update drag position and check drop targets."""
        if not self.active_drag:
            return
        
        self.active_drag['current'] = (column, row)
        
        # Check which drop target is under cursor
        for target in self.drop_targets:
            if target.is_point_inside(column, row):
                if target.can_accept_drop(self.active_drag['item']):
                    target.highlight_as_drop_target()
                else:
                    target.unhighlight()
    
    def complete_drag(self, column: int, row: int):
        """Complete drag operation at drop location."""
        if not self.active_drag:
            return
        
        # Find drop target
        for target in self.drop_targets:
            if target.is_point_inside(column, row):
                if target.can_accept_drop(self.active_drag['item']):
                    target.handle_drop(self.active_drag['item'])
                    break
        
        self.active_drag = None
    
    def register_drop_target(self, target):
        """Register a component as a drop target."""
        self.drop_targets.append(target)
```


## Testing Guidelines

### Unit Testing

**Test coordinate transformation**:
```python
def test_coordinate_transformation():
    """Test window to text grid coordinate transformation."""
    backend = CoreGraphicsBackend()
    backend.cell_width = 10.0
    backend.cell_height = 20.0
    
    # Test basic transformation
    col, row, sub_x, sub_y = backend._transform_coordinates(25.0, 45.0)
    assert col == 2  # 25 / 10 = 2
    assert row == 2  # 45 / 20 = 2
    assert sub_x == 0.5  # (25 % 10) / 10 = 0.5
    assert sub_y == 0.25  # (45 % 20) / 20 = 0.25
```

**Test event routing**:
```python
def test_event_routing_to_topmost_layer():
    """Test that only topmost layer receives events."""
    layer1 = MockUILayer()
    layer2 = MockUILayer()
    
    ui_layers = [layer1, layer2]
    event = MouseEvent(
        event_type=MouseEventType.BUTTON_DOWN,
        column=5, row=10,
        sub_cell_x=0.5, sub_cell_y=0.5,
        button=MouseButton.LEFT,
        timestamp=time.time()
    )
    
    # Route to topmost
    ui_layers[-1].handle_mouse_event(event)
    
    assert layer2.received_event == event
    assert layer1.received_event is None
```

### Property-Based Testing

**Test sub-cell bounds**:
```python
from hypothesis import given, strategies as st

@given(
    x=st.floats(min_value=0, max_value=10000),
    y=st.floats(min_value=0, max_value=10000),
    cell_width=st.floats(min_value=1, max_value=100),
    cell_height=st.floats(min_value=1, max_value=100)
)
def test_sub_cell_position_bounds(x, y, cell_width, cell_height):
    """Sub-cell positions must be in range [0.0, 1.0)."""
    backend = CoreGraphicsBackend()
    backend.cell_width = cell_width
    backend.cell_height = cell_height
    
    col, row, sub_x, sub_y = backend._transform_coordinates(x, y)
    
    assert 0.0 <= sub_x < 1.0
    assert 0.0 <= sub_y < 1.0
```

### Integration Testing

**Test pane focus switching**:
```python
def test_pane_focus_switching_integration():
    """Test complete flow from mouse event to focus change."""
    # Setup file manager with two panes
    fm = FileManager()
    
    # Create mouse event in left pane
    event = MouseEvent(
        event_type=MouseEventType.BUTTON_DOWN,
        column=5,  # Inside left pane
        row=10,
        sub_cell_x=0.5,
        sub_cell_y=0.5,
        button=MouseButton.LEFT,
        timestamp=time.time()
    )
    
    # Route event
    fm.handle_mouse_event(event)
    
    # Verify focus switched to left pane
    assert fm.active_pane == fm.left_pane
```


## Debugging and Troubleshooting

### Common Issues

**Issue: Mouse events not being received**

Diagnosis:
```python
# Check backend support
if not backend.supports_mouse():
    print("Backend does not support mouse events")

# Check if mouse events are enabled
if not backend.enable_mouse_events():
    print("Failed to enable mouse events")

# Check if callback is registered
if not hasattr(backend, 'event_callback'):
    print("Event callback not registered with backend")

# Add logging to on_mouse_event callback
def on_mouse_event(self, event: MouseEvent):
    self.logger.info(f"Received mouse event: {event.event_type.value}")
    # ... route to layers
```

**Issue: Incorrect coordinate transformation**

Diagnosis:
```python
# Log cell dimensions
print(f"Cell dimensions: {backend.cell_width}x{backend.cell_height}")

# Log transformation results
col, row, sub_x, sub_y = backend._transform_coordinates(x, y)
print(f"Screen ({x}, {y}) -> Grid ({col}, {row}) + ({sub_x:.2f}, {sub_y:.2f})")

# Verify sub-cell bounds
assert 0.0 <= sub_x < 1.0, f"Invalid sub_cell_x: {sub_x}"
assert 0.0 <= sub_y < 1.0, f"Invalid sub_cell_y: {sub_y}"
```

**Issue: Events not reaching component**

Diagnosis:
```python
# Check layer stack
print(f"UI layers: {len(ui_layers)}")
print(f"Topmost layer: {ui_layers[-1].__class__.__name__}")

# Check bounds
if not component.is_point_inside(event.column, event.row):
    print(f"Event ({event.column}, {event.row}) outside component bounds")
    print(f"Component bounds: ({component.x}, {component.y}) to "
          f"({component.x + component.width}, {component.y + component.height})")
```

### Logging

Enable mouse event logging for debugging:

```python
from tfm_log_manager import getLogger

logger = getLogger("Mouse")

def handle_mouse_event(self, event: MouseEvent) -> bool:
    logger.info(f"Mouse event: {event.event_type.value} at ({event.column}, {event.row})")
    logger.info(f"Sub-cell: ({event.sub_cell_x:.2f}, {event.sub_cell_y:.2f})")
    logger.info(f"Button: {event.button.name}, Timestamp: {event.timestamp}")
    
    # ... handle event
```

### Performance Monitoring

Monitor mouse event processing performance:

```python
import time

def poll_mouse_event(self) -> Optional[MouseEvent]:
    start = time.time()
    event = self._poll_native_event()
    elapsed = time.time() - start
    
    if elapsed > 0.016:  # 16ms = 60 FPS threshold
        logger.warning(f"Slow mouse event polling: {elapsed*1000:.1f}ms")
    
    return event
```


## Backend Capability Matrix

| Feature | CoreGraphics | Curses | Notes |
|---------|--------------|--------|-------|
| Button Down | ✓ | ✓ | All backends |
| Button Up | ✓ | ✓ | All backends |
| Double Click | ✓ | ✗ | Desktop only |
| Mouse Move | ✓ | ✗ | Desktop only |
| Scroll Wheel | ✓ | ✗ | Desktop only |
| Drag Events | ✓ | ✗ | Desktop only (future) |
| Sub-Cell Position | ✓ | ✗ | Desktop only |
| Modifier Keys | ✓ | Partial | Limited in terminals |
| Scroll Delta | ✓ | ✗ | Desktop only |

## File Reference

### Core Implementation Files

- `ttk/ttk_mouse_event.py` - MouseEvent data structures and enums
- `ttk/ttk_backend.py` - Backend interface with mouse methods
- `ttk/backends/coregraphics_backend.py` - CoreGraphics mouse implementation
- `ttk/backends/curses_backend.py` - Curses mouse implementation
- `src/tfm_ui_layer.py` - UILayer base class with mouse support
- `src/tfm_main.py` - Event routing and main loop integration

### Test Files

- `test/test_mouse_event_structure.py` - MouseEvent structure tests
- `test/test_mouse_coordinate_transform.py` - Coordinate transformation tests
- `test/test_mouse_event_routing.py` - Event routing tests
- `test/test_mouse_pane_focus_switching.py` - Pane focus switching tests
- `test/test_mouse_event_timestamp_ordering.py` - Event ordering tests
- `temp/test_mouse_backend_checkpoint.py` - Backend integration tests
- `temp/test_mouse_routing_integration.py` - Full routing integration tests

### Documentation Files

- `doc/MOUSE_EVENT_SUPPORT_FEATURE.md` - End-user documentation
- `doc/dev/MOUSE_EVENT_SUPPORT_IMPLEMENTATION.md` - This document
- `.kiro/specs/mouse-event-support/design.md` - Design specification
- `.kiro/specs/mouse-event-support/requirements.md` - Requirements specification

### Demo Files

- `demo/demo_mouse_events.py` - Interactive demonstration of mouse support


## Best Practices

### Do's

✓ **Check backend capabilities before using features**
```python
if backend.supports_mouse():
    backend.enable_mouse_events()
```

✓ **Use is_point_inside() for bounds checking**
```python
if self.is_point_inside(event.column, event.row):
    # Handle event
```

✓ **Handle events gracefully when mouse unavailable**
```python
def handle_mouse_event(self, event: MouseEvent) -> bool:
    # Provide keyboard alternative
    return False  # Let keyboard handling work
```

✓ **Use sub-cell positioning for precise interactions**
```python
if event.sub_cell_x < 0.5:
    # Click on left half of cell
else:
    # Click on right half of cell
```

✓ **Log mouse events for debugging**
```python
self.logger.info(f"Mouse {event.event_type.value} at ({event.column}, {event.row})")
```

### Don'ts

✗ **Don't assume mouse support is available**
```python
# BAD: Assumes mouse works
backend.enable_mouse_events()
event = backend.poll_mouse_event()

# GOOD: Check first
if backend.supports_mouse():
    backend.enable_mouse_events()
```

✗ **Don't propagate events to lower layers**
```python
# BAD: Manual propagation
for layer in reversed(ui_layers):
    if layer.handle_mouse_event(event):
        break

# GOOD: Only topmost layer
ui_layers[-1].handle_mouse_event(event)
```

✗ **Don't ignore event timestamps**
```python
# BAD: Process events out of order
events.sort(key=lambda e: e.column)

# GOOD: Maintain temporal order
events.sort(key=lambda e: e.timestamp)
```

✗ **Don't block in event handlers**
```python
# BAD: Blocking operation
def handle_mouse_event(self, event):
    time.sleep(1)  # Blocks event loop!
    return True

# GOOD: Non-blocking
def handle_mouse_event(self, event):
    self.schedule_async_operation()
    return True
```


## Future Enhancements

### Planned Features

1. **Drag-and-Drop Support**
   - Add DRAG event type to backends
   - Implement DragManager for cross-layer drag operations
   - Add visual feedback for drag preview
   - Support file/directory dragging between panes

2. **Context Menus**
   - Right-click to show context menu
   - Position menu at mouse location
   - Support keyboard navigation in menus

3. **Hover Effects**
   - Track mouse movement over UI elements
   - Show tooltips on hover
   - Highlight interactive elements

4. **Selection with Mouse**
   - Click to select items
   - Shift-click for range selection
   - Ctrl-click for multi-selection

5. **Scroll Wheel Support**
   - Scroll file lists with wheel
   - Horizontal scrolling with shift-wheel
   - Smooth scrolling animation

### Extension Points

The architecture provides these extension points:

1. **Custom Event Types**: Add new MouseEventType values for specialized interactions
2. **Gesture Recognition**: Implement gesture recognizers for complex patterns
3. **Multi-Touch**: Extend MouseEvent for touch events (pinch, rotate, etc.)
4. **Accessibility**: Add keyboard equivalents for all mouse operations

## Conclusion

The mouse event support system provides a solid foundation for mouse interaction in TFM. The architecture is designed for extensibility, allowing future features like drag-and-drop to be added without major refactoring. By following the patterns and best practices in this document, developers can effectively implement mouse support in new components and extend the system with additional capabilities.

For questions or issues, refer to:
- Design document: `.kiro/specs/mouse-event-support/design.md`
- End-user guide: `doc/MOUSE_EVENT_SUPPORT_FEATURE.md`
- Demo script: `demo/demo_mouse_events.py`

