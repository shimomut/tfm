# Implementation Plan: Archive Task Migration

## Overview

This implementation plan migrates archive creation and extraction operations from synchronous blocking operations to the unified task framework with threading support. The migration follows established patterns from FileOperationTask, FileOperationExecutor, and FileOperationUI.

The implementation will create three new components and modify the existing ArchiveOperations class to delegate to the new task-based system while maintaining backward compatibility.

## Tasks

- [x] 1. Create ArchiveOperationTask with state machine
  - Create `src/tfm_archive_operation_task.py` with ArchiveOperationTask class
  - Implement state machine: IDLE → CONFIRMING → CHECKING_CONFLICTS → RESOLVING_CONFLICT → EXECUTING → COMPLETED
  - Implement ArchiveOperationContext dataclass with operation_type, source_paths, destination, format_type, conflicts, results, options
  - Implement state transition methods: `start_operation()`, `on_confirmed()`, `on_conflict_resolved()`
  - Add logger initialization: `self.logger = getLogger("ArchiveOp")`
  - _Requirements: 1.1, 1.2, 1.3, 6.1, 6.2, 6.3, 6.4_

- [ ]* 1.1 Write property test for state machine transitions
  - **Property 1: State Machine Transitions**
  - **Validates: Requirements 1.2, 6.3, 6.4, 13.3, 13.4, 13.6, 13.10**

- [x] 2. Create ArchiveOperationExecutor with threading
  - Create `src/tfm_archive_operation_executor.py` with ArchiveOperationExecutor class
  - Migrate `create_archive()` logic from ArchiveOperations to `perform_create_operation()` with background thread
  - Migrate `extract_archive()` logic from ArchiveOperations to `perform_extract_operation()` with background thread
  - Migrate `_get_archive_handler()` helper method from ArchiveOperations
  - Set daemon=True for all background threads
  - Add cancellation support by checking `operation_cancelled` flag
  - Add logger initialization: `self.logger = getLogger("ArchiveExec")`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 2.1 Write property test for background thread execution
  - **Property 3: Background Thread Execution**
  - **Validates: Requirements 2.2, 3.1**

- [ ]* 2.2 Write property test for daemon thread usage
  - **Property 7: Daemon Thread Usage**
  - **Validates: Requirements 3.5**

- [ ]* 2.3 Write property test for thread cleanup
  - **Property 6: Thread Cleanup**
  - **Validates: Requirements 3.4**

- [x] 3. Implement progress tracking in executor
  - Add `_count_files_recursively()` method to count total files for progress tracking
  - Integrate with ProgressManager for file-by-file progress updates during creation
  - Integrate with ProgressManager for file-by-file progress updates during extraction
  - Add `_progress_callback()` method to trigger UI refresh
  - Track error count separately from success count
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 3.1 Write property test for progress updates during creation
  - **Property 8: Progress Updates for Creation**
  - **Validates: Requirements 4.2**

- [ ]* 3.2 Write property test for progress updates during extraction
  - **Property 9: Progress Updates for Extraction**
  - **Validates: Requirements 4.3**

- [ ]* 3.3 Write property test for error count tracking
  - **Property 10: Error Count Tracking**
  - **Validates: Requirements 4.5, 7.2**

- [x] 4. Implement cancellation support
  - Add cancellation check in executor's main loop (check `operation_cancelled` flag)
  - Handle ESC key in task to set cancellation flag
  - Clean up partial work on cancellation
  - Transition task to IDLE state on cancellation
  - Invoke completion callback even when cancelled
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - **Status: COMPLETED** ✅

- [ ]* 4.1 Write property test for cancellation support
  - **Property 4: Cancellation Support**
  - **Validates: Requirements 2.4, 5.2, 5.4, 5.5**

- [ ]* 4.2 Write property test for callback on cancellation
  - **Property 20: Callback on Cancellation**
  - **Validates: Requirements 10.5**

