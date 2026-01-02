# Design Document: Archive Task Migration

## Overview

This design describes the migration of archive creation and extraction operations from synchronous blocking operations to the unified task framework with threading support. The migration follows the established patterns from FileOperationTask, FileOperationExecutor, and FileOperationUI to provide consistent architecture, non-blocking execution, progress tracking, and conflict resolution.

The design introduces three new components:
- **ArchiveOperationTask**: State machine orchestration for archive operations
- **ArchiveOperationExecutor**: Background thread execution of archive I/O operations
- **ArchiveOperationUI**: User interface interactions for confirmations and conflict resolution

These components integrate with the existing ArchiveOperations class, which maintains its public API for backward compatibility while delegating to the new task-based implementation.

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FileManager                              │
│  - Manages active task                                          │
│  - Coordinates UI refresh                                       │
│  - Provides operation_in_progress and operation_cancelled flags │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ manages
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ArchiveOperationTask                          │
│  State Machine: IDLE → CONFIRMING → CHECKING_CONFLICTS →       │
│                 RESOLVING_CONFLICT → EXECUTING → COMPLETED      │
│                                                                  │
│  - Orchestrates operation workflow                              │
│  - Manages operation context                                    │
│  - Coordinates conflict resolution                              │
└────┬──────────────────────────────────────┬─────────────────────┘
     │                                       │
     │ delegates UI                          │ delegates I/O
     ▼                                       ▼
┌──────────────────────┐          ┌──────────────────────────────┐
│  ArchiveOperationUI  │          │  ArchiveOperationExecutor    │
│  - Confirmation      │          │  - Background threads        │
│  - Conflict dialogs  │          │  - Progress tracking         │
│  - User input        │          │  - Archive I/O operations    │
└──────────────────────┘          │  - Format detection          │
                                  │  - Cross-storage support     │
                                  │                              │
                                  │  (Migrated from              │
                                  │   ArchiveOperations)         │
                                  └──────────────────────────────┘

Note: ArchiveOperations class remains for backward compatibility but 
delegates to ArchiveOperationTask. Core logic migrated to executor.
```

### State Machine

The ArchiveOperationTask implements a state machine that mirrors FileOperationTask:

```
IDLE
  │
  ├─ start_operation() → CONFIRMING (if confirmation required)
  │                   └─ CHECKING_CONFLICTS (if confirmation disabled)
  │
CONFIRMING
  │
  ├─ on_confirmed(True) → CHECKING_CONFLICTS
  └─ on_confirmed(False) → IDLE
  
CHECKING_CONFLICTS
  │
  ├─ conflicts found → RESOLVING_CONFLICT
  └─ no conflicts → EXECUTING
  
RESOLVING_CONFLICT
  │
  ├─ on_conflict_resolved("overwrite") → EXECUTING
  ├─ on_conflict_resolved("skip") → EXECUTING (extraction only)
  └─ on_conflict_resolved(None) → IDLE (ESC pressed)
  
EXECUTING
  │
  └─ operation complete → COMPLETED
  
COMPLETED
  │
  └─ cleanup → IDLE
```

### Threading Model

Archive operations execute in background daemon threads to keep the UI responsive:

1. **Main Thread**: Handles UI events, state transitions, and user input
2. **Background Thread**: Executes archive I/O operations (creation/extraction)
3. **Animation Thread**: Updates progress display during "Preparing..." phase

The `operation_in_progress` flag blocks user input during operations, and `operation_cancelled` flag enables cancellation.

## Components and Interfaces

### ArchiveOperationTask

**Responsibilities:**
- Orchestrate archive operation workflow through state machine
- Manage operation context (operation type, files, destination, conflicts)
- Coordinate with UI for confirmations and conflict resolution
- Delegate I/O operations to ArchiveOperationExecutor
- Handle state transitions and cleanup

**Key Methods:**
```python
def start_operation(self, operation_type: str, source_paths: List[Path], 
                   destination: Path, format_type: str = 'tar.gz'):
    """Start archive creation or extraction operation"""
    
