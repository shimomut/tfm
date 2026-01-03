# Implementation Plan: String Width Reduction Utility

## Overview

Implement a string width reduction utility module (`src/tfm_string_width.py`) that intelligently shortens strings to fit within specified display widths. The implementation will leverage TTK's existing `wide_char_utils` for width calculations and provide flexible shortening strategies with region-based control.

## Tasks

- [x] 1. Create core module structure and data models
  - Create `src/tfm_string_width.py` with module docstring
  - Implement `ShorteningRegion` dataclass with all fields (start, end, priority, strategy, abbrev_position, filepath_mode)
  - Import TTK's `get_display_width` and `unicodedata` for normalization
  - Add logging support using `tfm_log_manager.getLogger("StrWidth")`
  - _Requirements: 1.1, 1.2, 3.2_

- [x] 2. Implement basic width calculation and validation
  - [x] 2.1 Implement `calculate_display_width()` wrapper function
    - Delegate to TTK's `get_display_width()`
    - _Requirements: 1.2_
  
  - [x] 2.2 Implement `normalize_unicode()` function
    - Use `unicodedata.normalize('NFC', text)`
    - _Requirements: 7.1_
  
  - [ ]* 2.3 Write property test for width calculation
    - **Property 2: Wide character width calculation**
    - **Validates: Requirements 1.2**
  
  - [ ]* 2.4 Write property test for Unicode normalization
    - **Property 16: Unicode NFC normalization**
    - **Validates: Requirements 7.1, 7.2**

- [x] 3. Implement removal strategy
  - [x] 3.1 Create `RemovalStrategy` class
    - Implement `shorten()` method that removes characters from region
    - Remove characters from end of region until width fits
    - Do not add ellipsis
    - _Requirements: 2.1_
  
  - [ ]* 3.2 Write property test for removal strategy
    - **Property 4: Removal strategy excludes ellipsis**
    - **Validates: Requirements 2.1**

- [x] 4. Implement abbreviation strategy
  - [x] 4.1 Create `AbbreviationStrategy` class
    - Implement `shorten()` method with position support (left/middle/right)
    - For left: place ellipsis at start, preserve right portion
    - For right: place ellipsis at end, preserve left portion
    - For middle: place ellipsis in center, preserve both ends with balanced distribution
    - _Requirements: 2.2, 4.1, 4.2, 4.3, 4.4_
  
  - [ ]* 4.2 Write property test for abbreviation strategy
    - **Property 5: Abbreviation strategy includes ellipsis**
    - **Validates: Requirements 2.2**
  
  - [ ]* 4.3 Write property test for abbreviation positions
    - **Property 10: Abbreviation position correctness**
    - **Validates: Requirements 4.1, 4.2, 4.3**
  
  - [ ]* 4.4 Write property test for middle abbreviation balance
    - **Property 11: Middle abbreviation balance**
    - **Validates: Requirements 4.4**

- [x] 5. Implement filepath strategy
  - [x] 5.1 Create `FilepathStrategy` class
    - Parse path into directory components and filename
    - Implement `shorten()` method that abbreviates directories before filename
    - Preserve path separators (/ or \)
    - _Requirements: 5.3, 5.4_
  
  - [ ]* 5.2 Write property test for filepath directory priority
    - **Property 12: Filepath directory priority**
    - **Validates: Requirements 5.3**
  
  - [ ]* 5.3 Write property test for filepath separator preservation
    - **Property 13: Filepath separator preservation**
    - **Validates: Requirements 5.4**

- [x] 6. Implement region processing engine
  - [x] 6.1 Implement region sorting by priority
    - Sort regions by priority (descending)
    - Handle equal priorities by definition order
    - _Requirements: 3.1_
  
  - [x] 6.2 Implement region boundary validation
    - Validate start < end, non-negative indices
    - Log warnings for invalid regions and skip them
    - _Requirements: Error Handling_
  
  - [x] 6.3 Implement region processing loop
    - Process regions in priority order
    - Apply appropriate strategy to each region
    - Check if target width met after each region
    - Preserve characters outside region boundaries
    - _Requirements: 3.3, 3.4_
  
  - [ ]* 6.4 Write property test for priority ordering
    - **Property 7: Priority ordering**
    - **Validates: Requirements 3.1**
  
  - [ ]* 6.5 Write property test for region boundary preservation
    - **Property 8: Region boundary preservation**
    - **Validates: Requirements 3.3**
  
  - [ ]* 6.6 Write property test for overlapping regions
    - **Property 9: Overlapping region handling**
    - **Validates: Requirements 3.4**

- [x] 7. Implement main reduce_width() function
  - [x] 7.1 Implement input validation and edge cases
    - Handle empty string, None input
    - Handle negative or zero target width (return empty string)
    - Handle string already fitting (return unchanged)
    - _Requirements: 1.3, 1.4_
  
  - [x] 7.2 Implement region-based shortening
    - If regions specified, process them in priority order
    - If no regions, create default region for entire string
    - _Requirements: 3.5_
  
  - [x] 7.3 Implement fallback to entire string
    - If target not met after all regions, shorten entire string
    - Use default strategy and position
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 7.4 Write property test for output width constraint
    - **Property 1: Output width constraint**
    - **Validates: Requirements 1.1**
  
  - [ ]* 7.5 Write property test for idempotence
    - **Property 3: Idempotence for fitting strings**
    - **Validates: Requirements 1.3**
  
  - [ ]* 7.6 Write property test for fallback behavior
    - **Property 14: Fallback to entire string**
    - **Validates: Requirements 6.1**
  
  - [ ]* 7.7 Write property test for fallback position respect
    - **Property 15: Fallback position respect**
    - **Validates: Requirements 6.2**

- [x] 8. Implement convenience functions
  - [x] 8.1 Implement `abbreviate_middle()` function
    - Call `reduce_width()` with default_position='middle'
    - _Requirements: 8.3_
  
  - [x] 8.2 Implement `abbreviate_path()` function
    - Create region with filepath_mode=True
    - Call `reduce_width()` with the region
    - _Requirements: 8.3_
  
  - [ ]* 8.3 Write unit tests for convenience functions
    - Test that abbreviate_middle uses middle position
    - Test that abbreviate_path uses filepath mode
    - _Requirements: 8.3_

- [x] 9. Implement error handling and logging
  - [x] 9.1 Add error handling for invalid inputs
    - Invalid strategy names: fall back to 'abbreviate', log warning
    - Invalid abbreviation positions: fall back to 'right', log warning
    - Invalid region boundaries: skip region, log warning
    - _Requirements: Error Handling_
  
  - [x] 9.2 Add edge case handling
    - String shorter than ellipsis: return ellipsis only
    - Target width = 1: return first character or ellipsis
    - All wide characters: handle correctly
    - _Requirements: Error Handling_
  
  - [ ]* 9.3 Write unit tests for error handling
    - Test invalid strategy fallback
    - Test invalid position fallback
    - Test invalid region handling
    - _Requirements: Error Handling_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Integration and documentation
  - [x] 11.1 Add module docstring with usage examples
    - Include examples for basic usage, regions, filepath mode
    - Document all public functions
    - _Requirements: 8.4_
  
  - [x] 11.2 Add type hints to all functions
    - Use `Optional`, `List`, `Tuple` from typing module
    - _Requirements: 8.4_
  
  - [ ]* 11.3 Write integration tests
    - Test QuickChoiceBar integration pattern
    - Test status bar integration pattern
    - Test with real-world examples (long paths, CJK filenames)

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation leverages TTK's `wide_char_utils` for width calculations
- All logging uses TFM's unified logging system via `tfm_log_manager`
