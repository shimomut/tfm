# Implementation Plan

- [x] 1. Add IME state tracking to TTKView
  - Add instance variables for marked_text, marked_range, and selected_range in initWithFrame_backend_
  - Initialize marked_range with NSNotFound location
  - Initialize selected_range as zero-length range
  - _Requirements: 3.2, 3.3, 5.1_

- [x] 2. Implement basic NSTextInputClient protocol methods
- [x] 2.1 Implement hasMarkedText method
  - Return True if marked_range.location != NSNotFound
  - _Requirements: 3.2_

- [x] 2.2 Implement markedRange method
  - Return the current marked_range
  - _Requirements: 3.2_

- [x] 2.3 Implement selectedRange method
  - Return the current selected_range
  - _Requirements: 3.3_

- [x] 2.4 Implement validAttributesForMarkedText method
  - Return empty array for basic support
  - _Requirements: 3.1_

- [x] 3. Implement composition text handling
- [x] 3.1 Implement setMarkedText_selectedRange_replacementRange_ method
  - Extract plain text from NSString or NSAttributedString
  - Update marked_text instance variable
  - Update marked_range based on text length
  - Store selected_range parameter
  - Trigger redraw via setNeedsDisplay_(True)
  - _Requirements: 3.4, 5.1_

- [x] 3.2 Implement unmarkText method
  - Clear marked_text to empty string
  - Reset marked_range to NSNotFound location
  - Reset selected_range to zero-length
  - Trigger redraw via setNeedsDisplay_(True)
  - _Requirements: 5.4, 5.5, 7.3_

- [x] 3.3 Add marked text rendering in drawRect_ method
  - Render marked text at cursor position after cursor drawing
  - Use yellow background (RGB: 255, 255, 200) for composition text
  - Add underline to match macOS IME conventions
  - Add debug output when TFM_DEBUG=1
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 4. Implement text commit handling
- [x] 4.1 Implement insertText_ method
  - Clear marked text state by calling unmarkText
  - Extract plain text from NSString or NSAttributedString
  - Generate CharEvent for each character in the text
  - Deliver CharEvent via backend.event_callback.on_char_event()
  - Trigger redraw via setNeedsDisplay_(True)
  - _Requirements: 1.5, 3.5, 6.1, 6.2_

- [ ]* 4.2 Write property test for CharEvent generation
  - **Property 1: IME committed text generates CharEvent**
  - **Validates: Requirements 1.5, 6.1, 6.2**

- [x] 5. Add cursor position tracking to CoreGraphicsBackend
- [x] 5.1 Add cursor_row and cursor_col instance variables
  - Initialize to 0 in __init__
  - _Requirements: 2.4, 4.1_

- [x] 5.2 Implement set_cursor_position method
  - Accept row and col parameters
  - Clamp row to [0, rows-1]
  - Clamp col to [0, cols-1]
  - Store in cursor_row and cursor_col
  - _Requirements: 2.4, 2.5, 4.4_

- [x] 5.3 Fix set_caret_position to actually update cursor position
  - Changed from no-op to call set_cursor_position(y, x)
  - Note: x is column, y is row in TTK convention
  - Fixes both marked text rendering and candidate window positioning
  - _Requirements: 2.4, 2.5, 4.1, 4.2, 4.4_

- [ ]* 5.4 Write property test for cursor position clamping
  - **Property 2: Cursor position determines IME overlay position**
  - **Validates: Requirements 2.4, 2.5, 4.1, 4.2**

- [x] 6. Implement IME positioning
- [x] 6.1 Implement firstRectForCharacterRange_actualRange_ method
  - Get cursor position from backend.cursor_row and backend.cursor_col
  - Convert to pixel coordinates using char_width and char_height
  - Apply coordinate system transformation (TTK to CoreGraphics)
  - Create NSRect at cursor position with character dimensions
  - Convert from view coordinates to screen coordinates
  - Fill actual_range parameter if not None
  - Return screen rectangle
  - _Requirements: 2.4, 2.5, 4.1, 4.2, 4.3, 4.4_

- [x] 6.2 Fix PyObjC pointer assignment error in firstRectForCharacterRange_actualRange_
  - Wrap actual_range assignment in try-except block
  - Handle TypeError/AttributeError gracefully
  - Allow method to complete successfully and return correct coordinates
  - Add debug output when TFM_DEBUG=1
  - _Requirements: 4.1, 4.2, 4.3_
  - _Note: actual_range is optional; macOS uses char_range if not set_

