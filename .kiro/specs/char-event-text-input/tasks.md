# Implementation Plan

- [x] 1. Add CharEvent class and EventCallback interface to TTK
- [x] 1.1 Add CharEvent class to ttk/input_event.py
  - Create CharEvent dataclass with char field
  - Add __repr__ method for debugging
  - _Requirements: 6.1_

- [x] 1.2 Add EventCallback interface to ttk/renderer.py
  - Define EventCallback base class with on_key_event, on_char_event, on_system_event methods
  - Add set_event_callback method to Renderer base class
  - _Requirements: 1.3, 4.2_

- [ ]* 1.3 Write unit tests for CharEvent
  - Test CharEvent creation with printable characters
  - Test __repr__ output
  - _Requirements: 6.1, 6.5_

- [x] 2. Implement callback system in curses backend
- [x] 2.1 Add callback support to CursesBackend
  - Add event_callback field to store callback
  - Implement set_event_callback method
  - _Requirements: 5.1, 5.3_

- [x] 2.2 Implement run_event_loop for curses backend
  - Create event loop that polls getch()
  - Generate KeyEvent for all input
  - Deliver KeyEvent via on_key_event callback
  - _Requirements: 1.2, 5.1_

- [x] 2.3 Implement KeyEvent to CharEvent translation in curses backend
  - Add _translate_key_to_char method
  - Check for command modifiers (Ctrl, Alt, Cmd)
  - Check for printable character in KeyEvent.char field
  - Generate CharEvent if conditions met
  - _Requirements: 2.1, 7.4, 7.5_

- [x] 2.4 Integrate translation into curses event loop
  - Call _translate_key_to_char when KeyEvent not consumed
  - Deliver CharEvent via on_char_event callback
  - _Requirements: 1.1, 2.2_

- [ ]* 2.5 Write unit tests for curses backend callback system
  - Test callback registration
  - Test KeyEvent delivery
  - Test CharEvent translation and delivery
  - Test modifier key handling
  - _Requirements: 5.1, 5.3_

- [x] 3. Implement callback system in CoreGraphics backend
- [x] 3.1 Add callback support to CoreGraphicsBackend
  - Add event_callback field to store callback
  - Implement set_event_callback method
  - _Requirements: 5.2, 5.4_

- [x] 3.2 Implement NSTextInputClient protocol in TTKView
  - Add hasMarkedText method (return False for now)
  - Add markedRange method (return NSNotFound for now)
  - Add selectedRange method
  - Add validAttributesForMarkedText method
  - _Requirements: 5.2_

- [x] 3.3 Implement keyDown: callback in TTKView
  - Translate NSEvent to KeyEvent
  - Deliver KeyEvent via on_key_event callback
  - If not consumed, call interpretKeyEvents:
  - _Requirements: 1.2, 5.2_

- [x] 3.4 Implement insertText: callback in TTKView
  - Extract character from NSString
  - Generate CharEvent for each character
  - Deliver CharEvent via on_char_event callback
  - _Requirements: 1.1, 2.2, 5.2_

- [x] 3.5 Implement run_event_loop for CoreGraphics backend
  - Set up NSApplication event loop
  - Integrate with existing window management
  - _Requirements: 5.2_

- [ ]* 3.6 Write unit tests for CoreGraphics backend callback system
  - Test callback registration
  - Test keyDown: → KeyEvent delivery
  - Test insertText: → CharEvent delivery
  - Test NSTextInputClient protocol methods
  - _Requirements: 5.2, 5.4_

- [x] 4. Update SingleLineTextEdit to handle CharEvent
- [x] 4.1 Add CharEvent handling to handle_key method
  - Add isinstance check for CharEvent
  - Call insert_char for CharEvent
  - _Requirements: 2.2, 4.2_

- [x] 4.2 Remove printable character handling from KeyEvent branch
  - Remove event.is_printable() check from KeyEvent handling
  - Keep only navigation and editing commands in KeyEvent branch
  - _Requirements: 4.4_

