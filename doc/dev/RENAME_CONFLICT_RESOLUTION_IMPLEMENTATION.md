# Rename Conflict Resolution Implementation

## Overview

This document describes the implementation of the rename conflict resolution feature in TFM, which allows users to specify alternative filenames when file conflicts occur during copy, move, and archive extraction operations.

## Architecture

### Components

The rename conflict resolution feature is implemented across three main modules:

1. **tfm_file_operations.py** - Handles copy and move operations
2. **tfm_archive.py** - Handles archive extraction operations
3. **tfm_main.py** - Provides UI dialogs (input dialog and choice dialog)

### Design Pattern

The implementation follows a recursive callback pattern:

```
Conflict Detected
    ↓
Show Dialog (Overwrite/Skip/Rename/Cancel)
    ↓
User Selects "Rename"
    ↓
Show Input Dialog
    ↓
User Enters New Name
    ↓
Check for Conflict
    ↓
If Conflict: Recursively Show Dialog Again
If No Conflict: Proceed with Operation
```

## Implementation Details

### File Operations Module (tfm_file_operations.py)

#### Copy Operation Changes

Modified `copy_files_to_directory()` method:

```python
# Added "Rename" choice to conflict dialog
choices = [
    {"text": "Overwrite", "key": "o", "value": "overwrite"},
    {"text": "Skip", "key": "s", "value": "skip"},
    {"text": "Rename", "key": "r", "value": "rename"},  # NEW
    {"text": "Cancel", "key": "c", "value": "cancel"}
]

# Added rename handler
elif choice == "rename":
    if len(conflicts) == 1:
        self._handle_copy_rename(files_to_copy[0], destination_dir)
    else:
        print("Rename option only available for single file conflicts")
```

#### Move Operation Changes

Modified `move_files_to_directory()` method with identical pattern to copy operations.

#### Helper Methods

Added three new helper methods:

1. **`_handle_copy_rename(source_file, destination_dir)`**
   - Shows input dialog for new filename
   - Validates new name for conflicts
   - Recursively handles conflicts if new name also exists
   - Calls `_perform_single_copy()` when unique name found

2. **`_handle_move_rename(source_file, destination_dir)`**
   - Same pattern as copy rename
   - Calls `_perform_single_move()` when unique name found

3. **`_perform_single_copy(source_file, dest_path, overwrite)`**
   - Performs copy operation for a single file
   - Handles both files and directories
   - Updates cache and refreshes UI

4. **`_perform_single_move(source_file, dest_path, overwrite)`**
   - Performs move operation for a single file
   - Handles cross-storage moves
   - Updates cache and refreshes UI

### Archive Module (tfm_archive.py)

#### Extraction Operation Changes

Modified `_proceed_with_extraction()` method:

```python
# Changed from simple confirmation to choice dialog
message = f"Directory '{archive_basename}' already exists."
choices = [
    {"text": "Overwrite", "key": "o", "value": "overwrite"},
    {"text": "Rename", "key": "r", "value": "rename"},  # NEW
    {"text": "Cancel", "key": "c", "value": "cancel"}
]

def handle_conflict_choice(choice):
    if choice == "overwrite":
        self.perform_extraction(selected_file, extract_dir, other_pane, overwrite=True)
    elif choice == "rename":
        self._handle_extraction_rename(selected_file, other_pane, archive_basename)
    else:
        print("Extraction cancelled")
```

#### Helper Method

Added `_handle_extraction_rename()` method:
- Shows input dialog for new directory name
- Validates new name for conflicts
- Recursively handles conflicts
- Calls `perform_extraction()` when unique name found

## Recursive Conflict Resolution

### Algorithm

The recursive conflict resolution follows this pattern:

```python
def _handle_operation_rename(source, destination_dir):
    def rename_callback(new_name):
        new_path = destination_dir / new_name
        
        if new_path.exists():
            # Conflict detected - show dialog again
            show_dialog_with_choices([
                "Overwrite",
                "Rename",  # Recursive call
                "Cancel"
            ])
        else:
            # No conflict - proceed
            perform_operation(source, new_path)
    
    show_input_dialog(rename_callback)
```

### Termination Conditions

The recursion terminates when:
1. User enters a unique name (no conflict)
2. User chooses "Overwrite" option
3. User chooses "Cancel" option

### Stack Safety

The implementation uses callback-based recursion rather than direct recursion, which:
- Prevents stack overflow issues
- Allows the UI event loop to process between iterations
- Provides better user experience with responsive UI

## UI Integration

### Input Dialog

The feature relies on `FileManager.show_input_dialog()`:

```python
self.file_manager.show_input_dialog(
    prompt="Rename 'file.txt' to:",
    initial_value="file.txt",
    callback=rename_callback
)
```

### Choice Dialog

Uses `FileManager.show_dialog()` for conflict resolution:

```python
self.file_manager.show_dialog(
    message="'file.txt' already exists in destination.",
    choices=[
        {"text": "Overwrite", "key": "o", "value": "overwrite"},
        {"text": "Rename", "key": "r", "value": "rename"},
        {"text": "Cancel", "key": "c", "value": "cancel"}
    ],
    callback=handle_choice
)
```

