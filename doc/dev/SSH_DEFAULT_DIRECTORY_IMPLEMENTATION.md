# SSH Default Directory Implementation

## Overview

This document describes the implementation of SSH default directory detection, which ensures that SFTP browsing starts in a natural location (home directory or current working directory) instead of always starting at the root directory.

## Problem Statement

Previously, when opening an SFTP connection through the drives dialog, TFM would always navigate to the root directory (`/`). This required users to manually navigate through the directory tree to reach their working directory, typically:

```
/ → home → username → projects
```

This was inconvenient and inconsistent with typical SSH/SFTP client behavior, which usually starts in the user's home directory.

## Solution

The solution involves two components:

1. **Connection-level detection**: Capture the default directory during connection establishment
2. **Navigation-level usage**: Use the default directory when navigating to SSH drives

### Component 1: Default Directory Detection

**File**: `src/tfm_ssh_connection.py`

During connection establishment, the `connect()` method already executes a `pwd` command to test the connection. We now parse the output to capture the default directory:

```python
# Test connection with a simple pwd command
stdout, stderr, returncode = self._execute_sftp_command(['pwd'], timeout=10)

if returncode == 0:
    self._connected = True
    
    # Parse pwd output to get default directory
    # SFTP pwd output format: "Remote working directory: /path/to/dir"
    for line in stdout.strip().split('\n'):
        if line.startswith('Remote working directory:'):
            self.default_directory = line.split(':', 1)[1].strip()
            break
    
    # Fallback to root if we couldn't parse the directory
    if not self.default_directory:
        self.default_directory = '/'
```

**Key points**:
- No additional network round-trip required (reuses existing `pwd` command)
- Graceful fallback to root if parsing fails
- Stored in `SSHConnection.default_directory` attribute

### Component 2: Navigation Integration

**File**: `src/tfm_drives_dialog.py`

When navigating to an SSH drive through the drives dialog, we now connect to the server and use the default directory:

```python
elif drive_entry.drive_type == 'ssh':
    # For SSH, connect and get the default directory
    try:
        from tfm_ssh_connection import SSHConnectionManager
        from tfm_ssh_config import SSHConfigParser
        
        # Extract hostname from ssh://hostname/ path
        hostname = drive_entry.path.replace('ssh://', '').rstrip('/')
        
        # Get SSH config
        parser = SSHConfigParser()
        hosts = parser.parse()
        config = hosts.get(hostname, {'HostName': hostname})
        
        # Get connection and retrieve default directory
        conn_manager = SSHConnectionManager.get_instance()
        conn = conn_manager.get_connection(hostname, config)
        
        # Use the default directory if available
        if conn.default_directory and conn.default_directory != '/':
            drive_path = Path(f"ssh://{hostname}{conn.default_directory}")
            
    except Exception as e:
        # If we can't get the default directory, fall back to root
        pass
```

**Key points**:
- Connection is established on-demand (only when user selects the drive)
- Uses connection pooling (existing connection reused if available)
- Graceful fallback to root on any error
- No changes required to SSH path implementation

## SFTP pwd Output Format

The SFTP `pwd` command returns output in this format:

```
Remote working directory: /home/username
```

The implementation parses this line to extract the directory path. If the format is different or parsing fails, it falls back to `/`.

## Error Handling

The implementation includes multiple layers of error handling:

1. **Parsing failure**: Falls back to `/` if pwd output cannot be parsed
2. **Connection failure**: Falls back to original root path if connection fails
3. **Exception during navigation**: Catches all exceptions to prevent dialog crashes

## Performance Considerations

- **No additional overhead**: Reuses existing `pwd` command during connection
- **Connection pooling**: Leverages existing connection manager for efficiency
- **Lazy evaluation**: Only connects when user actually selects the drive

## Testing

**Test file**: `test/test_ssh_default_directory.py`

Test coverage includes:
- Default directory detection from pwd output
- Fallback to root on parsing failure
- Drives dialog navigation using default directory
- Error handling and fallback behavior

**Demo file**: `demo/demo_ssh_default_directory.py`

Demonstrates:
- Default directory detection
- Drives dialog navigation
- Before/after comparison
- Fallback behavior

## User Experience

**Before**:
```
User selects "devserver" from drives dialog
→ Navigates to: ssh://devserver/
→ Shows: /, /bin, /etc, /home, /usr, ...
→ User must navigate: / → home → alice → projects
```

**After**:
```
User selects "devserver" from drives dialog
→ Connects and detects: /home/alice/projects
→ Navigates to: ssh://devserver/home/alice/projects
→ Shows project directory immediately
```

## Compatibility

- **Backward compatible**: Falls back to root if detection fails
- **No breaking changes**: Existing SSH functionality unchanged
- **Server agnostic**: Works with any SFTP server that supports `pwd` command

## Future Enhancements

Potential improvements:
1. Cache default directory per hostname to avoid repeated connections
2. Allow user to configure preferred starting directory per host
3. Remember last visited directory per host (like browser history)

## References

- **SSH Connection**: `src/tfm_ssh_connection.py`
- **Drives Dialog**: `src/tfm_drives_dialog.py`
- **SSH Path**: `src/tfm_ssh.py`
- **SFTP Feature**: `doc/SFTP_SUPPORT_FEATURE.md`
