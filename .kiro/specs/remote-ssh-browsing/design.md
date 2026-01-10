# Design Document: Remote SSH Browsing

## Overview

This design document describes the implementation of remote file browsing capabilities for TFM using SSH-based protocols. The feature will integrate seamlessly with TFM's existing Path polymorphism architecture, allowing users to browse, view, and manipulate files on remote systems through SSH connections.

The implementation will use SFTP (SSH File Transfer Protocol) as the backend protocol, accessed through the standard `sftp` command-line tool. Remote servers will be discovered from the user's `~/.ssh/config` file and presented in the Drives Dialog alongside local drives and S3 buckets.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      TFM Application                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ File Manager │    │ Text Viewer  │    │ Drives Dialog│ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘ │
│         │                   │                    │          │
│         └───────────────────┴────────────────────┘          │
│                             │                                │
│                    ┌────────▼────────┐                      │
│                    │   Path (Facade) │                      │
│                    └────────┬────────┘                      │
│                             │                                │
│         ┌───────────────────┼───────────────────┐          │
│         │                   │                   │          │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐   │
│  │LocalPathImpl│    │ S3PathImpl  │    │SSHPathImpl  │   │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘   │
│                             │                   │          │
└─────────────────────────────┼───────────────────┼──────────┘
                              │                   │
                     ┌────────▼────────┐ ┌────────▼────────┐
                     │   AWS S3 API    │ │  SFTP Command   │
                     └─────────────────┘ └─────────────────┘
```

### Component Responsibilities

1. **SSHPathImpl**: Implements the PathImpl interface for remote SSH paths
2. **SSHConnectionManager**: Manages persistent SSH/SFTP connections
3. **SSHConfigParser**: Parses ~/.ssh/config to discover remote servers
4. **DrivesDialog**: Extended to list remote servers from SSH config
5. **Path Factory**: Extended to recognize ssh:// URIs and create SSHPathImpl instances

## Components and Interfaces

### SSHPathImpl

Implements the `PathImpl` abstract base class for remote SSH paths.

```python
class SSHPathImpl(PathImpl):
    """
    SSH/SFTP implementation of PathImpl.
    
    Represents paths on remote systems accessible via SSH/SFTP.
    URI format: ssh://hostname/path/to/file
    """
    
    def __init__(self, uri: str):
        """
        Initialize SSH path from URI.
        
        Args:
            uri: SSH URI in format ssh://hostname/path/to/file
        
        Raises:
            ValueError: If URI format is invalid
        """
        
    def _parse_uri(self, uri: str) -> tuple:
        """
        Parse SSH URI into components.
        
        Returns:
            (hostname, remote_path) tuple
        """
        
    def _get_connection(self) -> 'SSHConnection':
        """
        Get or create SSH connection for this host.
        
        Returns:
            SSHConnection instance for the hostname
        """
        
    # PathImpl interface methods...
    # All methods delegate to SSHConnection for actual operations
