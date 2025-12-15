# Implementation Plan

- [x] 1. Set up TTK library structure and core interfaces
  - Create ttk/ package directory with __init__.py
  - Define project structure with backends/, serialization, and utils modules
  - Set up Python package configuration (setup.py or pyproject.toml)
  - _Requirements: 1.1, 1.4, 16.3_

- [x] 2. Implement abstract Renderer base class
  - Create renderer.py with Renderer ABC
  - Define all abstract methods for drawing operations (draw_text, draw_rect, draw_hline, draw_vline)
  - Define abstract methods for window management (get_dimensions, clear, refresh)
  - Define abstract methods for color management (init_color_pair)
  - Define abstract methods for input handling (get_input)
  - Define abstract methods for cursor control (set_cursor_visibility, move_cursor)
  - Add comprehensive docstrings for all methods
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 10.1_

- [x] 3. Implement input event system
  - Create input_event.py module
  - Define KeyCode IntEnum with all special keys (arrows, function keys, etc.)
  - Define ModifierKey IntEnum with modifier flags
  - Define KeyEvent dataclass with key_code, modifiers, char, and mouse fields
  - Implement helper methods (is_printable, is_special_key, has_modifier)
  - _Requirements: 1.2, 5.1, 5.2, 5.3, 5.4, 10.1_

- [x] 4. Implement TextAttribute enum
  - Define TextAttribute IntEnum in renderer.py
  - Include NORMAL, BOLD, UNDERLINE, REVERSE attributes
  - Document that attributes can be combined with bitwise OR
  - _Requirements: 1.1, 9.1, 9.2, 9.3, 9.4_

- [x] 5. Implement CursesBackend class
  - Create backends/curses_backend.py
  - Implement CursesBackend class inheriting from Renderer
  - Implement initialize() method to set up curses
  - Implement shutdown() method to clean up curses
  - _Requirements: 2.1, 2.5_

- [x] 6. Implement curses drawing operations
  - Implement draw_text() with color and attribute support
  - Implement draw_hline() and draw_vline()
  - Implement draw_rect() for both filled and outlined rectangles
  - Implement clear() and clear_region()
  - Implement refresh() and refresh_region()
  - Handle curses.error exceptions gracefully
  - _Requirements: 2.1, 2.2, 4.1, 4.2, 4.3, 4.5, 4.6_

- [x] 7. Implement curses color management
  - Implement init_color_pair() with RGB to curses color conversion
  - Implement _rgb_to_curses_color() helper method
  - Track initialized color pairs to avoid re-initialization
  - _Requirements: 2.2, 4.4, 7.1, 7.2_

- [x] 8. Implement curses input handling
  - Implement get_input() with timeout support
  - Implement _translate_curses_key() to convert curses keys to KeyEvent
  - Map all special keys (arrows, function keys, etc.)
  - Handle printable characters and special characters
  - _Requirements: 2.3, 5.1, 5.2, 5.5_

- [x] 9. Implement curses window management
  - Implement get_dimensions() to return terminal size
  - Implement set_cursor_visibility() and move_cursor()
  - Handle terminal resize events (KEY_RESIZE)
  - _Requirements: 2.4, 8.3, 8.4_

- [x] 10. Checkpoint - Verify curses backend functionality
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement MetalBackend class structure
  - Create backends/metal_backend.py
  - Implement MetalBackend class inheriting from Renderer
  - Define __init__() with window_title, font_name, font_size parameters
  - Initialize instance variables for Metal resources
  - _Requirements: 3.1_

- [x] 12. Implement Metal initialization
  - Implement initialize() method
  - Create Metal device using PyObjC
  - Create command queue
  - Create native macOS window
  - Calculate character dimensions for monospace font
  - Initialize character grid buffer
  - _Requirements: 3.1, 3.2, 17.1, 17.3_

- [x] 13. Implement Metal font validation
  - Implement _validate_font() method
  - Check that font is monospace using Core Text
  - Raise ValueError for proportional fonts with clear error message
  - _Requirements: 17.2, 17.5_

