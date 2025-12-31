# Task Framework Implementation

## Overview

The Task Framework provides a structured approach to implementing complex UI × threading workflows in TFM. It introduces an abstract `BaseTask` class that defines a consistent pattern for operations requiring user interaction, background processing, and state management.

The first concrete implementation, `FileOperationTask`, replaces the previous callback-based file operations system with a clean state machine architecture.

## Architecture

### Refactored Architecture (Post-Refactoring)

The file operations architecture has been refactored to achieve clean separation of concerns with four distinct layers:

```
Layer 1: File List Management
┌─────────────────────────────────────────┐
│ FileListManager                         │
│ - refresh_files()                       │
│ - sort_entries()                        │
│ - toggle_selection()                    │
│ - apply_filter()                        │
└─────────────────────────────────────────┘

Layer 2: UI Interactions
┌─────────────────────────────────────────┐
│ FileOperationsUI                        │
│ - show_confirmation_dialog()            │
│ - show_conflict_dialog()                │
│ - show_rename_dialog()                  │
│ - Entry points (copy/move/delete)      │
└──────────────┬──────────────────────────┘
               │ creates & provides callbacks
               ↓
Layer 3: Orchestration
┌─────────────────────────────────────────┐
│ FileOperationTask                       │
│ - State machine logic                   │
│ - Conflict detection                    │
│ - Workflow coordination                 │
│ - Calls ui.show_*() methods             │
│ - Calls executor.perform_*() methods    │
└──────────────┬──────────────────────────┘
               │ delegates I/O
               ↓
Layer 4: I/O Operations
┌─────────────────────────────────────────┐
│ FileOperationsExecutor                  │
│ - perform_copy_operation()              │
│ - perform_move_operation()              │
│ - perform_delete_operation()            │
│ - Progress tracking                     │
│ - Error handling                        │
└─────────────────────────────────────────┘
```

### Dependency Flow

```
FileManager
    ├── creates FileListManager (renamed from FileOperations)
    ├── creates FileOperationsExecutor (new class)
    └── creates FileOperationsUI
            └── creates FileOperationTask(ui=self, executor=executor)
                    ├── calls ui.show_*() for UI
                    └── calls executor.perform_*() for I/O
```

### Key Improvements

1. **Clear Naming**: `FileOperations` → `FileListManager` accurately reflects responsibilities
2. **No Boundary Violations**: Each layer has distinct responsibilities
3. **No Circular Dependencies**: One-way dependency flow
4. **Testable**: Each component can be tested independently
5. **Maintainable**: Changes localized to appropriate layer

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FileManager                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Task Management                                │  │
│  │  - current_task: Optional[BaseTask]                    │  │
│  │  - start_task(task: BaseTask)                          │  │
│  │  - cancel_current_task()                               │  │
│  │  - _clear_task()                                       │  │
│  │  - Future: task_queue: List[BaseTask]                  │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Component Instances                            │  │
│  │  - file_list_manager: FileListManager                  │  │
│  │  - file_operations_executor: FileOperationsExecutor    │  │
│  │  - file_operations_ui: FileOperationsUI                │  │
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
│  │                                                         │  │
│  │  Dependencies:                                         │  │
│  │  - ui: FileOperationsUI (for UI interactions)         │  │
│  │  - executor: FileOperationsExecutor (for I/O)         │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↕                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         FileOperationsUI                               │  │
│  │  - Creates and starts FileOperationTask                │  │
│  │  - Provides UI methods (dialogs, confirmations)        │  │
│  │  - NO I/O operations                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↕                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         FileOperationsExecutor                         │  │
│  │  - Executes file I/O operations                        │  │
│  │  - Progress tracking                                   │  │
│  │  - Background threading                                │  │
│  │  - NO UI code                                          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Class Hierarchy

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
│  Dependencies:           │
│  - ui: FileOperationsUI  │
│  - executor: Executor    │
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

### Component Responsibilities

