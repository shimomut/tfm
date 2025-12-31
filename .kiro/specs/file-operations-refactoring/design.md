# Design Document: File Operations Architecture Refactoring

## Overview

This design document describes the refactoring of the file operations architecture to achieve proper separation of concerns and accurate naming. The refactoring addresses two main issues:

1. **Naming Confusion**: The `FileOperations` class is misnamed - it handles file list management, not file operations
2. **Boundary Violations**: `FileOperationTask` contains UI code, and `FileOperationsUI` contains I/O code

The solution creates a clean four-layer architecture with clear responsibilities and one-way dependencies.

## Architecture

### Current Architecture (Problems)

```
┌─────────────────────────────────────────┐
│ FileOperations                          │  ← MISNAMED
│ (Actually: file list management)        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ FileOperationsUI                        │  ← MIXED RESPONSIBILITIES
│ - Entry points (copy/move/delete)      │     (UI + I/O)
│ - I/O operations (perform_*)            │
└──────────────┬──────────────────────────┘
               │ creates
               ↓
┌─────────────────────────────────────────┐
│ FileOperationTask                       │  ← BOUNDARY VIOLATION
│ - State machine                         │     (contains UI code)
│ - show_dialog() calls                   │
│ - show_confirmation() calls             │
│ - QuickEditBar usage                    │
│ - Calls back to FileOperationsUI       │  ← CIRCULAR DEPENDENCY
└─────────────────────────────────────────┘
```

### Target Architecture (Clean)

```
┌─────────────────────────────────────────┐
│ FileListManager                         │  Layer 1: File List Management
│ - refresh_files()                       │
│ - sort_entries()                        │
│ - toggle_selection()                    │
│ - apply_filter()                        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ FileOperationsUI                        │  Layer 2: UI Interactions
│ - show_confirmation_dialog()            │
│ - show_conflict_dialog()                │
│ - show_rename_dialog()                  │
│ - Entry points (copy/move/delete)      │
└──────────────┬──────────────────────────┘
               │ creates & provides callbacks
               ↓
┌─────────────────────────────────────────┐
│ FileOperationTask                       │  Layer 3: Orchestration
│ - State machine logic                   │
│ - Conflict detection                    │
│ - Workflow coordination                 │
│ - Calls ui.show_*() methods             │
│ - Calls executor.perform_*() methods    │
└──────────────┬──────────────────────────┘
               │ delegates I/O
               ↓
┌─────────────────────────────────────────┐
│ FileOperationsExecutor                  │  Layer 4: I/O Operations
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
    ├── creates FileListManager
    ├── creates FileOperationsExecutor
    └── creates FileOperationsUI
            └── creates FileOperationTask(ui=self, executor=executor)
                    ├── calls ui.show_*() for UI
                    └── calls executor.perform_*() for I/O
```

## Components and Interfaces

### FileListManager (Renamed from FileOperations)

```python
class FileListManager:
    """Manages file lists, sorting, filtering, and selection.
    
    This class handles all file list management operations for file panes,
    including refreshing directory contents, sorting entries, applying filters,
    and managing file selection state.
    """
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
        self.show_hidden = getattr(config, 'SHOW_HIDDEN_FILES', False)
        self.logger = getLogger("FileList")
    
    def refresh_files(self, pane_data):
        """Refresh the file list for specified pane."""
        pass
    
    def sort_entries(self, entries, sort_mode, reverse=False):
        """Sort file entries based on the specified mode."""
        pass
    
    def get_file_info(self, path):
        """Get file information for display."""
        pass
    
    def toggle_selection(self, pane_data, move_cursor=True, direction=1):
        """Toggle selection of current file/directory."""
        pass
    
    def apply_filter(self, pane_data, pattern):
        """Apply filename filter to the specified pane."""
        pass
    
    # ... other file list management methods
```

### FileOperationsUI (Refactored)

