# Design Document

## Overview

This design enhances TFM's key bindings configuration system to support all KeyCode names from TTK and modifier key combinations. The enhancement introduces a new KeyBindings class that centralizes key binding management and eliminates the need for the legacy SPECIAL_KEY_MAP dictionary.

The key insight is that KeyCode is now a StrEnum in TTK, so we can use KeyCode string values directly in configuration without needing a separate mapping table. The design also introduces a flexible key expression format that supports modifier keys (Shift, Control, Alt, Command) in a case-insensitive, order-independent manner.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     TFM Application                          │
│                  (tfm_main.py, etc.)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ Uses KeyBindings
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  KeyBindings Class                           │
│  - Manages KEY_BINDINGS from Config                         │
│  - find_action_for_event(event, has_selection) → action     │
│  - get_keys_for_action(action) → (keys, selection_req)      │
│  - Parses key expressions with modifiers                    │
│  - Matches KeyEvent against bindings                        │
└────────────────────────┬────────────────────────────────────┘
                         │ Reads from
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Config (tfm_config.py)                      │
│  KEY_BINDINGS = {                                           │
│    'quit': ['q', 'Q'],                                      │
│    'help': ['?'],                                           │
│    'move_up': ['UP', 'k'],                                  │
│    'move_down': ['DOWN', 'j'],                              │
│    'page_up': ['PAGE_UP', 'Shift-UP'],                     │
│    'page_down': ['PAGE_DOWN', 'Shift-DOWN'],               │
│    'delete_files': {                                        │
│      'keys': ['DELETE', 'Command-Backspace'],              │
│      'selection': 'required'                                │
│    }                                                        │
│  }                                                          │
└────────────────────────┬────────────────────────────────────┘
                         │ Uses
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  TTK KeyCode (StrEnum)                       │
│  - UP, DOWN, LEFT, RIGHT                                    │
│  - ENTER, ESCAPE, TAB, BACKSPACE, DELETE                    │
│  - PAGE_UP, PAGE_DOWN, HOME, END                            │
│  - F1-F12, INSERT                                           │
│  - KEY_A-KEY_Z, KEY_0-KEY_9, SPACE                         │
│  - KEY_MINUS, KEY_EQUAL, etc.                              │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Direct KeyCode Usage**: Use KeyCode string values directly without intermediate mapping
2. **Flexible Key Expressions**: Support both simple characters and complex modifier combinations
3. **Case Insensitivity**: All key expressions are case-insensitive for user convenience
4. **Order Independence**: Modifier order doesn't matter (Command-Shift-X = Shift-Command-X)
5. **Backward Compatibility**: Existing single-character bindings continue to work
6. **Centralized Logic**: All key binding logic encapsulated in KeyBindings class

## Components and Interfaces

### 1. KeyBindings Class

**Location**: `src/tfm_config.py`

