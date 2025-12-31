# Design Document

## Overview

This design document describes the implementation of a task-based framework for complex UI × threading workflows in TFM. The framework introduces an abstract BaseTask class that provides a consistent pattern for operations requiring user interaction, background processing, and state management. The first concrete implementation, FileOperationTask, will replace the current callback-based file operations system in FileOperationsUI.

The task framework provides:
- Clear state transitions through an event-driven state machine
- Elimination of callback hell through structured state management
- Simplified threading coordination between worker threads and the UI thread
- A foundation for future complex workflows (e.g., batch operations, search operations, archive operations)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FileManager                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Task Management                                │  │
│  │  - current_task: Optional[BaseTask]                    │  │
│  │  - start_task(task: BaseTask)                          │  │
│  │  - cancel_current_task()                               │  │
│  │  - Future: task_queue: List[BaseTask]                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↕                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              BaseTask (Abstract)                       │  │
│  │  - start()                                             │  │
│  │  - cancel()                                            │  │
│  │  - is_active() → bool                                  │  │
│  │  - get_state() → str                                   │  │
│  │  - on_state_enter(state)                               │  │
│  │  - on_state_exit(state)                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↕                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         FileOperationTask (Concrete)                   │  │
│  │                                                         │  │
│  │  States: IDLE → CONFIRMING → CHECKING_CONFLICTS →     │  │
│  │          RESOLVING_CONFLICT → EXECUTING → COMPLETED   │  │
│  │                                                         │  │
│  │  Context: {operation_type, files, destination,        │  │
│  │            conflicts, results, options}                │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↕                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         FileOperationsUI                               │  │
│  │  - Creates and starts FileOperationTask                │  │
│  │  - Delegates to task for all operations                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Task Framework Class Hierarchy

```
┌──────────────────────────┐
│      BaseTask            │
│      (Abstract)          │
│                          │
│  + start()               │
│  + cancel()              │
│  + is_active()           │
│  + get_state()           │
│  # on_state_enter()      │
│  # on_state_exit()       │
└────────────┬─────────────┘
             │
             │ inherits
             ↓
┌──────────────────────────┐
│  FileOperationTask       │
│                          │
│  + start_operation()     │
│  + on_confirmed()        │
│  + on_conflict_resolved()│
│  + on_renamed()          │
│  - _check_conflicts()    │
│  - _execute_operation()  │
└──────────────────────────┘

Future tasks:
┌──────────────────────────┐
│  SearchTask              │
│  BatchRenameTask         │
│  ArchiveExtractionTask   │
│  ...                     │
└──────────────────────────┘
```

### FileOperationTask State Diagram

```
                    ┌──────┐
                    │ IDLE │
                    └──┬───┘
                       │ start_operation()
                       ↓
                 ┌────────────┐
                 │ CONFIRMING │
                 └──┬─────┬───┘
          confirmed│     │cancelled
                   ↓     ↓
         ┌──────────────────┐    ┌──────┐
         │CHECKING_CONFLICTS│    │ IDLE │
         └──┬───────────┬───┘    └──────┘
    conflicts│         │no conflicts
             ↓         ↓
    ┌─────────────────┐ │
    │RESOLVING_CONFLICT│ │
    └──┬──────────────┘ │
       │all resolved    │
       ↓                ↓
    ┌──────────────────────┐
    │     EXECUTING        │
    └──────────┬───────────┘
               │completed
               ↓
         ┌───────────┐
         │ COMPLETED │
         └─────┬─────┘
               │
               ↓
         ┌──────┐
         │ IDLE │
         └──────┘
```

## Components and Interfaces

### BaseTask Abstract Class

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

