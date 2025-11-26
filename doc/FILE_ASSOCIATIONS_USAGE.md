# Using File Associations in TFM

## Overview

TFM now uses the file associations system to determine which programs to use when opening, viewing, or editing files. This provides a consistent and configurable way to handle different file types.

## Key Bindings

### Enter Key - Open File
When you press Enter on a file, TFM uses the **open** action from file associations:

```python
# Example: Pressing Enter on 'photo.jpg'
# Uses: FILE_ASSOCIATIONS entry for *.jpg with 'open' action
# Result: Launches Preview app (on macOS)
```

**Behavior**:
1. Checks file associations for 'open' action
2. If found, launches the configured program
3. If not found, falls back to built-in text viewer for text files
4. Otherwise, shows file info dialog

### V Key - View File
When you press V on a file, TFM uses the **view** action from file associations:

```python
# Example: Pressing V on 'document.pdf'
# Uses: FILE_ASSOCIATIONS entry for *.pdf with 'view' action
# Result: Launches Preview app for viewing
```

**Behavior**:
1. Checks file associations for 'view' action
2. If found, launches the configured viewer
3. If not found, checks if file is a text file using `is_text_file()`
4. If it's a text file, opens built-in text viewer
5. Otherwise, shows "No viewer configured" message

### E Key - Edit File
When you press E on a file, TFM uses the **edit** action from file associations:

```python
# Example: Pressing E on 'script.py'
# Uses: FILE_ASSOCIATIONS entry for *.py with 'edit' action
# Result: Launches vim editor
```

**Behavior**:
1. Checks file associations for 'edit' action
2. If found, launches the configured editor
3. If not found, falls back to TEXT_EDITOR config setting
4. Shows error if no editor is configured

## Configuration Examples

### Images - Same Viewer, Different Editor

```python
{
    'extensions': ['*.jpg', '*.png'],
    'open|view': ['open', '-a', 'Preview'],  # Same for both
    'edit': ['open', '-a', 'Photoshop']      # Different editor
}
```

**Usage**:
- Press Enter on `photo.jpg` → Opens in Preview
- Press V on `photo.jpg` → Opens in Preview (same as Enter)
- Press E on `photo.jpg` → Opens in Photoshop

### Videos - Viewer Only

```python
{
    'extensions': '*.avi',
    'open|view': ['open', '-a', 'VLC'],
    'edit': None  # No editor configured
}
```

**Usage**:
- Press Enter on `movie.avi` → Opens in VLC
- Press V on `movie.avi` → Opens in VLC
- Press E on `movie.avi` → Shows "No editor configured" message

### Text Files - Built-in Viewer for View Action

```python
{
    'extensions': '*.txt',
    'open': ['open', '-e'],      # TextEdit
    'view': None,                # Built-in text viewer
    'edit': ['vim']              # Terminal editor
}
```

**Usage**:
- Press Enter on `readme.txt` → Opens in TextEdit
- Press V on `readme.txt` → Opens in built-in text viewer (with syntax highlighting)
- Press E on `readme.txt` → Opens in vim

**Note**: Setting `view: None` explicitly tells TFM to use the built-in text viewer, which provides syntax highlighting and is optimized for viewing code and text files.

## Fallback Behavior

### Files Without Associations

If a file has no configured association:

1. **Enter key**: Falls back to text viewer for text files, otherwise shows file info
2. **V key**: Checks if file is a text file first
   - If text file: Opens in built-in text viewer
   - If not text file: Shows "No viewer configured" error
3. **E key**: Falls back to TEXT_EDITOR config setting

### Example

```python
# No association for *.xyz files

# Pressing Enter on 'data.xyz' (binary file)
# Result: Shows file info dialog (not a text file)

# Pressing V on 'data.xyz' (binary file)
# Result: "No viewer configured for 'data.xyz' (not a text file)"

# Pressing V on 'notes.xyz' (text file)
# Result: Opens in built-in text viewer (detected as text)

# Pressing E on 'data.xyz'
# Result: Opens in vim (TEXT_EDITOR fallback)
```

### Text File Detection

TFM uses the `is_text_file()` function to determine if a file is text:
- Checks file extension against known text extensions
- Reads file content to detect text encoding
- Falls back to built-in viewer only for confirmed text files

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

## Tips

1. **Use open|view for media files**: Most media files use the same program for opening and viewing
2. **Separate edit actions**: Use different programs for editing than viewing
3. **Test your associations**: Use the demo script to verify your configuration
4. **Fallback is available**: Don't worry about configuring every file type

## Troubleshooting

### Program Not Found

If you see "Editor not found" or similar errors:
- Check that the program is installed
- Verify the command name is correct
- Use full path if the program isn't in PATH

### Wrong Program Opens

If the wrong program opens:
- Check your FILE_ASSOCIATIONS configuration
- Verify the file extension matches the pattern
- Remember patterns are case-insensitive

### Action Not Working

If pressing a key does nothing:
- Check that the file has an association for that action
- Verify the action isn't set to None
- Check the log for error messages

## Related Documentation

- Configuration: `doc/FILE_ASSOCIATIONS_FEATURE.md`
- Quick Start: `doc/FILE_ASSOCIATIONS_QUICK_START.md`
- Compact Format: `doc/FILE_ASSOCIATIONS_COMPACT_FORMAT.md`
- Implementation: `doc/dev/FILE_ASSOCIATIONS_IMPLEMENTATION.md`
