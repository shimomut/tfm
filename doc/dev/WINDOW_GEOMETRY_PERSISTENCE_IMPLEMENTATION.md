# Window Geometry Persistence Implementation

## Overview

This document provides detailed implementation information for the window geometry persistence feature in TFM's CoreGraphics backend. It explains the technical architecture, macOS integration mechanisms, storage formats, and implementation patterns used to achieve automatic window size and position persistence across application sessions.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    TFM Application Layer                        │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         CoreGraphicsBackend Class                         │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────┐    │ │
│  │  │  _create_window()                               │    │ │
│  │  │  - Creates NSWindow instance                    │    │ │
│  │  │  - Calls setFrameAutosaveName:                  │    │ │
│  │  │  - Triggers automatic restoration               │    │ │
│  │  └─────────────────────────────────────────────────┘    │ │
│  │                      │                                    │ │
│  │                      │ setFrameAutosaveName:             │ │
│  │                      ▼                                    │ │
│  │  ┌─────────────────────────────────────────────────┐    │ │
│  │  │  reset_window_geometry()                        │    │ │
│  │  │  - Removes NSUserDefaults entry                 │    │ │
│  │  │  - Applies default frame                        │    │ │
│  │  │  - Provides manual reset capability             │    │ │
│  │  └─────────────────────────────────────────────────┘    │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ PyObjC Bridge
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    macOS Cocoa Framework                        │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         NSWindow (AppKit)                                 │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────┐    │ │
│  │  │  Frame Autosave System                          │    │ │
│  │  │  - Monitors window frame changes                │    │ │
│  │  │  - Automatically saves to NSUserDefaults        │    │ │
│  │  │  - Automatically restores on creation           │    │ │
│  │  │  - Handles multi-monitor scenarios              │    │ │
│  │  │  - Detects off-screen positions                 │    │ │
│  │  └─────────────────────────────────────────────────┘    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              │ Automatic persistence            │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         NSUserDefaults                                    │ │
│  │                                                           │ │
│  │  Key: "NSWindow Frame TFMMainWindow"                     │ │
│  │  Value: "100 100 1200 800"                               │ │
│  │  Storage: ~/Library/Preferences/com.tfm.plist            │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

#### Window Creation and Restoration Flow

```
1. Application Launch
   │
   ├─> CoreGraphicsBackend.__init__()
   │   │
   │   └─> _create_window()
   │       │
   │       ├─> Create NSWindow with default frame
   │       │   frame = NSMakeRect(100, 100, width, height)
   │       │
   │       ├─> Call setFrameAutosaveName:("TFMMainWindow")
   │       │   │
   │       │   └─> NSWindow checks NSUserDefaults
   │       │       │
   │       │       ├─> If saved frame exists:
   │       │       │   └─> Restore saved frame automatically
   │       │       │
   │       │       └─> If no saved frame:
   │       │           └─> Use default frame from creation
   │       │
   │       └─> Window appears at correct position/size
   │
   └─> User interacts with window
       │
       ├─> User resizes window
       │   └─> NSWindow automatically saves to NSUserDefaults
       │
       ├─> User moves window
       │   └─> NSWindow automatically saves to NSUserDefaults
       │
       └─> User quits application
           └─> Final frame state persisted in NSUserDefaults
```

#### Reset Flow

```
1. reset_window_geometry() called
   │
   ├─> Get NSUserDefaults.standardUserDefaults()
   │
   ├─> Remove key "NSWindow Frame TFMMainWindow"
   │   └─> user_defaults.removeObjectForKey_(frame_key)
   │
   ├─> Synchronize NSUserDefaults
   │   └─> user_defaults.synchronize()
   │
   ├─> Calculate default frame
   │   └─> NSMakeRect(100, 100, default_width, default_height)
   │
   ├─> Apply default frame to window
   │   └─> window.setFrame_display_(default_frame, True)
   │
   └─> Log reset action
       └─> print("Window geometry reset to defaults")
```

## NSWindow Frame Autosave Mechanism

### How Frame Autosave Works

