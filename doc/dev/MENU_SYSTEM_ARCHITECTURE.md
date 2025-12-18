# Menu System Architecture

## Overview

This document provides comprehensive technical documentation for TFM's menu system architecture. It covers the design, implementation, and integration of the native menu bar feature in Desktop mode, including how to add new menu items, handle menu events, and extend the system.

The menu system is designed with clear separation of concerns: TFM defines menu structure and behavior at the application layer, while TTK backends handle platform-specific rendering. This architecture ensures maintainability, testability, and cross-platform compatibility.

## Target Audience

This documentation is intended for:
- **TFM developers** who need to add new menu items or modify menu behavior
- **TTK backend developers** who need to implement menu support for new platforms
- **Contributors** who want to understand the menu system architecture

## Architecture Overview

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TFM Application Layer                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MenuManager (src/tfm_menu_manager.py)                 │ │
│  │  - Defines menu structure and hierarchy                │ │
│  │  - Manages menu item IDs and constants                 │ │
│  │  - Calculates menu item enable/disable states          │ │
│  │  - Provides platform-independent shortcuts             │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  TFM Main (src/tfm_main.py)                            │ │
│  │  - Initializes MenuManager in desktop mode             │ │
│  │  - Calls set_menu_bar() during initialization          │ │
│  │  - Updates menu states in main loop                    │ │
│  │  - Handles MenuEvent objects                           │ │
│  │  - Dispatches to action handlers                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↕ Menu Structure / MenuEvent
┌─────────────────────────────────────────────────────────────┐
│                      TTK Library Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Renderer Abstract Interface (ttk/renderer.py)         │ │
│  │  - set_menu_bar(menu_structure) abstract method        │ │
│  │  - update_menu_item_state(item_id, enabled) method     │ │
│  │  - get_event() returns MenuEvent objects               │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MenuEvent Class (ttk/input_event.py)                  │ │
│  │  - item_id: str - menu item identifier                 │ │
│  │  - Inherits from Event base class                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Platform-Specific Backend                             │ │
│  │  ┌──────────────────┐  ┌──────────────────┐           │ │
│  │  │ CoreGraphics     │  │ Windows Backend  │           │ │
│  │  │ (macOS)          │  │ (Future)         │           │ │
│  │  │ - NSMenu API     │  │ - Win32 API      │           │ │
│  │  │ - NSMenuItem     │  │ - Menu handles   │           │ │
│  │  │ - Shortcut parse │  │ - Accelerators   │           │ │
│  │  └──────────────────┘  └──────────────────┘           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```


### Data Flow Sequence

1. **Initialization Phase**:
   - TFM detects desktop mode during startup
   - Creates MenuManager instance with reference to FileManager
   - MenuManager builds menu structure with platform-appropriate shortcuts
   - TFM calls `renderer.set_menu_bar(menu_structure)`
   - Backend creates native menu bar (NSMenu on macOS)

2. **Runtime State Updates**:
   - Main loop calls `menu_manager.update_menu_states()`
   - MenuManager calculates enabled/disabled state for each item
   - TFM calls `renderer.update_menu_item_state(item_id, enabled)` for each change
   - Backend updates native menu item state

3. **User Interaction**:
   - User selects menu item (via click or keyboard shortcut)
   - OS generates menu selection event
   - Backend creates MenuEvent with item_id
   - MenuEvent added to event queue

4. **Event Processing**:
   - TFM calls `renderer.get_event()`
   - Backend returns MenuEvent from queue
   - TFM's `_handle_menu_event()` dispatches to action handler
   - Action handler executes corresponding operation

## Core Components

### 1. MenuManager (Application Layer)

**Location**: `src/tfm_menu_manager.py`

**Purpose**: Manages menu structure, menu item IDs, and state calculation logic.

**Key Responsibilities**:
- Define menu hierarchy (File, Edit, View, Go menus)
- Provide menu item ID constants for type-safe references
- Build menu structure with platform-appropriate shortcuts
- Calculate enable/disable state based on application context
- Provide menu structure to TTK backend

**Public Interface**:

```python
class MenuManager:
    # Menu item ID constants
    FILE_NEW_FILE = 'file.new_file'
    FILE_NEW_FOLDER = 'file.new_folder'
    # ... more constants
    
    def __init__(self, file_manager):
        """Initialize with reference to FileManager."""
        
    def get_menu_structure(self) -> dict:
        """Get complete menu structure."""
        
    def update_menu_states(self) -> dict:
        """Calculate current enable/disable state for all items.
        
        Returns:
            dict: Map of item_id -> enabled (bool)
        """
        
    def should_enable_item(self, item_id: str) -> bool:
        """Check if specific item should be enabled."""
```

**Menu Structure Format**:

```python
{
    'menus': [
        {
            'id': 'file',              # Menu identifier
            'label': 'File',           # Display label
            'items': [
                {
                    'id': 'file.new_file',      # Unique item ID
                    'label': 'New File',        # Display label
                    'shortcut': 'Cmd+N',        # Keyboard shortcut
                    'enabled': True             # Initial state
                },
                {'separator': True},            # Menu separator
                # ... more items
            ]
        },
        # ... more menus
    ]
}
```


### 2. Renderer Abstract Interface (TTK Layer)

**Location**: `ttk/renderer.py`

**Purpose**: Define platform-independent interface for menu operations.

**Key Methods**:

```python
@abstractmethod
def set_menu_bar(self, menu_structure: dict) -> None:
    """Set the menu bar structure.
    
    Args:
        menu_structure: Dictionary with 'menus' list containing
                       menu definitions with items, labels, shortcuts
    """
    
