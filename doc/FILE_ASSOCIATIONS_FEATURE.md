# File Extension Associations Feature

## Overview

The File Extension Associations feature allows you to configure which programs TFM uses to open, view, and edit different types of files based on their extensions. This provides a flexible way to customize how TFM handles various file types.

## Quick Start

### What is it?

File associations let you configure which programs TFM uses to open, view, and edit different file types. For example, you can use Preview for viewing images but Photoshop for editing them.

### Basic Example

Add this to your `~/.tfm/config.py`:

```python
FILE_ASSOCIATIONS = [
    # Images: Multiple patterns, Preview for viewing, Photoshop for editing
    {
        'pattern': ['*.jpg', '*.jpeg', '*.png', '*.gif'],
        'open|view': ['open', '-a', 'Preview'],  # Same for open and view
        'edit': ['open', '-a', 'Photoshop']
    },
    
    # Videos: QuickTime for viewing, Final Cut for editing
    {
        'pattern': ['*.mp4', '*.mov'],
        'open|view': ['open', '-a', 'QuickTime Player'],
        'edit': ['open', '-a', 'Final Cut Pro']
    },
    
    # PDFs: Preview for viewing, Acrobat for editing
    {
        'pattern': '*.pdf',
        'open|view': ['open', '-a', 'Preview'],
        'edit': ['open', '-a', 'Adobe Acrobat']
    }
]
```

## Configuration

File associations are configured in your `~/.tfm/config.py` file using the `FILE_ASSOCIATIONS` list.

### Compact Format Structure

```python
FILE_ASSOCIATIONS = [
    {
        'pattern': '*.ext' or ['*.ext1', '*.ext2'],  # Single or multiple
        'open|view': ['command', 'args'],  # Combined actions
        'edit': ['command', 'args']        # Separate action
    }
]
```

### Key Features

1. **Multiple patterns**: Group related patterns in a list
2. **Combined actions**: Use `|` to assign same command to multiple actions
3. **Flexible format**: Single pattern as string, multiple as list

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

### Compact Format Features

#### 1. Multiple Patterns

Group related file patterns together:

```python
{
    'pattern': ['*.jpg', '*.jpeg', '*.png', '*.gif']
}
```

Instead of repeating the same configuration for each extension.

#### 2. Combined Actions

Use the pipe `|` operator to assign the same command to multiple actions:

```python
{
    'open|view': ['open', '-a', 'Preview']
}
```

This clearly shows that open and view use the same program, making the intent explicit.

#### 3. Flexible Pattern Format

Single pattern as string:
```python
'pattern': '*.pdf'
```

Multiple patterns as list:
```python
'pattern': ['*.mp4', '*.mov', '*.avi']
```

### Format Comparison

**Old Format (Verbose)**:
```python
FILE_ASSOCIATIONS = {
    '*.jpg': {
        'open': ['open', '-a', 'Preview'],
        'view': ['open', '-a', 'Preview'],
        'edit': ['open', '-a', 'Photoshop']
    },
    '*.jpeg': {
        'open': ['open', '-a', 'Preview'],
        'view': ['open', '-a', 'Preview'],
        'edit': ['open', '-a', 'Photoshop']
    },
    # ... repeat for each extension
}
```

**New Format (Compact)**:
```python
FILE_ASSOCIATIONS = [
    {
        'pattern': ['*.jpg', '*.jpeg', '*.png', '*.gif'],
        'open|view': ['open', '-a', 'Preview'],
        'edit': ['open', '-a', 'Photoshop']
    }
]
```

**Reduction**: 75% fewer lines!

## Priority Matching

FILE_ASSOCIATIONS entries are checked in order from top to bottom. This allows you to define specific rules before general rules, giving you fine-grained control over file handling.

### How It Works

When TFM needs to find a program for a file and action:

1. **Check each entry** in FILE_ASSOCIATIONS from top to bottom
2. **For each entry**:
   - Check if the filename matches the pattern
   - If pattern matches, check if the action exists in that entry
   - If action exists, use that command (even if None)
   - If action doesn't exist, continue to next entry
3. **Stop at first match** where both pattern and action are found

### Key Principle

**First matching entry wins** - but only if the action is present in that entry.

### Priority Examples

#### Example 1: Specific Before General

```python
FILE_ASSOCIATIONS = [
    # Specific: Test files
    {
        'pattern': 'test_*.py',
        'open': ['pytest', '-v'],
        'edit': ['vim']
    },
    # General: All Python files
    {
        'pattern': '*.py',
        'open': ['python3'],
        'view': ['less'],
        'edit': ['vim']
    }
]
```

