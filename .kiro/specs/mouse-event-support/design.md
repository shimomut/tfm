# Design Document: Mouse Event Support

## Overview

This design implements comprehensive mouse event support for TFM across both terminal (curses) and desktop (CoreGraphics) modes. The architecture introduces a unified mouse event abstraction in TTK, backend-specific event capture implementations, and integration with the existing UI layer stack for event routing. The initial implementation focuses on pane focus switching via mouse clicks, with the architecture designed to support future drag-and-drop operations.

The design follows a layered approach:
1. **Backend Layer**: Captures native mouse events and transforms coordinates
2. **TTK API Layer**: Provides unified mouse event abstraction
3. **Application Layer**: Handles mouse events in TFM components

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    TFM Application                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │           UI Layer Stack Manager                 │  │
│  │  (Routes events to topmost layer only)           │  │
│  └──────────────────────┬───────────────────────────┘  │
│                         │                               │
│  ┌──────────────┐  ┌───┴──────────┐  ┌──────────────┐ │
│  │  File Pane   │  │  File Pane   │  │ Other UI     │ │
│  │   (Left)     │  │   (Right)    │  │ Components   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────┐
│                       TTK Library                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Mouse Event Abstraction                  │  │
│  │  - MouseEvent class                              │  │
│  │  - Event type enumeration                        │  │
│  │  - Coordinate transformation utilities           │  │
│  └──────────────────────┬───────────────────────────┘  │
│                         │                               │
│         ┌───────────────┴───────────────┐              │
│         │                                │              │
│  ┌──────┴──────────┐          ┌─────────┴──────────┐  │
│  │ CoreGraphics    │          │ Curses Backend     │  │
│  │ Backend         │          │                    │  │
│  │ - Full mouse    │          │ - Limited mouse    │  │
│  │   support       │          │   support          │  │
│  └─────────────────┘          └────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Event Flow

1. **Native Event Capture**: Backend receives OS/terminal mouse event
2. **Coordinate Transformation**: Backend converts to text grid coordinates with sub-cell positioning
3. **Event Object Creation**: Backend creates MouseEvent object with all relevant data
4. **Event Delivery**: TTK provides event to application via polling or callback
5. **Event Routing**: TFM's UI Layer Stack Manager delivers event to topmost UILayer only
6. **Event Handling**: UILayer processes event (no propagation to lower layers)

## Components and Interfaces

### MouseEvent Class

The core data structure representing a mouse event:

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class MouseEventType(Enum):
    """Types of mouse events supported by TTK."""
    BUTTON_DOWN = "button_down"
    BUTTON_UP = "button_up"
    DOUBLE_CLICK = "double_click"
    MOVE = "move"
    WHEEL = "wheel"
    DRAG = "drag"  # For future use

class MouseButton(Enum):
    """Mouse button identifiers."""
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3
    NONE = 0  # For move events without button

@dataclass
class MouseEvent:
    """
    Represents a mouse event with text grid coordinates.
    
    Coordinates are in text grid units (column, row) with sub-cell
    positioning expressed as fractional values from 0.0 to 1.0.
    """
    event_type: MouseEventType
    column: int  # Text grid column (0-based)
    row: int  # Text grid row (0-based)
    sub_cell_x: float  # Horizontal position within cell (0.0 = left, 1.0 = right)
    sub_cell_y: float  # Vertical position within cell (0.0 = top, 1.0 = bottom)
    button: MouseButton
    scroll_delta_x: float = 0.0  # Horizontal scroll amount (for wheel events)
    scroll_delta_y: float = 0.0  # Vertical scroll amount (for wheel events)
    timestamp: float  # Unix timestamp for event ordering
    shift: bool = False  # Modifier keys for future gesture support
    ctrl: bool = False
    alt: bool = False
    meta: bool = False
```

### Backend Interface Extensions

Each backend must implement mouse event capture:

```python
class TtkBackend:
    """Base backend interface with mouse support."""
    
    def supports_mouse(self) -> bool:
        """
        Query whether this backend supports mouse events.
        
        Returns:
            True if mouse events are available, False otherwise.
        """
        raise NotImplementedError
    
    def get_supported_mouse_events(self) -> set[MouseEventType]:
        """
        Query which mouse event types are supported.
        
        Returns:
            Set of MouseEventType values supported by this backend.
        """
        raise NotImplementedError
    
    def enable_mouse_events(self) -> bool:
        """
        Enable mouse event capture.
        
        Returns:
            True if mouse events were successfully enabled, False otherwise.
        """
        raise NotImplementedError
    
    def poll_mouse_event(self) -> Optional[MouseEvent]:
        """
        Poll for pending mouse events.
        
        Returns:
            MouseEvent if one is available, None otherwise.
        """
        raise NotImplementedError
