# Requirements Document

## Introduction

This document specifies requirements for remote file browsing capabilities in TFM using SSH-based protocols. The feature will leverage TFM's existing Path polymorphism architecture to provide seamless browsing of remote filesystems through SSH connections, with configuration discovery from the user's SSH config file.

## Glossary

- **Remote_Browser**: The system component that enables browsing remote filesystems
- **SSH_Config_Parser**: Component that reads and parses ~/.ssh/config
- **Remote_Path**: A Path implementation for remote filesystem access via SSH
- **Drives_Dialog**: The existing dialog (D key) that lists available storage locations
- **SFTP_Backend**: The underlying protocol implementation using SFTP over SSH
- **Host_Entry**: A remote server configuration from SSH config
- **TFM**: Terminal File Manager application

## Requirements

### Requirement 1: SSH Configuration Discovery

**User Story:** As a user, I want TFM to automatically discover my configured SSH servers from ~/.ssh/config, so that I can quickly access remote systems I've already set up.

#### Acceptance Criteria

1. WHEN TFM starts, THE SSH_Config_Parser SHALL read the ~/.ssh/config file if it exists
2. WHEN parsing the SSH config, THE SSH_Config_Parser SHALL extract Host entries with their connection parameters
3. WHEN a Host entry uses wildcards or patterns, THE SSH_Config_Parser SHALL exclude it from the remote server list
4. WHEN SSH config contains Include directives, THE SSH_Config_Parser SHALL recursively parse included files
5. WHEN the SSH config file does not exist, THE Remote_Browser SHALL continue without error
6. WHEN parsing fails for a specific Host entry, THE SSH_Config_Parser SHALL log a warning and continue with remaining entries

### Requirement 2: Remote Server Listing in Drives Dialog

**User Story:** As a user, I want to see my remote SSH servers listed in the Drives Dialog, so that I can select and browse them like local drives.

#### Acceptance Criteria

1. WHEN the Drives_Dialog is opened, THE Remote_Browser SHALL provide a list of available remote servers
2. WHEN displaying remote servers, THE Drives_Dialog SHALL show the Host name and connection details
3. WHEN a user selects a remote server, THE Drives_Dialog SHALL initiate a connection to that server
4. WHEN remote servers are listed, THE Drives_Dialog SHALL visually distinguish them from local drives
5. WHEN no remote servers are configured, THE Drives_Dialog SHALL display only local drives

### Requirement 3: SFTP Protocol Implementation

**User Story:** As a developer, I want to use SFTP as the backend protocol, so that the implementation provides reliable file operations and uses only standard tools.

#### Acceptance Criteria

1. THE SFTP_Backend SHALL use the sftp command-line tool for all remote operations
2. THE SFTP_Backend SHALL NOT use third-party Python libraries
3. WHEN establishing a connection, THE SFTP_Backend SHALL use SSH key-based authentication
4. WHEN SSH key authentication fails, THE SFTP_Backend SHALL return an appropriate error
5. THE SFTP_Backend SHALL reuse SSH connections when possible to minimize overhead

### Requirement 4: Remote Path Implementation

**User Story:** As a developer, I want Remote_Path to implement the existing Path interface, so that remote files integrate seamlessly with TFM's architecture.

#### Acceptance Criteria

1. THE Remote_Path SHALL implement all methods required by TFM's Path protocol
2. WHEN listing directory contents, THE Remote_Path SHALL return file metadata including name, size, and modification time
3. WHEN accessing file properties, THE Remote_Path SHALL retrieve them via SFTP
4. WHEN a remote operation fails, THE Remote_Path SHALL raise appropriate exceptions consistent with local Path behavior
5. THE Remote_Path SHALL represent remote paths in the format "ssh://hostname/path/to/file"

### Requirement 5: Directory Browsing Operations

**User Story:** As a user, I want to browse remote directories, so that I can navigate remote filesystems like local ones.

#### Acceptance Criteria

1. WHEN entering a remote directory, THE Remote_Browser SHALL list all files and subdirectories
2. WHEN navigating to parent directories, THE Remote_Browser SHALL update the view accordingly
3. WHEN a directory is inaccessible, THE Remote_Browser SHALL display an error message
4. WHEN listing large directories, THE Remote_Browser SHALL provide feedback during the operation
5. THE Remote_Browser SHALL cache directory listings to improve performance