The NSWindow frame autosave feature is a built-in macOS mechanism that provides automatic window geometry persistence. When enabled, it handles all aspects of saving and restoring window frames without requiring manual intervention.

#### Key Characteristics

1. **Automatic Saving**: NSWindow monitors its own frame changes and automatically saves to NSUserDefaults
2. **Automatic Restoration**: During window creation, NSWindow checks for saved frame and restores it
3. **Multi-Monitor Support**: Handles monitor configurations, disconnections, and reconnections
4. **Off-Screen Detection**: Automatically adjusts positions that would be off-screen
5. **Zero Overhead**: No performance impact on application

### Enabling Frame Autosave

```python
# In CoreGraphicsBackend._create_window()

# Create window with initial frame
frame = Cocoa.NSMakeRect(100, 100, window_width, window_height)
self.window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
    frame,
    style_mask,
    Cocoa.NSBackingStoreBuffered,
    False
)

# Enable frame autosave with unique identifier
self.window.setFrameAutosaveName_("TFMMainWindow")
```

### Autosave Name Requirements

- **Must be unique**: Each window requiring separate persistence needs a unique name
- **Must be set early**: Call `setFrameAutosaveName:` immediately after window creation
- **Must be consistent**: Use the same name across application launches
- **Naming convention**: Use descriptive names like "TFMMainWindow", "PreferencesWindow", etc.

### What Gets Saved

The frame autosave mechanism saves:
- Window origin (x, y coordinates)
- Window size (width, height)
- Screen identifier (for multi-monitor setups)

The frame autosave mechanism does NOT save:
- Window state (minimized, maximized, fullscreen)
- Window content or internal state
- Custom window properties

## NSUserDefaults Storage Format

### Storage Location

NSUserDefaults stores preferences in property list (plist) files:

```
~/Library/Preferences/com.tfm.plist
```

The actual bundle identifier depends on how the application is packaged. For development builds, it may use a different identifier.

### Key Format

NSWindow uses a specific key format for frame autosave:

```
"NSWindow Frame <autosave-name>"
```

For TFM with autosave name "TFMMainWindow":

```
"NSWindow Frame TFMMainWindow"
```

### Value Format

The saved frame is stored as a string with space-separated values:

```
"<x> <y> <width> <height>"
```

Example:
```
"100 100 1200 800"
```

This represents:
- x = 100 (horizontal position from left edge)
- y = 100 (vertical position from bottom edge)
- width = 1200 (window width in pixels)
- height = 800 (window height in pixels)

### Coordinate System

macOS uses a bottom-left origin coordinate system:

```
┌─────────────────────────────────────┐
│                                     │ ← Top of screen
│                                     │
│         (x, y + height)             │
│         ┌──────────────┐            │
│         │              │            │
│         │    Window    │            │
│         │              │            │
│         └──────────────┘            │
│         (x, y)                      │
│                                     │
└─────────────────────────────────────┘ ← Bottom of screen (y = 0)
(0, 0)
```

### Accessing NSUserDefaults Programmatically

```python
import Cocoa

# Get standard user defaults
user_defaults = Cocoa.NSUserDefaults.standardUserDefaults()

# Read saved frame
frame_key = "NSWindow Frame TFMMainWindow"
saved_frame = user_defaults.stringForKey_(frame_key)
print(f"Saved frame: {saved_frame}")  # Output: "100 100 1200 800"

# Remove saved frame (for reset)
user_defaults.removeObjectForKey_(frame_key)
user_defaults.synchronize()  # Force immediate write to disk

# Manually set frame (not recommended - use setFrameAutosaveName: instead)
user_defaults.setObject_forKey_("200 200 1400 900", frame_key)
user_defaults.synchronize()
```

### Multi-Monitor Storage

For multi-monitor setups, NSWindow may store additional information:

```
"100 100 1200 800 0 0 1920 1080 "
```

The additional values represent the screen frame:
- Screen origin (0, 0)
- Screen size (1920, 1080)