```

### CoreGraphics Backend Implementation

The CoreGraphics backend provides full mouse support:

```python
class CoreGraphicsBackend(TtkBackend):
    """macOS CoreGraphics backend with full mouse support."""
    
    def __init__(self):
        self.mouse_enabled = False
        self.cell_width = 0  # Set during initialization
        self.cell_height = 0
        self.pending_mouse_events = []
    
    def supports_mouse(self) -> bool:
        return True
    
    def get_supported_mouse_events(self) -> set[MouseEventType]:
        return {
            MouseEventType.BUTTON_DOWN,
            MouseEventType.BUTTON_UP,
            MouseEventType.DOUBLE_CLICK,
            MouseEventType.MOVE,
            MouseEventType.WHEEL,
            MouseEventType.DRAG
        }
    
    def enable_mouse_events(self) -> bool:
        """Enable mouse event tracking in the native window."""
        # Register for NSEvent mouse event types
        # Implementation in C++ extension
        self.mouse_enabled = True
        return True
    
    def _transform_coordinates(self, window_x: float, window_y: float) -> tuple:
        """
        Transform window coordinates to text grid coordinates.
        
        Args:
            window_x: X coordinate in window space
            window_y: Y coordinate in window space
            
        Returns:
            Tuple of (column, row, sub_cell_x, sub_cell_y)
        """
        column = int(window_x / self.cell_width)
        row = int(window_y / self.cell_height)
        
        # Calculate sub-cell position as fraction
        sub_cell_x = (window_x % self.cell_width) / self.cell_width
        sub_cell_y = (window_y % self.cell_height) / self.cell_height
        
        return column, row, sub_cell_x, sub_cell_y
```

### Curses Backend Implementation

The curses backend provides limited mouse support:

```python
class CursesBackend(TtkBackend):
    """Terminal curses backend with limited mouse support."""
    
    def __init__(self):
        self.mouse_enabled = False
        self.mouse_available = False
    
    def supports_mouse(self) -> bool:
        """Check if terminal supports mouse events."""
        try:
            import curses
            # Check if terminal has mouse capability
            self.mouse_available = curses.has_key(curses.KEY_MOUSE)
            return self.mouse_available
        except:
            return False
    
    def get_supported_mouse_events(self) -> set[MouseEventType]:
        """Curses typically only supports button clicks."""
        if self.mouse_available:
            return {
                MouseEventType.BUTTON_DOWN,
                MouseEventType.BUTTON_UP
            }
        return set()
    
    def enable_mouse_events(self) -> bool:
        """Enable mouse event capture in curses."""
        if not self.mouse_available:
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
        import time
        
        # Check if KEY_MOUSE is available
        ch = self.stdscr.getch()
        if ch != curses.KEY_MOUSE:
            # Put it back for other handlers
            curses.ungetch(ch)
            return None
        
        try:
            _, x, y, _, bstate = curses.getmouse()
            
            # Map curses button state to our event type
            event_type = self._map_curses_event(bstate)
            button = self._map_curses_button(bstate)
            
            # Curses coordinates are already in text grid units
            # Sub-cell positioning not available in curses
            return MouseEvent(
                event_type=event_type,
                column=x,
                row=y,
                sub_cell_x=0.5,  # Center of cell
                sub_cell_y=0.5,
                button=button,
                timestamp=time.time()
            )
        except:
            return None
```

### UILayer Mouse Event Handling

Extend the UILayer base class to support mouse events:

```python
class UILayer:
    """Base class for UI components in the layer stack."""
    
    def handle_mouse_event(self, event: MouseEvent) -> bool:
        """
        Handle a mouse event.
        
        Note: Only the topmost layer in the stack receives mouse events.
        There is no event propagation to lower layers.
        
        Args:
            event: The mouse event to handle
            
        Returns:
            True if the event was handled, False otherwise.
            (Return value is for future use; currently no propagation occurs)
        """
        # Default implementation: not handled
        return False
    
    def is_point_inside(self, column: int, row: int) -> bool:
        """
        Check if a point is inside this layer's bounds.
        
        Args:
            column: Text grid column
            row: Text grid row
            
        Returns:
            True if the point is inside this layer's bounds.
        """
        # Default implementation: check against layer bounds
        if not hasattr(self, 'x') or not hasattr(self, 'y'):
            return False
        if not hasattr(self, 'width') or not hasattr(self, 'height'):
            return False
        
        return (self.x <= column < self.x + self.width and
                self.y <= row < self.y + self.height)
