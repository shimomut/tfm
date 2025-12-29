# Implementation Plan: Clipboard Support

## Overview

This plan implements clipboard (pasteboard) support for TTK, enabling applications to read from and write to the system clipboard. The implementation adds three methods to the Renderer base class and provides backend-specific implementations for CoreGraphics (desktop mode) and Curses (terminal mode).

## Tasks

- [x] 1. Add clipboard methods to Renderer base class
  - Add `supports_clipboard()` abstract method to `ttk/renderer.py`
  - Add `get_clipboard_text()` abstract method to `ttk/renderer.py`
  - Add `set_clipboard_text()` abstract method to `ttk/renderer.py`
  - Include comprehensive docstrings with examples
  - _Requirements: 3.4, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 1.1 Write unit tests for Renderer interface
  - Test that abstract methods are defined
  - Test that subclasses must implement all three methods
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 2. Implement clipboard support in CoreGraphics backend
  - [x] 2.1 Implement `supports_clipboard()` in `ttk/backends/coregraphics_backend.py`
    - Return True (desktop mode supports clipboard)
    - _Requirements: 3.1_

  - [x] 2.2 Implement `get_clipboard_text()` in `ttk/backends/coregraphics_backend.py`
    - Use `Cocoa.NSPasteboard.generalPasteboard()` to access system clipboard
    - Retrieve text using `stringForType_(Cocoa.NSPasteboardTypeString)`
    - Return empty string if clipboard is empty or contains no text
    - Handle errors gracefully (return empty string, log error)
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.3_

  - [x] 2.3 Implement `set_clipboard_text()` in `ttk/backends/coregraphics_backend.py`
    - Use `Cocoa.NSPasteboard.generalPasteboard()` to access system clipboard
    - Clear existing content with `clearContents()`
    - Write text using `setString_forType_(text, Cocoa.NSPasteboardTypeString)`
    - Return True on success, False on failure
    - Handle errors gracefully (return False, log error)
    - _Requirements: 2.1, 2.2, 2.3, 4.2, 4.3_

- [ ]* 2.4 Write unit tests for CoreGraphics clipboard
  - Test `supports_clipboard()` returns True
  - Test reading empty clipboard returns empty string
  - Test writing and reading simple text
  - Test writing and reading text with newlines
  - Test writing and reading text with tabs
  - Test writing and reading Unicode/emoji
  - Test writing empty string clears clipboard
  - Test error handling (graceful degradation)
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ]* 2.5 Write property test for clipboard round trip
  - **Property 3: Clipboard Write Round Trip**
  - **Validates: Requirements 2.1, 2.3**
  - Generate random UTF-8 strings (including special characters)
  - Write to clipboard, then read back
  - Verify returned string equals original string
  - Run with minimum 100 iterations

- [ ]* 2.6 Write property test for special characters preservation
  - **Property 5: Special Characters Preserved**
  - **Validates: Requirements 2.3**
  - Generate strings with newlines, tabs, Unicode, emoji
  - Write to clipboard, then read back
  - Verify all characters preserved exactly
  - Run with minimum 100 iterations

- [x] 3. Implement clipboard stubs in Curses backend
  - [x] 3.1 Implement `supports_clipboard()` in `ttk/backends/curses_backend.py`
    - Return False (terminal mode doesn't support clipboard)
    - _Requirements: 3.2_

  - [x] 3.2 Implement `get_clipboard_text()` in `ttk/backends/curses_backend.py`
    - Return empty string (stub implementation)
    - _Requirements: 1.4_

  - [x] 3.3 Implement `set_clipboard_text()` in `ttk/backends/curses_backend.py`
    - Return False (stub implementation)
    - _Requirements: 2.4_

- [ ]* 3.4 Write unit tests for Curses clipboard stubs
  - Test `supports_clipboard()` returns False
  - Test `get_clipboard_text()` returns empty string
  - Test `set_clipboard_text()` returns False
  - Test operations don't raise exceptions
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ]* 3.5 Write property test for terminal mode graceful degradation
  - **Property 6: Terminal Mode Graceful Degradation**
  - **Validates: Requirements 1.4, 2.4, 3.2, 3.3**
  - Generate random strings and operations
  - Test all operations complete without exceptions
  - Test reads always return empty string
  - Test writes always return False
  - Run with minimum 100 iterations

- [x] 4. Create interactive demo application
  - Create `ttk/demo/demo_clipboard.py`
  - Demonstrate reading from clipboard
  - Demonstrate writing to clipboard
  - Show behavior in both desktop and terminal modes
  - Include instructions for manual testing
  - _Requirements: 5.5_

- [x] 5. Create documentation
  - Create `ttk/doc/CLIPBOARD_FEATURE.md` (end-user documentation)
  - Document API usage with examples
  - Document backend support (desktop vs terminal)
  - Document limitations (plain-text only initially)
  - Include troubleshooting section
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Checkpoint - Ensure all tests pass
  - Run all unit tests: `pytest ttk/test/test_*clipboard*.py -v`
  - Run all property tests with 100+ iterations
  - Verify demo application works in desktop mode
  - Verify graceful degradation in terminal mode
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation follows TTK's existing architectural patterns
- Desktop mode (CoreGraphics) provides full clipboard functionality
- Terminal mode (Curses) provides graceful degradation with stub implementations
