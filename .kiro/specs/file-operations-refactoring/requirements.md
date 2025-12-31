# Requirements Document: File Operations Architecture Refactoring

## Introduction

This specification defines the requirements for refactoring the file operations architecture to fix naming confusion and architectural boundary violations. The current implementation has misnamed classes and mixed responsibilities that make the codebase difficult to understand and maintain.

## Glossary

- **FileListManager**: Class responsible for file list management (sorting, filtering, selection)
- **FileOperationsUI**: Class responsible for UI interactions (dialogs, confirmations)
- **FileOperationTask**: Class responsible for orchestrating file operations (state machine)
- **FileOperationsExecutor**: Class responsible for executing file I/O operations (copy, move, delete)
- **Boundary Violation**: When a class contains code that belongs to a different architectural layer
- **Circular Dependency**: When two classes depend on each other, creating a cycle

## Requirements

### Requirement 1: Rename FileOperations to FileListManager

**User Story:** As a developer, I want FileOperations renamed to FileListManager, so that the class name accurately reflects its responsibilities.

#### Acceptance Criteria

1. THE System SHALL rename the FileOperations class to FileListManager
2. THE System SHALL update all imports of FileOperations to use FileListManager
3. THE System SHALL update all references to file_operations to use file_list_manager
4. THE System SHALL maintain all existing functionality during the rename
5. THE System SHALL update all test files to use the new class name

### Requirement 2: Create FileOperationsExecutor Class

**User Story:** As a developer, I want file I/O operations separated into a dedicated executor class, so that I/O logic is isolated from UI and orchestration logic.

#### Acceptance Criteria

1. THE System SHALL create a new FileOperationsExecutor class
2. THE FileOperationsExecutor SHALL contain perform_copy_operation() method
3. THE FileOperationsExecutor SHALL contain perform_move_operation() method
4. THE FileOperationsExecutor SHALL contain perform_delete_operation() method
5. THE FileOperationsExecutor SHALL handle progress tracking for all operations
6. THE FileOperationsExecutor SHALL handle error logging for all operations
7. THE FileOperationsExecutor SHALL execute operations in background threads
8. THE FileOperationsExecutor SHALL support cancellation via operation_cancelled flag

### Requirement 3: Extract UI Methods from FileOperationTask

**User Story:** As a developer, I want UI code removed from FileOperationTask, so that the task focuses solely on orchestration logic.

#### Acceptance Criteria

1. THE FileOperationTask SHALL NOT call file_manager.show_dialog() directly
2. THE FileOperationTask SHALL NOT call file_manager.show_confirmation() directly
3. THE FileOperationTask SHALL NOT call file_manager.quick_edit_bar methods directly
4. THE FileOperationTask SHALL NOT call file_manager.mark_dirty() directly
5. THE FileOperationTask SHALL delegate all UI interactions to FileOperationsUI
6. THE FileOperationTask SHALL receive UI callbacks via constructor injection

### Requirement 4: Add UI Methods to FileOperationsUI

**User Story:** As a developer, I want all UI interactions centralized in FileOperationsUI, so that UI logic is in one place.

#### Acceptance Criteria

1. THE FileOperationsUI SHALL provide show_confirmation_dialog() method
2. THE FileOperationsUI SHALL provide show_conflict_dialog() method
3. THE FileOperationsUI SHALL provide show_rename_dialog() method
4. THE FileOperationsUI SHALL handle all dialog creation and display
5. THE FileOperationsUI SHALL manage all QuickEditBar interactions
6. THE FileOperationsUI SHALL provide callback interfaces for task responses

### Requirement 5: Remove I/O Methods from FileOperationsUI

**User Story:** As a developer, I want I/O operations removed from FileOperationsUI, so that the UI layer doesn't contain file operations logic.

#### Acceptance Criteria

1. THE FileOperationsUI SHALL NOT contain perform_copy_operation() method
2. THE FileOperationsUI SHALL NOT contain perform_move_operation() method
3. THE FileOperationsUI SHALL NOT contain perform_delete_operation() method
4. THE FileOperationsUI SHALL NOT contain file I/O helper methods
5. THE FileOperationsUI SHALL delegate all I/O operations to FileOperationsExecutor

### Requirement 6: Update FileOperationTask Dependencies

**User Story:** As a developer, I want FileOperationTask to depend on clear interfaces, so that dependencies are explicit and testable.

#### Acceptance Criteria

