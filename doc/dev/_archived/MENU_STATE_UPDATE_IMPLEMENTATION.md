# Menu State Update Implementation

## Overview

TFM's menu bar uses a lazy update mechanism to efficiently manage menu item states (enabled/disabled). Instead of continuously checking and updating menu states in the event loop, menu states are updated only when a menu is about to be displayed to the user.

This document describes the implementation of the menu-will-open callback mechanism that enables this optimization.

## Architecture

### Components

The menu state update system consists of three main components:

1. **TTKMenuDelegate** (ttk/backends/coregraphics_backend.py)
   - Objective-C delegate class that receives menu events from macOS
   - Implements `menuNeedsUpdate_:` method called by NSMenu before display
   - Forwards menu-will-open events to the CoreGraphics backend

2. **CoreGraphicsBackend._on_menu_will_open()** (ttk/backends/coregraphics_backend.py)
   - Backend method that receives menu-will-open notifications from delegate
   - Forwards the event to the application's event callback

3. **TFMEventCallback.on_menu_will_open()** (src/tfm_main.py)
   - Application-level callback that handles menu-will-open events
   - Calls FileManager._update_menu_states() to refresh menu item states

### Event Flow

```
User clicks menu
    ↓
macOS NSMenu calls menuNeedsUpdate_:
    ↓
TTKMenuDelegate.menuNeedsUpdate_()
    ↓
CoreGraphicsBackend._on_menu_will_open()
    ↓
TFMEventCallback.on_menu_will_open()
    ↓
FileManager._update_menu_states()
    ↓
MenuManager.update_menu_states()
    ↓
CoreGraphicsBackend.update_menu_item_state() for each item
    ↓
Menu displays with correct states
```

## Implementation Details

### TTKMenuDelegate Class

Located in `ttk/backends/coregraphics_backend.py`:

```python
class TTKMenuDelegate(Cocoa.NSObject):
    """
    Menu delegate for handling menu open events.
    
    This delegate handles menuNeedsUpdate: events, allowing the application
    to update menu item states right before a menu is displayed.
    """
    
    def initWithBackend_(self, backend):
        """Initialize the menu delegate with a backend reference."""
        self = objc.super(TTKMenuDelegate, self).init()
        if self is None:
            return None
        self.backend = backend
        return self
    
    def menuNeedsUpdate_(self, menu):
        """
        Called when a menu is about to be displayed.
        
        This method is invoked by macOS right before a menu opens,
        giving us a chance to update menu item states.
        """
        if hasattr(self.backend, '_on_menu_will_open'):
            self.backend._on_menu_will_open()
```

### Backend Integration

The CoreGraphics backend creates and assigns the delegate in `set_menu_bar()`:

```python
def set_menu_bar(self, menu_structure: dict) -> None:
    # Create menu delegate if not already done
    if not hasattr(self, 'menu_delegate'):
        self.menu_delegate = TTKMenuDelegate.alloc().initWithBackend_(self)
    
    # Create main menu bar
    main_menu = Cocoa.NSMenu.alloc().init()
    
    # Process each top-level menu
    for menu_def in menu_structure.get('menus', []):
        submenu = Cocoa.NSMenu.alloc().initWithTitle_(menu_def['label'])
        
        # Disable auto-enabling - we'll manage states manually
        submenu.setAutoenablesItems_(False)
        
        # Set delegate to receive menuNeedsUpdate: callbacks
        submenu.setDelegate_(self.menu_delegate)
        
        # ... rest of menu creation
```

The backend forwards the event to the application callback:

```python
def _on_menu_will_open(self):
    """
    Called by menu delegate when a menu is about to open.
    
    This method notifies the event callback that menu states should be updated.
    """
    if self.event_callback and hasattr(self.event_callback, 'on_menu_will_open'):
        self.event_callback.on_menu_will_open()
```

### Application Callback

The TFM event callback implements the handler in `src/tfm_main.py`:

