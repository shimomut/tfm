# File Associations Quick Start

## What is it?

File associations let you configure which programs TFM uses to open, view, and edit different file types. For example, you can use Preview for viewing images but Photoshop for editing them.

## Quick Example (Compact Format)

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

## Compact Format Features

### 1. Multiple Patterns
Group related patterns together:
```python
{
    'pattern': ['*.jpg', '*.jpeg', '*.png'],  # Multiple fnmatch patterns
    'open|view': ['open', '-a', 'Preview'],
    'edit': ['open', '-a', 'Photoshop']
}
```

### 2. Combined Actions
Use `|` to assign the same command to multiple actions:
```python
{
    'pattern': '*.pdf',
    'open|view': ['open', '-a', 'Preview'],  # Same for both
    'edit': ['open', '-a', 'Acrobat']
}
```

### 3. Three Actions

Each file type can have three actions:
- **open**: Default action (usually system default app)
- **view**: Quick preview (usually read-only)
- **edit**: Full editing (specialized software)

### 4. Omit Actions

Simply omit an action if you want default behavior:
```python
{
    'pattern': '*.txt',
    'open': ['open', '-e'],
    'edit': ['vim']
    # 'view' omitted - will use built-in text viewer for text files
}
```

Or explicitly set to `None` to prevent the action:
```python
{
    'pattern': '*.avi',
    'open|view': ['open', '-a', 'VLC'],
    'edit': None  # No editor configured
}
```

## Testing Your Configuration

Run the demo to see your associations:

```bash
python3 demo/demo_file_associations.py
```

Run the test to verify everything works:

```bash
python3 test/test_file_associations.py
```

## More Information

- Full documentation: `doc/FILE_ASSOCIATIONS_FEATURE.md`
- Implementation details: `doc/dev/FILE_ASSOCIATIONS_IMPLEMENTATION.md`
