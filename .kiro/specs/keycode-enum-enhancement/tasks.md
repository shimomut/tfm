# Implementation Plan: KeyCode Enum Enhancement

## Overview

This plan implements the enhanced KeyCode enum with comprehensive key mappings for both macOS (CoreGraphics) and curses backends. The implementation follows an incremental approach: first extending the enum, then updating each backend's mapping system, and finally adding comprehensive tests.

## Tasks

- [x] 1. Extend KeyCode enum with printable characters
  - Add letter keys (KEY_A through KEY_Z) in range 2000-2025
  - Add digit keys (KEY_0 through KEY_9) in range 2100-2109
  - Add SPACE key using Unicode value 32
  - Add symbol/punctuation keys in range 2200-2299
  - Ensure no conflicts with existing special key codes (1000+ range)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_

- [ ]* 1.1 Write unit tests for KeyCode enum structure
  - Test that all letter keys exist (KEY_A through KEY_Z)
  - Test that all digit keys exist (KEY_0 through KEY_9)
  - Test that SPACE key exists
  - Test that all symbol keys exist
  - Test that existing special keys still exist
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 6.3_

- [ ]* 1.2 Write property test for KeyCode uniqueness
  - **Property 1: KeyCode Value Uniqueness**
  - **Validates: Requirements 1.6**
  - Generate all KeyCode enum values
  - Verify no two distinct entries have the same integer value
  - _Requirements: 1.6_

- [ ]* 1.3 Write property test for backward compatibility
  - **Property 3: Backward Compatibility of Existing KeyCodes**
  - **Validates: Requirements 1.5, 6.1, 6.2, 6.4**
  - For all existing special keys, verify integer values unchanged
  - Test keys: UP, DOWN, LEFT, RIGHT, F1-F12, ENTER, ESCAPE, BACKSPACE, TAB, INSERT, DELETE, HOME, END, PAGE_UP, PAGE_DOWN
  - _Requirements: 1.5, 6.1, 6.2, 6.4_

- [x] 2. Implement macOS key mapping system
  - [x] 2.1 Create MACOS_ANSI_KEY_MAP dictionary
    - Map all letter keys (0x00-0x2E range to KEY_A through KEY_Z)
    - Map all digit keys (0x12-0x1D range to KEY_0 through KEY_9)
    - Map space key (0x31 to SPACE)
    - Map all symbol/punctuation keys
    - Include existing special key mappings
    - Add comments referencing https://gist.github.com/eegrok/949034
    - _Requirements: 2.1, 2.2, 2.3, 5.1, 5.4_

  - [x] 2.2 Add keyboard_layout parameter to CoreGraphicsBackend.__init__
    - Accept keyboard_layout parameter (default: 'ANSI')
    - Store layout in instance variable
    - Call _get_key_map to initialize key mapping
    - _Requirements: 2.4, 4.2, 4.3_

  - [x] 2.3 Implement _get_key_map method
    - Return MACOS_ANSI_KEY_MAP for 'ANSI' layout
    - Raise NotImplementedError for 'JIS' and 'ISO' layouts with helpful message
    - Raise ValueError for unknown layouts
    - _Requirements: 2.5, 4.1, 4.5_

  - [x] 2.4 Update _convert_key_event method
    - Look up key_code in self._key_map
    - Return KeyEvent with mapped TTK KeyCode if found
    - Fallback to character code point for unmapped printable ASCII (32-126)
    - Return None for completely unmapped keys
    - Include character in KeyEvent for convenience
    - _Requirements: 2.1, 2.6_

- [ ]* 2.5 Write unit tests for CoreGraphics mapping completeness
  - Test that MACOS_ANSI_KEY_MAP includes all letter keys
  - Test that MACOS_ANSI_KEY_MAP includes all digit keys
  - Test that MACOS_ANSI_KEY_MAP includes all symbol keys
  - Test that MACOS_ANSI_KEY_MAP includes all special keys
  - _Requirements: 2.2, 2.3_

- [ ]* 2.6 Write property test for CoreGraphics mapping correctness
  - **Property 4: CoreGraphics Mapping Correctness**
  - **Validates: Requirements 2.1**
  - For any macOS virtual key code in MACOS_ANSI_KEY_MAP
  - Verify _convert_key_event returns KeyEvent with correct TTK KeyCode
  - _Requirements: 2.1_

- [ ]* 2.7 Write property test for CoreGraphics error handling
  - **Property 5: CoreGraphics Graceful Error Handling**
  - **Validates: Requirements 2.6**
  - For any unmapped macOS virtual key code
  - Verify _convert_key_event returns None or valid KeyEvent without crashing
  - _Requirements: 2.6_

