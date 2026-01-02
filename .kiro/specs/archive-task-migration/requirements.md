# Requirements Document

## Introduction

This specification defines the requirements for migrating archive creation and extraction operations to the unified task system with threading support. Currently, archive operations (create_archive and extract_archive) are implemented as synchronous blocking operations in the ArchiveOperations class. This migration will integrate them into the existing task framework used by file operations (copy, move, delete), providing consistent user experience, progress tracking, cancellation support, and non-blocking execution.

## Glossary

- **Archive_System**: The existing archive handling infrastructure including ArchiveOperations, ArchiveHandler, and related classes
- **Task_Framework**: The unified task system consisting of BaseTask, FileOperationTask, FileOperationExecutor, and FileOperationUI
- **Archive_Task**: The new task implementation for archive operations (ArchiveOperationTask) that will integrate with the Task_Framework
- **Archive_Executor**: The new executor component (ArchiveOperationExecutor) that will handle archive I/O operations in background threads
- **Archive_UI**: The new UI component (ArchiveOperationUI) that will handle user interactions for archive operations
- **Progress_Manager**: The existing system for tracking and displaying operation progress
- **File_Manager**: The main application controller that manages tasks and UI interactions
- **Archive_Operation**: Either archive creation or extraction operation
- **Cross_Storage**: Operations involving different storage backends (local, S3, etc.)

## Requirements

### Requirement 1: Archive Task Implementation

**User Story:** As a developer, I want archive operations to use the task framework, so that they have consistent architecture with file operations.

#### Acceptance Criteria

1. THE Archive_Task SHALL extend BaseTask following the same pattern as FileOperationTask
2. THE Archive_Task SHALL implement a state machine with states: IDLE, CONFIRMING, CHECKING_CONFLICTS, RESOLVING_CONFLICT, EXECUTING, COMPLETED
3. THE Archive_Task SHALL support both archive creation and extraction operations
4. THE Archive_Task SHALL delegate UI interactions to ArchiveOperationUI
5. THE Archive_Task SHALL delegate I/O operations to ArchiveOperationExecutor

### Requirement 2: Archive Executor Implementation

**User Story:** As a developer, I want archive I/O operations separated from task orchestration, so that concerns are properly separated.

#### Acceptance Criteria

1. THE Archive_Executor SHALL follow the same architectural pattern as FileOperationExecutor
2. THE Archive_Executor SHALL execute archive operations in background threads
3. THE Archive_Executor SHALL use Progress_Manager for progress tracking
4. THE Archive_Executor SHALL support operation cancellation via operation_cancelled flag
5. THE Archive_Executor SHALL handle both local and cross-storage archive operations

### Requirement 3: Threading Support

**User Story:** As a user, I want archive operations to run in the background, so that the UI remains responsive during long operations.

#### Acceptance Criteria

1. WHEN an archive operation starts, THE Archive_Executor SHALL create a background thread for execution
2. WHILE an archive operation is running, THE File_Manager SHALL remain responsive to user input
3. WHEN an archive operation is running, THE Progress_Manager SHALL display animated progress
4. WHEN an archive operation completes, THE background thread SHALL terminate cleanly
5. THE Archive_Executor SHALL use daemon threads to prevent blocking application shutdown

### Requirement 4: Progress Tracking

**User Story:** As a user, I want to see progress during archive operations, so that I know the operation is working and how long it will take.

#### Acceptance Criteria

1. WHEN counting files for an archive operation, THE Archive_Executor SHALL display "Preparing..." message
2. WHEN processing files during archive creation, THE Progress_Manager SHALL update progress for each file added
3. WHEN processing files during archive extraction, THE Progress_Manager SHALL update progress for each file extracted
4. WHEN an archive operation completes, THE Progress_Manager SHALL display completion summary
5. THE Progress_Manager SHALL track and display error count separately from success count

### Requirement 5: Cancellation Support

**User Story:** As a user, I want to cancel long-running archive operations, so that I can stop operations I no longer need.

#### Acceptance Criteria

1. WHEN a user presses ESC during an archive operation, THE Archive_Task SHALL set operation_cancelled flag
2. WHEN operation_cancelled is set, THE Archive_Executor SHALL stop processing remaining files
3. WHEN an archive operation is cancelled, THE Progress_Manager SHALL display cancellation message
4. WHEN an archive operation is cancelled, THE Archive_Task SHALL transition to IDLE state
5. WHEN an archive operation is cancelled, THE File_Manager SHALL clear the task

### Requirement 6: Confirmation Dialogs

**User Story:** As a user, I want to confirm archive operations before they execute, so that I can prevent accidental operations.

#### Acceptance Criteria

1. WHEN starting an archive creation operation, THE Archive_Task SHALL show confirmation dialog if configured
2. WHEN starting an archive extraction operation, THE Archive_Task SHALL show confirmation dialog if configured
3. WHEN a user confirms an operation, THE Archive_Task SHALL transition to EXECUTING state
4. WHEN a user cancels confirmation, THE Archive_Task SHALL transition to IDLE state
5. THE confirmation requirement SHALL be configurable via CONFIRM_ARCHIVE_CREATE and CONFIRM_ARCHIVE_EXTRACT settings

### Requirement 7: Error Handling

**User Story:** As a user, I want clear error messages when archive operations fail, so that I understand what went wrong.