@abstractmethod
def update_menu_item_state(self, item_id: str, enabled: bool) -> None:
    """Update menu item enabled/disabled state.
    
    Args:
        item_id: Unique menu item identifier
        enabled: True to enable, False to disable
    """
    
@abstractmethod
def get_event(self, timeout_ms: int = -1) -> Optional[Event]:
    """Get next event including MenuEvent objects.
    
    Returns:
        Event object (KeyEvent, MouseEvent, SystemEvent, MenuEvent)
        or None if timeout expires
    """
```

**Design Principles**:
- Platform-agnostic interface
- No platform-specific types in signatures
- Simple dictionary-based menu structure
- Consistent with other TTK event handling

### 3. MenuEvent Class (TTK Layer)

**Location**: `ttk/input_event.py`

**Purpose**: Represent menu selection events in the unified event system.

**Implementation**:

```python
@dataclass
class MenuEvent(Event):
    """Represents a menu selection event.
    
    Generated when user selects a menu item via click or keyboard shortcut.
    """
    item_id: str  # Unique identifier for selected menu item
    
    def __repr__(self):
        return f"MenuEvent(item_id='{self.item_id}')"
```

**Key Characteristics**:
- Inherits from Event base class
- Contains only item_id (no platform-specific data)
- Immutable dataclass for safety
- Works identically across all backends

### 4. CoreGraphics Backend (Platform Layer)

**Location**: `ttk/backends/coregraphics_backend.py`

**Purpose**: Implement menu support using macOS NSMenu APIs.

**Key Components**:

```python
class CoreGraphicsBackend(Renderer):
    def __init__(self):
        self.menu_bar = None              # NSMenu instance
        self.menu_items = {}              # item_id -> NSMenuItem
        self.menu_event_queue = []        # MenuEvent queue
    
    def set_menu_bar(self, menu_structure: dict):
        """Create native macOS menu bar."""
        # Create NSMenu
        # Add menu items with shortcuts
        # Register callbacks
        
    def _parse_shortcut(self, shortcut: str):
        """Convert 'Cmd+N' to NSMenuItem format."""
        # Parse modifier keys
        # Extract key equivalent
        # Return (key, modifier_mask)
        
    def _menu_item_selected_(self, sender):
        """Callback when menu item selected."""
        # Get item_id from NSMenuItem
        # Create MenuEvent
        # Add to event queue
        
    def update_menu_item_state(self, item_id: str, enabled: bool):
        """Update NSMenuItem enabled state."""
        # Look up NSMenuItem by item_id
        # Call setEnabled_()
        
    def get_event(self, timeout_ms: int = -1):
        """Return MenuEvent from queue or other events."""
        # Check menu event queue first
        # Fall back to keyboard/mouse events
```


### 5. TFM Main Integration (Application Layer)

**Location**: `src/tfm_main.py`

**Purpose**: Integrate menu system into TFM's main event loop.

**Key Methods**:

```python
class TFM:
    def __init__(self, stdscr, backend_name='auto'):
        # Initialize menu manager for desktop mode
        if self.is_desktop_mode():
            self.menu_manager = MenuManager(self)
            self._setup_menu_bar()
    
    def is_desktop_mode(self) -> bool:
        """Check if running in desktop mode."""
        return hasattr(self.renderer, 'set_menu_bar')
    
    def _setup_menu_bar(self):
        """Initialize menu bar."""
        menu_structure = self.menu_manager.get_menu_structure()
        self.renderer.set_menu_bar(menu_structure)
    
    def _update_menu_states(self):
        """Update menu item states based on application state."""
        states = self.menu_manager.update_menu_states()
        for item_id, enabled in states.items():
            self.renderer.update_menu_item_state(item_id, enabled)
    
    def main_loop(self):
        """Main event loop."""
        while self.running:
            # Update menu states
            if self.is_desktop_mode():
                self._update_menu_states()
            
            # Get and handle events
            event = self.renderer.get_event()
            if isinstance(event, MenuEvent):
                self._handle_menu_event(event)
            # ... handle other events
    
    def _handle_menu_event(self, event: MenuEvent) -> bool:
        """Dispatch menu events to action handlers."""
        item_id = event.item_id
        
        # File menu
        if item_id == 'file.new_file':
            return self._action_create_file()
        elif item_id == 'file.quit':
            return self._action_quit()
        # ... handle other menu items
```

## Adding New Menu Items

### Step-by-Step Guide

#### 1. Define Menu Item ID Constant

Add a new constant to MenuManager:

```python
# In src/tfm_menu_manager.py
class MenuManager:
    # Existing constants...
    
    # Add new constant
    FILE_PROPERTIES = 'file.properties'
```

**Best Practices**:
- Use descriptive, hierarchical names: `menu.action`
- Follow existing naming conventions
- Use UPPER_CASE for constants
- Group related items together

#### 2. Add Menu Item to Structure

Add the item to the appropriate menu builder method:

```python
def _build_file_menu(self, modifier):
    return {
        'id': 'file',
        'label': 'File',
        'items': [
            # Existing items...
            {
                'id': self.FILE_PROPERTIES,
                'label': 'Properties',
                'shortcut': f'{modifier}+I',  # Cmd+I or Ctrl+I
                'enabled': False  # Disabled when no selection
            },
            # More items...
        ]
    }
