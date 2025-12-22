# Implementation Plan: Directory Diff Viewer

## Overview

This implementation plan breaks down the Directory Diff Viewer feature into discrete, incremental coding tasks. Each task builds on previous work, with testing integrated throughout to ensure correctness. The plan follows the established TFM architecture patterns and integrates seamlessly with the existing UILayer stack system.

## Tasks

- [x] 1. Create core data structures and enumerations
  - Create `src/tfm_directory_diff_viewer.py` file
  - Define `DifferenceType` enumeration (IDENTICAL, ONLY_LEFT, ONLY_RIGHT, CONTENT_DIFFERENT, CONTAINS_DIFFERENCE)
  - Define `FileInfo` dataclass for file metadata
  - Define `TreeNode` dataclass for tree structure
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 1.1 Write property test for data structures
  - **Property 1: Tree Structure Completeness**
  - **Validates: Requirements 2.4**

- [x] 2. Implement DirectoryScanner class
  - [x] 2.1 Create DirectoryScanner class with threading support
    - Implement `__init__` with path parameters and progress callback
    - Implement `scan()` method for recursive directory traversal
    - Implement `cancel()` method for cancellation support
    - Use `tfm_path.Path` for file system abstraction
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 2.2 Write property test for directory scanning
    - **Property 8: Progress Reporting Monotonicity**
    - **Validates: Requirements 10.2**

  - [ ]* 2.3 Write property test for cancellation
    - **Property 9: Cancellation Responsiveness**
    - **Validates: Requirements 10.4, 10.5**

- [-] 3. Implement DiffEngine class
  - [x] 3.1 Create DiffEngine class for tree building
    - Implement `__init__` with file dictionaries
    - Implement `build_tree()` to create unified tree structure
    - Implement `classify_node()` for difference detection
    - Implement `compare_file_content()` for file comparison
    - _Requirements: 2.4, 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 3.2 Write property test for difference classification
    - **Property 2: Difference Classification Consistency**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

  - [ ]* 3.3 Write property test for directory difference propagation
    - **Property 3: Directory Difference Propagation**
    - **Validates: Requirements 4.4**

  - [ ]* 3.4 Write property test for file content comparison
    - **Property 7: File Content Comparison Accuracy**
    - **Validates: Requirements 4.3**

- [x] 4. Checkpoint - Ensure core data structures and scanning work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement DirectoryDiffViewer class skeleton
  - [x] 5.1 Create DirectoryDiffViewer class implementing UILayer interface
    - Implement `__init__` with renderer and directory paths
    - Implement all UILayer interface methods (stubs initially)
    - Initialize state variables (scroll_offset, cursor_position, etc.)
    - _Requirements: 1.1, 1.2_

  - [x] 5.2 Implement scanning initialization
    - Implement `start_scan()` to launch DirectoryScanner in worker thread
    - Implement progress callback to update UI state
    - Handle scan completion and error cases
    - _Requirements: 2.1, 10.1, 10.2_

- [x] 6. Implement tree structure management
  - [x] 6.1 Implement tree flattening and visibility
    - Implement method to flatten tree into visible_nodes list
    - Implement method to update visible_nodes when expanding/collapsing
    - Maintain node_index_map for efficient lookups
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 6.2 Write property test for expand/collapse state
    - **Property 5: Expand/Collapse State Preservation**
    - **Validates: Requirements 7.2, 7.3**

- [x] 7. Implement keyboard navigation
  - [x] 7.1 Implement handle_key_event for navigation
    - Implement UP/DOWN arrow keys for cursor movement
    - Implement LEFT/RIGHT or ENTER for expand/collapse
    - Implement ESC/Q for closing viewer
    - Implement PgUp/PgDn for page scrolling
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 7.2 Write property test for navigation consistency
    - **Property 4: Tree Navigation Consistency**
    - **Validates: Requirements 7.1**