**Behavior**:
- `test_main.py` + open → `pytest -v` (matches first entry)
- `test_main.py` + view → `less` (first entry has no 'view', uses second entry)
- `script.py` + open → `python3` (doesn't match first pattern, uses second entry)

#### Example 2: README Files

```python
FILE_ASSOCIATIONS = [
    # Specific: README files with special viewer
    {
        'pattern': 'README*',
        'view': ['glow']  # Markdown renderer
    },
    # General: All markdown files
    {
        'pattern': '*.md',
        'open': ['typora'],
        'view': ['less'],
        'edit': ['vim']
    }
]
```

**Behavior**:
- `README.md` + view → `glow` (matches first entry)
- `README.md` + open → `typora` (first entry has no 'open', uses second entry)
- `notes.md` + view → `less` (doesn't match first pattern, uses second entry)

### Best Practices for Priority

1. **Specific Patterns First**: Always put more specific patterns before general ones
2. **Document Your Intent**: Add comments to explain why entries are ordered
3. **Test Your Configuration**: Verify that files match the expected patterns

## Usage in TFM

Once configured, TFM will use these associations when you:

1. Select a file and choose an action (open, view, or edit)
2. Use keyboard shortcuts for file operations
3. Use the file context menu

### Key Bindings

#### Enter Key - Open File
When you press Enter on a file, TFM uses the **open** action from file associations.

**Behavior**:
1. Checks file associations for 'open' action
2. If found, launches the configured program
3. If not found, falls back to built-in text viewer for text files
4. Otherwise, shows file info dialog

#### V Key - View File
When you press V on a file, TFM uses the **view** action from file associations.

**Behavior**:
1. Checks file associations for 'view' action
2. If found, launches the configured viewer
3. If not found, checks if file is a text file using `is_text_file()`
4. If it's a text file, opens built-in text viewer
5. Otherwise, shows "No viewer configured" message

#### E Key - Edit File
When you press E on a file, TFM uses the **edit** action from file associations.

**Behavior**:
1. Checks file associations for 'edit' action
2. If found, launches the configured editor
3. If not found, falls back to TEXT_EDITOR config setting
4. Shows error if no editor is configured

### Usage Examples

#### Images - Same Viewer, Different Editor

```python
{
    'pattern': ['*.jpg', '*.png'],
    'open|view': ['open', '-a', 'Preview'],  # Same for both
    'edit': ['open', '-a', 'Photoshop']      # Different editor
}
```

**Usage**:
- Press Enter on `photo.jpg` → Opens in Preview
- Press V on `photo.jpg` → Opens in Preview (same as Enter)
- Press E on `photo.jpg` → Opens in Photoshop

#### Videos - Viewer Only

```python
{
    'pattern': '*.avi',
    'open|view': ['open', '-a', 'VLC'],
    'edit': None  # No editor configured
}
```

**Usage**:
- Press Enter on `movie.avi` → Opens in VLC
- Press V on `movie.avi` → Opens in VLC
- Press E on `movie.avi` → Shows "No editor configured" message

#### Text Files - Built-in Viewer for View Action

```python
{
    'pattern': '*.txt',
    'open': ['open', '-e'],      # TextEdit
    'edit': ['vim']              # Terminal editor
    # 'view' omitted - will use built-in text viewer
}
```

**Usage**:
- Press Enter on `readme.txt` → Opens in TextEdit
- Press V on `readme.txt` → Opens in built-in text viewer (with syntax highlighting)
- Press E on `readme.txt` → Opens in vim

**Note**: Omitting the `view` action allows TFM to use the built-in text viewer for text files, which provides syntax highlighting and is optimized for viewing code and text files.

### Fallback Behavior

If a file has no configured association:

1. **Enter key**: Falls back to text viewer for text files, otherwise shows file info
2. **V key**: Checks if file is a text file first
   - If text file: Opens in built-in text viewer
   - If not text file: Shows "No viewer configured" error
3. **E key**: Falls back to TEXT_EDITOR config setting

## Examples

### Image Files

Group multiple image extensions and use the same program for opening and viewing:

```python
{
    'pattern': ['*.jpg', '*.jpeg', '*.png', '*.gif'],
    'open|view': ['open', '-a', 'Preview'],
    'edit': ['open', '-a', 'Photoshop']
}
```

### Video Files

```python
{
    'pattern': ['*.mp4', '*.mov'],
    'open|view': ['open', '-a', 'QuickTime Player'],
    'edit': ['open', '-a', 'Final Cut Pro']
},
{
    'pattern': '*.avi',
    'open|view': ['open', '-a', 'VLC'],
    'edit': None  # No editor configured
}
```

### PDF Files

```python
{
    'pattern': '*.pdf',
    'open|view': ['open', '-a', 'Preview'],
    'edit': ['open', '-a', 'Adobe Acrobat']
}
```

### Text and Code Files

```python
{
    'pattern': '*.txt',
    'open': ['open', '-e'],  # TextEdit on macOS
    'edit': ['vim']
    # 'view' omitted - uses built-in text viewer
},
{
    'pattern': ['*.py', '*.js'],
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
        'pattern': ['*.jpg', '*.png'],
        'open|view': ['open', '-a', 'Preview'],
        'edit': ['open', '-a', 'Photoshop']
    })
elif platform.system() == 'Linux':
    FILE_ASSOCIATIONS.append({
        'pattern': ['*.jpg', '*.png'],
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

## Tips and Best Practices

1. **Same program for multiple actions**: It's common to use the same program for both 'open' and 'view' actions, especially for media files.

2. **Specialized editors**: Use the 'edit' action for specialized editing software that's different from your viewing application.

3. **No action available**: Set an action to `None` if you don't want that action available for a file type.

4. **Test your commands**: Make sure the commands work from your terminal before adding them to the configuration.

5. **Use absolute paths**: If a program isn't in your PATH, use the absolute path to the executable.

6. **Specific patterns first**: Always put more specific patterns before general ones in your configuration.

7. **Document your intent**: Add comments to explain why entries are ordered a certain way.

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
- Check the order of entries (specific before general)

### Action not available

If an action doesn't appear:
- Check that the action is configured (not set to `None`)
- Verify the file extension matches a configured pattern
- Check for typos in the configuration

### Pattern Not Matching

If a file doesn't match the expected pattern:
- Remember patterns are checked in order from top to bottom
- More specific patterns should come before general patterns
- Check that the pattern syntax is correct (use `*.ext` format)

## Testing Your Configuration

Run the demo to see your associations:

```bash
python3 demo/demo_file_associations.py
```

Run the test to verify everything works:

```bash
python3 test/test_file_associations.py
```

## Related Documentation

- Implementation details: `doc/dev/FILE_ASSOCIATIONS_IMPLEMENTATION.md`
- TFM User Guide: `doc/TFM_USER_GUIDE.md`
