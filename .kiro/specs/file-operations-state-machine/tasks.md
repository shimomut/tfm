# Implementation Plan: File Operations State Machine

## Overview

This implementation plan outlines the tasks for creating a task-based framework for complex UI × threading workflows in TFM. The framework introduces an abstract BaseTask class and a concrete FileOperationTask implementation to replace the current callback-based file operations system. The migration will be incremental, starting with the task framework, then the file operation task, followed by integration with copy, move, and delete operations, and finally cleaning up the old implementation.

## Tasks

- [ ] 1. Create BaseTask abstract class
  - Create `src/tfm_base_task.py` module
  - Define BaseTask abstract class with abstract methods
  - Implement start(), cancel(), is_active(), get_state() as abstract methods
  - Implement on_state_enter() and on_state_exit() as hooks
  - Add comprehensive docstrings
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 15.1, 15.3_

- [ ]* 1.1 Write unit tests for BaseTask interface
  - Test that BaseTask cannot be instantiated directly
  - Test that subclasses must implement abstract methods
  - Test hook methods can be overridden
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Add task management to FileManager
  - [ ] 2.1 Add current_task attribute to FileManager.__init__()
    - Initialize as None
    - Add type hint: Optional[BaseTask]
    - _Requirements: 2.1_

  - [ ] 2.2 Implement start_task() method
    - Check if task is already active
    - Raise RuntimeError if task already active
    - Store task reference
    - Call task.start()
    - _Requirements: 2.2, 2.3_

  - [ ] 2.3 Implement cancel_current_task() method
    - Check if task exists and is active
    - Call task.cancel()
    - _Requirements: 2.4_

  - [ ] 2.4 Implement _clear_task() method
    - Clear current_task reference
    - Called by tasks when they complete
    - _Requirements: 2.5_

  - [ ]* 2.5 Write unit tests for task management
    - Test start_task with no active task
    - Test start_task with active task (should raise RuntimeError)
    - Test cancel_current_task
    - Test _clear_task
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 2.6 Write property test for single active task
    - **Property 2: Single Active Task**
    - **Validates: Requirements 2.3**

  - [ ]* 2.7 Write property test for task start exclusivity
    - **Property 13: Task Start Exclusivity**
    - **Validates: Requirements 2.3**

- [ ] 3. Create FileOperationTask infrastructure
  - Create `src/tfm_file_operation_task.py` module
  - Define State enum with all required states
  - Define OperationContext dataclass
  - Implement FileOperationTask class skeleton inheriting from BaseTask
  - Implement abstract methods: start(), cancel(), is_active(), get_state()
  - _Requirements: 3.1, 3.2, 3.3, 11.1, 15.1, 15.3_

- [ ]* 3.1 Write unit tests for FileOperationTask initialization
  - Test task starts in IDLE state
  - Test context is None initially
  - Test is_active() returns False initially
  - _Requirements: 3.1, 3.2_

- [ ]* 3.2 Write property test for task lifecycle validity
  - **Property 1: Task Lifecycle Validity**
  - **Validates: Requirements 1.6, 3.6**

- [ ] 4. Implement state transition logic
- [ ] 4. Implement state transition logic
  - [ ] 4.1 Implement start_operation() method
    - Validate operation type
    - Create operation context
    - Transition to CONFIRMING state
    - Trigger confirmation dialog
    - _Requirements: 3.3, 4.1, 11.1_

  - [ ]* 4.2 Write property test for state transitions
    - **Property 4: State Transition Validity**
    - **Validates: Requirements 3.6**

  - [ ] 4.3 Implement on_confirmed() callback
    - Handle confirmation acceptance
    - Handle confirmation cancellation
    - Transition to CHECKING_CONFLICTS or IDLE
    - _Requirements: 4.3, 4.4, 3.3_

  - [ ]* 4.4 Write unit tests for confirmation flow
    - Test confirmation with single file
    - Test confirmation with multiple files
    - Test confirmation cancellation
    - _Requirements: 4.1, 4.3, 4.4_

