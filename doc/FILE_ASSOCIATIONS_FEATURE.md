# File Extension Associations Feature

## Overview

The File Extension Associations feature allows you to configure which programs TFM uses to open, view, and edit different types of files based on their extensions. This provides a flexible way to customize how TFM handles various file types.

## Configuration

File associations are configured in your `~/.tfm/config.py` file using the `FILE_ASSOCIATIONS` list.

### Compact Format Structure

```python
FILE_ASSOCIATIONS = [
    {
        'extensions': '*.ext' or ['*.ext1', '*.ext2'],  # Single or multiple
        'open|view': ['command', 'args'],  # Combined actions
        'edit': ['command', 'args']        # Separate action
    }
]
```

### Key Features

1. **Multiple extensions**: Group related extensions in a list
2. **Combined actions**: Use `|` to assign same command to multiple actions
3. **Flexible format**: Single extension as string, multiple as list

### Actions

Each file extension can have up to three actions configured:

- **open**: Default action for opening the file (typically with the system default application)
- **view**: Action for viewing the file (typically read-only or quick preview)
- **edit**: Action for editing the file (typically with a specialized editor)

### Command Formats

Programs can be specified in two formats:

1. **Command list** (recommended):
   ```python
   'open': ['open', '-a', 'Preview']
   ```

2. **Command string** (automatically converted to list):
   ```python
   'open': 'open -a Preview'
   ```

3. **None** (action not available):
   ```python
   'edit': None  # No editor configured for this file type
   ```

## Examples

### Image Files (Compact Format)

Group multiple image extensions and use the same program for opening and viewing:

```python
{
    'extensions': ['*.jpg', '*.jpeg', '*.png', '*.gif'],
    'open|view': ['open', '-a', 'Preview'],
    'edit': ['open', '-a', 'Photoshop']
}
```

### Video Files

```python
{
    'extensions': ['*.mp4', '*.mov'],
    'open|view': ['open', '-a', 'QuickTime Player'],
    'edit': ['open', '-a', 'Final Cut Pro']
},
{
    'extensions': '*.avi',
    'open|view': ['open', '-a', 'VLC'],
    'edit': None  # No editor configured
}
```

### PDF Files

```python
{
    'extensions': '*.pdf',
    'open|view': ['open', '-a', 'Preview'],
    'edit': ['open', '-a', 'Adobe Acrobat']
}
```

### Text and Code Files

```python
{
    'extensions': '*.txt',
    'open': ['open', '-e'],  # TextEdit on macOS
    'edit': ['vim']
    # 'view' omitted - uses built-in text viewer
},
{
    'extensions': ['*.py', '*.js'],
    'open': ['open', '-a', 'Visual Studio Code'],
    'edit': ['vim']
    # 'view' omitted - uses built-in text viewer with syntax highlighting
}
```

## Pattern Matching

File associations use wildcard pattern matching:

- `*.pdf` - matches all PDF files
- `*.jpg` - matches all JPG files
- `*.tar.gz` - matches compressed tar archives

Pattern matching is case-insensitive, so `*.PDF` and `*.pdf` are treated the same.

## Platform-Specific Configuration

You can configure different programs for different platforms:

```python
import platform

FILE_ASSOCIATIONS = []

if platform.system() == 'Darwin':  # macOS
    FILE_ASSOCIATIONS.append({
        'extensions': ['*.jpg', '*.png'],
        'open|view': ['open', '-a', 'Preview'],
        'edit': ['open', '-a', 'Photoshop']
    })
elif platform.system() == 'Linux':
    FILE_ASSOCIATIONS.append({
        'extensions': ['*.jpg', '*.png'],
        'open': ['xdg-open'],
        'view': ['eog'],  # Eye of GNOME
        'edit': ['gimp']
    })
```

## Default Associations

TFM comes with default file associations for common file types:

- **Images**: JPG, JPEG, PNG, GIF
- **Videos**: MP4, MOV, AVI
- **Audio**: MP3, WAV
- **Documents**: PDF, TXT, MD
- **Code**: PY, JS

You can override any of these defaults in your configuration file.

## Usage in TFM

Once configured, TFM will use these associations when you:

1. Select a file and choose an action (open, view, or edit)
2. Use keyboard shortcuts for file operations
3. Use the file context menu

The appropriate program will be launched based on the file's extension and the action you choose.

## Tips

1. **Same program for multiple actions**: It's common to use the same program for both 'open' and 'view' actions, especially for media files.

2. **Specialized editors**: Use the 'edit' action for specialized editing software that's different from your viewing application.

3. **No action available**: Set an action to `None` if you don't want that action available for a file type.

4. **Test your commands**: Make sure the commands work from your terminal before adding them to the configuration.

5. **Use absolute paths**: If a program isn't in your PATH, use the absolute path to the executable.

## Troubleshooting

### Program not found

If TFM can't find the program:
- Check that the program is installed
- Verify the command name is correct
- Use the full path to the executable if needed

### Wrong program opens

If the wrong program opens:
- Check your pattern matches the file extension correctly
- Verify the pattern is case-insensitive
- Make sure there are no conflicting patterns

### Action not available

If an action doesn't appear:
- Check that the action is configured (not set to `None`)
- Verify the file extension matches a configured pattern
- Check for typos in the configuration