**Design**:
```python
class KeyBindings:
    """
    Manages key bindings and provides lookup functionality.
    
    This class encapsulates all key binding logic, including:
    - Parsing key expressions with modifiers
    - Matching KeyEvents against configured bindings
    - Looking up actions from key events
    - Looking up key expressions from actions
    """
    
    def __init__(self, key_bindings_config: dict):
        """
        Initialize KeyBindings with configuration.
        
        Args:
            key_bindings_config: KEY_BINDINGS dictionary from Config
        """
        self.logger = getLogger("KeyBindings")
        self._bindings = key_bindings_config
        
        # Build reverse lookup: (key_expr, modifiers) -> [(action, selection_req), ...]
        self._key_to_actions = self._build_key_lookup()
    
    def _build_key_lookup(self) -> dict:
        """
        Build a reverse lookup table from key expressions to actions.
        
        Returns:
            Dictionary mapping (key_expr, modifier_flags) to list of (action, selection_req) tuples
        """
        lookup = {}
        
        for action, binding in self._bindings.items():
            # Extract keys and selection requirement
            if isinstance(binding, list):
                keys = binding
                selection_req = 'any'
            elif isinstance(binding, dict) and 'keys' in binding:
                keys = binding['keys']
                selection_req = binding.get('selection', 'any')
            else:
                continue
            
            # Process each key expression
            for key_expr in keys:
                # Parse key expression to get main key and modifiers
                main_key, modifiers = self._parse_key_expression(key_expr)
                
                # Add to lookup table
                lookup_key = (main_key, modifiers)
                if lookup_key not in lookup:
                    lookup[lookup_key] = []
                lookup[lookup_key].append((action, selection_req))
        
        return lookup
    
    def _parse_key_expression(self, key_expr: str) -> tuple[str, int]:
        """
        Parse a key expression into main key and modifier flags.
        
        Args:
            key_expr: Key expression string (e.g., "Shift-Down", "Command-Shift-X", "q")
        
        Returns:
            Tuple of (main_key, modifier_flags)
            - main_key: The main key as uppercase string
            - modifier_flags: Bitwise OR of ModifierKey values
        
        Examples:
            "q" -> ("Q", 0)
            "Shift-Down" -> ("DOWN", ModifierKey.SHIFT)
            "Command-Shift-X" -> ("X", ModifierKey.COMMAND | ModifierKey.SHIFT)
        """
        # Single character - return as-is with no modifiers
        if len(key_expr) == 1:
            return (key_expr.upper(), 0)
        
        # Multi-character - parse as key expression
        parts = key_expr.split('-')
        
        # Last part is the main key
        main_key = parts[-1].upper()
        
        # Earlier parts are modifiers
        modifiers = 0
        for part in parts[:-1]:
            modifier_name = part.upper()
            if modifier_name == 'SHIFT':
                modifiers |= ModifierKey.SHIFT
            elif modifier_name == 'CONTROL' or modifier_name == 'CTRL':
                modifiers |= ModifierKey.CONTROL
            elif modifier_name == 'ALT' or modifier_name == 'OPTION':
                modifiers |= ModifierKey.ALT
            elif modifier_name == 'COMMAND' or modifier_name == 'CMD':
                modifiers |= ModifierKey.COMMAND
            else:
                self.logger.warning(f"Unknown modifier in key expression: {part}")
        
        return (main_key, modifiers)
    
    def _keycode_from_string(self, key_str: str) -> Optional[int]:
        """
        Convert a KeyCode name string to its integer value.
        
        Args:
            key_str: KeyCode name (e.g., "DOWN", "ENTER", "A")
        
        Returns:
            KeyCode integer value, or None if not found
        """
        try:
            # KeyCode is a StrEnum, so we can access by name
            return getattr(KeyCode, key_str, None)
        except AttributeError:
            return None
    
    def _match_key_event(self, event: KeyEvent, main_key: str, modifiers: int) -> bool:
        """
        Check if a KeyEvent matches a key expression.
        
        Args:
            event: KeyEvent from TTK
            main_key: Main key string (uppercase)
            modifiers: Expected modifier flags
        
        Returns:
            True if event matches the key expression
        """
        # Check modifiers first
        if event.modifiers != modifiers:
            return False
        
        # Single character - match against event.char
        if len(main_key) == 1:
            return event.char and event.char.upper() == main_key
        
        # KeyCode name - match against event.key_code
        expected_keycode = self._keycode_from_string(main_key)
        if expected_keycode is None:
            return False
        
        return event.key_code == expected_keycode
    
    def find_action_for_event(self, event: KeyEvent, has_selection: bool) -> Optional[str]:
        """
        Find the action bound to a KeyEvent, respecting selection requirements.
        
        Args:
            event: KeyEvent from TTK
            has_selection: Whether files are currently selected
        
        Returns:
            Action name if found, None otherwise
        """
        if not event:
            return None
        
        # Try to match against all key bindings
        for (main_key, modifiers), actions in self._key_to_actions.items():
            if self._match_key_event(event, main_key, modifiers):
                # Found a matching key - check selection requirements
                for action, selection_req in actions:
                    if self._check_selection_requirement(selection_req, has_selection):
                        return action
        
        return None
    
    def _check_selection_requirement(self, requirement: str, has_selection: bool) -> bool:
        """
        Check if selection requirement is satisfied.
        
        Args:
            requirement: 'required', 'none', or 'any'
            has_selection: Whether files are currently selected
        
        Returns:
            True if requirement is satisfied
        """
        if requirement == 'required':
            return has_selection
        elif requirement == 'none':
            return not has_selection
        else:  # 'any'
            return True
    
    def get_keys_for_action(self, action: str) -> tuple[list[str], str]:
        """
        Get the key expressions and selection requirement for an action.
        
        Args:
            action: Action name
        
        Returns:
            Tuple of (key_expressions, selection_requirement)
            - key_expressions: List of key expression strings
            - selection_requirement: 'required', 'none', or 'any'
        """
        if action not in self._bindings:
            return ([], 'any')
        
        binding = self._bindings[action]
        
        # Extract keys and selection requirement
        if isinstance(binding, list):
            return (binding, 'any')
        elif isinstance(binding, dict) and 'keys' in binding:
            keys = binding['keys']
            selection_req = binding.get('selection', 'any')
            return (keys, selection_req)
        
        return ([], 'any')
    
    def format_key_for_display(self, key_expr: str) -> str:
        """
        Format a key expression for display in UI.
        
        Args:
            key_expr: Key expression string
        
        Returns:
            Formatted string suitable for display
        
        Examples:
            "q" -> "q"
            "Shift-Down" -> "Shift-Down"
            "Command-Shift-X" -> "Cmd-Shift-X"
        """
        # Single character - return as-is
        if len(key_expr) == 1:
            return key_expr
        
        # Multi-character - format nicely
        parts = key_expr.split('-')
        
        # Format modifiers
        formatted_parts = []
        for part in parts[:-1]:
            modifier = part.capitalize()
            # Abbreviate Command to Cmd
            if modifier == 'Command':
                modifier = 'Cmd'
            formatted_parts.append(modifier)
        
        # Add main key
        formatted_parts.append(parts[-1].upper())
        
        return '-'.join(formatted_parts)
```

