# S3 File Editing Capability Feature

## Overview

This feature adds a capability indicator for S3 file editing operations in TFM (TUI File Manager). The `supports_file_editing()` method allows applications to check whether a storage implementation supports file editing, without actually blocking the operations.

## Implementation

### Core Changes

1. **Added `supports_file_editing()` method to PathImpl hierarchy**:
   - Abstract method in `PathImpl` base class
   - Returns `True` for `LocalPathImpl` (local file system supports editing)
   - Returns `False` for `S3PathImpl` (indicates S3 editing capability)
   - Exposed through `Path` wrapper class

2. **S3 file editing methods work normally**:
   - `open()` - supports all modes including write ('w') and append ('a')
   - `write_text()` - works normally for S3 objects
   - `write_bytes()` - works normally for S3 objects
   - Read operations work normally

3. **Capability pattern consistency**:
   - Follows the same pattern as `supports_directory_rename()`
   - Provides information without blocking functionality

### Files Modified

- `src/tfm_path.py`: Added abstract `supports_file_editing()` method and LocalPathImpl implementation
- `src/tfm_s3.py`: Added S3PathImpl implementation and capability indicator
- `src/tfm_main.py`: Added capability check in FileManager.edit_selected_file() method

### Files Created

- `test/test_s3_file_editing_restriction.py`: S3PathImpl capability test suite
- `demo/demo_s3_file_editing_restriction.py`: S3PathImpl capability demonstration
- `test/test_filemanager_s3_edit_restriction.py`: FileManager integration test suite
- `demo/demo_filemanager_s3_edit_restriction.py`: FileManager integration demonstration
- `doc/S3_FILE_EDITING_RESTRICTION_FEATURE.md`: This documentation

## Behavior

### S3 Path Operations

All S3 file operations work normally at the Path level:

```python
s3_path = Path('s3://bucket/file.txt')

# All these operations work:
s3_path.open('w')                    # Write mode
s3_path.open('a')                    # Append mode  
s3_path.open('r')                    # Read mode
s3_path.write_text("content")        # Text writing
s3_path.write_bytes(b"content")      # Binary writing
s3_path.read_text()                  # Text reading
s3_path.read_bytes()                 # Binary reading
s3_path.supports_file_editing()      # Returns False (capability indicator)
```

### FileManager Integration

The FileManager class checks the capability before launching external editors:

```python
# In FileManager.edit_selected_file():
if not selected_file.supports_file_editing():
    print("Editing S3 files is not supported for now")
    return

# Otherwise, launch editor normally...
```

This means:
- **S3 files**: User sees error message, editor is not launched
- **Local files**: Editor launches normally
- **Clear feedback**: User understands why editing was blocked

## Capability Detection

Applications can check if a path supports file editing as a capability indicator:

```python
path = Path('s3://bucket/file.txt')
if path.supports_file_editing():
    # Local file system - full editing support expected
    path.write_text("new content")
else:
    # S3 or other storage - editing works but may have different characteristics
    # (e.g., eventual consistency, different performance, etc.)
    print("Note: This storage type has different editing characteristics")
    path.write_text("new content")  # Still works
```

## Design Pattern

This implementation follows the established capability pattern used for `supports_directory_rename()`:

1. **Abstract method** in base `PathImpl` class
2. **Implementation-specific behavior** in each PathImpl subclass
3. **Capability indicator** for applications to understand storage characteristics
4. **No operation blocking** - methods work normally regardless of capability
5. **Wrapper method** in `Path` class for easy access

## Testing

### Unit Tests

The test suite (`test/test_s3_file_editing_restriction.py`) verifies:

- `supports_file_editing()` returns `False` for S3 paths
- All file editing operations work normally for S3 paths
- Read operations work normally
- Write operations work normally and return expected values

### Demo Script

The demo script (`demo/demo_s3_file_editing_restriction.py`) provides:

- Interactive demonstration of the capability indicator
- Examples of working S3 file operations
- Clear success indicators for all operations

## Impact on Existing Tests

Existing tests that test S3 file editing functionality should continue to work normally since the operations are not blocked. The `supports_file_editing()` method is purely informational.

## Future Considerations

The `supports_file_editing()` method can be used to indicate different levels of editing support:

1. **Current behavior**: S3 returns `False` to indicate different editing characteristics
2. **Future enhancement**: Could return `True` when S3 editing is considered fully equivalent to local editing
3. **Extended capabilities**: Could be enhanced to return capability levels or feature sets

The capability-based design allows applications to adapt their behavior based on storage characteristics without breaking functionality.

## Benefits

- **Informational capability**: Applications can understand storage characteristics
- **Consistent API**: Follows established patterns for capability indication
- **Non-blocking**: All operations work normally regardless of capability
- **Extensible**: Easy to extend with additional capability information
- **Flexible**: Applications can choose how to handle different storage types