```
┌─────────────────────────────────────────┐
│ FileListManager                         │  Layer 1: File List Management
│ - File list operations ONLY             │
│ - NO UI, NO I/O, NO orchestration       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ FileOperationsUI                        │  Layer 2: UI Interactions
│ - UI dialogs and confirmations ONLY     │
│ - NO I/O operations                     │
│ - Creates FileOperationTask             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ FileOperationTask                       │  Layer 3: Orchestration
│ - State machine logic ONLY              │
│ - NO UI code (delegates to ui)          │
│ - NO I/O code (delegates to executor)   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ FileOperationsExecutor                  │  Layer 4: I/O Operations
│ - File I/O operations ONLY              │
│ - NO UI code                            │
│ - Background threading                  │
└─────────────────────────────────────────┘
```

## BaseTask Design

### Purpose

`BaseTask` is an abstract base class that provides a framework for implementing complex workflows involving:
- User interaction (dialogs, confirmations)
- Background processing (worker threads)
- State management (state machines)
- Progress tracking
- Cancellation support

### Interface

```python
class BaseTask(ABC):
    """Abstract base class for long-running tasks with UI interaction"""
    
    def __init__(self, file_manager):
        """Initialize base task
        
        Args:
            file_manager: Reference to FileManager for UI interactions
        """
        self.file_manager = file_manager
        self.logger = getLogger(self.__class__.__name__)
    
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
    
    def on_state_enter(self, state):
        """Hook called when entering a new state"""
        pass
    
    def on_state_exit(self, state):
        """Hook called when exiting a state"""
        pass
```

### Design Principles

1. **Single Responsibility**: Each task handles one type of workflow
2. **State Encapsulation**: All task state is contained within the task instance
3. **Lifecycle Management**: Clear start, active, and completion states
4. **Extensibility**: Hooks for state transitions allow customization
5. **Thread Safety**: Tasks coordinate between UI and worker threads

## FileOperationTask Design

### Dependencies

FileOperationTask now uses dependency injection for clean separation:

```python
class FileOperationTask(BaseTask):
    def __init__(self, file_manager, ui, executor):
        """Initialize task with dependencies.
        
        Args:
            file_manager: FileManager for task management
            ui: FileOperationsUI for UI interactions
            executor: FileOperationsExecutor for I/O operations
        """
        super().__init__(file_manager)
        self.ui = ui
        self.executor = executor
        self.state = State.IDLE
        self.context = None
```

### State Machine

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

### States

1. **IDLE**: Task is not active, waiting to be started
2. **CONFIRMING**: Showing confirmation dialog to user
3. **CHECKING_CONFLICTS**: Detecting file conflicts
4. **RESOLVING_CONFLICT**: User is resolving conflicts one by one
5. **EXECUTING**: Background thread is performing file operations
6. **COMPLETED**: Operation finished, about to return to IDLE

### Operation Context

All operation state is stored in a single `OperationContext` dataclass:

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

### Key Methods

#### Public API

```python
def start_operation(self, operation_type, files, destination=None):
    """Start a new file operation
    
    Args:
        operation_type: 'copy', 'move', or 'delete'
        files: List of Path objects to operate on
        destination: Destination Path (for copy/move only)
    """

def on_confirmed(self, confirmed):
    """Handle confirmation response from UI"""

def on_conflict_resolved(self, choice, apply_to_all=False):
    """Handle conflict resolution choice from UI"""

def on_renamed(self, source_file, new_name):
    """Handle rename confirmation from UI"""

def on_rename_cancelled(self):
    """Handle rename cancellation from UI"""
```

#### Internal Methods

```python
def _check_conflicts(self):
    """Detect file conflicts"""

def _resolve_next_conflict(self):
    """Show conflict dialog via ui.show_conflict_dialog()"""

def _show_rename_dialog(self, source_file):
    """Show rename dialog via ui.show_rename_dialog()"""

def _execute_operation(self):
    """Execute operation via executor.perform_*_operation()"""

def _complete_operation(self):
    """Complete the operation and return to IDLE"""
```

### UI Delegation

All UI interactions are delegated to FileOperationsUI:

```python
# Confirmation
self.ui.show_confirmation_dialog(
    operation_type, files, destination, self.on_confirmed
)

# Conflict resolution
self.ui.show_conflict_dialog(
    source_file, dest_file, choices, self.on_conflict_resolved
)

# Rename
self.ui.show_rename_dialog(
    source_file, destination, self.on_renamed, self.on_rename_cancelled
)
```

### I/O Delegation

All I/O operations are delegated to FileOperationsExecutor:

```python
# Copy
self.executor.perform_copy_operation(
    files_to_copy, destination, overwrite, self._complete_operation
)

# Move
self.executor.perform_move_operation(
    files_to_move, destination, overwrite, self._complete_operation
)

# Delete
self.executor.perform_delete_operation(
    files_to_delete, self._complete_operation
)
```

## Task Management

### FileManager Integration

FileManager maintains a single active task:

```python
class FileManager:
    def __init__(self, ...):
        self.current_task: Optional[BaseTask] = None
    
    def start_task(self, task: BaseTask):
        """Start a new task
        
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

### Task Lifecycle

1. **Creation**: Task is created by FileOperationsUI
2. **Starting**: Task is started via `file_manager.start_task()`
3. **Active**: Task manages state transitions and user interactions
4. **Completion**: Task transitions to IDLE and calls `file_manager._clear_task()`

## Migration Process

The migration from callback-based to task-based architecture was done incrementally:

### Phase 1: Create Task Framework
- Implemented `BaseTask` abstract class in `src/tfm_base_task.py`
- Added task management to `FileManager`
- Added unit tests for `BaseTask` interface

### Phase 2: Create FileOperationTask
- Implemented `FileOperationTask` class in `src/tfm_file_operation_task.py`
- Implemented `OperationContext` dataclass
- Added unit tests for `FileOperationTask`

### Phase 3: Integrate Copy Operations
- Refactored `copy_selected_files()` to use `FileOperationTask`
- Removed old copy conflict resolution methods
- Added integration tests

### Phase 4: Integrate Move Operations
- Refactored `move_selected_files()` to use `FileOperationTask`
- Removed old move conflict resolution methods
- Added integration tests

### Phase 5: Integrate Delete Operations
- Refactored `delete_selected_files()` to use `FileOperationTask`
- Added integration tests

### Phase 6: Cleanup
- Removed all old callback-based code
- Removed temporary context objects from `file_manager`
- Updated documentation

## Architecture Refactoring (Post-Task Framework)

After the task framework was implemented, a second refactoring addressed naming confusion and boundary violations:

### Phase 1: Create FileOperationsExecutor
- Created new `FileOperationsExecutor` class in `src/tfm_file_operations_executor.py`
- Moved I/O methods from `FileOperationsUI` to executor
- Added tests for executor

### Phase 2: Extract UI Methods from Task
- Added UI methods to `FileOperationsUI` (show_confirmation_dialog, etc.)
- Updated `FileOperationTask` to accept ui parameter
- Replaced direct UI calls in task with ui.show_*() calls

### Phase 3: Rename FileOperations to FileListManager
- Renamed `FileOperations` class to `FileListManager`
- Updated all imports and references
- Updated tests

### Phase 4: Update Task to Use Executor
- Updated `FileOperationTask` to accept executor parameter
- Replaced I/O calls with executor.perform_*() calls
- Updated tests

### Phase 5: Update FileManager Integration
- Created `file_list_manager` instance
- Created `file_operations_executor` instance
- Updated `file_operations_ui` initialization
- Removed old I/O methods from `FileOperationsUI`

### Phase 6: Update Tests
- Updated test imports for renamed classes
- Updated test mocks for new structure
- Added comprehensive executor tests
- Verified all tests pass

### Phase 7: Update Documentation
- Updated this document with refactored architecture
- Updated class docstrings
- Added architecture diagrams
- Added migration notes

## Benefits

### Before (Callback-Based)

Problems with the old approach:
- **Callback Hell**: Nested callbacks made code hard to follow
- **Scattered State**: Operation state spread across multiple context objects
- **Complex Threading**: Manual coordination between UI and worker threads
- **Difficult Testing**: Hard to test individual state transitions
- **Poor Maintainability**: Changes required updates in multiple places

### After (Task-Based)

Improvements with the new approach:
- **Clear State Transitions**: State machine makes workflow explicit
- **Encapsulated State**: All state in single context object
- **Simplified Threading**: Task coordinates threads internally
- **Easy Testing**: Each state transition can be tested independently
- **Better Maintainability**: Changes localized to task implementation

## Future Enhancements

### Task Queue Support

The framework is designed to support future task queueing:

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

### Future Task Implementations

The `BaseTask` framework can support many types of workflows:

1. **SearchTask**: Background search with progressive results display
2. **BatchRenameTask**: Multi-step batch rename with preview and confirmation
3. **ArchiveExtractionTask**: Archive extraction with progress and conflict resolution
4. **SyncTask**: Directory synchronization with conflict resolution
5. **CompareTask**: Directory comparison with diff display

### Task Composition

Future enhancement could allow composing multiple tasks into workflows:

```python
class CompositeTask(BaseTask):
    """Task that executes multiple sub-tasks in sequence"""
    
    def __init__(self, file_manager, tasks):
        super().__init__(file_manager)
        self.tasks = tasks
        self.current_task_index = 0
    
    def start(self):
        """Start the first sub-task"""
        if self.tasks:
            self.tasks[0].start()
    
    def _on_subtask_complete(self):
        """Called when a sub-task completes"""
        self.current_task_index += 1
        if self.current_task_index < len(self.tasks):
            self.tasks[self.current_task_index].start()
        else:
            # All sub-tasks complete
            self._complete()
