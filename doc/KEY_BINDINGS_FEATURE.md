# Key Bindings Feature

## Overview

TFM's key bindings system allows you to customize keyboard shortcuts for all actions in the application. The system supports:

- **Single-character keys**: Simple keys like 'q', 'a', '?'
- **KeyCode names**: Special keys like 'ENTER', 'UP', 'PAGE_DOWN'
- **Modifier combinations**: Keys with modifiers like 'Shift-Down', 'Command-Q'
- **Multiple keys per action**: Assign several keys to the same action
- **Selection requirements**: Control when actions are available based on file selection

## Key Expression Format

### Single Character Keys

The simplest form - just a single character:

```python
'quit': ['q', 'Q']
'help': ['?']
'toggle_hidden': ['.']
```

These match against the character typed by the user.

### KeyCode Names

For special keys, use the KeyCode name directly:

```python
'move_up': ['UP']
'move_down': ['DOWN']
'page_up': ['PAGE_UP']
'page_down': ['PAGE_DOWN']
'confirm': ['ENTER']
'cancel': ['ESCAPE']
```

**Available KeyCode names:**
- Navigation: `UP`, `DOWN`, `LEFT`, `RIGHT`, `HOME`, `END`, `PAGE_UP`, `PAGE_DOWN`
- Editing: `ENTER`, `ESCAPE`, `TAB`, `BACKSPACE`, `DELETE`, `INSERT`, `SPACE`
- Function keys: `F1` through `F12`
- Letter keys: `KEY_A` through `KEY_Z`
- Number keys: `KEY_0` through `KEY_9`
- Symbol keys: `KEY_MINUS`, `KEY_EQUAL`, etc.

KeyCode names are **case-insensitive**: `'ENTER'`, `'enter'`, and `'Enter'` all work.

### Modifier Key Combinations

Add modifiers before the main key, separated by hyphens:

```python
'page_up': ['PAGE_UP', 'Shift-UP']
'page_down': ['PAGE_DOWN', 'Shift-DOWN']
'jump_to_top': ['Command-UP']
'jump_to_bottom': ['Command-DOWN']
'delete_files': ['DELETE', 'Command-Backspace']
```

**Available modifiers:**
- `Shift` - Shift key
- `Control` or `Ctrl` - Control key
- `Alt` or `Option` - Alt/Option key
- `Command` or `Cmd` - Command key (macOS)

**Modifier rules:**
- Modifiers are **case-insensitive**: `'Shift'`, `'SHIFT'`, and `'shift'` all work
- Modifier **order doesn't matter**: `'Command-Shift-X'` equals `'Shift-Command-X'`
- You can combine **multiple modifiers**: `'Command-Shift-X'`, `'Control-Alt-Delete'`

## Configuration Format

### Simple Format

For actions without selection requirements, use a list of keys:

```python
KEY_BINDINGS = {
    'quit': ['q', 'Q'],
    'help': ['?'],
    'move_up': ['UP', 'k'],
    'move_down': ['DOWN', 'j'],
}
```

### Extended Format

For actions that require or prohibit file selection, use a dictionary:

```python
KEY_BINDINGS = {
    'delete_files': {
        'keys': ['DELETE', 'Command-Backspace', 'k', 'K'],
        'selection': 'required'  # Only available when files are selected
    },
    'create_directory': {
        'keys': ['m', 'M'],
        'selection': 'none'  # Only available when no files are selected
    },
}
```

**Selection requirements:**
- `'required'` - Action only available when files are selected
- `'none'` - Action only available when no files are selected
- `'any'` - Action always available (default)

## Complete Example

Here's a complete configuration example:

```python
# ~/.tfm/config.py

class Config:
    KEY_BINDINGS = {
        # Basic navigation
        'quit': ['q', 'Q'],
        'help': ['?'],
        'move_up': ['UP', 'k'],
        'move_down': ['DOWN', 'j'],
        'move_left': ['LEFT', 'h'],
        'move_right': ['RIGHT', 'l'],
        
        # Page navigation with modifiers
        'page_up': ['PAGE_UP', 'Shift-UP'],
        'page_down': ['PAGE_DOWN', 'Shift-DOWN'],
        'jump_to_top': ['HOME', 'Command-UP'],
        'jump_to_bottom': ['END', 'Command-DOWN'],
        
        # File operations with selection requirements
        'delete_files': {
            'keys': ['DELETE', 'Command-Backspace'],
            'selection': 'required'
        },
        'copy_files': {
            'keys': ['c', 'C'],
            'selection': 'required'
        },
        'create_directory': {
            'keys': ['m', 'M'],
            'selection': 'none'
        },
    }
```

## Migration from Old Format

If you have an existing configuration, here's how to migrate:

### Old Format (Before)

```python
KEY_BINDINGS = {
    'move_up': ['UP', 'k'],
    'page_up': ['PPAGE'],  # Old special key name
}
```

### New Format (After)

```python
KEY_BINDINGS = {
    'move_up': ['UP', 'k'],
    'page_up': ['PAGE_UP', 'Shift-UP'],  # Use KeyCode name + modifier
}
```

**Key changes:**
- `PPAGE` → `PAGE_UP`
- `NPAGE` → `PAGE_DOWN`
- All other KeyCode names remain the same
- Add modifier combinations for enhanced functionality

## Tips and Best Practices

1. **Use descriptive keys**: Choose keys that make sense for the action
2. **Provide alternatives**: Assign multiple keys to important actions
3. **Consider modifiers**: Use modifiers for related actions (e.g., Shift for page navigation)
4. **Test your bindings**: Make sure keys don't conflict with each other
5. **Document custom bindings**: Add comments to explain non-obvious choices

## Troubleshooting

### Key not working

1. Check the key expression format is correct
2. Verify the KeyCode name is valid (case doesn't matter)
3. Make sure modifiers are spelled correctly
4. Check for conflicts with other key bindings

### Action not available

1. Check the selection requirement matches your current state
2. Verify files are selected if action requires `'selection': 'required'`
3. Verify no files are selected if action requires `'selection': 'none'`

### Modifier key not recognized

1. Verify modifier name is one of: Shift, Control/Ctrl, Alt/Option, Command/Cmd
2. Check spelling (case doesn't matter)
3. Make sure you're using hyphens to separate modifiers from the main key

## See Also

- [Configuration Feature](CONFIGURATION_FEATURE.md) - General configuration guide
- [Help Dialog Feature](HELP_DIALOG_FEATURE.md) - Viewing key bindings in TFM
