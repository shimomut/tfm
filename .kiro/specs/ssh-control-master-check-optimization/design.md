# Design Document

## Overview

This design optimizes SSH control master checking by caching the health status and skipping redundant subprocess calls within the health check interval. The key insight is that if we recently verified the connection is healthy, we don't need to check again immediately.

## Architecture

The optimization focuses on two areas:

1. **SSHConnection.is_connected()** - Cache the control master status
2. **SSHConnectionManager._check_connection_health()** - Use cached status more aggressively

### Current Implementation Problem

```python
# Current flow for EVERY operation:
get_connection()
  → _check_connection_health()
    → conn.is_connected()
      → _check_control_master()  # Subprocess call!
        → subprocess.run(['ssh', '-O', 'check', ...])  # Expensive!
```

Even with the health check interval, `is_connected()` still calls `_check_control_master()` on line 1204, which runs a subprocess.

### Optimized Implementation

```python
# Optimized flow:
get_connection()
  → _check_connection_health()
    → Check if within health check interval
      → If yes: return cached status (no subprocess)
      → If no: call is_connected() which checks control master
```

## Components and Interfaces

### Modified Component 1: SSHConnection

**Location:** `src/tfm_ssh_connection.py`

**Changes:**
1. Add `_last_control_master_check` timestamp
2. Add `_control_master_check_interval` (default: 5 seconds)
3. Modify `is_connected()` to cache control master status
4. Only call `_check_control_master()` if interval has elapsed

**New attributes:**
```python
self._last_control_master_check = 0  # Timestamp of last check
self._control_master_check_interval = 5.0  # Seconds between checks
self._cached_control_master_status = False  # Cached status
```

**Modified method:**
```python
def is_connected(self) -> bool:
    """Check if connection is active (with caching)"""
    with self._lock:
        if not self._connected:
            return False
        
        # Check if we need to verify control master
        current_time = time.time()
        if current_time - self._last_control_master_check < self._control_master_check_interval:
            # Use cached status
            return self._cached_control_master_status
        
        # Perform actual check
        status = self._check_control_master()
        self._cached_control_master_status = status
        self._last_control_master_check = current_time
        
        if not status:
            self._connected = False
        
        return status
```

### Modified Component 2: SSHConnectionManager

**Location:** `src/tfm_ssh_connection.py`

**Changes:**
1. Simplify `_check_connection_health()` to trust the cached status more
2. Only force a check when the health check interval has elapsed

**Modified method:**
```python
def _check_connection_health(self, hostname: str, conn: SSHConnection) -> bool:
    """Check if a connection is still healthy (optimized)"""
    current_time = time.time()
    
    # Check if we've done a health check recently
    last_check = self._last_health_check.get(hostname, 0)
    if current_time - last_check < self._health_check_interval:
        # Trust the connection's internal status without forcing a check
        # This avoids subprocess calls within the health check interval
        with conn._lock:
            return conn._connected
    
    # Health check interval elapsed, perform actual check
    try:
        if conn.is_connected():
            self._last_health_check[hostname] = current_time
            return True
        else:
            self.logger.warning(f"Health check failed for {hostname}: control master not active")
            return False
    except Exception as e:
        self.logger.warning(f"Health check failed for {hostname}: {e}")
        return False
```

## Data Models

No changes to data models. The optimization adds internal caching fields to existing classes.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system - essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Control Master Check Rate Limiting

*For any* sequence of operations within the check interval, at most one control master subprocess call should occur.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Health Status Accuracy

*For any* connection, if the cached status is healthy and within the interval, operations should succeed or trigger a fresh check on failure.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Disconnection Detection

*For any* connection that becomes inactive, the system should detect it within one health check interval plus one control master check interval.

**Validates: Requirements 3.1, 3.2**

### Property 4: Backward Compatibility

*For any* valid usage of SSHConnection or SSHConnectionManager, the optimized implementation should behave identically to the original.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 5: Performance Improvement

*For any* series of cached operations, the number of subprocess calls should be reduced by at least 80% compared to the unoptimized version.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

## Error Handling

### Connection Failures During Operations

