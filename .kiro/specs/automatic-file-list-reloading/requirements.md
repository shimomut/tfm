# Requirements Document

## Introduction

This document specifies requirements for automatic file list reloading in TFM (Terminal File Manager). Currently, TFM only reloads the file list after user-initiated actions. This feature will enable TFM to automatically detect and reflect changes made by external applications, ensuring the displayed file list remains synchronized with the actual filesystem state.

## Glossary

- **TFM**: Terminal File Manager - the application being enhanced
- **File_List**: The displayed list of files and directories in the current view
- **External_Change**: A filesystem modification (create, delete, modify, rename) performed by a process other than TFM
- **File_Monitor**: The component responsible for detecting filesystem changes
- **Storage_Backend**: The underlying storage system (local filesystem, S3, remote mount, etc.)
- **Native_Monitoring**: OS-provided filesystem monitoring APIs (inotify on Linux, FSEvents on macOS, ReadDirectoryChangesW on Windows)
- **Fallback_Mode**: Monitoring mode used when Native_Monitoring is unavailable
- **Watched_Directory**: The currently displayed directory being monitored for changes

## Requirements

### Requirement 1: Detect External File Creation

**User Story:** As a TFM user, I want the file list to automatically update when external applications create new files, so that I can see new files without manually refreshing.

#### Acceptance Criteria

1. WHEN a file is created in the Watched_Directory by an external process, THE File_Monitor SHALL detect the creation event
2. WHEN a creation event is detected, THE TFM SHALL reload the File_List within 500ms
3. WHEN multiple files are created simultaneously, THE TFM SHALL batch the reload to occur once after all events are processed
4. THE File_Monitor SHALL detect file creation in the Watched_Directory only, not in subdirectories

### Requirement 2: Detect External File Deletion

**User Story:** As a TFM user, I want the file list to automatically update when external applications delete files, so that I don't see stale entries for deleted files.

#### Acceptance Criteria

1. WHEN a file is deleted from the Watched_Directory by an external process, THE File_Monitor SHALL detect the deletion event
2. WHEN a deletion event is detected, THE TFM SHALL reload the File_List within 500ms
3. WHEN multiple files are deleted simultaneously, THE TFM SHALL batch the reload to occur once after all events are processed
4. THE File_Monitor SHALL detect file deletion in the Watched_Directory only, not in subdirectories

### Requirement 3: Detect External File Modification

**User Story:** As a TFM user, I want the file list to update when external applications modify files, so that I can see updated file sizes and timestamps.

#### Acceptance Criteria

1. WHEN a file in the Watched_Directory is modified by an external process, THE File_Monitor SHALL detect the modification event
2. WHEN a modification event is detected, THE TFM SHALL reload the File_List within 500ms
3. WHEN multiple files are modified simultaneously, THE TFM SHALL batch the reload to occur once after all events are processed
4. THE File_Monitor SHALL detect modifications to file content, size, and timestamps

### Requirement 4: Detect External File Rename

**User Story:** As a TFM user, I want the file list to update when external applications rename files, so that I see the current filenames.

#### Acceptance Criteria

1. WHEN a file in the Watched_Directory is renamed by an external process, THE File_Monitor SHALL detect the rename event
2. WHEN a rename event is detected, THE TFM SHALL reload the File_List within 500ms
3. IF the rename operation moves a file into the Watched_Directory from elsewhere, THE File_Monitor SHALL treat it as a creation event
4. IF the rename operation moves a file out of the Watched_Directory, THE File_Monitor SHALL treat it as a deletion event

### Requirement 5: Use Native Monitoring on Supported Platforms

**User Story:** As a TFM user, I want efficient filesystem monitoring, so that the feature doesn't consume excessive system resources.

#### Acceptance Criteria

1. WHERE the Storage_Backend is a local filesystem on Linux, THE File_Monitor SHALL use inotify for monitoring
2. WHERE the Storage_Backend is a local filesystem on macOS, THE File_Monitor SHALL use FSEvents for monitoring
3. WHERE the Storage_Backend is a local filesystem on Windows, THE File_Monitor SHALL use ReadDirectoryChangesW for monitoring
4. WHEN Native_Monitoring is active, THE File_Monitor SHALL consume less than 5MB of memory per watched directory
5. WHEN Native_Monitoring is active, THE File_Monitor SHALL use less than 1% CPU during idle periods

### Requirement 6: Handle Unsupported Storage Backends

**User Story:** As a TFM user working with remote or special filesystems, I want TFM to continue functioning even when automatic monitoring isn't available, so that I can still use TFM with all storage types.