### 2. Config Integration

**Location**: `src/tfm_config.py`

**Changes**:

1. **Remove SPECIAL_KEY_MAP and SPECIAL_KEY_NAMES**:
```python
# DELETE these dictionaries - no longer needed
# SPECIAL_KEY_MAP = { ... }
# SPECIAL_KEY_NAMES = { ... }
```

2. **Update DefaultConfig.KEY_BINDINGS**:
```python
class DefaultConfig:
    # ... other settings ...
    
    KEY_BINDINGS = {
        'quit': ['q', 'Q'],
        'help': ['?'],
        'toggle_hidden': ['.'],
        
        # Use KeyCode names directly
        'move_up': ['UP', 'k'],
        'move_down': ['DOWN', 'j'],
        'move_left': ['LEFT', 'h'],
        'move_right': ['RIGHT', 'l'],
        
        # Use modifier combinations
        'page_up': ['PAGE_UP', 'Shift-UP'],
        'page_down': ['PAGE_DOWN', 'Shift-DOWN'],
        'jump_to_top': ['HOME', 'Command-UP'],
        'jump_to_bottom': ['END', 'Command-DOWN'],
        
        # Extended format with selection requirements
        'delete_files': {
            'keys': ['DELETE', 'Command-Backspace', 'k', 'K'],
            'selection': 'required'
        },
        
        # ... rest of bindings ...
    }
```

3. **Add KeyBindings instance to ConfigManager**:
```python
class ConfigManager:
    def __init__(self):
        self.logger = getLogger("Config")
        self.config_dir = Path.home() / '.tfm'
        self.config_file = self.config_dir / 'config.py'
        self.config = None
        self._key_bindings = None  # NEW: Cached KeyBindings instance
    
    def get_key_bindings(self) -> KeyBindings:
        """Get the KeyBindings instance for current configuration."""
        config = self.get_config()
        
        # Rebuild if config changed or not yet built
        if self._key_bindings is None:
            key_bindings_config = getattr(config, 'KEY_BINDINGS', DefaultConfig.KEY_BINDINGS)
            self._key_bindings = KeyBindings(key_bindings_config)
        
        return self._key_bindings
    
    def reload_config(self):
        """Reload configuration from file."""
        self.config = None
        self._key_bindings = None  # Clear cached KeyBindings
        return self.load_config()
```

4. **Update public API functions**:
```python
def find_action_for_event(event: KeyEvent, has_selection: bool = False) -> Optional[str]:
    """
    Find the action bound to a KeyEvent.
    
    Args:
        event: KeyEvent from TTK
        has_selection: Whether files are currently selected
    
    Returns:
        Action name if found, None otherwise
    """
    key_bindings = config_manager.get_key_bindings()
    return key_bindings.find_action_for_event(event, has_selection)


def get_keys_for_action(action: str) -> tuple[list[str], str]:
    """
    Get the key expressions and selection requirement for an action.
    
    Args:
        action: Action name
    
    Returns:
        Tuple of (key_expressions, selection_requirement)
    """
    key_bindings = config_manager.get_key_bindings()
    return key_bindings.get_keys_for_action(action)


def format_key_for_display(key_expr: str) -> str:
    """
    Format a key expression for display in UI.
    
    Args:
        key_expr: Key expression string
    
    Returns:
        Formatted string suitable for display
    """
    key_bindings = config_manager.get_key_bindings()
    return key_bindings.format_key_for_display(key_expr)


# DEPRECATED: Keep for backward compatibility, but mark as deprecated
def is_key_bound_to(key_char, action):
    """DEPRECATED: Use find_action_for_event instead."""
    # ... keep existing implementation for now ...
```

