# File Operations Architecture

## Overview

This document provides detailed architecture diagrams for the file operations system in TFM. The architecture has been refactored to achieve clean separation of concerns with four distinct layers.

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FileManager                              │
│                                                                  │
│  Responsibilities:                                               │
│  - Task management (current_task, start_task, cancel_task)      │
│  - Component initialization and wiring                           │
│  - UI coordination                                               │
│                                                                  │
│  Components:                                                     │
│  - file_list_manager: FileListManager                            │
│  - file_operations_executor: FileOperationsExecutor              │
│  - file_operations_ui: FileOperationsUI                          │
│  - current_task: Optional[BaseTask]                              │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │ creates and manages
                           ↓
        ┌──────────────────────────────────────────┐
        │                                          │
        ↓                                          ↓
┌────────────────────┐                  ┌──────────────────────┐
│ FileListManager    │                  │ FileOperationsExecutor│
│                    │                  │                       │
│ Layer 1:           │                  │ Layer 4:              │
│ File List Mgmt     │                  │ I/O Operations        │
│                    │                  │                       │
│ - refresh_files()  │                  │ - perform_copy()      │
│ - sort_entries()   │                  │ - perform_move()      │
│ - toggle_selection()│                 │ - perform_delete()    │
│ - apply_filter()   │                  │ - progress tracking   │
│ - get_file_info()  │                  │ - error handling      │
└────────────────────┘                  └──────────────────────┘
        ↑                                          ↑
        │                                          │
        │ uses                                     │ uses
        │                                          │
┌────────────────────────────────────────────────────────────────┐
│                    FileOperationsUI                             │
│                                                                 │
│ Layer 2: UI Interactions                                        │
│                                                                 │
│ Entry Points:                    UI Methods:                   │
│ - copy_selected_files()          - show_confirmation_dialog()  │
│ - move_selected_files()          - show_conflict_dialog()      │
│ - delete_selected_files()        - show_rename_dialog()        │
│                                                                 │
│ Creates:                                                        │
│ - FileOperationTask(ui=self, executor=executor)                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ creates
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FileOperationTask                             │
│                                                                  │
│ Layer 3: Orchestration (State Machine)                          │
│                                                                  │
│ Dependencies:                                                    │
│ - ui: FileOperationsUI (for UI interactions)                    │
│ - executor: FileOperationsExecutor (for I/O operations)         │
│                                                                  │
│ States:                                                          │
│ IDLE → CONFIRMING → CHECKING_CONFLICTS → RESOLVING_CONFLICT    │
│      → EXECUTING → COMPLETED → IDLE                             │
│                                                                  │
│ Methods:                                                         │
│ - start_operation()                                              │
│ - on_confirmed()                                                 │
│ - on_conflict_resolved()                                         │
│ - on_renamed()                                                   │
│ - _check_conflicts()                                             │
│ - _execute_operation()                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Dependency Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FileManager                              │
│                                                                  │
│  Creates and owns all components                                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ↓                  ↓                  ↓
┌────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│FileListManager │  │FileOperationsUI  │  │FileOperationsExecutor│
│                │  │                  │  │                      │
│ No dependencies│  │ Depends on:      │  │ Depends on:          │
│                │  │ - FileManager    │  │ - FileManager        │
│                │  │ - FileListMgr    │  │   (for progress,     │
│                │  │                  │  │    cache)            │
└────────────────┘  └────────┬─────────┘  └──────────────────────┘
                             │                       ↑
                             │ creates               │
                             ↓                       │
                    ┌──────────────────┐            │
                    │FileOperationTask │            │
                    │                  │            │
                    │ Depends on:      │            │
                    │ - FileManager    │            │
                    │ - ui (UI layer)  │────────────┘
                    │ - executor (I/O) │────────────┐
                    └──────────────────┘            │
                                                    │
                                                    ↓
                                          (delegates I/O)

