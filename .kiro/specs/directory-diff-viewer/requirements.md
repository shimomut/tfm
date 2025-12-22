# Requirements Document

## Introduction

The Directory Diff Viewer is a feature that enables users to compare two directories recursively, displaying differences in a tree-structured view. This viewer integrates with TFM's dual-pane file manager interface, comparing the left and right pane directories and presenting the results in a dedicated UILayer similar to TextViewer and DiffViewer.

## Glossary

- **Directory_Diff_Viewer**: The UILayer component that displays recursive directory comparison results
- **File_Manager**: The main TFM application with dual-pane file list interface
- **UILayer**: A full-screen interface component in TFM (e.g., TextViewer, DiffViewer)
- **Tree_Node**: A collapsible/expandable item in the tree structure representing a file or directory
- **Difference_Type**: Classification of detected differences (only-left, only-right, content-different, contains-difference)
- **Left_Pane**: The left file list pane in File_Manager
- **Right_Pane**: The right file list pane in File_Manager

## Requirements

### Requirement 1: Directory Comparison Initiation

**User Story:** As a user, I want to open a directory diff viewer from the file manager, so that I can compare the directories currently displayed in the left and right panes.

#### Acceptance Criteria

1. WHEN a user invokes the directory diff command, THE Directory_Diff_Viewer SHALL capture the current paths from Left_Pane and Right_Pane
2. WHEN the directory diff command is invoked, THE Directory_Diff_Viewer SHALL open as a new UILayer
3. WHEN either Left_Pane or Right_Pane does not contain a valid directory path, THE System SHALL display an error message and prevent opening the viewer

### Requirement 2: Recursive Directory Scanning

**User Story:** As a user, I want the viewer to scan both directories recursively, so that I can see all nested files and subdirectories in the comparison.

#### Acceptance Criteria

1. WHEN Directory_Diff_Viewer opens, THE System SHALL recursively scan both directory trees
2. WHEN scanning directories, THE System SHALL collect all files and subdirectories at all nesting levels
3. WHEN a directory is inaccessible due to permissions, THE System SHALL mark it as an error and continue scanning other directories
4. WHEN scanning completes, THE System SHALL build a unified tree structure containing all unique paths from both sides

### Requirement 3: Tree Structure Display

**User Story:** As a user, I want to see directories and files in a foldable/expandable tree structure, so that I can navigate through the comparison results hierarchically.

#### Acceptance Criteria

1. THE Directory_Diff_Viewer SHALL display results in a tree structure with collapsible nodes
2. WHEN a Tree_Node represents a directory, THE System SHALL display it with an expand/collapse indicator
3. WHEN a user activates an expand action on a collapsed directory node, THE System SHALL expand the node to show its children
4. WHEN a user activates a collapse action on an expanded directory node, THE System SHALL collapse the node to hide its children
5. WHEN a Tree_Node represents a file, THE System SHALL display it without an expand/collapse indicator

### Requirement 4: Difference Detection and Classification

**User Story:** As a user, I want differences between directories to be automatically detected and classified, so that I can quickly identify what has changed.

#### Acceptance Criteria

1. WHEN a file or directory exists only in the left directory, THE System SHALL classify it as "only-left"
2. WHEN a file or directory exists only in the right directory, THE System SHALL classify it as "only-right"
3. WHEN a file exists in both directories with different content, THE System SHALL classify it as "content-different"
4. WHEN a directory contains any descendant with differences, THE System SHALL classify it as "contains-difference"
5. WHEN a file or directory exists in both locations with identical content and no descendant differences, THE System SHALL classify it as "identical"

### Requirement 5: Difference Highlighting

**User Story:** As a user, I want differences to be highlighted with distinct background colors, so that I can visually identify them at a glance.

#### Acceptance Criteria

