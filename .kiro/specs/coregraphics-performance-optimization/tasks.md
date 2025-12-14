# Implementation Plan

- [ ] 1. Establish performance baseline
  - Run TFM with profiling enabled and record current FPS
  - Capture cProfile data for drawRect_ method
  - Document current performance metrics (FPS, API call count, time per frame)
  - Create benchmark script for consistent performance testing
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 2. Implement ColorCache class
  - Create ColorCache class in coregraphics_backend.py
  - Implement get_color() method with RGB tuple caching
  - Implement cache size management with simple LRU eviction
  - Add clear() method for cache reset
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 2.1 Write property test for ColorCache
  - **Property 3: Color cache correctness**
  - **Validates: Requirements 3.4**

- [ ] 3. Implement FontCache class
  - Create FontCache class in coregraphics_backend.py
  - Implement get_font() method with attribute-based caching
  - Handle BOLD attribute with NSFontManager
  - Add clear() method for cache reset
  - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 3.1 Write property test for FontCache
  - **Property 6: Font attribute preservation**
  - **Validates: Requirements 7.4**

- [ ] 4. Implement RectangleBatcher class
  - Create RectangleBatcher and RectBatch classes
  - Implement add_cell() method for batch accumulation
  - Implement _can_extend_batch() for adjacency checking
  - Implement finish_row() and get_batches() methods
  - _Requirements: 2.1, 2.2, 2.4, 2.5_

- [ ]* 4.1 Write property test for RectangleBatcher
  - **Property 2: Batch coverage completeness**
  - **Validates: Requirements 2.2**

- [ ]* 4.2 Write property test for API call reduction
  - **Property 5: API call reduction**
  - **Validates: Requirements 2.3**

- [ ] 5. Implement DirtyRegionCalculator
  - Create DirtyRegionCalculator class with static method
  - Implement get_dirty_cells() for coordinate conversion
  - Handle CoreGraphics bottom-left to TTK top-left conversion
  - Add boundary clamping for edge cases
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 5.1 Write property test for DirtyRegionCalculator
  - **Property 4: Dirty region containment**
  - **Validates: Requirements 5.4**

- [ ] 6. Integrate caches into CoreGraphicsBackend initialization
  - Add _color_cache and _font_cache to __init__
  - Initialize ColorCache with max_size=256
  - Initialize FontCache with base font
  - Update any cleanup code to clear caches
  - _Requirements: 3.1, 4.1_

- [ ] 7. Refactor drawRect_ Phase 1 - Background batching
  - Add dirty region calculation at start of drawRect_
  - Create RectangleBatcher instance
  - Iterate through dirty region cells
  - Accumulate cells into batches by color
  - Draw all batched backgrounds with cached colors
  - _Requirements: 2.1, 2.2, 2.3, 5.1, 5.2_

- [ ] 8. Refactor drawRect_ Phase 2 - Character drawing
  - Iterate through dirty region cells for non-space characters
  - Use cached colors from ColorCache
  - Use cached fonts from FontCache
  - Create NSAttributedString and draw characters
  - Maintain underline attribute handling
  - _Requirements: 3.2, 4.2_

- [ ] 9. Update cursor drawing to use ColorCache
  - Replace direct NSColor creation with ColorCache.get_color()
  - Maintain cursor visibility and positioning logic
  - _Requirements: 3.2_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Measure optimized performance
  - Run TFM with profiling enabled
  - Record new FPS measurements
  - Capture new cProfile data
  - Compare with baseline metrics
  - Calculate percentage improvement
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 11.1 Write integration test for performance improvement
  - Verify FPS improvement is at least 20%
  - Verify reduced time in drawRect_
  - _Requirements: 6.4_

- [ ] 12. Visual correctness verification
  - Create test script that renders complex UI
  - Capture screenshots before and after optimization
  - Implement pixel-by-pixel comparison
  - Test with various color schemes and content types
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 12.1 Write property test for visual output equivalence
  - **Property 1: Visual output equivalence**
  - **Validates: Requirements 7.2**

- [ ] 13. Evaluate native implementation need
  - Review performance measurements from task 11
  - If FPS < 30, document need for native implementation
  - If FPS 30-60, document as acceptable
  - If FPS > 60, document as excellent
  - Create decision document with rationale
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 14. Document optimization implementation
  - Add inline comments explaining batching logic
  - Document cache sizing decisions
  - Explain coordinate transformation preservation
  - Create summary of performance improvements
  - Document any trade-offs or limitations
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 15. Create end-user documentation
  - Document performance improvements in user-facing docs
  - Explain any visible changes (if any)
  - Update TFM user guide with performance notes
  - _Requirements: 9.4_

- [ ] 16. Create developer documentation
  - Document optimization techniques used
  - Explain batching algorithm
  - Document cache implementations
  - Provide guidance for future optimizations
  - _Requirements: 9.1, 9.2, 9.3, 9.5_

- [ ] 17. Final checkpoint - Verify all requirements met
  - Ensure all tests pass, ask the user if questions arise.
