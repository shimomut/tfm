# Using Built-in Text Viewer with File Associations

## Overview

TFM's file association system supports using `None` as a special value to explicitly indicate that the built-in text viewer should be used for an action. This is particularly useful for text and code files where you want syntax highlighting and TFM's optimized viewing experience.

## The None Value

### Meaning

When you set an action to `None` in FILE_ASSOCIATIONS:
- It explicitly tells TFM to use the built-in text viewer
- It's different from having no association at all
- It only works for text files (checked via `is_text_file()`)

### Example

```python
{
    'extensions': ['*.txt', '*.md', '*.py', '*.js'],
    'open': ['open', '-a', 'Visual Studio Code'],
    'view': None,  # Use built-in text viewer
    'edit': ['vim']
}
```

## Why Use None?

### Benefits of Built-in Text Viewer

1. **Syntax Highlighting**: Automatic syntax highlighting for many languages
2. **Fast**: No external program launch overhead
3. **Consistent**: Same viewing experience across all text files
4. **Integrated**: Seamless integration with TFM's UI
5. **Remote Files**: Works with S3 and other remote file systems

### When to Use None

Use `None` for the view action when:
- You want syntax highlighting for code files
- You prefer TFM's integrated viewer over external programs
- You're viewing remote files (S3, etc.)
- You want fast, lightweight viewing without launching external apps

### When to Use External Programs

Use explicit commands when:
- You need advanced features (like `less` search capabilities)
- You prefer a specific external viewer
- The file format requires specialized rendering

## Configuration Examples

### Code Files - Built-in Viewer

```python
{
    'extensions': ['*.py', '*.js', '*.java', '*.cpp'],
    'open': ['open', '-a', 'Visual Studio Code'],
    'view': None,  # Built-in viewer with syntax highlighting
    'edit': ['vim']
}
```

**Result**: Press V on `script.py` → Opens in TFM's built-in viewer with Python syntax highlighting

### Markdown Files - Built-in Viewer

```python
{
    'extensions': '*.md',
    'open': ['open', '-a', 'Typora'],  # Rich markdown editor
    'view': None,  # Built-in viewer for quick viewing
    'edit': ['vim']
}
```

**Result**: Press V on `README.md` → Opens in TFM's built-in viewer with markdown highlighting

### Mixed Approach

```python
# Use built-in viewer for some text files
{
    'extensions': ['*.txt', '*.log'],
    'view': None  # Built-in viewer
},
# Use external viewer for others
{
    'extensions': '*.json',
    'view': ['jq', '.']  # External JSON formatter
}
```

## None vs No Association

### Important Distinction

There are three different scenarios:

1. **Explicit Command**: `'view': ['less']`
   - Uses the specified external program

2. **Explicit None**: `'view': None`
   - Uses built-in text viewer (if file is text)
   - Shows error if file is not text

3. **No Association**: File extension not in FILE_ASSOCIATIONS
   - Checks if file is text
   - If text: Uses built-in viewer (fallback)
   - If not text: Shows "No viewer configured" error

### Example Comparison

```python
# Configuration
FILE_ASSOCIATIONS = [
    {
        'extensions': '*.txt',
        'view': None  # Explicit None
    }
    # *.xyz has no association
]
```

**Behavior**:

| File | Association | Is Text? | Result |
|------|-------------|----------|--------|
| `readme.txt` | Explicit None | Yes | Built-in viewer |
| `readme.txt` | Explicit None | N/A | Built-in viewer (always for None) |
| `data.xyz` | No association | Yes | Built-in viewer (fallback) |
| `data.xyz` | No association | No | Error: No viewer configured |

## Implementation Details

### How TFM Handles None

When you press V on a file:

```
1. Check FILE_ASSOCIATIONS for 'view' action
   ↓
2. Found explicit command? → Launch external program
   ↓
3. Found explicit None? → Check if text file
   ↓                         ├─ Yes → Built-in viewer
   ↓                         └─ No → Error
   ↓
4. No association? → Check if text file
                     ├─ Yes → Built-in viewer (fallback)
                     └─ No → Error
```

### Helper Functions

```python
# Check if action has a command
has_action_for_file('readme.txt', 'view')
# Returns: False (None is not a command)

# Check if action has explicit association (including None)
has_explicit_association('readme.txt', 'view')
# Returns: True (None is an explicit association)
```

## Default Configuration

TFM's default configuration uses `None` for common text and code files:

```python
FILE_ASSOCIATIONS = [
    # Text files
    {
        'extensions': '*.txt',
        'open': ['open', '-e'],
        'view': None,  # Built-in viewer
        'edit': ['vim']
    },
    # Markdown
    {
        'extensions': '*.md',
        'open': ['open', '-a', 'Typora'],
        'view': None,  # Built-in viewer
        'edit': ['vim']
    },
    # Code files
    {
        'extensions': ['*.py', '*.js'],
        'open': ['open', '-a', 'Visual Studio Code'],
        'view': None,  # Built-in viewer
        'edit': ['vim']
    }
]
```

## Customization

### Override to Use External Viewer

If you prefer external viewers, change `None` to a command:

```python
{
    'extensions': ['*.py', '*.js'],
    'view': ['less', '-R']  # Use less with color support
}
```

### Add More File Types

Extend the configuration with more file types:

```python
{
    'extensions': ['*.c', '*.h', '*.cpp', '*.hpp'],
    'view': None  # Built-in viewer for C/C++ files
}
```

## Tips

1. **Start with None**: For text files, start with `None` and switch to external viewers only if needed
2. **Syntax Highlighting**: The built-in viewer supports many languages automatically
3. **Performance**: Built-in viewer is faster than launching external programs
4. **Consistency**: Using `None` provides consistent viewing experience across file types

## Related Documentation

- File Associations: `doc/FILE_ASSOCIATIONS_FEATURE.md`
- View Behavior: `doc/VIEW_FILE_BEHAVIOR.md`
- Text Viewer: `doc/dev/TEXT_VIEWER_SYSTEM.md`