```

### TFM File Pane Mouse Handling

Implement mouse handling in TFM file panes:

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
        # Only handle button down events for focus switching
        if event.event_type != MouseEventType.BUTTON_DOWN:
            return False
        
        # Check if click is inside this pane
        if not self.is_point_inside(event.column, event.row):
            return False
        
        # Switch focus to this pane
        self.logger.info(f"Mouse click in {'left' if self.is_left_pane else 'right'} pane")
        self.pane_manager.set_active_pane(self.is_left_pane)
        
        # Event handled
        return True
```

## Data Models

### Coordinate System

The mouse event system uses a dual coordinate representation:

1. **Text Grid Coordinates**: Integer column and row values representing character cells
   - Column: 0-based horizontal position (0 = leftmost column)
   - Row: 0-based vertical position (0 = topmost row)

2. **Sub-Cell Positioning**: Fractional coordinates within a cell
   - sub_cell_x: 0.0 (left edge) to 1.0 (right edge)
   - sub_cell_y: 0.0 (top edge) to 1.0 (bottom edge)
   - Example: (0.4, 0.8) means 40% from left, 80% from top

### Event Type Hierarchy

```
MouseEvent
├── BUTTON_DOWN (button pressed)
├── BUTTON_UP (button released)
├── DOUBLE_CLICK (rapid double press)
├── MOVE (cursor movement)
├── WHEEL (scroll wheel)
└── DRAG (movement with button held) [future]
```

### Backend Capability Matrix

| Event Type    | CoreGraphics | Curses |
|---------------|--------------|--------|
| BUTTON_DOWN   | ✓            | ✓      |
| BUTTON_UP     | ✓            | ✓      |
| DOUBLE_CLICK  | ✓            | ✗      |
| MOVE          | ✓            | ✗      |
| WHEEL         | ✓            | ✗      |
| DRAG          | ✓            | ✗      |


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, several redundancies were identified:
- Requirements 6.1-6.6 duplicate requirement 1.1 (MouseEvent structure)
- Requirements 2.4-2.5 duplicate requirements 1.2-1.3 (coordinate transformation)
- Requirements 4.2 and 4.3 about event propagation are no longer applicable since events only go to the topmost layer

The following properties eliminate these redundancies while ensuring comprehensive coverage.

### Core Properties

**Property 1: MouseEvent structure completeness**
*For any* MouseEvent instance, it must contain all required fields: event_type, column, row, sub_cell_x, sub_cell_y, button, scroll_delta_x, scroll_delta_y, timestamp, and modifier keys (shift, ctrl, alt, meta).
**Validates: Requirements 1.1, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 8.4**

**Property 2: Coordinate transformation correctness**
*For any* screen coordinates (x, y) and cell dimensions (width, height), transforming to grid coordinates must produce column = floor(x / width) and row = floor(y / height).
**Validates: Requirements 1.2, 2.4**

**Property 3: Sub-cell position bounds**
*For any* screen coordinates and cell dimensions, the calculated sub_cell_x and sub_cell_y values must be in the range [0.0, 1.0).
**Validates: Requirements 1.3, 2.5**

**Property 4: Sub-cell position accuracy**
*For any* screen coordinates (x, y) and cell dimensions (width, height), sub_cell_x must equal (x % width) / width and sub_cell_y must equal (y % height) / height.
**Validates: Requirements 1.3, 2.5**

**Property 5: Event handler registration and invocation**
*For any* registered mouse event handler, when a mouse event occurs, the handler must be invoked with the event object.
**Validates: Requirements 1.5**

**Property 6: Event stack routing to topmost layer only**
*For any* non-empty UI layer stack and mouse event, only the topmost layer must receive the event, and no lower layers should receive it.
**Validates: Requirements 4.1, 4.2**

**Property 7: Consistent routing for mouse and keyboard events**
*For any* UI layer stack, the event routing pattern (delivery to topmost layer only) must be identical for both mouse events and keyboard events.
**Validates: Requirements 4.3**

**Property 8: Pane focus follows click location**
*For any* click event with coordinates inside the left pane bounds, focus must be set to the left pane; for coordinates inside the right pane bounds, focus must be set to the right pane.
**Validates: Requirements 5.1, 5.2**

**Property 9: Focus state reflects active pane**
*For any* focus change operation, the active pane indicator must be updated to reflect which pane currently has focus.
**Validates: Requirements 5.3**

**Property 10: Focus preservation outside pane bounds**
*For any* click event with coordinates outside both pane bounds, the current focus state must remain unchanged.
**Validates: Requirements 5.4**

**Property 11: Curses backend graceful degradation**
*For any* terminal environment where mouse support is unavailable, calling mouse-related methods on the Curses backend must not raise exceptions.
**Validates: Requirements 3.4**

