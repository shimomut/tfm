# Requirements Document

## Introduction

This specification addresses a performance issue where `_check_control_master()` subprocess calls occur too frequently in SSH operations, even when using cached data. The health check mechanism helps but still results in expensive subprocess calls that block operations.

## Glossary

- **Control Master**: SSH multiplexing feature that reuses a single connection for multiple sessions
- **_check_control_master()**: Method that runs `ssh -O check` subprocess to verify control master status
- **Health Check**: Periodic verification that an SSH connection is still active
- **Health Check Interval**: Time period between health checks (currently used to rate-limit checks)
- **SSHConnection**: Class managing a single SSH connection to a remote host
- **SSHConnectionManager**: Singleton managing multiple SSH connections
- **SSHCache**: Cache for stat results to avoid redundant network operations

## Requirements

### Requirement 1: Reduce Control Master Check Frequency

**User Story:** As a user browsing remote directories, I want operations to be fast, so that I don't experience delays from unnecessary subprocess calls.

#### Acceptance Criteria

1. WHEN a connection is recently verified as healthy, THE System SHALL skip control master checks within the health check interval
2. WHEN using cached data, THE System SHALL NOT perform control master checks
3. WHEN the health check interval has not elapsed, THE System SHALL assume the connection is still active
4. WHEN a connection operation fails, THE System SHALL perform a control master check to verify status

### Requirement 2: Optimize Health Check Logic

**User Story:** As a developer, I want health checks to be efficient, so that they don't add unnecessary overhead to operations.

#### Acceptance Criteria

1. WHEN checking connection health, THE System SHALL use the cached health status if within the interval
2. WHEN the health check interval elapses, THE System SHALL perform a single control master check
3. WHEN a control master check succeeds, THE System SHALL cache the result for the health check interval
4. WHEN a control master check fails, THE System SHALL mark the connection as unhealthy immediately

### Requirement 3: Maintain Connection Reliability

**User Story:** As a user, I want the system to detect disconnections, so that I get clear error messages instead of hanging operations.

#### Acceptance Criteria

1. WHEN a connection operation fails with a network error, THE System SHALL verify control master status
2. WHEN control master is inactive, THE System SHALL attempt reconnection
3. WHEN reconnection fails, THE System SHALL provide a clear error message
4. WHEN control master is active but operations fail, THE System SHALL report the specific error

### Requirement 4: Preserve Existing Behavior

**User Story:** As a developer, I want the optimization to be transparent, so that existing code continues to work without changes.

#### Acceptance Criteria

1. THE System SHALL maintain the same public API for SSHConnection
2. THE System SHALL maintain the same public API for SSHConnectionManager
3. THE System SHALL detect connection failures as reliably as before
4. THE System SHALL reconnect automatically when connections are lost
5. THE System SHALL maintain thread safety for concurrent operations

### Requirement 5: Performance Improvement

**User Story:** As a user on a remote connection, I want operations to complete quickly, so that I can navigate efficiently.

#### Acceptance Criteria

1. WHEN performing cached operations, THE System SHALL NOT call _check_control_master()
2. WHEN within the health check interval, THE System SHALL NOT call _check_control_master()
3. WHEN browsing directories, THE System SHALL minimize subprocess overhead
4. WHEN profiling is enabled, THE System SHALL show reduced subprocess call count
