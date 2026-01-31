# Task Cancellation Implementation

## Overview

TFM implements task cancellation to allow users to interrupt long-running operations (file operations, archive operations) using the ESC key. While a task is active, all other keyboard actions are blocked to prevent conflicting operations.

## Architecture

### Task Management

Tasks are managed through the `FileManager` class:

```python
class FileManager:
    def __init__(self, ...):
        self.current_task: Optional[BaseTask] = None
    
    def start_task(self, task: BaseTask):
        """Start a new task"""
        if self.current_task and self.current_task.is_active():
            raise RuntimeError("Cannot start task: another task is already active")
        self.current_task = task
        task.start()
    
    def cancel_current_task(self):
        """Cancel the currently active task"""
        if self.current_task and self.current_task.is_active():
            self.current_task.cancel()
    
    def _clear_task(self):
        """Clear the current task reference (called by task when complete)"""
        self.current_task = None
```

### Input Handling

The `handle_main_screen_key_event()` method implements the cancellation and blocking logic for keyboard events:

```python
def handle_main_screen_key_event(self, event):
    # Handle ESC key to cancel active task
    if event.key_code == KeyCode.ESCAPE:
        if self.current_task and self.current_task.is_active():
            self.logger.info("Cancelling task...")
            self.cancel_current_task()
            self.mark_dirty()
            return True
        return False
    
    # Block all actions while a task is active
    if self.current_task and self.current_task.is_active():
        self.logger.warning("Action blocked: task in progress (press ESC to cancel)")
        return True
    
    # Normal action processing continues...
```

The `_handle_menu_event()` method implements the blocking logic for menu events:

```python
def _handle_menu_event(self, event):
    if not isinstance(event, MenuEvent):
        return False
    
    # Block all menu actions while a task is active
    if self.current_task and self.current_task.is_active():
        self.logger.warning("Menu action blocked: task in progress (press ESC to cancel)")
        return True
    
    # Normal menu action processing continues...
```

## Key Features

### 1. ESC Key Cancellation

- **Behavior**: Pressing ESC during an active task cancels it
- **Feedback**: Logs "Cancelling task..." message
- **Result**: Task's `cancel()` method is called, which sets cancellation flag

### 2. Action Blocking

- **Behavior**: All keyboard and menu actions are blocked while a task is active
- **Feedback**: Logs warning "Action blocked: task in progress (press ESC to cancel)" for keyboard actions
- **Feedback**: Logs warning "Menu action blocked: task in progress (press ESC to cancel)" for menu actions
- **Scope**: Applies to all main screen actions (navigation, file operations, etc.) and all menu items

### 3. Task State Management

- **Active Check**: `task.is_active()` determines if task is running
- **Completion**: Tasks call `file_manager._clear_task()` when done
- **Cancellation**: Tasks check `self.is_cancelled()` periodically

## Task Types

### File Operations

File operations (copy, move, delete) are implemented as tasks:

- `FileOperationTask` in `tfm_file_operation_task.py`
- Runs in background thread
- Checks cancellation flag during operation
- Cleans up and exits gracefully when cancelled

### Archive Operations

Archive operations (create, extract) are implemented as tasks:

- `ArchiveOperationTask` in `tfm_archive_operation_task.py`
- Runs in background thread
- Checks cancellation flag during operation
- Cleans up and exits gracefully when cancelled

## Implementation Details

### BaseTask Interface

All tasks inherit from `BaseTask` which provides:

```python
class BaseTask(ABC):
    @abstractmethod
    def start(self):
        """Start the task execution"""
        pass
    
    @abstractmethod
    def cancel(self):
        """Cancel the task if possible"""
        pass
    
    @abstractmethod
    def is_active(self) -> bool:
        """Check if the task is currently active"""
        pass
    
    @abstractmethod
    def get_state(self) -> str:
        """Get the current state of the task"""
        pass
    
    def is_cancelled(self) -> bool:
        """Check if the task has been cancelled"""
        return self._cancelled
    
    def request_cancellation(self):
        """Request task cancellation"""
        self._cancelled = True
```

### Cancellation Flow

1. User presses ESC key
2. `handle_main_screen_key_event()` detects ESC
3. Checks if `current_task` exists and is active
4. Calls `cancel_current_task()`
5. Task's `cancel()` method sets `_cancelled` flag
6. Task checks `is_cancelled()` periodically
7. Task exits gracefully and calls `_clear_task()`

### Action Blocking Flow

1. User presses any key or selects a menu item
2. `handle_main_screen_key_event()` or `_handle_menu_event()` checks if task is active
3. If active, logs warning and returns True (consumed)
4. Action is not processed
5. User sees warning in log pane

## User Experience

### Normal Operation

1. User starts a file operation (F5 to copy or File > Copy menu)
2. Operation begins in background
3. User can see progress in log pane
4. User can press ESC to cancel
5. All keyboard and menu input is blocked
6. Operation completes or is cancelled
7. Normal keyboard and menu input resumes

### Cancellation

1. User presses ESC during operation
2. Log shows "Cancelling task..."
3. Task stops gracefully
4. Log shows cancellation result
5. Normal keyboard input resumes

### Blocked Actions

1. User tries to perform action during operation (keyboard or menu)
2. Log shows "Action blocked: task in progress (press ESC to cancel)" or "Menu action blocked: task in progress (press ESC to cancel)"
3. Action is not performed
4. User can press ESC to cancel and retry

## Testing

### Unit Tests

See `test/test_task_cancellation.py`:

- `test_esc_cancels_active_task`: ESC cancels active task
- `test_esc_ignored_when_no_task`: ESC ignored when no task
- `test_actions_blocked_during_task`: Keyboard actions blocked during task
- `test_menu_actions_blocked_during_task`: Menu actions blocked during task
- `test_actions_allowed_when_no_task`: Actions work when no task
- `test_task_completion_allows_actions`: Actions work after completion
- `test_esc_during_task_logs_message`: Cancellation logs message
- `test_blocked_action_logs_warning`: Blocked actions log warning

### Demo

See `demo/demo_task_cancellation.py` for interactive demonstration.

## Future Enhancements

### Potential Improvements

1. **Progress Display**: Show progress bar in status line
2. **Partial Results**: Allow viewing partial results before completion
3. **Pause/Resume**: Add ability to pause and resume operations
4. **Multiple Tasks**: Support queuing multiple tasks
5. **Task History**: Show history of completed/cancelled tasks

### Considerations

- **Thread Safety**: Ensure cancellation flag is thread-safe
- **Resource Cleanup**: Ensure all resources are cleaned up on cancellation
- **User Feedback**: Provide clear feedback about cancellation status
- **Error Handling**: Handle errors during cancellation gracefully

## Related Files

- `src/tfm_main.py`: Main input handling and task management
- `src/tfm_base_task.py`: Base task interface
- `src/tfm_file_operation_task.py`: File operation task implementation
- `src/tfm_archive_operation_task.py`: Archive operation task implementation
- `test/test_task_cancellation.py`: Unit tests
- `demo/demo_task_cancellation.py`: Interactive demo

## References

- **Task System**: See `doc/dev/TASK_SYSTEM.md` (if exists)
- **File Operations**: See `doc/dev/FILE_OPERATIONS_IMPLEMENTATION.md` (if exists)
- **Archive Operations**: See `doc/dev/ARCHIVE_OPERATIONS_IMPLEMENTATION.md` (if exists)