def on_confirmed(self, confirmed: bool):
    """Handle user confirmation response"""
    
def on_conflict_resolved(self, choice: str, apply_to_all: bool = False):
    """Handle conflict resolution choice"""
    
def _check_conflicts(self):
    """Detect conflicts before execution"""
    
def _execute_operation(self):
    """Execute the archive operation via executor"""
```

**State:**
```python
@dataclass
class ArchiveOperationContext:
    operation_type: str  # 'create' or 'extract'
    source_paths: List[Path]  # Files to archive or archive file to extract
    destination: Path  # Archive file path or extraction directory
    format_type: str  # 'tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'zip'
    conflicts: List[Path]  # Conflicting files/directories
    current_conflict_index: int  # Current conflict being resolved
    results: Dict[str, List]  # success, skipped, errors
    options: Dict[str, bool]  # overwrite_all, skip_all
```

### ArchiveOperationExecutor

**Responsibilities:**
- Execute archive operations in background threads
- Track progress for individual files
- Handle errors and continue processing
- Support operation cancellation
- Manage cache invalidation

**Migration Strategy:**

This class will **migrate and adapt existing methods** from the `ArchiveOperations` class:

1. **Migrate core logic**: Move `create_archive()` and `extract_archive()` implementation to executor
2. **Add threading**: Wrap operations in background threads with daemon flag
3. **Add progress tracking**: Integrate with ProgressManager for file-by-file updates
4. **Add cancellation**: Check `operation_cancelled` flag during processing
5. **Keep helpers**: Migrate `_get_archive_handler()` and related helper methods
6. **Add conflict detection**: New `_check_conflicts()` method for pre-execution validation

**Key Methods:**
```python
def perform_create_operation(self, source_paths: List[Path], archive_path: Path,
                            format_type: str, completion_callback=None):
    """Create archive in background thread with progress tracking.
    
    Migrated from ArchiveOperations.create_archive() with threading support.
    """
    
def perform_extract_operation(self, archive_path: Path, destination_dir: Path,
                             overwrite: bool, completion_callback=None):
    """Extract archive in background thread with progress tracking.
    
    Migrated from ArchiveOperations.extract_archive() with threading support.
    """
    
def _count_files_recursively(self, paths: List[Path]) -> int:
    """Count total files for progress tracking"""
    
def _progress_callback(self):
    """Callback for progress manager to trigger UI refresh"""
    
def _get_archive_handler(self, archive_path: Path):
    """Get appropriate archive handler based on file extension.
    
    Migrated from ArchiveOperations._get_archive_handler().
    """
    
def _check_conflicts(self, context: ArchiveOperationContext) -> List[ConflictInfo]:
    """Check for conflicts before execution (new method)"""
```

### ArchiveOperationUI

**Responsibilities:**
- Display confirmation dialogs
- Display conflict resolution dialogs
- Handle user input and callbacks
- Format dialog messages

**Key Methods:**
```python
def show_confirmation_dialog(self, operation_type: str, source_paths: List[Path],
                            destination: Path, callback):
    """Show confirmation dialog for archive operation"""
    
def show_conflict_dialog(self, conflict_type: str, conflict_info: Dict,
                        conflict_num: int, total_conflicts: int, callback):
    """Show conflict resolution dialog"""
```

### ArchiveOperations (Modified)

**Responsibilities:**
- Maintain existing public API for backward compatibility
- Delegate to ArchiveOperationTask for task-based execution
- Support both synchronous (legacy) and asynchronous (new) usage

**Migration Strategy:**

The `ArchiveOperations` class will be **simplified** after migration:

1. **Keep public API**: `create_archive()` and `extract_archive()` methods remain
2. **Delegate to task**: Methods delegate to `ArchiveOperationTask` when `use_task=True`
3. **Legacy fallback**: Keep synchronous code path for backward compatibility (initially)
4. **Eventual cleanup**: Remove legacy code once all callers migrate to task-based approach

**Modified Methods:**
```python
def create_archive(self, source_paths: List[Path], archive_path: Path,
                  format_type: str = 'tar.gz', use_task: bool = True) -> bool:
    """Create archive - delegates to task if use_task=True.
    
    The core logic has been migrated to ArchiveOperationExecutor.
    This method now serves as a thin wrapper for backward compatibility.
    """
    
