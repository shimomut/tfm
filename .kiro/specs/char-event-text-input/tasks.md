# Implementation Plan

- [ ] 1. Add CharEvent class and EventCallback interface to TTK
- [ ] 1.1 Add CharEvent class to ttk/input_event.py
  - Create CharEvent dataclass with char field
  - Add __repr__ method for debugging
  - _Requirements: 6.1_

- [ ] 1.2 Add EventCallback interface to ttk/renderer.py
  - Define EventCallback base class with on_key_event, on_char_event, on_system_event methods
  - Add set_event_callback method to Renderer base class
  - _Requirements: 1.3, 4.2_

- [ ]* 1.3 Write unit tests for CharEvent
  - Test CharEvent creation with printable characters
  - Test __repr__ output
  - _Requirements: 6.1, 6.5_

- [ ] 2. Implement callback system in curses backend
- [ ] 2.1 Add callback support to CursesBackend
  - Add event_callback field to store callback
  - Implement set_event_callback method
  - _Requirements: 5.1, 5.3_

- [ ] 2.2 Implement run_event_loop for curses backend
  - Create event loop that polls getch()
  - Generate KeyEvent for all input
  - Deliver KeyEvent via on_key_event callback
  - _Requirements: 1.2, 5.1_

- [ ] 2.3 Implement KeyEvent to CharEvent translation in curses backend
  - Add _translate_key_to_char method
  - Check for command modifiers (Ctrl, Alt, Cmd)
  - Check for printable character in KeyEvent.char field
  - Generate CharEvent if conditions met
  - _Requirements: 2.1, 7.4, 7.5_

- [ ] 2.4 Integrate translation into curses event loop
  - Call _translate_key_to_char when KeyEvent not consumed
  - Deliver CharEvent via on_char_event callback
  - _Requirements: 1.1, 2.2_

- [ ]* 2.5 Write unit tests for curses backend callback system
  - Test callback registration
  - Test KeyEvent delivery
  - Test CharEvent translation and delivery
  - Test modifier key handling
  - _Requirements: 5.1, 5.3_

- [ ] 3. Implement callback system in CoreGraphics backend
- [ ] 3.1 Add callback support to CoreGraphicsBackend
  - Add event_callback field to store callback
  - Implement set_event_callback method
  - _Requirements: 5.2, 5.4_

- [ ] 3.2 Implement NSTextInputClient protocol in TTKView
  - Add hasMarkedText method (return False for now)
  - Add markedRange method (return NSNotFound for now)
  - Add selectedRange method
  - Add validAttributesForMarkedText method
  - _Requirements: 5.2_

- [ ] 3.3 Implement keyDown: callback in TTKView
  - Translate NSEvent to KeyEvent
  - Deliver KeyEvent via on_key_event callback
  - If not consumed, call interpretKeyEvents:
  - _Requirements: 1.2, 5.2_

- [ ] 3.4 Implement insertText: callback in TTKView
  - Extract character from NSString
  - Generate CharEvent for each character
  - Deliver CharEvent via on_char_event callback
  - _Requirements: 1.1, 2.2, 5.2_

- [ ] 3.5 Implement run_event_loop for CoreGraphics backend
  - Set up NSApplication event loop
  - Integrate with existing window management
  - _Requirements: 5.2_

- [ ]* 3.6 Write unit tests for CoreGraphics backend callback system
  - Test callback registration
  - Test keyDown: → KeyEvent delivery
  - Test insertText: → CharEvent delivery
  - Test NSTextInputClient protocol methods
  - _Requirements: 5.2, 5.4_

- [ ] 4. Update SingleLineTextEdit to handle CharEvent
- [ ] 4.1 Add CharEvent handling to handle_key method
  - Add isinstance check for CharEvent
  - Call insert_char for CharEvent
  - _Requirements: 2.2, 4.2_

- [ ] 4.2 Remove printable character handling from KeyEvent branch
  - Remove event.is_printable() check from KeyEvent handling
  - Keep only navigation and editing commands in KeyEvent branch
  - _Requirements: 4.4_

- [ ]* 4.3 Write unit tests for SingleLineTextEdit CharEvent handling
  - Test CharEvent insertion
  - Test cursor position after CharEvent
  - Test KeyEvent navigation commands still work
  - _Requirements: 2.2, 4.4_

- [ ] 5. Implement TFMEventCallback for application layer
- [ ] 5.1 Create TFMEventCallback class
  - Implement on_key_event to call handle_command
  - Implement on_char_event to pass to active text widget
  - Implement on_system_event for resize and close
  - _Requirements: 3.3, 4.3_

- [ ] 5.2 Update command handlers to return consumption status
  - Modify handle_command to return True when command is consumed
  - Return False when command is not recognized
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 5.3 Integrate TFMEventCallback into main loop
  - Create TFMEventCallback instance
  - Call backend.set_event_callback
  - Call backend.run_event_loop
  - _Requirements: 1.3, 4.2_

- [ ]* 5.4 Write integration tests for TFMEventCallback
  - Test command consumption (Q to quit, A to select all)
  - Test unconsumed KeyEvent → CharEvent flow
  - Test text input in SingleLineTextEdit
  - _Requirements: 3.1, 3.2, 3.3, 2.2_

- [ ] 6. Maintain backward compatibility with get_event()
- [ ] 6.1 Update get_event() to work with callbacks
  - Check if event_callback is set
  - If set, process events but return None
  - If not set, use traditional polling
  - _Requirements: 1.2_

- [ ] 6.2 Add _process_events helper method
  - Process one event cycle
  - Deliver via callbacks if enabled
  - Used by get_event() when callbacks are enabled
  - _Requirements: 1.2_

- [ ]* 6.3 Write tests for backward compatibility
  - Test get_event() without callbacks (traditional mode)
  - Test get_event() with callbacks (returns None)
  - Test mixed usage scenarios
  - _Requirements: 1.2_

- [ ] 7. Update existing code to use isinstance checks
- [ ] 7.1 Audit codebase for event type assumptions
  - Search for event.char usage
  - Search for event.key_code usage
  - Identify code that assumes KeyEvent
  - _Requirements: 4.1_

- [ ] 7.2 Add isinstance checks where needed
  - Add isinstance(event, KeyEvent) checks
  - Add isinstance(event, CharEvent) checks
  - Handle both event types appropriately
  - _Requirements: 4.1, 4.2_

- [ ]* 7.3 Write tests for isinstance checks
  - Test code correctly distinguishes event types
  - Test code handles both KeyEvent and CharEvent
  - _Requirements: 4.1, 4.2_

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Update documentation
- [ ] 9.1 Update TTK documentation
  - Document CharEvent class
  - Document EventCallback interface
  - Document callback-based event system
  - Document backward compatibility with get_event()
  - _Requirements: 6.4_

- [ ] 9.2 Update TFM documentation
  - Document event handling changes
  - Document migration guide from polling to callbacks
  - Document best practices for event handling
  - _Requirements: 6.4_

- [ ] 10. Final integration testing
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

- [ ] 11. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