```python
class FileOperationsUI:
    """Handles file operation UI interactions.
    
    This class provides the user interface layer for file operations,
    including confirmation dialogs, conflict resolution dialogs, and
    rename dialogs. It creates and starts FileOperationTask instances.
    """
    
    def __init__(self, file_manager, file_list_manager):
        """Initialize with file manager and file list manager.
        
        Args:
            file_manager: FileManager instance for UI access
            file_list_manager: FileListManager for file list operations
        """
        self.file_manager = file_manager
        self.file_list_manager = file_list_manager
        self.logger = getLogger("FileOpUI")
    
    # Entry points (unchanged)
    def copy_selected_files(self):
        """Entry point for copy operation."""
        # Get files to copy
        # Validate operation
        # Create task with ui=self, executor=file_manager.file_operations_executor
        # Start task
        pass
    
    def move_selected_files(self):
        """Entry point for move operation."""
        pass
    
    def delete_selected_files(self):
        """Entry point for delete operation."""
        pass
    
    # New UI methods (extracted from FileOperationTask)
    def show_confirmation_dialog(self, operation_type, files, destination, callback):
        """Show confirmation dialog for file operation.
        
        Args:
            operation_type: 'copy', 'move', or 'delete'
            files: List of files to operate on
            destination: Destination path (for copy/move)
            callback: Function to call with confirmation result (True/False)
        """
        message = self._build_confirmation_message(operation_type, files, destination)
        self.file_manager.show_confirmation(message, callback)
    
    def show_conflict_dialog(self, source_file, dest_file, choices, callback):
        """Show conflict resolution dialog.
        
        Args:
            source_file: Source file path
            dest_file: Destination file path
            choices: List of choice dictionaries
            callback: Function to call with user's choice
        """
        message = f"File '{dest_file.name}' already exists.\n\nWhat would you like to do?"
        self.file_manager.show_dialog(message, choices, callback)
    
    def show_rename_dialog(self, source_file, destination, callback, cancel_callback):
        """Show rename dialog.
        
        Args:
            source_file: Source file to rename
            destination: Destination directory
            callback: Function to call with new name
            cancel_callback: Function to call if cancelled
        """
        prompt = f"Rename '{source_file.name}' to:"
        self.file_manager.quick_edit_bar.show_status_line_input(
            prompt=prompt,
            initial_text=source_file.name,
            on_confirm=lambda new_name: callback(source_file, new_name),
            on_cancel=cancel_callback
        )
        self.file_manager.mark_dirty()
    
    # Helper methods
    def _build_confirmation_message(self, operation_type, files, destination):
        """Build confirmation message for operation."""
        pass
    
    def _validate_operation_capabilities(self, operation, source_paths, dest_path=None):
        """Validate if operation is allowed based on storage capabilities."""
        pass
```

### FileOperationTask (Refactored)

```python
class FileOperationTask(BaseTask):
    """Task for file operations - pure orchestration.
    
    This class orchestrates file operations using a state machine pattern.
    It delegates UI interactions to FileOperationsUI and I/O operations
    to FileOperationsExecutor, maintaining clean separation of concerns.
    """
    
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
    
    def start_operation(self, operation_type, files, destination=None):
        """Start a new file operation."""
        # Create context
        # Transition to CONFIRMING
        # Show confirmation via UI
        self._transition_to_state(State.CONFIRMING)
        
        if self._should_confirm():
            self.ui.show_confirmation_dialog(
                operation_type,
                files,
                destination,
                self.on_confirmed
            )
        else:
            self.on_confirmed(True)
    
    def on_confirmed(self, confirmed):
        """Handle confirmation response."""
        if confirmed:
            self._transition_to_state(State.CHECKING_CONFLICTS)
            self._check_conflicts()
        else:
            self._transition_to_state(State.IDLE)
            self.file_manager._clear_task()
    
    def _check_conflicts(self):
        """Check for file conflicts."""
        # Detect conflicts
        if conflicts:
            self._transition_to_state(State.RESOLVING_CONFLICT)
            self._resolve_next_conflict()
        else:
            self._transition_to_state(State.EXECUTING)
            self._execute_operation()
    
    def _resolve_next_conflict(self):
        """Resolve next conflict via UI."""
        conflict = self.context.conflicts[self.context.current_conflict_index]
        choices = [
            {"text": "Overwrite", "key": "o", "value": "overwrite"},
            {"text": "Rename", "key": "r", "value": "rename"},
            {"text": "Skip", "key": "s", "value": "skip"}
        ]
        self.ui.show_conflict_dialog(
            conflict[0],  # source
            conflict[1],  # dest
            choices,
            self.on_conflict_resolved
        )
    
    def on_conflict_resolved(self, choice, apply_to_all=False):
        """Handle conflict resolution choice."""
        if choice == 'rename':
            self.ui.show_rename_dialog(
                source_file,
                destination,
                self.on_renamed,
                self.on_rename_cancelled
            )
        else:
            # Process choice
            # Move to next conflict or execute
            pass
    
    def _execute_operation(self):
        """Execute operation via executor."""
        self._transition_to_state(State.EXECUTING)
        
        if self.context.operation_type == 'copy':
            self.executor.perform_copy_operation(
                files_to_copy,
                self.context.destination,
                overwrite=False,
                completion_callback=self._complete_operation
            )
        elif self.context.operation_type == 'move':
            self.executor.perform_move_operation(
                files_to_move,
                self.context.destination,
                overwrite=False,
                completion_callback=self._complete_operation
            )
        elif self.context.operation_type == 'delete':
            self.executor.perform_delete_operation(
                files_to_delete,
                completion_callback=self._complete_operation
            )
    
    # No UI code - all delegated to self.ui
    # No I/O code - all delegated to self.executor
```

### FileOperationsExecutor (New Class)

