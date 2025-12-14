# Implementation Plan

- [ ] 1. Create baseline performance measurement tool
  - Create a script to measure current character drawing performance
  - Generate representative grid states (various characters, colors, attributes)
  - Measure t4-t3 time delta for full-screen dirty regions
  - Record baseline performance metrics
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 1.1 Write property test for baseline performance measurement
  - **Property 1: Character drawing performance target**
  - **Validates: Requirements 1.1**

- [ ] 2. Implement Optimization 1: Cache frequently accessed attributes
  - Extract char_width, char_height, rows, grid, color_pairs to local variables
  - Reuse cached values from Phase 1 if possible
  - Update the character drawing loop to use cached values
  - Ensure no behavioral changes
  - _Requirements: 3.1_

- [ ]* 2.1 Write property test for attribute caching correctness
  - **Property 2: Visual output equivalence**
  - **Validates: Requirements 3.5, 4.1**

- [ ]* 2.2 Measure performance improvement from Optimization 1
  - **Property 3: Performance improvement**
  - **Validates: Requirements 4.2, 4.4**

- [ ] 3. Implement Optimization 2: Pre-calculate row Y-coordinates
  - Move y-coordinate calculation outside the inner loop
  - Calculate y once per row instead of per cell
  - Verify correctness with existing tests
  - _Requirements: 3.3_

- [ ]* 3.1 Write property test for y-coordinate pre-calculation correctness
  - **Property 2: Visual output equivalence**
  - **Validates: Requirements 3.5, 4.1**

- [ ]* 3.2 Measure performance improvement from Optimization 2
  - **Property 3: Performance improvement**
  - **Validates: Requirements 4.2, 4.4**

- [ ] 4. Implement Optimization 3: Cache attribute dictionaries
  - Create attribute dictionary cache at class level
  - Key cache by (font, color, underline) tuple
  - Reuse cached dictionaries when possible
  - Verify identical behavior
  - _Requirements: 3.1, 3.4_

- [ ]* 4.1 Write property test for attribute dictionary caching correctness
  - **Property 2: Visual output equivalence**
  - **Validates: Requirements 3.5, 4.1**

- [ ]* 4.2 Measure performance improvement from Optimization 3
  - **Property 3: Performance improvement**
  - **Validates: Requirements 4.2, 4.4**

- [ ] 5. Checkpoint - Evaluate if target is met
  - Measure current performance after Optimizations 1-3
  - Compare against 0.01s (10ms) target
  - Decide if Optimization 5 (NSString direct) is needed
  - Document findings
  - _Requirements: 1.1, 4.2_

- [ ] 6. (Conditional) Implement Optimization 5: Use NSString drawAtPoint:withAttributes:
  - Only if performance target not met after Optimization 3
  - Replace NSAttributedString creation with NSString direct drawing
  - Maintain code clarity with comments
  - Measure performance impact
  - _Requirements: 3.2_

- [ ]* 6.1 Write property test for NSString direct drawing correctness
  - **Property 2: Visual output equivalence**
  - **Validates: Requirements 3.5, 4.1**

- [ ]* 6.2 Measure performance improvement from Optimization 5
  - **Property 3: Performance improvement**
  - **Validates: Requirements 4.2, 4.4**

- [ ] 7. (Conditional) Implement Optimization 4: Batch character drawing
  - Only if performance target still not met
  - Accumulate adjacent characters with same attributes
  - Draw batches as single NSAttributedString
  - Measure performance impact
  - _Requirements: 3.3_

- [ ]* 7.1 Write property test for batched drawing correctness
  - **Property 2: Visual output equivalence**
  - **Validates: Requirements 3.5, 4.1**

- [ ]* 7.2 Measure performance improvement from Optimization 4
  - **Property 3: Performance improvement**
  - **Validates: Requirements 4.2, 4.4**

- [ ] 8. Run comprehensive visual correctness tests
  - Run all existing visual correctness tests
  - Verify no regressions in visual output
  - Test with various grid states and dirty regions
  - Test character rendering with different attributes (bold, underline, reverse)
  - _Requirements: 4.1, 4.3_

- [ ] 9. Create performance comparison documentation
  - Document baseline vs optimized performance
  - Create before/after comparison charts
  - Explain which optimizations had the most impact
  - Document any trade-offs made
  - _Requirements: 2.3, 2.4_

- [ ] 10. Update implementation documentation
  - Document the optimization techniques used
  - Explain the performance improvements achieved
  - Add comments to the optimized code
  - Update developer documentation
  - _Requirements: 2.4_

- [ ] 11. Final checkpoint - Verify all requirements met
  - Ensure all tests pass, ask the user if questions arise
  - Verify performance target achieved (< 0.01s / 10ms)
  - Verify visual correctness maintained
  - Verify all documentation complete
  - _Requirements: 1.1, 3.5, 4.1, 4.2, 4.3, 4.4_