class BaseTask(ABC):
    """Abstract base class for long-running tasks with UI interaction
    
    This class provides a framework for implementing complex workflows that
    involve user interaction, background processing, and state management.
    
    Subclasses must implement:
    - start(): Begin the task execution
    - cancel(): Cancel the task if possible
    - is_active(): Check if task is currently active
    - get_state(): Get current task state as string
    
    Subclasses may override:
    - on_state_enter(state): Called when entering a new state
    - on_state_exit(state): Called when exiting a state
    """
    
    def __init__(self, file_manager):
        """Initialize base task
        
        Args:
            file_manager: Reference to FileManager for UI interactions
        """
        self.file_manager = file_manager
        self.logger = getLogger(self.__class__.__name__)
    
    @abstractmethod
    def start(self):
        """Start the task execution
        
        This method should initiate the task workflow. It will be called
        by FileManager when the task is started.
        """
        pass
    
    @abstractmethod
    def cancel(self):
        """Cancel the task if possible
        
        This method should attempt to cancel the task gracefully. It may
        not be possible to cancel immediately if the task is in the middle
        of a critical operation.
        """
        pass
    
    @abstractmethod
    def is_active(self) -> bool:
        """Check if the task is currently active
        
        Returns:
            True if task is active (not IDLE or COMPLETED), False otherwise
        """
        pass
    
    @abstractmethod
    def get_state(self) -> str:
        """Get the current state of the task
        
        Returns:
            String representation of current state
        """
        pass
    
    def on_state_enter(self, state):
        """Hook called when entering a new state
        
        Subclasses can override this to perform actions when entering states.
        
        Args:
            state: The state being entered
        """
        pass
    
    def on_state_exit(self, state):
        """Hook called when exiting a state
        
        Subclasses can override this to perform cleanup when exiting states.
        
        Args:
            state: The state being exited
        """
        pass
```

### FileManager Task Management

```python
class FileManager:
    """File manager with task management support"""
    
    def __init__(self, ...):
        # Existing initialization
        ...
        # Task management
        self.current_task: Optional[BaseTask] = None
    
    def start_task(self, task: BaseTask):
        """Start a new task
        
        Args:
            task: The task to start
            
        Raises:
            RuntimeError: If a task is already active
        """
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

### FileOperationTask Class

```python
class FileOperationTask(BaseTask):
    """Task for file operations (copy, move, delete)"""
    
    class State(Enum):
        """Operation states"""
        IDLE = "idle"
        CONFIRMING = "confirming"
        CHECKING_CONFLICTS = "checking_conflicts"
        RESOLVING_CONFLICT = "resolving_conflict"
        EXECUTING = "executing"
        COMPLETED = "completed"
    
    def __init__(self, file_manager, file_operations_ui):
        """Initialize file operation task
        
        Args:
            file_manager: Reference to FileManager for UI interactions
            file_operations_ui: Reference to FileOperationsUI for operation execution
        """
        super().__init__(file_manager)
        self.file_operations_ui = file_operations_ui
        self.state = State.IDLE
        self.context = None
    
    def start(self):
        """Start the task (called by FileManager)"""
        # Task is started via start_operation() which is called by FileOperationsUI
        pass
    
    def cancel(self):
        """Cancel the task"""
        if self.is_active():
            self._transition_to_state(State.IDLE)
            self.context = None
            self.logger.info("Task cancelled")
            self.file_manager._clear_task()
    
    def is_active(self) -> bool:
        """Check if task is active"""
        return self.state not in (State.IDLE, State.COMPLETED)
    
    def get_state(self) -> str:
        """Get current state"""
        return self.state.value
    
    def start_operation(self, operation_type, files, destination=None):
        """Start a new file operation
        
        Args:
            operation_type: 'copy', 'move', or 'delete'
            files: List of Path objects to operate on
            destination: Destination Path (for copy/move only)
        """
        pass
    
    def on_confirmed(self, confirmed):
        """Handle confirmation response"""
        pass
    
    def on_conflict_resolved(self, choice, apply_to_all=False):
        """Handle conflict resolution choice"""
        pass
    
    def on_renamed(self, source_file, new_name):
        """Handle rename confirmation"""
        pass
    
    def on_rename_cancelled(self):
        """Handle rename cancellation"""
        pass
    
    def _transition_to_state(self, new_state):
        """Transition to a new state with hooks"""
        old_state = self.state
        self.on_state_exit(old_state)
        self.state = new_state
        self.on_state_enter(new_state)
```

### OperationContext Class

```python
@dataclass
class OperationContext:
    """Context for a file operation"""
    operation_type: str  # 'copy', 'move', 'delete'
    files: List[Path]
    destination: Optional[Path]
    conflicts: List[Tuple[Path, Path]]  # (source, dest) pairs
    current_conflict_index: int
    results: Dict[str, List]  # {'success': [], 'skipped': [], 'errors': []}
    options: Dict[str, bool]  # {'overwrite_all': False, 'skip_all': False, ...}
```

### Public API