- [ ]* 6.3 Write unit test for coordinate conversion
  - Test TTK to CoreGraphics coordinate transformation
  - Test view to screen coordinate conversion
  - Test with various cursor positions
  - _Requirements: 4.1, 4.2_

- [x] 7. Implement font information for IME
- [x] 7.1 Implement attributedSubstringForProposedRange_actualRange_ method
  - Create attributes dictionary with NSFontAttributeName set to backend.font
  - Create NSAttributedString with single space character and attributes
  - Fill actual_range parameter if not None
  - Return attributed string
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 7.2 Write property test for font matching
  - **Property 3: Font size matches application font**
  - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 8. Update keyDown_ method for IME integration
- [x] 8.1 Modify keyDown_ to call interpretKeyEvents_
  - Generate KeyEvent from NSEvent (existing code)
  - Deliver KeyEvent to application via callback
  - If consumed, return early without IME processing
  - If not consumed, call interpretKeyEvents_ with event array
  - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 8.2 Write unit test for command key handling during composition
  - Test Cmd+C during composition doesn't commit
  - Test Cmd+V during composition cancels composition
  - Test Escape during composition cancels composition
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 9. Add error handling
- [x] 9.1 Add bounds checking in set_cursor_position
  - Log warning if position is significantly out of bounds
  - Clamp to valid range
  - _Requirements: 2.4_

- [x] 9.2 Add null checks in insertText_
  - Check if event_callback exists before generating CharEvent
  - Log warning in debug mode if callback is None
  - _Requirements: 6.1_

- [x] 9.3 Add null checks in firstRectForCharacterRange_actualRange_
  - Check if window exists before coordinate conversion
  - Return zero rect at origin if window is None
  - Log warning about missing window
  - _Requirements: 4.1_

- [x] 9.4 Add null checks in attributedSubstringForProposedRange_actualRange_
  - Check if backend.font exists
  - Return None if font is None
  - Log warning about missing font
  - _Requirements: 2.1_

- [x] 9.5 Suppress PyObjC pointer warnings
  - Add warning filter for objc.ObjCPointerWarning
  - Prevents harmless warnings about pointer creation in NSTextInputClient methods
  - _Note: Warnings are expected PyObjC behavior and don't affect functionality_

- [x] 9.6 Implement debug mode for TFM
  - Add dual output to LogCapture class (log pane + terminal)
  - Pass debug_mode flag from TFM_DEBUG environment variable
  - Enable with --debug flag or TFM_DEBUG=1
  - _Note: Allows seeing stdout/stderr in both log pane and terminal_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Debug and fix IME rendering issues
- [x] 11.1 Fix composition text rendering
  - Added marked text rendering in drawRect_ method
  - Renders at cursor position with yellow background
  - Adds underline to match macOS conventions
  - _Requirements: 9.1, 9.2_

- [x] 11.2 Fix composition text positioning
  - Fixed set_caret_position to actually update cursor position
  - Changed from no-op to call set_cursor_position(y, x)
  - Fixes marked text rendering at correct location
  - _Requirements: 2.4, 2.5, 4.1, 4.2_

- [x] 11.3 Fix candidate window positioning
  - Added debug output to trace coordinate transformations
  - Discovered PyObjC pointer assignment error in firstRectForCharacterRange_actualRange_
  - Wrapped actual_range assignment in try-except block
  - Allows method to complete and return correct screen coordinates
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 11.4 Add comprehensive debug output
  - Added debug output for marked text rendering (when TFM_DEBUG=1)
  - Added debug output for coordinate transformations (when TFM_DEBUG=1)
  - Added debug output for PyObjC pointer handling (when TFM_DEBUG=1)
  - _Note: Helps troubleshoot IME issues during development_

- [ ]* 12. Create integration test for Japanese IME
  - Test hiragana input and kanji conversion
  - Test composition text positioning
  - Test candidate window appearance
  - Test text commitment
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 10.1_

- [ ]* 12. Create integration test for Chinese IME
  - Test pinyin input and character selection
  - Test composition text positioning
  - Test candidate window appearance
  - Test text commitment
  - _Requirements: 10.2_

- [ ]* 13. Create integration test for Korean IME
  - Test hangul composition
  - Test composition text positioning
  - Test text commitment
  - _Requirements: 10.3_

- [ ]* 14. Create integration test for multi-language IME switching
  - Test switching between Japanese, Chinese, and Korean IME
  - Test that each IME works correctly after switching
  - _Requirements: 10.5_

- [ ]* 15. Create demo script for IME testing
  - Create demo that shows text input with IME support
  - Include instructions for testing with different IME languages
  - Show composition text and committed text
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 16. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
