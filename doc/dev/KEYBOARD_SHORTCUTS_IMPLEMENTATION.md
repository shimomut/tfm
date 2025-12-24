# Keyboard Shortcuts Implementation

## Overview

This document describes the technical implementation of keyboard shortcuts in TFM's Desktop mode. Keyboard shortcuts are implemented using native operating system menu APIs to provide reliable, platform-standard behavior.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TFM Application Layer                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MenuManager (src/tfm_menu_manager.py)                 │ │
│  │  - Defines shortcuts in platform-independent format    │ │
│  │  - Uses _get_shortcut_modifier() for platform detection│ │
│  │  - Builds menu structure with shortcuts                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓ Menu Structure
┌─────────────────────────────────────────────────────────────┐
│                      TTK Library Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Renderer Abstract Interface (ttk/renderer.py)         │ │
│  │  - set_menu_bar(menu_structure)                        │ │
│  │  - MenuEvent class for shortcut events                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  CoreGraphics Backend (ttk/backends/coregraphics_backend.py) │
│  │  - _parse_shortcut() converts to native format         │ │
│  │  - NSMenuItem with key equivalents                     │ │
│  │  - Generates MenuEvent on shortcut press               │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Menu Structure Creation**: MenuManager creates menu structure with shortcuts
2. **Platform Detection**: `_get_shortcut_modifier()` determines Cmd (macOS) or Ctrl (Windows)
3. **Menu Bar Setup**: TFM calls `set_menu_bar()` with menu structure
4. **Shortcut Parsing**: Backend's `_parse_shortcut()` converts to native format
5. **Native Registration**: OS registers shortcuts with menu items
6. **Event Generation**: OS generates menu event when shortcut is pressed
7. **Event Delivery**: MenuEvent delivered through `get_event()`
8. **Action Execution**: TFM's `_handle_menu_event()` executes action

## Implementation Details

### MenuManager Shortcut Definition

The MenuManager defines shortcuts in a platform-independent format:

```python
def _get_shortcut_modifier(self):
    """Get the platform-appropriate modifier key for shortcuts.
    
    Returns:
        str: 'Cmd' for macOS, 'Ctrl' for other platforms
    """
    return 'Cmd' if platform.system() == 'Darwin' else 'Ctrl'

def _build_file_menu(self, modifier):
    """Build the File menu structure with shortcuts."""
    return {
        'id': 'file',
        'label': 'File',
        'items': [
            {
                'id': self.FILE_NEW_FILE,
                'label': 'New File',
                'shortcut': f'{modifier}+N',  # Cmd+N on macOS, Ctrl+N on Windows
                'enabled': True
            },
            {
                'id': self.FILE_NEW_FOLDER,
                'label': 'New Folder',
                'shortcut': f'{modifier}+Shift+N',  # Multiple modifiers
                'enabled': True
            },
            # ... more items
        ]
    }
```

### Shortcut Format Specification

Shortcuts follow this format:

```
Shortcut := Modifier ('+' Modifier)* '+' Key

Modifier := 'Cmd' | 'Ctrl' | 'Shift' | 'Alt' | 'Option'
Key      := Single character or special key name
```

Examples:
- `Cmd+N` - Command + N
- `Cmd+Shift+N` - Command + Shift + N
- `Ctrl+C` - Control + C
- `Cmd+Up` - Command + Up Arrow

### CoreGraphics Backend Parsing

The CoreGraphics backend converts platform-independent shortcuts to macOS format:

```python
def _parse_shortcut(self, shortcut: str):
    """Parse keyboard shortcut string into macOS key equivalent and modifier mask.
    
    Args:
        shortcut: Shortcut string (e.g., 'Cmd+N', 'Cmd+Shift+S')
    
    Returns:
        Tuple of (key_equivalent: str, modifier_mask: int or None)
    """
    if not shortcut:
        return ('', None)
    
    # Split shortcut into parts
    parts = shortcut.split('+')
    key = parts[-1]
    modifiers = parts[:-1]
    
    # Build modifier mask
    modifier_mask = 0
    for mod in modifiers:
        mod_lower = mod.lower()
        if mod_lower == 'cmd' or mod_lower == 'command':
            modifier_mask |= Cocoa.NSEventModifierFlagCommand
        elif mod_lower == 'shift':
            modifier_mask |= Cocoa.NSEventModifierFlagShift
        elif mod_lower == 'ctrl' or mod_lower == 'control':
            modifier_mask |= Cocoa.NSEventModifierFlagControl
        elif mod_lower == 'alt' or mod_lower == 'option':
            modifier_mask |= Cocoa.NSEventModifierFlagOption
    
    # Convert key to lowercase unless Shift is in modifiers
    if 'shift' not in [m.lower() for m in modifiers]:
        key = key.lower()
    
    return (key, modifier_mask if modifier_mask > 0 else None)
```

