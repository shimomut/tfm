# Requirements Document

## Introduction

This specification addresses a performance issue in `FileListManager.sort_entries()` where redundant `is_dir()` calls cause significant slowdowns, especially on remote filesystems (SFTP, S3). Each `is_dir()` call can trigger a network stat operation, and the current implementation calls it twice per entry during sorting.

## Glossary

- **FileListManager**: Component responsible for managing file lists, sorting, filtering, and selection
- **Entry**: A Path object representing a file or directory
- **is_dir()**: Method that checks if a path is a directory (potentially expensive on remote filesystems)
- **sort_entries()**: Method that sorts file entries based on a specified mode
- **Remote Filesystem**: Network-based filesystem like SFTP or S3 where stat operations involve network latency

## Requirements

### Requirement 1: Eliminate Redundant is_dir() Calls

**User Story:** As a user browsing remote directories, I want sorting to be fast, so that I can navigate efficiently without waiting for network operations.

#### Acceptance Criteria

1. WHEN sorting entries, THE System SHALL call is_dir() at most once per entry
2. WHEN separating directories from files, THE System SHALL reuse cached directory status
3. WHEN sorting completes, THE System SHALL maintain correct directory-first ordering
4. WHEN an entry's directory status is unknown, THE System SHALL handle the error gracefully

### Requirement 2: Maintain Sorting Correctness

**User Story:** As a user, I want files to be sorted correctly with directories always first, so that I can find items predictably.

#### Acceptance Criteria

1. WHEN entries are sorted, THE System SHALL place all directories before all files
2. WHEN sort mode is 'name', THE System SHALL use natural sorting for both directories and files
3. WHEN sort mode is 'ext', THE System SHALL sort by extension with directories first
4. WHEN sort mode is 'size', THE System SHALL sort by file size with directories first
5. WHEN sort mode is 'date', THE System SHALL sort by modification time with directories first
6. WHEN reverse is True, THE System SHALL reverse the sort order within each group (directories, files)

### Requirement 3: Handle Stat Errors Gracefully

**User Story:** As a user, I want sorting to work even when some files have permission errors, so that I can still browse the accessible files.

#### Acceptance Criteria

1. WHEN is_dir() raises OSError, THE System SHALL treat the entry as a file
2. WHEN is_dir() raises PermissionError, THE System SHALL treat the entry as a file
3. WHEN stat() fails during sorting, THE System SHALL use the entry name as fallback sort key
4. WHEN errors occur, THE System SHALL continue sorting remaining entries

### Requirement 4: Preserve Existing Behavior

**User Story:** As a developer, I want the optimization to be transparent, so that existing code continues to work without changes.

#### Acceptance Criteria

1. THE System SHALL maintain the same method signature for sort_entries()
2. THE System SHALL return results in the same format as before
3. THE System SHALL support all existing sort modes (name, ext, size, date, type)
4. THE System SHALL respect the reverse parameter
5. THE System SHALL maintain backward compatibility with existing callers

### Requirement 5: Performance Improvement

**User Story:** As a user on a slow network, I want sorting to complete quickly, so that I don't experience UI freezes.

#### Acceptance Criteria

1. WHEN sorting N entries, THE System SHALL call is_dir() at most N times (not 2N times)
2. WHEN sorting remote directories, THE System SHALL complete noticeably faster than before
3. WHEN sorting local directories, THE System SHALL maintain similar or better performance
4. WHEN profiling is enabled, THE System SHALL show reduced is_dir() call count
