# Implementation Plan: Text Layout System

## Overview

This plan implements a comprehensive text layout system for TFM that handles text segment rendering with intelligent width management, color attributes, and flexible shortening strategies. The implementation will be done in Python, creating a new module `tfm_text_layout.py` that is independent of the legacy `tfm_string_width.py`.

## Tasks

- [x] 1. Create module structure and base classes
  - Create `src/tfm_text_layout.py` with module docstring
  - Import required dependencies (TTK wide_char_utils, unicodedata, dataclasses, typing, abc)
  - Initialize logger using TFM's unified logging system
  - Define TextSegment abstract base class with common attributes
  - Define SpacerSegment class
  - _Requirements: 1.1-1.7, 10.2, 10.3, 11.5, 12.1, 12.3_

- [ ]* 1.1 Write property test for TextSegment creation
  - **Property 1: Default values are applied correctly**
  - **Validates: Requirements 1.8**

- [x] 2. Implement TextSegment subclasses
  - [x] 2.1 Implement AbbreviationSegment class
    - Define class with abbrev_position attribute
    - Implement shorten() method with left/middle/right ellipsis placement
    - Handle edge cases (target_width = 0, 1, text shorter than ellipsis)
    - _Requirements: 2.1, 3.1, 3.2, 3.3_

- [ ]* 2.2 Write property test for abbreviation strategy
  - **Property 8: Abbreviation Strategy Ellipsis Presence**
  - **Validates: Requirements 2.1, 3.1, 3.2, 3.3**

- [x] 2.3 Implement FilepathSegment class
    - Define class with abbrev_position attribute
    - Implement shorten() method with directory-level removal
    - Parse path into components, remove directories before filename
    - Handle edge cases (no directories, single component, different separators)
    - _Requirements: 2.2_

- [ ]* 2.4 Write property test for filepath abbreviation
  - **Property 12: Filepath Abbreviation Directory Preservation**
  - **Validates: Requirements 2.2**

- [x] 2.5 Implement TruncateSegment class
    - Define class without abbrev_position
    - Implement shorten() method that removes characters from end
    - Ensure no ellipsis is added
    - _Requirements: 2.3_

- [ ]* 2.6 Write property test for truncate strategy
  - **Property 9: Truncate Strategy No Ellipsis**
  - **Validates: Requirements 2.3**

- [x] 2.7 Implement AllOrNothingSegment class
    - Define class
    - Implement shorten() method that returns full text or empty string
    - _Requirements: 2.4_

- [ ]* 2.8 Write property test for all-or-nothing strategy
  - **Property 10: All-or-Nothing Behavior**
  - **Validates: Requirements 2.4**

- [x] 2.9 Implement AsIsSegment class
    - Define class
    - Implement shorten() method that always returns original text
    - _Requirements: 2.5_

- [ ]* 2.10 Write property test for as-is strategy
  - **Property 11: As-Is Strategy Preservation**
  - **Validates: Requirements 2.5**

- [x] 3. Implement wide character support utilities
  - Create helper function for NFC normalization
  - Create helper function for display width calculation (delegates to TTK)
  - Create helper function for wide character boundary checking
  - Handle Unicode errors gracefully with logging
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ]* 3.1 Write property test for wide character handling
  - **Property 13: Wide Character Boundary Preservation**
  - **Property 14: Wide Character Width Accounting**
  - **Validates: Requirements 8.2, 8.3**

- [x] 4. Implement layout calculation engine
  - [x] 4.1 Create LayoutState dataclass
    - Define internal state structure
    - Track current widths, original widths, spacer indices
    - _Requirements: Internal implementation_

- [x] 4.2 Implement spacer collapse logic
    - Identify all spacer segments
    - Set spacer widths to zero when shortening is needed
    - _Requirements: 6.5_

- [ ]* 4.3 Write property test for spacer collapse
  - **Property 5: Spacer Collapse Before Shortening**
  - **Validates: Requirements 6.5**

- [x] 4.4 Implement priority-based shortening
    - Sort segments by priority (descending)
    - Shorten segments at each priority level
    - Respect minimum length constraints
    - Stop when target width is met
    - _Requirements: 4.1, 4.2, 5.1, 5.2_