### NSMenuItem Integration

The parsed shortcut is applied to NSMenuItem:

```python
def _create_menu_item(self, item_def: dict):
    """Create NSMenuItem with keyboard shortcut."""
    # Parse keyboard shortcut
    key_equivalent, modifier_mask = self._parse_shortcut(item_def.get('shortcut', ''))
    
    # Create menu item with key equivalent
    item = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        item_def['label'],
        objc.selector(self._menu_item_selected_, signature=b'v@:@'),
        key_equivalent
    )
    
    # Set modifier mask if present
    if modifier_mask is not None:
        item.setKeyEquivalentModifierMask_(modifier_mask)
    
    # Set other properties
    item.setEnabled_(item_def.get('enabled', True))
    item.setRepresentedObject_(item_def['id'])
    item.setTarget_(self)
    
    return item
```

### Event Generation

When a keyboard shortcut is pressed:

1. macOS menu system recognizes the shortcut
2. Calls `_menu_item_selected_()` callback
3. Callback creates MenuEvent and adds to queue

```python
def _menu_item_selected_(self, sender):
    """Callback when menu item is selected (via click or shortcut).
    
    Args:
        sender: The NSMenuItem that was selected
    """
    item_id = sender.representedObject()
    
    if item_id:
        from ttk.input_event import MenuEvent
        event = MenuEvent(item_id=item_id)
        self.menu_event_queue.append(event)
```

### Event Handling in TFM

TFM's main loop handles MenuEvents:

```python
def main_loop(self):
    """Main event loop."""
    while self.running:
        event = self.renderer.get_event()
        
        if isinstance(event, MenuEvent):
            self._handle_menu_event(event)
        # ... handle other events

def _handle_menu_event(self, event):
    """Handle menu selection events (from clicks or shortcuts).
    
    Args:
        event: MenuEvent with item_id
    
    Returns:
        bool: True if event was handled
    """
    item_id = event.item_id
    
    if item_id == 'file.new_file':
        return self._action_create_file()
    elif item_id == 'file.quit':
        return self._action_quit()
    # ... handle other menu items
```

## Platform-Specific Considerations

### macOS (CoreGraphics Backend)

**Key Equivalent Format**:
- Single character (lowercase): `'n'`, `'c'`, `'v'`
- With Shift: uppercase character: `'N'`, `'S'`
- Special keys: Use NSEvent constants (not yet implemented for arrow keys)

**Modifier Masks**:
- `NSEventModifierFlagCommand` - Command (⌘) key
- `NSEventModifierFlagShift` - Shift key
- `NSEventModifierFlagControl` - Control key
- `NSEventModifierFlagOption` - Option (Alt) key

**Behavior**:
- Shortcuts work even when menu is not open
- System handles shortcut recognition and event generation
- Shortcuts are displayed automatically in menu items
- Disabled menu items don't respond to shortcuts

### Windows (Future Implementation)

**Accelerator Format**:
- Will use Win32 ACCEL structure
- Format: `FVIRTKEY | modifier_flags, virtual_key_code`

**Modifier Flags**:
- `FCONTROL` - Ctrl key
- `FSHIFT` - Shift key
- `FALT` - Alt key

**Implementation Notes**:
- Will need to parse shortcuts into virtual key codes
- Accelerator table registered with window
- Similar event generation pattern to macOS

## Testing

### Unit Tests

Test shortcut parsing and menu structure:

```python
def test_keyboard_shortcuts_use_correct_modifier(self):
    """Test that shortcuts use platform-appropriate modifier"""
    expected_modifier = 'Cmd' if platform.system() == 'Darwin' else 'Ctrl'
    
    menus = self.menu_manager.menu_structure['menus']
    for menu in menus:
        for item in menu['items']:
            if 'shortcut' in item and item['shortcut']:
                self.assertTrue(
                    item['shortcut'].startswith(expected_modifier),
                    f"Shortcut '{item['shortcut']}' should start with '{expected_modifier}'"
                )
```

