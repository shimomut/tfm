# Requirements Document

## Introduction

This document specifies the requirements for adding drag-and-drop support to TFM (Terminal File Manager), enabling users to drag files from TFM to other applications for copy, move, or open operations. This feature builds on the existing mouse event support infrastructure and focuses on desktop mode (CoreGraphics backend) where drag-and-drop is natively supported by the operating system.

## Glossary

- **TFM**: Terminal File Manager, the application using TTK
- **TTK**: The Terminal ToolKit library that provides the backend abstraction layer for TFM
- **CoreGraphics_Backend**: The macOS-native rendering backend that supports desktop mode
- **Drag_Source**: The TFM component from which files are dragged
- **Drop_Target**: The external application or location where files are dropped
- **Drag_Session**: The period from when a drag begins until it completes (drop or cancel)
- **Drag_Payload**: The collection of file paths being dragged
- **Selected_Files**: Files that have been marked for selection in the file list
- **Focused_Item**: The file or directory currently under the cursor when no files are selected
- **Pasteboard**: The macOS system clipboard/drag-and-drop data transfer mechanism
- **File_Promise**: A mechanism for providing file data asynchronously during drag-and-drop

## Requirements

### Requirement 1: Drag Initiation

**User Story:** As a TFM user, I want to initiate a drag operation by clicking and dragging on files, so that I can transfer files to other applications.

#### Acceptance Criteria

1. WHEN a user presses the mouse button on a file item and moves the mouse, THE TFM SHALL initiate a drag session
2. WHEN selected files exist, THE Drag_Payload SHALL contain all Selected_Files
3. WHEN no files are selected, THE Drag_Payload SHALL contain only the Focused_Item
4. WHEN the Focused_Item is the parent directory marker (".."), THE TFM SHALL not initiate a drag session
5. THE TFM SHALL require a minimum mouse movement threshold before starting the drag to distinguish from clicks

### Requirement 2: Drag Visual Feedback

**User Story:** As a TFM user, I want visual feedback during drag operations, so that I understand what is being dragged and the drag state.

#### Acceptance Criteria

1. WHEN a drag session begins, THE TFM SHALL display a drag image showing the file count being dragged
2. WHEN dragging a single file, THE drag image SHALL display the filename
3. WHEN dragging multiple files, THE drag image SHALL display the count (e.g., "3 files")
4. WHEN the drag cursor moves over a valid Drop_Target, THE system SHALL show an appropriate cursor indicator
5. WHEN the drag is cancelled, THE TFM SHALL restore normal cursor and visual state

### Requirement 3: File Path Payload

**User Story:** As a system integrator, I want file paths provided in standard formats, so that external applications can receive and process the dragged files.

#### Acceptance Criteria

1. THE Drag_Payload SHALL contain file paths as absolute paths
2. THE Drag_Payload SHALL use the file:// URL scheme for compatibility with macOS applications
3. WHEN dragging local files, THE TFM SHALL provide paths in the NSFilenamesPboardType format
4. WHEN dragging remote files (S3, SSH), THE TFM SHALL not initiate a drag session
5. THE TFM SHALL validate that all files in the Drag_Payload exist before starting the drag

### Requirement 4: Drag Session Management

**User Story:** As a developer, I want proper drag session lifecycle management, so that resources are properly allocated and released.

#### Acceptance Criteria

1. WHEN a drag session begins, THE TFM SHALL register the session with the operating system
2. WHEN a drag session completes (drop or cancel), THE TFM SHALL clean up drag-related resources
3. WHEN a drag is in progress, THE TFM SHALL not process other mouse events for the Drag_Source
4. THE TFM SHALL track the drag state (idle, dragging, completed, cancelled)
5. WHEN the user releases the mouse button outside a valid Drop_Target, THE TFM SHALL cancel the drag session

### Requirement 5: Backend Integration

**User Story:** As a system architect, I want drag-and-drop integrated with the TTK backend system, so that the feature works consistently with other mouse events.

#### Acceptance Criteria

1. THE CoreGraphics_Backend SHALL provide a method to initiate a drag session with file paths
2. THE CoreGraphics_Backend SHALL handle the native drag-and-drop protocol with the operating system
3. THE CoreGraphics_Backend SHALL notify TFM when a drag session completes
4. WHEN running in terminal mode (Curses backend), THE TFM SHALL gracefully disable drag-and-drop features
5. THE TTK SHALL provide a capability query method for drag-and-drop support

### Requirement 6: Drag Gesture Detection

**User Story:** As a TFM user, I want drag gestures distinguished from clicks, so that clicking doesn't accidentally start a drag.

#### Acceptance Criteria

1. THE TFM SHALL define a minimum drag distance threshold (e.g., 5 pixels)
2. WHEN mouse movement is less than the threshold, THE TFM SHALL treat the event as a click
3. WHEN mouse movement exceeds the threshold with button held, THE TFM SHALL initiate a drag session
4. THE TFM SHALL track mouse button state to detect drag gestures
5. THE TFM SHALL use a time threshold to distinguish between click and drag (e.g., 150ms)

### Requirement 7: Multi-File Drag Support

**User Story:** As a TFM user, I want to drag multiple selected files at once, so that I can efficiently transfer groups of files.

#### Acceptance Criteria

1. WHEN multiple files are selected, THE Drag_Payload SHALL include all Selected_Files in order
2. THE TFM SHALL support dragging up to 1000 files in a single operation
3. WHEN the file count exceeds the limit, THE TFM SHALL show an error message and prevent the drag
4. THE TFM SHALL maintain selection state during and after the drag operation
5. THE TFM SHALL include both files and directories in the Drag_Payload when selected

### Requirement 8: Error Handling

**User Story:** As a TFM user, I want clear feedback when drag operations fail, so that I understand what went wrong.

#### Acceptance Criteria

1. WHEN a file in the Drag_Payload no longer exists, THE TFM SHALL show an error message and cancel the drag
2. WHEN dragging remote files, THE TFM SHALL show a message explaining that only local files can be dragged
3. WHEN the operating system rejects the drag, THE TFM SHALL log the error and restore normal state
4. WHEN dragging the parent directory marker, THE TFM SHALL not initiate a drag and show no error
5. THE TFM SHALL handle drag cancellation gracefully without leaving the UI in an inconsistent state

### Requirement 9: Archive File Support

**User Story:** As a TFM user, I want to drag files from within archive views, so that I can extract files by dragging them out.

#### Acceptance Criteria

1. WHEN viewing files inside an archive, THE TFM SHALL not support drag-and-drop operations
2. THE TFM SHALL show a message explaining that files must be extracted before dragging
3. WHEN the Focused_Item is an archive file itself (not inside), THE TFM SHALL allow dragging the archive file
4. THE TFM SHALL detect archive paths and disable drag initiation for virtual archive contents
5. THE TFM SHALL provide clear visual indication that drag is not available in archive views

### Requirement 10: Drag Operation Types

**User Story:** As a TFM user, I want the receiving application to determine the operation type (copy/move/open), so that I can use standard OS conventions.

#### Acceptance Criteria

1. THE TFM SHALL provide file paths to the operating system without specifying operation type
2. THE receiving application SHALL determine whether to copy, move, or open the files
3. THE TFM SHALL support the standard macOS drag operation modifiers (Option for copy, Command for move)
4. THE operating system SHALL handle the actual file operations based on Drop_Target capabilities
5. THE TFM SHALL not track or verify the outcome of the drop operation

