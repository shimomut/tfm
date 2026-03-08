# Bugfix: Directory Creation/Deletion Detection on macOS

## Problem Statement

Directory creation and deletion events are not being detected properly on macOS with FSEvents. The root cause is that FSEvents reports directory content changes differently than file changes:

- **File operations**: Generate specific events (`created`, `deleted`, `modified`) for the file PLUS a `modified` event for the parent directory
- **Directory operations**: Only generate a `modified` event for the parent directory, with NO specific event for the subdirectory

## Diagnostic Findings

From `temp/diagnose_fsevents.py`:

```
TEST 1: Creating a subdirectory
[Event #3]
  Type: modified
  Is Directory: True
  Src Path: /private/var/.../test
  Src == Watched: True
  
TEST 2: Deleting the subdirectory  
[Event #4]
  Type: modified
  Is Directory: True
  Src Path: /private/var/.../test
  Src == Watched: True

TEST 3: Creating a file
[Event #5]
  Type: created
  Is Directory: False
  Src Path: /private/var/.../test/test.txt
  Src.parent == Watched: True
  
[Event #6]
  Type: modified
  Is Directory: True
  Src Path: /private/var/.../test
  Src == Watched: True
```

**Key insight**: Directory operations ONLY generate parent modification events, while file operations generate BOTH child-specific events AND parent modification events.

## Current Implementation Issues

The current fix in `on_modified()` triggers a reload whenever the watched directory itself is modified:

```python
if event_path_obj.resolve() == self.watched_path.resolve():
    if event.is_directory:
        self.logger.info(f"Directory contents modified: {self.watched_path.name}")
        self.callback("modified", "")
        return
```

This causes problems:

1. **Too many reload events**: Every file operation triggers TWO events (child-specific + parent modification), leading to excessive reloads
2. **Cross-pane contamination**: When left pane creates a file, BOTH panes get parent modification events, causing both to reload
3. **Test failures**: Rate limiting and coalescing tests fail because they expect 1-2 reloads but get 3+

## Root Cause Analysis

The issue is that we're treating ALL parent directory modification events as reload triggers, but we should only use them as a fallback for operations that don't generate child-specific events (i.e., directory creation/deletion).

## Solution Design

We need to distinguish between:
1. **Redundant parent modifications**: Caused by file operations that already generated child-specific events → IGNORE
2. **Meaningful parent modifications**: Caused by directory operations that don't generate child-specific events → TRIGGER RELOAD

However, we cannot reliably distinguish these cases because:
- FSEvents doesn't tell us WHY the parent was modified
- The parent modification event arrives AFTER the child event, but timing is not guaranteed
- We can't track "recent child events" because coalescing delays mean we might not process them immediately

## Alternative Solution: Accept Parent Modification Events But Improve Filtering

Instead of trying to distinguish event types, we should:

1. **Keep the parent modification detection** (needed for directory operations)
2. **Improve the filtering logic** to prevent cross-pane contamination
3. **Adjust coalescing** to handle the increased event volume

The key insight is that parent modification events should ONLY trigger reloads for panes that are actually monitoring that specific directory. The current implementation has a bug where both panes get reload requests even though they're monitoring different directories.

## Investigation Needed

Check `_on_filesystem_event()` in `FileMonitorManager` to see if there's a bug in how it determines which pane(s) to reload when a parent modification event occurs.

## Expected Behavior

- Creating a file in left pane → Only left pane reloads (1 reload request)
- Creating a directory in left pane → Only left pane reloads (1 reload request)
- Creating files in both panes → Both panes reload independently (2 reload requests, one per pane)
- Rapid file creation in one pane → Coalesced into 1-2 reload requests for that pane only

## Test Failures

## Root Cause Identified

The failing tests are NOT caused by incorrect event processing. The actual root cause is:

**FSEvents generates initialization events when monitoring starts**, reporting the watched directories as "created" and "modified". These initialization events are posted to the reload queue BEFORE the test performs its action.

When tests don't drain these initialization events, they see:
- Initialization events (1-2 reload requests)
- Test action events (1+ reload requests)
- Total: 2-3+ reload requests instead of the expected 1

## Test Failures Analysis

Current failing tests all share the same issue - they don't drain initialization events:

1. `test_left_pane_change_only_reloads_left` - Sees init events + file creation event
2. `test_right_pane_change_only_reloads_right` - Sees init events + file creation event
3. `test_rapid_changes_coalesced` - Sees init events + rapid file events
4. `test_suppression_after_user_action` - Init events not suppressed
5. `test_coalescing_batches_events` - Sees init events + coalesced events
6. `test_dual_pane_independence` - Init events contaminate independence check

## Solution

Tests must wait for initialization events to complete, then drain the reload queue before performing test actions:

```python
# Start monitoring
self.manager.start_monitoring(self.left_path, self.right_path)
time.sleep(0.5)  # Wait for initialization events (FSEvents needs ~0.3-0.5s)

# Drain initialization events
while not self.file_manager.reload_queue.empty():
    self.file_manager.reload_queue.get_nowait()

# Now perform test action
test_file = self.left_path / "test.txt"
test_file.write_text("content")
```

**Key timing insight**: FSEvents generates initialization events 0.3-0.5 seconds after monitoring starts. Tests that wait only 0.2s will miss these events, causing them to contaminate the test results.

## Implementation Status

**Fixed**: All 75 file monitoring tests now pass after updating wait time from 0.2s to 0.5s and adding queue draining.

**Files modified**:
- `test/test_end_to_end_file_monitoring.py` - Updated 6 tests
- `test/test_file_monitor_manager_lifecycle.py` - Updated 2 tests

**No production code changes needed** - The implementation is correct. The issue was purely in test setup timing.
