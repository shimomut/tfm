# Implementation Plan

- [x] 1. Establish baseline performance measurement
  - Create performance test script that fills 24x80 grid with non-space characters
  - Apply various attributes (colors, bold, underline, reverse)
  - Measure and record current t4-t3 time
  - Verify baseline demonstrates approximately 30ms (0.03 seconds) as expected
  - Create demo script for visual verification
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - _Status: COMPLETED - test/test_character_drawing_performance.py and demo/demo_character_drawing_optimization.py exist, baseline measurements recorded_

- [ ] 2. Implement AttributeDictCache class
  - Create AttributeDictCache class with cache dictionary
  - Implement get_attributes() method with cache lookup logic
  - Integrate with existing FontCache and ColorCache
  - Build NSDictionary with NSFont, NSForegroundColor, and optional NSUnderlineStyle
  - Implement clear() method for cache invalidation
  - _Requirements: 3.1, 3.4_

- [ ]* 2.1 Write unit tests for AttributeDictCache
  - Test cache hit/miss behavior
  - Test correct attribute dictionary construction
  - Test cache clearing functionality
  - Test integration with font and color caches
  - _Requirements: 3.1, 3.4_

- [ ]* 2.2 Write property test for AttributeDictCache
  - **Property 3: Attribute Dictionary Cache Correctness**
  - **Validates: Requirements 3.4**
  - Generate random sequences of attribute lookups
  - Verify cache returns same NSDictionary object for identical keys
  - Verify cache hit rate improves with repeated patterns
  - _Requirements: 3.4_

- [ ] 3. Implement AttributedStringCache class
  - Create AttributedStringCache class with cache dictionary
  - Implement get_attributed_string() method with cache lookup
  - Integrate with AttributeDictCache for building new strings
  - Implement LRU eviction when cache exceeds max_cache_size (1000 entries)
  - Implement clear() method for cache invalidation
  - _Requirements: 3.2, 3.4_

- [ ]* 3.1 Write unit tests for AttributedStringCache
  - Test cache hit/miss behavior for repeated strings
  - Test LRU eviction when cache limit reached
  - Test cache clearing functionality
  - Test correct attributed string construction
  - _Requirements: 3.2, 3.4_

- [ ]* 3.2 Write property test for AttributedStringCache
  - **Property 5: NSAttributedString Cache Correctness**
  - **Validates: Requirements 3.4**
  - Generate random sequences of (text, attributes) lookups
  - Verify cache returns same NSAttributedString object for identical keys
  - Verify LRU eviction maintains most-used entries
  - _Requirements: 3.4_

- [ ] 4. Implement character batching logic
  - Modify drawRect_() character drawing loop to identify continuous character runs
  - Implement space skipping logic for efficient iteration
  - Implement batch boundary detection (attribute changes)
  - Collect characters with same attributes into batch list
  - Calculate correct x-coordinate for batch start position
  - _Requirements: 3.3, 3.5_

- [ ]* 4.1 Write unit tests for character batching
  - Test identification of continuous character runs
  - Test batch boundary detection on attribute changes
  - Test space skipping within batching logic
  - Test coordinate calculations for batches
  - Test edge cases (empty region, single char, all same attrs, all different attrs)
  - _Requirements: 3.3, 3.5_

- [ ]* 4.2 Write property test for batching correctness
  - **Property 6: Batching Correctness**
  - **Validates: Requirements 3.5**
  - Generate random rows with various attribute patterns
  - Compare batched drawing output to individual character drawing
  - Verify pixel-identical results
  - _Requirements: 3.5_

- [ ] 5. Integrate caches into character drawing loop
  - Instantiate AttributeDictCache in CoreGraphicsBackend.__init__()
  - Instantiate AttributedStringCache in CoreGraphicsBackend.__init__()
  - Replace individual character drawing with batched drawing
  - Use AttributedStringCache.get_attributed_string() for each batch
  - Call drawAtPoint_() once per batch instead of per character
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [ ]* 5.1 Write integration tests for cache integration
  - Test attribute dict cache with existing font cache
  - Test attribute dict cache with existing color cache
  - Test NSAttributedString cache with attribute dict cache
  - Test full rendering pipeline with all caches
  - _Requirements: 3.1, 3.2, 3.4_

- [ ] 6. Implement cache clearing on resize and color scheme change
  - Hook AttributeDictCache.clear() into terminal resize event
  - Hook AttributedStringCache.clear() into terminal resize event
  - Hook AttributeDictCache.clear() into color scheme change event
  - Hook AttributedStringCache.clear() into color scheme change event
  - Verify caches rebuild correctly after clearing
  - _Requirements: 3.4_

- [ ]* 6.1 Write tests for cache clearing
  - Test all caches clear on terminal resize
  - Test all caches clear on color scheme change
  - Test LRU eviction in NSAttributedString cache under memory pressure
  - Verify caches rebuild correctly after clearing
  - _Requirements: 3.4_

- [ ] 7. Add performance instrumentation
  - Add metrics tracking for attribute dict cache hit/miss rates
  - Add metrics tracking for NSAttributedString cache hit/miss rates
  - Add metrics tracking for average batch size
  - Add metrics tracking for number of batches per frame
  - Add metrics tracking for average time per character and per batch
  - Create CharacterDrawingMetrics dataclass for structured metrics
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 8. Checkpoint - Verify performance improvement
  - Run baseline performance test from task 1
  - Measure optimized t4-t3 time (target: <10ms)
  - Calculate improvement percentage (target: 70-85% reduction)
  - Verify visual output matches baseline (pixel-identical)
  - Review cache hit rates and batching efficiency
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 1.1, 1.2, 3.5, 5.1, 5.2, 5.3, 5.4_

- [ ]* 9. Write property test for visual equivalence
  - **Property 1: Visual Output Equivalence**
  - **Validates: Requirements 3.5**
  - Generate random grid states with various attributes
  - Render with both original and optimized implementations
  - Compare output pixel-by-pixel
  - _Requirements: 3.5_

- [ ]* 10. Write property test for performance improvement
  - **Property 2: Performance Improvement**
  - **Validates: Requirements 1.1**
  - Generate maximum workload scenarios (full grid, all non-space)
  - Measure character drawing phase time
  - Verify time is consistently under 10ms threshold
  - _Requirements: 1.1_

- [ ]* 11. Write property test for attribute dictionary completeness
  - **Property 4: Attribute Dictionary Completeness**
  - **Validates: Requirements 3.1, 3.5**
  - Generate random attribute combinations
  - Inspect cached dictionaries
  - Verify all required keys present (NSFont, NSForegroundColor, NSUnderlineStyle when applicable)
  - _Requirements: 3.1, 3.5_

- [ ] 12. Final checkpoint - Comprehensive testing
  - Run all unit tests and verify they pass
  - Run all property-based tests and verify they pass
  - Test with real TFM usage scenarios (file browsing, text viewing)
  - Verify no visual regressions in actual application use
  - Verify performance meets <10ms target consistently
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 1.1, 3.5, 5.1, 5.2, 5.3, 5.4_