def extract_archive(self, archive_path: Path, destination_dir: Path,
                   overwrite: bool = False, use_task: bool = True) -> bool:
    """Extract archive - delegates to task if use_task=True.
    
    The core logic has been migrated to ArchiveOperationExecutor.
    This method now serves as a thin wrapper for backward compatibility.
    """
```

**What gets migrated:**
- Core archive creation logic → `ArchiveOperationExecutor.perform_create_operation()`
- Core extraction logic → `ArchiveOperationExecutor.perform_extract_operation()`
- Archive handler selection → `ArchiveOperationExecutor._get_archive_handler()`
- File counting logic → `ArchiveOperationExecutor._count_files_recursively()`

**What stays in ArchiveOperations:**
- Public API methods (thin wrappers)
- Cross-storage coordination (if not moved to executor)
- Backward compatibility code (temporary)

## Data Models

### ArchiveOperationContext

```python
@dataclass
class ArchiveOperationContext:
    """Context for an archive operation.
    
    Holds all state for an ongoing archive operation, ensuring
    operation state is self-contained.
    """
    operation_type: str  # 'create' or 'extract'
    source_paths: List[Path]  # Files to archive or archive file
    destination: Path  # Archive file or extraction directory
    format_type: str  # Archive format
    conflicts: List[Path] = field(default_factory=list)
    current_conflict_index: int = 0
    results: Dict[str, List] = field(default_factory=lambda: {
        'success': [],
        'skipped': [],
        'errors': []
    })
    options: Dict[str, bool] = field(default_factory=lambda: {
        'overwrite_all': False,
        'skip_all': False
    })
```

### ConflictInfo

```python
@dataclass
class ConflictInfo:
    """Information about a detected conflict.
    
    Used to pass conflict details to UI for display.
    """
    conflict_type: str  # 'archive_exists' or 'file_exists'
    path: Path  # Conflicting path
    size: Optional[int] = None  # File size if applicable
    is_directory: bool = False  # Whether conflict is a directory
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: State Machine Transitions

*For any* archive operation, state transitions should follow the defined state machine rules: IDLE can only transition to CONFIRMING or CHECKING_CONFLICTS, CONFIRMING can only transition to CHECKING_CONFLICTS or IDLE, CHECKING_CONFLICTS can only transition to RESOLVING_CONFLICT or EXECUTING, RESOLVING_CONFLICT can only transition to EXECUTING or IDLE, EXECUTING can only transition to COMPLETED, and COMPLETED can only transition to IDLE.

**Validates: Requirements 1.2, 6.3, 6.4, 13.3, 13.4, 13.6, 13.10**

### Property 2: Operation Type Support

*For any* operation type ('create' or 'extract'), the Archive_Task should be able to initiate and complete the operation successfully when given valid inputs.

**Validates: Requirements 1.3**

### Property 3: Background Thread Execution

*For any* archive operation, when the operation starts executing, a new background thread should be created and the operation should run on that thread (not the main thread).

**Validates: Requirements 2.2, 3.1**

### Property 4: Cancellation Support

*For any* archive operation in progress, when the operation_cancelled flag is set to True, the executor should stop processing remaining files and the task should transition to IDLE state.

**Validates: Requirements 2.4, 5.2, 5.4, 5.5**

### Property 5: Cross-Storage Operations

*For any* combination of storage schemes (local, S3, etc.), archive operations should complete successfully when source and destination use different storage backends.

**Validates: Requirements 2.5, 9.4**

### Property 6: Thread Cleanup