```

**Configuration Options**:
- `id`: Use the constant defined in step 1
- `label`: User-visible text (use title case)
- `shortcut`: Optional keyboard shortcut (see shortcut format below)
- `enabled`: Initial state (True/False)

**Shortcut Format**:
- Use `{modifier}+Key` for platform-independent shortcuts
- `modifier` is 'Cmd' on macOS, 'Ctrl' on Windows
- Multiple modifiers: `{modifier}+Shift+Key`
- Examples: `Cmd+N`, `Cmd+Shift+S`, `Ctrl+Alt+D`


#### 3. Add State Calculation Logic

Update `update_menu_states()` to calculate the enabled state:

```python
def update_menu_states(self):
    states = {}
    
    # Get application context
    current_pane = self.file_manager.get_current_pane()
    has_selection = len(current_pane['selected_files']) > 0
    
    # Existing state calculations...
    
    # Add new item state
    states[self.FILE_PROPERTIES] = has_selection
    
    return states
```

**State Calculation Patterns**:

```python
# Always enabled
states[item_id] = True

# Requires file selection
states[item_id] = has_selection

# Requires single file selection
states[item_id] = len(selected_files) == 1

# Requires clipboard content
states[item_id] = self._has_clipboard_content()

# Requires not at root
states[item_id] = not self._is_at_root(current_dir)

# Complex condition
states[item_id] = has_selection and not is_readonly
```

#### 4. Add Event Handler

Add handler in TFM's `_handle_menu_event()` method:

```python
def _handle_menu_event(self, event: MenuEvent) -> bool:
    item_id = event.item_id
    
    # Existing handlers...
    
    # Add new handler
    elif item_id == 'file.properties':
        return self._action_show_properties()
    
    return False
```

#### 5. Implement Action Handler

Create the action handler method:

```python
def _action_show_properties(self) -> bool:
    """Show properties dialog for selected file."""
    try:
        # Get selected file
        current_pane = self.get_current_pane()
        if not current_pane['selected_files']:
            return False
        
        selected_file = current_pane['selected_files'][0]
        file_path = current_pane['path'] / selected_file
        
        # Show properties dialog
        self._show_file_properties_dialog(file_path)
        
        return True
    except Exception as e:
        self.log_manager.add_message(f"Error showing properties: {e}", "ERROR")
        return False
```

**Action Handler Best Practices**:
- Return True if action was handled successfully
- Return False if action failed or was cancelled
- Use try/except for error handling
- Log errors with LogManager
- Validate preconditions (selection, permissions, etc.)
- Update UI state after action completes

#### 6. Test the New Menu Item

Create tests to verify the implementation:

```python
# In test/test_menu_manager.py
def test_properties_menu_item_exists(self):
    """Test that properties menu item is defined."""
    menus = self.menu_manager.menu_structure['menus']
    file_menu = next(m for m in menus if m['id'] == 'file')
    
    properties_item = next(
        (item for item in file_menu['items'] 
         if item.get('id') == 'file.properties'),
        None
    )
    
    assert properties_item is not None
    assert properties_item['label'] == 'Properties'

def test_properties_disabled_without_selection(self):
    """Test that properties is disabled when no files selected."""
    # Set up: no selection
    self.file_manager.get_current_pane()['selected_files'] = []
    
    # Get states
    states = self.menu_manager.update_menu_states()
    
    # Verify
    assert states['file.properties'] == False

def test_properties_enabled_with_selection(self):
    """Test that properties is enabled when file selected."""
    # Set up: one file selected
    self.file_manager.get_current_pane()['selected_files'] = ['file.txt']
    
    # Get states
    states = self.menu_manager.update_menu_states()
    
    # Verify
    assert states['file.properties'] == True
```


### Complete Example: Adding "Duplicate File" Menu Item

Here's a complete example showing all steps:

```python
# Step 1: Add constant to MenuManager
class MenuManager:
    FILE_DUPLICATE = 'file.duplicate'

# Step 2: Add to menu structure
def _build_file_menu(self, modifier):
    return {
        'id': 'file',
        'label': 'File',
        'items': [
            # ... existing items
            {
                'id': self.FILE_DUPLICATE,
                'label': 'Duplicate',
                'shortcut': f'{modifier}+D',
                'enabled': False
            },
            # ... more items
        ]
    }

# Step 3: Add state calculation
def update_menu_states(self):
    states = {}
    # ... existing calculations
    
    # Duplicate requires exactly one file selected
    states[self.FILE_DUPLICATE] = len(selected_files) == 1
    
    return states

# Step 4: Add event handler in TFM
def _handle_menu_event(self, event: MenuEvent) -> bool:
    # ... existing handlers
    elif item_id == 'file.duplicate':
        return self._action_duplicate_file()