### 3. Application Integration

**Location**: Various TFM files (tfm_main.py, tfm_pane_manager.py, etc.)

**Changes**:

Replace calls to old API with new API:

```python
# OLD:
from tfm_config import is_input_event_bound_to_with_selection
if is_input_event_bound_to_with_selection(event, 'quit', has_selection):
    # handle quit

# NEW:
from tfm_config import find_action_for_event
action = find_action_for_event(event, has_selection)
if action == 'quit':
    # handle quit
```

## Data Models

### KeyEvent (from TTK)

The KeyEvent class from TTK provides the input data:

```python
@dataclass
class KeyEvent(Event):
    """Represents a keyboard command event."""
    key_code: int          # KeyCode enum value
    modifiers: int         # Bitwise OR of ModifierKey flags
    char: Optional[str]    # Character representation (if printable)
```

### ModifierKey (from TTK)

The ModifierKey flags from TTK:

```python
class ModifierKey(IntFlag):
    """Modifier key flags."""
    NONE = 0
    SHIFT = 1
    CONTROL = 2
    ALT = 4
    COMMAND = 8
```

### Key Binding Configuration Format

Two formats are supported:

**Simple Format** (list of key expressions):
```python
'action_name': ['key1', 'key2', 'key3']
```

**Extended Format** (dict with keys and selection requirement):
```python
'action_name': {
    'keys': ['key1', 'key2'],
    'selection': 'required'  # or 'none' or 'any'
}
```

### Key Expression Format

Key expressions follow these patterns:

1. **Single Character**: `'q'`, `'a'`, `'?'`
   - Matches against KeyEvent.char
   - Case-sensitive as typed

2. **KeyCode Name**: `'ENTER'`, `'DOWN'`, `'PAGE_UP'`
   - Matches against KeyEvent.key_code
   - Case-insensitive

3. **Modified Key**: `'Shift-Down'`, `'Command-Q'`
   - Matches against KeyEvent.key_code and KeyEvent.modifiers
   - Case-insensitive
   - Order-independent for modifiers

4. **Multiple Modifiers**: `'Command-Shift-X'`, `'Control-Alt-Delete'`
   - Matches against KeyEvent.key_code and KeyEvent.modifiers
   - Case-insensitive
   - Order-independent for modifiers

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: KeyCode Name Recognition

*For any* KeyCode name string (regardless of case), the system should recognize it as a valid key binding and correctly resolve it to the corresponding KeyCode value.

**Validates: Requirements 1.1, 1.2, 1.3**

**Rationale**: This ensures that all KeyCode names from TTK can be used in configuration with case-insensitive matching, providing a complete and user-friendly key binding system.

### Property 2: Modifier Key Support

*For any* combination of modifier keys (Shift, Control, Alt, Command) with any main key, the system should correctly parse the key expression regardless of modifier order or case, and match it against KeyEvents with the corresponding modifier flags.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

**Rationale**: This ensures comprehensive modifier support with flexible, user-friendly syntax that doesn't require users to remember specific ordering or casing conventions.

### Property 3: Single Character Backward Compatibility

*For any* single-character key binding, the system should match it against KeyEvent.char, maintaining backward compatibility with existing character-based bindings.

**Validates: Requirements 1.5, 2.6, 7.1**

**Rationale**: This ensures existing configurations continue to work without modification, providing a smooth migration path for users.

### Property 4: Key Expression Parsing

*For any* key expression with length greater than 1, the system should parse it as a KeyCode name or modified key expression (with hyphen separators), correctly extracting the main key and modifier flags.

**Validates: Requirements 2.7, 3.1, 3.2, 3.4**

**Rationale**: This ensures consistent parsing logic that distinguishes between simple character keys and complex key expressions.

### Property 5: Configuration Format Support

*For any* action with key bindings in either simple format (list) or extended format (dict with 'keys' and 'selection'), the system should correctly extract the keys and selection requirement.

**Validates: Requirements 4.4, 7.2, 7.3**