#### Acceptance Criteria

1. WHEN the Storage_Backend does not support Native_Monitoring, THE File_Monitor SHALL detect this condition during initialization
2. IF Native_Monitoring is unavailable, THEN THE File_Monitor SHALL operate in Fallback_Mode
3. WHILE in Fallback_Mode, THE File_Monitor SHALL use periodic polling at 5-second intervals
4. WHERE the Storage_Backend is S3, THE File_Monitor SHALL operate in Fallback_Mode
5. WHERE the Storage_Backend is a network mount without change notification support, THE File_Monitor SHALL operate in Fallback_Mode

### Requirement 7: Update Monitoring When Directory Changes

**User Story:** As a TFM user, I want monitoring to follow me as I navigate directories, so that automatic updates work regardless of which directory I'm viewing.

#### Acceptance Criteria

1. WHEN the user navigates to a different directory, THE File_Monitor SHALL stop monitoring the previous Watched_Directory
2. WHEN the user navigates to a different directory, THE File_Monitor SHALL start monitoring the new Watched_Directory
3. THE transition between monitored directories SHALL complete within 100ms
4. IF monitoring initialization fails for the new directory, THEN THE File_Monitor SHALL log an error and operate in Fallback_Mode for that directory

### Requirement 8: Preserve User Selection During Reload

**User Story:** As a TFM user, I want my cursor position and selection to be preserved when the file list reloads, so that automatic updates don't disrupt my workflow.

#### Acceptance Criteria

1. WHEN the File_List is reloaded due to an External_Change, THE TFM SHALL preserve the currently selected filename
2. IF the selected file still exists after reload, THEN THE TFM SHALL maintain the cursor on that file
3. IF the selected file no longer exists after reload, THEN THE TFM SHALL position the cursor on the nearest remaining file by alphabetical order
4. WHEN the File_List is reloaded, THE TFM SHALL preserve the current scroll position when possible

### Requirement 9: Handle Monitoring Errors Gracefully

**User Story:** As a TFM user, I want TFM to remain stable even when filesystem monitoring encounters errors, so that temporary issues don't crash the application.

#### Acceptance Criteria

1. IF the File_Monitor encounters an error during event processing, THEN THE File_Monitor SHALL log the error and continue monitoring
2. IF the File_Monitor loses connection to the Native_Monitoring API, THEN THE File_Monitor SHALL attempt to reinitialize monitoring
3. IF reinitialization fails after 3 attempts, THEN THE File_Monitor SHALL fall back to Fallback_Mode
4. WHEN operating in Fallback_Mode due to errors, THE TFM SHALL display a status indicator to inform the user

### Requirement 10: Provide User Control Over Monitoring

**User Story:** As a TFM user, I want to control whether automatic monitoring is enabled, so that I can disable it if needed for performance or compatibility reasons.

#### Acceptance Criteria

1. THE TFM SHALL provide a configuration option to enable or disable automatic file monitoring
2. WHEN automatic monitoring is disabled by configuration, THE TFM SHALL not initialize the File_Monitor
3. WHEN automatic monitoring is disabled, THE TFM SHALL reload the File_List only after user-initiated actions
4. THE TFM SHALL allow toggling the monitoring feature at runtime without restarting the application

### Requirement 11: Minimize Redundant Reloads

**User Story:** As a TFM user, I want efficient file list updates, so that the interface remains responsive even during periods of high filesystem activity.

#### Acceptance Criteria

1. WHEN multiple External_Changes occur within 200ms, THE File_Monitor SHALL coalesce them into a single reload operation
2. WHEN the user performs an action that triggers a reload, THE File_Monitor SHALL suppress automatic reloads for 1 second
3. THE File_Monitor SHALL not trigger more than 5 reloads per second regardless of event frequency
4. WHEN event coalescing occurs, THE TFM SHALL ensure all changes are reflected in the final reload

### Requirement 12: Log Monitoring Activity

**User Story:** As a TFM developer, I want detailed logging of monitoring activity, so that I can diagnose issues and verify correct operation.

#### Acceptance Criteria

1. WHEN the File_Monitor initializes, THE File_Monitor SHALL log the monitoring mode (Native_Monitoring or Fallback_Mode)
2. WHEN the File_Monitor detects an External_Change, THE File_Monitor SHALL log the event type and affected filename
3. WHEN the File_Monitor encounters an error, THE File_Monitor SHALL log the error with sufficient context for debugging
4. THE File_Monitor SHALL use the TFM unified logging system with the logger name "FileMonitor"
5. WHEN monitoring mode changes, THE File_Monitor SHALL log the transition and reason