Dependency Flow: One-way, no circular dependencies
FileManager → Components → Task → UI/Executor
```

## Sequence Diagram: Copy Operation

```
User          FileOperationsUI    FileOperationTask    FileOperationsExecutor
 │                   │                    │                      │
 │ Press F5 (copy)   │                    │                      │
 ├──────────────────>│                    │                      │
 │                   │                    │                      │
 │                   │ create task        │                      │
 │                   ├───────────────────>│                      │
 │                   │                    │                      │
 │                   │ start_operation()  │                      │
 │                   ├───────────────────>│                      │
 │                   │                    │                      │
 │                   │                    │ State: CONFIRMING    │
 │                   │                    │                      │
 │                   │<───────────────────┤                      │
 │                   │ show_confirmation_ │                      │
 │                   │ dialog()           │                      │
 │                   │                    │                      │
 │<──────────────────┤                    │                      │
 │ Show dialog       │                    │                      │
 │                   │                    │                      │
 │ Press Y (confirm) │                    │                      │
 ├──────────────────>│                    │                      │
 │                   │                    │                      │
 │                   │ on_confirmed(True) │                      │
 │                   ├───────────────────>│                      │
 │                   │                    │                      │
 │                   │                    │ State: CHECKING_     │
 │                   │                    │ CONFLICTS            │
 │                   │                    │                      │
 │                   │                    │ _check_conflicts()   │
 │                   │                    │                      │
 │                   │                    │ (if conflicts found) │
 │                   │                    │ State: RESOLVING_    │
 │                   │                    │ CONFLICT             │
 │                   │                    │                      │
 │                   │<───────────────────┤                      │
 │                   │ show_conflict_     │                      │
 │                   │ dialog()           │                      │
 │                   │                    │                      │
 │<──────────────────┤                    │                      │
 │ Show dialog       │                    │                      │
 │                   │                    │                      │
 │ Choose action     │                    │                      │
 ├──────────────────>│                    │                      │
 │                   │                    │                      │
 │                   │ on_conflict_       │                      │
 │                   │ resolved()         │                      │
 │                   ├───────────────────>│                      │
 │                   │                    │                      │
 │                   │                    │ (all resolved)       │
 │                   │                    │ State: EXECUTING     │
 │                   │                    │                      │
 │                   │                    │ perform_copy_        │
 │                   │                    │ operation()          │
 │                   │                    ├─────────────────────>│
 │                   │                    │                      │
 │                   │                    │                      │ Background
 │                   │                    │                      │ thread
 │                   │                    │                      │ copies files
 │                   │                    │                      │
 │                   │                    │<─────────────────────┤
 │                   │                    │ completion_callback()│
 │                   │                    │                      │
 │                   │                    │ State: COMPLETED     │
 │                   │                    │                      │
 │                   │                    │ State: IDLE          │
 │                   │                    │                      │
 │<──────────────────┴────────────────────┴──────────────────────┘
 │ UI refreshed                                                   │
 │                                                                │
```

## State Machine Diagram

```
                    ┌──────┐
                    │ IDLE │◄─────────────────────────┐
                    └──┬───┘                          │
                       │                              │
                       │ start_operation()            │
                       │                              │
                       ↓                              │
                 ┌────────────┐                       │
                 │ CONFIRMING │                       │
                 └──┬─────┬───┘                       │
          confirmed│     │cancelled                   │
                   │     │                            │
                   │     └────────────────────────────┘
                   ↓
         ┌──────────────────┐
         │CHECKING_CONFLICTS│
         └──┬───────────┬───┘
    conflicts│         │no conflicts
             │         │
             ↓         │
    ┌─────────────────┐│
    │RESOLVING_CONFLICT││
    └──┬──────────────┘│
       │               │
       │ all resolved  │
       │               │
       └───────┬───────┘
               │
               ↓
    ┌──────────────────────┐
    │     EXECUTING        │
    └──────────┬───────────┘
               │
               │ completed
               │
               ↓
         ┌───────────┐
         │ COMPLETED │
         └─────┬─────┘
               │
               │ cleanup
               │
               └──────────────────────────────────────┘