*For any* archive operation, when the operation completes (successfully or with errors), all background threads created for that operation should terminate cleanly.

**Validates: Requirements 3.4**

### Property 7: Daemon Thread Usage

*For any* background thread created by Archive_Executor, the thread's daemon flag should be set to True.

**Validates: Requirements 3.5**

### Property 8: Progress Updates for Creation

*For any* archive creation operation, the progress manager should receive an update call for each file added to the archive.

**Validates: Requirements 4.2**

### Property 9: Progress Updates for Extraction

*For any* archive extraction operation, the progress manager should receive an update call for each file extracted from the archive.

**Validates: Requirements 4.3**

### Property 10: Error Count Tracking

*For any* archive operation that encounters errors, the error count should be incremented for each error and tracked separately from the success count.

**Validates: Requirements 4.5, 7.2**

### Property 11: Configuration-Based Confirmation

*For any* archive operation, when the corresponding confirmation setting (CONFIRM_ARCHIVE_CREATE or CONFIRM_ARCHIVE_EXTRACT) is False, the operation should skip the CONFIRMING state and proceed directly to CHECKING_CONFLICTS.

**Validates: Requirements 6.5**

### Property 12: Error Logging

*For any* archive operation that encounters an error, the error should be logged with contextual information (operation type, file name, error message).

**Validates: Requirements 7.1**

### Property 13: Continue After Errors

*For any* archive operation processing multiple files, when an error occurs on one file, the operation should continue processing the remaining files.

**Validates: Requirements 7.3**

### Property 14: Exception Handling

*For any* archive operation, when a PermissionError, OSError, or ArchiveError is raised, the exception should be caught and handled appropriately (logged, error count incremented, operation continues).

**Validates: Requirements 7.5**

### Property 15: Archive Format Support

