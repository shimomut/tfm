# Rename Feature Implementation

## Overview

The rename feature allows users to rename files and directories in TFM using the 'R' key. This document describes the complete implementation of the rename functionality.

## Key Binding

- **Keys**: `r` and `R`
- **Action**: `rename_file`
- **Behavior**: Enters rename mode for the currently selected file or directory

## Implementation Details

### 1. Configuration Changes

**File**: `src/tfm_config.py`
- Added `'rename_file': ['r', 'R']` to the `KEY_BINDINGS` dictionary in `DefaultConfig`

**File**: `src/_config.py` 
- Added `'rename_file': ['r', 'R']` to the user configuration template

### 2. Core Functionality

**File**: `src/tfm_main.py`

#### New Instance Variables
```python
# Rename mode state
self.rename_mode = False
self.rename_pattern = ""
self.rename_original_name = ""
self.rename_file_path = None
```

#### New Methods

1. **`enter_rename_mode()`**
   - Checks if files are selected (blocks bulk rename - not implemented yet)
   - Validates that a file/directory is selected
   - Prevents renaming parent directory (..)
   - Initializes rename mode with current filename

2. **`exit_rename_mode()`**
   - Cleans up rename mode state
   - Triggers screen redraw

3. **`perform_rename()`**
   - Validates new filename (non-empty, no invalid characters)
   - Checks if target already exists
   - Performs the actual rename operation using `Path.rename()`
   - Handles errors (permission denied, file exists, etc.)
   - Refreshes file list and repositions cursor

4. **`handle_rename_input(key)`**
   - Handles keyboard input during rename mode
   - ESC: Cancel rename
   - Enter: Confirm rename
   - Backspace: Remove last character
   - Printable characters: Add to filename

### 3. User Interface Integration

#### Status Bar Display
- Shows rename prompt: `Rename 'original_name' to: new_name_`
- Displays help text: `ESC:cancel Enter:confirm`
- Cursor indicator shows current input position

#### Main Input Loop
- Added rename mode handling before regular key processing
- Added key binding check for `rename_file` action
- Integrated with dialog exclusion system

#### Help Dialog
- Added rename operation to FILE OPERATIONS section
- Shows `r / R            Rename file (single file only)`

### 4. Error Handling

The implementation handles several error conditions:

- **No files selected**: Shows appropriate message
- **Parent directory**: Cannot rename ".." entry
- **Selected files**: Blocks operation (bulk rename not implemented)
- **Invalid characters**: Rejects filenames with '/' or null bytes
- **Empty filename**: Prevents empty names
- **File exists**: Prevents overwriting existing files
- **Permission denied**: Shows error message
- **Other errors**: Generic error handling with descriptive messages

### 5. Limitations

Current limitations of the implementation:

1. **No bulk rename**: Only works on single files/directories
2. **No advanced validation**: Basic filename validation only
3. **No undo**: Rename operations cannot be undone
4. **No conflict resolution**: Cannot overwrite existing files

## Usage Instructions

1. Navigate to the file or directory you want to rename
2. Ensure no files are selected (press Space to deselect if needed)
3. Press 'r' or 'R' to enter rename mode
4. Edit the filename:
   - Current name is pre-filled
   - Use Backspace to delete characters
   - Type new characters to add them
5. Press Enter to confirm or ESC to cancel

## Testing

The implementation includes comprehensive tests:

- **`test/test_rename_feature.py`**: Basic functionality tests
- **`test/demo_rename_feature.py`**: Creates demo files for interactive testing
- **`test/verify_rename_implementation.py`**: Verifies implementation completeness
- **`test/final_rename_test.py`**: Comprehensive final testing

All tests pass successfully, confirming the feature works as expected.

## Future Enhancements

Potential improvements for future versions:

1. **Bulk rename**: Support for renaming multiple selected files
2. **Pattern-based rename**: Support for regex or pattern-based renaming
3. **Conflict resolution**: Options to handle existing files
4. **Undo functionality**: Ability to undo rename operations
5. **Advanced validation**: More sophisticated filename validation
6. **Preview mode**: Show preview before confirming rename

## Files Modified

1. `src/tfm_config.py` - Added key binding configuration
2. `src/_config.py` - Updated user configuration template  
3. `src/tfm_main.py` - Implemented core rename functionality
4. `doc/RENAME_FEATURE_IMPLEMENTATION.md` - This documentation

## Verification

Run the following commands to verify the implementation:

```bash
# Run comprehensive tests
python test/final_rename_test.py

# Create demo files for interactive testing
python test/demo_rename_feature.py

# Test the feature interactively
python tfm.py
# Navigate to rename_demo directory and press 'r' on a file
```

The rename feature is now fully implemented and ready for use.