```

## Implementation Files

### Core Framework
- `src/tfm_base_task.py`: BaseTask abstract class
- `src/tfm_file_operation_task.py`: FileOperationTask implementation

### Refactored Components
- `src/tfm_file_operations.py`: FileListManager (renamed from FileOperations)
- `src/tfm_file_operations_executor.py`: FileOperationsExecutor (new class for I/O)
- `src/tfm_main.py`: FileManager with refactored component initialization

### Integration Points
- `src/tfm_main.py`: FileManager task management and component wiring

### Tests
- `test/test_base_task.py`: BaseTask interface tests
- `test/test_file_operation_task.py`: FileOperationTask tests
- `test/test_file_operations_executor.py`: FileOperationsExecutor tests
- `test/test_file_operations_integration.py`: Integration tests
- `test/test_file_operations_refactoring.py`: Refactoring verification tests

## Usage Examples

### Creating and Starting a Task

```python
# In FileOperationsUI.copy_selected_files()
task = FileOperationTask(
    self.file_manager,
    ui=self,
    executor=self.file_manager.file_operations_executor
)
task.start_operation('copy', files_to_copy, destination_dir)
self.file_manager.start_task(task)
```

### Task Delegates to UI and Executor

```python
# Task delegates UI interactions to FileOperationsUI
def _resolve_next_conflict(self):
    self.ui.show_conflict_dialog(
        source_file, dest_file, choices, self.on_conflict_resolved
    )

# Task delegates I/O operations to FileOperationsExecutor
def _execute_operation(self):
    if self.context.operation_type == 'copy':
        self.executor.perform_copy_operation(
            files_to_copy, destination, overwrite, self._complete_operation
        )
```

### Cancelling a Task

```python
# User presses ESC during operation
if self.file_manager.current_task:
    self.file_manager.cancel_current_task()
