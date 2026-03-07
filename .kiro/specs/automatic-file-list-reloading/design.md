# Design Document: Automatic File List Reloading

## Overview

This design document specifies the architecture and implementation approach for automatic file list reloading in TFM. The feature enables TFM to detect and reflect filesystem changes made by external applications without requiring manual user refresh actions.

### Problem Statement

Currently, TFM only reloads file lists after user-initiated actions (navigation, file operations, manual refresh). When external applications create, delete, modify, or rename files in the currently viewed directory, these changes remain invisible until the user manually refreshes. This creates a disconnect between the displayed state and actual filesystem state, leading to confusion and potential errors.

### Solution Approach

We will implement a filesystem monitoring system that:
- Detects external changes using OS-native APIs when available (inotify on Linux, FSEvents on macOS, ReadDirectoryChangesW on Windows)
- Falls back to periodic polling for unsupported storage backends (S3, network mounts without notification support)
- Monitors both left and right pane directories simultaneously
- Coalesces multiple rapid changes into single reload operations
- Preserves user context (cursor position, selection) during automatic reloads
- Provides user control through configuration options

### Key Design Decisions

1. **Dual-Pane Monitoring**: Both panes are monitored simultaneously regardless of which pane is active, since TFM is a dual-pane file manager and users need to see updates in both panes
2. **Library Selection**: Use `watchdog` library for cross-platform filesystem monitoring with native API support
3. **Event Coalescing**: Batch multiple events within 200ms into a single reload to avoid UI thrashing
4. **Graceful Degradation**: Automatically fall back to polling mode when native monitoring is unavailable
5. **User Control**: Provide configuration option to disable monitoring entirely for compatibility or performance reasons

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        FileManager                           │
│                     (Main Application)                       │
└────────────┬────────────────────────────────┬───────────────┘
             │                                 │
             │ creates/manages                 │ triggers reload
             │                                 │
             ▼                                 ▼
┌────────────────────────┐          ┌──────────────────────────┐
│   FileMonitorManager   │          │   FileListManager        │
│  (Monitoring Control)  │          │   (File List Ops)        │
└────────┬───────────────┘          └──────────────────────────┘
         │
         │ manages
         │
         ▼
┌────────────────────────┐
│  FileMonitorObserver   │
│  (Per-Directory Watch) │
└────────┬───────────────┘
         │
         │ uses
         │
         ▼
┌────────────────────────┐
│   watchdog library     │
│  (Native FS Events)    │
└────────────────────────┘
```

### Component Responsibilities

**FileMonitorManager**
- Central coordinator for filesystem monitoring
- Manages lifecycle of directory watchers
- Implements event coalescing and rate limiting
- Handles monitoring mode selection (native vs fallback)
- Provides configuration-based enable/disable control
- Coordinates monitoring for both left and right panes simultaneously
- Posts reload requests to file_manager.reload_queue (thread-safe)

**FileMonitorObserver**
- Wraps watchdog Observer for a single directory
- Detects and reports filesystem events (create, delete, modify, rename)
- Handles errors and attempts reinitialization
- Provides monitoring status information

**FileManager Integration**
- Creates and configures FileMonitorManager during initialization
- Provides reload_queue (queue.Queue) for thread-safe communication
- Checks reload_queue at start of each event loop iteration
- Processes reload requests on main thread via _handle_reload_request()
- Notifies FileMonitorManager when directories change
- Preserves user context during automatic reloads

### Threading Model

The monitoring system operates on a separate thread to avoid blocking the main UI. Communication between threads uses a thread-safe queue to ensure UI operations only occur on the main thread.

**TFM's Event Loop Architecture:**

TFM's main thread runs a blocking event loop that waits for user input:

```python
# Main thread in FileManager.run()
while True:
    # Process events (blocks waiting for keyboard/mouse input)
    self.renderer.run_event_loop_iteration(timeout_ms=timeout_ms)
    
    # Redraw interface
    self.draw_interface()
