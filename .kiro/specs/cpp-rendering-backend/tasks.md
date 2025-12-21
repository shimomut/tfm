# Implementation Plan: C++ Rendering Backend

## Overview

This plan outlines the implementation of a C++ rendering backend for the CoreGraphics backend, providing direct API access for improved performance while maintaining backward compatibility with the existing PyObjC implementation.

## Tasks

- [ ] 1. Set up C++ extension module infrastructure
  - Create `src/cpp_renderer.cpp` with Python extension boilerplate
  - Configure `setup.py` to build the C++ extension with CoreGraphics/CoreText linking
  - Add compiler flags for C++17, optimization, and warnings
  - Verify module can be imported from Python
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ]* 1.1 Write unit test for module import
  - Test that `import cpp_renderer` succeeds after build
  - Test that module has expected functions
  - _Requirements: 9.4_

- [ ] 2. Implement core data structure parsing
  - [ ] 2.1 Implement `parse_grid()` function to convert Python grid to C++ vector
    - Extract character, color_pair, and attributes from each cell tuple
    - Handle UTF-8 encoding for characters
    - Validate grid dimensions match expected rows/cols
    - _Requirements: 1.2, 11.5_

  - [ ] 2.2 Implement `parse_color_pairs()` function to convert Python dict to C++ map
    - Extract foreground and background RGB tuples
    - Pack RGB values into uint32_t (0x00RRGGBB format)
    - Validate color values are in range 0-255
    - _Requirements: 1.2, 11.5_

  - [ ]* 2.3 Write unit tests for data structure parsing
    - Test valid grid parsing
    - Test valid color pair parsing
    - Test error handling for invalid data
    - _Requirements: 13.1, 13.4_

- [ ] 3. Implement ColorCache class
  - [ ] 3.1 Implement ColorCache constructor and destructor
    - Initialize cache map and max_size
    - Ensure proper cleanup of CGColorRef objects in destructor
    - _Requirements: 4.2, 12.1_

  - [ ] 3.2 Implement `get_color()` method
    - Check cache for existing color
    - Create CGColorRef if not cached
    - Implement LRU eviction when cache is full
    - _Requirements: 4.2, 4.4_

  - [ ] 3.3 Implement `clear()` method
    - Release all cached CGColorRef objects
    - Clear the cache map
    - _Requirements: 4.5, 12.1_

  - [ ]* 3.4 Write unit tests for ColorCache
    - Test cache hit/miss behavior
    - Test LRU eviction
    - Test memory cleanup
    - _Requirements: 13.5_

- [ ] 4. Implement FontCache class
  - [ ] 4.1 Implement FontCache constructor and destructor
    - Store base_font reference
    - Initialize cache map
    - Ensure proper cleanup of CTFontRef objects in destructor
    - _Requirements: 4.1, 12.1_

  - [ ] 4.2 Implement `get_font()` method
    - Check cache for font with attributes
    - Apply BOLD attribute using CTFontCreateCopyWithSymbolicTraits if needed
    - Cache and return font
    - _Requirements: 4.1, 1.5_

  - [ ] 4.3 Implement `clear()` method
    - Release all cached CTFontRef objects
    - Clear the cache map
    - _Requirements: 4.5, 12.1_

  - [ ]* 4.4 Write unit tests for FontCache
    - Test cache hit/miss behavior
    - Test BOLD attribute application
    - Test memory cleanup
    - _Requirements: 13.5_

- [ ] 5. Implement AttributeDictCache class
  - [ ] 5.1 Implement AttributeDictCache constructor and destructor
    - Store references to FontCache and ColorCache
    - Initialize cache map and metrics counters
    - Ensure proper cleanup of CFDictionaryRef objects in destructor
    - _Requirements: 4.3, 12.1_

  - [ ] 5.2 Implement `get_attributes()` method
    - Check cache for attribute dictionary
    - Get font from FontCache
    - Get color from ColorCache
    - Create CFDictionary with kCTFontAttributeName and kCTForegroundColorAttributeName
    - Add kCTUnderlineStyleAttributeName if underline is true
    - Track cache hits/misses
    - _Requirements: 4.3, 1.5_

  - [ ] 5.3 Implement metrics methods
    - Implement `get_hit_count()`, `get_miss_count()`, `reset_metrics()`
    - _Requirements: 10.2, 10.5_

  - [ ]* 5.4 Write unit tests for AttributeDictCache
    - Test cache hit/miss behavior
    - Test attribute dictionary creation
    - Test metrics tracking
    - _Requirements: 13.5_

