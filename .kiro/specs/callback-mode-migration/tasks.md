# Implementation Plan: Callback Mode Migration

## Overview

This plan breaks down the callback mode migration into discrete implementation tasks. The migration removes polling mode support, simplifies the architecture, and ensures all code uses callback-only event delivery.

## Tasks

- [ ] 1. Create test infrastructure for callback mode
  - Create `ttk/test/test_utils.py` with EventCapture helper class
  - Implement `get_next_event()` helper method
  - Implement `wait_for_event()` helper method
  - _Requirements: 6.2_

- [ ]* 1.1 Write unit tests for EventCapture helper
  - Test event capture for key events
  - Test event capture for character events
  - Test event capture for resize events
  - Test get_next_event() with timeout
  - Test wait_for_event() with specific event types
  - _Requirements: 6.2_

- [ ] 2. Update Renderer interface
  - Remove `get_event()` method from abstract interface
  - Remove `get_input()` method from abstract interface
  - Make `callback` parameter non-optional in `set_event_callback()` signature
  - Add docstring explaining callback is required
  - Add docstring for `run_event_loop_iteration()` explaining event delivery
  - _Requirements: 1.1, 1.2, 2.1_

- [ ]* 2.1 Write unit tests for Renderer interface changes
  - Test that `get_event()` method doesn't exist
  - Test that `get_input()` method doesn't exist
  - Test that `set_event_callback()` signature requires callback
  - _Requirements: 1.1, 1.2_

- [ ] 3. Update CoreGraphics backend - remove polling mode
  - Remove `get_event()` method implementation
  - Remove `_process_events()` method
  - Remove `event_queue` instance variable
  - Remove any initialization of event queue
  - _Requirements: 1.3, 1.4_

- [ ]* 3.1 Write unit tests for removed methods
  - Test that `get_event()` method doesn't exist on CoreGraphicsBackend
  - Test that `event_queue` attribute doesn't exist
  - _Requirements: 1.3, 1.4_

- [ ] 4. Update CoreGraphics backend - add validation
  - Add validation to `set_event_callback()` to reject None
  - Add validation to `run_event_loop_iteration()` to check callback is set
  - Raise `ValueError` if callback is None in `set_event_callback()`
  - Raise `RuntimeError` if callback not set in `run_event_loop_iteration()`
  - _Requirements: 2.1, 2.2_

- [ ]* 4.1 Write property test for callback requirement
  - **Property 1: Event callback required before event loop**
  - **Validates: Requirements 2.1, 2.2**
  - Test that calling run_event_loop_iteration() without callback raises RuntimeError
  - Test that calling set_event_callback(None) raises ValueError
  - _Requirements: 2.1, 2.2_

- [ ] 5. Simplify CoreGraphics backend event delivery
  - Remove conditional `if self.event_callback:` checks from `keyDown_()`
  - Remove conditional checks from other event handler methods
  - Ensure all events are delivered directly via callback methods
  - Simplify `keyDown_()` to always use callback path
  - _Requirements: 2.3, 2.4, 4.1, 4.2_

- [ ]* 5.1 Write property test for event delivery
  - **Property 2: All events delivered via callbacks**
  - **Validates: Requirements 2.3, 2.5, 3.3, 3.5, 4.1, 4.3**
  - Test that key events are delivered via on_key_event()
  - Test that character events are delivered via on_char_event()
  - Test that resize events are delivered via on_resize()
  - Test that events are not returned from event loop methods
  - Use hypothesis to generate various event types
  - _Requirements: 2.3, 4.1, 4.3_

- [ ] 6. Checkpoint - Verify core TTK changes
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Update TFM application initialization
  - Remove `enable_callback_mode()` method from TFM class
  - Remove `disable_callback_mode()` method from TFM class
  - Remove `callback_mode_enabled` instance variable
  - Set event callback in `__init__` method
  - Create TFMEventCallback instance in `__init__`
  - Call `renderer.set_event_callback()` in `__init__`
  - _Requirements: 5.2, 5.3, 5.4_

- [ ]* 7.1 Write unit tests for TFM initialization
  - Test that callback is set during initialization
  - Test that `enable_callback_mode()` method doesn't exist
  - Test that `disable_callback_mode()` method doesn't exist
  - Test that `callback_mode_enabled` attribute doesn't exist
  - _Requirements: 5.2, 5.3, 5.4_

- [ ] 8. Simplify TFM main loop
  - Remove unnecessary `get_event()` call from main loop
  - Keep only `run_event_loop_iteration()` call
  - Remove `run_with_callbacks()` method if it exists
  - Merge any callback-specific logic into main `run()` method
  - _Requirements: 5.1_

- [ ]* 8.1 Write integration test for TFM event loop
  - Test that TFM main loop processes events via callbacks
  - Test that key events trigger TFM actions
  - Test that TFM responds to events correctly
  - _Requirements: 5.1, 10.1_

