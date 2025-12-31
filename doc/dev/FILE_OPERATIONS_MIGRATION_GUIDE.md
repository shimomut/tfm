# File Operations Architecture Migration Guide

## Overview

This guide documents the migration from the old file operations architecture to the refactored architecture. It explains what changed, why it changed, and how to adapt code that interacts with the file operations system.

## What Changed

### 1. FileOperations → FileListManager

**Change**: The `FileOperations` class has been renamed to `FileListManager`.

**Reason**: The old name was misleading. The class manages file lists (sorting, filtering, selection), not file operations (copy, move, delete).

**Impact**: All imports and references to `FileOperations` must be updated to `FileListManager`.

### 2. FileOperationsExecutor Created

**Change**: A new `FileOperationsExecutor` class has been created to handle all file I/O operations.

**Reason**: The old architecture had I/O code mixed into `FileOperationsUI`, violating separation of concerns. The executor extracts all I/O operations into a dedicated class.

**Impact**: File I/O operations are now performed by the executor, not by `FileOperationsUI`.

### 3. FileOperationTask Dependencies

**Change**: `FileOperationTask` now receives `ui` and `executor` parameters via dependency injection.

**Reason**: The task needs to delegate UI interactions to `FileOperationsUI` and I/O operations to `FileOperationsExecutor`. Dependency injection makes these dependencies explicit and testable.

**Impact**: Task creation code must pass both `ui` and `executor` parameters.

### 4. FileOperationsUI Simplified

**Change**: All I/O methods have been removed from `FileOperationsUI`. It now only handles UI interactions.

**Reason**: Mixed responsibilities made the class difficult to understand and test. Separating UI from I/O creates cleaner boundaries.

**Impact**: Code that called I/O methods on `FileOperationsUI` must now use `FileOperationsExecutor`.

### 5. UI Methods Added to FileOperationsUI

**Change**: New UI methods have been added: `show_confirmation_dialog()`, `show_conflict_dialog()`, `show_rename_dialog()`.

**Reason**: These methods centralize all UI interactions, making it clear where UI code lives.

**Impact**: `FileOperationTask` now calls these methods instead of calling `file_manager` methods directly.

## Why It Changed

### Problems with Old Architecture

1. **Naming Confusion**
   - `FileOperations` class name suggested it performed file operations
   - Actually managed file lists (sorting, filtering, selection)
   - Developers had to read the code to understand what it did

2. **Mixed Responsibilities**
   - `FileOperationsUI` contained both UI code and I/O code
   - Violated single responsibility principle
   - Made testing difficult (had to mock both UI and I/O)

3. **Boundary Violations**
   - `FileOperationTask` contained UI code (show_dialog calls)
   - Task should only orchestrate, not interact with UI directly
   - Made the state machine harder to understand

4. **Circular Dependencies**
   - Task called back to `FileOperationsUI` for I/O operations
   - `FileOperationsUI` created tasks
   - Created a circular dependency that complicated testing

5. **Testing Difficulty**
   - Mixed responsibilities made unit testing complex
   - Had to mock multiple concerns in single tests
   - Integration tests were the only way to test some functionality

### Benefits of New Architecture

1. **Clear Naming**
   - `FileListManager` accurately describes its purpose
   - `FileOperationsExecutor` clearly indicates it executes operations
   - No confusion about what each class does

2. **Single Responsibility**
   - Each class has one clear purpose
   - `FileListManager`: File list management
   - `FileOperationsUI`: UI interactions
   - `FileOperationTask`: Orchestration
   - `FileOperationsExecutor`: I/O operations

3. **No Boundary Violations**
   - UI code only in `FileOperationsUI`
   - I/O code only in `FileOperationsExecutor`
   - Orchestration code only in `FileOperationTask`
   - File list code only in `FileListManager`

4. **One-Way Dependencies**
   - Clean dependency flow: UI → Task → Executor
   - No circular dependencies
   - Easy to understand and test

5. **Easy Testing**
   - Each component can be tested independently
   - Mock only what you need for each test
   - Unit tests are straightforward

## How to Adapt Code

### Import Changes

**Old Code**:
```python
from tfm_file_operations import FileOperations
```

