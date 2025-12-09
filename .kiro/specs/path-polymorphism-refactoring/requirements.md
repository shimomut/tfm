# Requirements Document

## Introduction

This document specifies the requirements for refactoring TFM's path handling architecture to achieve complete storage-agnostic code through polymorphism. The goal is to eliminate all storage-specific conditionals from UI and dialog code by extending the PathImpl interface with strategic virtual methods that encapsulate storage-specific behavior.

## Glossary

- **PathImpl**: Abstract base class defining the interface for all storage implementations (local files, archives, S3, etc.)
- **Storage-specific conditional**: Code that checks the storage type (e.g., `if scheme == 'archive'`) to determine behavior
- **Virtual method**: Abstract method in PathImpl that each storage implementation must provide
- **Storage-agnostic code**: Code that works with any storage type without checking what type it is
- **UI/Dialog code**: User interface components including text viewer, info dialog, search dialog, and file operations
- **Polymorphic behavior**: Different behavior for different storage types achieved through method overriding rather than conditionals

## Requirements

### Requirement 1

**User Story:** As a developer, I want the UI code to be completely storage-agnostic, so that adding new storage types requires no changes to existing UI components.

#### Acceptance Criteria

1. WHEN a new storage type is added THEN the system SHALL require zero modifications to UI/dialog code
2. WHEN UI code needs storage-specific behavior THEN the system SHALL obtain it through virtual methods on PathImpl
3. WHEN examining UI/dialog source files THEN the system SHALL contain zero storage-specific conditionals (e.g., no `if scheme == 'archive'` checks)
4. WHEN a PathImpl subclass is implemented THEN the system SHALL enforce implementation of all required virtual methods through the abstract base class
5. WHEN storage-specific behavior is needed THEN the system SHALL encapsulate it within the appropriate PathImpl subclass

### Requirement 2

**User Story:** As a developer, I want display formatting to be handled polymorphically, so that each storage type controls its own presentation without UI code needing to know about storage types.

#### Acceptance Criteria

1. WHEN displaying a file path in the text viewer THEN the system SHALL use PathImpl virtual methods to obtain the display prefix and title
2. WHEN formatting a path for display THEN the system SHALL not check the storage scheme or type
3. WHEN an archive path is displayed THEN the ArchivePathImpl SHALL provide "ARCHIVE: " as the prefix and the full archive URI as the title
4. WHEN a local path is displayed THEN the LocalPathImpl SHALL provide an empty prefix and the standard path string as the title
5. WHEN an S3 path is displayed THEN the S3PathImpl SHALL provide "S3: " as the prefix and the S3 URI as the title

### Requirement 3

**User Story:** As a developer, I want file operation validation to use capability-based checks, so that any read-only storage is handled correctly without storage-specific code.

#### Acceptance Criteria

1. WHEN validating a delete operation THEN the system SHALL check if paths support file editing through a virtual method
2. WHEN validating a move operation THEN the system SHALL check if paths support directory renaming through a virtual method
3. WHEN validating a copy-to-destination operation THEN the system SHALL check if the destination supports file editing through a virtual method
4. WHEN a path does not support an operation THEN the system SHALL provide a storage-agnostic error message
5. WHEN checking operation support THEN the system SHALL not parse path strings or check storage schemes

### Requirement 4

**User Story:** As a developer, I want metadata display to be handled polymorphically, so that each storage type provides its own relevant metadata without the info dialog needing storage-specific code.

#### Acceptance Criteria

1. WHEN displaying file metadata THEN the system SHALL request extended metadata from the PathImpl virtual method
2. WHEN an archive entry's metadata is displayed THEN the ArchivePathImpl SHALL provide archive-specific details including archive name, internal path, compression info, and compressed/uncompressed sizes
3. WHEN a local file's metadata is displayed THEN the LocalPathImpl SHALL provide standard file details including size, permissions, and modification time
4. WHEN an S3 object's metadata is displayed THEN the S3PathImpl SHALL provide S3-specific details including bucket, key, storage class, and last modified time
5. WHEN displaying metadata THEN the system SHALL use a unified code path that works for all storage types

### Requirement 5

**User Story:** As a developer, I want search operations to use storage-appropriate strategies, so that each storage type can optimize search performance without the search dialog containing storage-specific logic.

#### Acceptance Criteria

1. WHEN searching files THEN the system SHALL request the search strategy from the PathImpl virtual method
2. WHEN searching local files THEN the LocalPathImpl SHALL indicate streaming strategy for line-by-line reading
3. WHEN searching archive files THEN the ArchivePathImpl SHALL indicate extracted strategy requiring full content extraction
4. WHEN searching S3 objects THEN the S3PathImpl SHALL indicate buffered strategy for downloaded content
5. WHEN implementing search THEN the system SHALL use the strategy hint without checking storage type or scheme
6. WHEN determining whether to cache search content THEN the system SHALL query the PathImpl virtual method
7. WHEN displaying search context THEN the system SHALL use the display prefix virtual method without storage-specific conditionals

### Requirement 6

**User Story:** As a developer, I want content reading behavior to be specified by storage implementations, so that the system can optimize reading strategies without UI code containing storage-specific logic.

#### Acceptance Criteria

1. WHEN determining if content requires extraction THEN the system SHALL query the PathImpl virtual method
2. WHEN determining if streaming read is supported THEN the system SHALL query the PathImpl virtual method
3. WHEN archive content is accessed THEN the ArchivePathImpl SHALL indicate that extraction is required and streaming is not supported
4. WHEN local file content is accessed THEN the LocalPathImpl SHALL indicate that extraction is not required and streaming is supported
5. WHEN S3 content is accessed THEN the S3PathImpl SHALL indicate that extraction is required and streaming is not supported

### Requirement 7

**User Story:** As a developer maintaining the codebase, I want all storage-specific conditionals removed from UI code, so that the code is simpler, more maintainable, and easier to test.

#### Acceptance Criteria

1. WHEN examining tfm_file_operations.py THEN the system SHALL contain zero storage-specific conditional checks
2. WHEN examining tfm_text_viewer.py THEN the system SHALL contain zero storage-specific conditional checks
3. WHEN examining tfm_info_dialog.py THEN the system SHALL contain zero storage-specific conditional checks
4. WHEN examining tfm_search_dialog.py THEN the system SHALL contain zero storage-specific conditional checks
5. WHEN storage-specific methods exist (like `_is_archive_path()`) THEN the system SHALL remove them entirely
6. WHEN error messages reference storage types THEN the system SHALL use storage-agnostic language

### Requirement 8

**User Story:** As a developer, I want the PathImpl interface to be well-documented and complete, so that implementing new storage types is straightforward and all necessary behaviors are specified.

#### Acceptance Criteria

1. WHEN a virtual method is added to PathImpl THEN the system SHALL include comprehensive docstrings explaining the method's purpose, return values, and expected behavior
2. WHEN implementing a new PathImpl subclass THEN the system SHALL enforce implementation of all abstract methods through Python's ABC mechanism
3. WHEN virtual methods return structured data THEN the system SHALL document the expected structure and field meanings
4. WHEN a virtual method has multiple possible return values THEN the system SHALL document all valid values and their semantics
5. WHEN adding virtual methods THEN the system SHALL implement them in all existing PathImpl subclasses (LocalPathImpl, ArchivePathImpl, S3PathImpl)