- [x] 14. Implement Metal character grid
  - Implement _initialize_grid() to create character buffer
  - Calculate rows and columns based on window size and character dimensions
  - Create 2D grid structure storing (char, color_pair, attributes) tuples
  - _Requirements: 3.1, 8.1, 8.2_

- [x] 15. Implement Metal drawing operations
  - Implement draw_text() to update grid buffer
  - Implement draw_hline() and draw_vline()
  - Implement draw_rect() for both filled and outlined rectangles
  - Implement clear() and clear_region()
  - Handle out-of-bounds coordinates gracefully
  - _Requirements: 3.2, 4.1, 4.2, 4.3, 4.5, 8.5_

- [x] 16. Implement Metal rendering pipeline
  - Implement _create_render_pipeline() to load shaders
  - Create vertex and fragment shaders for text rendering
  - Implement _render_grid() to render entire character grid
  - Implement _render_grid_region() for partial updates
  - Implement _render_character() to render individual characters
  - _Requirements: 3.2, 3.6, 14.1_

- [x] 17. Implement Metal color management
  - Implement init_color_pair() to store RGB color pairs
  - Store color pairs in dictionary
  - Use colors during rendering
  - _Requirements: 3.3, 4.4, 7.1, 7.4_

- [x] 18. Implement Metal input handling
  - Implement get_input() to poll macOS event queue
  - Implement _poll_macos_event() using NSEvent
  - Implement _translate_macos_event() to convert to KeyEvent
  - Map keyboard events, mouse events, and window events
  - Handle modifier keys (Shift, Control, Alt, Command)
  - _Requirements: 3.4, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 19. Implement Metal window management
  - Implement get_dimensions() to return grid dimensions
  - Implement refresh() and refresh_region()
  - Implement set_cursor_visibility() and move_cursor()
  - Handle window resize events
  - _Requirements: 3.5, 4.6, 8.3, 8.4_

- [x] 20. Implement Metal shutdown
  - Implement shutdown() method
  - Close native window
  - Release Metal resources (device, command queue, pipeline)
  - Clean up grid buffer
  - _Requirements: 3.1_

- [x] 21. Checkpoint - Verify Metal backend functionality
  - Ensure all tests pass, ask the user if questions arise.

- [x] 22. Implement command serialization
  - Create serialization.py module
  - Define command representation format (dict or dataclass)
  - Implement serialize_command() for all drawing operations
  - Include all parameters needed to reproduce commands
  - _Requirements: 13.1, 13.2_

- [x] 23. Implement command parsing
  - Implement parse_command() to reconstruct commands from serialized format
  - Validate command structure and parameters
  - Handle all command types (draw_text, draw_rect, etc.)
  - _Requirements: 13.3_

- [ ]* 23.1 Write property test for command serialization
  - **Property 10: Command serialization round-trip**
  - **Validates: Requirements 13.1, 13.2, 13.3**

- [x] 24. Implement command pretty-printing
  - Implement pretty_print_command() for human-readable output
  - Format commands with indentation and parameter names
  - Handle all command types
  - _Requirements: 13.4_

- [x]* 24.1 Write property test for pretty-printing
  - **Property 11: Pretty-print completeness**
  - **Validates: Requirements 13.4**

- [x] 25. Implement utility functions
  - Create utils.py module
  - Implement get_recommended_backend() for platform detection
  - Implement helper functions for color conversion
  - Implement validation functions for parameters
  - _Requirements: 16.1, 16.2_

- [x] 26. Create demo application structure
  - Create demo/demo_ttk.py
  - Implement command-line argument parsing (--backend option)
  - Implement backend selection logic
  - Set up main application loop
  - _Requirements: 6.1_

- [x] 27. Implement demo test interface
  - Create demo/test_interface.py
  - Implement test UI showing text in various colors and attributes
  - Implement rectangle and line drawing demonstrations
  - Implement input echo area
  - Display window dimensions and coordinate system
  - _Requirements: 6.2, 6.3, 6.4_

