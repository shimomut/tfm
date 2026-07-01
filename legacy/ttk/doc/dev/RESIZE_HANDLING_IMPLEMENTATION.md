# Window Resize Handling Implementation

## Overview

This document describes the implementation of window resize handling in the TTK demo application. The resize handling ensures that the test interface properly responds to window resize events and updates the UI layout accordingly.

## Implementation Details

### Resize Event Detection

The resize handling is implemented in the `TestInterface` class in `ttk/demo/test_interface.py`. The implementation detects resize events using the `KeyCode.RESIZE` event type that is already defined in the TTK input event system.

### Key Components

#### 1. Event Handling in Main Loop

The main event loop in `TestInterface.run()` checks for resize events before processing other input:

```python
# Check for resize event first
if event.key_code == KeyCode.RESIZE:
    # Window was resized - redraw interface with new dimensions
    self.draw_interface()
    continue
```

This ensures that resize events trigger an immediate redraw of the interface without being stored in the input history.

#### 2. Input Handler Updates

The `handle_input()` method was updated to properly handle resize events:

```python
def handle_input(self, event: KeyEvent) -> bool:
    # Handle resize events
    if event.key_code == KeyCode.RESIZE:
        # Window was resized - redraw interface with new dimensions
        # Don't store resize events in history
        return True
    
    # ... rest of input handling
```

Resize events:
- Return `True` to continue running
- Are not stored in the input history
- Do not update the `last_input` field

#### 3. Dynamic Layout Adaptation

The `draw_interface()` method already queries window dimensions dynamically using `self.renderer.get_dimensions()` at multiple points during rendering. This means that when a resize event triggers a redraw, all UI elements automatically adapt to the new dimensions:

- **Header**: Centered based on current width
- **Color and attribute tests**: Drawn if space available
- **Shape tests**: Drawn if space available
- **Coordinate information**: Shows updated dimensions
- **Corner markers**: Positioned at new corners
- **Performance metrics**: Displayed if space available
- **Input echo**: Displayed if space available

### Behavior

#### Resize Event Flow

1. User resizes the window
2. Backend detects resize and generates `KeyEvent` with `key_code=KeyCode.RESIZE`
3. Main loop receives the resize event
4. Interface is redrawn with `draw_interface()`
5. All sections query current dimensions and adapt layout
6. Display is refreshed to show updated interface

#### Layout Adaptation

The interface adapts to window size changes by:

- **Smaller windows**: Sections that don't fit are skipped
- **Larger windows**: More sections become visible
- **Corner markers**: Always positioned at actual window corners
- **Dimension display**: Shows current window size
- **Content centering**: Header and other elements re-center

### Testing

Comprehensive tests were added in `ttk/test/test_resize_handling.py`:

#### Unit Tests

1. **test_resize_event_detection**: Verifies resize events are detected and don't affect input history
2. **test_resize_triggers_redraw**: Confirms resize events trigger interface redraw
3. **test_dimensions_update_after_resize**: Validates dimension queries after resize
4. **test_layout_adapts_to_smaller_window**: Tests layout adaptation when window shrinks
5. **test_layout_adapts_to_larger_window**: Tests layout adaptation when window grows
6. **test_corner_markers_update_after_resize**: Verifies corner markers move to new positions
7. **test_resize_does_not_affect_quit_functionality**: Ensures resize doesn't interfere with quit
8. **test_multiple_resize_events**: Tests handling of consecutive resize events

#### Integration Tests

1. **test_resize_between_normal_inputs**: Verifies resize events work correctly when interspersed with normal input

### Requirements Validation

This implementation satisfies **Requirement 6.4**:

> WHEN the demo application runs THEN the system SHALL demonstrate window resizing and coordinate handling

The implementation:
- ✅ Handles resize events in the demo application
- ✅ Updates UI layout on resize
- ✅ Displays updated dimensions
- ✅ Maintains all functionality during and after resize
- ✅ Adapts layout to available space

## Usage

### Running the Demo

The resize handling works automatically when running the demo application:

```bash
# Run with curses backend (terminal)
python ttk/demo/demo_ttk.py --backend curses

# Run with CoreGraphics backend (macOS)
python ttk/demo/demo_ttk.py --backend coregraphics
```

### Testing Resize Behavior

1. Launch the demo application
2. Resize the terminal window (curses) or application window (CoreGraphics)
3. Observe that:
   - The interface redraws immediately
   - Corner markers move to new positions
   - Dimension display updates
   - Layout adapts to new size
   - All functionality continues to work

### Running Tests

```bash
# Run resize handling tests
python -m pytest ttk/test/test_resize_handling.py -v

# Run all demo tests
python -m pytest ttk/test/test_demo_application.py -v
python -m pytest ttk/test/test_test_interface.py -v
```

## Implementation Notes

### Design Decisions

1. **Resize events don't appear in history**: This prevents cluttering the input history with non-user-initiated events

2. **Immediate redraw**: Resize events trigger an immediate redraw rather than waiting for the next frame, ensuring responsive UI updates

3. **No special resize handling needed in draw methods**: The existing dynamic dimension queries mean all drawing code automatically adapts to new dimensions

4. **Separate resize check in main loop**: Checking for resize before normal input handling ensures resize events are processed quickly

### Backend Compatibility

The resize handling works with both backends:

- **Curses backend**: Terminal resize events are translated to `KeyCode.RESIZE`
- **CoreGraphics backend**: Window resize events are translated to `KeyCode.RESIZE`

Both backends use the same `KeyEvent` structure, ensuring consistent behavior.

### Performance Considerations

- Resize events trigger a full redraw, which is necessary to adapt the layout
- The performance monitor (if enabled) tracks resize-triggered redraws
- No special optimization is needed as resize events are relatively infrequent

## Future Enhancements

Potential improvements for resize handling:

1. **Smooth resize animations**: Animate transitions between sizes
2. **Minimum window size**: Enforce minimum dimensions for usability
3. **Layout persistence**: Remember layout preferences across resizes
4. **Resize throttling**: Debounce rapid resize events during dragging
5. **Aspect ratio handling**: Optimize layout for different aspect ratios

## Related Documentation

- [Test Interface Implementation](TEST_INTERFACE_IMPLEMENTATION.md)
- [Demo Application Structure](DEMO_STRUCTURE.md)
- [Input Event System](../API_REFERENCE.md#input-events)
- [Coordinate System](../API_REFERENCE.md#coordinate-system)
