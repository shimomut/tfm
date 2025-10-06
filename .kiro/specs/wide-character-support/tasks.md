# Implementation Plan

- [x] 1. Set up project structure and core wide character utilities
  - Create `src/tfm_wide_char_utils.py` module with basic structure and imports
  - Implement core Unicode character classification functions
  - Add terminal capability detection functionality
  - _Requirements: 3.1, 3.2, 5.1, 5.3_

- [x] 1.1 Implement display width calculation functions
  - Write `get_display_width()` function using unicodedata module
  - Implement `is_wide_character()` function for East Asian width detection
  - Handle combining characters and zero-width characters properly
  - _Requirements: 3.1, 4.1, 4.2, 4.3_

- [x] 1.2 Implement text truncation and padding utilities
  - Write `truncate_to_width()` function that preserves character boundaries
  - Implement `pad_to_width()` function for column alignment
  - Create `split_at_width()` function for text wrapping
  - _Requirements: 3.2, 3.3_

- [x] 1.3 Add terminal capability detection
  - Implement `detect_terminal_unicode_support()` function
  - Create fallback mechanisms for limited terminal support
  - Add configuration options for Unicode handling modes
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 1.4 Write comprehensive unit tests for wide character utilities
  - Create test cases for display width calculation with various character types
  - Test truncation and padding functions with mixed character widths
  - Test edge cases including empty strings, only wide chars, and combining characters
  - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3_

- [ ] 2. Update file display system to use wide character utilities
  - Modify `draw_pane()` method in `tfm_main.py` to use wide character functions
  - Replace all `len()` calls with `get_display_width()` for filename width calculations
  - Update filename truncation logic to use `truncate_to_width()`
  - _Requirements: 1.1, 1.3, 2.1, 2.3_

- [ ] 2.1 Fix column alignment in file list display
  - Update basename and extension column width calculations
  - Use `pad_to_width()` for proper column alignment with wide characters
  - Ensure consistent spacing regardless of character types in filenames
  - _Requirements: 1.3, 2.3_

- [ ] 2.2 Update file selection and cursor positioning
  - Ensure cursor positioning works correctly with wide character filenames
  - Fix selection highlighting to cover entire filename display width
  - Update scroll position calculations to account for display width
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 2.3 Write integration tests for file display
  - Create test files with Japanese and mixed character filenames
  - Test file list display with various terminal widths
  - Verify column alignment and cursor positioning accuracy
  - _Requirements: 1.1, 1.3, 2.1, 2.2, 2.3_

- [ ] 3. Update TextViewer to handle wide characters in file content
  - Modify `tfm_text_viewer.py` to use wide character utilities for text display
  - Update line wrapping logic to use `get_display_width()` and `split_at_width()`
  - Fix text truncation in viewer to preserve character boundaries
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 3.1 Implement proper text wrapping for wide characters
  - Replace character-based wrapping with display-width-based wrapping
  - Handle mixed narrow and wide characters in text lines
  - Ensure wrapped lines maintain proper visual alignment
  - _Requirements: 4.1, 4.2_

- [ ] 3.2 Fix cursor positioning and scrolling in text viewer
  - Update cursor position calculations to use display width
  - Ensure horizontal scrolling works correctly with wide characters
  - Fix line number display alignment with wide character content
  - _Requirements: 4.1, 4.2_

- [ ]* 3.3 Write tests for TextViewer wide character support
  - Create test files with Japanese and wide character content
  - Test text wrapping and display with various character types
  - Verify cursor positioning and scrolling functionality
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 4. Update dialog system components for wide character input
  - Modify `SingleLineTextEdit` class to use wide character utilities
  - Update cursor positioning logic in text input fields
  - Fix text display and editing with wide characters
  - _Requirements: 2.2, 4.1, 4.2_

- [ ] 4.1 Update text input field rendering
  - Replace `len()` with `get_display_width()` in text field width calculations
  - Use `truncate_to_width()` for text field content display
  - Ensure proper cursor positioning with wide character input
  - _Requirements: 2.2, 4.1_

- [ ] 4.2 Fix text editing operations with wide characters
  - Update character insertion and deletion to handle wide characters
  - Ensure backspace and delete operations work correctly
  - Fix cursor movement (left/right arrows) with wide characters
  - _Requirements: 2.2, 4.1, 4.2_

- [ ] 4.3 Update all dialog components to use wide character utilities
  - Modify general purpose dialog, search dialog, and other dialog components
  - Ensure consistent wide character handling across all dialogs
  - Update dialog sizing and layout calculations
  - _Requirements: 2.2, 4.1, 4.2_

- [ ]* 4.4 Write tests for dialog system wide character support
  - Test text input with Japanese characters in various dialogs
  - Verify cursor positioning and text editing functionality
  - Test dialog layout and sizing with wide character content
  - _Requirements: 2.2, 4.1, 4.2_

- [ ] 5. Add error handling and fallback mechanisms
  - Implement safe wrapper functions for all wide character utilities
  - Add graceful handling of Unicode encoding errors
  - Create fallback modes for terminals with limited Unicode support
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 5.1 Implement safe display width calculation
  - Create `safe_get_display_width()` with error handling and fallback
  - Handle malformed Unicode sequences in filenames gracefully
  - Log warnings for debugging while maintaining functionality
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 5.2 Add terminal compatibility detection and fallback
  - Detect terminal Unicode capabilities at application startup
  - Implement ASCII-safe fallback mode for limited terminals
  - Add configuration options for different Unicode handling modes
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 5.3 Write tests for error handling and compatibility
  - Test behavior with malformed Unicode filenames
  - Test fallback modes in different terminal environments
  - Verify graceful degradation when Unicode support is limited
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 6. Performance optimization and final integration
  - Optimize display width calculations for common use cases
  - Add caching for frequently calculated filename widths
  - Ensure acceptable performance impact compared to current implementation
  - _Requirements: 1.1, 1.3, 2.1, 2.3_

- [ ] 6.1 Implement performance optimizations
  - Add LRU cache for display width calculations
  - Optimize for ASCII-only filenames (common case)
  - Implement lazy evaluation where appropriate
  - _Requirements: 1.1, 1.3_

- [ ] 6.2 Conduct comprehensive integration testing
  - Test complete application with directories containing wide character filenames
  - Verify all components work together correctly
  - Test performance with large directories containing mixed character types
  - _Requirements: 1.1, 1.3, 2.1, 2.2, 2.3, 4.1, 4.2_

- [ ]* 6.3 Write performance and integration tests
  - Benchmark display width calculation performance
  - Test memory usage with wide character processing
  - Create comprehensive integration test suite
  - _Requirements: 1.1, 1.3, 2.1, 2.2, 2.3, 4.1, 4.2_

- [ ] 7. Documentation and configuration updates
  - Update user documentation to mention wide character support
  - Add configuration options for Unicode handling preferences
  - Create troubleshooting guide for Unicode-related issues
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 7.1 Update configuration system
  - Add configuration options for enabling/disabling wide character support
  - Create settings for fallback modes and Unicode handling preferences
  - Update default configuration with appropriate Unicode settings
  - _Requirements: 5.1, 5.2, 5.4_

- [ ] 7.2 Create user documentation
  - Document wide character support features in user guide
  - Create troubleshooting section for Unicode display issues
  - Add examples of supported character types and terminal requirements
  - _Requirements: 5.1, 5.2, 5.3, 5.4_