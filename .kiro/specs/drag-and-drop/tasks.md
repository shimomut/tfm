# Implementation Plan: Drag-and-Drop Support

## Overview

This implementation adds drag-and-drop functionality to TFM, enabling users to drag files from the file manager to external applications on desktop platforms. The work is organized into gesture detection, payload building, session management, backend integration, and testing, with initial focus on macOS via the CoreGraphics backend.

## Tasks

- [ ] 1. Create drag gesture detection module
  - Create `src/tfm_drag_gesture.py` with DragGestureDetector class
  - Implement button down, move, and button up handlers
  - Add distance and time threshold constants
  - Implement state tracking (button_down, start position, dragging flag)
  - _Requirements: 1.1, 1.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 1.1 Write property test for drag gesture detection
  - **Property 1: Drag initiation on movement threshold**
  - **Property 15: Time threshold for drag detection**
  - **Validates: Requirements 1.1, 1.5, 6.2, 6.3, 6.5**

- [ ] 2. Create drag payload builder module
  - Create `src/tfm_drag_payload.py` with DragPayloadBuilder class
  - Implement build_payload method with file selection logic
  - Add validation for remote files, archive contents, parent directory
  - Implement file existence checking
  - Add file:// URL conversion with proper encoding
  - _Requirements: 1.2, 1.3, 1.4, 3.1, 3.2, 3.4, 3.5, 7.1, 7.5, 9.1, 9.3_

- [ ]* 2.1 Write property tests for payload building
  - **Property 2: Payload contains selected files**
  - **Property 3: Payload contains focused item when no selection**
  - **Property 6: Absolute file:// URLs in payload**
  - **Property 7: Remote files rejected**
  - **Property 8: File existence validation**
  - **Property 17: Files and directories in payload**
  - **Property 19: Archive content rejection**
  - **Property 20: Archive file vs content distinction**
  - **Validates: Requirements 1.2, 1.3, 3.1, 3.2, 3.4, 3.5, 7.1, 7.5, 9.1, 9.3**

- [ ]* 2.2 Write unit tests for payload edge cases
  - Test parent directory marker rejection
  - Test file count limit (1000 files)
  - Test error message for too many files
  - _Requirements: 1.4, 7.2, 7.3_

- [ ] 3. Create drag session manager module
  - Create `src/tfm_drag_session.py` with DragSessionManager class
  - Implement state machine (IDLE, DRAGGING, COMPLETED, CANCELLED)
  - Add start_drag, handle_drag_completed, handle_drag_cancelled methods
  - Implement resource cleanup
  - Add completion callback support
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 3.1 Write property tests for session management
  - **Property 9: Backend registration on drag start**
  - **Property 10: Resource cleanup on completion**
  - **Property 11: Event blocking during drag**
  - **Property 12: State machine transitions**
  - **Property 13: Cancellation callback handling**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

- [ ] 4. Checkpoint - Ensure core module tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Extend TTK backend interface for drag-and-drop
  - Add supports_drag_and_drop() method to `ttk/ttk_backend.py`
  - Add start_drag_session() method with file_urls and drag_image_text parameters
  - Add set_drag_completion_callback() method
  - Document platform-agnostic interface design
  - _Requirements: 5.1, 5.5_

- [ ] 6. Implement CoreGraphics backend drag-and-drop
  - Extend `ttk/backends/coregraphics_backend.py` with drag support
  - Implement supports_drag_and_drop() returning True
  - Implement start_drag_session() calling C++ extension
  - Add _on_drag_completed() and _on_drag_cancelled() callback handlers
  - Document macOS-specific implementation details
  - _Requirements: 2.1, 2.2, 2.3, 3.3, 5.2, 5.3_

- [ ] 7. Implement C++ extension for macOS drag-and-drop
  - Extend `ttk/backends/coregraphics_backend.cpp` with native drag support
  - Create NSDraggingItem with file URLs
  - Set up NSPasteboard with NSFilenamesPboardType
  - Generate drag image with text overlay using NSImage
  - Begin NSDraggingSession
  - Register completion/cancellation callbacks
  - _Requirements: 2.1, 2.2, 2.3, 3.3, 5.2_

- [ ]* 7.1 Write unit tests for CoreGraphics drag support
  - Test capability detection returns True
  - Test start_drag_session calls native method
  - Test completion callback invocation
  - Test cancellation callback invocation
  - _Requirements: 5.2, 5.3_

- [ ] 8. Implement Curses backend graceful degradation
  - Update `ttk/backends/curses_backend.py` with drag support
  - Implement supports_drag_and_drop() returning False
  - Implement start_drag_session() returning False with log message
  - _Requirements: 5.4_

- [ ]* 8.1 Write property test for Curses degradation
  - **Property 14: Graceful degradation in terminal mode**
  - **Validates: Requirements 5.4**

- [ ] 9. Checkpoint - Ensure backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Integrate drag-and-drop into FileManager
  - Update `src/tfm_main.py` to instantiate drag components
  - Add DragGestureDetector, DragPayloadBuilder, DragSessionManager instances
  - Update handle_mouse_event() to detect drag gestures
  - Implement _initiate_drag() method
  - Add _on_drag_completed() callback handler
  - Block other mouse events during drag
  - _Requirements: 1.1, 4.3, 5.5_

- [ ]* 10.1 Write property tests for FileManager integration
  - **Property 4: Drag image shows file count**
  - **Property 5: State restoration on cancellation**
  - **Property 16: Selection state preservation**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.5, 7.4**

- [ ]* 10.2 Write unit tests for FileManager drag integration
  - Test drag initiation from file list
  - Test selected files vs focused item logic
  - Test event blocking during drag
  - Test state restoration after completion
  - _Requirements: 1.1, 1.2, 1.3, 4.3, 7.4_

- [ ] 11. Add error handling and user feedback
  - Add error messages for remote files, archive contents, missing files
  - Add error message for too many files (> 1000)
  - Implement error logging for OS rejection
  - Add visual feedback for drag not available
  - _Requirements: 8.1, 8.2, 8.3, 9.2_

- [ ]* 11.1 Write property test for error handling
  - **Property 18: Error handling for OS rejection**
  - **Validates: Requirements 8.3**

- [ ]* 11.2 Write unit tests for error scenarios
  - Test error message for remote files
  - Test error message for archive contents
  - Test error message for missing files
  - Test error message for too many files
  - _Requirements: 8.1, 8.2, 9.2, 7.3_

- [ ] 12. Checkpoint - Ensure integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Create demo script for drag-and-drop
  - Create `demo/demo_drag_and_drop.py` showing drag functionality
  - Demonstrate single file drag
  - Demonstrate multi-file drag
  - Demonstrate error cases (remote files, archive contents)
  - Show drag image with file count
  - _Requirements: All_

- [ ] 14. Create end-user documentation
  - Create `doc/DRAG_AND_DROP_FEATURE.md` with user guide
  - Document how to drag files to external applications
  - Document supported platforms (macOS desktop mode)
  - Document limitations (terminal mode, remote files, archive contents)
  - Document file count limit
  - _Requirements: All_

- [ ] 15. Create developer documentation
  - Create `doc/dev/DRAG_AND_DROP_IMPLEMENTATION.md`
  - Document drag gesture detection algorithm
  - Document payload building and validation
  - Document session lifecycle management
  - Document backend interface and platform-specific implementations
  - Document how to add Windows/Linux support in future
  - _Requirements: All_

- [ ] 16. Final checkpoint - Complete feature verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The architecture is designed for future Windows/Linux support
- Initial implementation focuses on macOS via CoreGraphics backend