```

When an event arrives (keyboard, mouse, resize), `run_event_loop_iteration()` immediately invokes callbacks synchronously on the main thread before returning. This means callbacks execute within the event processing, not as separate scheduled tasks.

**File Monitoring Thread Communication:**

Since the monitor thread cannot directly call UI methods, we use a thread-safe queue:

```
Main Thread                           Monitor Thread
    │                                      │
    │ Check reload_queue                  │
    │ (at start of each loop)             │
    │                                      │
    │ navigate_to_dir()                   │
    ├─────────────────────────────────────>│
    │                                      │ start_watching()
    │                                      │
    │                                      │ [filesystem change detected]
    │                                      │
    │                                      │ reload_queue.put(pane_name)
    │ <─────────────────────────────────────┤
    │ reload_queue.get_nowait()           │
    │ _handle_reload_request(pane_name)   │
    │ refresh_files()                      │
    │                                      │
    │ run_event_loop_iteration()          │
    │ draw_interface()                     │
    │                                      │
```

**Implementation Details:**

```python
# In FileManager.__init__():
import queue
self.reload_queue = queue.Queue()  # Thread-safe queue for reload requests

# In FileManager.run() main loop:
while True:
    # Check reload queue BEFORE processing events
    try:
        while True:
            pane_name = self.reload_queue.get_nowait()
            self._handle_reload_request(pane_name)
            self.mark_dirty()  # Trigger redraw
    except queue.Empty:
        pass
    
    # Check for quit, log updates, etc.
    # ...
    
    # Process events (blocks waiting for input)
    self.renderer.run_event_loop_iteration(timeout_ms=timeout_ms)
    
    # Draw interface
    self.draw_interface()

# Monitor thread callback (safe to call from any thread):
def _on_filesystem_change(self, pane_name: str):
    # Just post to queue - no UI operations
    self.file_manager.reload_queue.put(pane_name)
```

**Thread Safety Guarantees:**

- `queue.Queue` is thread-safe for put/get operations
- Monitor thread only posts pane names to queue (no UI access)
- Main thread is sole consumer of queue (processes reloads)
- All UI operations (refresh_files, draw_interface) occur on main thread
- FileMonitorManager uses locks only for its own state management
- No direct callback invocation from monitor thread to UI code

## Components and Interfaces

### FileMonitorManager

Primary interface for filesystem monitoring control.

```python
class FileMonitorManager:
    """
    Manages filesystem monitoring for TFM directories.
    
    Coordinates monitoring of both left and right pane directories,
    handles event coalescing, and triggers file list reloads via
    a thread-safe queue mechanism.
    """
    
    def __init__(self, config, file_manager):
        """
        Initialize the file monitor manager.
        
        Args:
            config: TFM configuration object
            file_manager: FileManager instance (for accessing reload_queue)
        """
        
    def start_monitoring(self, left_path: Path, right_path: Path) -> None:
        """
        Start monitoring both pane directories.
        
        Args:
            left_path: Path object for left pane directory
            right_path: Path object for right pane directory
        """
        
    def update_monitored_directory(self, pane_name: str, new_path: Path) -> None:
        """
        Update the monitored directory for a specific pane.
        
        Args:
            pane_name: "left" or "right"
            new_path: New directory path to monitor
        """
        
    def stop_monitoring(self) -> None:
        """Stop all monitoring and cleanup resources."""
        
    def is_monitoring_enabled(self) -> bool:
        """Check if monitoring is currently enabled."""
        
    def get_monitoring_mode(self, path: Path) -> str:
        """
        Get the monitoring mode for a path.
        
        Returns:
            "native", "polling", or "disabled"
        """
        
    def suppress_reloads(self, duration_ms: int) -> None:
        """
        Temporarily suppress automatic reloads.
        
        Used after user-initiated actions to avoid redundant reloads.
        
        Args:
            duration_ms: Suppression duration in milliseconds
        """
```

### FileMonitorObserver

Wraps watchdog Observer for a single directory.

```python
class FileMonitorObserver:
    """
    Monitors a single directory for filesystem changes.
    
    Wraps watchdog Observer and provides error handling and status reporting.
    """
    
    def __init__(self, path: Path, event_callback, logger):
        """
        Initialize observer for a directory.
        
        Args:
            path: Directory path to monitor
            event_callback: Function to call on events (event_type: str, filename: str) -> None
            logger: Logger instance
        """
        
    def start(self) -> bool:
        """
        Start monitoring the directory.
        
        Returns:
            True if monitoring started successfully, False otherwise
        """
        
    def stop(self) -> None:
        """Stop monitoring and cleanup resources."""
        
    def is_alive(self) -> bool:
        """Check if observer is running."""
        
    def get_monitoring_mode(self) -> str:
        """
        Get current monitoring mode.
        
        Returns:
            "native" or "polling"
        """