*For any* supported archive format ('tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'zip'), both creation and extraction operations should complete successfully.

**Validates: Requirements 9.3**

### Property 16: Cache Invalidation

*For any* archive operation that completes successfully, the cache manager should be called to invalidate affected paths.

**Validates: Requirements 9.5**

### Property 17: Completion Callback Invocation

*For any* archive operation with a completion_callback provided, when the operation completes, the callback should be called with (success_count, error_count) parameters.

**Validates: Requirements 10.2**

### Property 18: Callback Suppresses Logging

*For any* archive operation with a completion_callback provided, the default summary logging should be suppressed.

**Validates: Requirements 10.3**

### Property 19: Callback Thread Context

*For any* archive operation with a completion_callback provided, the callback should be invoked on the background thread (not the main thread).

**Validates: Requirements 10.4**

### Property 20: Callback on Cancellation

*For any* archive operation with a completion_callback provided, if the operation is cancelled, the callback should still be invoked.

**Validates: Requirements 10.5**

### Property 21: File List Refresh After Creation

*For any* archive creation operation that completes successfully, the file manager's refresh method should be called.

**Validates: Requirements 11.1**

### Property 22: File List Refresh After Extraction

*For any* archive extraction operation that completes successfully, the file manager's refresh method should be called.

**Validates: Requirements 11.2**

### Property 23: UI Dirty Flag

*For any* archive operation that completes, the file manager's mark_dirty method should be called to trigger UI redraw.

**Validates: Requirements 11.3**

### Property 24: Operation Flag Cleanup

*For any* archive operation that completes, the operation_in_progress flag should be cleared.

**Validates: Requirements 11.4**

### Property 25: Completion State Transition

*For any* archive operation that completes, the task should transition from EXECUTING to COMPLETED and then to IDLE.

**Validates: Requirements 11.5**

### Property 26: Backward Compatibility

*For any* existing code that calls ArchiveOperations.create_archive or ArchiveOperations.extract_archive, the methods should continue to work and return boolean success indicators.

**Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5**

### Property 27: Creation Conflict Detection

*For any* archive creation operation, if the destination archive file already exists, a conflict should be detected and the task should transition to CHECKING_CONFLICTS state.

**Validates: Requirements 13.1, 13.3**

### Property 28: Extraction Conflict Detection

*For any* archive extraction operation, if any files in the archive would overwrite existing files in the destination directory, conflicts should be detected and the task should transition to CHECKING_CONFLICTS state.

**Validates: Requirements 13.2, 13.3**

### Property 29: Overwrite Conflict Resolution

*For any* archive operation with conflicts, when the user selects "Overwrite", the operation should proceed and overwrite the conflicting files.

**Validates: Requirements 13.7**

### Property 30: Skip Conflict Resolution

*For any* archive extraction operation with conflicts, when the user selects "Skip", the conflicting files should not be extracted.

**Validates: Requirements 13.8**

### Property 31: Batch Conflict Resolution

*For any* archive operation with multiple conflicts, when the user selects an option with the Shift modifier key, the same decision should be applied to all remaining conflicts without showing additional dialogs.

**Validates: Requirements 13.9**

### Property 32: No Conflicts Fast Path

*For any* archive operation, when no conflicts are detected during CHECKING_CONFLICTS, the task should transition directly to EXECUTING state without entering RESOLVING_CONFLICT.

**Validates: Requirements 13.10**

## Error Handling

### Error Categories

1. **Archive Format Errors**
   - Unsupported format
   - Corrupted archive file
   - Invalid archive structure
   - **Handling**: Log error, increment error count, show user-friendly message

2. **File System Errors**
   - Permission denied
   - Disk space exhausted
   - File not found
   - Path too long
   - **Handling**: Log error, increment error count, continue with remaining files

3. **Cross-Storage Errors**
   - Network timeout
   - S3 access denied
   - Remote storage unavailable
   - **Handling**: Log error, increment error count, retry once, then fail gracefully

4. **Cancellation**
   - User presses ESC
   - Operation timeout
   - **Handling**: Clean up partial work, transition to IDLE, log cancellation

### Error Recovery Strategy

```python
try:
    # Perform archive operation
    perform_archive_operation()
except PermissionError as e:
    logger.error(f"Permission denied: {e}")
    error_count += 1
    progress_manager.increment_errors()
    # Continue with next file
except OSError as e:
    if "No space left" in str(e):
        logger.error(f"Disk space exhausted: {e}")
        # Stop operation, cannot continue
        break
    else:
        logger.error(f"OS error: {e}")
        error_count += 1
        # Continue with next file
except ArchiveError as e:
    logger.error(f"Archive error: {e.user_message}")
    error_count += 1
    # Continue with next file
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    error_count += 1
    # Continue with next file
finally:
    # Always clean up resources
    cleanup_resources()
```

### User-Facing Error Messages

- **Permission Denied**: "Cannot access {filename}: Permission denied"
- **Disk Space**: "Insufficient disk space to complete operation"
- **Corrupted Archive**: "Archive file '{filename}' is corrupted or invalid"
- **Unsupported Format**: "Archive format not supported: {format}"
- **Network Error**: "Cannot access remote storage: {error}"

## Testing Strategy

### Dual Testing Approach

The testing strategy combines unit tests for specific scenarios and property-based tests for comprehensive coverage:

- **Unit Tests**: Verify specific examples, edge cases, and error conditions
- **Property Tests**: Verify universal properties across all inputs using randomized testing

Both approaches are complementary and necessary for comprehensive validation.

### Unit Testing

Unit tests focus on:
- **State transitions**: Verify correct state machine behavior for specific sequences
- **Conflict detection**: Test specific conflict scenarios (file exists, directory exists)
- **Error handling**: Test specific error conditions (permission denied, disk full)
- **Integration points**: Test interaction between components
- **Edge cases**: Empty archives, single file archives, nested directories

Example unit tests:
```python
def test_archive_creation_with_existing_file():
    """Test that existing archive file triggers conflict detection"""
    
def test_extraction_skips_conflicting_files():
    """Test that Skip option prevents file extraction"""
    
def test_cancellation_stops_operation():
    """Test that ESC key cancels operation"""
```

### Property-Based Testing

Property tests use a PBT library (e.g., Hypothesis for Python) to verify properties across many randomized inputs. Each test should run minimum 100 iterations.

**Test Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with: **Feature: archive-task-migration, Property {number}: {property_text}**
- Tests reference design document properties

Example property tests:
```python
@given(operation_type=st.sampled_from(['create', 'extract']),
       files=st.lists(st.text(), min_size=1))
def test_property_2_operation_type_support(operation_type, files):
    """Feature: archive-task-migration, Property 2: Operation Type Support
    
    For any operation type, the Archive_Task should be able to initiate
    and complete the operation successfully.
    """
    
@given(storage_schemes=st.lists(st.sampled_from(['file', 's3']), min_size=2, max_size=2))
def test_property_5_cross_storage_operations(storage_schemes):
    """Feature: archive-task-migration, Property 5: Cross-Storage Operations
    
    For any combination of storage schemes, archive operations should
    complete successfully.
    """
```

### Testing Guidelines

1. **Avoid over-testing**: Focus on core functional logic and important edge cases
2. **Limit verification attempts**: Maximum 2 attempts to fix failing tests
3. **No mocks for passing tests**: Tests must validate real functionality
4. **Explore existing tests first**: Review and extend existing test files before creating new ones
5. **Minimal test solutions**: Write concise tests that verify specific behaviors

### Test Organization

```
test/
├── test_archive_operation_task.py       # Task state machine tests
├── test_archive_operation_executor.py   # Executor I/O tests
├── test_archive_operation_ui.py         # UI interaction tests
└── test_archive_integration.py          # End-to-end integration tests
```

### Property Test Examples

**Property 1: State Machine Transitions**
- Generate random sequences of valid state transitions
- Verify each transition follows state machine rules
- Verify invalid transitions are rejected

**Property 8: Progress Updates for Creation**
- Generate random file lists of varying sizes
- Create archive and count progress update calls
- Verify update count matches file count

**Property 31: Batch Conflict Resolution**
- Generate random number of conflicts (2-10)
- Apply "overwrite_all" or "skip_all" decision
- Verify decision applied to all conflicts without additional dialogs

## Implementation Notes

### Naming Consistency

All new classes use the `ArchiveOperation` prefix for consistency:
- `ArchiveOperationTask` (matches `FileOperationTask`)
- `ArchiveOperationExecutor` (matches `FileOperationExecutor`)
- `ArchiveOperationUI` (matches `FileOperationUI`)

### Code Reuse

The implementation reuses patterns and code from file operations:
- State machine structure from `FileOperationTask`
- Threading patterns from `FileOperationExecutor`
- Dialog patterns from `FileOperationUI`
- Progress tracking from `ProgressManager`

### Migration Path

The migration supports gradual adoption:
1. **Phase 1**: Implement new task-based components
2. **Phase 2**: Add `use_task` parameter to `ArchiveOperations` methods (default `True`)
3. **Phase 3**: Update callers to use task-based approach
4. **Phase 4**: Remove legacy synchronous code paths

### Performance Considerations

- **File counting**: Performed in background thread to avoid blocking UI
- **Progress updates**: Throttled to avoid excessive UI redraws
- **Large archives**: Use lazy loading for archive structure caching
- **Cross-storage**: Use temporary files to minimize network round-trips

### Logging Standards

All components use the unified logging system:
```python
from tfm_log_manager import getLogger

class ArchiveOperationTask(BaseTask):
    def __init__(self, file_manager, ui, executor):
        super().__init__(file_manager)
        self.logger = getLogger("ArchiveOp")
```

Log levels:
- **ERROR**: Operation failures, exceptions, critical issues
- **WARNING**: Conflicts, skipped files, degraded functionality
- **INFO**: Normal operations, state transitions, completion summaries
- **DEBUG**: Detailed diagnostic information (rarely used)
