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
    └─ Association NOT found?
        ↓ NO
        Check if file is a text file (is_text_file)
            ↓
            ├─ Is text file?
            │   ↓ YES
            │   Open built-in text viewer
            │   (TFM's internal viewer with syntax highlighting)
            │
            └─ Is NOT text file?
                ↓ NO
                Show error: "No viewer configured"
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
2. Checks if file is text using `is_text_file()`
3. File is detected as text
4. Opens in built-in text viewer

### Binary Files Without Associations

**User Action**: Press V on `data.bin` (binary content)
**Result**:
1. No association found for `*.bin`
2. Checks if file is text using `is_text_file()`
3. File is NOT text
4. Shows error: "No viewer configured for 'data.bin' (not a text file)"

## Text File Detection

The `is_text_file()` function determines if a file is text by:

1. **Extension Check**: Checks against known text extensions
   - `.txt`, `.md`, `.py`, `.js`, `.json`, `.xml`, `.html`, etc.

2. **Content Analysis**: Reads file content to detect encoding
   - Checks for valid UTF-8 or ASCII encoding
   - Detects binary content patterns

3. **Size Limits**: Very large files may be skipped for performance

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
- Usage Guide: `doc/FILE_ASSOCIATIONS_USAGE.md`
- Text Viewer: `doc/dev/TEXT_VIEWER_SYSTEM.md`