```python
# FileManager task management
file_manager.start_task(task)
file_manager.cancel_current_task()

# Creating and starting a file operation task
task = FileOperationTask(file_manager, file_operations_ui)
task.start_operation('copy', files, destination)
file_manager.start_task(task)

# Or more commonly, FileOperationsUI creates and starts the task:
# In FileOperationsUI.copy_selected_files():
task = FileOperationTask(self.file_manager, self)
task.start_operation('copy', files, destination)
self.file_manager.start_task(task)

# State transition callbacks (called by UI components)
task.on_confirmed(True/False)
task.on_conflict_resolved('overwrite'/'rename'/'skip', apply_to_all=True/False)
task.on_renamed(source_file, new_name)
task.on_rename_cancelled()

# Task status queries
task.is_active()  # Returns bool
task.get_state()  # Returns string
```

## Data Models

### State Transitions

| Current State | Event | Next State | Action |
|--------------|-------|------------|--------|
| IDLE | start_operation() | CONFIRMING | Show confirmation dialog |
| CONFIRMING | on_confirmed(True) | CHECKING_CONFLICTS | Check for conflicts |
| CONFIRMING | on_confirmed(False) | IDLE | Log cancellation |
| CHECKING_CONFLICTS | conflicts found | RESOLVING_CONFLICT | Show conflict dialog |
| CHECKING_CONFLICTS | no conflicts | EXECUTING | Execute operation |
| RESOLVING_CONFLICT | on_conflict_resolved() | RESOLVING_CONFLICT or EXECUTING | Process choice, continue or execute |
| RESOLVING_CONFLICT | on_conflict_resolved('rename') | (stays in state) | Show rename dialog |
| RESOLVING_CONFLICT | on_renamed() | RESOLVING_CONFLICT | Process rename, continue |
| RESOLVING_CONFLICT | on_rename_cancelled() | IDLE | Cancel operation |
| EXECUTING | operation complete | COMPLETED | Show summary |
| COMPLETED | (automatic) | IDLE | Reset state |

### Operation Results Structure

```python
results = {
    'success': [
        (source_file, dest_path, overwrite_flag),
        ...
    ],
    'skipped': [
        source_file,
        ...
    ],
    'errors': [
        (source_file, error_message),
        ...
    ]
}
```

### Options Structure

```python
options = {
    'overwrite_all': False,  # Apply overwrite to all remaining conflicts
    'skip_all': False,       # Skip all remaining conflicts
    'rename_all': False      # Rename all remaining conflicts
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Task Lifecycle Validity

*For any* task, the task should only be in IDLE or COMPLETED state when is_active() returns False.

**Validates: Requirements 1.6, 3.6**

### Property 2: Single Active Task

*For any* point in time, FileManager should have at most one active task (current_task is None or current_task.is_active() is False).

**Validates: Requirements 2.3, 11.3**

### Property 3: Task Cleanup

*For any* task that completes or is cancelled, the task should transition to IDLE or COMPLETED state and FileManager should clear the task reference.

**Validates: Requirements 2.5, 11.5**

### Property 4: State Transition Validity

*For any* state transition in FileOperationTask, the task should only transition to valid next states as defined in the state diagram.

**Validates: Requirements 3.6**

### Property 5: Context Cleanup

*For any* FileOperationTask that completes or is cancelled, the task should reset to IDLE state and clear the operation context.

**Validates: Requirements 11.5**

### Property 6: Conflict Resolution Completeness

*For any* operation with conflicts, all conflicts should be either resolved (in results['success']), skipped (in results['skipped']), or cause cancellation before transitioning to EXECUTING state.

**Validates: Requirements 6.6**

### Property 7: Apply-to-All Consistency

*For any* conflict resolution with apply_to_all=True, all remaining conflicts should receive the same resolution choice.

**Validates: Requirements 6.5**

### Property 8: Rename Uniqueness

*For any* rename operation, if the new name conflicts with an existing file, the system should prompt for resolution before proceeding.

**Validates: Requirements 7.3**

### Property 9: Thread Safety

*For any* worker thread operation, no curses functions should be called directly from the worker thread.

**Validates: Requirements 13.1**

### Property 10: Operation Atomicity

*For any* operation context, the context should remain unchanged during UI interactions (between state transitions).

**Validates: Requirements 11.1**

### Property 11: Error Isolation

*For any* file operation error, the error should be logged and tracked, but remaining files should continue processing.

**Validates: Requirements 12.2**

### Property 12: Cancellation Responsiveness

*For any* operation in EXECUTING state, checking the operation_cancelled flag should stop processing within one file operation.

**Validates: Requirements 8.5**

### Property 13: Task Start Exclusivity

*For any* attempt to start a new task when one is already active, FileManager should raise a RuntimeError.

**Validates: Requirements 2.3**

## Error Handling

### Error Categories

1. **User Cancellation**: User presses ESC or selects Cancel
   - Action: Transition to IDLE, log cancellation
   - No error tracking needed

2. **File I/O Errors**: Permission denied, file not found, disk full
   - Action: Log error, increment error count, continue with next file
   - Include in completion summary

3. **Invalid State Transitions**: Attempting invalid state transition
   - Action: Log error, remain in current state
   - Should not occur in correct implementation

4. **Empty Input**: User provides empty filename during rename
   - Action: Show error message, remain in rename dialog
   - Allow user to retry or cancel

5. **Thread Errors**: Exception in worker thread
   - Action: Log error, finish progress tracking, transition to COMPLETED
   - Ensure operation_in_progress flag is cleared

### Error Recovery

```python
try:
    # State transition logic
    self._transition_to_next_state()