```python
class FileOperationsExecutor:
    """Executes file operations with progress tracking.
    
    This class handles the actual file I/O operations (copy, move, delete)
    in background threads with fine-grained progress tracking and error handling.
    """
    
    def __init__(self, file_manager):
        """Initialize executor with file manager.
        
        Args:
            file_manager: FileManager for progress and cache management
        """
        self.file_manager = file_manager
        self.progress_manager = file_manager.progress_manager
        self.cache_manager = file_manager.cache_manager
        self.logger = getLogger("FileExec")
    
    def perform_copy_operation(self, files_to_copy, destination_dir, 
                               overwrite=False, completion_callback=None):
        """Perform copy operation in background thread.
        
        Args:
            files_to_copy: List of (source, dest, overwrite) tuples
            destination_dir: Destination directory path
            overwrite: Whether to overwrite existing files
            completion_callback: Function to call when complete
        """
        def copy_worker():
            # Count total files
            # Start progress tracking
            # Copy each file with progress updates
            # Handle errors
            # Call completion callback
            pass
        
        thread = threading.Thread(target=copy_worker, daemon=True)
        thread.start()
    
    def perform_move_operation(self, files_to_move, destination_dir,
                               overwrite=False, completion_callback=None):
        """Perform move operation in background thread."""
        pass
    
    def perform_delete_operation(self, files_to_delete, completion_callback=None):
        """Perform delete operation in background thread."""
        pass
    
    # All helper methods for file I/O
    def _copy_file_with_progress(self, source_file, dest_file, overwrite=False):
        """Copy single file with byte-level progress tracking."""
        pass
    
    def _copy_directory_with_progress(self, source_dir, dest_dir, processed_files, total_files):
        """Copy directory recursively with progress updates."""
        pass
    
    # ... all other I/O helper methods
```

## Data Models

### Class Responsibilities Matrix

| Class | UI | Orchestration | I/O | File List |
|-------|----|--------------|----|-----------|
| FileListManager | ❌ | ❌ | ❌ | ✅ |
| FileOperationsUI | ✅ | ❌ | ❌ | ❌ |
| FileOperationTask | ❌ | ✅ | ❌ | ❌ |
| FileOperationsExecutor | ❌ | ❌ | ✅ | ❌ |

### Dependency Graph

```
FileManager
    │
    ├─→ FileListManager (no dependencies)
    │
    ├─→ FileOperationsExecutor
    │       └─→ FileManager (for progress, cache)
    │
    └─→ FileOperationsUI
            ├─→ FileManager (for UI access)
            ├─→ FileListManager (for file list ops)
            └─→ creates FileOperationTask
                    ├─→ FileOperationsUI (for UI)
                    └─→ FileOperationsExecutor (for I/O)
```

## Migration Strategy

### Phase 1: Create FileOperationsExecutor

1. Create new file `src/tfm_file_operations_executor.py`
2. Move I/O methods from FileOperationsUI to FileOperationsExecutor
3. Update FileOperationsExecutor to use file_manager for progress/cache
4. Test executor independently

### Phase 2: Extract UI Methods from Task

1. Add UI methods to FileOperationsUI (show_confirmation_dialog, etc.)
2. Update FileOperationTask to accept ui parameter
3. Replace direct UI calls in task with ui.show_*() calls
4. Test task with new UI interface

### Phase 3: Rename FileOperations

1. Rename FileOperations class to FileListManager
2. Update all imports in tfm_main.py
3. Update all test imports
4. Run tests to verify

### Phase 4: Update Task to Use Executor

1. Update FileOperationTask to accept executor parameter
2. Replace calls to file_operations_ui.perform_*() with executor.perform_*()
3. Test task with executor

### Phase 5: Update FileManager

1. Create file_list_manager instance
2. Create file_operations_executor instance
3. Update file_operations_ui initialization
4. Update all references from file_operations to file_list_manager
5. Test integration

### Phase 6: Update Tests

1. Update test imports for renamed classes
2. Update test mocks for new structure
3. Add tests for FileOperationsExecutor
4. Run full test suite

### Phase 7: Update Documentation

1. Update TASK_FRAMEWORK_IMPLEMENTATION.md
2. Update class docstrings
3. Update architecture diagrams
4. Add migration notes

## Error Handling

All error handling remains unchanged from current implementation:
- File I/O errors logged and tracked in results
- Operations continue after individual file errors
- Completion summary includes error counts
- Thread errors properly handled and logged

## Testing Strategy

### Unit Tests

- Test FileListManager methods independently
- Test FileOperationsUI dialog methods
- Test FileOperationTask state transitions
- Test FileOperationsExecutor I/O operations

### Integration Tests

- Test complete copy operation flow
- Test complete move operation flow
- Test complete delete operation flow
- Test conflict resolution flows
- Test cancellation

### Regression Tests

- Verify all existing tests still pass
- Verify no behavior changes
- Verify performance unchanged

## Performance Considerations

- No additional object creation overhead (same number of objects)
- No additional method call overhead (same call depth)
- Thread management unchanged
- Progress tracking unchanged
- Memory usage unchanged

## Backward Compatibility

- All existing functionality preserved
- All configuration options unchanged
- All keyboard shortcuts unchanged
- All log messages unchanged
- All UI behavior unchanged

## Dependencies

- No new external dependencies
- Internal dependencies clarified and simplified
- Circular dependencies eliminated