This allows NSWindow to:
- Restore window to correct monitor
- Detect when monitor is disconnected
- Adjust position if screen configuration changes

## Implementation Details

### CoreGraphicsBackend Class Modifications

#### Constants

```python
class CoreGraphicsBackend:
    # Frame autosave name for NSWindow
    WINDOW_FRAME_AUTOSAVE_NAME = "TFMMainWindow"
```

#### Window Creation Method

```python
def _create_window(self):
    """
    Create the NSWindow with calculated dimensions and enable frame autosave.
    
    This method creates the main application window and enables automatic
    frame persistence using NSWindow's built-in frame autosave feature.
    """
    # Calculate window dimensions from grid size and character dimensions
    window_width = self.cols * self.char_width
    window_height = self.rows * self.char_height
    
    # Create window frame (positioned at top-left of screen with some offset)
    # This is the DEFAULT frame used on first launch or after reset
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
    
    try:
        # Enable automatic window frame persistence
        # This single call enables:
        # - Automatic saving on frame changes
        # - Automatic restoration on window creation
        # - Multi-monitor support
        # - Off-screen detection
        self.window.setFrameAutosaveName_(self.WINDOW_FRAME_AUTOSAVE_NAME)
    except Exception as e:
        # Log warning but continue - persistence is non-critical
        print(f"Warning: Could not enable window geometry persistence: {e}")
    
    # Set window title
    self.window.setTitle_(self.window_title)
    
    # ... rest of window setup ...
```

#### Reset Method

```python
def reset_window_geometry(self):
    """
    Reset window geometry to default size and position.
    
    This method provides a way to clear saved window geometry and return
    to the default size and position. Useful for recovering from problematic
    window states or when the user wants to reset their layout.
    
    Implementation:
    1. Clear the saved frame from NSUserDefaults
    2. Calculate default frame from configuration
    3. Apply default frame to window
    4. Log the reset action
    
    Returns:
        bool: True if reset was successful, False otherwise
    """
    try:
        # Get standard user defaults
        user_defaults = Cocoa.NSUserDefaults.standardUserDefaults()
        
        # Construct the frame key used by NSWindow
        frame_key = f"NSWindow Frame {self.WINDOW_FRAME_AUTOSAVE_NAME}"
        
        # Remove the saved frame entry
        user_defaults.removeObjectForKey_(frame_key)
        
        # Force immediate write to disk
        user_defaults.synchronize()
        
        # Calculate default window dimensions from configuration
        window_width = self.cols * self.char_width
        window_height = self.rows * self.char_height
        
        # Create default frame (same as initial creation)
        default_frame = Cocoa.NSMakeRect(100, 100, window_width, window_height)
        
        # Apply default frame to window
        # The second parameter (True) means animate the change
        self.window.setFrame_display_(default_frame, True)
        
        # Log the reset action for debugging
        print(f"Window geometry reset to defaults: {window_width}x{window_height}")
        return True
        
    except Exception as e:
        # Log error but don't crash - reset is non-critical
        print(f"Warning: Could not reset window geometry: {e}")
        return False
```

### Error Handling Strategy

The implementation follows a "fail gracefully" approach:

```python
# Pattern 1: Non-critical operation with warning
try:
    self.window.setFrameAutosaveName_(self.WINDOW_FRAME_AUTOSAVE_NAME)
except Exception as e:
    print(f"Warning: Could not enable window geometry persistence: {e}")
    # Continue without persistence - application still functional

# Pattern 2: Optional operation with return value
try:
    # Reset operation
    user_defaults.removeObjectForKey_(frame_key)
    return True
except Exception as e:
    print(f"Warning: Could not reset window geometry: {e}")
    return False  # Indicate failure but don't crash
```

### Backend-Specific Implementation

The feature is CoreGraphics backend specific:

```python
# In CoreGraphicsBackend class
def _create_window(self):
    # ... window creation ...
    self.window.setFrameAutosaveName_(self.WINDOW_FRAME_AUTOSAVE_NAME)
    # ... rest of setup ...

# Curses backend is unaffected
# No changes needed to CursesBackend class
```

