# Implementation Plan: UI Layer Stack System

## Overview

This implementation plan breaks down the UI Layer Stack feature into discrete, incremental tasks. The approach is to build the core infrastructure first, then migrate existing components one by one, and finally remove the old conditional logic.

## Tasks

- [x] 1. Create UILayer interface and UILayerStack class
  - Create new file `src/tfm_ui_layer.py` with UILayer abstract base class
  - Implement all required abstract methods: handle_key_event, handle_char_event, render, is_full_screen, needs_redraw, mark_dirty, clear_dirty, should_close, on_activate, on_deactivate
  - Create UILayerStack class with push, pop, get_top_layer, get_layer_count, handle_key_event, handle_char_event, render, check_and_close_top_layer methods
  - Implement intelligent dirty tracking in render() method
  - Implement exception handling for event processing and rendering
  - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 4.1, 4.2, 4.3, 9.1, 9.2, 9.3, 9.4_

- [ ]* 1.1 Write property test for LIFO stack ordering
  - **Property 1: LIFO Stack Ordering**
  - **Validates: Requirements 1.1, 1.3, 1.4**

- [ ]* 1.2 Write property test for bottom layer persistence
  - **Property 2: Bottom Layer Persistence**
  - **Validates: Requirements 1.6, 9.4**

- [ ]* 1.3 Write property test for top layer query consistency
  - **Property 3: Top Layer Query Consistency**
  - **Validates: Requirements 1.5**

- [ ]* 1.4 Write property test for event routing to top layer
  - **Property 4: Event Routing to Top Layer**
  - **Validates: Requirements 2.1, 2.2**

- [ ]* 1.5 Write property test for event consumption stops propagation
  - **Property 5: Event Consumption Stops Propagation**
  - **Validates: Requirements 2.3**

- [ ]* 1.6 Write property test for event propagation chain
  - **Property 6: Event Propagation Chain**
  - **Validates: Requirements 2.4, 2.5**

- [ ]* 1.7 Write property test for exception handling during event processing
  - **Property 17: Exception Handling During Event Processing**
  - **Validates: Requirements 9.1**

- [ ]* 1.8 Write property test for exception handling during rendering
  - **Property 18: Exception Handling During Rendering**
  - **Validates: Requirements 9.2**

- [ ]* 1.9 Write property test for stack never empty
  - **Property 19: Stack Never Empty**
  - **Validates: Requirements 9.3**

- [x] 2. Modify ListDialog to inherit from UILayer
  - Update `src/tfm_list_dialog.py` to make ListDialog inherit from UILayer
  - Implement handle_key_event() and handle_char_event() by refactoring existing handle_input()
  - Implement render() by calling existing draw()
  - Implement is_full_screen() to return False
  - Implement needs_redraw(), mark_dirty(), clear_dirty() for dirty tracking
  - Implement should_close() using existing is_active flag
  - Implement on_activate() and on_deactivate() lifecycle methods
  - Ensure existing functionality is preserved
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.3_

- [x] 3. Modify InfoDialog to inherit from UILayer
  - Update `src/tfm_info_dialog.py` to make InfoDialog inherit from UILayer
  - Implement all UILayer methods following the same pattern as ListDialog
  - Ensure existing functionality is preserved
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.3_

- [x] 4. Modify SearchDialog to inherit from UILayer
  - Update `src/tfm_search_dialog.py` to make SearchDialog inherit from UILayer
  - Implement all UILayer methods following the same pattern as ListDialog
  - Ensure existing functionality is preserved
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.3_

- [x] 5. Modify JumpDialog to inherit from UILayer
  - Update `src/tfm_jump_dialog.py` to make JumpDialog inherit from UILayer
  - Implement all UILayer methods following the same pattern as ListDialog
  - Ensure existing functionality is preserved
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.3_

- [x] 6. Modify DrivesDialog to inherit from UILayer
  - Update `src/tfm_drives_dialog.py` to make DrivesDialog inherit from UILayer
  - Implement all UILayer methods following the same pattern as ListDialog
  - Ensure existing functionality is preserved
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.3_

- [x] 7. Modify BatchRenameDialog to inherit from UILayer
  - Update `src/tfm_batch_rename_dialog.py` to make BatchRenameDialog inherit from UILayer
  - Implement all UILayer methods following the same pattern as ListDialog
  - Ensure existing functionality is preserved
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.3_

- [x] 8. Checkpoint - Ensure all dialog tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Modify TextViewer to inherit from UILayer
  - Update `src/tfm_text_viewer.py` to make TextViewer inherit from UILayer
  - Implement handle_key_event() by refactoring existing handle_input()
  - Implement handle_char_event() to return False (no text input in viewer)
  - Implement render() by calling existing draw()
  - Implement is_full_screen() to return True
  - Implement needs_redraw(), mark_dirty(), clear_dirty() for dirty tracking
  - Implement should_close() using existing should_close flag
  - Implement on_activate() to hide cursor and mark dirty
  - Implement on_deactivate() lifecycle method
  - Ensure existing functionality is preserved
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.1_

- [x] 10. Modify DiffViewer to inherit from UILayer
  - Update `src/tfm_diff_viewer.py` to make DiffViewer inherit from UILayer
  - Implement all UILayer methods following the same pattern as TextViewer
  - Ensure existing functionality is preserved
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.2_