1. WHEN a Tree_Node is classified as "only-left", THE System SHALL display it with a distinct background color
2. WHEN a Tree_Node is classified as "only-right", THE System SHALL display it with a distinct background color
3. WHEN a Tree_Node is classified as "content-different", THE System SHALL display it with a distinct background color
4. WHEN a Tree_Node is classified as "contains-difference", THE System SHALL display it with a distinct background color
5. WHEN a Tree_Node is classified as "identical", THE System SHALL display it with the default background color

### Requirement 6: Side-by-Side Layout

**User Story:** As a user, I want to see matching files and directories aligned in the same row, so that I can easily compare corresponding items.

#### Acceptance Criteria

1. WHEN displaying the tree structure, THE System SHALL show left-side and right-side information in aligned columns
2. WHEN a file or directory exists in both locations, THE System SHALL display both names in the same row
3. WHEN a file or directory exists only on one side, THE System SHALL display a blank space with gray background on the other side
4. THE System SHALL maintain row alignment for all tree levels regardless of expansion state

### Requirement 7: Navigation and Interaction

**User Story:** As a user, I want to navigate through the tree structure using keyboard commands, so that I can efficiently explore the comparison results.

#### Acceptance Criteria

1. WHEN the Directory_Diff_Viewer is active, THE System SHALL support cursor movement up and down through visible tree nodes
2. WHEN the cursor is on a collapsed directory node and the user presses the expand key, THE System SHALL expand that node
3. WHEN the cursor is on an expanded directory node and the user presses the collapse key, THE System SHALL collapse that node
4. WHEN the user presses the close key, THE System SHALL close the Directory_Diff_Viewer and return to File_Manager

### Requirement 8: File Content Comparison Integration

**User Story:** As a user, I want to open a file diff viewer for files marked as different, so that I can see the specific content differences.

#### Acceptance Criteria

1. WHEN the cursor is on a Tree_Node classified as "content-different" and the user invokes the view diff action, THE System SHALL open the existing DiffViewer with those two files
2. WHEN the cursor is on a Tree_Node that is not a file or not classified as "content-different", THE System SHALL ignore the view diff action
3. WHEN the DiffViewer is closed, THE System SHALL return focus to the Directory_Diff_Viewer

### Requirement 9: Performance for Large Directory Trees

**User Story:** As a user, I want the viewer to handle large directory trees efficiently, so that I can compare directories with thousands of files without performance degradation.

#### Acceptance Criteria

1. WHEN scanning directories with more than 1000 files, THE System SHALL complete the scan within a reasonable time
2. WHEN rendering the tree view, THE System SHALL only render visible tree nodes
3. WHEN scrolling through the tree, THE System SHALL update the display without noticeable lag
4. WHEN expanding or collapsing nodes, THE System SHALL respond immediately to user input

### Requirement 10: Progress Feedback

**User Story:** As a user, I want to see visual progress information while directories are being scanned, so that I know the operation is proceeding and can estimate completion time.

#### Acceptance Criteria

1. WHEN directory scanning begins, THE System SHALL display a progress indicator
2. WHILE scanning is in progress, THE System SHALL update the progress indicator with current status information
3. WHEN scanning completes, THE System SHALL remove the progress indicator and display the comparison results
4. WHILE scanning is in progress, THE System SHALL allow the user to cancel the operation
5. WHEN the user cancels scanning, THE System SHALL stop the scan and close the Directory_Diff_Viewer

### Requirement 11: Error Handling

**User Story:** As a system administrator, I want clear error messages when comparison fails, so that I can understand and resolve issues.

#### Acceptance Criteria

1. WHEN a directory cannot be accessed due to permissions, THE System SHALL display an error indicator for that directory and continue with accessible portions
2. WHEN file content comparison fails due to I/O errors, THE System SHALL mark the file with an error indicator
3. WHEN both directories are identical or empty, THE System SHALL display an appropriate message
4. WHEN the comparison is interrupted, THE System SHALL allow the user to close the viewer gracefully