### Requirement 6: File Metadata Display

**User Story:** As a user, I want to see file metadata for remote files, so that I can make informed decisions about file operations.

#### Acceptance Criteria

1. WHEN displaying remote files, THE Remote_Browser SHALL show file size
2. WHEN displaying remote files, THE Remote_Browser SHALL show modification date and time
3. WHEN displaying remote files, THE Remote_Browser SHALL show file permissions
4. WHEN metadata is unavailable, THE Remote_Browser SHALL display placeholder values
5. THE Remote_Browser SHALL format metadata consistently with local file display

### Requirement 7: Connection Management

**User Story:** As a user, I want TFM to manage SSH connections efficiently, so that remote browsing is responsive and doesn't create excessive connections.

#### Acceptance Criteria

1. WHEN connecting to a remote server, THE Remote_Browser SHALL establish a persistent SSH connection
2. WHEN a connection is idle, THE Remote_Browser SHALL keep it alive for a configurable timeout period
3. WHEN a connection fails, THE Remote_Browser SHALL attempt to reconnect automatically
4. WHEN TFM exits, THE Remote_Browser SHALL close all active SSH connections
5. WHEN multiple operations target the same host, THE Remote_Browser SHALL reuse the existing connection

### Requirement 8: Error Handling

**User Story:** As a user, I want clear error messages when remote operations fail, so that I can understand and resolve connection issues.

#### Acceptance Criteria

1. WHEN SSH key authentication fails, THE Remote_Browser SHALL display a message indicating authentication failure
2. WHEN a remote host is unreachable, THE Remote_Browser SHALL display a connection timeout message
3. WHEN a remote path does not exist, THE Remote_Browser SHALL display a "path not found" error
4. WHEN permission is denied, THE Remote_Browser SHALL display a permission error message
5. THE Remote_Browser SHALL log detailed error information for debugging purposes

### Requirement 9: File Operations Support

**User Story:** As a user, I want to perform file operations on remote files, so that I can manage remote filesystems effectively.

#### Acceptance Criteria

1. THE Remote_Browser SHALL support directory listing operations
2. THE Remote_Browser SHALL support file viewing operations
3. THE Remote_Browser SHALL support navigation operations (cd, parent directory)
4. THE Remote_Browser SHALL support file copy operations
5. THE Remote_Browser SHALL support file move operations
6. THE Remote_Browser SHALL support file delete operations
7. THE Remote_Browser SHALL support directory creation operations

### Requirement 10: Path Polymorphism Integration

**User Story:** As a developer, I want Remote_Path to integrate with TFM's existing Path polymorphism, so that minimal changes are needed to existing code.

#### Acceptance Criteria

1. WHEN TFM encounters a path starting with "ssh://", THE system SHALL create a Remote_Path instance
2. WHEN file operations are performed, THE system SHALL dispatch to the appropriate Path implementation
3. WHEN switching between local and remote paths, THE system SHALL handle the transition transparently
4. THE Remote_Path SHALL be compatible with existing TFM components that use the Path interface
5. THE system SHALL detect and handle mixed operations between local and remote paths appropriately

### Requirement 11: Cross-Storage File Operations

**User Story:** As a user, I want to copy and move files between different storage types (local to remote, remote to local, remote to remote), so that I can transfer files flexibly across systems.

#### Acceptance Criteria

1. WHEN copying from local to remote, THE Remote_Browser SHALL transfer the file using SFTP put operations
2. WHEN copying from remote to local, THE Remote_Browser SHALL transfer the file using SFTP get operations
3. WHEN copying between two remote hosts, THE Remote_Browser SHALL route the transfer through the local system
4. WHEN moving files across storage types, THE Remote_Browser SHALL copy then delete the source file
5. WHEN a cross-storage operation fails, THE Remote_Browser SHALL preserve the source file and report the error
6. WHEN copying directories across storage types, THE Remote_Browser SHALL recursively copy all contents
7. THE Remote_Browser SHALL display progress for large file transfers across storage types