```python
def on_menu_will_open(self) -> None:
    """
    Called when a menu is about to open.
    
    This callback updates menu item states right before the menu is displayed,
    ensuring that enabled/disabled states reflect the current application state.
    
    This is more efficient than continuously updating menu states, as it only
    updates when the user is about to interact with the menu.
    """
    try:
        # Update menu states to reflect current application state
        self.file_manager._update_menu_states()
    except Exception as e:
        # Log error message
        self.file_manager.logger.error(f"Error updating menu states: {e}")
        # Print stack trace to stderr if debug mode is enabled
        if os.environ.get('TFM_DEBUG') == '1':
            traceback.print_exc(file=sys.stderr)
```

### Menu State Update

The FileManager's `_update_menu_states()` method coordinates the update:

```python
def _update_menu_states(self):
    """
    Update menu item states based on current application state.
    
    This is called when application state changes that affect menu items
    (e.g., file selection changes, clipboard changes).
    """
    if not self.is_desktop_mode() or not self.menu_manager:
        return
    
    try:
        states = self.menu_manager.update_menu_states()
        for item_id, enabled in states.items():
            self.renderer.update_menu_item_state(item_id, enabled)
    except Exception as e:
        self.logger.error(f"Failed to update menu states: {e}")
```

## Benefits

### Performance

- **Eliminates continuous polling**: No need to check menu states on every event loop iteration
- **Reduces CPU usage**: Menu state updates only happen when menus are actually opened
- **Scales well**: Performance impact is proportional to menu usage, not application runtime

### Correctness

- **Always up-to-date**: Menu states are refreshed immediately before display
- **No stale states**: User always sees correct enabled/disabled states
- **Responsive**: Updates happen synchronously before menu display

### Maintainability

- **Clear separation of concerns**: Menu state logic is separate from event loop
- **Easy to debug**: Menu updates happen at predictable times
- **Testable**: Callback mechanism can be easily mocked and tested

## Testing

### Unit Tests

The implementation includes comprehensive unit tests in `test/test_menu_will_open_callback.py`:

1. **test_callback_has_on_menu_will_open_method**: Verifies callback method exists
2. **test_on_menu_will_open_calls_update_menu_states**: Verifies method is called
3. **test_on_menu_will_open_handles_exceptions**: Verifies error handling
4. **test_on_menu_will_open_with_debug_mode**: Verifies debug mode behavior
5. **test_callback_integration_with_file_manager**: Verifies end-to-end integration

### Integration Tests

Existing menu manager tests in `test/test_menu_manager.py` verify that menu states are correctly computed based on application state.

## Platform Considerations

### macOS

- Uses native NSMenu delegate mechanism
- `menuNeedsUpdate_:` is called automatically by AppKit
- Fully supported and tested

### Windows (Future)

When Windows support is added, a similar mechanism will be needed:
- Windows menus support `WM_INITMENUPOPUP` message
- Can be handled in window procedure to update menu states
- Should follow the same callback pattern for consistency

### Terminal Mode

- Terminal mode does not have native menus
- Menu state updates are not applicable
- Key bindings work directly without menu state checks

## Error Handling

The implementation includes robust error handling at multiple levels:

1. **Delegate level**: Checks for backend method existence before calling
2. **Backend level**: Checks for callback existence before calling
3. **Callback level**: Catches exceptions and logs errors
4. **Debug mode**: Prints stack traces when TFM_DEBUG=1

This ensures that menu state update failures never crash the application.

## Future Enhancements

### Potential Optimizations

1. **Selective updates**: Only update states for the specific menu being opened
2. **State caching**: Cache menu states and only update when application state changes
3. **Batch updates**: Group multiple state changes into single update operation

### Additional Features

1. **Menu item tooltips**: Show why items are disabled
2. **Dynamic menu items**: Add/remove items based on context
3. **Submenu state propagation**: Disable parent items when all children are disabled

## References

- **Menu Bar Feature Documentation**: `doc/MENU_BAR_FEATURE.md`
- **Menu Manager Implementation**: `src/tfm_menu_manager.py`
- **CoreGraphics Backend**: `ttk/backends/coregraphics_backend.py`
- **Event Callback System**: `ttk/renderer.py`
- **Unit Tests**: `test/test_menu_will_open_callback.py`
