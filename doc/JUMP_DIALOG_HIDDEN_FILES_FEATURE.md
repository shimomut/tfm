# JumpDialog Hidden Files Support

## Overview

The JumpDialog component now respects the `show_hidden` setting from FileOperations, ensuring consistent behavior with the main file panes when listing directories for navigation.

## Feature Description

When using the Jump Dialog (typically accessed via a keyboard shortcut), the dialog will now filter hidden directories based on the current `show_hidden` setting:

- **Hidden files OFF**: Hidden directories (those starting with `.`) are filtered out
- **Hidden files ON**: All directories are shown, including hidden ones
- **Fallback**: If no FileOperations reference is provided, all directories are included (backward compatibility)

## Implementation Details

### Key Changes

1. **JumpDialog Constructor**: Added `file_operations` reference storage
2. **show() Method**: Modified to accept optional `file_operations` parameter
3. **_scan_worker() Method**: Updated to filter directories based on `show_hidden` setting
4. **_should_include_directory() Method**: New helper method to determine if a directory should be included

### Directory Filtering Logic

The filtering logic uses context-aware filtering:
- If `show_hidden` is `True`, all directories are included
- If `show_hidden` is `False`, the behavior depends on context:
  - **From visible root**: Hidden directories (starting with `.`) are filtered out and not traversed
  - **From hidden root**: All subdirectories are accessible (you can navigate within hidden directories)
  - **Mixed context**: If already within a hidden directory tree, subdirectories are accessible

This smart filtering allows users to:
1. Avoid accidentally entering hidden directories when browsing from visible locations
2. Still navigate normally when already working within hidden directories (like `.git/`, `.config/`, etc.)

### Integration with Main Application

The main TFM application passes the `file_operations` reference when showing the jump dialog:

```python
self.jump_dialog.show(root_directory, self.file_operations)
```

## Usage Examples

### Example Directory Structure
```
/home/user/project/
├── documents/
├── downloads/
├── .git/
├── .vscode/
├── .config/
│   └── settings/
└── src/
    └── .cache/
```

### With Hidden Files OFF (show_hidden = False)

**From visible root (`/home/user/project/`):**
JumpDialog will show:
- `/home/user/project/`
- `/home/user/project/documents/`
- `/home/user/project/downloads/`
- `/home/user/project/src/`

Hidden directories filtered out:
- `.git/`, `.vscode/`, `.config/`, `.config/settings/`, `src/.cache/`

**From hidden root (`/home/user/project/.git/`):**
JumpDialog will show:
- `/home/user/project/.git/`
- `/home/user/project/.git/hooks/`
- `/home/user/project/.git/info/`
- `/home/user/project/.git/objects/`
- All subdirectories within the `.git/` context

### With Hidden Files ON (show_hidden = True)
JumpDialog will show all directories including:
- All visible directories
- All hidden directories: `.git/`, `.vscode/`, `.config/`, `.config/settings/`, `src/.cache/`

## Configuration

The behavior is controlled by the same setting that controls hidden file visibility in the main panes:

```python
# In config file
SHOW_HIDDEN_FILES = False  # Default: hide hidden directories in JumpDialog
SHOW_HIDDEN_FILES = True   # Show hidden directories in JumpDialog
```

Users can toggle this setting at runtime using the standard hidden files toggle command.

## Backward Compatibility

The implementation maintains backward compatibility:
- Existing code that calls `jump_dialog.show(directory)` without the `file_operations` parameter will continue to work
- In this case, all directories are included (previous behavior)
- New code should pass the `file_operations` reference for consistent behavior

## Testing

### Unit Tests
- `test/test_jump_dialog_hidden_files.py`: Comprehensive tests for the hidden files functionality
- Tests cover both `show_hidden = True` and `show_hidden = False` scenarios
- Tests verify fallback behavior when no `file_operations` reference is provided

### Demo
- `demo/demo_jump_dialog_hidden_files.py`: Interactive demonstration of the feature
- Creates test directory structure with hidden and visible directories
- Shows behavior differences between settings

## Benefits

1. **Consistency**: JumpDialog behavior now matches main file pane behavior
2. **User Control**: Users can control hidden directory visibility in navigation
3. **Performance**: Filtering hidden directories can improve performance in directories with many hidden files
4. **Security**: Reduces accidental navigation to sensitive hidden directories when not needed
5. **Context Awareness**: Smart filtering allows normal navigation within hidden directories while still protecting against accidental entry
6. **Developer Friendly**: When working in hidden directories (like `.git/`, `.config/`), navigation works naturally

## Technical Notes

### Thread Safety
The implementation maintains thread safety for the directory scanning operation:
- The `show_hidden` setting is read once when starting the scan
- Directory filtering is performed in the worker thread
- No race conditions between setting changes and scanning

### Performance Impact
- Minimal performance impact when `show_hidden = True` (no filtering)
- Slight performance improvement when `show_hidden = False` due to fewer directories processed
- Filtering is done during scanning, not after, for optimal performance

### Error Handling
- Graceful handling of permission errors during directory scanning
- Fallback behavior ensures functionality even without `file_operations` reference
- No crashes or exceptions when encountering inaccessible directories