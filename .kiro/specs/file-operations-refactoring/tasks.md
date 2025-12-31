# Implementation Plan: File Operations Architecture Refactoring

## Overview

This implementation plan outlines the tasks for refactoring the file operations architecture to fix naming confusion and boundary violations. The refactoring will be done in 7 incremental phases, with testing after each phase to ensure correctness.

## Tasks

- [x] 1. Phase 1: Create FileOperationsExecutor class
  - [x] 1.1 Create new file src/tfm_file_operations_executor.py
    - Create module with proper imports
    - Add module docstring
    - _Requirements: 2.1_

  - [x] 1.2 Create FileOperationsExecutor class skeleton
    - Define class with __init__ method
    - Accept file_manager parameter
    - Initialize progress_manager, cache_manager, logger
    - _Requirements: 2.1, 2.6_

  - [x] 1.3 Move perform_copy_operation() from FileOperationsUI
    - Copy method to FileOperationsExecutor
    - Update references to use self.file_manager
    - Keep original in FileOperationsUI temporarily
    - _Requirements: 2.2, 2.7_

  - [x] 1.4 Move perform_move_operation() from FileOperationsUI
    - Copy method to FileOperationsExecutor
    - Update references to use self.file_manager
    - Keep original in FileOperationsUI temporarily
    - _Requirements: 2.3, 2.7_

  - [x] 1.5 Move perform_delete_operation() from FileOperationsUI
    - Copy method to FileOperationsExecutor
    - Update references to use self.file_manager
    - Keep original in FileOperationsUI temporarily
    - _Requirements: 2.4, 2.7_

  - [x] 1.6 Move helper methods to FileOperationsExecutor
    - Move _count_files_recursively()
    - Move _progress_callback()
    - Move _animation_refresh_loop()
    - Move _copy_file_with_progress()
    - Move _copy_directory_with_progress()
    - Move _copy_directory_cross_storage_with_progress()
    - Move _move_directory_with_progress()
    - Move _delete_directory_with_progress()
    - Move _perform_single_copy()
    - Move _perform_single_move()
    - _Requirements: 2.5, 2.6_

  - [x] 1.7 Test FileOperationsExecutor independently
    - Create test file for executor
    - Test copy operation
    - Test move operation
    - Test delete operation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 9.3_

- [x] 2. Checkpoint: Verify Phase 1
  - Ensure executor tests pass
  - Ensure existing tests still pass
  - Verify no regressions

- [x] 3. Phase 2: Extract UI methods from FileOperationTask
  - [x] 3.1 Add show_confirmation_dialog() to FileOperationsUI
    - Create method with proper signature
    - Build confirmation message
    - Call file_manager.show_confirmation()
    - _Requirements: 4.1, 4.4_

  - [x] 3.2 Add show_conflict_dialog() to FileOperationsUI
    - Create method with proper signature
    - Build conflict message
    - Call file_manager.show_dialog()
    - _Requirements: 4.2, 4.4_

  - [x] 3.3 Add show_rename_dialog() to FileOperationsUI
    - Create method with proper signature
    - Set up QuickEditBar
    - Handle callbacks
    - Call file_manager.mark_dirty()
    - _Requirements: 4.3, 4.5_

  - [x] 3.4 Update FileOperationTask constructor
    - Add ui parameter
    - Store ui reference
    - Update docstring
    - _Requirements: 6.1, 6.3_

  - [x] 3.5 Replace show_confirmation() calls in task
    - Replace file_manager.show_confirmation() with ui.show_confirmation_dialog()
    - Update all call sites
    - _Requirements: 3.1, 3.2, 6.3_

  - [x] 3.6 Replace show_dialog() calls in task
    - Replace file_manager.show_dialog() with ui.show_conflict_dialog()
    - Update all call sites
    - _Requirements: 3.1, 3.3, 6.3_

  - [x] 3.7 Replace QuickEditBar calls in task
    - Replace file_manager.quick_edit_bar calls with ui.show_rename_dialog()
    - Update all call sites
    - _Requirements: 3.3, 3.4, 6.3_

  - [x] 3.8 Remove mark_dirty() calls from task
    - Remove direct file_manager.mark_dirty() calls
    - UI methods handle mark_dirty() internally
    - _Requirements: 3.4, 3.5_

  - [x] 3.9 Test task with new UI interface
    - Update task tests
    - Verify UI methods called correctly
    - Verify state transitions work
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.2_

- [x] 4. Checkpoint: Verify Phase 2
  - Ensure task tests pass
  - Ensure UI integration works
  - Verify no regressions

- [x] 5. Phase 3: Rename FileOperations to FileListManager
  - [x] 5.1 Rename class in tfm_file_operations.py
    - Change class name from FileOperations to FileListManager
    - Update class docstring
    - _Requirements: 1.1, 13.1_

  - [x] 5.2 Update imports in tfm_main.py
    - Change import from FileOperations to FileListManager
    - Update variable name from file_operations to file_list_manager
    - _Requirements: 1.2, 1.3_

  - [x] 5.3 Update all references in FileManager
    - Change self.file_operations to self.file_list_manager
    - Update all method calls
    - _Requirements: 1.3, 7.4_

  - [x] 5.4 Update test imports
    - Update all test files importing FileOperations
    - Change to import FileListManager
    - _Requirements: 1.5, 9.1_

  - [x] 5.5 Update test references
    - Update all test code using FileOperations
    - Change to use FileListManager
    - _Requirements: 1.5, 9.2_

  - [x] 5.6 Run full test suite
    - Verify all tests pass
    - Check for any missed references
    - _Requirements: 1.4, 9.4_

