# Implementation Plan: Sort Entries Optimization

## Overview

Optimize `FileListManager.sort_entries()` to eliminate redundant `is_dir()` calls by caching directory status during the initial separation phase. This reduces network operations on remote filesystems from 2N to N calls.

## Tasks

- [x] 1. Optimize sort_entries() to cache is_dir() results
  - Replace dual list comprehensions with single loop that caches is_dir() results
  - Use cached results for directory/file separation
  - Add error handling for OSError and PermissionError during is_dir() calls
  - Maintain all existing functionality and behavior
  - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.4, 4.1, 4.2_

- [ ]* 1.1 Write property test for single is_dir() call per entry
  - **Property 1: Single is_dir() Call Per Entry**
  - **Validates: Requirements 1.1**
  - Mock is_dir() to count calls
  - Generate random entry lists of various sizes
  - Verify call count equals entry count (not 2x entry count)
  - _Requirements: 1.1_

- [ ]* 1.2 Write property test for directory-first ordering
  - **Property 2: Directory-First Ordering Preserved**
  - **Validates: Requirements 2.1**
  - Generate random mixed lists of directories and files
  - Verify all directories appear before all files in sorted result
  - _Requirements: 2.1_

- [ ]* 1.3 Write property test for sort order correctness
  - **Property 3: Sort Order Correctness**
  - **Validates: Requirements 2.2, 2.3, 2.4, 2.5**
  - Generate random entry lists
  - Test all sort modes (name, ext, size, date, type)
  - Verify sorted order matches expected order for each mode
  - _Requirements: 2.2, 2.3, 2.4, 2.5_

- [ ]* 1.4 Write property test for reverse order correctness
  - **Property 4: Reverse Order Correctness**
  - **Validates: Requirements 2.6**
  - Generate random entry lists
  - Verify reverse=True produces reversed order within groups (directories, files)
  - _Requirements: 2.6_

- [ ]* 1.5 Write property test for error handling
  - **Property 5: Error Handling Preserves Sorting**
  - **Validates: Requirements 3.1, 3.2, 3.4**
  - Generate lists with some entries that raise OSError or PermissionError
  - Verify sorting completes and includes all entries
  - Verify error entries are treated as files
  - _Requirements: 3.1, 3.2, 3.4_

- [ ]* 1.6 Write property test for backward compatibility
  - **Property 6: Backward Compatibility**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
  - Generate random entry lists
  - Compare optimized output with original implementation output
  - Verify identical results for all sort modes and reverse settings
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 1.7 Write unit tests for edge cases
  - Test empty list
  - Test all directories
  - Test all files
  - Test mixed permissions
  - Test stat errors during sort key generation
  - _Requirements: 3.3, 4.5_

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 3. Create performance validation tests
  - [ ]* 3.1 Write test to measure is_dir() call reduction
    - Mock is_dir() to count calls
    - Compare call count before and after optimization
    - Verify 50% reduction (2N → N)
    - _Requirements: 5.1_

  - [ ]* 3.2 Write test to measure sorting time improvement
    - Mock remote filesystem with artificial latency
    - Measure sorting time before and after optimization
    - Verify noticeable improvement (target: 30-50% faster)
    - _Requirements: 5.2, 5.3_

  - [ ]* 3.3 Write test for local filesystem performance
    - Measure sorting time on local filesystem
    - Verify no performance regression
    - _Requirements: 5.3_

- [ ] 4. Final checkpoint - Ensure all tests pass
  - Run all unit tests, property tests, and performance tests
  - Verify no regressions in existing file list tests
  - Verify performance improvements are achieved
  - Ask user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Performance tests validate the optimization achieves its goals
- The implementation is very simple - main work is in testing and validation