State Descriptions:
- IDLE: No operation in progress, task inactive
- CONFIRMING: Showing confirmation dialog to user
- CHECKING_CONFLICTS: Detecting file conflicts
- RESOLVING_CONFLICT: User resolving conflicts one by one
- EXECUTING: Background thread performing file operations
- COMPLETED: Operation finished, preparing to return to IDLE
```

## Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: File List Management (FileListManager)                 │
│                                                                  │
│ Responsibilities:                                                │
│ - Refresh directory contents                                     │
│ - Sort file entries                                              │
│ - Apply filters                                                  │
│ - Manage selection state                                         │
│ - Get file information                                           │
│                                                                  │
│ Does NOT:                                                        │
│ - Perform file I/O operations                                    │
│ - Show UI dialogs                                                │
│ - Manage operation state                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: UI Interactions (FileOperationsUI)                     │
│                                                                  │
│ Responsibilities:                                                │
│ - Entry points for operations                                    │
│ - Show confirmation dialogs                                      │
│ - Show conflict resolution dialogs                               │
│ - Show rename dialogs                                            │
│ - Create FileOperationTask instances                             │
│                                                                  │
│ Does NOT:                                                        │
│ - Perform file I/O operations                                    │
│ - Manage operation state machine                                 │
│ - Execute background threads                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: Orchestration (FileOperationTask)                      │
│                                                                  │
│ Responsibilities:                                                │
│ - State machine logic                                            │
│ - Conflict detection                                             │
│ - Workflow coordination                                          │
│ - Delegate UI to FileOperationsUI                                │
│ - Delegate I/O to FileOperationsExecutor                         │
│                                                                  │
│ Does NOT:                                                        │
│ - Show UI dialogs directly                                       │
│ - Perform file I/O directly                                      │
│ - Manage file lists                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: I/O Operations (FileOperationsExecutor)                │
│                                                                  │
│ Responsibilities:                                                │
│ - Execute file copy operations                                   │
│ - Execute file move operations                                   │
│ - Execute file delete operations                                 │
│ - Track progress                                                 │
│ - Handle errors                                                  │
│ - Manage background threads                                      │
│                                                                  │
│ Does NOT:                                                        │
│ - Show UI dialogs                                                │
│ - Manage operation state machine                                 │
│ - Manage file lists                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Component Communication

```
┌─────────────────────────────────────────────────────────────────┐
│                    Communication Patterns                        │
└─────────────────────────────────────────────────────────────────┘

FileOperationsUI → FileOperationTask:
  - Creates task with ui=self, executor=executor
  - Calls task.start_operation()
  - Provides callback methods for task to call

FileOperationTask → FileOperationsUI:
  - Calls ui.show_confirmation_dialog()
  - Calls ui.show_conflict_dialog()
  - Calls ui.show_rename_dialog()

FileOperationTask → FileOperationsExecutor:
  - Calls executor.perform_copy_operation()
  - Calls executor.perform_move_operation()
  - Calls executor.perform_delete_operation()

FileOperationsExecutor → FileManager:
  - Uses progress_manager for progress tracking
  - Uses cache_manager for cache invalidation
  - Calls mark_dirty() for UI refresh

FileOperationTask → FileManager:
  - Calls file_manager._clear_task() when complete
  - Uses file_manager.operation_cancelled flag
```

## Benefits of Refactored Architecture

### Before Refactoring

Problems:
- **Naming Confusion**: FileOperations class misnamed (handled file lists, not operations)
- **Mixed Responsibilities**: FileOperationsUI contained both UI and I/O code
- **Boundary Violations**: FileOperationTask contained UI code
- **Circular Dependencies**: Task called back to UI for I/O operations
- **Testing Difficulty**: Mixed responsibilities made unit testing complex

### After Refactoring

Improvements:
- **Clear Naming**: FileListManager accurately reflects responsibilities
- **Single Responsibility**: Each class has one clear purpose
- **No Boundary Violations**: UI, orchestration, and I/O cleanly separated
- **One-Way Dependencies**: Clean dependency flow, no circular dependencies
- **Easy Testing**: Each component can be tested independently
- **Better Maintainability**: Changes localized to appropriate layer

## References

- **Implementation Documentation**: `doc/dev/TASK_FRAMEWORK_IMPLEMENTATION.md`
- **Refactoring Design**: `.kiro/specs/file-operations-refactoring/design.md`
- **Refactoring Requirements**: `.kiro/specs/file-operations-refactoring/requirements.md`
- **Refactoring Tasks**: `.kiro/specs/file-operations-refactoring/tasks.md`
