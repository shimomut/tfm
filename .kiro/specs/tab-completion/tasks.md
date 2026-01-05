# Implementation Plan: TAB Completion

## Overview

This implementation plan breaks down the TAB completion feature into discrete coding tasks. The implementation will extend SingleLineTextEdit with completion functionality, create a completer strategy interface with filepath completion implementation, and add a candidate list overlay UI component.

## Tasks

- [x] 1. Create completer interface and filepath implementation
  - Create `Completer` protocol in `src/tfm_single_line_text_edit.py`
  - Implement `FilepathCompleter` class with `get_candidates()` and `get_completion_start_pos()` methods
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

- [x] 2. Implement common prefix calculation utility
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

- [x] 3. Create CandidateListOverlay class
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

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Extend SingleLineTextEdit with TAB completion
  - Add `completer` parameter to `__init__()`
  - Create `CandidateListOverlay` instance if completer provided
  - Add `completion_active` state tracking
  - Store completion start position
  - _Requirements: 4.1, 4.2_

- [ ]* 5.1 Write unit tests for completer configuration
  - Test with and without completer
  - _Requirements: 4.1, 4.2_

- [x] 6. Implement handle_tab_completion() method
  - Get candidates from completer
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

- [x] 7. Implement update_candidate_list() method
  - Get current candidates from completer
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

- [x] 8. Update handle_key() method for TAB and ESC
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

- [x] 9. Update draw() method to render candidate list
  - Call existing draw logic for text field
  - Call `candidate_list.draw()` if visible
  - Pass correct positioning information
  - _Requirements: 2.1, 6.1, 6.2, 6.3, 6.4, 6.5, 6.7_

- [x] 10. Add focus handling for candidate list
  - Hide candidate list when text field loses focus
  - Ensure candidate list doesn't auto-appear on focus gain
  - _Requirements: 8.3, 8.4_

- [ ]* 10.1 Write unit tests for focus handling
  - Test focus loss hides list
  - Test focus gain doesn't show list
  - _Requirements: 8.3, 8.4_

- [x] 11. Add error handling for filesystem operations
  - Catch and handle PermissionError, FileNotFoundError
  - Return empty candidate list on errors
  - Add logging for debugging
  - _Requirements: 3.1_

- [ ]* 11.1 Write unit tests for error handling
  - Test permission errors, non-existent paths
  - Verify empty candidate list returned
  - _Requirements: 3.1_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation uses Python with the Hypothesis library for property-based testing

- [x] 13. Add focus state management to CandidateListOverlay
  - Add `focused_index` attribute (Optional[int]) to track focused candidate
  - Add `scroll_offset` attribute to track first visible candidate
  - Implement `move_focus_up()` method with wrapping behavior
  - Implement `move_focus_down()` method with wrapping behavior
  - Implement `get_focused_candidate()` method to return focused candidate text
  - Implement `has_focus()` method to check if any candidate is focused
  - Implement `clear_focus()` method to reset focus state
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ]* 13.1 Write property test for focus movement with Down arrow
  - **Property 17: Focus Movement with Down Arrow**
  - **Validates: Requirements 9.1, 9.3, 9.5**

- [ ]* 13.2 Write property test for focus movement with Up arrow
  - **Property 18: Focus Movement with Up Arrow**
  - **Validates: Requirements 9.2, 9.4, 9.6**

- [ ]* 13.3 Write unit tests for focus wrapping
  - Test wrap from last to first, first to last
  - Test initial focus activation
  - _Requirements: 9.3, 9.4, 9.5, 9.6_

- [x] 14. Add visual highlighting for focused candidate
  - Modify `draw()` method to highlight focused candidate
  - Use different background color or text attributes for focused item
  - Ensure focused candidate is visually distinct
  - _Requirements: 9.7_

- [ ]* 14.1 Write property test for focused candidate visual distinction
  - **Property 19: Focused Candidate Visual Distinction**
  - **Validates: Requirements 9.7**

- [ ]* 14.2 Write unit tests for visual highlighting
  - Test focused vs non-focused rendering
  - _Requirements: 9.7_