- [-] 5. Create ArchiveOperationUI for user interactions
  - Create `src/tfm_archive_operation_ui.py` with ArchiveOperationUI class
  - Implement `show_confirmation_dialog()` for archive creation/extraction confirmation
  - Implement `show_conflict_dialog()` for conflict resolution (Overwrite/Skip options)
  - Support Shift modifier key for batch conflict resolution (apply to all)
  - Format dialog messages with operation details
  - Add logger initialization: `self.logger = getLogger("ArchiveUI")`
  - _Requirements: 6.1, 6.2, 6.5, 13.5, 13.7, 13.8, 13.9_

- [ ]* 5.1 Write property test for configuration-based confirmation
  - **Property 11: Configuration-Based Confirmation**
  - **Validates: Requirements 6.5**

- [x] 6. Implement conflict detection
  - Add `_check_conflicts()` method to executor
  - Detect archive file exists for creation operations
  - Detect file overwrites for extraction operations
  - Create ConflictInfo dataclass with conflict_type, path, size, is_directory
  - Transition to CHECKING_CONFLICTS state before execution
  - Transition to RESOLVING_CONFLICT if conflicts found, or EXECUTING if no conflicts
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.10_

- [ ]* 6.1 Write property test for creation conflict detection
  - **Property 27: Creation Conflict Detection**
  - **Validates: Requirements 13.1, 13.3**

- [ ]* 6.2 Write property test for extraction conflict detection
  - **Property 28: Extraction Conflict Detection**
  - **Validates: Requirements 13.2, 13.3**

- [ ]* 6.3 Write property test for no conflicts fast path
  - **Property 32: No Conflicts Fast Path**
  - **Validates: Requirements 13.10**

- [x] 7. Implement conflict resolution
  - Handle "Overwrite" choice in task: set overwrite flag and proceed to EXECUTING
  - Handle "Skip" choice in task: mark files to skip and proceed to EXECUTING
  - Handle Shift modifier: apply choice to all remaining conflicts (overwrite_all/skip_all)
  - Handle ESC key: cancel operation and return to IDLE
  - Update executor to respect overwrite_all and skip_all flags
  - _Requirements: 13.7, 13.8, 13.9_

- [ ]* 7.1 Write property test for overwrite conflict resolution
  - **Property 29: Overwrite Conflict Resolution**
  - **Validates: Requirements 13.7**

- [ ]* 7.2 Write property test for skip conflict resolution
  - **Property 30: Skip Conflict Resolution**
  - **Validates: Requirements 13.8**

- [ ]* 7.3 Write property test for batch conflict resolution
  - **Property 31: Batch Conflict Resolution**
  - **Validates: Requirements 13.9**

- [x] 8. Implement error handling
  - Add try-except blocks for PermissionError, OSError, ArchiveError in executor
  - Log errors with contextual information (operation type, file name, error message)
  - Increment error count for each error
  - Continue processing remaining files after errors
  - Handle disk space exhaustion by stopping operation
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 8.1 Write property test for error logging
  - **Property 12: Error Logging**
  - **Validates: Requirements 7.1**

- [ ]* 8.2 Write property test for continue after errors
  - **Property 13: Continue After Errors**
  - **Validates: Requirements 7.3**

- [ ]* 8.3 Write property test for exception handling
  - **Property 14: Exception Handling**
  - **Validates: Requirements 7.5**

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement completion callbacks
  - Add completion_callback parameter to executor methods
  - Invoke callback with (success_count, error_count) when operation completes
  - Suppress default summary logging when callback provided
  - Invoke callback on background thread
  - Ensure callback invoked even on cancellation
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 10.1 Write property test for completion callback invocation
  - **Property 17: Completion Callback Invocation**
  - **Validates: Requirements 10.2**

- [ ]* 10.2 Write property test for callback suppresses logging
  - **Property 18: Callback Suppresses Logging**
  - **Validates: Requirements 10.3**

- [ ]* 10.3 Write property test for callback thread context
  - **Property 19: Callback Thread Context**
  - **Validates: Requirements 10.4**

- [x] 11. Implement file manager integration
  - Call file_manager.refresh() after successful archive creation
  - Call file_manager.refresh() after successful archive extraction
  - Call file_manager.mark_dirty() to trigger UI redraw
  - Clear operation_in_progress flag on completion
  - Transition from EXECUTING to COMPLETED to IDLE
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  - **Status: COMPLETED** ✅