- [x] 8. Checkpoint - Ensure navigation and tree management work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement rendering system
  - [x] 9.1 Implement header rendering
    - Draw header with directory paths
    - Draw controls/help text
    - Use tfm_colors for consistent styling
    - _Requirements: 1.2_

  - [x] 9.2 Implement content rendering
    - Draw tree structure with indentation
    - Draw expand/collapse indicators for directories
    - Implement side-by-side layout with separator
    - Apply horizontal scrolling if needed
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.1, 6.2, 6.3, 6.4_

  - [x] 9.3 Implement difference highlighting
    - Apply background colors based on DifferenceType
    - Use COLOR_DIFF_ONLY_ONE_SIDE for only-left/only-right
    - Use COLOR_DIFF_CHANGE for content-different
    - Use COLOR_DIFF_FOCUSED for contains-difference
    - Use COLOR_DIFF_BLANK for blank alignment spaces
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 9.4 Write property test for side-by-side alignment
    - **Property 6: Side-by-Side Alignment**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

  - [x] 9.5 Implement status bar rendering
    - Display current position and statistics
    - Show scan progress when scanning
    - Display error count if errors occurred
    - _Requirements: 10.1, 10.2, 10.3_

- [x] 10. Implement progress feedback during scanning
  - [x] 10.1 Add progress indicator display
    - Show progress bar or percentage during scan
    - Update status message with current operation
    - _Requirements: 10.1, 10.2_

  - [x] 10.2 Implement scan cancellation UI
    - Handle ESC key during scanning to cancel
    - Display cancellation message
    - Clean up worker thread properly
    - _Requirements: 10.4, 10.5_

- [x] 11. Implement error handling
  - [x] 11.1 Handle permission errors gracefully
    - Mark inaccessible nodes with error indicator
    - Store error messages in node metadata
    - Continue processing accessible portions
    - _Requirements: 11.1_

  - [x] 11.2 Handle I/O errors during file comparison
    - Catch and log file read errors
    - Mark affected nodes with error indicator
    - Display error count in status bar
    - _Requirements: 11.2_

  - [ ]* 11.3 Write property test for error handling
    - **Property 10: Error Handling Graceful Degradation**
    - **Validates: Requirements 11.1, 11.2**

  - [x] 11.4 Handle empty or identical directories
    - Display appropriate message when no differences
    - Show statistics in status bar
    - Allow normal viewer closure
    - _Requirements: 11.3_

- [x] 12. Checkpoint - Ensure rendering and error handling work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement file diff viewer integration
  - [x] 13.1 Add key binding to open file diff
    - Detect when cursor is on a content-different file node
    - Create DiffViewer instance with both file paths
    - Push DiffViewer onto UI layer stack
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ]* 13.2 Write integration test for file diff opening
    - Test opening DiffViewer from DirectoryDiffViewer
    - Test returning to DirectoryDiffViewer after closing DiffViewer
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 14. Integrate with FileManager
  - [x] 14.1 Add command to invoke directory diff viewer
    - Add key binding in FileManager (e.g., Ctrl+D)
    - Capture left and right pane paths
    - Validate that both paths are directories
    - Create DirectoryDiffViewer instance
    - Push onto UI layer stack
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 14.2 Write integration test for FileManager invocation
    - Test invoking viewer from FileManager
    - Test with valid directory paths
    - Test error handling with invalid paths
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 15. Add optional features and polish
  - [x] 15.1 Add filter to hide identical files
    - Add toggle key binding (e.g., 'i' for identical)
    - Update visible_nodes to exclude identical nodes when filter active
    - Update status bar to show filter state
    - _Requirements: 3.1, 3.5_

  - [x] 15.2 Add scrollbar support
    - Use tfm_scrollbar module for consistent scrollbar rendering
    - Calculate scrollbar position based on visible nodes
    - _Requirements: 9.3_

  - [x] 15.3 Add wide character support
    - Use tfm_wide_char_utils for proper display width calculation
    - Handle wide characters in file names correctly
    - _Requirements: 6.4_

- [x] 16. Create demo script
  - Create `demo/demo_directory_diff_viewer.py`
  - Set up test directory structures with various difference types
  - Demonstrate all viewer features
  - Include examples of error handling

- [x] 17. Create documentation
  - Create `doc/DIRECTORY_DIFF_VIEWER_FEATURE.md` for end users
  - Document key bindings and usage
  - Include screenshots or examples
  - Create `doc/dev/DIRECTORY_DIFF_VIEWER_IMPLEMENTATION.md` for developers
  - Document architecture and implementation details

- [x] 18. Final checkpoint - Integration testing
  - Run all unit tests and property tests
  - Test with various directory structures (empty, large, nested, with errors)
  - Test integration with FileManager and DiffViewer
  - Test on different terminal sizes
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests verify the viewer works correctly with the rest of TFM