## Error Handling

### Empty Filename Validation

```python
if not new_name or new_name.strip() == "":
    print("Operation cancelled: empty filename")
    return
```

### Exception Handling

All operations are wrapped in try-except blocks:

```python
try:
    source_file.copy_to(dest_path, overwrite=overwrite)
except Exception as e:
    print(f"Error copying {source_file.name}: {e}")
```

## Cache Management

After successful rename operations, the cache is invalidated:

```python
# For copy operations
self.cache_manager.invalidate_cache_for_copy_operation([source_file], dest_path.parent)

# For move operations
self.cache_manager.invalidate_cache_for_move_operation([source_file], dest_path.parent)
```

## UI Refresh

After operations complete:

```python
self.file_manager.refresh_files()
self.file_manager.needs_full_redraw = True
current_pane['selected_files'].clear()
```

## Cross-Storage Support

The implementation works across different storage backends:

### Local to Local
- Uses `Path.rename()` for moves
- Uses `Path.copy_to()` for copies

### Cross-Storage (Local ↔ S3)
- Uses `Path.copy_to()` followed by `Path.unlink()` for moves
- Uses `Path.copy_to()` for copies

### Directory Operations
- Recursively copies directory contents
- Handles symbolic links appropriately
- Maintains file permissions and metadata

## Limitations

### Single File Only

The rename option is only available for single file conflicts:

```python
if len(conflicts) == 1:
    self._handle_copy_rename(files_to_copy[0], destination_dir)
else:
    print("Rename option only available for single file conflicts")
```

**Rationale**: 
- Renaming multiple files requires complex UI for batch renaming
- Users can handle multiple conflicts by selecting "Skip" and then handling individual files
- Keeps the UI simple and predictable

### No Batch Rename Patterns

The current implementation doesn't support:
- Automatic numbering (file_1.txt, file_2.txt, etc.)
- Pattern-based renaming
- Bulk rename operations

These features could be added in future versions if needed.

## Testing

### Test Coverage

The feature includes comprehensive tests in `test/test_rename_conflict_resolution.py`:

1. **test_copy_rename_conflict()** - Tests copy with rename
2. **test_move_rename_conflict()** - Tests move with rename
3. **test_recursive_rename_conflict()** - Tests recursive conflict resolution
4. **test_directory_rename_conflict()** - Tests directory rename

### Test Scenarios

- Single file conflicts
- Directory conflicts
- Recursive conflict resolution (new name also conflicts)
- Cross-storage operations
- Empty filename validation

## Future Enhancements

### Potential Improvements

1. **Batch Rename Support**
   - Allow renaming multiple files with patterns
   - Auto-numbering for conflicts
   - Preview before applying

2. **Smart Name Suggestions**
   - Suggest names like "file (1).txt", "file (2).txt"
   - Timestamp-based suggestions
   - Preserve original name in suggestion

3. **Rename History**
   - Remember recent rename patterns
   - Quick access to previous rename choices

4. **Advanced Conflict Resolution**
   - Compare file contents before overwriting
   - Show file size/date differences
   - Merge options for text files

## Code Style

The implementation follows TFM coding standards:

- Module-level imports only
- Specific exception handling
- Comprehensive error messages
- Proper cache invalidation
- UI refresh after operations
- Clear method naming
- Detailed docstrings

## Dependencies

The feature depends on:

- `tfm_path.Path` - Cross-storage path abstraction
- `tfm_main.FileManager` - UI dialog methods
- `tfm_cache_manager.CacheManager` - Cache invalidation
- `tfm_progress_manager.ProgressManager` - Progress tracking

## Performance Considerations

### Conflict Checking

- Uses `Path.exists()` which is fast for local files
- May have latency for remote storage (S3, SCP)
- Checks are performed only when user enters a new name

### UI Responsiveness

- Callback-based design keeps UI responsive
- No blocking operations during rename input
- Progress tracking for large file operations

## Security Considerations

### Path Validation

- Filenames are validated for empty strings
- Path traversal is prevented by using `Path` API
- No shell command injection risks

### Permission Handling

- Respects filesystem permissions
- Proper error messages for permission denied
- No privilege escalation attempts

## See Also

<!-- TODO: Create FILE_OPERATIONS_IMPLEMENTATION.md -->
<!-- - [File Operations Implementation](FILE_OPERATIONS_IMPLEMENTATION.md) -->
<!-- Note: See ARCHIVE_OPERATIONS_SYSTEM.md for archive implementation details -->
<!-- - [Archive Operations Implementation](ARCHIVE_OPERATIONS_IMPLEMENTATION.md) -->
- [Dialog System](DIALOG_SYSTEM.md)
<!-- Note: See PATH_POLYMORPHISM_SYSTEM.md for path abstraction details -->
<!-- - [Path Abstraction](PATH_ABSTRACTION.md) -->