- [ ] 5. Implement conflict detection
  - [ ] 5.1 Implement _check_conflicts() method
    - Detect file conflicts for copy operations
    - Detect file conflicts for move operations
    - Store conflicts in context
    - Transition to RESOLVING_CONFLICT or EXECUTING
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 5.2 Write unit tests for conflict detection
    - Test detection with no conflicts
    - Test detection with single conflict
    - Test detection with multiple conflicts
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 5.3 Write property test for conflict completeness
    - **Property 6: Conflict Resolution Completeness**
    - **Validates: Requirements 6.6**

- [ ] 6. Implement conflict resolution
  - [ ] 6.1 Implement _resolve_next_conflict() method
    - Show conflict dialog for current conflict
    - Handle apply-to-all options
    - Process all conflicts sequentially
    - _Requirements: 6.1, 6.5, 6.6_

  - [ ] 6.2 Implement on_conflict_resolved() callback
    - Handle overwrite choice
    - Handle skip choice
    - Handle rename choice
    - Handle apply-to-all flag
    - Update results and options
    - _Requirements: 6.2, 6.3, 6.4, 6.5_

  - [ ]* 6.3 Write unit tests for conflict resolution
    - Test overwrite choice
    - Test skip choice
    - Test rename choice
    - Test apply-to-all for each choice
    - _Requirements: 6.2, 6.3, 6.4, 6.5_

  - [ ]* 6.4 Write property test for apply-to-all consistency
    - **Property 7: Apply-to-All Consistency**
    - **Validates: Requirements 6.5**

- [ ] 7. Implement rename handling
  - [ ] 7.1 Implement _show_rename_dialog() method
    - Display QuickEditBar with current filename
    - Set up callbacks for confirmation and cancellation
    - _Requirements: 7.1_

  - [ ] 7.2 Implement on_renamed() callback
    - Validate new name is not empty
    - Check if new name conflicts
    - Handle secondary conflict
    - Update results with renamed file
    - _Requirements: 7.2, 7.3, 7.4_

  - [ ] 7.3 Implement on_rename_cancelled() callback
    - Transition to IDLE state
    - Log cancellation
    - _Requirements: 7.5_

  - [ ]* 7.4 Write unit tests for rename handling
    - Test valid rename
    - Test empty rename rejection
    - Test rename with new conflict
    - Test rename cancellation
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 7.5 Write property test for rename uniqueness
    - **Property 8: Rename Uniqueness**
    - **Validates: Requirements 7.3**

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement operation execution
  - [ ] 9.1 Implement _execute_operation() method
    - Prepare file list for execution
    - Combine non-conflicting files with resolved conflicts
    - Delegate to operation-specific execution methods
    - _Requirements: 8.2, 8.3_

  - [ ] 9.2 Implement _execute_copy() method
    - Create background worker thread
    - Set operation_in_progress flag
    - Start progress tracking
    - Call existing perform_copy_operation with pre-resolved files
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ] 9.3 Implement _execute_move() method
    - Create background worker thread
    - Set operation_in_progress flag
    - Start progress tracking
    - Call existing perform_move_operation with pre-resolved files
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ] 9.4 Implement _execute_delete() method
    - Create background worker thread
    - Set operation_in_progress flag
    - Start progress tracking
    - Call existing perform_delete_operation
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 9.5 Write unit tests for execution
    - Test execution with no conflicts
    - Test execution with resolved conflicts
    - Test execution with mixed results
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ]* 9.6 Write property test for error isolation
    - **Property 11: Error Isolation**
    - **Validates: Requirements 12.2**

- [ ] 10. Implement completion handling
  - [ ] 10.1 Implement _complete_operation() method
    - Build summary message
    - Log summary with counts
    - Transition to IDLE state
    - Clear operation context
    - Call file_manager._clear_task()
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.5, 2.5_

  - [ ]* 10.2 Write unit tests for completion
    - Test completion with all success
    - Test completion with mixed results
    - Test completion with cancellation
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 10.3 Write property test for context cleanup
    - **Property 5: Context Cleanup**
    - **Validates: Requirements 11.5**

  - [ ]* 10.4 Write property test for task cleanup
    - **Property 3: Task Cleanup**
    - **Validates: Requirements 2.5, 11.5**

