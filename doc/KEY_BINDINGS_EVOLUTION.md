# Key Bindings Evolution Documentation

## Overview

This document describes the evolution of TFM's key binding system, including the migration of hardcoded functionality to proper key bindings and the simplification of navigation controls.

## Create Directory Key Binding Migration

### Problem with Original Implementation

Previously, directory creation was hardcoded in the `move_selected_files()` function:

```python
def move_selected_files(self):
    """Move selected files to the opposite pane's directory, or create new directory if no files selected"""
    if not current_pane['selected_files']:
        # No files selected - create new directory instead
        self.enter_create_directory_mode()
        return
```

#### Issues with the Old Approach
1. **Hidden Functionality**: F7 was mentioned in help but not in KEY_BINDINGS
2. **Confusing Behavior**: The 'm' key would create directories when no files were selected
3. **Not Configurable**: Users couldn't customize the key binding
4. **Inconsistent Design**: Violated the KEY_BINDINGS system design
5. **Poor Separation of Concerns**: Move and create were mixed in one function

### Solution: Proper Key Binding Integration

#### 1. Added `create_directory` Action to KEY_BINDINGS

**File**: `src/_config.py`

```python
KEY_BINDINGS = {
    # ... other bindings ...
    'create_directory': ['D'],             # Create new directory (prompts for directory name)
    # ... other bindings ...
}
```

#### 2. Removed Hardcoded Logic from `move_selected_files()`

**Before**:
```python
def move_selected_files(self):
    """Move selected files to the opposite pane's directory, or create new directory if no files selected"""
    if not current_pane['selected_files']:
        # No files selected - create new directory instead
        self.enter_create_directory_mode()
        return
```

**After**:
```python
def move_selected_files(self):
    """Move selected files to the opposite pane's directory"""
    if not current_pane['selected_files']:
        print("No files selected to move")
        return
```

#### 3. Added Proper Key Handling

```python
elif self.is_key_for_action(key, 'create_directory'):  # Create new directory
    self.enter_create_directory_mode()
```

### Key Sharing Innovation

This implementation demonstrates an innovative approach to key binding conflicts:

#### Traditional Problem
- Multiple actions want the same key
- Results in conflicts or suboptimal key assignments
- Users must remember many different keys

#### TFM's Solution: Selection-Aware Key Sharing
- Same key (`M`) used for related actions
- Selection requirements make them mutually exclusive:
  - `move_files`: requires selection (`'selection': 'required'`)
  - `create_directory`: requires no selection (`'selection': 'none'`)
- Context determines which action is available
- No conflicts, intuitive behavior

#### User Experience
```
Press 'M' when no files selected → Creates new directory
Press 'M' when files are selected → Moves selected files
```

### Current Configuration

| Action | Keys | Selection Requirement | Description |
|--------|------|----------------------|-------------|
| `move_files` | `m`, `M` | `required` | Move selected files (when files are selected) |
| `create_directory` | `M` | `none` | Create new directory (when no files are selected) |
| `create_file` | `E` | `any` | Create new file |

## Navigation Keys Simplification

### Background

The navigation system originally supported both arrow keys and vim-style j/k/h/l keys, creating complexity and potential conflicts.

### Changes Made

#### Removed Key Bindings
- **j key**: No longer used for down navigation
- **k key**: No longer used for up navigation (now exclusively for delete)
- **h key**: No longer used for left navigation
- **l key**: No longer used for right navigation or log scrolling
- **L key**: No longer used for log scrolling

#### Preserved Navigation
- **↑ Arrow**: Navigate files up
- **↓ Arrow**: Navigate files down  
- **← Arrow**: Navigate left (switch panes or go to parent)
- **→ Arrow**: Navigate right (switch panes or go to parent)

### Implementation Details

#### File Navigation
```python
# Before (removed):
elif key == curses.KEY_UP or key == ord('k'):
    # Navigate up

# After (simplified):
elif key == curses.KEY_UP:
    # Navigate up
```

#### Dialog Navigation
```python
# Before (removed):
elif key == curses.KEY_LEFT or key == ord('h'):
    # Move selection left

# After (simplified):
elif key == curses.KEY_LEFT:
    # Move selection left
```

#### Log Scrolling Changes
```python
# Removed entirely:
elif key == ord('l'):  # 'l' key - scroll log up
elif key == ord('L'):  # 'L' key - scroll log down

# Preserved:
elif key == curses.KEY_SR:  # Shift+Up - scroll log up
elif key == curses.KEY_SF:  # Shift+Down - scroll log down
```

