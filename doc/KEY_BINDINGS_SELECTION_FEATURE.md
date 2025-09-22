# Key Bindings Selection Requirements Feature

## Overview

The TFM key bindings system has been extended to support optional file selection status requirements. This allows key bindings to be configured to work only when files are selected, only when no files are selected, or regardless of selection status.

## Key Binding Formats

### Simple Format (Backward Compatible)
```python
'action': ['key1', 'key2']
```
This is the original format that works regardless of selection status.

### Extended Format (New)
```python
'action': {'keys': ['key1', 'key2'], 'selection': 'requirement'}
```

## Selection Requirements

- **`'any'`** (default): Works regardless of selection status
- **`'required'`**: Only works when at least one item is explicitly selected
- **`'none'`**: Only works when no items are explicitly selected

## Configuration Examples

```python
KEY_BINDINGS = {
    # Simple format - works always
    'quit': ['q', 'Q'],
    'help': ['?'],
    
    # Extended format - requires selection
    'copy_files': {'keys': ['c', 'C'], 'selection': 'required'},
    'delete_files': {'keys': ['k', 'K'], 'selection': 'required'},
    
    # Extended format - explicit 'any'
    'search': {'keys': ['f'], 'selection': 'any'},
    
    # Extended format - no selection allowed
    'create_file': {'keys': ['E'], 'selection': 'none'},
}
```

## Implementation

### Core Components

1. **Extended Config Format** (`src/_config.py`)
   - Updated `KEY_BINDINGS` to support both simple and extended formats
   - Actions requiring selection use the extended format

2. **KeyBindingManager Utility** (`src/tfm_key_bindings.py`)
   - `get_keys_for_action(action)` - Get keys for an action
   - `get_selection_requirement(action)` - Get selection requirement
   - `is_action_available(action, has_selection)` - Check availability
   - `get_available_actions(has_selection)` - Get all available actions
   - `get_key_to_action_mapping(has_selection)` - Get filtered key mapping
   - `validate_key_bindings()` - Validate configuration

3. **Config System Integration** (`src/tfm_config.py`)
   - Updated `ConfigManager` to handle extended format
   - Added `get_selection_requirement()` method
   - Added `is_action_available()` method
   - Added `is_key_bound_to_action_with_selection()` method
   - Module-level convenience functions for backward compatibility

4. **Main TFM Integration** (`src/tfm_main.py`)
   - Updated `is_key_for_action()` method to be selection-aware by default
   - All key handling automatically respects selection requirements
   - No need to manually choose between different methods

### Usage in TFM Code

```python
# Using KeyBindingManager utility
from tfm_key_bindings import KeyBindingManager

has_selection = len(selected_files) > 0
if KeyBindingManager.is_action_available('copy_files', has_selection):
    # Action is available
    pass

# Using config system integration
from tfm_config import is_key_bound_to_with_selection, is_action_available

if is_key_bound_to_with_selection('c', 'copy_files', has_selection):
    # Key is bound and action is available
    pass

# In main TFM loop (unified approach)
elif self.is_key_for_action(key, 'copy_files'):  # Automatically respects selection requirements
    self.copy_selected_files()
```

## Current Actions by Selection Requirement

### Actions Requiring Selection (`'required'`)
- `copy_files` - Copy selected files to other pane
- `move_files` - Move selected files to other pane  
- `delete_files` - Delete selected files/directories
- `create_archive` - Create archive from selected files
- `compare_selection` - Show file comparison options

### Actions Working Regardless (`'any'`)
- All other actions (quit, help, navigation, etc.)

### Actions Requiring No Selection (`'none'`)
- Currently none, but the framework supports this

## Benefits

1. **Improved User Experience**: Actions only appear when they make sense
2. **Reduced Errors**: Prevents accidental operations on wrong files
3. **Context Awareness**: UI can show/hide actions based on selection
4. **Backward Compatibility**: Existing simple format still works
5. **Flexible Configuration**: Easy to change requirements per action
6. **Unified Implementation**: Single `is_key_for_action()` method handles all cases
7. **User Configurable**: Users can set selection requirements for any action

## Testing

Comprehensive tests are provided:
- `test/test_key_bindings_selection.py` - Tests the extended format
- `test/test_key_bindings_manager.py` - Tests the utility manager
- `demo/demo_key_bindings_selection.py` - Interactive demonstration

## Migration Guide

### For Existing Configurations
No changes needed - simple format continues to work.

### For New Selection-Aware Actions
```python
# Old way (always available)
'my_action': ['x', 'X']

# New way (requires selection)
'my_action': {'keys': ['x', 'X'], 'selection': 'required'}
```

### User Configuration Examples
Users can now configure any action with selection requirements:

```python
KEY_BINDINGS = {
    # Make view_text require selection
    'view_text': {'keys': ['v', 'V'], 'selection': 'required'},
    
    # Make create_file only work when nothing is selected
    'create_file': {'keys': ['E'], 'selection': 'none'},
    
    # Keep search working regardless of selection (explicit)
    'search': {'keys': ['f'], 'selection': 'any'},
    
    # Traditional format still works (defaults to 'any')
    'quit': ['q', 'Q'],
}
```

### For TFM Core Integration
```python
# In your key handler
from tfm_key_bindings import KeyBindingManager

def handle_key(key, selected_files):
    has_selection = len(selected_files) > 0
    key_mapping = KeyBindingManager.get_key_to_action_mapping(has_selection)
    
    if key in key_mapping:
        action = key_mapping[key]
        # Execute action
```

## Implementation Status

✅ **COMPLETE** - The unified key bindings system with dynamic selection requirements is fully implemented and integrated into TFM.

### What's Working
- ✅ Extended KEY_BINDINGS format in configuration
- ✅ Selection requirement checking ('any', 'required', 'none')
- ✅ Integration with tfm_config.py
- ✅ **Unified key handling** - single `is_key_for_action()` method for all actions
- ✅ **User-configurable selection requirements** for ANY action
- ✅ Backward compatibility with existing simple format
- ✅ Automatic selection requirement enforcement
- ✅ Comprehensive test coverage (33+ tests passing)
- ✅ Utility functions and helper classes
- ✅ Configuration validation
- ✅ Documentation and examples
- ✅ Live demos and integration tests

### Actions Currently Using Selection Requirements
- `copy_files` - requires selection
- `move_files` - requires selection  
- `delete_files` - requires selection
- `create_archive` - requires selection
- `compare_selection` - requires selection

## Future Enhancements

1. **Dynamic Requirements**: Selection requirements based on file types
2. **Count-Based Requirements**: Require specific number of selected items
3. **Context-Aware Help**: Show only available actions in help dialog
4. **Visual Indicators**: Highlight available/unavailable actions in UI
5. **More Selection-Aware Actions**: Convert additional actions to use selection requirements