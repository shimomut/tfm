# Implementation Plan: Mouse Event Support

## Overview

This implementation adds comprehensive mouse event support to TFM across both terminal (curses) and desktop (CoreGraphics) modes. The work is organized into backend implementation, TTK API layer, and TFM application integration, with initial focus on pane focus switching via mouse clicks.

## Tasks

- [x] 1. Create TTK mouse event data structures
  - Create `ttk/ttk_mouse_event.py` with MouseEvent, MouseEventType, and MouseButton classes
  - Implement dataclass with all required fields including scroll deltas
  - Add coordinate transformation utility functions
  - _Requirements: 1.1, 1.2, 1.3, 6.1-6.6, 8.4_

- [ ]* 1.1 Write property test for MouseEvent structure
  - **Property 1: MouseEvent structure completeness**
  - **Validates: Requirements 1.1, 6.1-6.6, 8.4**

- [ ]* 1.2 Write property tests for coordinate transformation
  - **Property 2: Coordinate transformation correctness**
  - **Property 3: Sub-cell position bounds**
  - **Property 4: Sub-cell position accuracy**
  - **Validates: Requirements 1.2, 1.3, 2.4, 2.5**

- [x] 2. Extend TTK backend interface for mouse support
  - Add mouse support methods to `ttk/ttk_backend.py` base class
  - Implement `supports_mouse()`, `get_supported_mouse_events()`, `enable_mouse_events()`, `poll_mouse_event()`
  - Add capability detection methods
  - _Requirements: 1.5, 7.1, 7.2, 7.3_

- [x] 3. Implement CoreGraphics backend mouse support
  - Extend `ttk/backends/coregraphics_backend.py` with mouse event capture
  - Implement coordinate transformation from window to text grid coordinates
  - Add sub-cell position calculation
  - Support all mouse event types (button, move, wheel, double-click)
  - Implement scroll delta calculation for wheel events
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 3.1 Write unit tests for CoreGraphics mouse support
  - Test capability detection returns all event types
  - Test coordinate transformation with known cell dimensions
  - Test scroll delta calculation
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 4. Implement Curses backend mouse support
  - Extend `ttk/backends/curses_backend.py` with mouse event capture
  - Implement terminal capability detection
  - Map curses mouse events to TTK MouseEvent objects
  - Handle graceful degradation when mouse unsupported
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 4.1 Write property tests for Curses backend
  - **Property 11: Curses backend graceful degradation**
  - **Property 12: Curses backend coordinate validity**
  - **Validates: Requirements 3.3, 3.4**

- [ ]* 4.2 Write unit tests for Curses backend
  - Test capability detection on supported/unsupported terminals
  - Test event type mapping from curses to TTK
  - _Requirements: 3.1, 3.2, 3.5_

- [x] 5. Checkpoint - Ensure backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Add mouse event handling to UILayer base class
  - Extend `src/tfm_ui_layer.py` with `handle_mouse_event()` method
  - Add `is_point_inside()` helper method for bounds checking
  - Document that only topmost layer receives events (no propagation)
  - _Requirements: 4.4, 4.5_

- [ ]* 6.1 Write property test for event handler registration
  - **Property 5: Event handler registration and invocation**
  - **Validates: Requirements 1.5**

- [x] 7. Implement mouse event routing in TFM
  - Update `src/tfm_main.py` to poll for mouse events from backend
  - Route mouse events to topmost UILayer in stack
  - Ensure consistent routing with keyboard events
  - Query mouse capabilities at startup
  - _Requirements: 4.1, 4.2, 4.3, 7.5_

- [ ]* 7.1 Write property tests for event routing
  - **Property 6: Event stack routing to topmost layer only**
  - **Property 7: Consistent routing for mouse and keyboard events**
  - **Validates: Requirements 4.1, 4.2, 4.3**