### Integration Tests

Test end-to-end shortcut functionality:

```python
def test_keyboard_shortcut_generates_menu_event(self):
    """Test that pressing a keyboard shortcut generates a MenuEvent"""
    # Set up menu bar
    backend.set_menu_bar(menu_structure)
    
    # Simulate Cmd+N shortcut press
    # (This requires platform-specific event injection)
    
    # Get event
    event = backend.get_event(timeout_ms=100)
    
    # Verify MenuEvent was generated
    assert isinstance(event, MenuEvent)
    assert event.item_id == 'file.new_file'
```

### Demo Scripts

Demo scripts verify shortcut functionality:

- `demo/demo_menu_keyboard_shortcuts.py` - Interactive shortcut testing

## Performance Considerations

### Shortcut Registration

- Shortcuts are registered once during menu bar creation
- No runtime overhead for shortcut recognition
- OS handles all shortcut detection and event generation

### Event Processing

- MenuEvents are processed identically to menu clicks
- No additional overhead compared to menu selection
- Event queue prevents event loss during processing

## Error Handling

### Invalid Shortcuts

```python
def _parse_shortcut(self, shortcut: str):
    """Parse shortcut with error handling."""
    if not shortcut:
        return ('', None)
    
    try:
        # Parse shortcut
        parts = shortcut.split('+')
        # ... parsing logic
    except Exception as e:
        # Log error and return empty shortcut
        print(f"Warning: Failed to parse shortcut '{shortcut}': {e}")
        return ('', None)
```

### Shortcut Conflicts

- OS handles shortcut conflicts automatically
- System shortcuts take precedence over application shortcuts
- Application shortcuts take precedence when app is active

## Future Enhancements

### Custom Shortcuts

Allow users to customize keyboard shortcuts:

```python
class MenuManager:
    def set_custom_shortcut(self, item_id: str, shortcut: str):
        """Set custom keyboard shortcut for menu item."""
        # Update menu structure
        # Rebuild menu bar
        pass
```

### Shortcut Hints

Display shortcut hints in the application:

```python
def get_shortcut_for_action(self, action: str) -> str:
    """Get keyboard shortcut for an action."""
    # Look up shortcut in menu structure
    # Return formatted shortcut string
    pass
```

### Shortcut Chords

Support multi-key shortcuts (e.g., Cmd+K, Cmd+S):

```python
# First key: Cmd+K
# Second key: Cmd+S
# Action: Open settings
```

## Debugging

### Enable Shortcut Logging

```python
def _menu_item_selected_(self, sender):
    """Callback with logging."""
    item_id = sender.representedObject()
    print(f"Menu item selected: {item_id}")
    
    # Check if triggered by shortcut
    current_event = Cocoa.NSApp.currentEvent()
    if current_event.type() == Cocoa.NSEventTypeKeyDown:
        print(f"  Triggered by keyboard shortcut")
    else:
        print(f"  Triggered by menu click")
    
    # ... create event
```

### Verify Shortcut Registration

```python
def verify_shortcuts(self):
    """Verify all shortcuts are registered correctly."""
    for item_id, menu_item in self.menu_items.items():
        key_equiv = menu_item.keyEquivalent()
        mod_mask = menu_item.keyEquivalentModifierMask()
        
        if key_equiv:
            print(f"{item_id}: {key_equiv} (mask: {mod_mask})")
```

## References

### Apple Documentation

- [NSMenuItem Class Reference](https://developer.apple.com/documentation/appkit/nsmenuitem)
- [NSEvent Modifier Flags](https://developer.apple.com/documentation/appkit/nsevent/modifierflags)
- [Menu Programming Guide](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/MenuList/MenuList.html)

### Related TFM Documentation

- [Menu Bar Feature](../MENU_BAR_FEATURE.md) - End-user menu bar documentation (includes keyboard shortcuts reference)
- CoreGraphics Backend Implementation - Backend details

## Code Locations

- **MenuManager**: `src/tfm_menu_manager.py`
- **Renderer Interface**: `ttk/renderer.py`
- **CoreGraphics Backend**: `ttk/backends/coregraphics_backend.py`
- **MenuEvent**: `ttk/input_event.py`
- **Tests**: `test/test_menu_manager.py`
- **Demo**: `demo/demo_menu_keyboard_shortcuts.py`
