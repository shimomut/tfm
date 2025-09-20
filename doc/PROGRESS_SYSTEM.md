# Generalized Progress System

## Overview

The TFM progress system provides a unified way to track and display progress for long-running file operations. This system replaces the previous archive-specific progress tracking with a generalized solution that works for all file operations.

## Features

- **Unified Progress Tracking**: Single system for all file operations (copy, move, delete, archive creation/extraction)
- **Fine-Grained Progress**: Tracks individual files even when processing directories recursively
- **Real-time Updates**: Progress updates are displayed in the status bar during operations
- **Error Tracking**: Tracks errors that occur during operations
- **Flexible Display**: Automatically formats progress text to fit available screen space
- **Callback Support**: Supports callbacks for custom progress handling

## Architecture

### ProgressManager Class

The `ProgressManager` class in `tfm_progress_manager.py` handles all progress tracking functionality.

#### Key Methods

- `start_operation(operation_type, total_items, description, callback)`: Start tracking an operation
- `update_progress(current_item, processed_items)`: Update progress with current item
- `increment_errors()`: Track errors during operation
- `finish_operation()`: Complete and clear progress tracking
- `get_progress_text(max_width)`: Get formatted progress text for display

### Operation Types

The system supports these operation types via the `OperationType` enum:

- `COPY`: File/directory copying operations
- `MOVE`: File/directory moving operations  
- `DELETE`: File/directory deletion operations
- `ARCHIVE_CREATE`: Archive creation operations
- `ARCHIVE_EXTRACT`: Archive extraction operations

## Usage

### Basic Usage Pattern

```python
# Start progress tracking
self.progress_manager.start_operation(
    OperationType.COPY, 
    total_files, 
    "to destination",
    self._progress_callback
)

try:
    for i, file_path in enumerate(files):
        # Update progress before processing each file
        self.progress_manager.update_progress(file_path.name, i)
        
        # Perform the actual operation
        # ... copy/move/delete logic ...
        
        # Handle errors
        if error_occurred:
            self.progress_manager.increment_errors()
            
finally:
    # Always finish progress tracking
    self.progress_manager.finish_operation()
```

### Integration with TFM

The main TFM class integrates the progress manager as follows:

1. **Initialization**: `self.progress_manager = ProgressManager()`
2. **Progress Callback**: `_progress_callback()` method refreshes the display
3. **Status Display**: Status bar checks for active operations and displays progress
4. **Operation Integration**: Copy, move, delete, and archive operations use the progress system

### Display Logic

The status bar display logic prioritizes progress information:

```python
if self.progress_manager.is_operation_active():
    progress_text = self.progress_manager.get_progress_text(width - 4)
    self.safe_addstr(status_y, 2, progress_text, get_status_color())
    return
```

## Configuration

### Progress Threshold

Progress is only shown for operations involving multiple individual files (> 1 file). Single file operations complete too quickly to benefit from progress display.

### Fine-Grained Tracking

The system now counts and tracks individual files even when processing directories:

- **Directory Operations**: When copying/moving/deleting a directory, progress is shown for each individual file within that directory
- **Recursive Processing**: Files in nested subdirectories are tracked individually
- **Accurate Counts**: Total file count includes all files in all subdirectories
- **Detailed Display**: Shows relative paths for files in subdirectories (e.g., "src/components/header.py")

### Display Format

Progress text includes:
- Operation type (Copying, Moving, Deleting, etc.)
- Optional description (e.g., destination directory)
- Progress count (processed/total)
- Percentage complete
- Current file being processed (if space allows)

Examples: 
- `Copying (to Documents)... 15/50 (30%) - large_file.pdf`
- `Copying (to Backup)... 127/200 (63%) - src/components/header.py`
- `Moving (to Archive)... 45/78 (57%) - data/datasets/sales.csv`

## Migration from Legacy System

The legacy archive progress system has been fully migrated to use the new ProgressManager:

- Legacy `archive_progress` state has been removed
- `update_archive_progress()` method now delegates to ProgressManager
- Status bar uses only the new progress system
- All archive operations use the unified progress tracking

## Error Handling

The progress system includes robust error handling:

- Progress updates are wrapped in try/catch blocks
- Screen refresh errors are ignored during progress updates
- Progress state is always cleaned up via `finally` blocks

## Performance Considerations

- Progress updates are lightweight and don't significantly impact operation performance
- Screen refreshes are minimized to essential updates only
- Progress text formatting is optimized for different screen widths

## Future Enhancements

Potential future improvements:

- **Estimated Time Remaining**: Calculate and display ETA based on current progress
- **Transfer Speed**: Show files/second or bytes/second for large operations
- **Pause/Resume**: Allow users to pause long-running operations
- **Background Operations**: Support for operations that continue while user navigates
- **Progress History**: Log of completed operations with timing information

## Testing

The progress system includes comprehensive tests in `test/test_progress_manager.py`:

- Basic functionality tests
- Operation type verification
- Progress text formatting tests
- Error handling validation

Run tests with: `python test/test_progress_manager.py`