```

### SSHConnection

Manages a single SSH/SFTP connection to a remote host.

```python
class SSHConnection:
    """
    Manages an SSH/SFTP connection to a remote host.
    
    Provides methods for file operations over SFTP using subprocess
    to invoke the sftp command-line tool.
    """
    
    def __init__(self, hostname: str, config: dict):
        """
        Initialize SSH connection.
        
        Args:
            hostname: Remote hostname
            config: SSH configuration from ~/.ssh/config
        """
        
    def connect(self) -> bool:
        """
        Establish SSH connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        
    def disconnect(self):
        """Close the SSH connection."""
        
    def is_connected(self) -> bool:
        """Check if connection is active."""
        
    def list_directory(self, remote_path: str) -> list:
        """
        List directory contents.
        
        Args:
            remote_path: Remote directory path
            
        Returns:
            List of file/directory entries with metadata
        """
        
    def stat(self, remote_path: str) -> dict:
        """
        Get file/directory metadata.
        
        Args:
            remote_path: Remote file/directory path
            
        Returns:
            Dictionary with stat information
        """
        
    def read_file(self, remote_path: str) -> bytes:
        """
        Read file contents.
        
        Args:
            remote_path: Remote file path
            
        Returns:
            File contents as bytes
        """
        
    def write_file(self, remote_path: str, data: bytes):
        """
        Write file contents.
        
        Args:
            remote_path: Remote file path
            data: File contents as bytes
        """
        
    def delete_file(self, remote_path: str):
        """Delete a file."""
        
    def delete_directory(self, remote_path: str):
        """Delete a directory (must be empty)."""
        
    def create_directory(self, remote_path: str):
        """Create a directory."""
        
    def rename(self, old_path: str, new_path: str):
        """Rename/move a file or directory."""
        
    def _execute_sftp_command(self, commands: list) -> tuple:
        """
        Execute SFTP batch commands.
        
        Args:
            commands: List of SFTP commands to execute
            
        Returns:
            (stdout, stderr, returncode) tuple
        """
```

### SSHConnectionManager

Manages the pool of SSH connections.

```python
class SSHConnectionManager:
    """
    Manages SSH connections with connection pooling and lifecycle management.
    
    Singleton pattern ensures only one manager exists per application instance.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'SSHConnectionManager':
        """Get the singleton instance."""
        
    def __init__(self):
        """Initialize connection manager."""
        self._connections = {}  # hostname -> SSHConnection
        self._lock = threading.Lock()
        self._last_used = {}  # hostname -> timestamp
        self._timeout = 300  # 5 minutes idle timeout
        
    def get_connection(self, hostname: str, config: dict) -> SSHConnection:
        """
        Get or create connection for hostname.
        
        Args:
            hostname: Remote hostname
            config: SSH configuration
            
        Returns:
            SSHConnection instance
        """
        
    def close_connection(self, hostname: str):
        """Close connection for hostname."""
        
    def close_all(self):
        """Close all connections."""
        
    def cleanup_idle_connections(self):
        """Close connections that have been idle beyond timeout."""
```

### SSHConfigParser

Parses SSH configuration files.

```python
class SSHConfigParser:
    """
    Parses SSH configuration files to discover remote servers.
    
    Supports:
    - Host entries with connection parameters
    - Include directives for additional config files
    - Wildcard exclusion (Host * entries are ignored)
    """
    
    def __init__(self, config_path: str = "~/.ssh/config"):
        """
        Initialize parser.
        
        Args:
            config_path: Path to SSH config file
        """
        
    def parse(self) -> dict:
        """
        Parse SSH config file.
        
        Returns:
            Dictionary mapping hostname to configuration dict
            {
                'hostname': {
                    'HostName': 'actual.host.com',
                    'User': 'username',
                    'Port': 22,
                    'IdentityFile': '/path/to/key',
                    ...
                }
            }
        """
        
    def _parse_file(self, file_path: str, hosts: dict):
        """
        Parse a single config file.
        
        Args:
            file_path: Path to config file
            hosts: Dictionary to populate with host entries
        """
        
    def _is_wildcard_host(self, host_pattern: str) -> bool:
        """
        Check if host pattern is a wildcard.
        
        Args:
            host_pattern: Host pattern from config
            
        Returns:
            True if pattern contains wildcards
        """
```

### DriveEntry Extension

Extend the existing `DriveEntry` class to support SSH hosts.

```python
# In tfm_drives_dialog.py

class DriveEntry:
    """Represents a drive/storage entry in the drives dialog"""
    
    def __init__(self, name, path, drive_type, description=None):
        self.name = name
        self.path = path
        self.drive_type = drive_type  # 'local', 's3', 'ssh'  # <-- Add 'ssh'
        self.description = description or ""
    
    def get_display_text(self):
        """Get formatted display text for this drive entry"""
        if self.drive_type == 'local':
            icon = "🏠" if "Home" in self.name else "📁"
            display_name = self.name
        elif self.drive_type == 's3':
            icon = "☁️ "
            display_name = f"s3://{self.name}" if self.path else self.name
        elif self.drive_type == 'ssh':  # <-- Add SSH support
            icon = "🖥️ "
            display_name = f"ssh://{self.name}"
        else:
            icon = "💾"
            display_name = self.name
        
        if self.description:
            return f"{icon} {display_name} - {self.description}"
        else:
            return f"{icon} {display_name}"