**New Code**:
```python
from tfm_file_operations import FileListManager
```

### Variable Name Changes

**Old Code**:
```python
self.file_operations = FileOperations(config)
```

**New Code**:
```python
self.file_list_manager = FileListManager(config)
```

### Task Creation Changes

**Old Code**:
```python
task = FileOperationTask(file_manager, file_operations_ui)
```

**New Code**:
```python
task = FileOperationTask(
    file_manager,
    ui=file_operations_ui,
    executor=file_manager.file_operations_executor
)
```

### I/O Operation Changes

**Old Code** (calling I/O on FileOperationsUI):
```python
self.file_operations_ui.perform_copy_operation(
    files_to_copy,
    destination_dir,
    overwrite=False,
    completion_callback=self._complete_operation
)
```

**New Code** (calling I/O on FileOperationsExecutor):
```python
self.executor.perform_copy_operation(
    files_to_copy,
    destination_dir,
    overwrite=False,
    completion_callback=self._complete_operation
)
```

### UI Interaction Changes

**Old Code** (task calling file_manager directly):
```python
self.file_manager.show_confirmation(message, callback)
```

**New Code** (task calling ui methods):
```python
self.ui.show_confirmation_dialog(
    operation_type,
    files,
    destination,
    callback
)
```

### FileManager Initialization Changes

**Old Code**:
```python
class FileManager:
    def __init__(self, ...):
        self.file_operations = FileOperations(self.config)
        self.file_operations_ui = FileOperationsUI(self, self.file_operations)
```

**New Code**:
```python
class FileManager:
    def __init__(self, ...):
        self.file_list_manager = FileListManager(self.config)
        self.file_operations_executor = FileOperationsExecutor(self)
        self.file_operations_ui = FileOperationsUI(self, self.file_list_manager)
```

## Migration Checklist

If you're updating code that interacts with the file operations system:

- [ ] Update imports: `FileOperations` → `FileListManager`
- [ ] Update variable names: `file_operations` → `file_list_manager`
- [ ] Update task creation to pass `ui` and `executor` parameters
- [ ] Update I/O calls to use `executor` instead of `file_operations_ui`
- [ ] Update UI calls to use `ui.show_*_dialog()` methods
- [ ] Update tests to mock the correct components
- [ ] Verify no circular dependencies in your code
- [ ] Run tests to ensure everything works

## Common Patterns

### Pattern 1: Creating and Starting a Task

**Old**:
```python
task = FileOperationTask(self.file_manager, self)
task.start_operation('copy', files, destination)
self.file_manager.start_task(task)
```

**New**:
```python
task = FileOperationTask(
    self.file_manager,
    ui=self,
    executor=self.file_manager.file_operations_executor
)
task.start_operation('copy', files, destination)
self.file_manager.start_task(task)
```

### Pattern 2: Delegating UI Interactions

**Old** (in FileOperationTask):
```python
self.file_manager.show_confirmation(message, self.on_confirmed)
```

**New** (in FileOperationTask):
```python
self.ui.show_confirmation_dialog(
    self.context.operation_type,
    self.context.files,
    self.context.destination,
    self.on_confirmed
)
```

### Pattern 3: Delegating I/O Operations

**Old** (in FileOperationTask):
```python
self.file_operations_ui.perform_copy_operation(
    files, destination, overwrite, self._complete_operation
)
```

**New** (in FileOperationTask):
```python
self.executor.perform_copy_operation(
    files, destination, overwrite, self._complete_operation
)
```

### Pattern 4: Accessing File List Operations

**Old**:
```python
self.file_operations.refresh_files(pane_data)
self.file_operations.sort_entries(entries, sort_mode)
```

**New**:
```python
self.file_list_manager.refresh_files(pane_data)
self.file_list_manager.sort_entries(entries, sort_mode)
```

## Testing Changes

### Unit Test Changes

**Old** (testing FileOperationsUI with I/O):
```python
def test_copy_operation():
    ui = FileOperationsUI(file_manager, file_operations)
    # Had to mock both UI and I/O
    ui.perform_copy_operation(files, dest, callback)
```