1. THE FileOperationTask constructor SHALL accept ui parameter
2. THE FileOperationTask constructor SHALL accept executor parameter
3. THE FileOperationTask SHALL call ui methods for all UI interactions
4. THE FileOperationTask SHALL call executor methods for all I/O operations
5. THE FileOperationTask SHALL NOT have circular dependencies

### Requirement 7: Update FileManager Integration

**User Story:** As a developer, I want FileManager to properly initialize all components, so that the architecture is correctly wired.

#### Acceptance Criteria

1. THE FileManager SHALL create FileListManager instance
2. THE FileManager SHALL create FileOperationsExecutor instance
3. THE FileManager SHALL create FileOperationsUI instance with proper dependencies
4. THE FileManager SHALL update all references from file_operations to file_list_manager
5. THE FileManager SHALL maintain backward compatibility for existing functionality

### Requirement 8: Maintain Backward Compatibility

**User Story:** As a user, I want the refactored system to behave identically to the current system, so that my workflow is not disrupted.

#### Acceptance Criteria

1. THE System SHALL maintain all existing file operation functionality
2. THE System SHALL maintain all existing UI behavior
3. THE System SHALL maintain all existing configuration options
4. THE System SHALL maintain all existing keyboard shortcuts
5. THE System SHALL maintain all existing log message formats
6. THE System SHALL maintain all existing progress display behavior

### Requirement 9: Update Tests

**User Story:** As a developer, I want all tests updated for the new architecture, so that test coverage is maintained.

#### Acceptance Criteria

1. THE System SHALL update all test imports for renamed classes
2. THE System SHALL update all test mocks for new class structure
3. THE System SHALL add tests for FileOperationsExecutor
4. THE System SHALL maintain all existing test coverage
5. THE System SHALL ensure all tests pass after refactoring

### Requirement 10: Update Documentation

**User Story:** As a developer, I want documentation updated for the new architecture, so that the system is well-documented.

#### Acceptance Criteria

1. THE System SHALL update TASK_FRAMEWORK_IMPLEMENTATION.md with new architecture
2. THE System SHALL update all class docstrings
3. THE System SHALL update architecture diagrams
4. THE System SHALL add migration notes for developers
5. THE System SHALL document the new class responsibilities

### Requirement 11: Eliminate Circular Dependencies

**User Story:** As a developer, I want no circular dependencies between classes, so that the architecture is clean and maintainable.

#### Acceptance Criteria

1. THE FileOperationsUI SHALL NOT depend on FileOperationTask
2. THE FileOperationTask SHALL NOT depend on FileOperationsUI for I/O operations
3. THE FileOperationsExecutor SHALL NOT depend on FileOperationTask
4. THE System SHALL have one-way dependency flow: UI → Task → Executor
5. THE System SHALL allow dependency injection for testing

### Requirement 12: Preserve Task Framework Pattern

**User Story:** As a developer, I want the task framework pattern preserved, so that it can be reused for other operations.

#### Acceptance Criteria

1. THE BaseTask abstract class SHALL remain unchanged
2. THE FileOperationTask SHALL continue to inherit from BaseTask
3. THE Task framework SHALL support future task implementations
4. THE Task lifecycle methods SHALL remain consistent
5. THE FileManager task management SHALL remain unchanged

### Requirement 13: Clean Separation of Concerns

**User Story:** As a developer, I want each class to have a single, clear responsibility, so that the codebase is maintainable.

#### Acceptance Criteria

1. THE FileListManager SHALL only handle file list management
2. THE FileOperationsUI SHALL only handle UI interactions
3. THE FileOperationTask SHALL only handle orchestration logic
4. THE FileOperationsExecutor SHALL only handle I/O operations
5. THE System SHALL have no mixed responsibilities in any class

### Requirement 14: Incremental Migration

**User Story:** As a developer, I want the refactoring done incrementally, so that each step can be tested independently.

#### Acceptance Criteria

1. THE System SHALL implement changes in discrete phases
2. THE System SHALL run tests after each phase
3. THE System SHALL commit code after each successful phase
4. THE System SHALL allow rollback if a phase fails
5. THE System SHALL maintain working code throughout migration

### Requirement 15: Performance Preservation

**User Story:** As a user, I want no performance degradation from the refactoring, so that operations remain fast.

#### Acceptance Criteria

1. THE System SHALL maintain current operation performance
2. THE System SHALL not add unnecessary object creation overhead
3. THE System SHALL maintain efficient progress tracking
4. THE System SHALL maintain efficient thread management
5. THE System SHALL not introduce memory leaks
