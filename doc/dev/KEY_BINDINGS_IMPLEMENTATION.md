# Key Bindings System Implementation

## Overview

This document describes the implementation of TFM's enhanced key bindings system, which supports KeyCode names, modifier key combinations, and flexible configuration formats.

## Architecture

### Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                     TFM Application                          │
│                  (tfm_main.py, etc.)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ Uses
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Public API (tfm_config.py)                      │
│  - find_action_for_event(event, has_selection)              │
│  - get_keys_for_action(action)                              │
│  - format_key_for_display(key_expr)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ Delegates to
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  KeyBindings Class                           │
│  - Parses key expressions                                   │
│  - Matches KeyEvents against bindings                       │
│  - Enforces selection requirements                          │
└────────────────────────┬────────────────────────────────────┘
                         │ Uses
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  TTK KeyCode & ModifierKey                   │
│  - KeyCode enum (StrEnum)                                   │
│  - ModifierKey flags (IntFlag)                              │
└─────────────────────────────────────────────────────────────┘
```

## KeyBindings Class

### Location
`src/tfm_config.py`

### Purpose
Encapsulates all key binding logic, providing:
- Key expression parsing
- KeyEvent matching
- Action lookup
- Display formatting

### Key Methods

#### `__init__(key_bindings_config: dict)`
Initializes the KeyBindings instance with configuration and builds a reverse lookup table.

#### `_parse_key_expression(key_expr: str) -> tuple[str, int]`
Parses a key expression into main key and modifier flags.

**Examples:**
- `"q"` → `("Q", 0)`
- `"Shift-Down"` → `("DOWN", ModifierKey.SHIFT)`
- `"Command-Shift-X"` → `("X", ModifierKey.COMMAND | ModifierKey.SHIFT)`

**Algorithm:**
1. If single character, return uppercase with no modifiers
2. Split on hyphen to separate modifiers from main key
3. Parse each modifier name (case-insensitive)
4. Combine modifiers using bitwise OR
5. Return tuple of (main_key, modifier_flags)

#### `_keycode_from_string(key_str: str) -> Optional[int]`
Converts a KeyCode name string to its integer value.

Uses `getattr(KeyCode, key_str, None)` to access KeyCode enum values by name.

#### `_match_key_event(event, main_key: str, modifiers: int) -> bool`
Checks if a KeyEvent matches a key expression.

**Matching logic:**
1. Check modifiers match exactly
2. For single-character keys, match against `event.char`
3. For multi-character keys, match against `event.key_code`

#### `find_action_for_event(event, has_selection: bool) -> Optional[str]`
Finds the action bound to a KeyEvent, respecting selection requirements.

**Algorithm:**
1. Iterate through reverse lookup table
2. For each key binding, check if event matches
3. If match found, check selection requirement
4. Return first action that satisfies all conditions

#### `get_keys_for_action(action: str) -> tuple[list[str], str]`
Returns all key expressions and selection requirement for an action.

Used by help dialog to display key bindings.

#### `format_key_for_display(key_expr: str) -> str`
Formats a key expression for display in UI.

**Formatting rules:**
- Single characters: return as-is
- Multi-character: capitalize modifiers, uppercase main key
- Abbreviate "Command" to "Cmd"

## Public API Functions

### `find_action_for_event(event, has_selection: bool = False) -> Optional[str]`
**Primary API for key binding lookup.**

Replaces all deprecated functions:
- `is_key_bound_to()`
- `is_special_key_bound_to()`
- `is_input_event_bound_to()`
- And their `_with_selection` variants

**Usage:**
```python
from tfm_config import find_action_for_event

action = find_action_for_event(event, has_selection)
if action == 'quit':
    # Handle quit
elif action == 'delete_files':
    # Handle delete
```

### `get_keys_for_action(action: str) -> tuple[list[str], str]`
Returns key expressions and selection requirement for an action.

**Usage:**
```python
from tfm_config import get_keys_for_action

keys, selection_req = get_keys_for_action('delete_files')
# keys = ['DELETE', 'Command-Backspace']
# selection_req = 'required'
```

### `format_key_for_display(key_expr: str) -> str`
Formats a key expression for display.

**Usage:**
```python
from tfm_config import format_key_for_display

display = format_key_for_display('Command-Shift-X')
# display = 'Cmd-Shift-X'
```

## Deprecated API Functions

The following functions are deprecated but maintained for backward compatibility:

- `is_key_bound_to(key_char, action)`
- `is_key_bound_to_with_selection(key_char, action, has_selection)`
- `is_special_key_bound_to(key_code, action)`
- `is_special_key_bound_to_with_selection(key_code, action, has_selection)`
- `is_input_event_bound_to(event, action)`
- `is_input_event_bound_to_with_selection(event, action, has_selection)`
- `get_action_for_key(key)`

All deprecated functions emit `DeprecationWarning` when called.

**Migration:**
```python
# OLD
if is_input_event_bound_to_with_selection(event, 'quit', has_selection):
    # handle quit

# NEW
action = find_action_for_event(event, has_selection)
if action == 'quit':
    # handle quit