**Strategy:** On operation failure, force a control master check to verify connection status.

**Implementation:**
```python
def stat(self, path: str) -> Dict:
    """Get file stats with error handling"""
    try:
        # Perform operation
        return self._sftp_stat(path)
    except Exception as e:
        # Force a control master check on error
        if not self._check_control_master():
            self._connected = False
            raise SSHConnectionError("Connection lost")
        # Connection is fine, re-raise original error
        raise
```

### Stale Cached Status

**Strategy:** Clear cached status on any connection error.

**Implementation:**
```python
def _handle_connection_error(self):
    """Handle connection errors by clearing cache"""
    with self._lock:
        self._connected = False
        self._cached_control_master_status = False
        self._last_control_master_check = 0
```

## Testing Strategy

### Unit Tests

1. **Test control master check caching**
   - Mock `_check_control_master()` to count calls
   - Perform multiple `is_connected()` calls within interval
   - Verify only one subprocess call

2. **Test health check optimization**
   - Mock time to control intervals
   - Verify health checks use cached status within interval
   - Verify fresh checks after interval elapses

3. **Test error handling**
   - Simulate connection failures
   - Verify control master check is forced
   - Verify cached status is cleared

### Property Tests

1. **Property 1: Control master check rate limiting**
   - Generate random operation sequences
   - Count subprocess calls
   - Verify at most one call per interval

2. **Property 2: Health status accuracy**
   - Generate random operation patterns
   - Verify operations succeed when cached status is healthy
   - Verify fresh checks on failures

3. **Property 3: Disconnection detection**
   - Simulate connection drops at random times
   - Verify detection within expected time bounds

4. **Property 4: Backward compatibility**
   - Run existing SSH tests
   - Verify all pass without modification

5. **Property 5: Performance improvement**
   - Measure subprocess call count before and after
   - Verify at least 80% reduction

### Integration Tests

1. **Test with real SFTP operations**
   - Connect to SFTP server
   - Perform multiple stat operations
   - Verify reduced subprocess calls
   - Verify operations still work correctly

2. **Test connection recovery**
   - Establish connection
   - Simulate network interruption
   - Verify automatic reconnection
   - Verify operations resume

## Performance Analysis

### Expected Improvements

**Subprocess Call Reduction:**
- Before: 1 subprocess call per operation (even with health check interval)
- After: 1 subprocess call per 5 seconds (control master check interval)
- For 100 operations in 5 seconds: 100 calls → 1 call (99% reduction)

**Operation Latency:**
- Subprocess call overhead: ~10-50ms per call
- Cached check overhead: <1ms
- For 100 operations: 1-5 seconds saved

**User Experience:**
- More responsive directory browsing
- Smoother scrolling through file lists
- Faster sorting operations

### Measurement Strategy

1. Add counters for subprocess calls
2. Measure operation latency with profiling
3. Compare before/after metrics
4. Test on both fast and slow networks

## Implementation Notes

### Thread Safety

The optimization maintains thread safety by:
1. Using locks around cached status access
2. Atomic updates to cached values
3. No race conditions between check and use

### Configuration

The check intervals should be configurable:
```python
# In SSHConnection.__init__
self._control_master_check_interval = config.get('control_master_check_interval', 5.0)
```

### Backward Compatibility

- No API changes
- No behavior changes (except performance)
- Existing tests should pass without modification
- Safe to deploy without coordination

## Risks and Mitigations

### Risk 1: Delayed Disconnection Detection

**Risk:** Cached status might hide disconnections for up to 5 seconds.

**Mitigation:** 
- 5 seconds is acceptable for most use cases
- Operations that fail will force immediate check
- Health check interval can be tuned if needed

### Risk 2: Stale Cache After Network Changes

**Risk:** Network changes might not be detected immediately.

**Mitigation:**
- Any operation failure triggers fresh check
- Health check interval provides periodic verification
- Connection errors clear the cache

### Risk 3: Race Conditions

**Risk:** Concurrent operations might see inconsistent cached status.

**Mitigation:**
- All cache access is protected by locks
- Atomic updates to cached values
- Existing thread safety mechanisms maintained