```

### Event Handler

Internal class for processing watchdog events.

```python
class TFMFileSystemEventHandler(FileSystemEventHandler):
    """
    Handles filesystem events from watchdog.
    
    Filters events and forwards relevant changes to FileMonitorManager.
    """
    
    def __init__(self, callback, watched_path: str):
        """
        Initialize event handler.
        
        Args:
            callback: Function to call on events (event_type: str, filename: str) -> None
            watched_path: Directory being watched (for filtering subdirectory events)
        """
        
    def on_created(self, event):
        """Handle file/directory creation."""
        
    def on_deleted(self, event):
        """Handle file/directory deletion."""
        
    def on_modified(self, event):
        """Handle file/directory modification."""
        
    def on_moved(self, event):
        """Handle file/directory rename/move."""
```

### Configuration Schema

Add to TFM configuration file:

```python
{
    "file_monitoring": {
        "enabled": true,                    # Enable/disable automatic monitoring
        "coalesce_delay_ms": 200,          # Event coalescing window
        "max_reloads_per_second": 5,       # Rate limit for reloads
        "suppress_after_action_ms": 1000,  # Suppress time after user actions
        "fallback_poll_interval_s": 5      # Polling interval for fallback mode
    }
}
```

## Data Models

### Event Types

```python
class FileSystemEventType(Enum):
    """Types of filesystem events."""
    CREATED = "created"
    DELETED = "deleted"
    MODIFIED = "modified"
    MOVED = "moved"
```

### Monitoring State

```python
@dataclass
class MonitoringState:
    """State information for a monitored directory."""
    path: Path
    observer: Optional[FileMonitorObserver]
    monitoring_mode: str  # "native", "polling", "disabled"
    last_reload_time: float
    pending_reload: bool
    error_count: int
```

### Reload Request

```python
@dataclass
class ReloadRequest:
    """Request to reload a pane's file list."""
    pane_name: str  # "left" or "right"
    timestamp: float
    event_types: Set[FileSystemEventType]
    affected_files: List[str]
