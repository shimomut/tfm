# Desktop Menu Bar Feature Design

## Overview

This design document describes the implementation of a native menu bar feature for TFM when running in Desktop mode. The design emphasizes separation of concerns, with menu structure and behavior defined in the TFM application layer while TTK backends handle platform-specific rendering. Menu selections are delivered as MenuEvent objects through TTK's existing event system, maintaining consistency with other input handling.

The implementation will initially support macOS through the CoreGraphics backend, with architecture designed to support Windows in the future. Menu items can be dynamically enabled or disabled based on application state, and keyboard shortcuts are displayed and functional.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TFM Application Layer                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Menu Structure Definition (tfm_menu_manager.py)       │ │
│  │  - Menu hierarchy                                       │ │
│  │  - Menu item IDs and labels                            │ │
│  │  │  - Keyboard shortcuts                                │ │
│  │  - Enable/disable logic                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Menu Event Handler (tfm_main.py)                      │ │
│  │  - Receives MenuEvent from TTK                         │ │
│  │  - Dispatches to appropriate action handlers           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↕ MenuEvent / Menu Config
┌─────────────────────────────────────────────────────────────┐
│                      TTK Library Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Abstract Menu Interface (ttk_renderer_abc.py)         │ │
│  │  - set_menu_bar(menu_structure)                        │ │
│  │  - update_menu_item_state(item_id, enabled)            │ │
│  │  - MenuEvent class definition                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Platform-Specific Backend                             │ │
│  │  ┌──────────────────┐  ┌──────────────────┐           │ │
│  │  │ CoreGraphics     │  │ Windows Backend  │           │ │
│  │  │ (macOS)          │  │ (Future)         │           │ │
│  │  │ - NSMenu API     │  │ - Win32 API      │           │ │
│  │  └──────────────────┘  └──────────────────┘           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Initialization**: TFM creates menu structure and passes to TTK via `set_menu_bar()`
2. **Rendering**: TTK backend creates platform-native menu bar
3. **State Updates**: TFM updates menu item states via `update_menu_item_state()`
4. **User Interaction**: User selects menu item
5. **Event Generation**: TTK backend creates MenuEvent
6. **Event Delivery**: MenuEvent returned through `get_event()`
7. **Action Execution**: TFM handles MenuEvent and executes corresponding action

## Components and Interfaces

### 1. Menu Structure Definition (TFM Layer)

#### MenuManager Class (`src/tfm_menu_manager.py`)

```python
class MenuManager:
    """Manages menu structure and state for TFM Desktop mode."""
    
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.menu_structure = self._build_menu_structure()
    
    def _build_menu_structure(self) -> dict:
        """Build the complete menu structure.
        
        Returns:
            dict: Menu structure in format:
            {
                'menus': [
                    {
                        'id': 'file',
                        'label': 'File',
                        'items': [
                            {
                                'id': 'file.new_file',
                                'label': 'New File',
                                'shortcut': 'Cmd+N',
                                'enabled': True
                            },
                            {'separator': True},
                            ...
                        ]
                    },
                    ...
                ]
            }
        """
        pass
    
    def get_menu_structure(self) -> dict:
        """Get current menu structure."""
        return self.menu_structure
    
    def update_menu_states(self) -> dict:
        """Calculate current enable/disable state for all menu items.
        
        Returns:
            dict: Map of menu item IDs to enabled state
            {
                'file.new_file': True,
                'file.delete': False,  # No selection
                'edit.copy': True,
                ...
            }
        """
        pass
    
    def should_enable_item(self, item_id: str) -> bool:
        """Determine if a menu item should be enabled."""
        pass
```

#### Menu Item IDs

Standard menu item identifiers:
- File menu: `file.new_file`, `file.new_folder`, `file.open`, `file.delete`, `file.rename`, `file.quit`
- Edit menu: `edit.copy`, `edit.cut`, `edit.paste`, `edit.select_all`
- View menu: `view.show_hidden`, `view.sort_by_name`, `view.sort_by_size`, `view.sort_by_date`, `view.sort_by_extension`, `view.refresh`
- Go menu: `go.parent`, `go.home`, `go.favorites`, `go.recent`

### 2. TTK Abstract Interface

#### Renderer ABC Extensions (`ttk/ttk_renderer_abc.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class MenuEvent:
    """Event generated when a menu item is selected."""
    
    def __init__(self, item_id: str):
        self.item_id = item_id
        self.type = 'menu'
    
    def __repr__(self):
        return f"MenuEvent(item_id='{self.item_id}')"

