# File Extension Associations Implementation

## Overview

The file extension associations system provides a flexible mechanism for mapping file extensions to programs for different actions (open, view, edit). This document describes the implementation details for developers.

## Architecture

### Configuration Storage

File associations are stored in the configuration system as a list of dictionaries (compact format):

```python
FILE_ASSOCIATIONS = [
    {
        'pattern': '*.pdf' or ['*.jpg', '*.png'],
        'open|view': ['command'],  # Combined actions
        'edit': ['command']
    }
]
```

Where:
- `extensions`: Single pattern string or list of patterns (e.g., `'*.pdf'` or `['*.jpg', '*.png']`)
- Action keys: `'open'`, `'view'`, `'edit'`, or combined like `'open|view'`
- `command`: Command list, command string, or `None`

### Compact Format Benefits

1. **Reduced duplication**: Group related extensions together
2. **Clearer intent**: Combined actions show when programs are shared
3. **More maintainable**: Fewer entries to update
4. **Backward compatible**: Old format can be converted if needed

### Location

File associations are defined in two places:

1. **DefaultConfig** (`src/tfm_config.py`): Default associations
2. **User Config** (`~/.tfm/config.py`): User-customized associations

User config takes precedence over default config.

## Implementation Details

### Core Functions

#### `get_file_associations()`

Returns the file associations list from configuration.

```python
def get_file_associations():
    """Get the file extension associations from configuration"""
    config = get_config()
    
    if hasattr(config, 'FILE_ASSOCIATIONS') and config.FILE_ASSOCIATIONS:
        return config.FILE_ASSOCIATIONS
    elif hasattr(DefaultConfig, 'FILE_ASSOCIATIONS'):
        return DefaultConfig.FILE_ASSOCIATIONS
    
    return []
```

**Returns**: List of file association entries or empty list if none configured.

#### `_expand_association_entry(entry)`

Internal function that expands a compact association entry into individual pattern-action mappings.

```python
def _expand_association_entry(entry):
    """
    Expand a compact association entry into individual pattern-action mappings.
    
    Args:
        entry: Dictionary with 'extensions' key and action keys
    
    Returns:
        List of (pattern, action, command) tuples
    """
```

**Algorithm**:
1. Extract extensions (convert string to list if needed)
2. Iterate through action keys (skip 'extensions')
3. Split combined action keys (e.g., 'open|view' → ['open', 'view'])
4. Generate tuple for each (extension, action, command) combination

**Returns**: List of `(pattern, action, command)` tuples

#### `get_program_for_file(filename, action='open')`

Retrieves the program command for a specific file and action.

```python
def get_program_for_file(filename, action='open'):
    """
    Get the program command for a specific file and action.
    
    Args:
        filename: The filename to check (e.g., 'document.pdf')
        action: The action to perform ('open', 'view', or 'edit')
    
    Returns:
        Command list if found, None otherwise
    """
```

**Algorithm**:
1. Get file associations list from config
2. Convert filename to lowercase for case-insensitive matching
3. For each entry, expand using `_expand_association_entry()`
4. Match pattern and action using `fnmatch.fnmatch()`
5. Return first matching program command
6. Convert string commands to list format
7. Return `None` if no match found

**Returns**: Command list `['program', 'arg1', 'arg2']` or `None`

#### `has_action_for_file(filename, action='open')`

Checks if a specific action is available for a file.

```python
def has_action_for_file(filename, action='open'):
    """
    Check if a specific action is available for a file.
    
    Args:
        filename: The filename to check
        action: The action to check ('open', 'view', or 'edit')
    
    Returns:
        True if the action is available, False otherwise
    """
```

**Returns**: Boolean indicating if action is available

### Pattern Matching

Pattern matching uses Python's `fnmatch` module:

```python
import fnmatch

if fnmatch.fnmatch(filename_lower, pattern.lower()):
    # Pattern matches
```

**Features**:
- Case-insensitive matching
- Wildcard support (`*`, `?`, `[seq]`, `[!seq]`)
- Standard Unix shell-style wildcards

**Examples**:
- `*.pdf` matches `document.pdf`, `file.PDF`
- `*.tar.gz` matches `archive.tar.gz`
- `image_*.jpg` matches `image_001.jpg`, `image_photo.jpg`

### Command Format Handling

Commands can be specified in multiple formats:

1. **List format** (preferred):
   ```python
   ['open', '-a', 'Preview']
   ```

2. **String format** (converted to list):
   ```python
   'open -a Preview'  # Converted to ['open', '-a', 'Preview']
   ```

3. **None** (action not available):
   ```python
   None  # Action not configured
   ```

The `get_program_for_file()` function normalizes all formats to list format or `None`.

## Integration Points

### Configuration System

File associations integrate with the existing configuration system:

1. **DefaultConfig class**: Provides default associations
2. **User Config class**: Allows user customization
3. **ConfigManager**: Handles loading and merging

### Usage in TFM

Components that should use file associations:

1. **File operations**: Open, view, edit actions
2. **Context menus**: Show available actions for files
3. **Keyboard shortcuts**: Execute actions based on file type
4. **External programs**: Launch appropriate programs

Example integration:

```python
from tfm_config import get_program_for_file, has_action_for_file

# Check if action is available
if has_action_for_file('document.pdf', 'view'):
    # Get the program command
    command = get_program_for_file('document.pdf', 'view')
    # Execute the command
    subprocess.run(command + ['document.pdf'])
```

## Data Structures

### FILE_ASSOCIATIONS List (Compact Format)

```python
[
    {
        'pattern': '*.pdf',
        'open|view': ['open', '-a', 'Preview'],
        'edit': ['open', '-a', 'Adobe Acrobat']
    },
    {
        'pattern': ['*.jpg', '*.jpeg', '*.png'],
        'open|view': ['open', '-a', 'Preview'],
        'edit': ['open', '-a', 'Photoshop']
    }
]
```

**Structure**:
- Top-level: List of association entries
- Each entry: Dictionary with 'extensions' key and action keys
- 'pattern': String or list of extension patterns
- Action keys: 'open', 'view', 'edit', or combined like 'open|view'
- Values: Command lists, command strings, or None

**Expansion Example**:
```python
{
    'pattern': ['*.jpg', '*.png'],
    'open|view': ['preview']
}
```
Expands to:
- `('*.jpg', 'open', ['preview'])`
- `('*.jpg', 'view', ['preview'])`
- `('*.png', 'open', ['preview'])`
- `('*.png', 'view', ['preview'])`

## Performance Considerations

### Pattern Matching Performance

- Pattern matching is O(n*m) where n is number of entries and m is average extensions per entry
- First match wins (no priority system)
- Case conversion happens once per lookup
- Entry expansion happens on each lookup

**Optimization opportunities**:
- Cache expanded entries (pre-expand on config load)
- Cache pattern matching results
- Pre-compile patterns for faster matching
- Use more specific patterns first

### Memory Usage

- Associations stored in memory once at config load
- No significant memory overhead
- Command lists are small (typically 2-5 elements)

## Error Handling

### Missing Configuration

If `FILE_ASSOCIATIONS` is not defined:
- `get_file_associations()` returns empty dict
- `get_program_for_file()` returns `None`
- `has_action_for_file()` returns `False`

### Invalid Configuration

Invalid configurations are handled gracefully:

1. **Invalid pattern**: Skipped during matching
2. **Invalid action**: Returns `None` for that action
3. **Invalid command**: Returned as-is (will fail at execution)

### No Match Found

If no pattern matches:
- `get_program_for_file()` returns `None`
- `has_action_for_file()` returns `False`
- Caller should handle fallback behavior

## Testing

### Unit Tests

Test cases should cover:

1. **Pattern matching**:
   - Case-insensitive matching
   - Wildcard patterns
   - Multiple extensions

2. **Command format handling**:
   - List format
   - String format
   - None values

3. **Action availability**:
   - Available actions
   - Unavailable actions
   - Missing patterns

4. **Configuration loading**:
   - Default config
   - User config
   - Missing config

### Example Test

```python
def test_get_program_for_file():
    # Test PDF file
    command = get_program_for_file('document.pdf', 'view')
    assert command == ['open', '-a', 'Preview']
    
    # Test case-insensitive
    command = get_program_for_file('DOCUMENT.PDF', 'view')
    assert command == ['open', '-a', 'Preview']
    
    # Test unavailable action
    command = get_program_for_file('file.xyz', 'edit')
    assert command is None
```

## Future Enhancements

### Priority System

Add priority to patterns for more specific matching:

```python
'*.tar.gz': {'priority': 10, 'open': ['tar', '-xzf']},
'*.gz': {'priority': 5, 'open': ['gunzip']}
```

### MIME Type Support

Support MIME type matching in addition to extensions:

```python
'image/jpeg': {'open': ['open', '-a', 'Preview']},
'application/pdf': {'view': ['open', '-a', 'Preview']}
```

### Action Chaining

Support multiple programs for a single action:

```python
'*.pdf': {
    'open': [
        ['open', '-a', 'Preview'],
        ['open', '-a', 'Adobe Acrobat']
    ]
}
```

### Environment Variables

Support environment variable expansion in commands:

```python
'*.txt': {
    'edit': ['$EDITOR']  # Expands to user's preferred editor
}
```

## Dependencies

- **fnmatch**: Standard library module for pattern matching
- **tfm_config**: Configuration system
- **tfm_path**: Path handling utilities

## API Reference

### Public Functions

```python
def get_file_associations() -> dict
def get_program_for_file(filename: str, action: str = 'open') -> list | None
def has_action_for_file(filename: str, action: str = 'open') -> bool
```

### Configuration Attributes

```python
class DefaultConfig:
    FILE_ASSOCIATIONS: dict  # File extension associations

class Config:
    FILE_ASSOCIATIONS: dict  # User-customized associations
```
