# Resolution: Directory Creation/Deletion Detection Issue

## Issue Summary

Directory creation and deletion events were not being detected on macOS with FSEvents, causing the automatic file list reloading feature to miss important filesystem changes.

## Root Cause Analysis

### FSEvents Behavior on macOS

FSEvents reports directory content changes differently than file changes:

1. **File operations** (create/delete/modify):
   - Generate specific child events (`created`, `deleted`, `modified`) for the file
   - PLUS a `modified` event for the parent directory

2. **Directory operations** (create/delete subdirectories):
   - Only generate a `modified` event for the parent directory
   - NO specific event for the subdirectory itself

### Test Failures

The failing tests were caused by FSEvents initialization events, not by incorrect event processing:

- FSEvents generates initialization events (`created` and `modified`) when monitoring starts
- These events arrive 0.3-0.5 seconds after `start_monitoring()` is called
- Tests that waited only 0.2 seconds missed these events, causing them to contaminate test results
- Tests saw both initialization events AND test action events, leading to unexpected reload counts

## Solution Implemented

### Test Fixes

Updated all affected tests to:
1. Wait 0.5 seconds after `start_monitoring()` (increased from 0.2s)
2. Drain the reload queue to remove initialization events
3. Then perform test actions

```python
# Start monitoring
self.manager.start_monitoring(self.left_path, self.right_path)
time.sleep(0.5)  # Wait for initialization events

# Drain initialization events
while not self.file_manager.reload_queue.empty():
    self.file_manager.reload_queue.get_nowait()

# Now perform test action
test_file = self.left_path / "test.txt"
test_file.write_text("content")
```

### Production Code

**No changes needed** - The implementation in `src/tfm_file_monitor_observer.py` correctly handles parent directory modification events:

```python
def on_modified(self, event):
    try:
        event_path_obj = Path(event.src_path)
        
        # Special case: If the modified path IS the watched directory itself,
        # this indicates a change to its contents (child added/removed/modified).
        if event_path_obj.resolve() == self.watched_path.resolve():
            if event.is_directory:
                self.logger.info(f"Directory contents modified: {self.watched_path.name}")
                self.callback("modified", "")
                return
        
        # Filter out subdirectory events
        if not self._is_immediate_child(event.src_path):
            return
        
        # Handle child file modifications
        filename = self._get_filename(event.src_path)
        item_type = "Directory" if event.is_directory else "File"
        self.logger.info(f"{item_type} modified: {filename}")
        self.callback("modified", filename)
    except Exception as e:
        self.logger.error(f"Error handling modification event: {e}")
```

This implementation:
- Detects when the watched directory itself is modified (directory content changes)
- Triggers a reload for directory operations (create/delete subdirectories)
- Still filters subdirectory events to avoid noise
- Handles file operations normally with specific child events

## Verification

### Test Results

All 75 file monitoring tests now pass:
- `test/test_end_to_end_file_monitoring.py` - 21 tests ✓
- `test/test_file_monitor_manager_lifecycle.py` - 17 tests ✓
- `test/test_file_monitor_observer.py` - 18 tests ✓
- `test/test_tfm_filesystem_event_handler.py` - 10 tests ✓
- `test/test_file_monitoring_config.py` - 9 tests ✓

### Manual Verification

Created `temp/verify_directory_detection.py` to confirm:
- ✓ Directory creation triggers reload
- ✓ Directory deletion triggers reload
- ✓ File creation triggers reload
- ✓ File deletion triggers reload

## Files Modified

### Test Files
- `test/test_end_to_end_file_monitoring.py` - Updated 6 tests with proper initialization event handling
- `test/test_file_monitor_manager_lifecycle.py` - Updated 2 tests with proper initialization event handling

### Documentation
- `.kiro/specs/automatic-file-list-reloading/bugfix.md` - Documented root cause and solution
- `.kiro/specs/automatic-file-list-reloading/RESOLUTION.md` - This file

## Lessons Learned

1. **FSEvents timing**: Initialization events can take 0.3-0.5 seconds to arrive
2. **Platform-specific behavior**: Different filesystem monitoring APIs have different event patterns
3. **Test isolation**: Tests must account for platform-specific initialization behavior
4. **Parent directory events**: On macOS, directory operations only generate parent modification events

## Status

**RESOLVED** - All tests passing, directory creation/deletion detection working correctly.
