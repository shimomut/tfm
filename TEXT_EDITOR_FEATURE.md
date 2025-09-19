# Text Editor Integration Feature

## Overview

The TFM (TUI File Manager) now includes integrated text editor support, allowing you to edit files directly from the file manager interface using your preferred text editor.

## Key Features

- **Seamless Integration**: Press 'e' or 'E' to edit the currently selected file
- **Curses Suspension**: The curses interface is properly suspended and resumed
- **Configurable Editor**: Choose your preferred text editor (vim, nano, emacs, VS Code, etc.)
- **Error Handling**: Graceful handling of missing editors or execution errors
- **Universal Support**: Works with any text editor that accepts file arguments

## Usage

1. **Navigate** to the file you want to edit using arrow keys
2. **Press 'e' or 'E'** to launch the text editor
3. **Edit** the file in your preferred editor
4. **Save and exit** the editor to return to TFM

## Configuration

### Default Editor
The default text editor is `vim`. You can change this in your configuration file.

### Configuring Your Editor
Edit `~/.tfm/config.py` and modify the `TEXT_EDITOR` setting:

```python
class Config:
    # Text editor settings
    TEXT_EDITOR = 'nano'  # Change to your preferred editor
```

### Popular Editor Options
- `vim` - Vi/Vim editor (default)
- `nano` - Nano editor (user-friendly)
- `emacs` - Emacs editor
- `code` - Visual Studio Code
- `subl` - Sublime Text
- `atom` - Atom editor
- `gedit` - GNOME Text Editor

## Implementation Details

### Curses Management
The implementation properly handles curses suspension and resumption:

```python
def suspend_curses(self):
    """Suspend the curses system to allow external programs to run"""
    curses.endwin()
    
def resume_curses(self):
    """Resume the curses system after external program execution"""
    self.stdscr.refresh()
    curses.curs_set(0)  # Hide cursor
    self.needs_full_redraw = True
```

### Editor Execution
The editor is launched as a subprocess with proper error handling:

```python
import subprocess
result = subprocess.run([editor, str(selected_file)], 
                      cwd=str(current_pane['path']))
```

### Key Binding
The feature is bound to the 'e' and 'E' keys by default, configurable via:

```python
KEY_BINDINGS = {
    'edit_file': ['e', 'E'],
    # ... other bindings
}
```

## Error Handling

The implementation includes comprehensive error handling:

- **Missing Editor**: If the configured editor is not found, an error message is displayed
- **Execution Errors**: If the editor exits with an error code, the exit code is reported
- **Exception Handling**: Any unexpected errors are caught and reported
- **Curses Recovery**: The curses interface is always properly restored, even after errors

## File Type Support

- **Any File Type**: The editor can be used on any file, not just text files
- **Directory Warning**: If you try to edit a directory, a warning is displayed
- **Parent Directory**: The parent directory (..) cannot be edited

## Benefits

1. **Productivity**: Edit files without leaving the file manager
2. **Flexibility**: Use any text editor you prefer
3. **Reliability**: Robust error handling and curses management
4. **Simplicity**: Single key press to edit files
5. **Integration**: Seamless workflow within TFM

## Technical Notes

- The feature uses `subprocess.run()` for editor execution
- Curses is properly suspended with `curses.endwin()`
- The working directory is set to the current pane's directory
- Full screen redraw is triggered after editor exit
- Log messages provide feedback on editor operations

## Future Enhancements

Potential future improvements could include:
- File type-specific editor associations
- Multiple editor profiles
- Editor command-line argument customization
- Integration with external diff tools
- Backup file creation before editing