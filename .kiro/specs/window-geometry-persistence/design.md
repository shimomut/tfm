# Design Document

## Overview

This document describes the design for implementing window geometry persistence in TFM's CoreGraphics backend mode. The feature leverages macOS's native NSWindow frame autosave functionality to automatically save and restore window size and position across application sessions.

The implementation is intentionally minimal, relying on macOS's built-in persistence mechanisms rather than implementing custom save/load logic. This approach provides robust multi-monitor support, off-screen detection, and automatic persistence with minimal code changes.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TFM Application                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         CoreGraphics Backend                         │  │
│  │                                                      │  │
│  │  ┌────────────────────────────────────────────┐    │  │
│  │  │  Window Initialization                     │    │  │
│  │  │  - Create NSWindow                         │    │  │
│  │  │  - Set frame autosave name                 │    │  │
│  │  │  - Apply default geometry (first launch)   │    │  │
│  │  └────────────────────────────────────────────┘    │  │
│  │                      │                              │  │
│  │                      ▼                              │  │
│  │  ┌────────────────────────────────────────────┐    │  │
│  │  │  NSWindow (macOS Cocoa)                    │    │  │
│  │  │  - Automatic frame persistence             │    │  │
│  │  │  - Multi-monitor support                   │    │  │
│  │  │  - Off-screen detection                    │    │  │
│  │  └────────────────────────────────────────────┘    │  │
│  │                      │                              │  │
│  │                      ▼                              │  │
│  │  ┌────────────────────────────────────────────┐    │  │
│  │  │  NSUserDefaults (macOS)                    │    │  │
│  │  │  - Stores window frame                     │    │  │
│  │  │  - Key: "NSWindow Frame <autosave-name>"   │    │  │
│  │  │  - Value: "x y width height"               │    │  │
│  │  └────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Initialization**: CoreGraphics backend creates NSWindow and calls `setFrameAutosaveName:` with a unique identifier
2. **Automatic Restoration**: NSWindow automatically restores frame from NSUserDefaults if available
3. **Automatic Persistence**: NSWindow automatically saves frame to NSUserDefaults on any geometry change
4. **Reset Mechanism**: Optional utility method to clear saved frame and reset to defaults

## Components and Interfaces

### CoreGraphicsBackend Class Modifications

The CoreGraphicsBackend class will be modified to enable window geometry persistence during window creation.

#### Modified Constructor

The `__init__` method will be updated to accept an optional `frame_autosave_name` parameter:

```python
def __init__(self, window_title: str = "TTK Application",
             font_name: str = "Menlo",
             font_size: int = 12,
             rows: int = 24,
             cols: int = 80,
             frame_autosave_name: Optional[str] = None):
    """
    Initialize the CoreGraphics backend.
    
    Args:
        window_title: Title for the application window
        font_name: Name of the monospace font to use
        font_size: Font size in points
        rows: Number of rows in the character grid
        cols: Number of columns in the character grid
        frame_autosave_name: Optional name for NSWindow frame autosave.
                           If provided, enables automatic window geometry persistence.
                           If None, defaults to "TTKApplication".
    """
    # ... existing initialization code ...
    
    # Store frame autosave name (use default if not provided)
    self.frame_autosave_name = frame_autosave_name or "TTKApplication"
```

#### Modified Window Creation Method

The `_create_window()` method will be updated to set the frame autosave name:

```python
def _create_window(self):
    """
    Create the NSWindow with calculated dimensions and enable frame autosave.
    """
    # Calculate window dimensions from grid size and character dimensions
    window_width = self.cols * self.char_width
    window_height = self.rows * self.char_height
    
    # Create window frame (positioned at top-left of screen with some offset)
    frame = Cocoa.NSMakeRect(100, 100, window_width, window_height)
    
    # Create window with standard style mask
    style_mask = (Cocoa.NSWindowStyleMaskTitled |
                 Cocoa.NSWindowStyleMaskClosable |
                 Cocoa.NSWindowStyleMaskMiniaturizable |
                 Cocoa.NSWindowStyleMaskResizable)
    
    self.window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        frame,
        style_mask,
        Cocoa.NSBackingStoreBuffered,
        False
    )
    
    if self.window is None:
        raise RuntimeError("Failed to create NSWindow")
    
    # Enable automatic window frame persistence
    # This tells macOS to automatically save and restore the window's
    # position and size using NSUserDefaults
    # Use the configurable frame autosave name
    self.window.setFrameAutosaveName_(self.frame_autosave_name)
    
    # Set window title
    self.window.setTitle_(self.window_title)
    
    # ... rest of window setup ...
```

