# Implementation Plan: SSH Control Master Check Optimization

## Overview

Optimize SSH control master checking by caching the health status and skipping redundant subprocess calls within the check interval. This reduces subprocess overhead from 1 call per operation to 1 call per 5 seconds.

## Tasks

- [x] 1. Add control master status caching to SSHConnection
  - Add `_last_control_master_check` timestamp attribute
  - Add `_control_master_check_interval` configuration attribute (default: 5.0 seconds)
  - Add `_cached_control_master_status` boolean attribute
  - Initialize new attributes in `__init__()`
  - _Requirements: 1.1, 1.2, 1.3, 4.1_

- [x] 2. Optimize SSHConnection.is_connected() to use cached status
  - Check if within control master check interval
  - Return cached status if within interval
  - Call `_check_control_master()` only if interval elapsed
  - Update cached status and timestamp after check
  - Mark connection as disconnected if check fails
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [x] 3. Optimize SSHConnectionManager._check_connection_health()
  - Check if within health check interval
  - Return `conn._connected` directly if within interval (skip is_connected() call)
  - Call `conn.is_connected()` only if health check interval elapsed
  - Update health check timestamp after check
  - _Requirements: 1.1, 2.1, 2.2, 4.2_

- [ ]* 3.1 Write property test for control master check rate limiting
  - **Property 1: Control Master Check Rate Limiting**
  - **Validates: Requirements 1.1, 1.2, 1.3**
  - Mock `_check_control_master()` to count calls
  - Generate random operation sequences within check interval
  - Verify at most one subprocess call per interval
  - _Requirements: 1.1, 1.2, 1.3_

- [ ]* 3.2 Write property test for health status accuracy
  - **Property 2: Health Status Accuracy**
  - **Validates: Requirements 2.1, 2.2, 2.3**
  - Generate random operation patterns
  - Verify operations succeed when cached status is healthy
  - Verify fresh checks triggered on failures
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 3.3 Write property test for disconnection detection
  - **Property 3: Disconnection Detection**
  - **Validates: Requirements 3.1, 3.2**
  - Simulate connection drops at random times
  - Verify detection within expected time bounds (interval + check time)
  - _Requirements: 3.1, 3.2_

- [ ]* 3.4 Write property test for backward compatibility
  - **Property 4: Backward Compatibility**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
  - Run existing SSH tests with optimized implementation
  - Verify all tests pass without modification
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 3.5 Write property test for performance improvement
  - **Property 5: Performance Improvement**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
  - Measure subprocess call count before and after optimization
  - Verify at least 80% reduction in calls
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 3.6 Write unit tests for caching behavior
  - Test control master check caching within interval
  - Test fresh check after interval elapses
  - Test cache invalidation on connection errors
  - Test thread safety of cached status
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 4.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 5. Create performance validation tests
  - [ ]* 5.1 Write test to measure subprocess call reduction
    - Mock `_check_control_master()` to count calls
    - Perform 100 operations within 5 seconds
    - Compare call count before and after optimization
    - Verify 99% reduction (100 → 1)
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 5.2 Write test to measure operation latency improvement
    - Mock subprocess with artificial latency (10ms)
    - Measure total time for 100 operations
    - Compare before and after optimization
    - Verify significant improvement (1000ms → 10ms)
    - _Requirements: 5.2, 5.3_

  - [ ]* 5.3 Write integration test with real SFTP
    - Connect to real SFTP server
    - Perform multiple stat operations
    - Measure subprocess call count
    - Verify operations still work correctly
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 6. Final checkpoint - Ensure all tests pass
  - Run all unit tests, property tests, and performance tests
  - Verify no regressions in existing SSH tests
  - Verify performance improvements are achieved
  - Ask user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Performance tests validate the optimization achieves its goals
- The implementation is straightforward - main work is in testing and validation
- Default check interval is 5 seconds, can be made configurable if needed
