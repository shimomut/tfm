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

### Renderer Suspension
The implementation properly handles renderer suspension and resumption using the TTK Renderer API:

```python
# Suspend renderer to allow external program to run
self.renderer.suspend()

# Launch the editor
result = subprocess.run([editor, str(selected_file)], 
                      cwd=str(current_pane['path']))

# Resume renderer after editor exits
self.renderer.resume()
```

The `suspend()` and `resume()` methods are part of the TTK Renderer interface and work across all backends (curses, CoreGraphics, etc.). For the curses backend, this internally calls `curses.endwin()` and `curses.reset_prog_mode()` respectively.

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
- The renderer is properly suspended with `renderer.suspend()` before launching external programs
- The renderer is restored with `renderer.resume()` after the external program exits
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