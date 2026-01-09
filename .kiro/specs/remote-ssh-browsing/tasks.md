# Implementation Plan: Remote SSH Browsing

## Overview

This implementation plan breaks down the remote SSH browsing feature into discrete, incremental coding tasks. Each task builds on previous work, with checkpoints to ensure quality and correctness. The implementation follows TFM's Path polymorphism architecture and integrates seamlessly with existing components.

## Tasks

- [ ] 1. Create SSH configuration parser
  - Implement SSHConfigParser class in new file `src/tfm_ssh_config.py`
  - Parse ~/.ssh/config file to extract Host entries
  - Support Include directives for additional config files
  - Exclude wildcard Host entries (Host *)
  - Return dictionary mapping hostname to configuration
  - Handle missing config file gracefully (return empty dict)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [ ]* 1.1 Write property test for SSH config parsing
  - **Property 1: SSH Config Parsing Completeness**
  - **Validates: Requirements 1.2, 1.3**

- [ ]* 1.2 Write unit tests for SSH config parser
  - Test parsing valid config with single host
  - Test parsing config with multiple hosts
  - Test Include directive handling
  - Test wildcard host exclusion
  - Test missing config file handling
  - Test malformed config entry handling
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [ ] 2. Implement SSH connection management
  - Create SSHConnection class in `src/tfm_ssh_connection.py`
  - Implement connection establishment using subprocess and sftp command
  - Implement connection state tracking (connected/disconnected)
  - Implement SFTP batch command execution
  - Add connection timeout handling
  - Add error handling for authentication failures
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 7.1, 8.1_

- [ ]* 2.1 Write unit tests for SSH connection
  - Test connection state management
  - Test SFTP command batching
  - Test error handling for failed commands
  - Test authentication failure handling
  - _Requirements: 3.3, 3.4, 8.1_

- [ ] 3. Implement SSH connection manager
  - Create SSHConnectionManager singleton class in `src/tfm_ssh_connection.py`
  - Implement connection pooling (hostname -> SSHConnection mapping)
  - Implement connection reuse for same hostname
  - Implement idle connection timeout (5 minutes default)
  - Implement cleanup of idle connections
  - Implement close_all() for application shutdown
  - Add thread-safe access with locks
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 3.1 Write property test for connection reuse
  - **Property 3: Connection Reuse**
  - **Validates: Requirements 7.5**

- [ ]* 3.2 Write property test for connection cleanup
  - **Property 10: Connection Cleanup**
  - **Validates: Requirements 7.4**

- [ ]* 3.3 Write unit tests for connection manager
  - Test connection pooling
  - Test connection reuse
  - Test idle timeout
  - Test cleanup on shutdown
  - Test thread safety
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement SSH file operations
  - Add list_directory() method to SSHConnection
  - Add stat() method to SSHConnection for file metadata
  - Add read_file() method to SSHConnection
  - Add write_file() method to SSHConnection
  - Add delete_file() and delete_directory() methods
  - Add create_directory() method
  - Add rename() method for move operations
  - Parse SFTP output to extract file metadata (size, mtime, permissions)
  - _Requirements: 5.1, 5.2, 6.1, 6.2, 6.3, 9.1, 9.2, 9.4, 9.5, 9.6, 9.7_

- [ ]* 5.1 Write property test for directory listing
  - **Property 4: Directory Listing Completeness**
  - **Validates: Requirements 5.1**

- [ ]* 5.2 Write property test for metadata consistency
  - **Property 5: Metadata Consistency**
  - **Validates: Requirements 6.1, 6.2, 6.3**

- [ ]* 5.3 Write unit tests for file operations
  - Test directory listing
  - Test file stat
  - Test file reading
  - Test file writing
  - Test file deletion
  - Test directory creation
  - Test rename operation
  - _Requirements: 5.1, 6.1, 6.2, 6.3, 9.1, 9.2, 9.4, 9.5, 9.6, 9.7_

- [ ] 6. Implement SSHPathImpl class
  - Create SSHPathImpl class in `src/tfm_ssh.py`
  - Implement PathImpl interface methods
  - Parse SSH URI format (ssh://hostname/path/to/file)
  - Delegate operations to SSHConnection via SSHConnectionManager
  - Implement path manipulation methods (parent, joinpath, etc.)
  - Implement file query methods (exists, is_dir, is_file, etc.)
  - Implement file I/O methods (open, read_text, write_text, etc.)
  - Implement directory operations (iterdir, mkdir, rmdir, etc.)
  - Implement file modification methods (unlink, rename, touch, chmod)
  - Set is_remote() to return True
  - Set get_scheme() to return 'ssh'
  - Implement as_uri() to return ssh:// URI
  - Set supports_directory_rename() to return True
  - Set supports_file_editing() to return False (no external editor support)
  - Set supports_write_operations() to return True
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ]* 6.1 Write property test for URI round-trip
  - **Property 2: URI Round-Trip Consistency**
  - **Validates: Requirements 4.5**

- [ ]* 6.2 Write property test for path polymorphism
  - **Property 9: Path Polymorphism Transparency**
  - **Validates: Requirements 10.3, 10.4**

- [ ]* 6.3 Write unit tests for SSHPathImpl
  - Test URI parsing
  - Test path manipulation methods
  - Test file query methods
  - Test storage-specific methods
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 7. Implement display and metadata methods for SSHPathImpl
  - Implement get_display_prefix() to return "SSH: "
  - Implement get_display_title() to return full ssh:// URI
  - Implement requires_extraction_for_reading() to return True
  - Implement supports_streaming_read() to return False
  - Implement get_search_strategy() to return 'buffered'
  - Implement should_cache_for_search() to return True
  - Implement get_extended_metadata() to return SSH-specific metadata
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ]* 7.1 Write unit tests for display methods
  - Test display prefix and title
  - Test content reading strategy methods
  - Test extended metadata
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Extend Path factory to recognize ssh:// URIs
  - Modify Path._create_implementation() in `src/tfm_path.py`
  - Add detection for ssh:// scheme
  - Import and instantiate SSHPathImpl for ssh:// URIs
  - Handle ImportError gracefully with clear error message
  - _Requirements: 10.1, 10.2_