class RendererABC(ABC):
    """Abstract base class for TTK renderers."""
    
    @abstractmethod
    def set_menu_bar(self, menu_structure: Dict[str, Any]) -> None:
        """Set the menu bar structure.
        
        Args:
            menu_structure: Dictionary defining menu hierarchy
                {
                    'menus': [
                        {
                            'id': str,
                            'label': str,
                            'items': [
                                {
                                    'id': str,
                                    'label': str,
                                    'shortcut': Optional[str],
                                    'enabled': bool
                                },
                                {'separator': True},
                                ...
                            ]
                        },
                        ...
                    ]
                }
        """
        pass
    
    @abstractmethod
    def update_menu_item_state(self, item_id: str, enabled: bool) -> None:
        """Update the enabled/disabled state of a menu item.
        
        Args:
            item_id: Unique identifier for the menu item
            enabled: True to enable, False to disable
        """
        pass
    
    @abstractmethod
    def get_event(self) -> Optional[Any]:
        """Get next event from the event queue.
        
        Returns:
            Event object (InputEvent, MenuEvent, etc.) or None
        """
        pass
```

### 3. CoreGraphics Backend Implementation

#### Menu Bar Support (`ttk/backends/coregraphics_backend.py`)

```python
class CoreGraphicsBackend(RendererABC):
    """macOS-specific backend using CoreGraphics and AppKit."""
    
    def __init__(self):
        super().__init__()
        self.menu_bar = None
        self.menu_items = {}  # Map item_id -> NSMenuItem
        self.menu_event_queue = []
    
    def set_menu_bar(self, menu_structure: Dict[str, Any]) -> None:
        """Create native macOS menu bar from structure."""
        from AppKit import NSMenu, NSMenuItem, NSApp
        
        # Create main menu bar
        main_menu = NSMenu.alloc().init()
        
        for menu_def in menu_structure.get('menus', []):
            # Create top-level menu
            menu = NSMenu.alloc().initWithTitle_(menu_def['label'])
            menu_item = NSMenuItem.alloc().init()
            menu_item.setSubmenu_(menu)
            
            # Add menu items
            for item_def in menu_def.get('items', []):
                if item_def.get('separator'):
                    menu.addItem_(NSMenuItem.separatorItem())
                else:
                    item = self._create_menu_item(item_def)
                    menu.addItem_(item)
                    self.menu_items[item_def['id']] = item
            
            main_menu.addItem_(menu_item)
        
        NSApp.setMainMenu_(main_menu)
        self.menu_bar = main_menu
    
    def _create_menu_item(self, item_def: dict):
        """Create a single NSMenuItem from definition."""
        from AppKit import NSMenuItem
        from Foundation import NSSelectorFromString
        
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            item_def['label'],
            NSSelectorFromString('menuItemSelected:'),
            self._parse_shortcut(item_def.get('shortcut', ''))
        )
        
        item.setEnabled_(item_def.get('enabled', True))
        item.setRepresentedObject_(item_def['id'])
        item.setTarget_(self.menu_delegate)
        
        return item
    
    def _parse_shortcut(self, shortcut: str) -> str:
        """Convert shortcut string to key equivalent.
        
        Args:
            shortcut: String like 'Cmd+N', 'Ctrl+C', etc.
        
        Returns:
            Key equivalent string for NSMenuItem
        """
        if not shortcut:
            return ''
        
        # Parse shortcut and return key equivalent
        # 'Cmd+N' -> 'n', 'Cmd+Shift+N' -> 'N', etc.
        parts = shortcut.split('+')
        if parts:
            return parts[-1].lower()
        return ''
    
    def update_menu_item_state(self, item_id: str, enabled: bool) -> None:
        """Update menu item enabled state."""
        if item_id in self.menu_items:
            self.menu_items[item_id].setEnabled_(enabled)
    
    def menu_item_selected(self, sender) -> None:
        """Callback when menu item is selected.
        
        This is called by the macOS menu system.
        """
        item_id = sender.representedObject()
        if item_id:
            event = MenuEvent(item_id)
            self.menu_event_queue.append(event)
    
    def get_event(self) -> Optional[Any]:
        """Get next event, including menu events."""
        # Check menu events first
        if self.menu_event_queue:
            return self.menu_event_queue.pop(0)
        
        # Fall back to other event types
        return super().get_event()