#### Acceptance Criteria

1. WHEN an archive operation encounters an error, THE Archive_Executor SHALL log the error with context
2. WHEN an archive operation encounters an error, THE Archive_Executor SHALL increment error count
3. WHEN an archive operation encounters an error, THE Archive_Executor SHALL continue processing remaining files
4. WHEN an archive operation completes with errors, THE Progress_Manager SHALL display error count
5. THE Archive_Executor SHALL handle PermissionError, OSError, and ArchiveError exceptions appropriately

### Requirement 8: Class Naming Consistency

**User Story:** As a developer, I want consistent naming between archive and file operation classes, so that the codebase is easier to understand.

#### Acceptance Criteria

1. THE new archive task class SHALL be named ArchiveOperationTask to match FileOperationTask pattern
2. THE new archive executor class SHALL be named ArchiveOperationExecutor to match FileOperationExecutor pattern
3. THE new archive UI class SHALL be named ArchiveOperationUI to match FileOperationUI pattern
4. THE Archive_System SHALL maintain ArchiveOperations as the high-level interface class
5. THE ArchiveOperations class SHALL delegate to ArchiveOperationTask for task management
6. ALL new archive operation classes SHALL use the ArchiveOperation prefix for consistency

### Requirement 9: Integration with Existing Code

**User Story:** As a developer, I want the migration to preserve existing functionality, so that no features are lost.

#### Acceptance Criteria

1. THE ArchiveOperations.create_archive method SHALL delegate to ArchiveOperationTask
2. THE ArchiveOperations.extract_archive method SHALL delegate to ArchiveOperationTask
3. THE Archive_Task SHALL support all existing archive formats (tar, tar.gz, tar.bz2, tar.xz, zip)
4. THE Archive_Task SHALL support cross-storage operations (local to S3, S3 to local, etc.)
5. THE Archive_Task SHALL invalidate cache after successful operations

### Requirement 10: Completion Callbacks

**User Story:** As a developer, I want completion callbacks for archive operations, so that I can perform actions after operations complete.

#### Acceptance Criteria

1. THE Archive_Executor SHALL accept optional completion_callback parameter
2. WHEN an archive operation completes, THE Archive_Executor SHALL call completion_callback with (success_count, error_count)
3. WHEN a completion_callback is provided, THE Archive_Executor SHALL suppress default summary logging
4. THE completion_callback SHALL be called on the background thread
5. THE completion_callback SHALL be called even if the operation is cancelled

### Requirement 11: UI Refresh and State Management

**User Story:** As a user, I want the file list to refresh after archive operations, so that I see the results immediately.

#### Acceptance Criteria

1. WHEN an archive creation completes successfully, THE File_Manager SHALL refresh the file list
2. WHEN an archive extraction completes successfully, THE File_Manager SHALL refresh the file list
3. WHEN an archive operation completes, THE File_Manager SHALL mark the UI as dirty to trigger redraw
4. WHEN an archive operation completes, THE Archive_Task SHALL clear operation_in_progress flag
5. WHEN an archive operation completes, THE Archive_Task SHALL transition to COMPLETED then IDLE state

### Requirement 12: Backward Compatibility

**User Story:** As a developer, I want the migration to maintain backward compatibility, so that existing code continues to work during the transition.

#### Acceptance Criteria

1. THE ArchiveOperations class SHALL maintain its existing public API
2. THE ArchiveOperations.create_archive method SHALL return boolean indicating success
3. THE ArchiveOperations.extract_archive method SHALL return boolean indicating success
4. THE migration SHALL not break existing callers of archive operations
5. THE migration SHALL allow gradual transition from synchronous to asynchronous usage

### Requirement 13: Conflict Detection and Resolution

**User Story:** As a user, I want to be notified of conflicts before archive operations execute, so that I can decide whether to proceed or cancel.

#### Acceptance Criteria

1. WHEN starting an archive creation operation, THE Archive_Task SHALL check if the destination archive file already exists
2. WHEN starting an archive extraction operation, THE Archive_Task SHALL check if any files in the archive would overwrite existing files in the destination directory
3. WHEN a conflict is detected, THE Archive_Task SHALL transition to CHECKING_CONFLICTS state
4. WHEN conflicts are found, THE Archive_Task SHALL transition to RESOLVING_CONFLICT state and show conflict dialog
5. THE conflict dialog SHALL present options: "Overwrite" and "Skip" (Skip only applicable for extraction with multiple files)
6. WHEN user presses ESC during conflict resolution, THE Archive_Task SHALL cancel the operation and transition to IDLE state
7. WHEN user selects "Overwrite", THE Archive_Task SHALL proceed with the operation and overwrite conflicting files
8. WHEN user selects "Skip", THE Archive_Task SHALL skip conflicting files during extraction
9. WHEN user selects an option with Shift modifier key, THE Archive_Task SHALL apply the decision to all remaining conflicts
10. WHEN no conflicts are detected, THE Archive_Task SHALL proceed directly to EXECUTING state
11. FOR archive creation conflicts, THE conflict dialog SHALL show the existing archive filename and size
12. FOR archive extraction conflicts with multiple files, THE conflict dialog SHALL show conflict count and current file being processed
13. FOR archive extraction conflicts with single file, THE Skip option SHALL not be shown