**Rationale**: This ensures both configuration formats are supported, maintaining backward compatibility while enabling new features.

### Property 6: Selection Requirement Enforcement

*For any* action with a selection requirement ('required', 'none', 'any') and any selection state (has_selection true/false), the system should only match the action when the selection requirement is satisfied.

**Validates: Requirements 4.5, 5.6**

**Rationale**: This ensures actions are only triggered when appropriate, preventing errors like trying to delete files when none are selected.

### Property 7: Multiple Keys Per Action

*For any* action with multiple key bindings, all of those keys should successfully trigger the action when pressed (subject to selection requirements).

**Validates: Requirements 4.6**

**Rationale**: This ensures users can have multiple ways to trigger the same action, improving usability and accommodating different preferences.

### Property 8: KeyEvent to Action Lookup

*For any* KeyEvent and selection state, the system should return the correct action name if a matching binding exists, or None if no match is found.

**Validates: Requirements 5.1, 5.3, 5.4, 5.5**

**Rationale**: This is the core functionality - correctly mapping user input to actions. It must work reliably across all key types and modifier combinations.

### Property 9: Action to Keys Reverse Lookup

*For any* action name, the system should return all key expressions bound to that action and the selection requirement, or an empty list if the action doesn't exist.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

**Rationale**: This enables displaying key bindings in help dialogs and UI, which is essential for user discoverability of features.

### Property 10: Display Formatting

*For any* key expression, the system should format it in a consistent, readable way suitable for display to users (e.g., abbreviating "Command" to "Cmd", capitalizing appropriately).

**Validates: Requirements 6.5**

**Rationale**: This ensures key bindings are displayed consistently and readably in the UI, improving user experience.

### Property 11: Legacy Key Name Compatibility

*For any* key name that existed in SPECIAL_KEY_MAP (e.g., "HOME", "END", "PPAGE"), the system should still recognize it as a valid KeyCode name.

**Validates: Requirements 7.5**

**Rationale**: This ensures configurations using old key names continue to work, even though SPECIAL_KEY_MAP is removed from the codebase.

## Error Handling

### Invalid Key Expressions

**Strategy**: When a key expression cannot be parsed:

1. **Log a warning** with the invalid expression
2. **Skip the binding** and continue processing other bindings
3. **Don't crash** the application

**Implementation**:
```python
def _parse_key_expression(self, key_expr: str) -> tuple[str, int]:
    try:
        # Parse logic...
        return (main_key, modifiers)
    except Exception as e:
        self.logger.warning(f"Invalid key expression: {key_expr}: {e}")
        return (key_expr.upper(), 0)  # Fallback to treating as simple key
```

### Unknown Modifier Names

**Strategy**: When an unknown modifier is encountered:

1. **Log a warning** with the unknown modifier name
2. **Ignore the unknown modifier** and continue parsing
3. **Process the rest of the expression** normally

**Implementation**:
```python
for part in parts[:-1]:
    modifier_name = part.upper()
    if modifier_name == 'SHIFT':
        modifiers |= ModifierKey.SHIFT
    # ... other modifiers ...
    else:
        self.logger.warning(f"Unknown modifier in key expression: {part}")
        # Continue processing - don't fail
```

### Unknown KeyCode Names

**Strategy**: When a KeyCode name cannot be resolved:

1. **Log a warning** with the unknown name
2. **Return None** from _keycode_from_string
3. **Skip the binding** in matching logic

**Implementation**:
```python
def _keycode_from_string(self, key_str: str) -> Optional[int]:
    try:
        keycode = getattr(KeyCode, key_str, None)
        if keycode is None:
            self.logger.warning(f"Unknown KeyCode name: {key_str}")
        return keycode
    except AttributeError:
        self.logger.warning(f"Invalid KeyCode name: {key_str}")
        return None
```

### Missing Configuration

**Strategy**: When KEY_BINDINGS is missing or invalid:

1. **Fall back to DefaultConfig.KEY_BINDINGS**
2. **Log an info message** about using defaults
3. **Continue normal operation**