- [x] 28. Implement demo performance monitoring
  - Create demo/performance.py
  - Track frame rate (FPS)
  - Track rendering time per frame
  - Display performance metrics in demo UI
  - _Requirements: 6.6_

- [x] 29. Implement demo keyboard handling
  - Handle keyboard input in demo application
  - Display pressed keys with key codes and modifiers
  - Demonstrate special key handling
  - Allow quitting with 'q' or ESC
  - _Requirements: 6.3_

- [x] 30. Implement demo window resize handling
  - Handle resize events in demo application
  - Update UI layout on resize
  - Display updated dimensions
  - _Requirements: 6.4_

- [x] 31. Checkpoint - Verify demo application works with both backends
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 32. Write unit tests for Renderer ABC
  - Test that incomplete implementations raise TypeError
  - Test that all abstract methods are defined
  - _Requirements: 1.5_

- [ ]* 33. Write unit tests for KeyEvent
  - Test is_printable() method
  - Test is_special_key() method
  - Test has_modifier() method
  - Test KeyEvent creation with various parameters
  - _Requirements: 5.1, 5.2, 5.3_

- [ ]* 34. Write unit tests for CursesBackend
  - Test initialization and shutdown
  - Test dimension queries
  - Test coordinate system (0,0 at top-left)
  - Test out-of-bounds drawing
  - Test color pair initialization
  - Test input timeout behavior
  - _Requirements: 2.1, 2.4, 8.2, 8.5_

- [ ]* 35. Write unit tests for MetalBackend
  - Test initialization and shutdown
  - Test font validation (reject proportional fonts)
  - Test dimension queries
  - Test coordinate system
  - Test out-of-bounds drawing
  - Test color pair initialization
  - _Requirements: 3.1, 17.2, 17.5, 8.2, 8.5_

- [ ]* 36. Write property test for drawing operations
  - **Property 1: Drawing operations robustness**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.5**

- [ ]* 37. Write property test for color pair initialization
  - **Property 2: Color pair initialization robustness**
  - **Validates: Requirements 4.4, 7.1**

- [ ]* 38. Write property test for refresh operations
  - **Property 3: Refresh operations robustness**
  - **Validates: Requirements 4.6**

- [ ]* 39. Write property test for text attributes
  - **Property 4: Text attribute support**
  - **Validates: Requirements 2.2, 7.3, 9.1, 9.2, 9.3, 9.4**

- [ ]* 40. Write property test for printable character input
  - **Property 5: Printable character input translation**
  - **Validates: Requirements 5.1**

- [ ]* 41. Write property test for special key input
  - **Property 6: Special key input translation**
  - **Validates: Requirements 5.2**

- [ ]* 42. Write property test for modifier keys
  - **Property 7: Modifier key detection**
  - **Validates: Requirements 5.3**

- [ ]* 43. Write property test for mouse input
  - **Property 8: Mouse input handling**
  - **Validates: Requirements 5.4**

- [ ]* 44. Write property test for dimension queries
  - **Property 9: Dimension query consistency**
  - **Validates: Requirements 8.3**

- [ ]* 45. Write property test for backend color equivalence
  - **Property 12: Backend color equivalence**
  - **Validates: Requirements 3.3**

- [ ]* 46. Write property test for backend input equivalence
  - **Property 13: Backend input equivalence**
  - **Validates: Requirements 2.3, 3.4**

- [x] 47. Create library documentation
  - Write README.md with library overview and quick start
  - Document all public APIs with examples
  - Create usage guide for implementing new backends
  - Document coordinate system and color management
  - Include examples for common use cases
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 16.4_

- [x] 48. Create package configuration
  - Create setup.py or pyproject.toml
  - Define package metadata (name, version, description)
  - Specify dependencies (curses is built-in, PyObjC for Metal)
  - Configure package for distribution
  - _Requirements: 16.3_

- [x] 49. Test library independence from TFM
  - Verify no TFM-specific imports or dependencies
  - Verify library can be used standalone
  - Test with a simple non-TFM application
  - _Requirements: 16.5_

- [x] 50. Final checkpoint - Verify all requirements are met
  - Ensure all tests pass, ask the user if questions arise.