- [ ]* 2.8 Write unit tests for CoreGraphics keyboard layout selection
  - Test that default layout is ANSI
  - Test that 'ANSI' layout works
  - Test that 'JIS' layout raises NotImplementedError
  - Test that 'ISO' layout raises NotImplementedError
  - Test that unknown layout raises ValueError
  - _Requirements: 2.4, 2.5, 4.2, 4.3_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement curses key mapping system
  - [x] 4.1 Create CURSES_ANSI_KEY_MAP dictionary
    - Map lowercase letters (ord('a') through ord('z') to KEY_A through KEY_Z)
    - Map uppercase letters (ord('A') through ord('Z') to KEY_A through KEY_Z)
    - Map digit characters (ord('0') through ord('9') to KEY_0 through KEY_9)
    - Map unshifted symbols to their respective KEY_* values
    - Map shifted symbols to same physical keys (e.g., '!' to KEY_1)
    - Map space (ord(' ') to SPACE)
    - Include existing special key mappings
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 4.2 Add keyboard_layout parameter to CursesBackend.__init__
    - Accept keyboard_layout parameter (default: 'ANSI')
    - Store layout in instance variable
    - Call _get_key_map to initialize key mapping
    - _Requirements: 3.4, 4.2, 4.3_

  - [x] 4.3 Implement _get_key_map method
    - Return CURSES_ANSI_KEY_MAP for 'ANSI' layout
    - Raise ValueError for unknown layouts
    - _Requirements: 3.5, 4.1, 4.5_

  - [x] 4.4 Update _convert_key_event method
    - Detect Shift modifier for uppercase letters (ord('A') <= key <= ord('Z'))
    - Look up key in self._key_map
    - Return KeyEvent with mapped TTK KeyCode if found
    - Fallback to character code point for unmapped printable ASCII (32-126)
    - Return None for completely unmapped keys
    - Include character in KeyEvent for convenience
    - _Requirements: 3.1, 3.6, 1.7_

- [ ]* 4.5 Write unit tests for curses mapping completeness
  - Test that CURSES_ANSI_KEY_MAP includes all letter keys (both cases)
  - Test that CURSES_ANSI_KEY_MAP includes all digit keys
  - Test that CURSES_ANSI_KEY_MAP includes all symbol keys (both shifted and unshifted)
  - Test that CURSES_ANSI_KEY_MAP includes all special keys
  - _Requirements: 3.2, 3.3_

- [ ]* 4.6 Write property test for curses mapping correctness
  - **Property 6: Curses Mapping Correctness**
  - **Validates: Requirements 3.1**
  - For any curses key code in CURSES_ANSI_KEY_MAP
  - Verify _convert_key_event returns KeyEvent with correct TTK KeyCode
  - _Requirements: 3.1_

- [ ]* 4.7 Write property test for curses error handling
  - **Property 7: Curses Graceful Error Handling**
  - **Validates: Requirements 3.6**
  - For any unmapped curses key code
  - Verify _convert_key_event returns None or valid KeyEvent without crashing
  - _Requirements: 3.6_

- [ ]* 4.8 Write property test for Shift modifier consistency
  - **Property 2: Shift Modifier Consistency for Letters**
  - **Validates: Requirements 1.7**
  - For any letter key (KEY_A through KEY_Z)
  - Verify lowercase and uppercase produce same key_code with different modifiers
  - Test in curses backend where Shift detection is explicit
  - _Requirements: 1.7_

- [ ]* 4.9 Write unit tests for curses keyboard layout selection
  - Test that default layout is ANSI
  - Test that 'ANSI' layout works
  - Test that unknown layout raises ValueError
  - _Requirements: 3.4, 3.5, 4.2, 4.3_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Integration and documentation
  - [x] 6.1 Update KeyEvent usage examples in docstrings
    - Add examples showing letter keys with and without Shift
    - Add examples showing digit keys with and without Shift (symbols)
    - Add examples showing symbol keys
    - Add examples showing space key
    - _Requirements: 6.5_

  - [x] 6.2 Add keyboard layout documentation
    - Document ANSI layout as default
    - Document how to add new layouts (JIS, ISO)
    - Document the structure of mapping tables
    - Add comments about future layout support
    - _Requirements: 4.4, 5.3_

  - [x] 6.3 Update TTK documentation
    - Update API reference with new KeyCode entries
    - Update event handling guide with printable character examples
    - Document keyboard layout selection
    - Add migration guide for applications using character codes directly
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.2_

- [ ]* 6.4 Write integration tests
  - Test KeyEvent creation with new KeyCode values
  - Test that existing TTK applications continue to work
  - Test keyboard layout selection in both backends
  - Test modifier key combinations with new KeyCodes
  - _Requirements: 6.5, 4.2_

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Checkpoints ensure incremental validation