# Step 5: Implement action handler
def _action_duplicate_file(self) -> bool:
    """Duplicate the selected file."""
    try:
        current_pane = self.get_current_pane()
        if len(current_pane['selected_files']) != 1:
            return False
        
        source_file = current_pane['selected_files'][0]
        source_path = current_pane['path'] / source_file
        
        # Generate duplicate name
        base_name = source_path.stem
        extension = source_path.suffix
        counter = 1
        
        while True:
            duplicate_name = f"{base_name} copy {counter}{extension}"
            duplicate_path = current_pane['path'] / duplicate_name
            if not duplicate_path.exists():
                break
            counter += 1
        
        # Copy file
        import shutil
        shutil.copy2(source_path, duplicate_path)
        
        # Refresh view
        self.refresh_current_pane()
        
        self.log_manager.add_message(
            f"Duplicated {source_file} to {duplicate_name}", 
            "INFO"
        )
        return True
        
    except Exception as e:
        self.log_manager.add_message(
            f"Error duplicating file: {e}", 
            "ERROR"
        )
        return False
```

## MenuEvent Handling

### Event Flow

1. **Event Generation**:
   - User selects menu item (click or shortcut)
   - OS calls backend's menu callback
   - Backend creates MenuEvent with item_id
   - MenuEvent added to event queue

2. **Event Retrieval**:
   - TFM calls `renderer.get_event()`
   - Backend checks menu event queue first
   - Returns MenuEvent if available
   - Falls back to keyboard/mouse events

3. **Event Dispatch**:
   - TFM checks event type with `isinstance(event, MenuEvent)`
   - Calls `_handle_menu_event(event)`
   - Dispatcher maps item_id to action handler
   - Action handler executes operation

### Event Handler Pattern

```python
def _handle_menu_event(self, event: MenuEvent) -> bool:
    """Handle menu selection events.
    
    Args:
        event: MenuEvent with item_id
    
    Returns:
        bool: True if event was handled successfully
    """
    item_id = event.item_id
    
    # Use if/elif chain for dispatch
    if item_id == 'file.new_file':
        return self._action_create_file()
    elif item_id == 'file.delete':
        return self._action_delete()
    # ... more handlers
    else:
        # Unknown menu item
        self.log_manager.add_message(
            f"Unknown menu item: {item_id}", 
            "WARNING"
        )
        return False
```

**Alternative: Dictionary Dispatch**

```python
def __init__(self):
    # Build dispatch table
    self.menu_handlers = {
        'file.new_file': self._action_create_file,
        'file.delete': self._action_delete,
        'edit.copy': self._action_copy,
        # ... more mappings
    }

def _handle_menu_event(self, event: MenuEvent) -> bool:
    """Handle menu event using dispatch table."""
    handler = self.menu_handlers.get(event.item_id)
    
    if handler:
        try:
            return handler()
        except Exception as e:
            self.log_manager.add_message(
                f"Error handling menu item {event.item_id}: {e}",
                "ERROR"
            )
            return False
    else:
        self.log_manager.add_message(
            f"Unknown menu item: {event.item_id}",
            "WARNING"
        )
        return False
```


### Error Handling in Event Handlers

```python
def _action_example(self) -> bool:
    """Example action with comprehensive error handling."""
    try:
        # Validate preconditions
        if not self._validate_preconditions():
            return False
        
        # Perform operation
        result = self._perform_operation()
        
        # Update UI
        self.refresh_current_pane()
        
        # Log success
        self.log_manager.add_message("Operation completed", "INFO")
        
        return True
        
    except PermissionError as e:
        self.log_manager.add_message(
            f"Permission denied: {e}",
            "ERROR"
        )
        return False
        
    except FileNotFoundError as e:
        self.log_manager.add_message(
            f"File not found: {e}",
            "ERROR"
        )
        return False
        
    except Exception as e:
        self.log_manager.add_message(
            f"Unexpected error: {e}",
            "ERROR"
        )
        return False
```

## Platform-Specific Implementation

### macOS (CoreGraphics Backend)

#### Shortcut Parsing

The CoreGraphics backend converts platform-independent shortcuts to macOS format:

```python
def _parse_shortcut(self, shortcut: str):
    """Parse keyboard shortcut into NSMenuItem format.
    
    Args:
        shortcut: String like 'Cmd+N', 'Cmd+Shift+S'
    
    Returns:
        Tuple of (key_equivalent: str, modifier_mask: int or None)
    """
    if not shortcut:
        return ('', None)
    
    # Split into parts
    parts = shortcut.split('+')
    key = parts[-1]
    modifiers = parts[:-1]
    
    # Build modifier mask
    modifier_mask = 0
    for mod in modifiers:
        mod_lower = mod.lower()
        if mod_lower in ('cmd', 'command'):
            modifier_mask |= Cocoa.NSEventModifierFlagCommand
        elif mod_lower == 'shift':
            modifier_mask |= Cocoa.NSEventModifierFlagShift
        elif mod_lower in ('ctrl', 'control'):
            modifier_mask |= Cocoa.NSEventModifierFlagControl
        elif mod_lower in ('alt', 'option'):
            modifier_mask |= Cocoa.NSEventModifierFlagOption
    
    # Convert key to lowercase unless Shift is present
    if 'shift' not in [m.lower() for m in modifiers]:
        key = key.lower()
    
    return (key, modifier_mask if modifier_mask > 0 else None)