## Integration with Existing Code

### Window Delegate Integration

The window geometry persistence integrates seamlessly with the existing window delegate:

```python
class WindowDelegate(Cocoa.NSObject):
    def windowWillResize_toSize_(self, window, size):
        """
        Called when window is about to resize.
        
        Frame autosave automatically saves the new size after this method
        completes, so no manual save is needed.
        """
        # Calculate new grid dimensions
        new_cols = int(size.width / self.backend.char_width)
        new_rows = int(size.height / self.backend.char_height)
        
        # Update backend grid
        self.backend.cols = new_cols
        self.backend.rows = new_rows
        
        # Notify application of resize
        if hasattr(self.backend, 'on_resize'):
            self.backend.on_resize(new_cols, new_rows)
        
        return size  # Allow the resize
        
        # NSWindow automatically saves the new frame to NSUserDefaults
```

### Startup Sequence

```python
# Application startup sequence
1. CoreGraphicsBackend.__init__()
   └─> _create_window()
       ├─> Create NSWindow with default frame
       ├─> setFrameAutosaveName:("TFMMainWindow")
       │   └─> NSWindow automatically restores saved frame if available
       └─> Window appears at correct position/size

2. Application runs normally
   └─> All frame changes automatically saved

3. Application quits
   └─> Final frame state persisted
```

## Testing Considerations

### Unit Testing

```python
def test_frame_autosave_enabled():
    """Verify frame autosave is enabled during window creation."""
    backend = CoreGraphicsBackend(cols=80, rows=24)
    
    # Verify autosave name is set
    autosave_name = backend.window.frameAutosaveName()
    assert autosave_name == "TFMMainWindow"

def test_reset_clears_defaults():
    """Verify reset removes NSUserDefaults entry."""
    backend = CoreGraphicsBackend(cols=80, rows=24)
    
    # Manually set a saved frame
    user_defaults = Cocoa.NSUserDefaults.standardUserDefaults()
    frame_key = "NSWindow Frame TFMMainWindow"
    user_defaults.setObject_forKey_("200 200 1400 900", frame_key)
    user_defaults.synchronize()
    
    # Reset geometry
    result = backend.reset_window_geometry()
    assert result == True
    
    # Verify entry is removed
    saved_frame = user_defaults.stringForKey_(frame_key)
    assert saved_frame is None
```

### Integration Testing

```python
def test_persistence_across_sessions():
    """Verify geometry persists across quit/relaunch."""
    # Launch 1: Create window and resize
    backend1 = CoreGraphicsBackend(cols=80, rows=24)
    backend1.window.setFrame_display_(
        Cocoa.NSMakeRect(200, 200, 1400, 900),
        False
    )
    # Simulate quit
    del backend1
    
    # Launch 2: Create new window
    backend2 = CoreGraphicsBackend(cols=80, rows=24)
    
    # Verify frame was restored
    frame = backend2.window.frame()
    assert abs(frame.origin.x - 200) < 1
    assert abs(frame.origin.y - 200) < 1
    assert abs(frame.size.width - 1400) < 1
    assert abs(frame.size.height - 900) < 1
```

### Manual Testing Checklist

- [ ] First launch: Window appears at default position/size
- [ ] Resize window: New size persisted after quit/relaunch
- [ ] Move window: New position persisted after quit/relaunch
- [ ] Multi-monitor: Window restores to correct monitor
- [ ] Monitor disconnect: Window moves to visible screen
- [ ] Reset: Window returns to default geometry
- [ ] Corrupted data: Application handles gracefully

## Performance Considerations

### Zero Runtime Overhead

The frame autosave mechanism has no measurable performance impact:

- **Saving**: Asynchronous, handled by macOS in background
- **Restoration**: Happens during window creation (one-time cost)
- **Memory**: Minimal (single string in NSUserDefaults)
- **Disk I/O**: Batched by macOS with other preference writes

### Optimization Notes

