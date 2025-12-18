# Menu Validation Optimization

## Overview

This document describes the optimization of menu state validation from a polling-based approach to the native macOS `validateMenuItem:` delegate pattern.

## Problem

The original implementation updated menu item states every frame (every 16ms) by:
1. Calling `_update_menu_states()` in the main loop
2. Iterating through all menu items
3. Calling `update_menu_item_state()` for each item
4. Setting enabled/disabled state via `NSMenuItem.setEnabled_()`

This approach had several issues:
- **Inefficient**: Updated menu states 60 times per second even when menus weren't visible
- **Unnecessary work**: Most of the time, menu states don't change between frames
- **Not idiomatic**: Doesn't follow macOS best practices for menu validation

## Solution

Implemented the native macOS `validateMenuItem:` delegate pattern:

### How It Works

1. **Callback Registration**: Application registers a validation callback once during initialization
2. **On-Demand Validation**: macOS calls `validateMenuItem:` only when a menu is about to be displayed
3. **Efficient Updates**: Menu states are validated only when needed, not every frame

### Implementation Details

#### TTK Backend (ttk/backends/coregraphics_backend.py)

```python
def set_menu_validation_callback(self, callback):
    """Set callback for menu validation."""
    self.menu_validation_callback = callback

def validateMenuItem_(self, menu_item):
    """macOS delegate method - called when menu opens."""
    item_id = menu_item.representedObject()
    if self.menu_validation_callback:
        return self.menu_validation_callback(item_id)
    return True
```

Key changes:
- Set `setAutoenablesItems_(True)` to enable automatic validation
- Set application delegate to self to receive `validateMenuItem:` calls
- Store validation callback for use in delegate method

#### Application Code (src/tfm_main.py)

```python
def _setup_menu_validation(self):
    """Set up menu validation callback."""
    self.renderer.set_menu_validation_callback(self._validate_menu_item)

def _validate_menu_item(self, item_id: str) -> bool:
    """Validate menu item (called by macOS when menu opens)."""
    return self.menu_manager.should_enable_item(item_id)
```

Key changes:
- Register validation callback during initialization
- Remove polling call from main loop
- Validation happens automatically when user opens a menu

## Benefits

### Performance
- **60x reduction in validation calls**: From 60 times per second to only when menus open
- **Zero overhead when menus closed**: No CPU cycles wasted on invisible menus
- **Scales better**: Performance independent of number of menu items

### Code Quality
- **Idiomatic macOS code**: Follows Apple's recommended patterns
- **Cleaner architecture**: Separation of concerns between UI and validation logic
- **Better maintainability**: Standard pattern familiar to macOS developers

### User Experience
- **Responsive menus**: Validation happens instantly when menu opens
- **No lag**: Menu states always reflect current application state
- **Native behavior**: Menus behave like standard macOS applications

## Migration Guide

### For Applications Using TTK

**Old Pattern (Deprecated):**
```python
# In main loop - called every frame
def main_loop(self):
    while running:
        # Update menu states every frame
        states = menu_manager.update_menu_states()
        for item_id, enabled in states.items():
            renderer.update_menu_item_state(item_id, enabled)
        
        event = renderer.get_input()
        # ... handle event
```

**New Pattern (Recommended):**
```python
# During initialization - called once
def initialize(self):
    renderer.set_menu_validation_callback(self.validate_menu_item)

def validate_menu_item(self, item_id):
    """Called automatically by macOS when menu opens."""
    if item_id == 'file.delete':
        return len(selected_files) > 0
    elif item_id == 'edit.paste':
        return clipboard_has_content()
    return True

# In main loop - no menu updates needed
def main_loop(self):
    while running:
        # No menu state updates - handled automatically
        event = renderer.get_input()
        # ... handle event
```

### Backward Compatibility

The old `update_menu_item_state()` method is still available but deprecated:
- Kept for backward compatibility
- Should not be called every frame
- Use `set_menu_validation_callback()` for new code

## Technical Details

### macOS Menu Validation Flow

1. User clicks on menu bar item (e.g., "File")
2. macOS prepares to display the menu
3. For each menu item, macOS calls `validateMenuItem:` on the delegate
4. Delegate returns `True` (enabled) or `False` (disabled)
5. macOS displays menu with correct enabled/disabled states

### Why This Is Better

**Polling Approach:**
- Application: "Let me check all menu states... again... and again..."
- System: "Okay, but nobody's looking at the menus"
- Application: "I'll keep checking anyway, just in case"

**Validation Callback Approach:**
- System: "User is opening the File menu, what should be enabled?"
- Application: "Let me check... Delete is enabled, Rename is disabled"
- System: "Thanks! I'll show it that way"

## Performance Measurements

### Before (Polling)
- Menu state updates: 60 times per second
- CPU usage: Constant overhead even when idle
- Validation calls: ~240 per second (4 menus × 60 fps)

### After (Callback)
- Menu state updates: Only when menu opens (~1-2 times per second during active use)
- CPU usage: Zero overhead when menus not in use
- Validation calls: ~4-8 per menu open (only items in opened menu)

**Result**: ~60x reduction in validation overhead

## Future Enhancements

Potential improvements:
1. **Caching**: Cache validation results within a menu open session
2. **Batch validation**: Validate multiple items in one call
3. **Lazy validation**: Only validate visible items in large menus
4. **State change notifications**: Invalidate cache when application state changes

## References

- [Apple Documentation: NSMenuItemValidation](https://developer.apple.com/documentation/appkit/nsmenuitemvalidation)
- [Apple Documentation: NSMenu](https://developer.apple.com/documentation/appkit/nsmenu)
- [Menu Programming Guide](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/MenuList/MenuList.html)

## Related Files

- `ttk/backends/coregraphics_backend.py` - Backend implementation
- `ttk/renderer.py` - Abstract interface
- `src/tfm_main.py` - Application integration
- `src/tfm_menu_manager.py` - Menu state logic