```

**Key Equivalent Rules**:
- Single character: lowercase ('n', 'c', 'v')
- With Shift: uppercase ('N', 'S')
- Special keys: Use NSEvent constants (future enhancement)

**Modifier Flags**:
- `NSEventModifierFlagCommand` - Command (⌘) key
- `NSEventModifierFlagShift` - Shift key
- `NSEventModifierFlagControl` - Control key
- `NSEventModifierFlagOption` - Option (Alt) key

#### Menu Item Creation

```python
def _create_menu_item(self, item_def: dict):
    """Create NSMenuItem from definition."""
    # Parse shortcut
    key_equivalent, modifier_mask = self._parse_shortcut(
        item_def.get('shortcut', '')
    )
    
    # Create menu item
    item = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        item_def['label'],
        objc.selector(self._menu_item_selected_, signature=b'v@:@'),
        key_equivalent
    )
    
    # Set modifier mask
    if modifier_mask is not None:
        item.setKeyEquivalentModifierMask_(modifier_mask)
    
    # Set properties
    item.setEnabled_(item_def.get('enabled', True))
    item.setRepresentedObject_(item_def['id'])
    item.setTarget_(self)
    
    return item
```

#### Menu Selection Callback

```python
def _menu_item_selected_(self, sender):
    """Callback when menu item is selected.
    
    This is called by macOS when user selects a menu item
    via click or keyboard shortcut.
    
    Args:
        sender: NSMenuItem that was selected
    """
    item_id = sender.representedObject()
    
    if item_id:
        from ttk.input_event import MenuEvent
        event = MenuEvent(item_id=item_id)
        self.menu_event_queue.append(event)
```


### Windows (Future Implementation)

#### Planned Architecture

```python
class WindowsBackend(Renderer):
    def set_menu_bar(self, menu_structure: dict):
        """Create Windows menu bar using Win32 API."""
        # Create menu handle with CreateMenu()
        # Add menu items with AppendMenu()
        # Register accelerators with CreateAcceleratorTable()
        # Attach menu to window with SetMenu()
        
    def _parse_shortcut(self, shortcut: str):
        """Convert shortcut to Win32 accelerator format."""
        # Parse modifiers (Ctrl, Shift, Alt)
        # Convert key to virtual key code
        # Build ACCEL structure
        # Return accelerator data
        
    def _handle_menu_command(self, command_id: int):
        """Handle WM_COMMAND message for menu selection."""
        # Look up item_id from command_id
        # Create MenuEvent
        # Add to event queue
```

**Key Differences from macOS**:
- Uses menu handles instead of objects
- Accelerators registered separately from menu items
- Command IDs instead of object references
- WM_COMMAND messages instead of callbacks

## Testing Strategy

### Unit Tests

Test menu structure and state calculation:

```python
# test/test_menu_manager.py

def test_menu_structure_has_all_menus(self):
    """Test that all required menus are present."""
    menus = self.menu_manager.menu_structure['menus']
    menu_ids = [m['id'] for m in menus]
    
    assert 'file' in menu_ids
    assert 'edit' in menu_ids
    assert 'view' in menu_ids
    assert 'go' in menu_ids

def test_menu_item_ids_are_unique(self):
    """Test that all menu item IDs are unique."""
    item_ids = []
    menus = self.menu_manager.menu_structure['menus']
    
    for menu in menus:
        for item in menu['items']:
            if 'id' in item:
                item_ids.append(item['id'])
    
    # Check for duplicates
    assert len(item_ids) == len(set(item_ids))

def test_shortcuts_use_correct_modifier(self):
    """Test that shortcuts use platform-appropriate modifier."""
    import platform
    expected_modifier = 'Cmd' if platform.system() == 'Darwin' else 'Ctrl'
    
    menus = self.menu_manager.menu_structure['menus']
    for menu in menus:
        for item in menu['items']:
            if 'shortcut' in item and item['shortcut']:
                assert item['shortcut'].startswith(expected_modifier)

def test_state_calculation_with_selection(self):
    """Test menu states when files are selected."""
    # Set up: files selected
    self.file_manager.get_current_pane()['selected_files'] = ['file.txt']
    
    states = self.menu_manager.update_menu_states()
    
    # Selection-dependent items should be enabled
    assert states['file.delete'] == True
    assert states['edit.copy'] == True
    assert states['edit.cut'] == True

def test_state_calculation_without_selection(self):
    """Test menu states when no files selected."""
    # Set up: no selection
    self.file_manager.get_current_pane()['selected_files'] = []
    
    states = self.menu_manager.update_menu_states()
    
    # Selection-dependent items should be disabled
    assert states['file.delete'] == False
    assert states['edit.copy'] == False
    assert states['edit.cut'] == False
```

### Integration Tests

Test end-to-end menu functionality:

```python
# test/test_menu_integration.py

def test_menu_event_generation(self):
    """Test that menu selection generates MenuEvent."""
    # Set up menu bar
    backend.set_menu_bar(menu_structure)
    
    # Simulate menu selection
    # (Platform-specific event injection)
    
    # Get event
    event = backend.get_event(timeout_ms=100)
    
    # Verify
    assert isinstance(event, MenuEvent)
    assert event.item_id == 'file.new_file'

def test_menu_state_updates(self):
    """Test that menu states update correctly."""
    # Set up
    backend.set_menu_bar(menu_structure)
    
    # Initially disabled
    backend.update_menu_item_state('file.delete', False)
    
    # Enable item
    backend.update_menu_item_state('file.delete', True)
    
    # Verify item is enabled
    # (Platform-specific verification)

def test_keyboard_shortcut_execution(self):
    """Test that keyboard shortcuts work."""
    # Set up menu bar
    backend.set_menu_bar(menu_structure)
    
    # Simulate Cmd+N shortcut
    # (Platform-specific event injection)
    
    # Get event
    event = backend.get_event(timeout_ms=100)
    
    # Verify MenuEvent generated
    assert isinstance(event, MenuEvent)
    assert event.item_id == 'file.new_file'
