# Implementation Plan

- [x] 1. Enable window frame autosave in CoreGraphics backend
  - Add `WINDOW_FRAME_AUTOSAVE_NAME` constant to CoreGraphicsBackend class
  - Modify `_create_window()` method to call `setFrameAutosaveName:` after window creation
  - Add error handling for frame autosave setup
  - _Requirements: 2.1, 2.3, 4.1_

- [x] 1.5 Make frame autosave name configurable
  - Add `frame_autosave_name` parameter to CoreGraphicsBackend `__init__` method
  - Store frame autosave name as instance variable (default to "TTKApplication" if not provided)
  - Update `_create_window()` to use `self.frame_autosave_name` instead of constant
  - Update `reset_window_geometry()` to use `self.frame_autosave_name` instead of constant
  - Update TFM's backend initialization to pass "TFMMainWindow" as frame autosave name
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 1.1 Write property test for frame autosave configuration
  - **Property 1: Frame autosave name is set**
  - **Validates: Requirements 2.3**

- [x] 2. Implement window geometry reset functionality
  - Add `reset_window_geometry()` method to CoreGraphicsBackend class
  - Implement NSUserDefaults key removal for saved frame
  - Apply default window frame from configuration
  - Add logging for reset operations
  - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [ ]* 2.1 Write property test for reset functionality
  - **Property 7: Reset clears persistence**
  - **Validates: Requirements 6.2, 6.3**

- [x] 3. Add error handling for persistence failures
  - Add try-except blocks around frame autosave setup
  - Add try-except blocks around reset operations
  - Implement graceful fallback behavior
  - Add warning messages for persistence failures
  - _Requirements: 1.5, 4.5_

- [ ]* 3.1 Write unit tests for error handling
  - Test corrupted NSUserDefaults data handling
  - Test missing NSUserDefaults data handling
  - Test frame autosave setup failure handling
  - Test reset operation failure handling
  - _Requirements: 1.5, 4.5, 6.4_

- [x] 4. Verify backend-specific behavior
  - Ensure frame autosave is only enabled in CoreGraphics backend
  - Verify curses backend is unaffected
  - Add backend type checks if necessary
  - _Requirements: 5.5_

- [ ]* 4.1 Write unit test for backend-specific behavior
  - Test that curses backend doesn't call NSWindow methods
  - Test that CoreGraphics backend enables persistence
  - _Requirements: 5.5_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 6. Write property test for geometry persistence round-trip
  - **Property 1: Geometry persistence round-trip**
  - **Validates: Requirements 1.4**

- [ ]* 7. Write property test for resize persistence
  - **Property 2: Resize persistence**
  - **Validates: Requirements 1.2, 4.3**

- [ ]* 8. Write property test for move persistence
  - **Property 3: Move persistence**
  - **Validates: Requirements 1.3, 4.3**

- [ ]* 9. Write property test for grid recalculation
  - **Property 4: Grid recalculation on restore**
  - **Validates: Requirements 5.4**

- [ ]* 10. Write property test for programmatic resize compatibility
  - **Property 5: Programmatic resize compatibility**
  - **Validates: Requirements 5.2**

- [ ]* 11. Write property test for resize event handling
  - **Property 6: Resize event handling preservation**
  - **Validates: Requirements 5.3**

- [ ]* 11.5 Write property test for frame autosave name configurability
  - **Property 8: Frame autosave name configurability**
  - **Validates: Requirements 7.1, 7.3**

- [x] 12. Write integration tests for persistence behavior
  - Test first launch behavior (default geometry)
  - Test persistence across quit/relaunch sessions
  - Test multi-monitor support
  - Test reset functionality in full application context
  - _Requirements: 1.1, 1.4, 3.1, 3.2, 6.1_

- [x] 13. Create demo script for window geometry persistence
  - Create demo script showing window geometry persistence in action
  - Demonstrate resize and move persistence
  - Demonstrate reset functionality
  - Demonstrate multi-monitor behavior (if available)
  - Place in `demo/demo_window_geometry_persistence.py`
  - _Requirements: All_

- [x] 14. Create end-user documentation
  - Document window geometry persistence feature for users
  - Explain automatic save/restore behavior
  - Document reset functionality
  - Include troubleshooting section
  - Place in `doc/WINDOW_GEOMETRY_PERSISTENCE_FEATURE.md`
  - _Requirements: All_

- [x] 15. Create developer documentation
  - Document implementation details for developers
  - Explain NSWindow frame autosave mechanism
  - Document NSUserDefaults storage format
  - Include code examples and architecture diagrams
  - Place in `doc/dev/WINDOW_GEOMETRY_PERSISTENCE_IMPLEMENTATION.md`
  - _Requirements: All_

- [x] 16. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
