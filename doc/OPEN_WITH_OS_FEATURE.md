# Open with OS and Reveal in File Manager Features

## Overview

TFM provides two convenient actions for interacting with the operating system's file management:

1. **Open with OS** - Opens files using the OS's default file associations
2. **Reveal in File Manager** - Opens the OS file manager and selects the focused file

These features allow quick access to system-level file operations without leaving TFM.

## Open with OS

### Usage

- **Keyboard**: `Command+Enter` (macOS) / `Ctrl+Enter` (Linux/Windows)
- **Menu**: File > Open with Default App

### Behavior

Opens selected files (or focused file if none selected) using the operating system's default application for each file type.

## Reveal in File Manager

### Usage

- **Keyboard**: `Alt+Enter`
- **Menu**: File > Reveal in File Manager

### Behavior

Opens the system file manager and reveals/selects the focused file or directory:
- **macOS**: Opens Finder and selects the item (both files and directories are revealed in their parent)
- **Windows**: Opens Explorer and selects the item (both files and directories are revealed in their parent)
- **Linux**: Opens the default file manager (nautilus, nemo, dolphin, etc.)

Note: This action always uses the focused item, not the selection. When a directory is focused, it will be revealed/selected in its parent directory (showing the directory as a selected item), not opened to show its contents.

## Comparison Table

| Feature | Open with OS | Reveal in File Manager |
|---------|-------------|------------------------|
| Shortcut | Command+Enter | Alt+Enter |
| Uses | Selected files or focused | Focused file only |
| Action | Opens files | Opens file manager |
| Multiple files | Yes | No (focused only) |

## Platform Support

Both features work across all supported platforms:
- **macOS**: Uses `open` and `open -R` commands
- **Linux**: Uses `xdg-open` and file manager detection
- **Windows**: Uses `start` and `explorer` commands

## Examples

### Opening Files with OS Default

1. Focus on a PDF file
2. Press `Command+Enter`
3. PDF opens in your default PDF viewer (e.g., Preview, Adobe Reader)

### Revealing File in File Manager

1. Focus on a file deep in a directory structure
2. Press `Alt+Enter`
3. Finder/Explorer opens with the file selected

### Opening Multiple Files

1. Select multiple image files using `Space`
2. Press `Command+Enter`
3. All images open in your default image viewer

## Comparison with TFM's Regular Open

| Feature | Regular Open (Cmd+O) | Open with OS (Cmd+Enter) | Reveal (Alt+Enter) |
|---------|---------------------|--------------------------|-------------------|
| Uses | TFM file associations | OS default associations | N/A |
| Configurable | Yes | No (system-wide) | No |
| Fallback | Built-in text viewer | None | None |
| Opens file manager | No | No | Yes |

## Tips

- Use `Command+Enter` when you want to quickly open files with system defaults
- Use `Alt+Enter` to locate a file in your file manager for further operations
- Use `Command+O` for consistent behavior based on TFM's configuration
- The reveal action is useful for drag-and-drop operations or accessing file context menus

## Related Features

- **File Associations**: Configure custom programs for file types in `_config.py`
- **View File** (`F3`): View files in TFM's built-in text viewer
- **Edit File** (`F4`): Edit files with TFM's configured editor
- **External Programs** (`Command+P`): Launch files with specific external programs
