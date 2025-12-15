# Requirements Document

## Introduction

This document specifies the requirements for adding archive file support to TFM (TUI File Manager). The feature will allow users to browse the contents of archive files (*.zip, *.tgz, *.tar.gz, etc.) as virtual directories without extracting them to the filesystem. Users will be able to navigate into archives, view files, copy files out of archives, and search within archive contents.

## Glossary

- **TFM**: TUI File Manager - the terminal-based file manager application
- **Archive File**: A compressed file container (e.g., .zip, .tgz, .tar.gz, .tar.bz2) that contains one or more files and directories
- **Virtual Directory**: A directory representation of archive contents that exists only in memory, not as extracted files on disk
- **Archive Entry**: A file or directory contained within an archive file
- **Built-in Text Viewer**: TFM's internal text file viewing component
- **Search Dialog**: TFM's file search interface for finding files by name or pattern
- **Local Filesystem**: The standard file system on the user's computer (as opposed to S3 or archive contents)
- **S3**: Amazon S3 cloud storage service
- **Archive Navigation**: The process of entering and browsing within archive files

## Requirements

### Requirement 1

**User Story:** As a user, I want to enter archive files by pressing ENTER, so that I can browse their contents without extracting them.

#### Acceptance Criteria

1. WHEN a user positions the cursor on an archive file and presses ENTER, THEN the system SHALL display the archive contents as a virtual directory
2. WHEN displaying archive contents, THE system SHALL show files and directories with their names, sizes, and modification dates
3. WHEN an archive file is recognized, THE system SHALL support .zip, .tar, .tar.gz, .tgz, .tar.bz2, and .tar.xz formats
4. WHEN entering an archive, THE system SHALL maintain the navigation history to allow returning to the parent directory
5. WHEN an archive cannot be opened, THE system SHALL display an error message and remain in the current directory

### Requirement 2

**User Story:** As a user, I want to navigate within archive contents using standard navigation keys, so that I can explore nested directories inside archives.

#### Acceptance Criteria

1. WHEN browsing archive contents, THE system SHALL support standard cursor movement keys (up, down, page up, page down)
2. WHEN a directory entry within an archive is selected and ENTER is pressed, THE system SHALL navigate into that directory
3. WHEN the backspace key is pressed within archive contents, THE system SHALL navigate to the parent directory within the archive
4. WHEN at the root of archive contents and backspace is pressed, THE system SHALL exit the archive and return to the filesystem directory containing the archive
5. WHEN navigating within archives, THE system SHALL display the current path showing the archive name and internal path

### Requirement 3

**User Story:** As a user, I want to copy files from archives to local filesystem or S3, so that I can extract specific files without extracting the entire archive.

#### Acceptance Criteria

1. WHEN files are selected within archive contents and a copy operation is initiated, THE system SHALL extract the selected files to the target location
2. WHEN copying from archive to local filesystem, THE system SHALL preserve file permissions and modification times where possible
3. WHEN copying from archive to S3, THE system SHALL upload the extracted file contents directly to S3
4. WHEN copying directories from archives, THE system SHALL recursively extract all contained files and subdirectories
5. WHEN a copy operation fails, THE system SHALL display an error message indicating which files failed and why

### Requirement 4

**User Story:** As a user, I want to view text files within archives using the built-in text viewer, so that I can read file contents without extracting them.

#### Acceptance Criteria

1. WHEN a text file within an archive is selected and the view command is triggered, THE system SHALL extract the file to a temporary location and display it in the built-in text viewer
2. WHEN viewing a file from an archive, THE system SHALL display the full archive path in the viewer title
3. WHEN the text viewer is closed, THE system SHALL clean up any temporary extracted files
4. WHEN a binary file is selected for viewing, THE system SHALL display an appropriate message or handle it according to existing binary file viewing behavior
5. WHEN viewing fails due to extraction errors, THE system SHALL display an error message

### Requirement 5

**User Story:** As a user, I want to search for files within archive contents, so that I can quickly find specific files in large archives.

#### Acceptance Criteria

1. WHEN the search dialog is opened while browsing archive contents, THE system SHALL search within the current archive location
2. WHEN searching in archives, THE system SHALL support filename pattern matching using the same syntax as filesystem searches
3. WHEN search results are displayed, THE system SHALL show the full path within the archive for each matching file
4. WHEN a search result is selected, THE system SHALL navigate to that file's location within the archive
5. WHEN searching large archives, THE system SHALL provide progress feedback during the search operation

### Requirement 6

**User Story:** As a user, I want visual indicators that distinguish archive contents from regular directories, so that I understand when I'm browsing virtual archive contents.

#### Acceptance Criteria

1. WHEN browsing archive contents, THE system SHALL display a visual indicator in the status bar or path display
2. WHEN displaying the current path, THE system SHALL clearly show the archive filename and the path within the archive
3. WHEN listing archive entries, THE system SHALL use consistent formatting that matches regular directory listings
4. WHEN an archive entry represents a directory, THE system SHALL display it with appropriate directory indicators
5. WHEN displaying file sizes for archive entries, THE system SHALL show the uncompressed size

### Requirement 7

**User Story:** As a user, I want archive operations to handle errors gracefully, so that corrupt or unsupported archives don't crash the application.

#### Acceptance Criteria

1. WHEN an archive file is corrupted, THE system SHALL display an error message and prevent navigation into the archive
2. WHEN an unsupported archive format is encountered, THE system SHALL display a message indicating the format is not supported
3. WHEN extraction fails due to insufficient permissions, THE system SHALL display a permission error message
4. WHEN extraction fails due to insufficient disk space, THE system SHALL display a disk space error message
5. WHEN any archive operation encounters an error, THE system SHALL log the error details for debugging purposes

### Requirement 8

**User Story:** As a user, I want archive browsing to integrate seamlessly with existing TFM features, so that I can use familiar operations within archives.

#### Acceptance Criteria

1. WHEN browsing archive contents, THE system SHALL support file selection using the same keys as regular directories
2. WHEN multiple files are selected in an archive, THE system SHALL allow batch operations on all selected files
3. WHEN the file details view is requested for an archive entry, THE system SHALL display available metadata
4. WHEN sorting options are changed, THE system SHALL apply the same sorting to archive contents as to regular directories
5. WHEN the dual-pane view is active, THE system SHALL allow one pane to show archive contents while the other shows a regular directory