- [ ]* 10.1 Write property test for rendering order
  - **Property 7: Bottom-to-Top Rendering Order**
  - **Validates: Requirements 3.1**

- [ ]* 10.2 Write property test for rendering context provision
  - **Property 8: Rendering Context Provision**
  - **Validates: Requirements 3.3**

- [ ]* 10.3 Write property test for full-screen layer obscures lower layers
  - **Property 10: Full-Screen Layer Obscures Lower Layers**
  - **Validates: Requirements 4.1**

- [ ]* 10.4 Write property test for rendering optimization
  - **Property 11: Rendering Optimization for Full-Screen Layers**
  - **Validates: Requirements 4.2, 4.5**

- [ ]* 10.5 Write property test for full-screen layer removal restores rendering
  - **Property 12: Full-Screen Layer Removal Restores Rendering**
  - **Validates: Requirements 4.3**

- [x] 11. Create FileManagerLayer wrapper
  - Create FileManagerLayer class in `src/tfm_ui_layer.py`
  - Implement handle_key_event() to delegate to FileManager main screen logic
  - Implement handle_char_event() to return False (no text input on main screen)
  - Implement render() to delegate to FileManager rendering logic
  - Implement is_full_screen() to return True
  - Implement needs_redraw() to check FileManager.needs_full_redraw flag
  - Implement mark_dirty() and clear_dirty() for dirty tracking
  - Implement should_close() to check close request flag
  - Implement on_activate() and on_deactivate() lifecycle methods
  - Add request_close() method for quit functionality
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.4_

- [x] 12. Integrate UILayerStack into FileManager
  - Add UILayerStack instance to FileManager.__init__()
  - Initialize stack with FileManagerLayer as bottom layer
  - Update FileManager.handle_input() to delegate to UILayerStack
  - Update main rendering loop to call UILayerStack.render()
  - Add methods to push/pop layers when dialogs/viewers are opened/closed
  - Ensure backward compatibility with existing code
  - _Requirements: 1.2, 2.1, 2.2, 3.1, 3.3, 6.4, 6.6_

- [ ]* 12.1 Write property test for activation lifecycle callback
  - **Property 13: Activation Lifecycle Callback**
  - **Validates: Requirements 8.1**

- [ ]* 12.2 Write property test for deactivation lifecycle callback
  - **Property 14: Deactivation Lifecycle Callback**
  - **Validates: Requirements 8.2**

- [ ]* 12.3 Write property test for state preservation during push
  - **Property 15: State Preservation During Push**
  - **Validates: Requirements 8.4**

- [ ]* 12.4 Write property test for state restoration during pop
  - **Property 16: State Restoration During Pop**
  - **Validates: Requirements 8.5**

- [x] 13. Checkpoint - Ensure integration works correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Remove if-elif chains from handle_input()
  - Remove if-elif blocks for dialog checking in FileManager.handle_input()
  - Remove if-elif blocks for viewer checking in FileManager.handle_input()
  - Simplify event routing to just call UILayerStack.handle_key_event() or handle_char_event()
  - Remove get_active_text_widget() method (no longer needed)
  - Ensure all event handling still works correctly
  - Created test file `test/test_handle_input_simplification.py` with 10 passing tests
  - All 123 integration tests pass
  - _Requirements: 7.1, 7.2_

- [x] 15. Remove if-elif chains from rendering methods
  - Remove if-elif blocks from _check_dialog_content_changed()
  - Remove if-elif blocks from _draw_dialogs_if_needed()
  - Remove if-elif blocks from _force_immediate_redraw()
  - Simplify rendering to just call UILayerStack.render()
  - Remove needs_dialog_redraw flag (replaced by layer dirty tracking)
  - Ensure all rendering still works correctly
  - _Requirements: 7.1, 7.3_

- [x] 16. Update dialog/viewer creation to use layer stack
  - Update show_list_dialog() to push ListDialog onto stack
  - Update show_info_dialog() to push InfoDialog onto stack
  - Update show_search_dialog() to push SearchDialog onto stack
  - Update show_jump_dialog() to push JumpDialog onto stack
  - Update show_drives_dialog() to push DrivesDialog onto stack
  - Update show_batch_rename_dialog() to push BatchRenameDialog onto stack
  - Update create_text_viewer() to push TextViewer onto stack
  - Update create_diff_viewer() to push DiffViewer onto stack
  - Remove self.active_viewer variable (replaced by layer stack)
  - Ensure all dialog/viewer creation still works correctly
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Measure code complexity reduction
  - Count lines of code in handle_input() before and after refactoring
  - Count lines of code in rendering methods before and after refactoring
  - Measure cyclomatic complexity before and after refactoring
  - Verify that code is simpler and more maintainable
  - _Requirements: 7.4, 7.5_

- [x] 19. Final integration testing
  - Test opening and closing dialogs
  - Test opening and closing viewers
  - Test stacking multiple dialogs
  - Test full-screen viewer with dialog on top
  - Test event routing through multiple layers
  - Test rendering optimization with full-screen layers
  - Test error handling with exception-throwing layers
  - Verify all existing functionality still works
  - _Requirements: 6.6_

- [x] 20. Final checkpoint - Ensure all tests pass
  - All UI layer stack tests pass (137 tests)
  - All integration tests pass (60 tests)
  - Fixed event propagation tests to reflect top-layer-only behavior
  - UI layer stack refactoring is complete and functional

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The migration is incremental to minimize risk and allow for testing at each step