- [ ] 9. Update TTK test files to use callback mode
  - Update `ttk/test/test_coregraphics_keyboard_input.py`
  - Update `ttk/test/test_coregraphics_menu.py`
  - Update `ttk/test/test_lines_simple.py`
  - Update `ttk/test/verify_coregraphics_keyboard_input.py`
  - Update `ttk/test/test_curses_input_handling.py`
  - Update `ttk/test/test_box_drawing_chars.py`
  - Update `ttk/test/verify_curses_black_background.py`
  - Update `ttk/test/test_drawrect_phase1_batching.py`
  - Update `ttk/test/test_curses_background.py`
  - Update `ttk/test/test_lines_visibility.py`
  - Update `ttk/demo/test_interface.py`
  - Replace `get_input()` calls with EventCapture pattern
  - _Requirements: 6.1, 6.3_

- [ ] 10. Update TFM test files to use callback mode
  - Update `test/test_tfm_main_input_handling.py`
  - Update `test/test_coregraphics_resize_event.py`
  - Update `test/test_coregraphics_resize_on_restore.py`
  - Update `test/test_performance_benchmarks.py`
  - Replace `get_input()` calls with EventCapture pattern
  - _Requirements: 6.1, 6.3_

- [ ] 11. Update TTK demo scripts to use callback mode
  - Update `ttk/demo/standalone_app.py`
  - Update `ttk/demo/backend_switching.py`
  - Update `ttk/demo/demo_unicode_emoji.py`
  - Implement EventCallback classes for each demo
  - Replace `get_input()` calls with callback pattern
  - _Requirements: 7.1, 7.2, 7.4_

- [ ] 12. Update TFM demo scripts to use callback mode
  - Update `demo/demo_menu_keyboard_shortcuts.py`
  - Update `demo/demo_character_drawing_optimization.py`
  - Update `demo/demo_menu_bar.py`
  - Update `demo/demo_coregraphics_resize.py`
  - Note: `demo/demo_japanese_input.py` already uses callback mode
  - Implement EventCallback classes for each demo
  - Replace `get_input()` calls with callback pattern
  - _Requirements: 7.1, 7.2, 7.4_

- [ ] 13. Checkpoint - Verify all code migrated
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 13.1 Write property test for IME unconsumed events
  - **Property 3: IME unconsumed events passed to interpretKeyEvents**
  - **Validates: Requirements 9.2**
  - Test that unconsumed key events are passed to IME
  - Test that consumed key events are not passed to IME
  - Use hypothesis to generate various key events
  - _Requirements: 9.2_

- [ ]* 13.2 Write property test for IME composed text delivery
  - **Property 4: IME composed text delivered via callback**
  - **Validates: Requirements 9.3**
  - Test that IME composition results are delivered via on_char_event()
  - Test various IME composition sequences
  - _Requirements: 9.3_

- [ ]* 13.3 Write property test for IME composition handling
  - **Property 5: IME composition handled correctly**
  - **Validates: Requirements 9.1**
  - Test complete IME composition sequences
  - Test marked text handling
  - Test composition finalization
  - Use hypothesis to generate various composition sequences
  - _Requirements: 9.1_

- [ ] 14. Update TTK documentation
  - Update `ttk/README.md` to remove polling mode examples
  - Add callback mode examples to `ttk/README.md`
  - Update any other TTK documentation files
  - Remove references to `get_event()` and `get_input()`
  - _Requirements: 8.1, 8.2_

- [ ] 15. Update developer documentation
  - Update `doc/dev/EVENT_HANDLING_IMPLEMENTATION.md`
  - Update `doc/dev/IME_SUPPORT_IMPLEMENTATION.md`
  - Update `doc/dev/CALLBACK_MODE_VS_POLLING_MODE.md`
  - Remove polling mode sections
  - Add callback-only architecture explanation
  - _Requirements: 8.3, 8.4_

- [ ] 16. Create migration guide (if needed)
  - Check if external TTK users exist
  - If yes, create migration guide document
  - Document breaking changes
  - Provide code examples for migration
  - _Requirements: 12.1, 12.3_

- [ ] 17. Update version number
  - Increment major version number (breaking change)
  - Update version in setup.py or equivalent
  - Update CHANGELOG with breaking changes
  - _Requirements: 12.4_

- [ ] 18. Final validation and testing
  - Run complete test suite
  - Verify all tests pass
  - Manual IME testing (Japanese, Chinese, Korean)
  - TFM regression testing (key bindings, dialogs, file operations)
  - Performance validation
  - _Requirements: 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 10.4_

- [ ] 19. Verify code simplification goals
  - Count lines of code removed (should be 400+)
  - Verify no conditional logic for callback mode in CoreGraphics backend
  - Verify Renderer interface is simpler
  - Verify no dead code paths remain
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [ ] 20. Final checkpoint - Migration complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- IME testing is critical - must be tested manually with real IME input
- The migration is a breaking change - version number must be incremented