**Property 12: Curses backend coordinate validity**
*For any* mouse event generated by the Curses backend, the column and row values must be non-negative integers within the terminal dimensions.
**Validates: Requirements 3.3**

**Property 13: Event timestamp ordering**
*For any* sequence of mouse events, the timestamps must be monotonically non-decreasing (later events have timestamps >= earlier events).
**Validates: Requirements 8.2**

## Error Handling

### Backend Initialization Errors

**Scenario**: Mouse event support unavailable in terminal
- **Detection**: `supports_mouse()` returns False
- **Response**: Gracefully disable mouse features, continue with keyboard-only operation
- **User Impact**: No error messages, seamless fallback to keyboard navigation

**Scenario**: CoreGraphics backend fails to register mouse events
- **Detection**: `enable_mouse_events()` returns False
- **Response**: Log warning, continue with keyboard-only operation
- **User Impact**: Application remains functional without mouse support

### Event Processing Errors

**Scenario**: Invalid coordinates in mouse event (negative or out of bounds)
- **Detection**: Coordinate validation in event handler
- **Response**: Clamp coordinates to valid range, log warning
- **User Impact**: Event processed at nearest valid location

**Scenario**: Exception in UILayer mouse event handler
- **Detection**: Try-catch in event routing code
- **Response**: Log error, mark event as handled to prevent propagation
- **User Impact**: Single layer fails gracefully, other layers unaffected

**Scenario**: Curses backend receives KEY_MOUSE but getmouse() fails
- **Detection**: Exception from curses.getmouse()
- **Response**: Return None from poll_mouse_event, continue processing
- **User Impact**: Single event lost, subsequent events processed normally

### Coordinate Transformation Errors

**Scenario**: Cell dimensions are zero or negative
- **Detection**: Validation during backend initialization
- **Response**: Use default cell dimensions (8x16 pixels), log error
- **User Impact**: Mouse events may be slightly inaccurate but functional

**Scenario**: Window coordinates outside window bounds
- **Detection**: Coordinate validation in transformation
- **Response**: Clamp to window bounds before transformation
- **User Impact**: Events at window edges processed correctly

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of coordinate transformations with known inputs/outputs
- Backend capability detection for CoreGraphics and Curses
- Event routing through a simple 2-layer stack
- Pane focus switching with specific click coordinates
- Error conditions (invalid coordinates, unsupported terminals)

**Property-Based Tests** focus on:
- Universal properties across all possible inputs
- Coordinate transformation correctness for arbitrary screen positions
- Sub-cell position bounds and accuracy for any coordinates
- Event routing behavior for arbitrary layer stack configurations
- Focus switching for any click coordinates relative to pane bounds

### Property-Based Testing Configuration

- **Library**: Use `hypothesis` for Python property-based testing
- **Iterations**: Minimum 100 iterations per property test
- **Tagging**: Each test must reference its design property with format:
  ```python
  # Feature: mouse-event-support, Property 2: Coordinate transformation correctness
  ```

### Test Organization

```
test/
├── test_mouse_event_structure.py          # Property 1 (PBT)
├── test_mouse_coordinate_transform.py     # Properties 2, 3, 4 (PBT)
├── test_mouse_event_handlers.py           # Property 5 (PBT)
├── test_mouse_event_routing.py            # Properties 6, 7 (PBT)
├── test_mouse_pane_focus.py               # Properties 8, 9, 10 (PBT)
├── test_mouse_curses_backend.py           # Properties 11, 12 (PBT + unit)
├── test_mouse_coregraphics_backend.py     # Unit tests for CoreGraphics
├── test_mouse_event_ordering.py           # Property 13 (PBT)
└── test_mouse_integration.py              # End-to-end integration tests
```

### Example Property Test

```python
from hypothesis import given, strategies as st
import time

# Feature: mouse-event-support, Property 3: Sub-cell position bounds
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
    
    assert 0.0 <= sub_x < 1.0, f"sub_cell_x {sub_x} out of bounds"
    assert 0.0 <= sub_y < 1.0, f"sub_cell_y {sub_y} out of bounds"
```

### Integration Testing

Integration tests verify the complete flow from backend event capture through to TFM pane focus switching:

1. **Mock Backend Test**: Create mock backend that generates test events
2. **Event Routing Test**: Verify events flow through layer stack correctly
3. **Pane Focus Test**: Verify clicking panes switches focus in TFM
4. **Cross-Backend Test**: Verify behavior consistent across CoreGraphics and Curses

### Manual Testing

Manual testing required for:
- Visual verification of pane focus indicators
- Real mouse interaction feel and responsiveness
- Terminal compatibility testing across different terminal emulators
- Edge cases like rapid clicking, dragging across panes