- [ ]* 4.3 Write unit tests for SingleLineTextEdit CharEvent handling
  - Test CharEvent insertion
  - Test cursor position after CharEvent
  - Test KeyEvent navigation commands still work
  - _Requirements: 2.2, 4.4_

- [x] 5. Implement TFMEventCallback for application layer
- [x] 5.1 Create TFMEventCallback class
  - Implement on_key_event to call handle_command
  - Implement on_char_event to pass to active text widget
  - Implement on_system_event for resize and close
  - _Requirements: 3.3, 4.3_

- [x] 5.2 Update command handlers to return consumption status
  - Modify handle_command to return True when command is consumed
  - Return False when command is not recognized
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 5.3 Integrate TFMEventCallback into main loop
  - Create TFMEventCallback instance
  - Call backend.set_event_callback
  - Call backend.run_event_loop
  - _Requirements: 1.3, 4.2_

- [ ]* 5.4 Write integration tests for TFMEventCallback
  - Test command consumption (Q to quit, A to select all)
  - Test unconsumed KeyEvent → CharEvent flow
  - Test text input in SingleLineTextEdit
  - _Requirements: 3.1, 3.2, 3.3, 2.2_

- [x] 6. Maintain backward compatibility with get_event()
- [x] 6.1 Update get_event() to work with callbacks
  - Check if event_callback is set
  - If set, process events but return None
  - If not set, use traditional polling
  - _Requirements: 1.2_

- [x] 6.2 Add _process_events helper method
  - Process one event cycle
  - Deliver via callbacks if enabled
  - Used by get_event() when callbacks are enabled
  - _Requirements: 1.2_

- [ ]* 6.3 Write tests for backward compatibility
  - Test get_event() without callbacks (traditional mode)
  - Test get_event() with callbacks (returns None)
  - Test mixed usage scenarios
  - _Requirements: 1.2_

- [x] 7. Update existing code to use isinstance checks
- [x] 7.1 Audit codebase for event type assumptions
  - Search for event.char usage
  - Search for event.key_code usage
  - Identify code that assumes KeyEvent
  - _Requirements: 4.1_

- [x] 7.2 Add isinstance checks where needed
  - Add isinstance(event, KeyEvent) checks
  - Add isinstance(event, CharEvent) checks
  - Handle both event types appropriately
  - _Requirements: 4.1, 4.2_

- [ ]* 7.3 Write tests for isinstance checks
  - Test code correctly distinguishes event types
  - Test code handles both KeyEvent and CharEvent
  - _Requirements: 4.1, 4.2_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Update documentation
- [x] 9.1 Update TTK documentation
  - Document CharEvent class
  - Document EventCallback interface
  - Document callback-based event system
  - Document backward compatibility with get_event()
  - _Requirements: 6.4_

- [x] 9.2 Update TFM documentation
  - Document event handling changes
  - Document migration guide from polling to callbacks
  - Document best practices for event handling
  - _Requirements: 6.4_

- [x] 10. Final integration testing
- [ ]* 10.1 Test terminal mode end-to-end
  - Test command execution (Q, A, arrows, etc.)
  - Test text input in dialogs
  - Test mixed command and text input
  - _Requirements: 3.1, 3.2, 3.3, 2.2_

- [ ]* 10.2 Test desktop mode end-to-end
  - Test command execution with keyboard shortcuts
  - Test text input in dialogs
  - Test mixed command and text input
  - Test window resize and close events
  - _Requirements: 3.1, 3.2, 3.3, 2.2, 5.2, 5.4_

- [ ]* 10.3 Test backend consistency
  - Compare terminal and desktop mode behavior
  - Verify same input produces same results
  - _Requirements: 5.5_

- [x] 11. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement UTF-8 byte accumulation in curses backend
- [ ] 12.1 Add UTF8Accumulator class to curses backend
  - Create UTF8Accumulator class with buffer and expected_bytes tracking
  - Implement add_byte method with UTF-8 validation logic
  - Implement reset method to clear accumulator state
  - Implement is_accumulating method to check buffer status
  - _Requirements: 8.1, 8.3_