except Exception as e:
    self.logger.error(f"State machine error: {e}")
    # Attempt to recover to IDLE state
    self.state = State.IDLE
    self.context = None
    self.file_manager.operation_in_progress = False
```

## Testing Strategy

### Unit Tests

Unit tests will verify specific examples and edge cases:

1. **State Transition Tests**
   - Test each valid state transition
   - Test invalid state transitions are rejected
   - Test state transitions with various inputs

2. **Confirmation Tests**
   - Test confirmation with single file
   - Test confirmation with multiple files
   - Test confirmation cancellation
   - Test skip confirmation when disabled in config

3. **Conflict Resolution Tests**
   - Test overwrite choice
   - Test rename choice
   - Test skip choice
   - Test apply-to-all for each choice
   - Test mixed conflict resolutions

4. **Rename Tests**
   - Test valid rename
   - Test empty rename (should reject)
   - Test rename with new conflict
   - Test rename cancellation

5. **Execution Tests**
   - Test execution with no conflicts
   - Test execution with resolved conflicts
   - Test execution with errors
   - Test execution cancellation

6. **Edge Cases**
   - Test operation with empty file list
   - Test operation with all files skipped
   - Test operation with all files errored
   - Test rapid state transitions

### Property-Based Tests

Property-based tests will verify universal properties across all inputs using a property testing library (e.g., Hypothesis for Python):

1. **Property Test: Task Lifecycle Validity**
   - Generate random task operations
   - Verify is_active() matches state correctly
   - **Feature: file-operations-state-machine, Property 1: Task Lifecycle Validity**

2. **Property Test: Single Active Task**
   - Generate random task sequences
   - Verify at most one task is active at any time
   - **Feature: file-operations-state-machine, Property 2: Single Active Task**

3. **Property Test: Task Cleanup**
   - Generate random tasks that complete or cancel
   - Verify task reference is cleared when returning to IDLE
   - **Feature: file-operations-state-machine, Property 3: Task Cleanup**

4. **Property Test: State Transition Validity**
   - Generate random sequences of events
   - Verify only valid state transitions occur
   - **Feature: file-operations-state-machine, Property 4: State Transition Validity**

5. **Property Test: Context Cleanup**
   - Generate random operations that complete or cancel
   - Verify context is always cleared when returning to IDLE
   - **Feature: file-operations-state-machine, Property 5: Context Cleanup**

6. **Property Test: Conflict Resolution Completeness**
   - Generate random file lists with conflicts
   - Verify all conflicts are resolved before execution
   - **Feature: file-operations-state-machine, Property 6: Conflict Resolution Completeness**

7. **Property Test: Apply-to-All Consistency**
   - Generate random conflict lists with apply-to-all choices
   - Verify all remaining conflicts receive same resolution
   - **Feature: file-operations-state-machine, Property 7: Apply-to-All Consistency**

8. **Property Test: Rename Uniqueness**
   - Generate random rename operations with conflicts
   - Verify conflicts are always detected and handled
   - **Feature: file-operations-state-machine, Property 8: Rename Uniqueness**

9. **Property Test: Operation Atomicity**
   - Generate random state transitions
   - Verify context remains unchanged during transitions
   - **Feature: file-operations-state-machine, Property 10: Operation Atomicity**

10. **Property Test: Error Isolation**
    - Generate random file lists with some that will error
    - Verify errors don't stop processing of remaining files
    - **Feature: file-operations-state-machine, Property 11: Error Isolation**

11. **Property Test: Task Start Exclusivity**
    - Generate random attempts to start multiple tasks
    - Verify RuntimeError is raised when task already active
    - **Feature: file-operations-state-machine, Property 13: Task Start Exclusivity**

### Integration Tests

Integration tests will verify the state machine works correctly with FileOperationsUI:

1. Test complete copy operation flow
2. Test complete move operation flow
3. Test complete delete operation flow
4. Test operation with UI interactions
5. Test operation with background thread execution

### Test Configuration

- Unit tests: Run with pytest
- Property tests: Run with pytest + Hypothesis
- Each property test: Minimum 100 iterations
- Integration tests: Require mock FileManager
- All tests: Must pass before merging

## Implementation Notes

### Migration Strategy

1. **Phase 1: Create Task Framework**
   - Implement BaseTask abstract class in `src/tfm_base_task.py`
   - Add task management to FileManager
   - Add unit tests for BaseTask interface

2. **Phase 2: Create FileOperationTask**
   - Implement FileOperationTask class in `src/tfm_file_operation_task.py`
   - Implement OperationContext dataclass
   - Add unit tests for FileOperationTask

3. **Phase 3: Integrate Copy Operations**
   - Refactor copy_selected_files() to use FileOperationTask
   - Keep old implementation as fallback
   - Add integration tests
   - Verify behavior matches old implementation

4. **Phase 4: Integrate Move Operations**
   - Refactor move_selected_files() to use FileOperationTask
   - Remove old move implementation
   - Add integration tests

5. **Phase 5: Integrate Delete Operations**
   - Refactor delete_selected_files() to use FileOperationTask
   - Remove old delete implementation
   - Add integration tests

6. **Phase 6: Cleanup**
   - Remove all old callback-based code
   - Remove temporary context objects from file_manager
   - Update documentation

### Future Task Implementations

The BaseTask framework is designed to support future complex workflows:

1. **SearchTask**: Background search with progressive results display
2. **BatchRenameTask**: Multi-step batch rename with preview and confirmation
3. **ArchiveExtractionTask**: Archive extraction with progress and conflict resolution
4. **SyncTask**: Directory synchronization with conflict resolution
5. **CompareTask**: Directory comparison with diff display

### Task Queue Support (Future)

The current design supports a single active task, but the framework is designed to allow future task queueing:

```python
class FileManager:
    def __init__(self, ...):
        self.current_task: Optional[BaseTask] = None
        # Future: self.task_queue: List[BaseTask] = []
    
    def start_task(self, task: BaseTask, queue_if_busy=False):
        """Start a task or queue it if another is active"""
        if self.current_task and self.current_task.is_active():
            if queue_if_busy:
                self.task_queue.append(task)
            else:
                raise RuntimeError("Task already active")
        else:
            self.current_task = task
            task.start()
    
    def _on_task_complete(self):
        """Called when a task completes"""
        self.current_task = None
        # Future: Start next queued task
        # if self.task_queue:
        #     next_task = self.task_queue.pop(0)
        #     self.start_task(next_task)
