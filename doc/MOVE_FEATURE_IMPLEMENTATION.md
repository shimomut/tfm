# Move Feature Implementation

## Overview

The move feature allows users to move selected files and directories from the current pane to the opposite pane using the 'm' or 'M' keys. This feature provides the same conflict resolution capabilities as the copy feature but removes files from the source location after successful transfer.

## Key Features

### Core Functionality
- **Single File Move**: Move the currently selected file/directory
- **Multiple File Move**: Move all selected files/directories at once
- **Recursive Directory Move**: Directories are moved with all their contents
- **Symbolic Link Preservation**: Symbolic links are copied as links, not target files
- **Conflict Resolution**: Interactive dialog for handling existing files

### Safety Features
- **Permission Checks**: Verifies write access to destination before attempting move
- **Parent Directory Protection**: Cannot move the parent directory (..) entry
- **Same Directory Prevention**: Cannot move files to the same directory they're already in
- **Error Handling**: Comprehensive error reporting with detailed messages
- **Selection Clearing**: Automatically clears selections after successful moves

## Implementation Details

### Key Binding Configuration

Added to `src/tfm_config.py`:
```python
KEY_BINDINGS = {
    # ... other bindings ...
    'move_files': ['m', 'M'],
    # ... other bindings ...
}
```

### Method Implementation

Added to `src/tfm_main.py`:

#### 1. `move_selected_files(self)`
- Main entry point for move operations
- Determines which files to move (selected files or current file)
- Performs initial validation and permission checks
- Calls `move_files_to_directory()` to handle the actual operation

#### 2. `move_files_to_directory(self, files_to_move, destination_dir)`
- Detects conflicts with existing files in destination
- Shows conflict resolution dialog if needed
- Handles user choice (overwrite, skip, cancel)
- Calls `perform_move_operation()` to execute the move

#### 3. `perform_move_operation(self, files_to_move, destination_dir, overwrite=False)`
- Performs the actual file/directory move operations
- Special handling for symbolic links using `os.readlink()`
- Uses `shutil.move()` for files and directories
- Provides detailed logging of operations and errors
- Refreshes panes and clears selections after successful moves

### Key Handler Integration

Added to the main event loop in `src/tfm_main.py`:
```python
elif self.is_key_for_action(key, 'move_files'):  # Move selected files
    self.move_selected_files()
```

## Usage Guide

### Basic Usage
1. Navigate to a file or directory using arrow keys
2. Press 'm' or 'M' to move it to the opposite pane
3. If conflicts exist, choose from the dialog options

### Multiple Selection
1. Select multiple files using Space bar
2. Press 'm' or 'M' to move all selected files
3. Selections are automatically cleared after successful move

### Conflict Resolution
When files with the same names exist in the destination:
- **Overwrite (o)**: Replace existing files with moved files
- **Skip (s)**: Move only non-conflicting files, leave conflicts untouched
- **Cancel (c)**: Abort the entire move operation

## Special Cases

### Directory Handling
- Directories are moved recursively with all contents
- Nested directory structures are preserved
- Empty directories are moved correctly

### Symbolic Link Handling
- Symbolic links are preserved as links (not dereferenced)
- Uses `os.readlink()` to get the link target
- Creates new symbolic link in destination with same target
- Original symbolic link is removed from source

### Error Conditions
- **Permission Denied**: Cannot write to destination directory
- **Same Directory**: Attempting to move files to their current location
- **Parent Directory**: Attempting to move the (..) entry
- **File System Errors**: Disk full, network issues, etc.

## Testing

### Test Files Created
- `test/test_move_feature.py`: Comprehensive functionality testing
- `test/demo_move_feature.py`: Feature demonstration and overview
- `test/verify_move_implementation.py`: Implementation verification
- `test/test_move_integration.py`: Integration testing with TFM systems

### Test Coverage
- ✅ Basic file move operations
- ✅ Directory move with nested content
- ✅ Symbolic link preservation
- ✅ Conflict detection and resolution
- ✅ Permission checking
- ✅ Error handling
- ✅ Key binding integration
- ✅ Configuration system integration

## Comparison with Copy Feature

| Aspect | Copy Feature | Move Feature |
|--------|-------------|-------------|
| Source Files | Remain in place | Removed after successful transfer |
| Key Binding | 'c', 'C' | 'm', 'M' |
| Conflict Resolution | Same dialog system | Same dialog system |
| Symbolic Links | Copied as links | Moved as links |
| Error Handling | Same approach | Same approach |
| Performance | Slower (copy + keep) | Faster (single operation) |

## Future Enhancements

Potential improvements for future versions:
- Progress bar for large directory moves
- Undo functionality for move operations
- Move to specific path (not just opposite pane)
- Batch move operations with different destinations
- Integration with system trash/recycle bin

## Troubleshooting

### Common Issues
1. **"Permission denied"**: Check write permissions on destination directory
2. **"Cannot move to same directory"**: Ensure you're moving to the opposite pane
3. **"Cannot move parent directory"**: The (..) entry cannot be moved
4. **Symbolic link issues**: Ensure the link target path is valid in new location

### Debug Information
The move feature provides detailed logging in the TFM log pane:
- Files being moved
- Conflict resolution choices
- Error messages with specific details
- Operation completion status

## Code Quality

### Standards Followed
- Consistent error handling patterns
- Comprehensive input validation
- Clear method documentation
- Integration with existing TFM systems
- Follows established code style

### Security Considerations
- Path traversal protection
- Permission validation
- Safe file operations
- No arbitrary code execution risks

## Conclusion

The move feature provides a robust, user-friendly way to relocate files and directories within TFM. It maintains the same high standards of safety and usability as the existing copy and delete features while providing the efficiency of direct file movement operations.