- [x] 8. Implement pane focus switching in FileManager
  - Update file pane components to handle mouse events
  - Implement `handle_mouse_event()` in pane classes
  - Add bounds checking using `is_point_inside()`
  - Switch focus when click occurs in pane bounds
  - Update visual indicators when focus changes
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 8.1 Write property tests for pane focus switching
  - **Property 8: Pane focus follows click location**
  - **Property 9: Focus state reflects active pane**
  - **Property 10: Focus preservation outside pane bounds**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [ ]* 8.2 Write unit tests for pane focus switching
  - Test focus switches to left pane on left click
  - Test focus switches to right pane on right click
  - Test focus preserved on click outside panes
  - Test visual indicators update
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 9. Add event timestamp ordering
  - Ensure all MouseEvent objects have monotonic timestamps
  - Add timestamp validation in event creation
  - _Requirements: 8.2_

- [ ]* 9.1 Write property test for event ordering
  - **Property 13: Event timestamp ordering**
  - **Validates: Requirements 8.2**

- [x] 10. Checkpoint - Ensure integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Create demo script for mouse event support
  - Create `demo/demo_mouse_events.py` showing pane focus switching
  - Demonstrate mouse event capture in both backends
  - Show coordinate transformation and sub-cell positioning
  - _Requirements: All_

- [x] 12. Create end-user documentation
  - Create `doc/MOUSE_EVENT_SUPPORT_FEATURE.md` with user guide
  - Document how to use mouse to switch pane focus
  - Document backend capabilities and limitations
  - _Requirements: All_

- [x] 13. Create developer documentation
  - Create `doc/dev/MOUSE_EVENT_SUPPORT_IMPLEMENTATION.md`
  - Document MouseEvent API and coordinate system
  - Document backend implementation details
  - Document how to extend for future drag-and-drop
  - _Requirements: All_

- [x] 14. Final checkpoint - Complete feature verification
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Implement mouse wheel scrolling in file lists
  - Add wheel event handling to FileManager.handle_mouse_event()
  - Detect which pane the mouse is over during wheel events
  - Adjust scroll_offset (not focused_index) based on scroll_delta_y with 1x multiplier
  - Implement boundary checking to prevent scrolling past top/bottom
  - Create comprehensive test suite for wheel scrolling (10 tests)
  - Update documentation with wheel scrolling feature
  - _Requirements: 2.5, 5.6_

- [x] 16. Implement mouse wheel scrolling in log pane
  - Add wheel event handling for log pane area in FileManager.handle_mouse_event()
  - Detect wheel events in log pane area (row >= log_pane_top)
  - Call log_manager.scroll_log_up/down() based on scroll direction
  - Create comprehensive test suite for log pane scrolling (7 tests)
  - _Requirements: 2.5, 5.6_

- [x] 17. Implement mouse wheel scrolling in viewers
  - Add wheel event handling to TextViewer.handle_mouse_event()
  - Add wheel event handling to DiffViewer.handle_mouse_event()
  - Add wheel event handling to DirectoryDiffViewer.handle_mouse_event()
  - Adjust scroll_offset based on scroll_delta_y with 1x multiplier
  - Implement boundary checking for each viewer type
  - Create comprehensive test suite for viewer scrolling (10 tests)
  - _Requirements: 2.5, 5.6_

- [x] 18. Fix DirectoryDiffViewer cursor visibility when navigating
  - Create helper method `_ensure_cursor_visible(display_height)` that checks both above and below
  - Update `_jump_to_previous_difference()` to use the helper
  - Update `_jump_to_next_difference()` to use the helper
  - Update LEFT arrow key handler to use the helper when moving to parent
  - Verify all navigation keeps cursor visible
  - All 10 viewer wheel scrolling tests pass
  - _Requirements: 5.6_

- [x] 19. Implement click-to-focus in DirectoryDiffViewer
  - Add button down event handling to DirectoryDiffViewer.handle_mouse_event()
  - Calculate which item was clicked based on row and scroll_offset
  - Move cursor_position to clicked item when valid
  - Implement boundary checking (tree view area: rows 2 to height-5)
  - Create comprehensive test suite (9 tests covering all scenarios)
  - All 44 mouse event tests pass
  - _Requirements: 5.1, 5.2_

- [x] 20. Implement click-to-focus in FileManager file lists
  - Add item selection when clicking in file list (in addition to pane focus switching)
  - Calculate clicked_file_index using scroll_offset
  - Set focused_index directly via pane_data dictionary
  - Update test suite to verify both pane switching and item selection
  - All 44 mouse event tests pass
  - _Requirements: 5.1, 5.2_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The architecture is designed for future drag-and-drop extensibility
