# Design Document

## Overview

This design optimizes `FileListManager.sort_entries()` to eliminate redundant `is_dir()` calls by caching the directory status during the initial separation phase. This reduces network operations on remote filesystems from 2N to N, providing a 50% reduction in stat calls.

## Architecture

The optimization is localized to the `sort_entries()` method in `src/tfm_file_list_manager.py`. No changes to the public API or calling code are required.

### Current Implementation Problem

```python
# Current code calls is_dir() twice per entry:
directories = [entry for entry in entries if entry.is_dir()]  # First call
files = [entry for entry in entries if not entry.is_dir()]    # Second call
```

For 100 entries, this results in 200 `is_dir()` calls. On SFTP, each call involves network latency.

### Optimized Implementation

```python
# Optimized code calls is_dir() once per entry:
dirs_and_files = []
for entry in entries:
    try:
        is_directory = entry.is_dir()  # Single call, cached result
        dirs_and_files.append((entry, is_directory))
    except (OSError, PermissionError):
        # Treat as file on error
        dirs_and_files.append((entry, False))

# Separate using cached results
directories = [entry for entry, is_dir in dirs_and_files if is_dir]
files = [entry for entry, is_dir in dirs_and_files if not is_dir]
```

For 100 entries, this results in 100 `is_dir()` calls - a 50% reduction.

## Components and Interfaces

### Modified Component: FileListManager.sort_entries()

**Location:** `src/tfm_file_list_manager.py`

**Changes:**
1. Add initial loop to cache `is_dir()` results
2. Use cached results for directory/file separation
3. Maintain all existing functionality

**Interface (unchanged):**
```python
def sort_entries(self, entries, sort_mode, reverse=False):
    """Sort file entries based on the specified mode
    
    Args:
        entries: List of Path objects to sort
        sort_mode: 'name', 'ext', 'size', or 'date'
        reverse: Whether to reverse the sort order
        
    Returns:
        Sorted list with directories always first
    """
```

## Data Models

No changes to data models. The optimization uses a temporary list of tuples:

```python
dirs_and_files: List[Tuple[Path, bool]]
# Each tuple contains (entry, is_directory_flag)
```

This temporary structure is only used within the method and is not exposed externally.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system - essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Single is_dir() Call Per Entry

*For any* list of entries, sorting should call `is_dir()` at most once per entry.

**Validates: Requirements 1.1**

### Property 2: Directory-First Ordering Preserved

*For any* sorted result, all directories should appear before all files.

**Validates: Requirements 2.1**

### Property 3: Sort Order Correctness

*For any* sort mode and list of entries, the sorted result should match the expected order for that mode.

**Validates: Requirements 2.2, 2.3, 2.4, 2.5**

### Property 4: Reverse Order Correctness

*For any* list of entries, sorting with reverse=True should produce the reverse order within each group (directories, files).

**Validates: Requirements 2.6**

### Property 5: Error Handling Preserves Sorting

*For any* entry that raises an error during `is_dir()`, the entry should be treated as a file and included in the sorted result.

**Validates: Requirements 3.1, 3.2, 3.4**

### Property 6: Backward Compatibility

*For any* valid input to the original implementation, the optimized implementation should produce identical output.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

## Error Handling

### OSError and PermissionError During is_dir()

**Strategy:** Treat the entry as a file and continue sorting.

**Rationale:** 
- Allows sorting to complete even with permission issues
- Consistent with existing error handling in `get_sort_key()`
- Prevents one bad entry from blocking the entire sort

**Implementation:**
```python
try:
    is_directory = entry.is_dir()
except (OSError, PermissionError):
    is_directory = False  # Treat as file
```

### Stat Errors During Sort Key Generation

**Strategy:** Use entry name as fallback sort key (existing behavior).

**Rationale:**
- Already implemented in current code
- Provides graceful degradation
- Ensures sorting always completes

## Testing Strategy

### Unit Tests

1. **Test basic sorting correctness**
   - Verify directories appear before files
   - Verify sort modes work correctly (name, ext, size, date)
   - Verify reverse parameter works

2. **Test error handling**
   - Mock `is_dir()` to raise OSError
   - Mock `is_dir()` to raise PermissionError
   - Verify sorting continues with errors

3. **Test edge cases**
   - Empty list
   - All directories
   - All files
   - Mixed permissions

### Property Tests

1. **Property 1: Single is_dir() call per entry**
   - Mock `is_dir()` to count calls
   - Generate random entry lists
   - Verify call count equals entry count

2. **Property 2: Directory-first ordering**
   - Generate random mixed lists
   - Verify all directories before all files

3. **Property 3: Sort order correctness**
   - Generate random entry lists
   - Compare with expected sort order for each mode

4. **Property 4: Reverse order correctness**
   - Generate random entry lists
   - Verify reverse=True produces reversed order within groups

5. **Property 5: Error handling preserves sorting**
   - Generate lists with some entries that raise errors
   - Verify sorting completes and includes all entries

6. **Property 6: Backward compatibility**
   - Generate random entry lists
   - Compare optimized output with original implementation output

### Performance Tests

1. **Measure is_dir() call reduction**
   - Count calls before and after optimization
   - Verify 50% reduction (2N → N)

2. **Measure sorting time improvement**
   - Time sorting on mock remote filesystem
   - Verify noticeable improvement (target: 30-50% faster)

### Integration Tests

1. **Test with real SFTP connection**
   - Sort large directory (100+ entries)
   - Measure time improvement
   - Verify correctness

2. **Test with local filesystem**
   - Verify no performance regression
   - Verify correctness maintained

## Performance Analysis

### Expected Improvements

**Remote Filesystems (SFTP, S3):**
- 50% reduction in network stat operations
- 30-50% faster sorting time (depends on network latency)
- More responsive UI during directory navigation

**Local Filesystems:**
- Minimal impact (is_dir() is already fast)
- Slight overhead from tuple creation (negligible)
- Overall performance similar or slightly better

### Measurement Strategy

1. Add profiling to count `is_dir()` calls
2. Measure sorting time with `--profile=rendering`
3. Compare before/after metrics
4. Test on both local and remote filesystems

## Implementation Notes

### Code Changes

**File:** `src/tfm_file_list_manager.py`

**Method:** `sort_entries()`

**Changes:**
1. Replace dual list comprehensions with single loop
2. Cache `is_dir()` results in tuples
3. Use cached results for separation
4. Add error handling for `is_dir()` calls

**Lines affected:** ~10 lines (lines 252-253 and surrounding context)

### Backward Compatibility

- No API changes
- No behavior changes (except performance)
- No changes to calling code required
- Safe to deploy without coordination

### Testing Requirements

- All existing tests must pass
- New tests must verify optimization
- Performance tests must show improvement
- No regressions on local filesystems