1. **No polling**: NSWindow monitors its own frame changes internally
2. **No manual saves**: No application code needed for persistence
3. **Efficient storage**: Simple string format, minimal disk space
4. **Lazy loading**: NSUserDefaults loads preferences on-demand

## Debugging

### Viewing Saved Geometry

```bash
# Read TFM preferences
defaults read com.tfm

# Read specific frame key
defaults read com.tfm "NSWindow Frame TFMMainWindow"

# Output: 100 100 1200 800
```

### Clearing Saved Geometry

```bash
# Remove specific frame key
defaults delete com.tfm "NSWindow Frame TFMMainWindow"

# Or use the reset method in code
backend.reset_window_geometry()
```

### Common Issues

#### Issue: Window not restoring position

**Possible causes:**
- Autosave name not set or set incorrectly
- NSUserDefaults entry corrupted or missing
- Monitor configuration changed significantly

**Debug steps:**
```python
# Check if autosave name is set
autosave_name = window.frameAutosaveName()
print(f"Autosave name: {autosave_name}")

# Check if saved frame exists
user_defaults = Cocoa.NSUserDefaults.standardUserDefaults()
frame_key = f"NSWindow Frame {autosave_name}"
saved_frame = user_defaults.stringForKey_(frame_key)
print(f"Saved frame: {saved_frame}")
```

#### Issue: Window appears off-screen

**Cause:** macOS should automatically detect and adjust, but may fail in edge cases

**Solution:**
```python
# Reset to defaults
backend.reset_window_geometry()
```

## Future Enhancements

### Potential Improvements

1. **Configuration Option**
   ```python
   # Add to config
   ENABLE_WINDOW_GEOMETRY_PERSISTENCE = True
   
   # Check in _create_window
   if config.ENABLE_WINDOW_GEOMETRY_PERSISTENCE:
       self.window.setFrameAutosaveName_(self.WINDOW_FRAME_AUTOSAVE_NAME)
   ```

2. **Multiple Windows**
   ```python
   # Use unique names for different windows
   MAIN_WINDOW_AUTOSAVE_NAME = "TFMMainWindow"
   PREFERENCES_WINDOW_AUTOSAVE_NAME = "TFMPreferencesWindow"
   ```

3. **Workspace Profiles**
   ```python
   # Different geometries for different profiles
   autosave_name = f"TFMMainWindow_{profile_name}"
   self.window.setFrameAutosaveName_(autosave_name)
   ```

4. **Fullscreen State Persistence**
   ```python
   # Save fullscreen state separately
   user_defaults.setBool_forKey_(is_fullscreen, "TFMWindowFullscreen")
   ```

## References

### Apple Documentation

- [NSWindow Class Reference](https://developer.apple.com/documentation/appkit/nswindow)
- [NSWindow Frame Autosave](https://developer.apple.com/documentation/appkit/nswindow/1419697-setframeautosavename)
- [NSUserDefaults Class Reference](https://developer.apple.com/documentation/foundation/nsuserdefaults)

### PyObjC Documentation

- [PyObjC Documentation](https://pyobjc.readthedocs.io/)
- [Working with Cocoa](https://pyobjc.readthedocs.io/en/latest/core/intro.html)

### Related TFM Documentation

- [Window Geometry Persistence Feature](../WINDOW_GEOMETRY_PERSISTENCE_FEATURE.md) - End-user documentation
- [CoreGraphics Backend](../../ttk/doc/COREGRAPHICS_BACKEND.md) - Backend architecture
- [Desktop Mode Guide](../DESKTOP_MODE_GUIDE.md) - Desktop mode overview

## Conclusion

The window geometry persistence implementation leverages macOS's built-in NSWindow frame autosave mechanism to provide robust, automatic window geometry persistence with minimal code. The implementation is:

- **Simple**: Single method call to enable persistence
- **Reliable**: Uses battle-tested macOS APIs
- **Efficient**: Zero runtime overhead
- **Robust**: Handles multi-monitor, off-screen, and error scenarios automatically
- **Maintainable**: Minimal code to maintain

This approach follows platform conventions and provides a seamless user experience while requiring minimal implementation effort.