**Implementation**:
```python
def get_key_bindings(self) -> KeyBindings:
    config = self.get_config()
    
    # Get key bindings config with fallback
    if hasattr(config, 'KEY_BINDINGS') and config.KEY_BINDINGS:
        key_bindings_config = config.KEY_BINDINGS
    else:
        self.logger.info("Using default key bindings")
        key_bindings_config = DefaultConfig.KEY_BINDINGS
    
    self._key_bindings = KeyBindings(key_bindings_config)
    return self._key_bindings
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests:

- **Unit tests**: Verify specific examples, edge cases, and structural requirements
- **Property tests**: Verify universal properties across all keys and configurations

### Unit Testing Focus

1. **KeyBindings Class Structure**:
   - Verify class initialization with valid configuration
   - Verify methods exist with correct signatures
   - Verify error handling for invalid input

2. **Specific Key Expressions**:
   - Test common single-character keys ('q', 'a', '?')
   - Test common KeyCode names ('ENTER', 'ESCAPE', 'UP', 'DOWN')
   - Test common modifier combinations ('Shift-Down', 'Command-Q')
   - Test edge cases (empty string, invalid format)

3. **Configuration Formats**:
   - Test simple format (list of keys)
   - Test extended format (dict with keys and selection)
   - Test mixed configurations

4. **Selection Requirements**:
   - Test 'required' with has_selection=True/False
   - Test 'none' with has_selection=True/False
   - Test 'any' with has_selection=True/False

5. **Backward Compatibility**:
   - Test all existing default key bindings still work
   - Test SPECIAL_KEY_MAP names still work
   - Test single-character bindings still work

### Property-Based Testing Focus

**Testing Framework**: Use Python's `hypothesis` library for property-based testing.

**Test Configuration**: Each property test must run minimum 100 iterations.

**Property Tests**:

1. **KeyCode Name Recognition** (Property 1):
   - Generate random KeyCode names with random casing
   - Verify all are recognized and resolve correctly
   - Tag: **Feature: key-bindings-enhancement, Property 1: KeyCode Name Recognition**

2. **Modifier Key Support** (Property 2):
   - Generate random combinations of modifiers with random keys
   - Generate random permutations of modifier order
   - Generate random casing for modifiers
   - Verify all parse correctly and match appropriately
   - Tag: **Feature: key-bindings-enhancement, Property 2: Modifier Key Support**

3. **Single Character Backward Compatibility** (Property 3):
   - Generate random single-character keys
   - Verify they match against KeyEvent.char
   - Tag: **Feature: key-bindings-enhancement, Property 3: Single Character Backward Compatibility**

4. **Key Expression Parsing** (Property 4):
   - Generate random multi-character key expressions
   - Verify they parse as KeyCode names or modified expressions
   - Tag: **Feature: key-bindings-enhancement, Property 4: Key Expression Parsing**

5. **Configuration Format Support** (Property 5):
   - Generate random configurations in both formats
   - Verify both are handled correctly
   - Tag: **Feature: key-bindings-enhancement, Property 5: Configuration Format Support**

6. **Selection Requirement Enforcement** (Property 6):
   - Generate random selection requirements and states
   - Verify requirements are enforced correctly
   - Tag: **Feature: key-bindings-enhancement, Property 6: Selection Requirement Enforcement**

7. **Multiple Keys Per Action** (Property 7):
   - Generate random actions with multiple keys
   - Verify all keys trigger the action
   - Tag: **Feature: key-bindings-enhancement, Property 7: Multiple Keys Per Action**

8. **KeyEvent to Action Lookup** (Property 8):
   - Generate random KeyEvents
   - Verify correct action lookup or None
   - Tag: **Feature: key-bindings-enhancement, Property 8: KeyEvent to Action Lookup**

9. **Action to Keys Reverse Lookup** (Property 9):
   - Generate random action names
   - Verify correct key expressions and requirements returned
   - Tag: **Feature: key-bindings-enhancement, Property 9: Action to Keys Reverse Lookup**

10. **Display Formatting** (Property 10):
    - Generate random key expressions
    - Verify formatting is consistent and readable
    - Tag: **Feature: key-bindings-enhancement, Property 10: Display Formatting**

11. **Legacy Key Name Compatibility** (Property 11):
    - Generate key names from old SPECIAL_KEY_MAP
    - Verify they still work as KeyCode names
    - Tag: **Feature: key-bindings-enhancement, Property 11: Legacy Key Name Compatibility**

### Test Organization

- Unit tests: `test/test_key_bindings.py`
- Property tests: `test/test_key_bindings_properties.py`
- Integration tests: `test/test_key_bindings_integration.py`

### Testing Best Practices

- Use descriptive test names that explain what is being tested
- Include comments referencing design properties
- Test error handling paths
- Verify backward compatibility with existing test suites
- Use property-based testing for comprehensive coverage
- Keep unit tests focused on specific examples and edge cases