```

### 4. TFM Integration

#### Main Application Integration (`src/tfm_main.py`)

```python
class TFM:
    """Main TFM application class."""
    
    def __init__(self, stdscr, backend_name='auto'):
        # ... existing initialization ...
        
        # Initialize menu manager for desktop mode
        if self.is_desktop_mode():
            self.menu_manager = MenuManager(self)
            self._setup_menu_bar()
    
    def is_desktop_mode(self) -> bool:
        """Check if running in desktop mode."""
        return hasattr(self.renderer, 'set_menu_bar')
    
    def _setup_menu_bar(self) -> None:
        """Initialize menu bar for desktop mode."""
        menu_structure = self.menu_manager.get_menu_structure()
        self.renderer.set_menu_bar(menu_structure)
    
    def _update_menu_states(self) -> None:
        """Update menu item states based on current application state."""
        if not self.is_desktop_mode():
            return
        
        states = self.menu_manager.update_menu_states()
        for item_id, enabled in states.items():
            self.renderer.update_menu_item_state(item_id, enabled)
    
    def handle_event(self, event) -> bool:
        """Handle input events including menu events."""
        if isinstance(event, MenuEvent):
            return self._handle_menu_event(event)
        
        # ... existing event handling ...
    
    def _handle_menu_event(self, event: MenuEvent) -> bool:
        """Handle menu selection events.
        
        Args:
            event: MenuEvent with item_id
        
        Returns:
            True if event was handled
        """
        item_id = event.item_id
        
        # File menu
        if item_id == 'file.new_file':
            return self._action_create_file()
        elif item_id == 'file.new_folder':
            return self._action_create_directory()
        elif item_id == 'file.open':
            return self._action_open_file()
        elif item_id == 'file.delete':
            return self._action_delete()
        elif item_id == 'file.rename':
            return self._action_rename()
        elif item_id == 'file.quit':
            return self._action_quit()
        
        # Edit menu
        elif item_id == 'edit.copy':
            return self._action_copy()
        elif item_id == 'edit.cut':
            return self._action_cut()
        elif item_id == 'edit.paste':
            return self._action_paste()
        elif item_id == 'edit.select_all':
            return self._action_select_all()
        
        # View menu
        elif item_id == 'view.show_hidden':
            return self._action_toggle_hidden()
        elif item_id.startswith('view.sort_by_'):
            sort_type = item_id.replace('view.sort_by_', '')
            return self._action_sort_by(sort_type)
        elif item_id == 'view.refresh':
            return self._action_refresh()
        
        # Go menu
        elif item_id == 'go.parent':
            return self._action_go_parent()
        elif item_id == 'go.home':
            return self._action_go_home()
        elif item_id == 'go.favorites':
            return self._action_show_favorites()
        elif item_id == 'go.recent':
            return self._action_show_recent()
        
        return False
    
    def main_loop(self):
        """Main event loop."""
        while self.running:
            # Update menu states before processing events
            if self.is_desktop_mode():
                self._update_menu_states()
            
            event = self.renderer.get_event()
            if event:
                self.handle_event(event)
            
            # ... existing loop logic ...