#### New Reset Method

A new method will be added to reset window geometry to defaults:

```python
def reset_window_geometry(self):
    """
    Reset window geometry to default size and position.
    
    This method clears the saved window frame from NSUserDefaults and
    resets the window to the default size and position specified in
    configuration.
    
    Returns:
        bool: True if reset was successful, False otherwise
    """
    try:
        # Clear the saved frame from NSUserDefaults
        user_defaults = Cocoa.NSUserDefaults.standardUserDefaults()
        frame_key = f"NSWindow Frame {self.frame_autosave_name}"
        user_defaults.removeObjectForKey_(frame_key)
        user_defaults.synchronize()
        
        # Calculate default window dimensions
        window_width = self.cols * self.char_width
        window_height = self.rows * self.char_height
        
        # Create default frame
        default_frame = Cocoa.NSMakeRect(100, 100, window_width, window_height)
        
        # Apply default frame to window
        self.window.setFrame_display_(default_frame, True)
        
        print(f"Window geometry reset to defaults: {window_width}x{window_height}")
        return True
        
    except Exception as e:
        print(f"Warning: Could not reset window geometry: {e}")
        return False
```

### NSUserDefaults Storage Format

macOS stores the window frame in NSUserDefaults with the following format:

- **Key**: `"NSWindow Frame <autosave-name>"` (e.g., `"NSWindow Frame TFMMainWindow"`)
- **Value**: String in format `"x y width height"` (e.g., `"100 100 800 600"`)
- **Coordinates**: Bottom-left origin (macOS screen coordinates)

The system automatically handles:
- Saving on window move/resize
- Restoring on window creation
- Multi-monitor configurations
- Off-screen detection and adjustment

## Data Models

### Window Geometry Data

Window geometry is represented by NSRect in macOS:

```python
# NSRect structure (from Cocoa framework)
NSRect = {
    'origin': {
        'x': float,  # X coordinate (left edge)
        'y': float   # Y coordinate (bottom edge in screen coordinates)
    },
    'size': {
        'width': float,   # Window width in pixels
        'height': float   # Window height in pixels
    }
}
```

### Configuration Data

Default window geometry is specified in TFM configuration:

```python
# From src/tfm_config.py DefaultConfig class
DESKTOP_WINDOW_WIDTH = 1200   # Default window width in pixels
DESKTOP_WINDOW_HEIGHT = 800   # Default window height in pixels
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Geometry persistence round-trip
*For any* valid window geometry (size and position), if the window is set to that geometry, the application is quit, and then relaunched, the window geometry should match the original geometry (within reasonable tolerance for screen boundaries).
**Validates: Requirements 1.4**

### Property 2: Resize persistence
*For any* valid window size, if the window is resized to that size, the size should be persisted to NSUserDefaults immediately.
**Validates: Requirements 1.2, 4.3**

### Property 3: Move persistence
*For any* valid window position, if the window is moved to that position, the position should be persisted to NSUserDefaults immediately.
**Validates: Requirements 1.3, 4.3**

### Property 4: Grid recalculation on restore
*For any* restored window size, the character grid dimensions should be correctly recalculated based on the window size and character dimensions.
**Validates: Requirements 5.4**

### Property 5: Programmatic resize compatibility
*For any* programmatic window resize operation, the resize should complete successfully and the new size should be persisted.
**Validates: Requirements 5.2**

### Property 6: Resize event handling preservation
*For any* window resize (user or programmatic), the window delegate's resize handler should be called and the character grid should be updated correctly.
**Validates: Requirements 5.3**

### Property 7: Reset clears persistence
*For any* saved window geometry, calling reset should clear the NSUserDefaults entry and the window should return to default geometry.
**Validates: Requirements 6.2, 6.3**

### Property 8: Frame autosave name configurability
*For any* valid frame autosave name string provided during initialization, the CoreGraphics backend should use that name for NSWindow frame persistence, and different names should result in separate NSUserDefaults entries.
**Validates: Requirements 7.1, 7.3**

## Error Handling

### Error Scenarios and Handling

1. **Corrupted NSUserDefaults Data**
   - **Detection**: NSWindow fails to restore frame or restores invalid frame
   - **Handling**: macOS automatically falls back to default frame specified in window creation
   - **User Impact**: Window appears at default position/size
   - **Logging**: No explicit logging needed (macOS handles silently)

2. **Missing NSUserDefaults Data (First Launch)**
   - **Detection**: No saved frame exists in NSUserDefaults
   - **Handling**: Window uses default frame specified in window creation
   - **User Impact**: Window appears at default position/size
   - **Logging**: No logging needed (expected behavior)

3. **Off-Screen Window Position**
   - **Detection**: Saved position is outside visible screen area
   - **Handling**: macOS automatically adjusts position to be visible
   - **User Impact**: Window appears at adjusted position on visible screen
   - **Logging**: No explicit logging needed (macOS handles automatically)

4. **Monitor Configuration Changes**
   - **Detection**: Saved position references disconnected monitor
   - **Handling**: macOS automatically moves window to primary monitor
   - **User Impact**: Window appears on primary monitor
   - **Logging**: No explicit logging needed (macOS handles automatically)

5. **Reset Operation Failure**
   - **Detection**: Exception during NSUserDefaults removal or frame setting
   - **Handling**: Log warning and return False
   - **User Impact**: Window geometry may not reset, but application continues
   - **Logging**: `"Warning: Could not reset window geometry: {error}"`

6. **Frame Autosave Name Setting Failure**
   - **Detection**: Exception during setFrameAutosaveName call
   - **Handling**: Log warning and continue (persistence disabled but app functional)
   - **User Impact**: Window geometry not persisted, but application works normally
   - **Logging**: `"Warning: Could not enable window geometry persistence: {error}"`

### Error Recovery Strategy

The design follows a "fail gracefully" approach:
- All persistence operations are non-critical to core functionality
- Failures result in warnings but don't prevent application operation
- macOS provides automatic fallback behavior for most error scenarios
- Reset mechanism provides user-accessible recovery option

## Testing Strategy

### Unit Testing

Unit tests will verify the implementation details:

1. **Test Frame Autosave Name Configuration**
   - Verify `setFrameAutosaveName:` is called during window creation
   - Verify the autosave name matches the expected constant
   - Verify the method is only called in CoreGraphics backend

2. **Test Reset Method**
   - Verify reset clears NSUserDefaults entry
   - Verify reset applies default frame to window
   - Verify reset returns True on success
   - Verify reset logs appropriate messages

3. **Test Backend-Specific Behavior**
   - Verify curses backend doesn't call NSWindow methods
   - Verify CoreGraphics backend enables persistence

### Property-Based Testing

Property-based tests will verify the correctness properties defined above. Each property will be tested with randomly generated valid inputs to ensure the behavior holds across all cases.

#### Test Configuration

- **Framework**: Use Python's `hypothesis` library for property-based testing
- **Iterations**: Each property test should run a minimum of 100 iterations
- **Input Generation**: Generate random window geometries within valid screen bounds

#### Property Test Implementations

1. **Property 1: Geometry persistence round-trip**
   - Generate random valid window geometries
   - Set window geometry, quit, relaunch
   - Verify restored geometry matches original (within tolerance)

2. **Property 2: Resize persistence**
   - Generate random valid window sizes
   - Resize window
   - Verify NSUserDefaults contains updated size

3. **Property 3: Move persistence**
   - Generate random valid window positions
   - Move window
   - Verify NSUserDefaults contains updated position

4. **Property 4: Grid recalculation on restore**
   - Generate random valid window sizes
   - Restore window with that size
   - Verify grid dimensions = window size / character size

5. **Property 5: Programmatic resize compatibility**
   - Generate random valid window sizes
   - Programmatically resize window
   - Verify resize succeeds and is persisted

6. **Property 6: Resize event handling preservation**
   - Generate random valid window sizes
   - Resize window (user or programmatic)
   - Verify delegate's resize handler is called
   - Verify grid is updated correctly

7. **Property 7: Reset clears persistence**
   - Generate random valid window geometries
   - Save geometry, then reset
   - Verify NSUserDefaults entry is cleared
   - Verify window returns to default geometry

### Integration Testing

Integration tests will verify the feature works correctly in the full application context:

1. **Test First Launch Behavior**
   - Clear NSUserDefaults
   - Launch TFM
   - Verify window appears at default size/position

2. **Test Persistence Across Sessions**
   - Launch TFM
   - Resize and move window
   - Quit TFM
   - Relaunch TFM
   - Verify window geometry is restored

3. **Test Multi-Monitor Support**
   - Move window to secondary monitor
   - Quit and relaunch
   - Verify window appears on secondary monitor

4. **Test Reset Functionality**
   - Resize and move window
   - Call reset method
   - Verify window returns to defaults

5. **Test Error Handling**
   - Corrupt NSUserDefaults data
   - Launch TFM
   - Verify window appears at default position (fallback)

### Manual Testing

Manual testing will verify user-facing behavior:

1. **Visual Verification**
   - Verify window appears at expected position/size
   - Verify window restores correctly after quit/relaunch
   - Verify window handles multi-monitor scenarios

2. **Edge Case Testing**
   - Test with window maximized
   - Test with window minimized
   - Test with window on secondary monitor that gets disconnected
   - Test with very small/large window sizes

3. **Performance Testing**
   - Verify no noticeable delay during window creation
   - Verify no performance impact during resize/move operations

## Implementation Notes

### macOS NSWindow Frame Autosave

The implementation relies on macOS's built-in frame autosave feature:

```objective-c
// Objective-C equivalent
[window setFrameAutosaveName:@"TFMMainWindow"];
```

```python
# PyObjC equivalent
window.setFrameAutosaveName_("TFMMainWindow")
```

This single method call enables:
- Automatic saving of window frame on any change
- Automatic restoration of window frame on window creation
- Multi-monitor support with automatic position adjustment
- Off-screen detection and correction

### NSUserDefaults Key Format

macOS uses a specific key format for storing window frames:

```
Key: "NSWindow Frame <autosave-name>"
Value: "<x> <y> <width> <height>"
```

For TFM with autosave name "TFMMainWindow":
```
Key: "NSWindow Frame TFMMainWindow"
Value: "100 100 1200 800"
```

### TFM Integration

TFM will pass the frame autosave name when initializing the CoreGraphics backend:

```python
# In TFM's backend initialization code
backend = CoreGraphicsBackend(
    window_title="TFM - Two File Manager",
    font_name=config.DESKTOP_FONT_NAME,
    font_size=config.DESKTOP_FONT_SIZE,
    rows=config.DESKTOP_ROWS,
    cols=config.DESKTOP_COLS,
    frame_autosave_name="TFMMainWindow"  # TFM-specific autosave name
)
```

This approach ensures:
- TTK remains independent and reusable by other applications
- Each application using TTK can have its own window geometry persistence
- Multiple applications using TTK won't interfere with each other's saved geometries

### Coordinate System

NSWindow uses bottom-left origin coordinates:
- (0, 0) is at the bottom-left corner of the primary screen
- Y increases upward
- Multi-monitor setups extend the coordinate space

### Timing Considerations

- Frame autosave is automatic and immediate (no delay)
- Frame restoration happens during window initialization
- No explicit save/load calls needed in application code

### Backward Compatibility

- Feature is CoreGraphics backend specific
- Curses backend is unaffected
- No changes to TFM's existing state manager
- No migration needed for existing users (feature starts fresh)

### Future Enhancements

Potential future improvements (not in current scope):

1. **Configuration Option**: Add config setting to disable persistence if desired
2. **Multiple Windows**: Support multiple TFM windows with unique autosave names
3. **Workspace Profiles**: Save different geometries for different workspace profiles
4. **Fullscreen State**: Persist fullscreen state in addition to geometry