```

### DrivesDialog Extension

Extend `DrivesDialog` to load SSH hosts from config.

```python
# In tfm_drives_dialog.py

class DrivesDialog(UILayer, BaseListDialog):
    """Drives dialog component for storage/drive selection"""
    
    def _load_ssh_hosts(self):
        """Load SSH hosts from ~/.ssh/config"""
        ssh_drives = []
        
        try:
            parser = SSHConfigParser()
            hosts = parser.parse()
            
            for hostname, config in hosts.items():
                # Get display name (use User@HostName if available)
                user = config.get('User', '')
                actual_host = config.get('HostName', hostname)
                
                if user:
                    display_name = f"{user}@{actual_host}"
                else:
                    display_name = actual_host
                
                ssh_drives.append(DriveEntry(
                    name=hostname,
                    path=f"ssh://{hostname}/",
                    drive_type="ssh",
                    description=display_name if display_name != hostname else None
                ))
                
        except Exception as e:
            # Log error but don't fail
            self.logger.warning(f"Failed to load SSH hosts: {e}")
        
        # Update drives list
        with self.s3_lock:
            self.drives.extend(ssh_drives)
            self._filter_drives_internal()
            self.content_changed = True
    
    def show(self, callback=None):
        """Show the drives dialog and start loading available drives"""
        # ... existing code ...
        
        # Load local drives immediately
        self._load_local_drives()
        
        # Load SSH hosts immediately (synchronous, should be fast)
        self._load_ssh_hosts()  # <-- Add this
        
        # Start S3 bucket loading in background
        self._start_s3_bucket_scan()
```

### Path Factory Extension

Extend the `Path._create_implementation()` method to recognize ssh:// URIs.

```python
# In tfm_path.py

class Path:
    def _create_implementation(self, path_str: str) -> PathImpl:
        """Create the appropriate implementation based on the path string"""
        # Detect archive URIs
        if path_str.startswith('archive://'):
            # ... existing code ...
        
        # Detect S3 URIs
        if path_str.startswith('s3://'):
            # ... existing code ...
        
        # Detect SSH URIs  # <-- Add this
        if path_str.startswith('ssh://'):
            try:
                try:
                    from .tfm_ssh import SSHPathImpl
                except ImportError:
                    from tfm_ssh import SSHPathImpl
                return SSHPathImpl(path_str)
            except ImportError as e:
                raise ImportError(f"SSH support not available: {e}")
        
        # Default to local file system
        return LocalPathImpl(PathlibPath(path_str))
```

## Data Models

### SSH URI Format

```
ssh://hostname/path/to/file
```

Components:
- **Scheme**: `ssh://`
- **Hostname**: The Host entry name from ~/.ssh/config
- **Path**: Absolute path on the remote system

Examples:
- `ssh://myserver/home/user/documents/file.txt`
- `ssh://prod-web-01/var/log/nginx/access.log`
- `ssh://dev-box/tmp/`

### SSH Configuration Structure

Parsed from ~/.ssh/config:

```python
{
    'myserver': {
        'HostName': 'actual.server.com',
        'User': 'myusername',
        'Port': 22,
        'IdentityFile': '~/.ssh/id_rsa',
        'ForwardAgent': 'yes',
        # ... other SSH options ...
    },
    'prod-web-01': {
        'HostName': '192.168.1.100',
        'User': 'deploy',
        'Port': 2222,
        'IdentityFile': '~/.ssh/prod_key',
    }
}
```

### File Metadata Structure

Returned by `SSHConnection.stat()`:

```python
{
    'name': 'filename.txt',
    'size': 1024,
    'mtime': 1704067200.0,  # Unix timestamp
    'mode': 0o644,  # File permissions
    'is_dir': False,
    'is_file': True,
    'is_symlink': False,
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: SSH Config Parsing Completeness

*For any* valid SSH config file, parsing should extract all non-wildcard Host entries with their complete configuration parameters.

**Validates: Requirements 1.2, 1.3**

### Property 2: URI Round-Trip Consistency

*For any* valid SSH path, converting to URI string and back to SSHPathImpl should produce an equivalent path.

**Validates: Requirements 4.5**

### Property 3: Connection Reuse

*For any* sequence of operations on the same hostname, the connection manager should reuse the existing connection rather than creating new ones.

**Validates: Requirements 7.5**

### Property 4: Directory Listing Completeness

*For any* accessible remote directory, listing should return all files and subdirectories without omissions.

**Validates: Requirements 5.1**

### Property 5: Metadata Consistency

*For any* remote file, the metadata returned by stat() should match the actual file properties on the remote system.

**Validates: Requirements 6.1, 6.2, 6.3**

### Property 6: Cross-Storage Copy Preservation

*For any* file copied between storage types (local ↔ remote, remote ↔ remote), the destination file should have identical content to the source file.

**Validates: Requirements 11.1, 11.2, 11.3**

### Property 7: Move Operation Atomicity

*For any* successful move operation, the source file should no longer exist and the destination file should exist with the same content.

**Validates: Requirements 11.4**

### Property 8: Error Recovery Safety

*For any* failed cross-storage operation, the source file should remain unchanged and accessible.

**Validates: Requirements 11.5**

### Property 9: Path Polymorphism Transparency

*For any* operation supported by the Path interface, switching between local and remote paths should not require code changes in calling components.

**Validates: Requirements 10.3, 10.4**

### Property 10: Connection Cleanup

*For any* application exit, all active SSH connections should be properly closed.

**Validates: Requirements 7.4**

## Error Handling

### Connection Errors

**Authentication Failure**:
- **Detection**: SSH key authentication fails
- **Handling**: Display clear error message indicating authentication failure
- **User Action**: Check SSH keys and permissions
- **Logging**: Log detailed error for debugging

**Connection Timeout**:
- **Detection**: Remote host unreachable or not responding
- **Handling**: Display timeout error with hostname
- **User Action**: Check network connectivity and host availability
- **Logging**: Log connection attempt details

**Connection Lost**:
- **Detection**: Existing connection drops during operation
- **Handling**: Attempt automatic reconnection once
- **User Action**: If reconnection fails, user must retry operation
- **Logging**: Log connection loss and reconnection attempts

### File Operation Errors

**Path Not Found**:
- **Detection**: Remote path does not exist
- **Handling**: Display "path not found" error
- **User Action**: Verify path exists on remote system
- **Logging**: Log attempted path

**Permission Denied**:
- **Detection**: Insufficient permissions for operation
- **Handling**: Display permission error with operation type
- **User Action**: Check file permissions on remote system
- **Logging**: Log permission error details

**Disk Full**:
- **Detection**: Write operation fails due to insufficient space
- **Handling**: Display disk full error
- **User Action**: Free space on remote system
- **Logging**: Log disk space error

### Configuration Errors

**Invalid SSH Config**:
- **Detection**: Malformed ~/.ssh/config file
- **Handling**: Log warning, skip invalid entries, continue with valid ones
- **User Action**: Fix SSH config syntax
- **Logging**: Log parsing errors with line numbers

**Missing SSH Config**:
- **Detection**: ~/.ssh/config does not exist
- **Handling**: Continue without error (no remote servers listed)
- **User Action**: None required
- **Logging**: Log info message

### Cross-Storage Operation Errors

**Partial Transfer Failure**:
- **Detection**: Copy operation fails mid-transfer
- **Handling**: Preserve source file, clean up partial destination
- **User Action**: Retry operation
- **Logging**: Log transfer progress and failure point

**Incompatible Operation**:
- **Detection**: Operation not supported between storage types
- **Handling**: Display clear error message
- **User Action**: Use alternative approach
- **Logging**: Log attempted operation

## Testing Strategy

### Unit Testing

Unit tests will verify specific examples, edge cases, and error conditions:

**SSHConfigParser Tests**:
- Parse valid config with single host
- Parse config with multiple hosts
- Parse config with Include directives
- Exclude wildcard hosts (Host *)
- Handle missing config file gracefully
- Handle malformed config entries

**SSHPathImpl Tests**:
- Parse valid SSH URIs
- Reject invalid URI formats
- Handle special characters in paths
- Path manipulation (parent, joinpath, etc.)

**SSHConnection Tests**:
- Mock SFTP command execution
- Test command batching
- Test error handling for failed commands
- Test connection state management

**DrivesDialog Tests**:
- Display SSH hosts alongside local and S3
- Filter SSH hosts by search text
- Handle SSH config loading errors

### Property-Based Testing

Property-based tests will verify universal properties across all inputs. Each test will run a minimum of 100 iterations.

**Property Test 1: SSH Config Parsing Completeness**
- **Property**: For any valid SSH config file, parsing should extract all non-wildcard Host entries
- **Generator**: Generate random SSH config files with varying numbers of hosts
- **Assertion**: Verify all non-wildcard hosts are extracted
- **Tag**: Feature: remote-ssh-browsing, Property 1: SSH Config Parsing Completeness

**Property Test 2: URI Round-Trip Consistency**
- **Property**: For any valid SSH path, URI conversion should be reversible
- **Generator**: Generate random hostnames and paths
- **Assertion**: SSHPathImpl(uri).as_uri() == uri
- **Tag**: Feature: remote-ssh-browsing, Property 2: URI Round-Trip Consistency

**Property Test 3: Connection Reuse**
- **Property**: For any sequence of operations on same hostname, connection should be reused
- **Generator**: Generate random sequences of operations on same host
- **Assertion**: Verify connection count remains 1
- **Tag**: Feature: remote-ssh-browsing, Property 3: Connection Reuse

**Property Test 4: Directory Listing Completeness**
- **Property**: For any directory, listing should return all entries
- **Generator**: Create temporary directories with random files
- **Assertion**: Verify all files are listed
- **Tag**: Feature: remote-ssh-browsing, Property 4: Directory Listing Completeness

**Property Test 5: Metadata Consistency**
- **Property**: For any file, stat() should return accurate metadata
- **Generator**: Create files with random sizes and permissions
- **Assertion**: Verify metadata matches actual file properties
- **Tag**: Feature: remote-ssh-browsing, Property 5: Metadata Consistency

**Property Test 6: Cross-Storage Copy Preservation**
- **Property**: For any file copied between storage types, content should be identical
- **Generator**: Generate random file contents and storage type pairs
- **Assertion**: Verify source and destination content match
- **Tag**: Feature: remote-ssh-browsing, Property 6: Cross-Storage Copy Preservation

**Property Test 7: Move Operation Atomicity**
- **Property**: For any successful move, source should not exist and destination should exist
- **Generator**: Generate random files and move destinations
- **Assertion**: Verify source deleted and destination exists with same content
- **Tag**: Feature: remote-ssh-browsing, Property 7: Move Operation Atomicity

**Property Test 8: Error Recovery Safety**
- **Property**: For any failed operation, source should remain unchanged
- **Generator**: Generate operations that will fail (invalid destinations, etc.)
- **Assertion**: Verify source file unchanged after failure
- **Tag**: Feature: remote-ssh-browsing, Property 8: Error Recovery Safety

**Property Test 9: Path Polymorphism Transparency**
- **Property**: For any Path operation, local and remote paths should behave consistently
- **Generator**: Generate random paths (local and remote) and operations
- **Assertion**: Verify operations work identically regardless of storage type
- **Tag**: Feature: remote-ssh-browsing, Property 9: Path Polymorphism Transparency

**Property Test 10: Connection Cleanup**
- **Property**: For any application exit, all connections should be closed
- **Generator**: Create random numbers of connections
- **Assertion**: Verify all connections closed after cleanup
- **Tag**: Feature: remote-ssh-browsing, Property 10: Connection Cleanup

### Integration Testing

Integration tests will verify end-to-end workflows:

- Browse remote directory through Drives Dialog
- View remote file in text viewer
- Copy file from local to remote
- Copy file from remote to local
- Move file between remote hosts
- Delete remote file
- Create remote directory
- Handle connection failures gracefully

### Manual Testing

Manual testing scenarios:

- Test with various SSH configurations (different ports, users, keys)
- Test with slow/unreliable network connections
- Test with large files (progress display)
- Test with many files (performance)
- Test with special characters in filenames
- Test with symlinks on remote system