- [ ]* 11.1 Write property test for file list refresh after creation
  - **Property 21: File List Refresh After Creation**
  - **Validates: Requirements 11.1**

- [ ]* 11.2 Write property test for file list refresh after extraction
  - **Property 22: File List Refresh After Extraction**
  - **Validates: Requirements 11.2**

- [ ]* 11.3 Write property test for UI dirty flag
  - **Property 23: UI Dirty Flag**
  - **Validates: Requirements 11.3**

- [ ]* 11.4 Write property test for operation flag cleanup
  - **Property 24: Operation Flag Cleanup**
  - **Validates: Requirements 11.4**

- [ ]* 11.5 Write property test for completion state transition
  - **Property 25: Completion State Transition**
  - **Validates: Requirements 11.5**

- [x] 12. Modify ArchiveOperations for backward compatibility
  - Add `use_task` parameter to `create_archive()` method (default True)
  - Add `use_task` parameter to `extract_archive()` method (default True)
  - Delegate to ArchiveOperationTask when use_task=True
  - Keep legacy synchronous code path when use_task=False
  - Maintain boolean return values for backward compatibility
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 12.1 Write property test for backward compatibility
  - **Property 26: Backward Compatibility**
  - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5**

- [x] 13. Implement cross-storage support
  - Ensure executor handles local file paths
  - Ensure executor handles S3 paths
  - Ensure executor handles mixed storage schemes (local to S3, S3 to local)
  - Test archive creation with cross-storage sources
  - Test archive extraction to cross-storage destinations
  - _Requirements: 2.5, 9.1, 9.2, 9.4_
  - **Status: COMPLETED** ✅

- [ ]* 13.1 Write property test for cross-storage operations
  - **Property 5: Cross-Storage Operations**
  - **Validates: Requirements 2.5, 9.4**

- [x] 14. Implement archive format support
  - Support tar format in executor
  - Support tar.gz format in executor
  - Support tar.bz2 format in executor
  - Support tar.xz format in executor
  - Support zip format in executor
  - _Requirements: 9.3_
  - **Status: COMPLETED** ✅

- [ ]* 14.1 Write property test for archive format support
  - **Property 15: Archive Format Support**
  - **Validates: Requirements 9.3**

- [x] 15. Implement cache invalidation
  - Call cache_manager.invalidate() for affected paths after successful creation
  - Call cache_manager.invalidate() for affected paths after successful extraction
  - Invalidate both source and destination paths
  - _Requirements: 9.5_
  - **Status: COMPLETED** ✅

- [ ]* 15.1 Write property test for cache invalidation
  - **Property 16: Cache Invalidation**
  - **Validates: Requirements 9.5**

- [x] 16. Wire components together in FileManager
  - Create ArchiveOperationTask instance in FileManager
  - Create ArchiveOperationExecutor instance in FileManager
  - Create ArchiveOperationUI instance in FileManager
  - Update archive creation key binding to use task
  - Update archive extraction key binding to use task
  - Pass file_manager, ui, and executor to task constructor
  - _Requirements: 1.1, 2.1, 6.1_
  - **Status: COMPLETED** ✅

- [ ]* 16.1 Write integration test for archive creation workflow
  - Test complete workflow: confirmation → conflict detection → execution → completion
  - _Requirements: 1.1, 1.2, 1.3, 6.1, 6.2, 6.3, 6.4, 13.1, 13.3_

- [ ]* 16.2 Write integration test for archive extraction workflow
  - Test complete workflow: confirmation → conflict detection → execution → completion
  - _Requirements: 1.1, 1.2, 1.3, 6.1, 6.2, 6.3, 6.4, 13.2, 13.3_

- [x] 17. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Migration follows the same patterns as FileOperationTask, FileOperationExecutor, and FileOperationUI
- Core archive logic is migrated from ArchiveOperations to ArchiveOperationExecutor
- ArchiveOperations becomes a thin wrapper for backward compatibility