```

### Backward Compatibility

The task framework will maintain backward compatibility by:

1. Respecting all existing configuration options
2. Using existing dialog components (show_dialog, show_confirmation, QuickEditBar)
3. Using existing progress manager
4. Using existing cache manager
5. Maintaining existing log message formats
6. Supporting existing keyboard shortcuts (Shift+key for apply-to-all)
7. FileOperationsUI remains the public interface (tasks are internal implementation)

### Performance Considerations

1. **State Transitions**: O(1) - simple state variable updates
2. **Conflict Detection**: O(n) - linear scan of files
3. **Conflict Resolution**: O(n) - process each conflict once
4. **Memory**: O(n) - store operation context with file lists
5. **Task Management**: O(1) - single task reference

No performance degradation expected compared to current implementation.

### Thread Safety Considerations

1. Tasks run entirely in main thread (state management and UI)
2. Worker threads only perform file I/O
3. Communication via thread-safe flags (operation_cancelled)
4. UI updates via mark_dirty() flag
5. No shared mutable state between threads
6. Task lifecycle managed by FileManager in main thread

## Dependencies

- **Internal**: FileManager, ProgressManager, CacheManager, QuickEditBar
- **External**: Python standard library (abc, enum, dataclasses, threading)
- **Testing**: pytest, hypothesis (for property-based testing)

## Future Enhancements

1. **Task Queue**: Support multiple queued tasks with priority
2. **Task History**: Track and display recent tasks
3. **Task Persistence**: Save/restore tasks across sessions
4. **Task Composition**: Combine multiple tasks into workflows
5. **Task Templates**: Predefined task configurations
6. **Task Monitoring**: Real-time task status dashboard
7. **Undo Support**: Tasks could track operations for undo
8. **Custom Task Types**: Plugin system for custom task implementations