```

## Thread Safety

### Main Thread
- All UI interactions (dialogs, rendering)
- State transitions
- Task lifecycle management

### Worker Thread
- File I/O operations
- Progress updates (via thread-safe flags)
- No direct curses calls

### Communication
- `operation_in_progress`: Flag to block user input
- `operation_cancelled`: Flag to signal cancellation
- `mark_dirty()`: Trigger UI refresh from worker thread
- `progress_manager`: Thread-safe progress tracking

## Performance Considerations

1. **State Transitions**: O(1) - simple state variable updates
2. **Conflict Detection**: O(n) - linear scan of files
3. **Conflict Resolution**: O(n) - process each conflict once
4. **Memory**: O(n) - store operation context with file lists
5. **Task Management**: O(1) - single task reference

No performance degradation compared to previous callback-based implementation.

## Testing Strategy

### Unit Tests
- Test each state transition independently
- Test conflict detection and resolution
- Test rename handling
- Test error handling

### Property-Based Tests
- Test task lifecycle validity
- Test single active task constraint
- Test state transition validity
- Test context cleanup

### Integration Tests
- Test complete copy operation flow
- Test complete move operation flow
- Test complete delete operation flow
- Test operation with UI interactions

## Backward Compatibility

The task framework maintains backward compatibility by:
1. Respecting all existing configuration options
2. Using existing dialog components
3. Using existing progress manager
4. Using existing cache manager
5. Maintaining existing log message formats
6. Supporting existing keyboard shortcuts
7. FileOperationsUI remains the public interface

The architecture refactoring also maintains backward compatibility:
1. All file operations work identically
2. All UI interactions unchanged
3. All configuration options preserved
4. All keyboard shortcuts preserved
5. No performance degradation

## Refactoring Notes

### What Changed

1. **FileOperations → FileListManager**: Class renamed to accurately reflect its responsibility (file list management, not file operations)

2. **FileOperationsExecutor Created**: New class extracts all I/O operations from FileOperationsUI into a dedicated executor

3. **FileOperationTask Dependencies**: Task now receives `ui` and `executor` parameters for clean dependency injection

4. **FileOperationsUI Simplified**: Removed all I/O methods, now only handles UI interactions

5. **Boundary Violations Fixed**: Each class now has a single, clear responsibility with no mixed concerns

### Why It Changed

1. **Naming Confusion**: `FileOperations` was misleading - it managed file lists, not file operations
2. **Mixed Responsibilities**: `FileOperationsUI` contained both UI code and I/O code
3. **Boundary Violations**: `FileOperationTask` contained UI code (show_dialog calls)
4. **Circular Dependencies**: Task called back to UI for I/O operations
5. **Testing Difficulty**: Mixed responsibilities made unit testing complex

### How to Adapt Code

If you're working with the file operations system:

1. **Import Changes**:
   ```python
   # Old
   from tfm_file_operations import FileOperations
   
   # New
   from tfm_file_operations import FileListManager
   ```

2. **Variable Names**:
   ```python
   # Old
   self.file_operations = FileOperations(config)
   
   # New
   self.file_list_manager = FileListManager(config)
   ```

3. **Task Creation**:
   ```python
   # Old
   task = FileOperationTask(file_manager, file_operations_ui)
   
   # New
   task = FileOperationTask(
       file_manager,
       ui=file_operations_ui,
       executor=file_manager.file_operations_executor
   )
   ```

4. **I/O Operations**:
   ```python
   # Old (in FileOperationsUI)
   self.perform_copy_operation(files, dest, callback)
   
   # New (use executor)
   self.file_manager.file_operations_executor.perform_copy_operation(
       files, dest, callback
   )
   ```

### Architecture Benefits

The refactored architecture provides:

1. **Clear Responsibilities**: Each class has one job
2. **Easy Testing**: Components can be tested independently
3. **No Circular Dependencies**: Clean one-way dependency flow
4. **Better Maintainability**: Changes localized to appropriate layer
5. **Accurate Naming**: Class names reflect actual responsibilities

## References

- **Task Framework Design**: `.kiro/specs/file-operations-state-machine/design.md`
- **Task Framework Requirements**: `.kiro/specs/file-operations-state-machine/requirements.md`
- **Task Framework Tasks**: `.kiro/specs/file-operations-state-machine/tasks.md`
- **Refactoring Design**: `.kiro/specs/file-operations-refactoring/design.md`
- **Refactoring Requirements**: `.kiro/specs/file-operations-refactoring/requirements.md`
- **Refactoring Tasks**: `.kiro/specs/file-operations-refactoring/tasks.md`
