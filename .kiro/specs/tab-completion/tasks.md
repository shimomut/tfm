# Implementation Plan: TAB Completion

## Overview

This implementation plan breaks down the TAB completion feature into discrete coding tasks. The implementation will extend SingleLineTextEdit with completion functionality, create a completion behavior strategy interface with filepath completion implementation, and add a candidate list overlay UI component.

## Tasks

- [ ] 1. Create completion behavior interface and filepath implementation
  - Create `CompletionBehavior` protocol in `src/tfm_single_line_text_edit.py`
  - Implement `FilepathCompletionBehavior` class with `get_candidates()` and `get_completion_start_pos()` methods
  - Handle directory parsing, file listing, and candidate formatting
  - Add trailing separators for directories
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.4_

- [ ]* 1.1 Write property test for filepath candidate generation
  - **Property 6: Filepath Candidate Generation**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [ ]* 1.2 Write property test for directory separator annotation
  - **Property 7: Directory Separator Annotation**
  - **Validates: Requirements 3.4, 3.5**

- [ ]* 1.3 Write property test for candidate format
  - **Property 8: Candidate Format**
  - **Validates: Requirements 3.6**

- [ ]* 1.4 Write unit tests for filepath completion edge cases
  - Test absolute paths, relative paths, non-existent directories
  - Test permission errors and empty directories
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 2. Implement common prefix calculation utility
  - Create `calculate_common_prefix()` function in `src/tfm_single_line_text_edit.py`
  - Handle empty lists, single-element lists, and multiple candidates
  - Use case-sensitive string comparison
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 2.1 Write property test for common prefix calculation
  - **Property 15: Common Prefix Calculation**
  - **Validates: Requirements 7.1, 7.2**

- [ ]* 2.2 Write unit tests for common prefix edge cases
  - Test empty list, single candidate, no common prefix
  - Test case-sensitive behavior
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 3. Create CandidateListOverlay class
  - Create `CandidateListOverlay` class in new file `src/tfm_candidate_list_overlay.py`
  - Implement `__init__()`, `set_candidates()`, `show()`, `hide()`, `draw()` methods
  - Calculate positioning (above/below text edit field)
  - Handle horizontal alignment with completion start position
  - Render candidates with borders and truncation
  - _Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3, 6.4, 6.5, 6.7_

- [ ]* 3.1 Write property test for candidate list display
  - **Property 2: Candidate List Display**
  - **Validates: Requirements 2.1**

- [ ]* 3.2 Write property test for candidate list positioning
  - **Property 3: Candidate List Positioning**
  - **Validates: Requirements 2.2, 2.3**

- [ ]* 3.3 Write property test for candidate line separation
  - **Property 11: Candidate Line Separation**
  - **Validates: Requirements 6.1**

- [ ]* 3.4 Write property test for candidate truncation
  - **Property 12: Candidate Truncation**
  - **Validates: Requirements 6.3**

- [ ]* 3.5 Write property test for candidate overflow indication
  - **Property 13: Candidate Overflow Indication**
  - **Validates: Requirements 6.4**

- [ ]* 3.6 Write property test for candidate list alignment
  - **Property 14: Candidate List Alignment**
  - **Validates: Requirements 6.7**

- [ ]* 3.7 Write unit tests for visual styling
  - Test colors, borders, and visual attributes
  - _Requirements: 6.2, 6.5_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Extend SingleLineTextEdit with TAB completion
  - Add `completion_behavior` parameter to `__init__()`
  - Create `CandidateListOverlay` instance if completion behavior provided
  - Add `completion_active` state tracking
  - Store completion start position
  - _Requirements: 4.1, 4.2_

- [ ]* 5.1 Write unit tests for completion behavior configuration
  - Test with and without completion behavior
  - _Requirements: 4.1, 4.2_

- [ ] 6. Implement handle_tab_completion() method
  - Get candidates from completion behavior
  - Calculate common prefix
  - Determine completion start position
  - Calculate text to insert
  - Insert completion text at cursor
  - Update cursor position
  - Show/update candidate list for multiple candidates
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 8.1_

- [ ]* 6.1 Write property test for common prefix insertion
  - **Property 1: Common Prefix Insertion**
  - **Validates: Requirements 1.1, 1.2, 8.1**

- [ ]* 6.2 Write unit tests for TAB completion edge cases
  - Test no candidates, empty common prefix
  - Test common prefix equals current input
  - _Requirements: 1.3, 1.4_

- [ ] 7. Implement update_candidate_list() method
  - Get current candidates from completion behavior
  - Update candidate list overlay with new candidates
  - Hide candidate list if no candidates
  - Maintain visibility for single candidate
  - _Requirements: 2.4, 2.5, 2.6, 5.1, 5.2_

- [ ]* 7.1 Write property test for dynamic candidate filtering
  - **Property 4: Dynamic Candidate Filtering**
  - **Validates: Requirements 2.4, 5.1, 5.2**

- [ ]* 7.2 Write property test for single candidate persistence
  - **Property 5: Single Candidate Persistence**
  - **Validates: Requirements 2.6**

- [ ]* 7.3 Write unit tests for candidate list hiding
  - Test zero candidates hide the list
  - _Requirements: 2.5_

- [ ] 8. Update handle_key() method for TAB and ESC
  - Check for TAB key press and call `handle_tab_completion()`
  - Check for ESC key press and hide candidate list
  - Update candidate list after text modifications
  - Preserve existing key handling logic
  - _Requirements: 1.1, 5.4, 8.2_

- [ ]* 8.1 Write property test for completion behavior integration
  - **Property 9: Completion Behavior Integration**
  - **Validates: Requirements 4.3**

- [ ]* 8.2 Write property test for cursor movement preservation
  - **Property 10: Cursor Movement Preservation**
  - **Validates: Requirements 5.3**

- [ ]* 8.3 Write property test for text editing preservation
  - **Property 16: Text Editing Preservation**
  - **Validates: Requirements 8.2**

- [ ]* 8.4 Write unit tests for ESC key handling
  - Test ESC hides candidate list
  - _Requirements: 5.4_

- [ ] 9. Update draw() method to render candidate list
  - Call existing draw logic for text field
  - Call `candidate_list.draw()` if visible
  - Pass correct positioning information
  - _Requirements: 2.1, 6.1, 6.2, 6.3, 6.4, 6.5, 6.7_

- [ ] 10. Add focus handling for candidate list
  - Hide candidate list when text field loses focus
  - Ensure candidate list doesn't auto-appear on focus gain
  - _Requirements: 8.3, 8.4_

- [ ]* 10.1 Write unit tests for focus handling
  - Test focus loss hides list
  - Test focus gain doesn't show list
  - _Requirements: 8.3, 8.4_

- [ ] 11. Add error handling for filesystem operations
  - Catch and handle PermissionError, FileNotFoundError
  - Return empty candidate list on errors
  - Add logging for debugging
  - _Requirements: 3.1_

- [ ]* 11.1 Write unit tests for error handling
  - Test permission errors, non-existent paths
  - Verify empty candidate list returned
  - _Requirements: 3.1_

- [ ] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation uses Python with the Hypothesis library for property-based testing