### Preserved Functionality

#### Delete Feature
The 'k' and 'K' keys are now exclusively used for the delete functionality:
- **k/K**: Delete selected files with confirmation

#### Log Scrolling
Log scrolling is available via:
- **Shift+Up**: Scroll log up (toward older messages)
- **Shift+Down**: Scroll log down (toward newer messages)
- **Shift+Left**: Fast scroll up (toward older messages)
- **Shift+Right**: Fast scroll down (toward newer messages)

#### Other Navigation
- **Tab**: Switch between left and right panes
- **Enter**: Open file or enter directory
- **Backspace**: Go to parent directory
- **Home/End**: Jump to first/last file
- **Page Up/Down**: Navigate by pages

## Benefits of Evolution

### Create Directory Migration Benefits

#### ✅ **Proper Separation of Concerns**
- Move files and create directory are now separate actions
- Each action has clear, predictable behavior

#### ✅ **User Configurable**
Users can now customize the create_directory key binding:

```python
KEY_BINDINGS = {
    # Use a different key
    'create_directory': ['N'],  # 'N' for New directory
    
    # Use multiple keys
    'create_directory': ['D', '7'],
    
    # Use extended format with selection requirements
    'create_directory': {'keys': ['D'], 'selection': 'none'},
}
```

#### ✅ **Consistent with KEY_BINDINGS System**
- Works with unified `is_key_for_action()` method
- Respects selection requirements
- Integrates with help dialog automatically

### Navigation Simplification Benefits

1. **Simplified Controls**: Only arrow keys for navigation reduces confusion
2. **Consistent Interface**: All navigation uses the same key paradigm
3. **Reduced Conflicts**: Eliminates potential conflicts between navigation and other features
4. **Clear Key Purpose**: 'k' is now exclusively for delete operations
5. **Easier Learning**: Users only need to remember arrow keys for navigation

## User Migration

### For Create Directory Changes
- No action required - existing behavior is preserved
- `D` key now creates directories instead of the old F7 behavior
- `m`/`M` keys now require file selection (no more accidental directory creation)

### For Navigation Changes
- Users can no longer use j/k/h/l for navigation
- Must use arrow keys for all navigation
- Delete feature still uses k/K keys
- Log scrolling uses Shift+Up/Down keys

### Configuration Updates
Users can customize the `create_directory` action like any other key binding:

```python
# In ~/.tfm/config.py
class Config:
    KEY_BINDINGS = {
        # ... other bindings ...
        'create_directory': ['7'],  # Use '7' key (similar to F7)
        # ... other bindings ...
    }
```

## Testing

### Comprehensive Testing
- ✅ `create_directory` action is properly configured
- ✅ Key binding works with unified approach
- ✅ Selection requirements are respected
- ✅ `move_files` now properly requires selection
- ✅ Help dialog integration works
- ✅ j/k/h/l navigation keys completely removed
- ✅ Arrow key navigation fully preserved
- ✅ Delete functionality (k/K) intact
- ✅ Log scrolling (Shift+Up/Down) preserved

### Test Files
- `test/test_create_directory_key_binding.py` - Create directory migration tests
- `test/test_help_dialog_integration.py` - Help dialog integration tests
- `test/test_navigation_keys_removed.py` - Navigation simplification tests
- `verify_navigation_changes.py` - Quick verification script

## Implementation Status

✅ **COMPLETE** - Both key binding evolutions are fully implemented and tested.

### Files Modified

#### Create Directory Migration
- `src/_config.py` - Added `create_directory` to KEY_BINDINGS
- `src/tfm_main.py` - Removed hardcoded logic, added proper key handling
- `src/tfm_info_dialog.py` - Updated help dialog to use dynamic key binding

#### Navigation Simplification
- `src/tfm_main.py` - Removed j/k/h/l navigation handling
- `src/tfm_search_dialog.py` - Removed j/k navigation handling
- `src/tfm_jump_dialog.py` - Removed h/l navigation handling
- `src/tfm_list_dialog.py` - Removed j/k/h/l navigation handling

## Conclusion

The key bindings evolution successfully:

1. **Migrated hardcoded functionality** to the proper KEY_BINDINGS system
2. **Simplified navigation controls** to use only arrow keys
3. **Maintained backward compatibility** where possible
4. **Improved user configurability** through proper key binding support
5. **Enhanced system consistency** by following established patterns

These changes provide users with full control over key bindings while maintaining clean separation of concerns and eliminating potential conflicts. The evolution demonstrates TFM's commitment to a well-designed, configurable, and intuitive user interface.