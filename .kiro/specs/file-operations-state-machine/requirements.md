# Requirements Document

## Introduction

This specification defines the requirements for refactoring the FileOperationsUI class to use an event-driven state machine pattern. The current implementation suffers from callback hell, scattered state management, and complex threading coordination. The state machine approach will provide clear state transitions, eliminate nested callbacks, and simplify the codebase.

## Glossary

- **Task**: An abstract base class representing a long-running operation with UI interactions and threading
- **State Machine**: A computational model that transitions between discrete states based on events and conditions
- **FileOperationTask**: A concrete task implementation for file operations (copy, move, delete)
- **Task Manager**: A component in FileManager that maintains and runs tasks
- **FileOperationsUI**: The class responsible for handling file operation UI interactions (copy, move, delete)
- **Worker Thread**: A background thread that performs file I/O operations
- **Main Thread**: The UI thread that handles curses rendering and user input
- **Conflict**: A situation where a destination file already exists during copy/move operations
- **Operation Context**: The complete state of an ongoing file operation including files, destination, and user choices

## Requirements

### Requirement 1: Abstract Task Base Class

**User Story:** As a developer, I want an abstract base class for tasks, so that I can implement various complex UI × threading workflows consistently.

#### Acceptance Criteria

1. THE System SHALL define an abstract BaseTask class with common task lifecycle methods
2. THE BaseTask SHALL define abstract methods: start(), cancel(), is_active(), get_state()
3. THE BaseTask SHALL provide hooks for state transitions: on_state_enter(), on_state_exit()
4. THE BaseTask SHALL maintain a reference to FileManager for UI interactions
5. THE BaseTask SHALL support task cancellation via a standard interface
6. THE BaseTask SHALL provide a standard way to check if the task is active

### Requirement 2: Task Manager Integration

**User Story:** As a developer, I want FileManager to manage tasks, so that complex operations can be coordinated centrally.

#### Acceptance Criteria

1. THE FileManager SHALL maintain a reference to the currently active task
2. THE FileManager SHALL provide a method to start a new task
3. THE FileManager SHALL prevent starting a new task when one is already active
4. THE FileManager SHALL provide a method to cancel the active task
5. THE FileManager SHALL clear the task reference when a task completes or is cancelled

### Requirement 3: FileOperationTask Implementation

**User Story:** As a developer, I want a FileOperationTask implementation, so that file operations use the task framework.

#### Acceptance Criteria

1. THE FileOperationTask SHALL inherit from BaseTask
2. THE FileOperationTask SHALL define discrete states: IDLE, CONFIRMING, CHECKING_CONFLICTS, RESOLVING_CONFLICT, EXECUTING, COMPLETED
3. THE FileOperationTask SHALL maintain a single operation context containing all operation state
4. THE FileOperationTask SHALL transition between states based on user input and operation results
5. THE FileOperationTask SHALL support copy, move, and delete operations
6. THE FileOperationTask SHALL prevent invalid state transitions

### Requirement 4: Confirmation Flow

**User Story:** As a user, I want to confirm file operations before they execute, so that I can prevent accidental data loss.

#### Acceptance Criteria

1. WHEN a file operation is initiated, THE System SHALL check configuration for confirmation requirement
2. IF confirmation is required, THE System SHALL display a confirmation dialog with operation details
3. WHEN the user confirms, THE System SHALL transition to conflict checking state
4. WHEN the user cancels, THE System SHALL transition to IDLE state and log cancellation
5. THE System SHALL display appropriate messages for single files vs multiple files

### Requirement 5: Conflict Detection

**User Story:** As a user, I want the system to detect file conflicts before operations execute, so that I can decide how to handle them.

#### Acceptance Criteria

1. WHEN checking conflicts for copy operations, THE System SHALL identify all destination files that already exist
2. WHEN checking conflicts for move operations, THE System SHALL identify all destination files that already exist
3. WHEN no conflicts exist, THE System SHALL proceed directly to execution
4. WHEN conflicts exist, THE System SHALL transition to conflict resolution state
5. THE System SHALL store all detected conflicts in the operation context

### Requirement 6: Conflict Resolution

**User Story:** As a user, I want to resolve file conflicts individually or in batch, so that I have control over how conflicts are handled.

#### Acceptance Criteria

1. WHEN resolving a conflict, THE System SHALL present options: Overwrite, Rename, Skip
2. WHEN the user selects Overwrite, THE System SHALL mark the file for overwrite and proceed to next conflict
3. WHEN the user selects Rename, THE System SHALL display a rename dialog
4. WHEN the user selects Skip, THE System SHALL mark the file as skipped and proceed to next conflict
5. WHEN the user holds Shift while selecting an option, THE System SHALL apply that choice to all remaining conflicts
6. WHEN all conflicts are resolved, THE System SHALL transition to execution state

### Requirement 7: Rename Handling

**User Story:** As a user, I want to rename files during conflict resolution, so that I can keep both the source and destination files.

#### Acceptance Criteria

1. WHEN a rename is requested, THE System SHALL display a text input dialog with the current filename
2. WHEN the user enters a new name, THE System SHALL validate it is not empty
3. WHEN the new name also conflicts, THE System SHALL show a secondary conflict dialog
4. WHEN the new name is unique, THE System SHALL mark the file for copy/move with the new name
5. WHEN the user cancels rename, THE System SHALL return to the conflict resolution dialog