- [ ]* 4.5 Write property test for priority ordering
  - **Property 2: Priority-Based Shortening Order**
  - **Validates: Requirements 4.1, 4.2**

- [ ]* 4.6 Write property test for minimum length
  - **Property 4: Minimum Length Preservation**
  - **Validates: Requirements 5.1, 5.2**

- [x] 4.7 Implement priority-based restoration
    - Calculate available space after shortening
    - Restore segments in reverse priority order (low to high)
    - Try to restore each segment with available space
    - _Requirements: 4.4_

- [ ]* 4.8 Write property test for restoration
  - **Property 3: Priority-Based Restoration Order**
  - **Validates: Requirements 4.4**

- [x] 4.9 Implement spacer expansion logic
    - Calculate extra space when total width < rendering width
    - Distribute space equally among spacers
    - Handle remainder distribution (first N spacers get +1)
    - _Requirements: 6.2, 6.3, 6.4_

- [ ]* 4.10 Write property test for spacer expansion
  - **Property 6: Spacer Equal Distribution**
  - **Property 7: No Padding Without Spacers**
  - **Validates: Requirements 6.2, 6.3, 6.4**

- [x] 5. Implement rendering logic
  - [x] 5.1 Create RenderContext dataclass
    - Track renderer, row, current column, defaults
    - _Requirements: Internal implementation_

- [x] 5.2 Implement segment rendering loop
    - Iterate through segments with calculated widths
    - Apply color pair (segment's or default)
    - Apply attributes (segment's or default)
    - Call renderer.draw_text() for each segment
    - Update current column position
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 9.1, 9.2, 9.3, 9.4_

- [ ]* 5.3 Write property test for color and attribute application
  - **Property 15: Color and Attribute Application**
  - **Property 16: Default Color and Attribute Usage**
  - **Validates: Requirements 7.3, 7.4, 9.1, 9.2, 9.3, 9.4**

- [ ]* 5.4 Write property test for rendering position
  - **Property 17: Rendering Position Continuity**
  - **Validates: Requirements 7.5**

- [x] 6. Implement main draw_text_segments function
  - Define function signature with all parameters
  - Validate input parameters (renderer, segments, rendering_width)
  - Create LayoutState from segments
  - Execute layout calculation (collapse, shorten, restore, expand)
  - Execute rendering with RenderContext
  - Handle errors gracefully with logging
  - _Requirements: 7.1, 7.6, 10.1, 10.5_

- [ ]* 6.1 Write property test for width constraint
  - **Property 1: Width Constraint Satisfaction**
  - **Validates: Requirements 6.6, 7.6**

- [x] 7. Add error handling and validation
  - Validate segment configuration (invalid abbrev_position, etc.)
  - Validate layout parameters (negative width, None renderer)
  - Handle Unicode errors in normalization and width calculation
  - Handle renderer exceptions during draw_text
  - Log all errors and warnings appropriately
  - _Requirements: 2.6, 3.4, 10.5, 11.1, 11.2, 11.3, 11.4_

- [ ]* 7.1 Write unit tests for error handling
  - Test invalid abbreviation position fallback
  - Test invalid parameters handling
  - Test renderer exception handling
  - _Requirements: 2.6, 3.4, 10.5_

- [x] 8. Add helper functions and convenience APIs
  - Create helper for common status bar layouts
  - Create helper for file list rendering
  - Create helper for dialog prompts
  - Add comprehensive docstrings with examples
  - _Requirements: 10.4_

- [x] 9. Create demo script
  - Create `demo/demo_text_layout_system.py`
  - Demonstrate all segment types
  - Demonstrate spacer behavior
  - Demonstrate priority-based shortening
  - Demonstrate wide character handling
  - _Requirements: Validation_

- [x] 10. Create unit tests for edge cases
  - Test empty segment list
  - Test zero rendering width
  - Test single character segments
  - Test all wide character text
  - Test mixed wide and narrow characters
  - Test spacer-only layouts
  - _Requirements: Comprehensive testing_

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation is independent of tfm_string_width.py
- All code uses TFM's unified logging system