- [ ] 12.2 Integrate UTF8Accumulator into curses event loop
  - Add utf8_accumulator instance to CursesBackend
  - Call add_byte for each getch() result
  - Generate CharEvent only when complete character is formed
  - Skip KeyEvent generation for multi-byte characters
  - _Requirements: 8.2, 8.5_

- [ ] 12.3 Handle invalid UTF-8 sequences
  - Catch UnicodeDecodeError in UTF8Accumulator
  - Reset accumulator on invalid sequences
  - Continue processing without generating events
  - _Requirements: 8.4_

- [ ]* 12.4 Write property test for UTF-8 accumulation
  - **Property 11: Multi-byte UTF-8 sequences form single CharEvent**
  - **Validates: Requirements 8.1, 8.2**

- [ ]* 12.5 Write property test for UTF-8 buffering
  - **Property 12: Incomplete UTF-8 sequences are buffered**
  - **Validates: Requirements 8.3**

- [ ]* 12.6 Write property test for invalid UTF-8 handling
  - **Property 13: Invalid UTF-8 sequences are discarded**
  - **Validates: Requirements 8.4**

- [ ]* 12.7 Write property test for no KeyEvents during accumulation
  - **Property 14: No KeyEvents for UTF-8 continuation bytes**
  - **Validates: Requirements 8.5**

- [ ] 13. Implement caret position management
- [ ] 13.1 Add caret position methods to Renderer base class
  - Add set_caret_position(x, y) method signature
  - Add hide_caret() method signature
  - Add show_caret() method signature
  - _Requirements: 9.1_

- [ ] 13.2 Implement caret position methods in CursesBackend
  - Implement set_caret_position using curses.setsyx()
  - Implement hide_caret using curses.curs_set(0)
  - Implement show_caret using curses.curs_set(1)
  - Handle curses.error exceptions gracefully
  - _Requirements: 9.1, 9.2_

- [ ] 13.3 Implement caret position methods in CoreGraphicsBackend
  - Implement set_caret_position as no-op (OS handles caret)
  - Implement hide_caret as no-op
  - Implement show_caret as no-op
  - _Requirements: 9.1_

- [ ] 13.4 Integrate caret positioning into SingleLineTextEdit
  - Update draw() method to call set_caret_position after rendering
  - Calculate caret position from widget coordinates and cursor offset
  - Call show_caret() when widget has focus
  - Call hide_caret() when widget loses focus
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ]* 13.5 Write property test for caret position matching
  - **Property 15: Caret position matches cursor position**
  - **Validates: Requirements 9.1, 9.3**

- [ ]* 13.6 Write property test for caret updates
  - **Property 16: Caret updates on cursor movement**
  - **Validates: Requirements 9.2**

- [ ]* 13.7 Write property test for caret hiding on focus loss
  - **Property 17: Caret hidden when widget loses focus**
  - **Validates: Requirements 9.4**

- [ ]* 13.8 Write property test for caret rendering order
  - **Property 18: Caret set after widget rendering**
  - **Validates: Requirements 9.5**

- [ ] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Integration testing for Unicode input
- [ ]* 15.1 Test Japanese character input (hiragana, katakana, kanji)
  - Test typing あ, い, う, え, お
  - Test typing カ, タ, ナ, ハ, マ
  - Test typing 日, 本, 語
  - Verify single CharEvent per character
  - _Requirements: 8.1, 8.2_

- [ ]* 15.2 Test other multi-byte Unicode characters
  - Test emoji input (😀, 🎉, etc.)
  - Test accented characters (é, ñ, ü, etc.)
  - Test Chinese characters
  - Test Korean characters
  - _Requirements: 8.1, 8.2_

- [ ]* 15.3 Test caret position with Unicode characters
  - Test caret positioning with mixed ASCII and Unicode
  - Test caret movement through Unicode text
  - Verify caret position accounts for character width
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 16. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