- [x] 15. Implement auto-scroll for focused candidate
  - Calculate visible range based on overlay height
  - Adjust `scroll_offset` when focused candidate is above visible area
  - Adjust `scroll_offset` when focused candidate is below visible area
  - Ensure focused candidate is always visible after navigation
  - _Requirements: 12.4, 12.5, 12.6_

- [ ]* 15.1 Write property test for auto-scroll on navigation
  - **Property 24: Auto-scroll on Navigation**
  - **Validates: Requirements 12.4, 12.5, 12.6**

- [ ]* 15.2 Write unit tests for scroll boundary conditions
  - Test scroll at top, bottom, and middle of list
  - _Requirements: 12.4, 12.5, 12.6_

- [x] 16. Add scrollbar rendering to CandidateListOverlay
  - Calculate scrollbar position and size based on scroll_offset and visible_count
  - Render scrollbar on right edge of overlay (inside border)
  - Use filled blocks (█) for visible portion, empty blocks (░) for non-visible
  - Only show scrollbar when candidates exceed visible area
  - _Requirements: 12.1, 12.2, 12.3_

- [ ]* 16.1 Write property test for scrollbar visibility
  - **Property 22: Scrollbar Visibility**
  - **Validates: Requirements 12.1**

- [ ]* 16.2 Write property test for scrollbar position indication
  - **Property 23: Scrollbar Position Indication**
  - **Validates: Requirements 12.2, 12.3**

- [ ]* 16.3 Write unit tests for scrollbar rendering
  - Test scrollbar with various list sizes
  - Test scrollbar position at different scroll offsets
  - _Requirements: 12.1, 12.2, 12.3_

- [x] 17. Update SingleLineTextEdit to handle Up/Down arrow keys
  - Check if candidate list is visible in `handle_key()`
  - On Down arrow: call `candidate_list.move_focus_down()` and return True
  - On Up arrow: call `candidate_list.move_focus_up()` and return True
  - Mark dirty to trigger redraw with updated focus
  - _Requirements: 9.1, 9.2_

- [ ]* 17.1 Write unit tests for arrow key handling
  - Test Up/Down keys when list is visible
  - Test Up/Down keys when list is hidden (should not be handled)
  - _Requirements: 9.1, 9.2_

- [x] 18. Implement Enter key selection in SingleLineTextEdit
  - Check if candidate list has focus in `handle_key()`
  - On Enter with focus: get focused candidate and apply it
  - Implement `apply_candidate()` method to replace completion portion
  - Update cursor position to end of inserted text
  - Hide candidate list after selection
  - Clear focus state
  - _Requirements: 10.1, 10.2, 10.3_

- [ ]* 18.1 Write property test for Enter key selection
  - **Property 20: Enter Key Selection**
  - **Validates: Requirements 10.1, 10.2, 10.3**

- [ ]* 18.2 Write unit tests for candidate application
  - Test text replacement and cursor positioning
  - Test with various candidate positions
  - _Requirements: 10.1, 10.2, 10.3_

- [x] 19. Update ESC key handling to clear focus
  - Modify existing ESC handling to also clear focus state
  - Ensure focus is cleared when candidate list is hidden
  - _Requirements: 11.3_

- [ ]* 19.1 Write property test for ESC key dismissal
  - **Property 21: ESC Key Dismissal**
  - **Validates: Requirements 11.1, 11.2, 11.3**

- [ ]* 19.2 Write unit tests for ESC with focus
  - Test ESC clears focus and hides list
  - _Requirements: 11.3_

- [x] 20. Checkpoint - Ensure all keyboard navigation tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 21. Integration testing for complete keyboard navigation workflow
  - Test complete workflow: TAB → Down → Down → Enter
  - Test complete workflow: TAB → Up → ESC
  - Test scrolling with long candidate lists
  - Test focus wrapping at boundaries
  - Verify visual feedback at each step
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 10.1, 10.2, 10.3, 11.1, 11.2, 11.3, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [ ]* 21.1 Write integration tests for keyboard navigation
  - Test full navigation workflows
  - Test edge cases and boundary conditions
  - _Requirements: All keyboard navigation requirements_

- [x] 22. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