### Requirement 8: Operation Execution

**User Story:** As a developer, I want file operations to execute in background threads, so that the UI remains responsive during long operations.

#### Acceptance Criteria

1. WHEN executing operations, THE System SHALL create a background worker thread
2. THE Worker_Thread SHALL process all resolved files (non-conflicting + resolved conflicts)
3. THE Worker_Thread SHALL update progress for each file processed
4. THE Worker_Thread SHALL handle errors gracefully and continue processing remaining files
5. THE Worker_Thread SHALL support cancellation via operation_cancelled flag
6. WHEN execution completes, THE System SHALL transition to COMPLETED state

### Requirement 9: Progress Tracking

**User Story:** As a user, I want to see progress during file operations, so that I know the operation is working and how long it will take.

#### Acceptance Criteria

1. WHEN an operation starts, THE System SHALL display a progress indicator
2. THE System SHALL update progress for each file processed
3. THE System SHALL show current filename being processed
4. THE System SHALL display error count if errors occur
5. THE System SHALL support animated progress indicators

### Requirement 10: Operation Completion

**User Story:** As a user, I want to see a summary when operations complete, so that I know what was accomplished.

#### Acceptance Criteria

1. WHEN an operation completes, THE System SHALL log a summary message
2. THE Summary SHALL include count of successful operations
3. THE Summary SHALL include count of skipped files
4. THE Summary SHALL include count of errors
5. WHEN the operation was cancelled, THE Summary SHALL indicate cancellation
6. THE System SHALL refresh file panes to show changes
7. THE System SHALL clear file selections after successful operations

### Requirement 11: State Persistence

**User Story:** As a developer, I want operation state to be self-contained, so that multiple operations don't interfere with each other.

#### Acceptance Criteria

1. THE State_Machine SHALL store all operation state in a single context object
2. THE State_Machine SHALL not use external context objects on file_manager
3. THE State_Machine SHALL support only one active operation at a time
4. WHEN an operation completes or is cancelled, THE State_Machine SHALL reset to IDLE state
5. THE State_Machine SHALL clear all operation context when transitioning to IDLE

### Requirement 12: Error Handling

**User Story:** As a user, I want errors to be handled gracefully, so that one error doesn't stop the entire operation.

#### Acceptance Criteria

1. WHEN a file operation fails, THE System SHALL log the error with filename and reason
2. THE System SHALL continue processing remaining files after an error
3. THE System SHALL track error count in operation results
4. THE System SHALL include error count in completion summary
5. WHEN multiple errors occur, THE System SHALL display a warning-level summary

### Requirement 13: Thread Safety

**User Story:** As a developer, I want thread-safe communication between worker and UI threads, so that the application doesn't crash or corrupt data.

#### Acceptance Criteria

1. THE Worker_Thread SHALL NOT call curses functions directly
2. THE Worker_Thread SHALL use mark_dirty() to trigger UI updates
3. THE State_Machine SHALL handle all UI interactions in the main thread
4. THE System SHALL use thread-safe flags for cancellation
5. THE System SHALL properly synchronize access to shared state

### Requirement 14: Backward Compatibility

**User Story:** As a user, I want the refactored system to behave identically to the current system, so that my workflow is not disrupted.

#### Acceptance Criteria

1. THE System SHALL support all existing configuration options (CONFIRM_COPY, CONFIRM_MOVE, CONFIRM_DELETE)
2. THE System SHALL support Shift+key for "apply to all" functionality
3. THE System SHALL support ESC to cancel operations
4. THE System SHALL maintain existing log message formats
5. THE System SHALL maintain existing progress display behavior
6. THE System SHALL maintain existing cache invalidation behavior

### Requirement 15: Code Organization

**User Story:** As a developer, I want the task framework to be a separate, testable module, so that it's easy to maintain and extend.

#### Acceptance Criteria

1. THE BaseTask SHALL be implemented as an abstract base class in a separate module
2. THE FileOperationTask SHALL be implemented in a separate module
3. THE Task classes SHALL not depend on FileOperationsUI implementation details
4. THE Task classes SHALL have a clear public API for starting and managing tasks
5. THE Task classes SHALL have clear callback methods for state transitions
6. THE Task classes SHALL be unit testable without requiring a full FileManager instance

### Requirement 16: Migration Path

**User Story:** As a developer, I want to migrate incrementally, so that I can test each operation type independently.

#### Acceptance Criteria

1. THE System SHALL support both old and new implementations during migration
2. THE System SHALL migrate copy operations first
3. THE System SHALL migrate move operations second
4. THE System SHALL migrate delete operations third
5. WHEN all operations are migrated, THE System SHALL remove old implementation code

### Requirement 17: Future Task Queue Support

**User Story:** As a developer, I want the task framework to support future task queueing, so that multiple operations can be queued and executed sequentially.

#### Acceptance Criteria

1. THE BaseTask SHALL be designed to support task queueing in the future
2. THE FileManager SHALL maintain a single active task for now
3. THE Task interface SHALL not prevent future queue implementation
4. THE Task lifecycle SHALL support being queued before execution
5. THE Task design SHALL allow for future priority-based queueing
