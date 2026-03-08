# Task 5 Resolution: Fix auto-reload stops working after O key synchronization

## Problem

After using the O key to synchronize paths between panes (making both panes view the same directory), the right pane stopped receiving auto-reload events. This occurred because the path synchronization methods didn't update the file monitoring system.

## Root Cause

The `sync_other_to_current()` and `sync_current_to_other()` methods in `src/tfm_main.py` were changing pane directories but not calling `update_monitored_directory()` to update the file monitoring for the affected pane.

When a pane's path changed via synchronization:
1. The pane's path was updated via `self.pane_manager.sync_other_to_current()` or `sync_current_to_other()`
2. The file list was refreshed via `self.refresh_files()`
3. **BUT** the file monitoring was never updated, so the observer continued watching the old directory

## Solution

Added calls to `self.file_monitor_manager.update_monitored_directory()` in both synchronization methods after the path change:

### Changes to `src/tfm_main.py`

1. **`sync_other_to_current()` method** (line ~1919):
   - Added monitoring update for the other pane after path sync
   - Determines other pane name based on active pane
   - Calls `update_monitored_directory()` with new path

2. **`sync_current_to_other()` method** (line ~1884):
   - Added monitoring update for the current pane after path sync
   - Uses `self.pane_manager.active_pane` to get current pane name
   - Calls `update_monitored_directory()` with new path

## Implementation Details

```python
# In sync_other_to_current():
if self.pane_manager.sync_other_to_current(print):
    self.refresh_files(other_pane)
    
    # Update file monitoring for the other pane
    other_pane_name = 'right' if self.pane_manager.active_pane == 'left' else 'left'
    self.file_monitor_manager.update_monitored_directory(other_pane_name, other_pane['path'])
    
    # ... rest of method

# In sync_current_to_other():
if self.pane_manager.sync_current_to_other(print):
    self.refresh_files(current_pane)
    
    # Update file monitoring for the current pane
    current_pane_name = self.pane_manager.active_pane
    self.file_monitor_manager.update_monitored_directory(current_pane_name, current_pane['path'])
    
    # ... rest of method
```

## Benefits

1. **Shared observer optimization**: When both panes sync to the same directory, they automatically share a single observer (implemented in Task 3)
2. **Consistent monitoring**: File monitoring stays synchronized with pane paths regardless of how navigation occurs
3. **No redundant observers**: The `update_monitored_directory()` method handles observer sharing and cleanup automatically

## Testing

Created comprehensive test suite in `test/test_path_sync_monitoring_update.py`:

1. **test_sync_other_to_current_updates_monitoring**: Verifies right pane monitoring updates when syncing to left
2. **test_sync_current_to_other_updates_monitoring**: Verifies left pane monitoring updates when syncing to right
3. **test_synced_panes_both_receive_events**: Confirms both panes receive filesystem events after sync
4. **test_multiple_syncs_maintain_correct_monitoring**: Tests sequential syncs maintain correct state

All tests pass, confirming the fix works correctly.

## Verification

The fix ensures that:
- ✓ After O key synchronization, both panes receive auto-reload events
- ✓ Shared observer is created when both panes view the same directory
- ✓ Monitoring is updated correctly for both sync directions
- ✓ Multiple syncs maintain correct monitoring state

## Files Modified

- `src/tfm_main.py`: Added monitoring updates to `sync_other_to_current()` and `sync_current_to_other()`
- `test/test_path_sync_monitoring_update.py`: New comprehensive test suite (4 tests)
- `test/test_shared_directory_monitoring.py`: Updated test to handle multiple reload events correctly

## Related Tasks

- Task 3: Shared observer implementation (prevents FSEvents errors when both panes monitor same directory)
- Task 1: State restoration monitoring update (similar pattern of updating monitoring after path changes)
