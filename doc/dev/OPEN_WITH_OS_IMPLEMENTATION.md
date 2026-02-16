# Open with OS and Reveal in File Manager - Implementation

## Overview

This document describes the implementation of two related features:
1. **Open with OS** - Opens files using the operating system's default file associations
2. **Reveal in File Manager** - Opens the OS file manager and selects the focused file

## Architecture

### Components Modified

1. **Menu Manager** (`src/tfm_menu_manager.py`)
   - Added `FILE_OPEN_WITH_OS` menu item constant
   - Added `FILE_REVEAL_IN_FILE_MANAGER` menu item constant
   - Added both menu items to File menu with keyboard shortcuts

2. **Main Application** (`src/tfm_main.py`)
   - Added `platform` module import
   - Added `_action_open_with_os()` method
   - Added `_action_reveal_in_file_manager()` method
   - Added menu event handlers for both actions
   - Added keyboard action handlers for both actions

3. **Configuration** (`src/_config.py`)
   - Added `open_with_os` keyboard action with `Command-ENTER` binding
   - Added `reveal_in_file_manager` keyboard action with `Alt-ENTER` binding

## Implementation Details

### Open with OS Action

```python
def _action_open_with_os(self):
    """Open the selected file(s) or directory with OS default application."""
```

The method:
1. Gets the current pane
2. Determines which files to open (selected files or focused file)
3. Detects the operating system using `platform.system()`
4. Calls the appropriate OS command for each file:
   - macOS: `open <file>`
   - Linux: `xdg-open <file>`
   - Windows: `start "" <file>`
5. Logs success or error messages
6. Marks the UI as dirty for redraw

### Reveal in File Manager Action

```python
def _action_reveal_in_file_manager(self):
    """Reveal the focused file in OS file manager (Finder/Explorer)."""
```

The method:
1. Gets the current pane
2. Uses only the focused file (ignores selection)
3. Detects the operating system
4. Calls the appropriate OS command:
   - macOS: `open -R <item>` (reveals/selects item in Finder, works for both files and directories)
   - Linux: Tries common file managers with `--select` flag, falls back to opening parent directory
   - Windows: `explorer /select, <item>` (selects item in Explorer, works for both files and directories)
5. Logs success or error messages
6. Marks the UI as dirty for redraw

Note: For all platforms, directories are revealed/selected in their parent directory, not opened.

### Error Handling

The implementation includes comprehensive error handling:

- **CalledProcessError**: Logged when the subprocess command fails
- **Generic Exception**: Catches any unexpected errors
- **Unsupported Platform**: Logs error and returns gracefully
- **Empty Pane**: Returns immediately without error

### Platform Detection

Uses Python's `platform.system()` which returns:
- `'Darwin'` for macOS
- `'Linux'` for Linux
- `'Windows'` for Windows

### Keyboard Shortcut Binding

The keyboard shortcut is defined in `_config.py`:

```python
'open_with_os': ['Command-ENTER'],  # Open file(s) with OS default application
```

The action is handled in `handle_main_screen_key_event()`:

```python
elif action == 'open_with_os':
    self._action_open_with_os()
    return True
```

### Menu Integration

The menu item is added to the File menu in `_build_file_menu()`:

```python
{
    'id': self.FILE_OPEN_WITH_OS,
    'label': 'Open with Default App',
    'shortcut': f'{modifier}+Enter',
    'enabled': True
}
```

The menu event is handled in `_handle_menu_event()`:

```python
elif item_id == MenuManager.FILE_OPEN_WITH_OS:
    return self._action_open_with_os()
```

## Design Decisions

### Multiple File Support

The feature supports opening multiple selected files in a single action. This is consistent with other file operations in TFM and provides a convenient way to open several files at once.

### No Renderer Suspension

Unlike the regular "Open" action which may suspend the renderer for interactive programs, this feature does not suspend the renderer because:
1. OS default applications typically launch in separate windows
2. The commands (`open`, `xdg-open`, `start`) return immediately
3. No terminal interaction is required

### Logging

All operations are logged using the unified logging system:
- **INFO**: Successful file opening
- **ERROR**: Command failures, unsupported platforms, exceptions

### Cross-Platform Compatibility

The implementation uses standard OS commands that are available by default:
- macOS: `open` (built-in)
- Linux: `xdg-open` (part of xdg-utils, typically pre-installed)
- Windows: `start` (built-in)

## Testing

### Unit Tests

Location: `test/test_open_with_os.py`

Test coverage includes:
- Opening single file on each platform (macOS, Linux, Windows)
- Opening multiple selected files
- Error handling for command failures
- Unsupported platform handling
- Empty pane handling

### Demo Script

Location: `demo/demo_open_with_os.py`

The demo creates a temporary directory with various file types and launches TFM for interactive testing.

## Future Enhancements

Potential improvements:
1. Add configuration option to customize the command per platform
2. Support for opening files with specific applications (e.g., "Open with...")
3. Integration with recent applications list
4. Async execution for better responsiveness with many files

## Related Code

- **File Associations**: `src/_config.py` - `FILE_ASSOCIATIONS` configuration
- **Regular Open**: `FileManager.handle_enter()` - Uses TFM's file associations
- **External Programs**: `src/tfm_external_programs.py` - Custom program execution
- **View/Edit**: `FileManager._action_view_file()`, `_action_edit_file()`

## References

- User Documentation: `doc/OPEN_WITH_OS_FEATURE.md`
- Menu System: `doc/dev/MENU_SYSTEM.md` (if exists)
- Keyboard Actions: `src/_config.py` - `KEY_BINDINGS`
