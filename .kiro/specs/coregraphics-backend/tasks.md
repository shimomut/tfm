# Implementation Plan

- [x] 1. Set up CoreGraphics backend file structure and dependencies
  - Create `ttk/backends/coregraphics_backend.py` file
  - Add PyObjC import with availability check
  - Import required Cocoa, Quartz, and objc modules
  - Import TTK base classes (Renderer, TextAttribute, InputEvent, KeyCode, ModifierKey)
  - _Requirements: 1.1, 1.5_

- [x] 2. Implement CoreGraphicsBackend class initialization
  - Create CoreGraphicsBackend class inheriting from Renderer
  - Implement `__init__` with window_title, font_name, and font_size parameters
  - Initialize instance variables (window, view, font, dimensions, grid, color_pairs)
  - _Requirements: 1.1, 1.4, 17.1_

- [x] 3. Implement font loading and character dimension calculation
  - Implement font loading using NSFont.fontWithName_size_
  - Add font validation to ensure font exists
  - Calculate character width and height using NSAttributedString
  - Add 20% line spacing to character height
  - Store char_width and char_height as instance variables
  - _Requirements: 3.1, 3.2, 3.5_

- [ ]* 3.1 Write property test for fixed character dimensions
  - **Property 3: Fixed Character Dimension Consistency**
  - **Validates: Requirements 3.3**

- [x] 4. Implement window creation and setup
  - Calculate window dimensions from grid size and character dimensions
  - Create NSWindow with calculated frame and style mask
  - Set window title from initialization parameter
  - Configure window to support close, minimize, and resize
  - _Requirements: 1.1, 7.1, 7.2_

- [ ]* 4.1 Write property test for window title preservation
  - **Property 8: Window Title Preservation**
  - **Validates: Requirements 7.1**

- [ ] 5. Implement character grid initialization
  - Calculate grid dimensions (default 80x24)
  - Create 2D list for character grid
  - Initialize each cell with (space, 0, 0) tuple
  - Initialize default color pair (0) with white on black
  - _Requirements: 2.1, 4.5_

- [ ]* 5.1 Write property test for grid positioning consistency
  - **Property 1: Character Grid Positioning Consistency**
  - **Validates: Requirements 1.3, 2.2**

- [ ] 6. Implement TTKView custom NSView class
  - Create TTKView class as NSView subclass
  - Implement initWithFrame_backend_ to store backend reference
  - Implement acceptsFirstResponder to return True for keyboard input
  - _Requirements: 8.1, 8.5, 6.5_

- [ ] 7. Implement TTKView drawRect_ rendering method
  - Implement drawRect_ to iterate through character grid
  - Skip empty cells (space with color pair 0) for performance
  - Calculate pixel positions using coordinate transformation
  - Draw background rectangles for each cell
  - Create NSAttributedString for each character with font and color
  - Draw characters at calculated positions
  - _Requirements: 8.2, 8.3, 9.3, 9.4, 9.5_

- [ ]* 7.1 Write property test for coordinate transformation
  - **Property 10: Y-Axis Coordinate Transformation**
  - **Property 11: X-Axis Coordinate Transformation**
  - **Validates: Requirements 9.3, 9.4, 9.5**

- [ ] 8. Implement text attribute support in rendering
  - Handle bold attribute using NSFontManager.convertFont_toHaveTrait_
  - Handle underline attribute using NSUnderlineStyleAttributeName
  - Handle reverse video by swapping foreground and background colors
  - Support combining multiple attributes simultaneously
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 8.1 Write property test for attribute combinations
  - **Property 5: Attribute Combination Support**
  - **Validates: Requirements 5.4**

- [ ] 9. Implement color pair management
  - Implement init_color_pair() to store RGB color pairs
  - Validate color pair ID is in range 1-255
  - Validate RGB components are in range 0-255
  - Store color pairs in dictionary
  - _Requirements: 4.1, 4.2, 12.3_

- [ ]* 9.1 Write property test for color pair storage
  - **Property 4: Color Pair Storage Integrity**
  - **Validates: Requirements 4.1**

- [ ]* 9.2 Write property test for color pair range validation
  - **Property 15: Color Pair Range Validation**
  - **Validates: Requirements 12.3**

- [ ] 10. Implement drawing operations
  - Implement draw_text() to update character grid cells
  - Implement clear() to reset all cells to spaces
  - Implement clear_region() to reset specified rectangular region
  - Implement draw_hline() to draw horizontal lines
  - Implement draw_vline() to draw vertical lines
  - Implement draw_rect() for filled and outlined rectangles
  - Handle out-of-bounds coordinates gracefully without crashing
  - _Requirements: 2.2, 2.5, 10.1, 10.2_

- [ ]* 10.1 Write property test for selective grid updates
  - **Property 12: Selective Grid Updates**
  - **Validates: Requirements 10.2**

- [ ]* 10.2 Write property test for out-of-bounds safety
  - **Property 2: Out-of-Bounds Safety**
  - **Validates: Requirements 2.5**

- [ ] 11. Implement display refresh operations
  - Implement refresh() to call view.setNeedsDisplay_(True)
  - Implement refresh_region() to mark region for redraw
  - Connect view to window as content view
  - Show window with makeKeyAndOrderFront_
  - _Requirements: 8.4, 10.3_

- [ ] 12. Implement window dimension queries
  - Implement get_dimensions() to return (rows, cols)
  - Ensure dimensions are always positive integers
  - _Requirements: 7.3_

- [ ]* 12.1 Write property test for dimension consistency
  - **Property 9: Dimension Query Consistency**
  - **Validates: Requirements 7.3**

