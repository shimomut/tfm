# View File Behavior in TFM

## Overview

The `view_file` action (V key) in TFM uses a smart fallback system that prioritizes configured file associations but gracefully handles files without associations.

## Behavior Flow

```
User presses V on a file
    ↓
Check FILE_ASSOCIATIONS for 'view' action
    ↓
    ├─ Association found?
    │   ↓ YES
    │   Launch configured viewer program
    │   (e.g., Preview for PDFs, less for text files)
    │
    └─ Association NOT found (or explicitly None)?
        ↓ NO
        Open the built-in text viewer
        (TFM's internal viewer with syntax highlighting)
            ↓
            The viewer sniffs the file's bytes:
            ├─ Decodes as text?
            │   ↓ YES
            │   Show it, with syntax highlighting
            │
            └─ Binary?
                ↓ NO
                Show "[Binary file — cannot display as text]"
```

## Examples

### Files With Associations

```python
# Configuration
{
    'pattern': '*.pdf',
    'open|view': ['open', '-a', 'Preview'],
    'edit': ['open', '-a', 'Adobe Acrobat']
}
```

**User Action**: Press V on `document.pdf`
**Result**: Opens in Preview (configured viewer)

### Text Files With Associations

```python
# Configuration
{
    'pattern': '*.txt',
    'open': ['open', '-e'],
    'view': ['less'],
    'edit': ['vim']
}
```

**User Action**: Press V on `readme.txt`
**Result**: Opens in less (configured viewer)

### Text Files Without Associations

**User Action**: Press V on `notes.xyz` (text content)
**Result**: 
1. No association found for `*.xyz`
2. Opens in the built-in text viewer
3. The viewer decodes the file successfully and shows it

Note that the unknown `.xyz` extension does not matter — nothing consults it.

### Binary Files Without Associations

**User Action**: Press V on `data.bin` (binary content)
**Result**:
1. No association found for `*.bin`
2. Opens in the built-in text viewer
3. The viewer finds the file is binary and shows
   `[Binary file — cannot display as text]`

## Text File Detection

**TFM detects text by reading the bytes, not by looking at the extension.**
There is no list of "text extensions" anywhere in TFM, by design: any such list
is wrong for files with no extension (`Makefile`, `README`), an unknown one, or
a misleading one — and content inspection gets all three right for free.

The built-in viewer decides like this:

1. **Try to decode** the file as `utf-8`, then `latin-1`, then `cp1252`
2. **If none decode**, read the raw bytes and look for a NUL byte in the first
   1024 — a NUL means binary, and the placeholder is shown
3. **Otherwise** fall back to `latin-1` with replacement characters

Content search applies the same idea more cheaply: a NUL byte in the first 1024
bytes means "skip this file". The rule of thumb across TFM is **detect
capability from the bytes; configure preference by extension**. Extensions
decide *which application you prefer* (see
[File Associations](FILE_ASSOCIATIONS_FEATURE.md)) — never whether a file is
readable as text.

## Comparison with Other Actions

### Enter Key (Open)

```
Press Enter on file
    ↓
Check FILE_ASSOCIATIONS for 'open' action
    ↓
    ├─ Association found? → Launch program
    │
    └─ No association?
        ↓
        Check if text file
            ↓
            ├─ Is text? → Built-in text viewer
            └─ Not text? → Show file info dialog
```

### E Key (Edit)

```
Press E on file
    ↓
Check FILE_ASSOCIATIONS for 'edit' action
    ↓
    ├─ Association found? → Launch editor
    │
    └─ No association? → Use TEXT_EDITOR config
```

## Key Differences

| Action | With Association | Without Association (Text) | Without Association (Binary) |
|--------|-----------------|---------------------------|------------------------------|
| **Enter** | Configured program | Built-in viewer | File info dialog |
| **V (View)** | Configured viewer | Built-in viewer | Error message |
| **E (Edit)** | Configured editor | TEXT_EDITOR config | TEXT_EDITOR config |

## Configuration Tips

### Explicit Text File Associations

For better control, explicitly configure text file associations:

```python
{
    'pattern': ['*.txt', '*.log', '*.conf'],
    'open': ['open', '-e'],
    'view': ['less'],
    'edit': ['vim']
}
```

### Rely on Fallback for Unknown Text Files

For files with uncommon extensions, rely on the fallback:

```python
# No need to configure every text extension
# Files like *.xyz, *.custom, *.unknown will automatically
# use built-in viewer if they contain text
```

### Disable Fallback for Specific Extensions

To prevent viewing certain files, add explicit None:

```python
{
    'pattern': '*.dat',
    'open': None,
    'view': None,  # Prevents viewing even if text
    'edit': ['vim']
}
```

## Benefits

1. **Flexibility**: Handles both configured and unconfigured file types
2. **Safety**: Only opens text files in built-in viewer
3. **User-Friendly**: Clear error messages for unsupported files
4. **Efficient**: No need to configure every text file extension

## Troubleshooting

### Built-in Viewer Opens for Configured Files

**Problem**: Press V on `readme.txt`, built-in viewer opens instead of `less`

**Solution**: Check your FILE_ASSOCIATIONS configuration:
```python
# Make sure you have:
{
    'pattern': '*.txt',
    'view': ['less']  # Not None or missing
}
```

### Binary File Opens in Viewer

**Problem**: Binary file opens in built-in viewer showing garbage

**Solution**: The file is being detected as text. Add explicit association:
```python
{
    'pattern': '*.dat',
    'view': None  # Prevent viewing
}
```

### Text File Shows Error

**Problem**: Press V on text file, shows "No viewer configured"

**Solution**: File not detected as text. Check:
1. File has valid text encoding (UTF-8, ASCII)
2. File extension is recognized
3. File isn't too large

## Related Documentation

- File Associations: `doc/FILE_ASSOCIATIONS_FEATURE.md`
- Text Viewer: `doc/dev/TEXT_VIEWER_SYSTEM.md`