```

## Data Models

### Menu Structure Format

```python
{
    'menus': [
        {
            'id': 'file',
            'label': 'File',
            'items': [
                {
                    'id': 'file.new_file',
                    'label': 'New File',
                    'shortcut': 'Cmd+N',
                    'enabled': True
                },
                {
                    'id': 'file.new_folder',
                    'label': 'New Folder',
                    'shortcut': 'Cmd+Shift+N',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': 'file.open',
                    'label': 'Open',
                    'shortcut': 'Cmd+O',
                    'enabled': True
                },
                {
                    'id': 'file.delete',
                    'label': 'Delete',
                    'shortcut': 'Cmd+D',
                    'enabled': False  # Disabled when no selection
                },
                {
                    'id': 'file.rename',
                    'label': 'Rename',
                    'shortcut': 'Cmd+R',
                    'enabled': False  # Disabled when no selection
                },
                {'separator': True},
                {
                    'id': 'file.quit',
                    'label': 'Quit',
                    'shortcut': 'Cmd+Q',
                    'enabled': True
                }
            ]
        },
        {
            'id': 'edit',
            'label': 'Edit',
            'items': [
                {
                    'id': 'edit.copy',
                    'label': 'Copy',
                    'shortcut': 'Cmd+C',
                    'enabled': False  # Disabled when no selection
                },
                {
                    'id': 'edit.cut',
                    'label': 'Cut',
                    'shortcut': 'Cmd+X',
                    'enabled': False  # Disabled when no selection
                },
                {
                    'id': 'edit.paste',
                    'label': 'Paste',
                    'shortcut': 'Cmd+V',
                    'enabled': False  # Disabled when clipboard empty
                },
                {'separator': True},
                {
                    'id': 'edit.select_all',
                    'label': 'Select All',
                    'shortcut': 'Cmd+A',
                    'enabled': True
                }
            ]
        },
        {
            'id': 'view',
            'label': 'View',
            'items': [
                {
                    'id': 'view.show_hidden',
                    'label': 'Show Hidden Files',
                    'shortcut': 'Cmd+H',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': 'view.sort_by_name',
                    'label': 'Sort by Name',
                    'enabled': True
                },
                {
                    'id': 'view.sort_by_size',
                    'label': 'Sort by Size',
                    'enabled': True
                },
                {
                    'id': 'view.sort_by_date',
                    'label': 'Sort by Date',
                    'enabled': True
                },
                {
                    'id': 'view.sort_by_extension',
                    'label': 'Sort by Extension',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': 'view.refresh',
                    'label': 'Refresh',
                    'shortcut': 'Cmd+R',
                    'enabled': True
                }
            ]
        },
        {
            'id': 'go',
            'label': 'Go',
            'items': [
                {
                    'id': 'go.parent',
                    'label': 'Parent Directory',
                    'shortcut': 'Cmd+Up',
                    'enabled': True  # Disabled at root
                },
                {
                    'id': 'go.home',
                    'label': 'Home',
                    'shortcut': 'Cmd+Shift+H',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': 'go.favorites',
                    'label': 'Favorites',
                    'shortcut': 'Cmd+F',
                    'enabled': True
                },
                {
                    'id': 'go.recent',
                    'label': 'Recent Locations',
                    'shortcut': 'Cmd+Shift+R',
                    'enabled': True
                }
            ]
        }
    ]
}
```

### MenuEvent Class

```python
class MenuEvent:
    """Event generated when a menu item is selected.
    
    Attributes:
        item_id: Unique identifier for the selected menu item
        type: Event type identifier ('menu')
    """
    
    def __init__(self, item_id: str):
        self.item_id = item_id
        self.type = 'menu'
    
    def __repr__(self):
        return f"MenuEvent(item_id='{self.item_id}')"
    
    def __eq__(self, other):
        if not isinstance(other, MenuEvent):
            return False
        return self.item_id == other.item_id
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Menu structure consistency

*For any* menu structure passed to `set_menu_bar()`, all menu item IDs should be unique across the entire menu hierarchy
**Validates: Requirements 2.3**

### Property 2: Menu event delivery

*For any* menu item selection, when a user selects an enabled menu item, a MenuEvent with the correct item_id should be returned by `get_event()`
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 3: Disabled menu items prevent events

*For any* menu item that is disabled, selecting that menu item should not generate a MenuEvent
**Validates: Requirements 1.4**

### Property 4: Menu state updates are reflected

*For any* menu item, when `update_menu_item_state()` is called with enabled=False, subsequent attempts to select that item should not generate events
**Validates: Requirements 9.3**

### Property 5: Menu structure completeness

*For any* standard menu (File, Edit, View, Go), the menu structure should contain all required menu items as specified in the requirements
**Validates: Requirements 4.2, 5.2, 6.2, 7.2**

### Property 6: Keyboard shortcuts are unique

*For any* menu structure, keyboard shortcuts should be unique within each platform (no two menu items should have the same shortcut)
**Validates: Requirements 10.3**

### Property 7: Menu action execution

*For any* MenuEvent received, when the event is handled, the corresponding action should be executed exactly once
**Validates: Requirements 1.3**

### Property 8: Parent directory menu state

*For any* current directory, when the directory is the root directory, the "Parent Directory" menu item should be disabled
**Validates: Requirements 7.4**

### Property 9: Selection-dependent menu states

*For any* application state with no files selected, menu items that require selection (Copy, Cut, Delete, Rename) should be disabled
**Validates: Requirements 4.4, 5.4**

### Property 10: Clipboard-dependent menu state

*For any* application state with an empty clipboard, the Paste menu item should be disabled
**Validates: Requirements 5.5**

## Error Handling

### Menu Structure Validation

- **Invalid menu structure**: If menu structure is malformed, log error and skip menu bar creation
- **Duplicate menu item IDs**: Log warning and use first occurrence
- **Missing required fields**: Log error and skip invalid menu items
- **Invalid shortcut format**: Log warning and create menu item without shortcut

### Menu Event Handling

- **Unknown menu item ID**: Log warning and ignore event
- **Action execution failure**: Log error, show user notification, continue operation
- **Menu state update failure**: Log warning, continue with stale state

### Platform-Specific Errors