**New** (testing components separately):
```python
def test_executor_copy_operation():
    executor = FileOperationsExecutor(file_manager)
    # Only mock I/O concerns
    executor.perform_copy_operation(files, dest, callback)

def test_ui_confirmation_dialog():
    ui = FileOperationsUI(file_manager, file_list_manager)
    # Only mock UI concerns
    ui.show_confirmation_dialog('copy', files, dest, callback)
```

### Integration Test Changes

**Old**:
```python
def test_copy_integration():
    # Create FileOperationsUI
    # Create task
    # Test complete flow
```

**New**:
```python
def test_copy_integration():
    # Create FileListManager
    # Create FileOperationsExecutor
    # Create FileOperationsUI
    # Create task with ui and executor
    # Test complete flow
```

## Backward Compatibility

The refactoring maintains backward compatibility for:

1. **User-Facing Behavior**
   - All file operations work identically
   - All UI interactions unchanged
   - All keyboard shortcuts preserved
   - All configuration options respected

2. **External Interfaces**
   - `FileOperationsUI` remains the public interface
   - Entry points (copy/move/delete) unchanged
   - Configuration options unchanged

3. **Performance**
   - No performance degradation
   - Same threading model
   - Same progress tracking

## Breaking Changes

The following are breaking changes for code that directly interacts with the file operations system:

1. **Import Changes**: Must update imports from `FileOperations` to `FileListManager`
2. **Task Creation**: Must pass `ui` and `executor` parameters
3. **I/O Operations**: Must use `FileOperationsExecutor` instead of `FileOperationsUI`
4. **Variable Names**: Must update `file_operations` to `file_list_manager`

These changes only affect internal code. User-facing behavior is unchanged.

## Troubleshooting

### Issue: ImportError for FileOperations

**Problem**: Code tries to import `FileOperations` which no longer exists.

**Solution**: Update import to `FileListManager`:
```python
from tfm_file_operations import FileListManager
```

### Issue: AttributeError for perform_copy_operation on FileOperationsUI

**Problem**: Code tries to call `perform_copy_operation()` on `FileOperationsUI`, but this method has been removed.

**Solution**: Use `FileOperationsExecutor` instead:
```python
self.file_manager.file_operations_executor.perform_copy_operation(...)
```

### Issue: TypeError when creating FileOperationTask

**Problem**: Task creation fails because `ui` and `executor` parameters are missing.

**Solution**: Pass both parameters:
```python
task = FileOperationTask(
    file_manager,
    ui=file_operations_ui,
    executor=file_manager.file_operations_executor
)
```

### Issue: Tests failing after migration

**Problem**: Tests fail because they mock the wrong components.

**Solution**: Update test mocks to match new architecture:
- Mock `FileListManager` for file list operations
- Mock `FileOperationsExecutor` for I/O operations
- Mock `FileOperationsUI` for UI interactions
- Mock `FileOperationTask` for orchestration

## Timeline

The refactoring was completed in 7 phases:

1. **Phase 1**: Create FileOperationsExecutor class
2. **Phase 2**: Extract UI methods from FileOperationTask
3. **Phase 3**: Rename FileOperations to FileListManager
4. **Phase 4**: Update FileOperationTask to use executor
5. **Phase 5**: Update FileManager integration
6. **Phase 6**: Update tests
7. **Phase 7**: Update documentation

Each phase was tested independently to ensure correctness.

## References

- **Architecture Documentation**: `doc/dev/TASK_FRAMEWORK_IMPLEMENTATION.md`
- **Architecture Diagrams**: `doc/dev/FILE_OPERATIONS_ARCHITECTURE.md`
- **Refactoring Design**: `.kiro/specs/file-operations-refactoring/design.md`
- **Refactoring Requirements**: `.kiro/specs/file-operations-refactoring/requirements.md`
- **Refactoring Tasks**: `.kiro/specs/file-operations-refactoring/tasks.md`

## Questions?

If you have questions about the migration or need help adapting your code:

1. Review the architecture diagrams in `doc/dev/FILE_OPERATIONS_ARCHITECTURE.md`
2. Check the implementation documentation in `doc/dev/TASK_FRAMEWORK_IMPLEMENTATION.md`
3. Look at the test files for examples of the new patterns
4. Review the design document in `.kiro/specs/file-operations-refactoring/design.md`
