# Directory Existence Check Feature

## Overview

TFM now automatically checks the existence of directories in cursor history during startup and removes entries for directories that no longer exist. This prevents issues with stale cursor history entries and keeps the state database clean.

## How It Works

### Startup Process

When TFM starts up, the following sequence occurs:

1. **Session Heartbeat Update**: Updates the session timestamp
2. **Directory Cleanup**: **NEW** - Removes cursor history entries for non-existing directories
3. **Window Layout Restoration**: Restores pane ratios and log height
4. **Pane State Restoration**: Restores directory paths (only if they exist)
5. **File List Refresh**: Loads current directory contents
6. **Cursor Position Restoration**: Restores cursor positions from cleaned history

### Cleanup Process

The cleanup process (`cleanup_non_existing_directories()`) performs the following:

1. **Iterates through both pane histories** (left and right)
2. **Checks directory existence** using `Path.exists()`
3. **Removes invalid entries** from cursor history
4. **Handles backward compatibility** with old dict format cursor history
5. **Saves cleaned history** back to the database
6. **Reports cleanup statistics** to the log

## Implementation Details

### State Manager Method

```python
def cleanup_non_existing_directories(self) -> bool:
    """
    Remove cursor history entries for directories that no longer exist.
    
    This method checks all saved cursor positions and removes entries
    for directories that no longer exist on the filesystem.
    
    Returns:
        bool: True if cleanup was successful
    """
```

### Integration Point

The cleanup is integrated into the `load_application_state()` method in `tfm_main.py`:

```python
def load_application_state(self):
    """Load saved application state from persistent storage."""
    try:
        # Update session heartbeat
        self.state_manager.update_session_heartbeat()
        
        # Clean up non-existing directories from cursor history before restoring state
        self.state_manager.cleanup_non_existing_directories()
        
        # ... rest of state loading
```

## Benefits

### 1. **Prevents Stale Data**
- Removes cursor history entries for deleted directories
- Keeps the state database clean and relevant

### 2. **Improves Performance**
- Reduces the size of cursor history data
- Faster lookups in cleaned history

### 3. **Better User Experience**
- No attempts to restore cursors to non-existing directories
- Cleaner cursor history navigation

### 4. **Automatic Maintenance**
- No user intervention required
- Happens transparently during startup

## Backward Compatibility

The cleanup function handles both cursor history formats:

### Old Dict Format
```python
{
    "/path/to/dir1": "filename1.txt",
    "/path/to/dir2": "filename2.txt"
}
```

### New List Format
```python
[
    [timestamp, "/path/to/dir1", "filename1.txt"],
    [timestamp, "/path/to/dir2", "filename2.txt"]
]
```

When cleaning old format entries, they are automatically converted to the new format.

## Configuration

No configuration is required. The cleanup runs automatically during startup.

The cleanup respects the existing `MAX_CURSOR_HISTORY_ENTRIES` configuration setting when saving cleaned history.

## Logging

The cleanup process provides informative log messages:

```
Cleaned up 3 non-existing directory entries from cursor history
```

If no cleanup is needed, no message is logged to avoid noise.

## Error Handling

The cleanup process includes comprehensive error handling:

- **Database errors**: Gracefully handled with warning messages
- **File system errors**: Individual directory checks are protected
- **Partial failures**: Continues processing even if some entries fail
- **Rollback safety**: Uses transactions to ensure data integrity

## Testing

The feature includes comprehensive tests:

- `test_directory_existence_check.py`: Basic functionality tests
- `test_startup_directory_cleanup.py`: Integration tests with mock FileManager
- `test_tfm_startup_cleanup.py`: Real-world scenario tests
- `demo_directory_cleanup.py`: Interactive demonstration

## Performance Impact

The cleanup process is designed to be efficient:

- **Minimal overhead**: Only runs once during startup
- **Batch processing**: Processes all entries in single database transactions
- **Early termination**: Skips processing if no cursor history exists
- **Optimized queries**: Uses efficient database operations

## Future Enhancements

Potential future improvements:

1. **Periodic cleanup**: Option to run cleanup periodically, not just at startup
2. **Cleanup threshold**: Only run cleanup if history size exceeds a threshold
3. **Cleanup statistics**: More detailed reporting of cleanup operations
4. **Manual cleanup command**: Allow users to trigger cleanup manually

## Related Features

This feature works in conjunction with:

- **Cursor History System**: Maintains cursor positions across sessions
- **State Manager**: Persistent application state storage
- **Startup Restoration**: Restores application state on startup
- **Pane Management**: Manages left and right pane states

## Code Locations

- **Implementation**: `src/tfm_state_manager.py` - `cleanup_non_existing_directories()`
- **Integration**: `src/tfm_main.py` - `load_application_state()`
- **Tests**: `test/test_*_cleanup.py`
- **Demo**: `demo/demo_directory_cleanup.py`