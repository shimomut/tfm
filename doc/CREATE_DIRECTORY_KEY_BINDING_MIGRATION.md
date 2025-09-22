# Create Directory Key Binding Migration

## Overview

This document describes the migration from hardcoded directory creation functionality to a proper key binding in the TFM KEY_BINDINGS system.

## Problem

Previously, directory creation was hardcoded in the `move_selected_files()` function:

```python
def move_selected_files(self):
    """Move selected files to the opposite pane's directory, or create new directory if no files selected"""
    if not current_pane['selected_files']:
        # No files selected - create new directory instead
        self.enter_create_directory_mode()
        return
```

### Issues with the Old Approach

1. **Hidden Functionality**: F7 was mentioned in help but not in KEY_BINDINGS
2. **Confusing Behavior**: The 'm' key would create directories when no files were selected
3. **Not Configurable**: Users couldn't customize the key binding
4. **Inconsistent Design**: Violated the KEY_BINDINGS system design
5. **Poor Separation of Concerns**: Move and create were mixed in one function

## Solution

### 1. Added `create_directory` Action to KEY_BINDINGS

**File**: `src/_config.py`

```python
KEY_BINDINGS = {
    # ... other bindings ...
    'create_directory': ['D'],             # Create new directory (prompts for directory name)
    # ... other bindings ...
}
```

### 2. Removed Hardcoded Logic from `move_selected_files()`

**File**: `src/tfm_main.py`

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

### 3. Added Proper Key Handling

**File**: `src/tfm_main.py`

```python
elif self.is_key_for_action(key, 'create_directory'):  # Create new directory
    self.enter_create_directory_mode()
```

### 4. Updated Help Dialog

**File**: `src/tfm_info_dialog.py`

**Before**:
```python
help_lines.append(f"• {'F7'.ljust(12)} Create new directory")
```

**After**:
```python
help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('create_directory')} Create new directory")
```

## Benefits

### ✅ **Proper Separation of Concerns**
- Move files and create directory are now separate actions
- Each action has clear, predictable behavior

### ✅ **User Configurable**
Users can now customize the create_directory key binding:

```python
KEY_BINDINGS = {
    # Use a different key
    'create_directory': ['N'],  # 'N' for New directory
    
    # Use multiple keys
    'create_directory': ['D', '7'],
    
    # Use extended format with selection requirements
    'create_directory': {'keys': ['D'], 'selection': 'none'},  # Only when nothing selected
}
```

### ✅ **Consistent with KEY_BINDINGS System**
- Works with unified `is_key_for_action()` method
- Respects selection requirements
- Integrates with help dialog automatically

### ✅ **Clear Behavior**
- `m` key moves files (requires selection)
- `M` key has context-aware behavior:
  - When files are selected: moves files
  - When no files are selected: creates directory
- No more hidden/confusing functionality
- Smart key sharing eliminates conflicts

## Current Configuration

| Action | Keys | Selection Requirement | Description |
|--------|------|----------------------|-------------|
| `move_files` | `m`, `M` | `required` | Move selected files (when files are selected) |
| `create_directory` | `M` | `none` | Create new directory (when no files are selected) |
| `create_file` | `E` | `any` | Create new file |

**Note**: The `M` key is cleverly shared between `move_files` and `create_directory` using different selection requirements. This eliminates key conflicts while providing intuitive context-aware behavior.

## Key Sharing Innovation

This implementation demonstrates an innovative approach to key binding conflicts:

### Traditional Problem
- Multiple actions want the same key
- Results in conflicts or suboptimal key assignments
- Users must remember many different keys

### TFM's Solution: Selection-Aware Key Sharing
- Same key (`M`) used for related actions
- Selection requirements make them mutually exclusive:
  - `move_files`: requires selection (`'selection': 'required'`)
  - `create_directory`: requires no selection (`'selection': 'none'`)
- Context determines which action is available
- No conflicts, intuitive behavior

### User Experience
```
Press 'M' when no files selected → Creates new directory
Press 'M' when files are selected → Moves selected files
```

This creates a natural, context-aware interface where the same key does the "right thing" based on the current situation.

## User Migration

### For Existing Users
- No action required - existing behavior is preserved
- `D` key now creates directories instead of the old F7 behavior
- `m`/`M` keys now require file selection (no more accidental directory creation)

### For New Configurations
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

Comprehensive tests verify:
- ✅ `create_directory` action is properly configured
- ✅ Key binding works with unified approach
- ✅ Selection requirements are respected
- ✅ `move_files` now properly requires selection
- ✅ Help dialog integration works
- ✅ Backward compatibility is maintained

## Implementation Status

✅ **COMPLETE** - The create_directory key binding migration is fully implemented and tested.

### Files Modified
- `src/_config.py` - Added `create_directory` to KEY_BINDINGS
- `src/tfm_main.py` - Removed hardcoded logic, added proper key handling
- `src/tfm_info_dialog.py` - Updated help dialog to use dynamic key binding
- `test/test_create_directory_key_binding.py` - Comprehensive tests
- `test/test_help_dialog_integration.py` - Help dialog integration tests

### Migration Complete
The hardcoded directory creation functionality has been successfully migrated to the proper KEY_BINDINGS system, providing users with full control over the key binding while maintaining clean separation of concerns.