- **macOS menu creation failure**: Log error, fall back to keyboard-only operation
- **Menu item state update failure**: Log warning, continue with current state
- **Event queue overflow**: Log warning, drop oldest events

### Error Recovery

- Menu bar creation failure should not prevent TFM from running
- Individual menu item failures should not affect other menu items
- Event handling errors should not crash the application

## Testing Strategy

### Unit Tests

Unit tests will verify specific examples and edge cases:

1. **Menu structure creation**: Test that MenuManager creates valid menu structure
2. **Menu item ID uniqueness**: Test that all menu item IDs are unique
3. **Menu state calculation**: Test enable/disable logic for various application states
4. **MenuEvent creation**: Test that MenuEvent objects are created correctly
5. **Event handler dispatch**: Test that menu item IDs map to correct action handlers
6. **Shortcut parsing**: Test conversion of shortcut strings to platform format
7. **Edge cases**:
   - Empty selection
   - Root directory navigation
   - Empty clipboard
   - Invalid menu item IDs

### Property-Based Tests

Property-based tests will verify universal properties across all inputs using the Hypothesis library for Python. Each test will run a minimum of 100 iterations.

1. **Property 1 test**: Generate random menu structures and verify all IDs are unique
2. **Property 2 test**: Generate random menu selections and verify MenuEvents are created
3. **Property 3 test**: Generate random disabled menu items and verify no events are generated
4. **Property 4 test**: Generate random state updates and verify menu items reflect changes
5. **Property 5 test**: Verify all required menu items exist in standard menus
6. **Property 6 test**: Generate random menu structures and verify shortcut uniqueness
7. **Property 7 test**: Generate random MenuEvents and verify actions execute once
8. **Property 8 test**: Generate random directory paths and verify parent menu state
9. **Property 9 test**: Generate random selection states and verify menu item states
10. **Property 10 test**: Generate random clipboard states and verify paste menu state

### Integration Tests

1. **End-to-end menu flow**: Create menu, select item, verify action executes
2. **Menu state updates**: Change application state, verify menu items update
3. **Keyboard shortcuts**: Press shortcut, verify action executes without opening menu
4. **Platform-specific rendering**: Verify native menus appear on macOS
5. **Cross-platform consistency**: Verify menu behavior is consistent across platforms

### Manual Testing

1. Visual verification of menu appearance on macOS
2. Keyboard shortcut functionality
3. Menu item enable/disable visual feedback
4. Menu responsiveness and performance
5. Integration with existing TFM workflows

## Platform-Specific Considerations

### macOS (CoreGraphics Backend)

- Use AppKit NSMenu and NSMenuItem APIs
- Keyboard shortcuts use Command (⌘) key by default
- Menu bar appears in system menu bar at top of screen
- Support for standard macOS menu conventions (File, Edit, View, Go, Window, Help)
- Native look and feel with system theme integration

### Windows (Future Implementation)

- Use Win32 API for menu creation
- Keyboard shortcuts use Ctrl key by default
- Menu bar appears at top of application window
- Support for standard Windows menu conventions
- Native look and feel with Windows theme integration

### Platform Abstraction

- TTK abstract interface hides platform differences
- TFM application code is platform-agnostic
- Menu structure format is platform-independent
- Keyboard shortcut notation is converted by backend

## Performance Considerations

### Menu Creation

- Menu structure is created once during initialization
- Menu items are cached for efficient state updates
- No menu reconstruction on state changes

### State Updates

- State updates are batched when possible
- Only changed menu items are updated
- State calculation is optimized for common cases

### Event Handling

- Menu events are queued for processing
- Event queue has reasonable size limit
- Events are processed in order received

## Future Enhancements

### Phase 2 Features

1. **Submenu support**: Allow nested submenus for complex menu hierarchies
2. **Dynamic menu items**: Add/remove menu items at runtime
3. **Menu item icons**: Support icons next to menu item labels
4. **Checkmark menu items**: Toggle items with checkmarks (e.g., "Show Hidden Files")
5. **Recent items**: Dynamic "Recent Files" and "Recent Folders" submenus
6. **Context menus**: Right-click context menus for files and folders
7. **Menu bar hiding**: Option to hide menu bar for full-screen mode
8. **Custom menus**: Allow users to define custom menu items in configuration

### Windows Support

1. Implement Windows backend with Win32 menu APIs
2. Test menu functionality on Windows
3. Adjust keyboard shortcuts for Windows conventions
4. Ensure visual consistency with Windows theme

### Accessibility

1. Screen reader support for menu items
2. High contrast mode support
3. Keyboard navigation improvements
4. Voice control integration