- [x] 6. Checkpoint: Verify Phase 3
  - Ensure all tests pass
  - Verify no references to old name
  - Check imports are correct

- [x] 7. Phase 4: Update FileOperationTask to use executor
  - [x] 7.1 Update FileOperationTask constructor
    - Add executor parameter
    - Store executor reference
    - Update docstring
    - _Requirements: 6.2, 6.4_

  - [x] 7.2 Replace perform_copy_operation() calls
    - Change from file_operations_ui.perform_copy_operation()
    - To executor.perform_copy_operation()
    - _Requirements: 5.1, 5.2, 6.4_

  - [x] 7.3 Replace perform_move_operation() calls
    - Change from file_operations_ui.perform_move_operation()
    - To executor.perform_move_operation()
    - _Requirements: 5.1, 5.3, 6.4_

  - [x] 7.4 Replace perform_delete_operation() calls
    - Change from file_operations_ui.perform_delete_operation()
    - To executor.perform_delete_operation()
    - _Requirements: 5.1, 5.4, 6.4_

  - [x] 7.5 Update task tests
    - Mock executor instead of file_operations_ui
    - Verify executor methods called
    - _Requirements: 6.4, 9.2_

  - [x] 7.6 Test task with executor
    - Run task tests
    - Verify I/O operations work
    - _Requirements: 6.4, 6.5_

- [x] 8. Checkpoint: Verify Phase 4
  - Ensure task uses executor
  - Verify no circular dependencies
  - Check tests pass

- [x] 9. Phase 5: Update FileManager integration
  - [x] 9.1 Create FileOperationsExecutor instance in FileManager
    - Add self.file_operations_executor = FileOperationsExecutor(self)
    - Place after progress_manager initialization
    - _Requirements: 7.2_

  - [x] 9.2 Update FileOperationsUI initialization
    - Change from FileOperationsUI(self, self.file_operations)
    - To FileOperationsUI(self, self.file_list_manager)
    - _Requirements: 7.3_

  - [x] 9.3 Update task creation in FileOperationsUI
    - Pass ui=self to task constructor
    - Pass executor=self.file_manager.file_operations_executor
    - Update all three operations (copy, move, delete)
    - _Requirements: 6.1, 6.2, 7.3_

  - [x] 9.4 Remove old perform_*_operation() methods from FileOperationsUI
    - Remove perform_copy_operation()
    - Remove perform_move_operation()
    - Remove perform_delete_operation()
    - Remove all helper methods moved to executor
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 9.5 Test FileManager integration
    - Test copy operation end-to-end
    - Test move operation end-to-end
    - Test delete operation end-to-end
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 10. Checkpoint: Verify Phase 5
  - Ensure all operations work
  - Verify architecture is clean
  - Check no old code remains

- [x] 11. Phase 6: Update tests
  - [x] 11.1 Update test imports for renamed classes
    - Update all FileOperations imports to FileListManager
    - Verify no old imports remain
    - _Requirements: 9.1_

  - [x] 11.2 Update test mocks for new structure
    - Mock FileOperationsExecutor where needed
    - Update FileOperationsUI mocks
    - Update FileOperationTask mocks
    - _Requirements: 9.2_

  - [x] 11.3 Add tests for FileOperationsExecutor
    - Test copy operation
    - Test move operation
    - Test delete operation
    - Test progress tracking
    - Test error handling
    - _Requirements: 9.3_

  - [x] 11.4 Update integration tests
    - Test complete copy flow
    - Test complete move flow
    - Test complete delete flow
    - Test conflict resolution
    - _Requirements: 9.4_

  - [x] 11.5 Run full test suite
    - Run all tests
    - Verify 100% pass rate
    - Check coverage maintained
    - _Requirements: 9.4_

- [x] 12. Checkpoint: Verify Phase 6
  - Ensure all tests pass
  - Verify test coverage maintained
  - Check no test failures

- [x] 13. Phase 7: Update documentation
  - [x] 13.1 Update TASK_FRAMEWORK_IMPLEMENTATION.md
    - Update architecture diagrams
    - Document new class structure
    - Update dependency flow
    - Add refactoring notes
    - _Requirements: 10.1_

  - [x] 13.2 Update class docstrings
    - Update FileListManager docstring
    - Update FileOperationsUI docstring
    - Update FileOperationTask docstring
    - Update FileOperationsExecutor docstring
    - _Requirements: 10.2_

  - [x] 13.3 Create architecture diagrams
    - Create class diagram
    - Create dependency diagram
    - Create sequence diagram for operations
    - _Requirements: 10.3_

  - [x] 13.4 Add migration notes
    - Document what changed
    - Document why it changed
    - Document how to adapt code
    - _Requirements: 10.4_

  - [x] 13.5 Update method docstrings
    - Update all public method docstrings
    - Document parameters clearly
    - Document return values
    - _Requirements: 10.5_

- [x] 14. Final checkpoint: Verify complete refactoring
  - Ensure all tests pass
  - Verify architecture is clean
  - Check documentation is complete
  - Verify no regressions
  - Confirm backward compatibility

## Notes

- Each phase should be completed and tested before moving to the next
- Commit code after each successful phase
- Keep old code temporarily during migration for safety
- Remove old code only after new code is verified
- Run full test suite after each phase
- Update documentation as you go
- Focus on one phase at a time

## Success Criteria

- [ ] All tests pass
- [ ] No circular dependencies
- [ ] FileOperationTask has no UI code
- [ ] FileOperationsUI has no I/O code
- [ ] FileListManager clearly named
- [ ] FileOperationsExecutor handles all I/O
- [ ] Documentation complete and accurate
- [ ] No performance degradation
- [ ] Backward compatibility maintained
