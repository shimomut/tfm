# File Associations Quick Start

## What is it?

File associations let you configure which programs TFM uses to open, view, and edit different file types. For example, you can use Preview for viewing images but Photoshop for editing them.

## Quick Example (Compact Format)

Add this to your `~/.tfm/config.py`:

```python
FILE_ASSOCIATIONS = [
    # Images: Multiple extensions, Preview for viewing, Photoshop for editing
    {
        'extensions': ['*.jpg', '*.jpeg', '*.png', '*.gif'],
        'open|view': ['open', '-a', 'Preview'],  # Same for open and view
        'edit': ['open', '-a', 'Photoshop']
    },
    
    # Videos: QuickTime for viewing, Final Cut for editing
    {
        'extensions': ['*.mp4', '*.mov'],
        'open|view': ['open', '-a', 'QuickTime Player'],
        'edit': ['open', '-a', 'Final Cut Pro']
    },
    
    # PDFs: Preview for viewing, Acrobat for editing
    {
        'extensions': '*.pdf',
        'open|view': ['open', '-a', 'Preview'],
        'edit': ['open', '-a', 'Adobe Acrobat']
    }
]
```

## Compact Format Features

### 1. Multiple Extensions
Group related extensions together:
```python
{
    'extensions': ['*.jpg', '*.jpeg', '*.png'],  # Multiple extensions
    'open|view': ['open', '-a', 'Preview'],
    'edit': ['open', '-a', 'Photoshop']
}
```

### 2. Combined Actions
Use `|` to assign the same command to multiple actions:
```python
{
    'extensions': '*.pdf',
    'open|view': ['open', '-a', 'Preview'],  # Same for both
    'edit': ['open', '-a', 'Acrobat']
}
```

### 3. Three Actions

Each file type can have three actions:
- **open**: Default action (usually system default app)
- **view**: Quick preview (usually read-only)
- **edit**: Full editing (specialized software)

### 4. No Action Available

Set an action to `None` if you don't want it available:
```python
{
    'extensions': '*.avi',
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