- [ ] 13. Implement keyboard input handling
  - Implement get_input() with timeout support
  - Use NSApp.nextEventMatchingMask_untilDate_inMode_dequeue_ for event retrieval
  - Support blocking mode (timeout=-1) with NSDate.distantFuture
  - Support non-blocking mode (timeout=0) with None date
  - Support timed mode (timeout>0) with NSDate.dateWithTimeIntervalSinceNow_
  - Dispatch events using NSApp.sendEvent_
  - _Requirements: 6.4, 13.1, 13.2, 13.3, 13.5_

- [ ] 14. Implement input event translation
  - Implement _translate_event() to convert NSEvent to InputEvent
  - Extract key code from NSEvent
  - Extract character from NSEvent
  - Translate modifier flags to ModifierKey mask
  - Map NSEventModifierFlagShift to ModifierKey.SHIFT
  - Map NSEventModifierFlagControl to ModifierKey.CONTROL
  - Map NSEventModifierFlagOption to ModifierKey.ALT
  - Map NSEventModifierFlagCommand to ModifierKey.COMMAND
  - Return InputEvent with key_code, char, and modifiers
  - _Requirements: 6.1, 6.2, 6.3_

- [ ]* 14.1 Write property test for input event translation
  - **Property 6: Input Event Translation Completeness**
  - **Validates: Requirements 6.1**

- [ ]* 14.2 Write property test for modifier key detection
  - **Property 7: Modifier Key Detection**
  - **Validates: Requirements 6.2**

- [ ] 15. Implement cursor management
  - Implement set_cursor_visibility() to show/hide cursor
  - Implement move_cursor() to position cursor
  - _Requirements: Renderer interface_

- [ ] 16. Implement shutdown and cleanup
  - Implement shutdown() to close window
  - Set window and view references to None
  - Handle cleanup gracefully even if errors occur
  - _Requirements: 7.5_

- [ ] 17. Implement error handling for initialization
  - Check PyObjC availability and raise RuntimeError with installation instructions
  - Validate font exists and raise ValueError if not found
  - Validate window creation and raise RuntimeError if it fails
  - _Requirements: 12.1, 12.2, 12.5_

- [ ] 18. Implement error handling for runtime operations
  - Validate color pair IDs and raise ValueError for out-of-range
  - Validate RGB components and raise ValueError for out-of-range
  - Handle drawing operation failures with warnings but no crashes
  - _Requirements: 12.3, 12.4_

- [ ]* 18.1 Write property test for exception type consistency
  - **Property 18: Exception Type Consistency**
  - **Validates: Requirements 17.4**

- [ ] 19. Add comprehensive docstrings and comments
  - Add module-level docstring explaining CoreGraphics backend
  - Add class-level docstrings for CoreGraphicsBackend and TTKView
  - Add method-level docstrings for all public methods
  - Add inline comments explaining coordinate transformation
  - Add inline comments explaining PyObjC method name translations
  - _Requirements: 14.5_

- [ ] 20. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 21. Test with existing TTK demo applications
  - Run demo applications with CoreGraphics backend
  - Verify visual output matches curses backend
  - Verify keyboard input works correctly
  - Verify window management works correctly
  - Verify no demo code changes are needed
  - _Requirements: 11.1, 11.2, 16.1, 16.2_

- [ ]* 21.1 Write property test for ASCII character rendering
  - **Property 13: ASCII Character Rendering**
  - **Validates: Requirements 11.3**

- [ ]* 21.2 Write property test for color pair range support
  - **Property 14: Color Pair Range Support**
  - **Validates: Requirements 11.4**

- [ ] 22. Test Unicode and emoji support
  - Test rendering Unicode characters
  - Test rendering emoji
  - Test rendering complex scripts (Arabic, Thai, etc.)
  - Verify automatic font fallback for missing glyphs
  - _Requirements: 15.1, 15.2, 15.3, 15.4_

- [ ]* 22.1 Write property test for Unicode support
  - **Property 16: Unicode Character Support**
  - **Validates: Requirements 15.1**

- [ ] 23. Test backend compatibility and API compliance
  - Verify CoreGraphicsBackend inherits from Renderer
  - Verify all abstract methods are implemented
  - Verify method signatures match Renderer interface
  - Verify backend works with any Renderer-based application
  - _Requirements: 17.1, 17.2, 17.3, 17.5_

- [ ] 24. Test key code consistency with curses backend
  - Compare key codes between CoreGraphics and curses backends
  - Verify same logical keys produce same key codes
  - Test arrow keys, function keys, Enter, Escape, Backspace, Delete
  - _Requirements: 16.4_

- [ ]* 24.1 Write property test for key code consistency
  - **Property 17: Key Code Consistency**
  - **Validates: Requirements 16.4**

- [ ] 25. Performance testing and optimization
  - Measure rendering time for 80x24 grid
  - Verify rendering completes in under 10ms
  - Measure rendering time for 200x60 grid
  - Verify acceptable performance for larger grids
  - Profile and optimize if needed
  - _Requirements: 10.5_

- [ ] 26. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 27. Update TTK documentation
  - Add CoreGraphics backend to backend list in documentation
  - Document PyObjC installation requirements
  - Add example of using CoreGraphics backend
  - Document platform requirements (macOS only)
  - _Requirements: Documentation_

- [ ] 28. Create demo application showing backend switching
  - Create demo that accepts --backend argument
  - Support both "curses" and "coregraphics" options
  - Demonstrate identical behavior with both backends
  - Show that no application code changes are needed
  - _Requirements: 11.1, 16.2_