```

**Note:** The actual implementation will use a simpler queue-based approach where only the pane name is posted to `file_manager.reload_queue`. The ReloadRequest dataclass is shown here for documentation purposes but may be simplified to just passing pane names as strings in the initial implementation.


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Filesystem Event Detection

*For any* filesystem event (create, delete, modify, rename) occurring in the watched directory, the File_Monitor shall detect and report the event.

**Validates: Requirements 1.1, 2.1, 3.1, 4.1**

### Property 2: Event Coalescing

*For any* sequence of multiple filesystem events occurring within the coalescing window (200ms), the File_Monitor shall batch them into a single reload operation.

**Validates: Requirements 1.3, 2.3, 3.3, 11.1**

### Property 3: Subdirectory Event Filtering

*For any* filesystem event occurring in a subdirectory of the watched directory, the File_Monitor shall not trigger a reload of the parent directory's file list.

**Validates: Requirements 1.4, 2.4**

### Property 4: Modification Type Detection

*For any* file in the watched directory, modifications to content, size, or timestamps shall all be detected as modification events.

**Validates: Requirements 3.4**

### Property 5: Move-In Detection

*For any* file moved into the watched directory from outside, the File_Monitor shall detect it as a creation event and trigger a reload.

**Validates: Requirements 4.3**

### Property 6: Move-Out Detection

*For any* file moved out of the watched directory to elsewhere, the File_Monitor shall detect it as a deletion event and trigger a reload.

**Validates: Requirements 4.4**

### Property 7: Unsupported Backend Fallback

*For any* storage backend that does not support native monitoring, the File_Monitor shall detect this condition during initialization and operate in fallback mode.

**Validates: Requirements 6.1, 6.2**

### Property 8: Directory Navigation Monitoring Transition

*For any* directory navigation operation, the File_Monitor shall stop monitoring the previous directory and start monitoring the new directory.

**Validates: Requirements 7.1, 7.2**

### Property 9: Monitoring Initialization Failure Handling

*For any* directory where monitoring initialization fails, the File_Monitor shall log an error and operate in fallback mode for that directory.

**Validates: Requirements 7.4**

### Property 10: Selection Preservation on Reload

*For any* automatic reload triggered by external changes, if the currently selected file still exists after the reload, the cursor shall remain on that file.

**Validates: Requirements 8.1, 8.2**

### Property 11: Cursor Repositioning After Deletion

*For any* automatic reload where the previously selected file no longer exists, the cursor shall be positioned on the nearest remaining file by alphabetical order.

**Validates: Requirements 8.3**

### Property 12: Scroll Position Preservation

*For any* automatic reload triggered by external changes, the scroll position shall be preserved when possible.

**Validates: Requirements 8.4**

### Property 13: Error Resilience

*For any* error encountered during event processing, the File_Monitor shall log the error and continue monitoring without terminating.

**Validates: Requirements 9.1**

### Property 14: Connection Loss Recovery

*For any* loss of connection to the native monitoring API, the File_Monitor shall attempt to reinitialize monitoring.

**Validates: Requirements 9.2**

### Property 15: Fallback After Repeated Failures

*For any* monitoring reinitialization that fails 3 consecutive times, the File_Monitor shall fall back to fallback mode.

**Validates: Requirements 9.3**

### Property 16: Configuration-Based Disable

*For any* TFM instance where automatic monitoring is disabled by configuration, the File_Monitor shall not be initialized and file list reloads shall occur only after user-initiated actions.

**Validates: Requirements 10.2, 10.3**

### Property 17: Runtime Toggle

*For any* runtime toggle of the monitoring feature, monitoring shall start or stop without requiring application restart.

**Validates: Requirements 10.4**

### Property 18: User Action Suppression

*For any* user-initiated action that triggers a reload, automatic reloads shall be suppressed for the configured suppression period (1 second).

**Validates: Requirements 11.2**

### Property 19: Rate Limiting

*For any* sequence of filesystem events, the File_Monitor shall not trigger more than the configured maximum reloads per second (5 reloads/second).

**Validates: Requirements 11.3**

### Property 20: Coalescing Completeness

*For any* set of filesystem events that are coalesced into a single reload, all changes from those events shall be reflected in the file list after the reload.

**Validates: Requirements 11.4**

### Property 21: Event Logging

*For any* filesystem event detected by the File_Monitor, the event type and affected filename shall be logged.

**Validates: Requirements 12.2**

### Property 22: Error Logging

*For any* error encountered by the File_Monitor, the error shall be logged with sufficient context for debugging.

**Validates: Requirements 12.3**

### Property 23: Mode Transition Logging

*For any* monitoring mode change (native to fallback or vice versa), the transition and reason shall be logged.

**Validates: Requirements 12.5**

## Error Handling

### Error Categories

**Initialization Errors**
- Directory does not exist
- Insufficient permissions to monitor directory
- Native monitoring API unavailable
- Resource limits exceeded (too many watches)

**Runtime Errors**
- Connection loss to native monitoring API
- Event processing exceptions
- Callback execution failures
- Thread synchronization errors

**Backend-Specific Errors**
- S3 access denied
- Network mount disconnection
- SSH connection timeout
- Archive path monitoring attempts

### Error Handling Strategies

**Graceful Degradation**
- When native monitoring fails, automatically fall back to polling mode
- When polling fails, disable monitoring for that directory but continue application operation
- Never crash the application due to monitoring errors

**Retry Logic**
- Attempt reinitialization up to 3 times with exponential backoff (1s, 2s, 4s)
- After 3 failures, switch to fallback mode permanently for that directory
- Reset retry counter when monitoring successfully runs for 60 seconds

**User Notification**
- Log all errors with ERROR level
- Display status indicator when operating in fallback mode due to errors
- Provide clear error messages in logs for troubleshooting

**Resource Cleanup**
- Always stop observers before starting new ones
- Release file handles and system resources on errors
- Clean up threads on shutdown or monitoring disable

### Error Recovery Flows

```
Native Monitoring Failure:
  1. Log error with context
  2. Attempt reinitialization (up to 3 times)
  3. If all retries fail, switch to polling mode
  4. Log mode transition
  5. Continue operation