```


### Demo Scripts

Interactive testing and demonstration:

```python
# demo/demo_menu_bar.py

"""
Demonstrate menu bar functionality in desktop mode.

This demo shows:
- Menu bar creation and display
- Menu item selection
- Menu state updates
- Keyboard shortcuts
"""

def main():
    # Initialize backend
    backend = CoreGraphicsBackend(
        window_title="Menu Bar Demo",
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Create menu structure
    menu_structure = {
        'menus': [
            {
                'id': 'demo',
                'label': 'Demo',
                'items': [
                    {
                        'id': 'demo.action1',
                        'label': 'Action 1',
                        'shortcut': 'Cmd+1',
                        'enabled': True
                    },
                    {
                        'id': 'demo.action2',
                        'label': 'Action 2',
                        'shortcut': 'Cmd+2',
                        'enabled': False
                    }
                ]
            }
        ]
    }
    
    # Set menu bar
    backend.set_menu_bar(menu_structure)
    
    # Main loop
    while True:
        # Draw instructions
        backend.clear()
        backend.draw_text(0, 0, "Menu Bar Demo")
        backend.draw_text(2, 0, "Try the Demo menu or press Cmd+1")
        backend.draw_text(3, 0, "Press 'e' to enable/disable Action 2")
        backend.draw_text(4, 0, "Press 'q' to quit")
        backend.refresh()
        
        # Get event
        event = backend.get_event()
        
        if isinstance(event, MenuEvent):
            # Handle menu event
            backend.draw_text(6, 0, f"Menu item selected: {event.item_id}")
            backend.refresh()
            
        elif isinstance(event, KeyEvent):
            if event.char == 'q':
                break
            elif event.char == 'e':
                # Toggle Action 2 state
                enabled = not action2_enabled
                backend.update_menu_item_state('demo.action2', enabled)
                action2_enabled = enabled
    
    backend.shutdown()
```

## Performance Considerations

### Menu Creation

- **One-time cost**: Menu structure created once during initialization
- **Caching**: Menu items cached in dictionary for fast state updates
- **No reconstruction**: State updates don't rebuild menu structure

### State Updates

- **Batched updates**: Calculate all states once per main loop iteration
- **Selective updates**: Only update changed items (future optimization)
- **Efficient lookup**: O(1) lookup of menu items by ID

### Event Processing

- **Queue-based**: Menu events queued for processing
- **Priority**: Menu events checked before keyboard/mouse events
- **No polling**: OS generates events, no active polling needed

## Debugging

### Enable Menu Logging

```python
def _menu_item_selected_(self, sender):
    """Callback with logging."""
    item_id = sender.representedObject()
    
    # Log selection
    print(f"Menu item selected: {item_id}")
    
    # Check trigger method
    current_event = Cocoa.NSApp.currentEvent()
    if current_event.type() == Cocoa.NSEventTypeKeyDown:
        print(f"  Triggered by keyboard shortcut")
    else:
        print(f"  Triggered by menu click")
    
    # Create event
    event = MenuEvent(item_id=item_id)
    self.menu_event_queue.append(event)
```

### Verify Menu Structure

```python
def debug_print_menu_structure(menu_structure):
    """Print menu structure for debugging."""
    for menu in menu_structure['menus']:
        print(f"Menu: {menu['label']} (id: {menu['id']})")
        for item in menu['items']:
            if 'separator' in item:
                print("  ---")
            else:
                shortcut = item.get('shortcut', '')
                enabled = item.get('enabled', True)
                print(f"  {item['label']:<20} {shortcut:<15} "
                      f"{'[enabled]' if enabled else '[disabled]'}")
                print(f"    id: {item['id']}")
```

### Verify Shortcut Registration

```python
def verify_shortcuts(self):
    """Verify all shortcuts are registered correctly."""
    for item_id, menu_item in self.menu_items.items():
        key_equiv = menu_item.keyEquivalent()
        mod_mask = menu_item.keyEquivalentModifierMask()
        
        if key_equiv:
            # Decode modifier mask
            modifiers = []
            if mod_mask & Cocoa.NSEventModifierFlagCommand:
                modifiers.append('Cmd')
            if mod_mask & Cocoa.NSEventModifierFlagShift:
                modifiers.append('Shift')
            if mod_mask & Cocoa.NSEventModifierFlagControl:
                modifiers.append('Ctrl')
            if mod_mask & Cocoa.NSEventModifierFlagOption:
                modifiers.append('Alt')
            
            shortcut = '+'.join(modifiers + [key_equiv])
            print(f"{item_id}: {shortcut}")
```


## Common Patterns and Best Practices

### Menu Item Naming

**Good Examples**:
```python
FILE_NEW_FILE = 'file.new_file'
EDIT_COPY = 'edit.copy'
VIEW_SORT_BY_NAME = 'view.sort_by_name'
GO_PARENT = 'go.parent'
```

**Bad Examples**:
```python
NEW_FILE = 'new_file'  # Missing menu prefix
FILE_NEW = 'file.new'  # Ambiguous (new what?)
COPY_FILES = 'copy'    # Missing menu prefix
```

**Guidelines**:
- Use hierarchical naming: `menu.action`
- Be specific: `file.new_file` not `file.new`
- Use underscores for multi-word actions
- Keep consistent with existing patterns

### State Calculation

**Efficient Pattern**:
```python
def update_menu_states(self):
    """Calculate states once, use multiple times."""
    # Get context once
    current_pane = self.file_manager.get_current_pane()
    selected_files = current_pane['selected_files']
    has_selection = len(selected_files) > 0
    single_selection = len(selected_files) == 1
    
    # Use cached values
    states = {}
    states[self.FILE_DELETE] = has_selection
    states[self.FILE_RENAME] = single_selection
    states[self.EDIT_COPY] = has_selection
    
    return states
```

**Inefficient Pattern**:
```python
def update_menu_states(self):
    """Recalculate context for each item."""
    states = {}
    
    # Repeated calls - inefficient
    states[self.FILE_DELETE] = len(
        self.file_manager.get_current_pane()['selected_files']
    ) > 0
    states[self.FILE_RENAME] = len(
        self.file_manager.get_current_pane()['selected_files']
    ) == 1
    
    return states
```

### Error Handling

**Comprehensive Pattern**:
```python
def _action_example(self) -> bool:
    """Action with proper error handling."""
    try:
        # Validate
        if not self._validate():
            return False
        
        # Execute
        self._perform_operation()
        
        # Update UI
        self.refresh_current_pane()
        
        # Log success
        self.log_manager.add_message("Success", "INFO")
        return True
        
    except PermissionError as e:
        self.log_manager.add_message(f"Permission denied: {e}", "ERROR")
        return False
    except Exception as e:
        self.log_manager.add_message(f"Error: {e}", "ERROR")
        return False
```

**Minimal Pattern** (for simple operations):
```python
def _action_simple(self) -> bool:
    """Simple action with basic error handling."""
    try:
        self._perform_simple_operation()
        return True
    except Exception as e:
        self.log_manager.add_message(f"Error: {e}", "ERROR")
        return False
```

### Keyboard Shortcuts

**Good Shortcuts**:
- Use standard conventions: Cmd+C for Copy, Cmd+V for Paste
- Avoid conflicts with system shortcuts
- Use mnemonic keys when possible: Cmd+N for New
- Group related shortcuts: Cmd+1, Cmd+2, Cmd+3

**Shortcut Assignment Guidelines**:
- File operations: Cmd+N, Cmd+O, Cmd+S, Cmd+W
- Edit operations: Cmd+C, Cmd+X, Cmd+V, Cmd+A
- View operations: Cmd+H (hide), Cmd+R (refresh)
- Navigation: Cmd+Up, Cmd+Down, Cmd+Left, Cmd+Right
- With Shift: Cmd+Shift+N (New Folder), Cmd+Shift+S (Save As)

## Troubleshooting

### Menu Bar Not Appearing

**Symptoms**: TFM launches but no menu bar visible

**Possible Causes**:
1. Not running in desktop mode
2. Backend doesn't support menus
3. Menu structure not set
4. macOS-specific issue

**Solutions**:
```python
# Check if desktop mode is active
if hasattr(self.renderer, 'set_menu_bar'):
    print("Desktop mode active")
else:
    print("Terminal mode - no menu bar")

# Verify menu structure was set
try:
    self.renderer.set_menu_bar(menu_structure)
    print("Menu bar set successfully")
except Exception as e:
    print(f"Error setting menu bar: {e}")
```

### Menu Items Not Updating

**Symptoms**: Menu items don't enable/disable based on state

**Possible Causes**:
1. State update not called in main loop
2. State calculation logic incorrect
3. Backend not updating menu items

**Solutions**:
```python
# Add logging to state updates
def _update_menu_states(self):
    states = self.menu_manager.update_menu_states()
    print(f"Updating {len(states)} menu items")
    
    for item_id, enabled in states.items():
        print(f"  {item_id}: {enabled}")
        self.renderer.update_menu_item_state(item_id, enabled)

# Verify state calculation
states = self.menu_manager.update_menu_states()
print(f"file.delete enabled: {states['file.delete']}")
print(f"Selected files: {len(current_pane['selected_files'])}")
```

### MenuEvents Not Generated

**Symptoms**: Selecting menu items doesn't trigger actions

**Possible Causes**:
1. Menu callback not registered
2. Event queue not checked
3. Event handler not implemented

**Solutions**:
```python
# Add logging to menu callback
def _menu_item_selected_(self, sender):
    item_id = sender.representedObject()
    print(f"Menu callback: {item_id}")
    
    event = MenuEvent(item_id=item_id)
    self.menu_event_queue.append(event)
    print(f"Event queue size: {len(self.menu_event_queue)}")

# Verify event handling
event = self.renderer.get_event()
print(f"Event type: {type(event)}")
if isinstance(event, MenuEvent):
    print(f"Menu event: {event.item_id}")
```


## Future Enhancements

### Planned Features

#### 1. Submenu Support

Add nested submenus for complex menu hierarchies:

```python
{
    'id': 'view.sort',
    'label': 'Sort By',
    'items': [
        {
            'id': 'view.sort.name',
            'label': 'Name',
            'enabled': True
        },
        {
            'id': 'view.sort.size',
            'label': 'Size',
            'enabled': True
        }
    ]
}
```

#### 2. Checkmark Menu Items

Toggle items with visual checkmarks:

```python
{
    'id': 'view.show_hidden',
    'label': 'Show Hidden Files',
    'type': 'checkbox',
    'checked': False,
    'enabled': True
}
```

#### 3. Dynamic Menu Items

Add/remove menu items at runtime:

```python
def add_recent_file(self, file_path: str):
    """Add file to Recent Files submenu."""
    item = {
        'id': f'file.recent.{file_path}',
        'label': file_path.name,
        'enabled': True
    }
    self.menu_manager.add_menu_item('file.recent', item)
    self.renderer.update_menu_bar()
```

#### 4. Menu Icons

Add icons to menu items:

```python
{
    'id': 'file.new_file',
    'label': 'New File',
    'icon': 'document.png',
    'enabled': True
}
```

#### 5. Context Menus

Right-click context menus for files:

```python
def show_context_menu(self, file_path: Path, position: Tuple[int, int]):
    """Show context menu for file."""
    context_menu = {
        'items': [
            {'id': 'context.open', 'label': 'Open'},
            {'id': 'context.rename', 'label': 'Rename'},
            {'separator': True},
            {'id': 'context.delete', 'label': 'Delete'}
        ]
    }
    self.renderer.show_context_menu(context_menu, position)
```

### Implementation Roadmap

**Phase 1** (Current):
- ✅ Basic menu bar with File, Edit, View, Go menus
- ✅ Menu item enable/disable
- ✅ Keyboard shortcuts
- ✅ MenuEvent handling
- ✅ macOS support

**Phase 2** (Next):
- ⬜ Windows backend implementation
- ⬜ Submenu support
- ⬜ Checkmark menu items
- ⬜ Menu item icons

**Phase 3** (Future):
- ⬜ Context menus
- ⬜ Dynamic menu items
- ⬜ Custom user menus
- ⬜ Menu bar hiding/showing

## Code Locations

### Source Files

- **MenuManager**: `src/tfm_menu_manager.py`
- **TFM Main**: `src/tfm_main.py`
- **Renderer Interface**: `ttk/renderer.py`
- **MenuEvent**: `ttk/input_event.py`
- **CoreGraphics Backend**: `ttk/backends/coregraphics_backend.py`

### Test Files

- **MenuManager Tests**: `test/test_menu_manager.py`
- **Integration Tests**: `test/test_menu_integration.py`

### Demo Files

- **Menu Bar Demo**: `demo/demo_menu_bar.py`
- **Keyboard Shortcuts Demo**: `demo/demo_menu_keyboard_shortcuts.py`

### Documentation

- **End-User Documentation**: `doc/MENU_BAR_FEATURE.md`
- **Keyboard Shortcuts**: `doc/MENU_BAR_KEYBOARD_SHORTCUTS_FEATURE.md`
- **Developer Documentation**: `doc/dev/MENU_SYSTEM_ARCHITECTURE.md` (this file)
- **Keyboard Shortcuts Implementation**: `doc/dev/KEYBOARD_SHORTCUTS_IMPLEMENTATION.md`

## References

### Apple Documentation

- [NSMenu Class Reference](https://developer.apple.com/documentation/appkit/nsmenu)
- [NSMenuItem Class Reference](https://developer.apple.com/documentation/appkit/nsmenuitem)
- [NSEvent Modifier Flags](https://developer.apple.com/documentation/appkit/nsevent/modifierflags)
- [Menu Programming Guide](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/MenuList/MenuList.html)

### Microsoft Documentation

- [Menu Resources](https://docs.microsoft.com/en-us/windows/win32/menurc/menus)
- [CreateMenu Function](https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createmenu)
- [AppendMenu Function](https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-appendmenua)
- [Keyboard Accelerators](https://docs.microsoft.com/en-us/windows/win32/menurc/keyboard-accelerators)

### Related TFM Documentation

- [Menu Bar Feature](../MENU_BAR_FEATURE.md) - End-user documentation
- [Keyboard Shortcuts Feature](../MENU_BAR_KEYBOARD_SHORTCUTS_FEATURE.md) - Shortcut reference
- [Desktop Mode Guide](../DESKTOP_MODE_GUIDE.md) - Desktop mode overview
- [CoreGraphics Backend Implementation](COREGRAPHICS_BACKEND_IMPLEMENTATION.md) - Backend details

## Contributing

### Adding New Features

When adding new menu-related features:

1. **Update MenuManager** if adding new menu items
2. **Update Renderer interface** if adding new capabilities
3. **Implement in backends** (CoreGraphics, future Windows)
4. **Add tests** for new functionality
5. **Update documentation** (both end-user and developer)
6. **Create demo** if feature is significant

### Code Review Checklist

- [ ] Menu item IDs follow naming conventions
- [ ] State calculation logic is efficient
- [ ] Error handling is comprehensive
- [ ] Tests cover new functionality
- [ ] Documentation is updated
- [ ] Demo script works correctly
- [ ] Platform-specific code is isolated in backends
- [ ] Keyboard shortcuts don't conflict with existing ones

## Support

For questions or issues with the menu system:

1. Check this documentation first
2. Review existing menu implementations
3. Check demo scripts for examples
4. Review test files for usage patterns
5. Consult with TFM maintainers

## Changelog

### Version 1.0 (Current)
- Initial menu bar implementation
- File, Edit, View, Go menus
- Menu item enable/disable
- Keyboard shortcuts
- macOS CoreGraphics backend support
- MenuEvent handling
- Comprehensive documentation

