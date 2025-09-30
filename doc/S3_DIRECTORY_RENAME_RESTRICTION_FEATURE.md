# S3 Directory Rename Restriction Feature

## Overview

This feature prevents users from renaming directories on S3 storage to avoid confusion and expensive operations. Unlike local file systems where directory renaming is a simple metadata operation, S3 directory renaming would require copying all objects within the directory and then deleting the originals, which can be:

- **Expensive**: Each object copy and delete operation incurs S3 API costs
- **Slow**: Large directories with many objects could take a very long time
- **Risky**: Potential for partial failures leaving the directory in an inconsistent state

## Implementation

### Core Changes

The restriction is implemented at two levels:

#### 1. Dialog Prevention (Primary UX)
In `src/tfm_main.py`, the `enter_rename_mode()` method uses the capability system to check if directory renaming is supported:

```python
def enter_rename_mode(self):
    # ... existing code ...
    
    # Check if this storage implementation supports directory renaming
    try:
        if selected_file.is_dir() and not selected_file.supports_directory_rename():
            print("Directory renaming is not supported on this storage type due to performance and cost considerations")
            return
    except Exception as e:
        # Handle any errors gracefully and continue
        print(f"Warning: Could not check directory rename capability: {e}")
    
    # ... continue with dialog creation ...
```

#### 2. Backend Protection (Fallback)
In `src/tfm_s3.py`, the `S3PathImpl.rename()` method provides backend protection:

```python
def rename(self, target) -> 'Path':
    """Rename this file or directory to the given target"""
    # Check if this is a directory - S3 directory renaming is not supported
    if self.is_dir():
        raise OSError("Directory renaming is not supported on S3 due to performance and cost considerations")
    
    # Continue with file rename logic...
```

### Behavior

- **Files**: Renaming S3 files continues to work as before (copy + delete)
- **Directories**: Attempting to rename any S3 directory raises an informative `OSError`
- **Virtual Directories**: Both explicit directories (ending with `/`) and virtual directories are blocked
- **Replace Method**: The `replace()` method is also blocked for directories since it calls `rename()`

### Error Message

When a user attempts to rename a directory on S3, they receive this clear error message:

```
Directory renaming is not supported on S3 due to performance and cost considerations
```

## User Experience

### Before This Feature
- Users could press 'r' to rename S3 directories
- Rename dialog would open normally
- Users would enter new names
- Operations would fail at the backend level
- Confusing experience with delayed feedback

### After This Feature
- Pressing 'r' on S3 directories shows immediate error message
- No rename dialog opens for S3 directories
- Users get instant feedback about the limitation
- File renames continue to work normally
- Consistent, predictable behavior across the application

## Technical Details

### Detection Logic

The feature uses a capability-based approach with two methods:

1. **Directory Detection**: Uses the existing `is_dir()` method to determine if a path represents a directory
   - **Explicit directories**: Keys ending with `/` (e.g., `s3://bucket/folder/`)
   - **Virtual directories**: Keys that have child objects (e.g., `s3://bucket/folder` with children)

2. **Capability Detection**: Uses the new `supports_directory_rename()` method to determine if the storage implementation supports directory renaming
   - **Local paths**: Return `True` (supports directory renaming)
   - **S3 paths**: Return `False` (does not support directory renaming)
   - **Future storage types**: Can implement their own capability logic

### Integration Points

The restriction is enforced at two levels:

#### UI Level (`enter_rename_mode()`)
- Direct rename operations via the `r` key in TFM
- Prevents dialog from opening for S3 directories
- Provides immediate user feedback

#### Backend Level (`S3PathImpl.rename()`)
- Fallback protection for any programmatic rename calls
- Batch rename operations
- The `replace()` method
- Any other code paths that might bypass the UI check

### Exception Handling

The feature follows TFM's exception handling policy:
- Raises specific `OSError` with descriptive message
- Error is caught and displayed by TFM's UI layer
- No silent failures or confusing behavior

## Testing

### Test Coverage

The feature includes comprehensive tests in `test/test_s3_directory_rename_restriction.py`:

- **Directory blocking**: Verifies directories cannot be renamed
- **File allowance**: Ensures files can still be renamed
- **Virtual directories**: Tests both explicit and virtual directory types
- **Replace method**: Verifies `replace()` is also blocked for directories
- **Error messages**: Validates informative error messages

### Demo Script

A demonstration script is available at `demo/demo_s3_directory_rename_restriction.py` that shows:

- File rename operations (allowed)
- Directory rename operations (blocked)
- Virtual directory operations (blocked)
- Replace method operations (blocked)

## Configuration

No configuration is required. The restriction is automatically applied to all S3 operations.

## Alternatives Considered

### 1. Allow with Warning
**Rejected**: Users might ignore warnings and accidentally incur high costs.

### 2. Implement Efficient Directory Rename
**Rejected**: S3 doesn't support atomic directory operations, making this technically impossible without the copy/delete approach.

### 3. Background Processing
**Rejected**: Still expensive and could fail partially, leaving inconsistent state.

## Future Enhancements

### Possible Improvements

1. **Batch Operations**: Could potentially support directory renames for small directories with user confirmation
2. **Cost Estimation**: Show estimated cost before allowing directory operations
3. **Configuration Option**: Allow power users to enable directory renames with explicit acknowledgment

### Implementation Considerations

Any future enhancements should:
- Maintain the default safe behavior
- Provide clear cost and time estimates
- Include confirmation dialogs for expensive operations
- Handle partial failures gracefully

## Related Features

- **S3 Support**: Core S3 integration in `src/tfm_s3.py`
- **File Operations**: General file operation handling in `src/tfm_file_operations.py`
- **Path Abstraction**: Path interface in `src/tfm_path.py`

## Troubleshooting

### Common Issues

**Q: Why can't I rename directories on S3?**
A: S3 directory renaming requires copying all objects and deleting originals, which is expensive and slow. Use file-level operations instead.

**Q: Can I rename files on S3?**
A: Yes, file renaming continues to work normally.

**Q: What about moving directories?**
A: Moving directories between different storage types may still work, but S3-to-S3 directory moves are also restricted.

### Workarounds

For users who need directory-like renaming:
1. Create new directory structure
2. Move/copy files individually
3. Delete old directory structure
4. Use S3 management tools outside of TFM for bulk operations

## Implementation Files

### Core Logic
- **Path Interface**: `src/tfm_path.py` - Added `supports_directory_rename()` abstract method
- **Local Implementation**: `src/tfm_path.py` - LocalPathImpl.supports_directory_rename() returns `True`
- **S3 Implementation**: `src/tfm_s3.py` - S3PathImpl.supports_directory_rename() returns `False`
- **S3 Backend Protection**: `src/tfm_s3.py` - S3PathImpl.rename() method
- **UI Prevention**: `src/tfm_main.py` - FileManager.enter_rename_mode() method

### Tests
- **Backend Tests**: `test/test_s3_directory_rename_restriction.py`
- **Integration Tests**: `test/test_integration_s3_directory_rename.py`
- **UI Tests**: `test/test_s3_directory_rename_dialog_prevention.py`
- **Capability Tests**: `test/test_directory_rename_capability.py`

### Demos
- **Backend Demo**: `demo/demo_s3_directory_rename_restriction.py`
- **UI Demo**: `demo/demo_s3_directory_rename_dialog_prevention.py`

### Documentation
- **Feature Documentation**: `doc/S3_DIRECTORY_RENAME_RESTRICTION_FEATURE.md`