- [ ] 6. Checkpoint - Verify caching infrastructure
  - Ensure all cache classes compile and link correctly
  - Verify memory management with Instruments (no leaks)
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement RectangleBatcher class
  - [ ] 7.1 Implement RectangleBatcher constructor
    - Initialize batches vector and current_batch optional
    - _Requirements: 2.1_

  - [ ] 7.2 Implement `add_cell()` method
    - Check if cell can extend current batch (same row, color, adjacent)
    - Extend current batch if possible
    - Otherwise, finish current batch and start new one
    - _Requirements: 2.1_

  - [ ] 7.3 Implement `finish_row()` and `get_batches()` methods
    - `finish_row()`: Add current batch to batches vector
    - `get_batches()`: Return batches and clear state
    - _Requirements: 2.1_

  - [ ]* 7.4 Write unit tests for RectangleBatcher
    - Test batching of adjacent cells
    - Test batch separation on color change
    - Test batch separation on row change
    - _Requirements: 13.5_

- [ ] 8. Implement coordinate transformation utilities
  - [ ] 8.1 Implement `calculate_dirty_cells()` function
    - Convert CGRect to cell coordinates
    - Handle TTK (top-left) to CoreGraphics (bottom-left) transformation
    - Clamp to valid grid bounds
    - _Requirements: 1.4, 2.5_

  - [ ] 8.2 Implement `ttk_to_cg_y()` function
    - Convert TTK row to CoreGraphics y-coordinate
    - Formula: y = (rows - row - 1) * char_height
    - _Requirements: 1.4_

  - [ ]* 8.3 Write unit tests for coordinate transformation
    - Test dirty cell calculation
    - Test coordinate transformation
    - Test boundary clamping
    - _Requirements: 13.5_

- [ ] 9. Implement background rendering
  - [ ] 9.1 Implement `render_backgrounds()` function
    - Iterate through dirty region cells
    - Accumulate cells into RectangleBatcher
    - Handle edge cell extension for window padding
    - _Requirements: 2.1, 2.3_

  - [ ] 9.2 Implement `draw_batched_backgrounds()` function
    - Iterate through batches from RectangleBatcher
    - Set fill color with CGContextSetRGBFillColor
    - Draw rectangle with CGContextFillRect
    - _Requirements: 2.2_

  - [ ]* 9.3 Write integration test for background rendering
    - Create test grid with various background colors
    - Render backgrounds
    - Verify correct number of batches
    - _Requirements: 13.1_

- [ ] 10. Implement character rendering
  - [ ] 10.1 Implement `render_characters()` function
    - Iterate through dirty region cells
    - Skip spaces (backgrounds already rendered)
    - Batch consecutive characters with same attributes
    - _Requirements: 3.1, 3.3_

  - [ ] 10.2 Implement `draw_character_batch()` function
    - Get attribute dictionary from AttributeDictCache
    - Create CFAttributedString with text and attributes
    - Create CTLine from attributed string
    - Set text position with CGContextSetTextPosition
    - Draw with CTLineDraw
    - _Requirements: 3.2, 1.5_

  - [ ] 10.3 Implement wide character handling
    - Detect wide characters using Unicode properties
    - Skip placeholder cells (empty strings)
    - _Requirements: 3.4_

  - [ ]* 10.4 Write integration test for character rendering
    - Test normal characters
    - Test wide characters (Japanese, Chinese)
    - Test character batching
    - _Requirements: 13.1_

- [ ] 11. Checkpoint - Verify core rendering
  - Test background and character rendering together
  - Compare output with PyObjC rendering visually
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement cursor rendering
  - [ ] 12.1 Implement `render_cursor()` function
    - Check cursor_visible flag
    - Calculate cursor pixel position
    - Set fill color (semi-transparent white)
    - Draw filled rectangle with CGContextFillRect
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 12.2 Write unit test for cursor rendering
    - Test cursor visibility flag
    - Test cursor position calculation
    - _Requirements: 13.1_

- [ ] 13. Implement IME marked text rendering
  - [ ] 13.1 Implement `render_marked_text()` function
    - Check if marked_text is non-empty
    - Calculate position at cursor location
    - Create attributed string with underline
    - Draw with CTLineDraw
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 13.2 Write unit test for IME marked text
    - Test marked text rendering
    - Test empty marked text (no rendering)
    - _Requirements: 13.1_