- [ ]* 9.1 Write unit tests for Path factory
  - Test ssh:// URI detection
  - Test SSHPathImpl instantiation
  - Test error handling for missing SSH support
  - _Requirements: 10.1, 10.2_

- [ ] 10. Extend DriveEntry to support SSH hosts
  - Modify DriveEntry class in `src/tfm_drives_dialog.py`
  - Add 'ssh' as valid drive_type
  - Update get_display_text() to handle SSH entries
  - Use 🖥️ emoji icon for SSH hosts
  - Format display as "ssh://hostname"
  - _Requirements: 2.4_

- [ ]* 10.1 Write unit tests for DriveEntry SSH support
  - Test SSH drive entry creation
  - Test display text formatting
  - _Requirements: 2.4_

- [ ] 11. Extend DrivesDialog to load SSH hosts
  - Add _load_ssh_hosts() method to DrivesDialog in `src/tfm_drives_dialog.py`
  - Use SSHConfigParser to load hosts from ~/.ssh/config
  - Create DriveEntry for each host with type='ssh'
  - Format display name as "user@hostname" when user is specified
  - Call _load_ssh_hosts() in show() method after loading local drives
  - Handle errors gracefully (log warning, continue without SSH hosts)
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [ ]* 11.1 Write unit tests for SSH host loading
  - Test SSH host loading from config
  - Test display name formatting
  - Test error handling
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [ ] 12. Implement cross-storage copy operations
  - Implement _copy_file_cross_storage() in Path class (`src/tfm_path.py`)
  - Handle local → remote transfers (read local, write remote)
  - Handle remote → local transfers (read remote, write local)
  - Handle remote → remote transfers (read source, write destination)
  - Create destination directories as needed (for local destinations)
  - _Requirements: 11.1, 11.2, 11.3_

- [ ]* 12.1 Write property test for cross-storage copy
  - **Property 6: Cross-Storage Copy Preservation**
  - **Validates: Requirements 11.1, 11.2, 11.3**

- [ ]* 12.2 Write unit tests for cross-storage copy
  - Test local → remote copy
  - Test remote → local copy
  - Test remote → remote copy
  - Test directory creation
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 13. Implement cross-storage move operations
  - Implement move_to() in Path class (`src/tfm_path.py`)
  - Use native rename for same-storage moves
  - Use copy + delete for cross-storage moves
  - Handle directory moves recursively
  - Preserve source file on failure
  - _Requirements: 11.4, 11.5_

- [ ]* 13.1 Write property test for move atomicity
  - **Property 7: Move Operation Atomicity**
  - **Validates: Requirements 11.4**

- [ ]* 13.2 Write property test for error recovery
  - **Property 8: Error Recovery Safety**
  - **Validates: Requirements 11.5**

- [ ]* 13.3 Write unit tests for cross-storage move
  - Test same-storage move
  - Test cross-storage move
  - Test directory move
  - Test error handling
  - _Requirements: 11.4, 11.5_

- [ ] 14. Implement recursive directory copy
  - Implement _copy_directory_cross_storage() in Path class
  - Create destination directory
  - Recursively copy all contents
  - Handle nested directories
  - _Requirements: 11.6_

- [ ]* 14.1 Write unit tests for directory copy
  - Test recursive directory copy
  - Test nested directories
  - Test mixed files and directories
  - _Requirements: 11.6_

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Add progress display for large transfers
  - Extend SSHConnection to track transfer progress
  - Emit progress events during file transfers
  - Integrate with existing progress display system
  - Show progress for files larger than 1MB
  - _Requirements: 11.7_

- [ ]* 16.1 Write unit tests for progress display
  - Test progress tracking
  - Test progress events
  - Test threshold behavior
  - _Requirements: 11.7_

- [ ] 17. Implement error handling for SSH operations
  - Add specific exception types for SSH errors
  - Handle authentication failures with clear messages
  - Handle connection timeouts with retry logic
  - Handle path not found errors
  - Handle permission denied errors
  - Add detailed logging for all errors
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 17.1 Write unit tests for error handling
  - Test authentication failure handling
  - Test connection timeout handling
  - Test path not found handling
  - Test permission denied handling
  - Test error logging
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 18. Add connection lifecycle management
  - Implement automatic reconnection on connection loss
  - Add connection health checks
  - Implement graceful connection shutdown
  - Add connection cleanup on application exit
  - Register cleanup handler with application lifecycle
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 18.1 Write unit tests for connection lifecycle
  - Test automatic reconnection
  - Test health checks
  - Test graceful shutdown
  - Test cleanup on exit
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 19. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 20. Integration and wiring
  - Verify SSH hosts appear in Drives Dialog
  - Verify navigation to SSH hosts works
  - Verify file browsing on remote systems
  - Verify file viewing on remote systems
  - Verify file operations (copy, move, delete) work
  - Verify cross-storage operations work
  - Verify error messages are clear and helpful
  - Test with real SSH servers
  - _Requirements: All_

- [ ]* 20.1 Write integration tests
  - Test end-to-end browsing workflow
  - Test end-to-end file viewing workflow
  - Test end-to-end copy workflow
  - Test end-to-end move workflow
  - Test error handling workflows
  - _Requirements: All_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end workflows
- The implementation uses only Python standard library and standard SSH/SFTP commands
- No third-party libraries are required beyond what TFM already uses