```

## Data Structures

### Key Expression Lookup Table

The `KeyBindings` class builds a reverse lookup table:

```python
_key_to_actions = {
    ('Q', 0): [('quit', 'any')],
    ('UP', 0): [('move_up', 'any')],
    ('UP', ModifierKey.SHIFT): [('page_up', 'any')],
    ('DELETE', 0): [('delete_files', 'required')],
}
```

**Key:** `(main_key, modifier_flags)` tuple
**Value:** List of `(action, selection_requirement)` tuples

This enables O(1) lookup of actions from key events.

### Configuration Formats

**Simple format:**
```python
'action_name': ['key1', 'key2']
```

**Extended format:**
```python
'action_name': {
    'keys': ['key1', 'key2'],
    'selection': 'required'  # or 'none' or 'any'
}
```

Both formats are supported for backward compatibility.

## Key Expression Parsing

### Grammar

```
key_expression := single_char | modified_key
single_char := any single character
modified_key := modifier_list "-" main_key
modifier_list := modifier | modifier "-" modifier_list
modifier := "Shift" | "Control" | "Ctrl" | "Alt" | "Option" | "Command" | "Cmd"
main_key := keycode_name | single_char
keycode_name := "UP" | "DOWN" | "ENTER" | ... (any KeyCode name)
```

### Parsing Algorithm

1. Check length: if 1, treat as single character
2. Split on hyphen: `parts = key_expr.split('-')`
3. Last part is main key: `main_key = parts[-1]`
4. Earlier parts are modifiers: `modifiers = parts[:-1]`
5. Parse each modifier name (case-insensitive)
6. Combine modifiers with bitwise OR
7. Return `(main_key, modifier_flags)`

### Case Insensitivity

All parsing is case-insensitive:
- Modifier names: `'Shift'`, `'SHIFT'`, `'shift'` all work
- KeyCode names: `'ENTER'`, `'enter'`, `'Enter'` all work
- Single characters: matched as uppercase

### Order Independence

Modifier order doesn't matter:
- `'Command-Shift-X'` equals `'Shift-Command-X'`
- Both parse to `('X', ModifierKey.COMMAND | ModifierKey.SHIFT)`

## KeyEvent Matching

### Matching Algorithm

1. **Check modifiers:** `event.modifiers == expected_modifiers`
2. **Check main key:**
   - Single character: `event.char.upper() == main_key`
   - KeyCode name: `event.key_code == keycode_value`

### Single Character Matching

Single-character keys match against `KeyEvent.char`:
```python
if len(main_key) == 1:
    return event.char and event.char.upper() == main_key
```

This maintains backward compatibility with existing character-based bindings.

### KeyCode Matching

Multi-character keys match against `KeyEvent.key_code`:
```python
expected_keycode = self._keycode_from_string(main_key)
return event.key_code == expected_keycode
```

## Selection Requirements

### Requirement Types

- `'required'`: Action only available when `has_selection == True`
- `'none'`: Action only available when `has_selection == False`
- `'any'`: Action always available (default)

### Enforcement

Selection requirements are checked in `find_action_for_event()`:

```python
for action, selection_req in actions:
    if self._check_selection_requirement(selection_req, has_selection):
        return action
```

This ensures actions are only triggered when appropriate.

## Error Handling

### Invalid Key Expressions

- Log warning
- Skip binding
- Continue processing other bindings
- Don't crash application

### Unknown Modifiers

- Log warning
- Ignore unknown modifier
- Continue parsing rest of expression

### Unknown KeyCode Names

- Log warning
- Return None from `_keycode_from_string()`
- Skip binding in matching logic

### Missing Configuration

- Fall back to `DefaultConfig.KEY_BINDINGS`
- Log info message
- Continue normal operation

## Performance Considerations

### Reverse Lookup Table

The `_key_to_actions` lookup table enables O(1) action lookup:
- Built once during initialization
- Indexed by `(main_key, modifiers)` tuple
- No linear search through all bindings

### Caching

The `ConfigManager` caches the `KeyBindings` instance:
- Created once per configuration
- Cleared on `reload_config()`
- Avoids rebuilding lookup table on every key press

## Testing

### Unit Tests

Located in `test/test_key_bindings.py`:
- KeyBindings class initialization
- Key expression parsing
- KeyEvent matching
- Selection requirement enforcement

### Property-Based Tests

Located in `test/test_key_bindings_properties.py`:
- KeyCode name recognition (all cases)
- Modifier key support (all combinations)
- Single character backward compatibility
- Configuration format support

### Integration Tests

Located in `test/test_key_bindings_integration.py`:
- Application-level key handling
- Help dialog display
- Configuration loading

## Migration Guide

### For Application Code

**Before:**
```python
from tfm_config import is_input_event_bound_to_with_selection

if is_input_event_bound_to_with_selection(event, 'quit', has_selection):
    self.quit()
elif is_input_event_bound_to_with_selection(event, 'delete_files', has_selection):
    self.delete_files()
```

**After:**
```python
from tfm_config import find_action_for_event

action = find_action_for_event(event, has_selection)
if action == 'quit':
    self.quit()
elif action == 'delete_files':
    self.delete_files()
```

### For Help Dialog

**Before:**
```python
from tfm_config import config_manager

keys = config_manager.get_key_for_action('delete_files')
# keys = ['DELETE', 'Command-Backspace']
```

**After:**
```python
from tfm_config import get_keys_for_action, format_key_for_display

keys, selection_req = get_keys_for_action('delete_files')
formatted_keys = [format_key_for_display(k) for k in keys]
# formatted_keys = ['DELETE', 'Cmd-Backspace']
```

## Future Enhancements

Possible future improvements:

1. **Key sequence support**: Multi-key sequences like "g g" for jump to top
2. **Context-sensitive bindings**: Different bindings for different modes
3. **Dynamic rebinding**: Change bindings at runtime
4. **Conflict detection**: Warn about conflicting key bindings
5. **Key recording**: Record key sequences for custom bindings

## See Also

- [Key Bindings Feature](../KEY_BINDINGS_FEATURE.md) - User documentation
- [Configuration System](CONFIGURATION_SYSTEM.md) - Configuration architecture
- [TTK Event System](../../ttk/doc/dev/EVENT_SYSTEM.md) - KeyEvent details