- [ ] 14. Implement main render_frame() function
  - [ ] 14.1 Implement parameter validation
    - Validate CGContext is not null
    - Validate grid dimensions
    - Validate color_pairs dict
    - Raise Python exceptions for invalid parameters
    - _Requirements: 11.2, 11.5_

  - [ ] 14.2 Implement rendering pipeline
    - Parse grid and color_pairs
    - Calculate dirty cells
    - Render backgrounds
    - Render characters
    - Render cursor if visible
    - Render marked text if present
    - _Requirements: 1.2, 1.3_

  - [ ] 14.3 Implement error handling
    - Wrap rendering in try-catch
    - Convert C++ exceptions to Python exceptions
    - Log errors for debugging
    - _Requirements: 11.1, 11.3_

  - [ ]* 14.4 Write integration test for full rendering
    - Test complete rendering pipeline
    - Test error handling
    - _Requirements: 13.1_

- [ ] 15. Implement performance metrics
  - [ ] 15.1 Add metrics tracking to Renderer class
    - Track frames_rendered, total_render_time, total_batches
    - Update metrics in render_frame()
    - _Requirements: 10.1, 10.3_

  - [ ] 15.2 Implement `get_performance_metrics()` function
    - Calculate averages and rates
    - Return Python dict with metrics
    - _Requirements: 10.4_

  - [ ] 15.3 Implement `reset_metrics()` function
    - Reset all counters to zero
    - _Requirements: 10.5_

  - [ ]* 15.4 Write unit test for performance metrics
    - Test metrics tracking
    - Test metrics reset
    - _Requirements: 13.1_

- [ ] 16. Checkpoint - Verify complete C++ implementation
  - Run all unit tests
  - Run integration tests
  - Check for memory leaks with Instruments
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Implement backend selector in Python
  - [ ] 17.1 Add USE_CPP_RENDERING flag to CoreGraphicsBackend
    - Read from environment variable TTK_USE_CPP_RENDERING
    - Default to False for backward compatibility
    - _Requirements: 7.2, 7.3_

  - [ ] 17.2 Implement C++ module import with fallback
    - Try to import cpp_renderer if USE_CPP_RENDERING is True
    - Fall back to PyObjC if import fails
    - Log which implementation is being used
    - _Requirements: 7.4, 7.5_

  - [ ] 17.3 Modify TTKView.drawRect_() to use backend selector
    - Check USE_CPP_RENDERING flag
    - Call C++ render_frame() if enabled
    - Fall back to PyObjC rendering on error
    - _Requirements: 7.1, 8.1_

  - [ ]* 17.4 Write integration test for backend switching
    - Test switching between PyObjC and C++
    - Test fallback behavior
    - _Requirements: 13.1_

- [ ] 18. Implement visual equivalence testing
  - [ ] 18.1 Create test harness for rendering to offscreen buffers
    - Render with PyObjC to CGBitmapContext
    - Render with C++ to CGBitmapContext
    - _Requirements: 13.3_

  - [ ] 18.2 Implement pixel comparison function
    - Compare images pixel-by-pixel
    - Calculate difference percentage
    - _Requirements: 13.2_

  - [ ]* 18.3 Write property test for visual equivalence
    - Generate random grids
    - Verify C++ output matches PyObjC output
    - _Requirements: 13.1_

- [ ] 19. Checkpoint - Verify integration and compatibility
  - Test backend switching
  - Verify visual equivalence
  - Test with real TFM application
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 20. Performance benchmarking
  - [ ] 20.1 Create benchmark script
    - Measure rendering time for various grid sizes
    - Compare C++ vs PyObjC performance
    - _Requirements: 10.1_

  - [ ] 20.2 Profile with Instruments
    - Identify performance bottlenecks
    - Verify cache effectiveness
    - _Requirements: 10.2_

  - [ ] 20.3 Document performance results
    - Create performance comparison table
    - Document cache hit rates
    - _Requirements: 14.4_

- [ ] 21. Documentation
  - [ ] 21.1 Write API documentation
    - Document all public C++ functions
    - Document Python interface
    - _Requirements: 14.1_

  - [ ] 21.2 Write architecture documentation
    - Explain design decisions
    - Document caching strategies
    - _Requirements: 14.2_

  - [ ] 21.3 Write build and installation guide
    - Document build requirements
    - Provide step-by-step instructions
    - _Requirements: 14.3_

  - [ ] 21.4 Write troubleshooting guide
    - Document common issues and solutions
    - Provide debugging tips
    - _Requirements: 14.5_

- [ ] 22. Final checkpoint - Complete implementation
  - All tests passing
  - Documentation complete
  - Performance benchmarks documented
  - Ready for release

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
