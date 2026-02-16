# Open with OS Default Application Feature

## Overview

The "Open with OS" feature allows you to open files using your operating system's default file associations, bypassing TFM's configured file associations. This is useful when you want to quickly open a file with the system's preferred application without configuring TFM's file associations.

## Usage

### Keyboard Shortcut

- **macOS**: `Command+Enter`
- **Linux/Windows**: `Ctrl+Enter`

### Menu Access

Navigate to: **File > Open with Default App**

### Behavior

1. **Single File**: When no files are selected, pressing `Command+Enter` opens the focused file with the OS default application.

2. **Multiple Files**: When files are selected (using `Space`), pressing `Command+Enter` opens all selected files with their respective default applications.

3. **Directories**: Opening a directory with the default app will open it in your system's file manager (Finder on macOS, File Explorer on Windows, etc.).

## Comparison with Regular Open

TFM provides two ways to open files:

| Feature | Regular Open (`Command+O`) | Open with OS (`Command+Enter`) |
|---------|---------------------------|--------------------------------|
| Uses | TFM's file associations | OS default associations |
| Configurable | Yes (via `_config.py`) | No (system-wide) |
| Fallback | Built-in text viewer | None |
| Best for | Customized workflows | Quick system-default access |

## Examples

### Opening a PDF

- `Command+O`: Opens with the application configured in TFM (e.g., Preview)
- `Command+Enter`: Opens with your system's default PDF viewer

### Opening a Text File

- `Command+O`: Opens with TFM's configured text editor
- `Command+Enter`: Opens with your system's default text editor

### Opening Multiple Images

1. Select multiple image files using `Space`
2. Press `Command+Enter`
3. All images open in your default image viewer

## Platform Support

The feature works across all supported platforms:

- **macOS**: Uses the `open` command
- **Linux**: Uses `xdg-open`
- **Windows**: Uses the `start` command

## Tips

- Use `Command+Enter` when you want to quickly open a file without worrying about TFM's configuration
- Use `Command+O` when you want consistent behavior based on your TFM file associations
- Select multiple files and use `Command+Enter` to open them all at once
- This feature respects your system-wide file associations set in your OS preferences

## Related Features

- **File Associations**: Configure custom programs for file types in `_config.py`
- **View File** (`F3`): View files in TFM's built-in text viewer
- **Edit File** (`F4`): Edit files with TFM's configured editor
- **External Programs** (`Command+P`): Launch files with specific external programs