Event Processing Error:
  1. Log error with event details
  2. Continue processing other events
  3. Ensure reload still occurs if needed
  4. Monitor for repeated errors (circuit breaker pattern)

Callback Execution Error:
  1. Log error with stack trace
  2. Prevent error from propagating to monitor thread
  3. Continue monitoring
  4. Retry callback on next event if appropriate
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of each event type (create, delete, modify, rename)
- Platform-specific monitoring initialization (Linux/inotify, macOS/FSEvents, Windows/ReadDirectoryChangesW)
- Configuration loading and validation
- Error handling for specific error conditions
- Integration between FileMonitorManager and FileManager
- UI state preservation during reloads

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Event detection across randomly generated file operations
- Coalescing behavior with varying event patterns
- Rate limiting under high event frequency
- Cursor preservation across random file changes
- Error resilience with randomly injected failures

### Property-Based Testing Configuration

**Library**: Use `hypothesis` for Python property-based testing

**Test Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with: `Feature: automatic-file-list-reloading, Property {number}: {property_text}`
- Use temporary directories for filesystem operations
- Clean up test artifacts after each iteration

**Example Property Test Structure**:

```python
from hypothesis import given, strategies as st
import pytest

@given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=20))
@pytest.mark.property_test
def test_property_1_filesystem_event_detection(filenames):
    """
    Feature: automatic-file-list-reloading
    Property 1: For any filesystem event (create, delete, modify, rename) 
    occurring in the watched directory, the File_Monitor shall detect 
    and report the event.
    """
    # Test implementation
    pass
```

### Test Scenarios

**Event Detection Tests**:
- Create files with various names and verify detection
- Delete files and verify detection
- Modify files (content, size, timestamps) and verify detection
- Rename files and verify detection
- Move files in/out of directory and verify detection

**Coalescing Tests**:
- Generate rapid sequences of events and verify single reload
- Test coalescing window boundaries
- Verify all changes reflected after coalesced reload

**Dual-Pane Tests**:
- Monitor both panes simultaneously
- Trigger events in left pane, verify left pane reloads
- Trigger events in right pane, verify right pane reloads
- Trigger events in both panes, verify both reload independently

**Backend Tests**:
- Test local filesystem monitoring (native mode)
- Test S3 paths (fallback mode)
- Test SSH paths (fallback mode)
- Test network mounts (fallback or native depending on support)

**Error Handling Tests**:
- Simulate monitoring initialization failures
- Simulate connection loss during monitoring
- Simulate event processing errors
- Verify fallback mode activation
- Verify retry logic and backoff

**Configuration Tests**:
- Test with monitoring enabled/disabled
- Test runtime toggling
- Test custom coalescing delays
- Test custom rate limits

**UI Preservation Tests**:
- Verify cursor stays on same file after reload
- Verify cursor moves to nearest file when selected file deleted
- Verify scroll position preserved
- Test with various file list sizes and cursor positions

### Integration Testing

**FileManager Integration**:
- Test monitoring lifecycle (start, update, stop)
- Test reload callback execution
- Test suppression after user actions
- Test interaction with manual refresh

**Multi-Threading Tests**:
- Verify thread safety of event callbacks
- Test concurrent events from both panes
- Verify proper cleanup on shutdown
- Test race conditions between navigation and events

### Performance Testing

While not part of correctness properties, performance should be validated:
- Memory usage per watched directory (< 5MB target)
- CPU usage during idle (< 1% target)
- Reload latency (< 500ms target)
- Rate limiting effectiveness (max 5 reloads/second)

### Manual Testing Checklist

- [ ] Create file in external editor, verify TFM shows it
- [ ] Delete file in terminal, verify TFM removes it
- [ ] Modify file externally, verify TFM updates size/timestamp
- [ ] Rename file externally, verify TFM shows new name
- [ ] Navigate between directories, verify monitoring follows
- [ ] Test with S3 paths, verify fallback mode works
- [ ] Disable monitoring in config, verify no automatic updates
- [ ] Toggle monitoring at runtime, verify immediate effect
- [ ] Generate many rapid changes, verify coalescing works
- [ ] Test on Linux, macOS, and Windows (if available)