- [ ] 11. Implement helper methods
  - [ ] 11.1 Implement _build_confirmation_message() method
    - Build message for single file operations
    - Build message for multiple file operations
    - Handle copy, move, and delete operations
    - _Requirements: 4.5_

  - [ ] 11.2 Implement _validate_operation() method
    - Check storage capabilities
    - Validate source and destination paths
    - Return validation result
    - _Requirements: 14.1_

  - [ ]* 11.3 Write unit tests for helper methods
    - Test confirmation message building
    - Test operation validation
    - _Requirements: 4.5, 14.1_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Integrate FileOperationTask with FileOperationsUI for copy operations
  - [ ] 13.1 Refactor copy_selected_files() to use FileOperationTask
    - Get files to copy
    - Validate operation capabilities
    - Create FileOperationTask instance
    - Call task.start_operation('copy', files, destination)
    - Call file_manager.start_task(task)
    - Remove old callback-based code
    - _Requirements: 16.2_

  - [ ] 13.2 Remove old copy conflict resolution methods
    - Remove _handle_copy_rename_batch()
    - Remove _process_next_copy_conflict()
    - Remove _handle_copy_rename()
    - Remove _on_copy_rename_confirm()
    - Remove _on_copy_rename_cancel()
    - _Requirements: 16.5_

  - [ ]* 13.3 Write integration tests for copy operations
    - Test complete copy flow with no conflicts
    - Test complete copy flow with conflicts
    - Test copy with rename
    - Test copy with skip
    - Test copy with overwrite
    - Test copy cancellation
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [ ] 14. Integrate FileOperationTask with FileOperationsUI for move operations
  - [ ] 14.1 Refactor move_selected_files() to use FileOperationTask
    - Get files to move
    - Validate operation capabilities
    - Check for cross-storage moves
    - Create FileOperationTask instance
    - Call task.start_operation('move', files, destination)
    - Call file_manager.start_task(task)
    - Remove old callback-based code
    - _Requirements: 16.3_

  - [ ] 14.2 Remove old move conflict resolution methods
    - Remove _handle_move_rename_batch()
    - Remove _process_next_move_conflict()
    - Remove _handle_move_rename()
    - Remove _on_move_rename_confirm()
    - Remove _on_move_rename_cancel()
    - _Requirements: 16.5_

  - [ ]* 14.3 Write integration tests for move operations
    - Test complete move flow with no conflicts
    - Test complete move flow with conflicts
    - Test move with rename
    - Test move with skip
    - Test move with overwrite
    - Test move cancellation
    - Test cross-storage move
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [ ] 15. Integrate FileOperationTask with FileOperationsUI for delete operations
  - [ ] 15.1 Refactor delete_selected_files() to use FileOperationTask
    - Get files to delete
    - Validate operation capabilities
    - Create FileOperationTask instance
    - Call task.start_operation('delete', files)
    - Call file_manager.start_task(task)
    - Remove old callback-based code
    - _Requirements: 16.4_

  - [ ]* 15.2 Write integration tests for delete operations
    - Test complete delete flow
    - Test delete with confirmation
    - Test delete without confirmation
    - Test delete cancellation
    - _Requirements: 14.1, 14.3, 14.4_

- [ ] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Clean up and finalize
  - [ ] 17.1 Remove temporary context objects from FileManager
    - Remove _copy_rename_batch_context
    - Remove _copy_rename_context
    - Remove _move_rename_batch_context
    - Remove _move_rename_context
    - _Requirements: 11.2_

  - [ ] 17.2 Update FileOperationsUI documentation
    - Document task usage
    - Update method docstrings
    - Add architecture notes
    - _Requirements: 15.4_

  - [ ] 17.3 Add developer documentation
    - Create doc/dev/TASK_FRAMEWORK_IMPLEMENTATION.md
    - Document BaseTask design
    - Document FileOperationTask design
    - Document migration process
    - Include state diagram
    - Include class hierarchy diagram
    - Document future task queue support
    - _Requirements: 15.5_

  - [ ]* 17.4 Write property test for operation atomicity
    - **Property 10: Operation Atomicity**
    - **Validates: Requirements 11.1**

  - [ ]* 17.5 Write property test for thread safety
    - **Property 9: Thread Safety**
    - **Validates: Requirements 13.1**

  - [ ]* 17.6 Write property test for cancellation responsiveness
    - **Property 12: Cancellation Responsiveness**
    - **Validates: Requirements 8.5**

- [ ] 18. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end functionality
- Migration is incremental: copy → move → delete → cleanup
