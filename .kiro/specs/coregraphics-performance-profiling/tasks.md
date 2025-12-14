# Implementation Plan

- [x] 1. Create profiling infrastructure module
  - Create `src/tfm_profiling.py` with core profiling classes
  - Implement `ProfilingManager` class with initialization and state management
  - Implement `FPSTracker` class for frame timing and FPS calculation
  - Implement `ProfileWriter` class for file output with timestamped names
  - _Requirements: 1.1, 2.1, 3.2, 4.2, 6.1, 6.2, 6.3, 6.5_

- [ ]* 1.1 Write property test for filename uniqueness
  - **Property 3: Profile filename uniqueness**
  - **Validates: Requirements 3.4, 4.4, 6.3**

- [ ]* 1.2 Write property test for filename descriptiveness
  - **Property 4: Profile filename descriptiveness**
  - **Validates: Requirements 6.2**

- [ ]* 1.3 Write unit tests for profiling infrastructure
  - Test ProfilingManager initialization (enabled/disabled states)
  - Test FPSTracker frame recording and FPS calculation
  - Test ProfileWriter filename generation and file writing
  - Test output directory creation
  - _Requirements: 1.1, 2.1, 6.1, 6.5_

- [x] 2. Add command-line flag support
  - Modify `tfm.py` to add `--profile` argument to argument parser
  - Pass profiling flag to FileManager initialization
  - Add help text explaining profiling mode
  - _Requirements: 1.1, 1.3_

- [ ]* 2.1 Write unit test for command-line parsing
  - Test `--profile` flag recognition
  - Test default behavior without flag
  - _Requirements: 1.1, 1.3_

- [x] 3. Integrate profiling into FileManager initialization
  - Modify `FileManager.__init__()` to accept `profiling_enabled` parameter
  - Initialize `ProfilingManager` when profiling is enabled
  - Display profiling mode message when enabled
  - Ensure zero overhead when profiling is disabled
  - _Requirements: 1.1, 1.2, 1.4, 7.1_

- [ ]* 3.1 Write property test for profiling flag activation
  - **Property 1: Profiling flag enables profiling mode**
  - **Validates: Requirements 1.1, 1.2**

- [x] 4. Implement FPS tracking in main loop
  - Add frame start timing at beginning of `FileManager.run()` loop
  - Add frame end timing after drawing
  - Implement FPS calculation using sliding window of frame times
  - Add periodic FPS printing (every 5 seconds)
  - Format FPS output with timestamp and FPS value
  - _Requirements: 2.1, 2.2, 2.3, 2.5, 7.2_

- [ ]* 4.1 Write property test for FPS output format
  - **Property 2: FPS output format consistency**
  - **Validates: Requirements 2.3**

- [ ]* 4.2 Write unit tests for FPS tracking
  - Test FPS calculation with known frame times
  - Test print interval timing (5 seconds)
  - Test output format includes timestamp and FPS
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [x] 5. Implement key event profiling
  - Wrap `handle_key_input()` call with profiling when enabled
  - Use cProfile to collect function call statistics
  - Generate timestamped filename for key profile
  - Write profile data to file in output directory
  - Print profile file location after writing
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3, 5.4, 6.4_

- [ ]* 5.1 Write integration test for key event profiling
  - Test that profile files are created for key events
  - Test that filenames include timestamps
  - Test that files are in correct directory
  - _Requirements: 3.1, 3.3, 3.4, 3.5_

- [x] 6. Implement rendering profiling
  - Wrap `draw_interface()` call with profiling when enabled
  - Use cProfile to collect function call statistics
  - Generate timestamped filename for render profile
  - Write profile data to file in output directory
  - Print profile file location after writing
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 6.4_

- [ ]* 6.1 Write integration test for rendering profiling
  - Test that profile files are created for rendering
  - Test that filenames include timestamps
  - Test that files are in correct directory
  - _Requirements: 4.1, 4.3, 4.4, 4.5_

- [x] 7. Add profiling output directory management
  - Implement output directory creation on first profile write
  - Add README.txt to output directory explaining how to analyze profiles
  - Ensure directory path is configurable
  - Handle file I/O errors gracefully
  - _Requirements: 6.1, 6.5_

- [ ]* 7.1 Write property test for output directory creation
  - **Property 5: Output directory creation**
  - **Validates: Requirements 6.1**

- [ ]* 7.2 Write unit tests for directory management
  - Test directory creation when it doesn't exist
  - Test handling when directory already exists
  - Test README.txt creation
  - _Requirements: 6.1, 6.5_

- [x] 8. Optimize profiling overhead
  - Ensure profiling checks are minimal when disabled
  - Implement efficient frame time tracking (use deque with maxlen)
  - Ensure file I/O doesn't block main loop
  - Add conditional profiling to avoid profiling every frame
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 8.1 Write performance tests
  - Test that disabled profiling has zero overhead
  - Test that enabled profiling overhead is acceptable
  - Measure and verify profiling impact
  - _Requirements: 7.1, 7.5_

- [x] 9. Add error handling and edge cases
  - Handle file write errors gracefully
  - Handle missing output directory permissions
  - Handle disk full scenarios
  - Add fallback to temp directory if needed
  - Log errors without crashing application
  - _Requirements: 1.4_

- [ ]* 9.1 Write unit tests for error handling
  - Test file write error handling
  - Test directory permission errors
  - Test disk full scenarios
  - Test fallback behavior
  - _Requirements: 1.4_

- [x] 10. Create documentation
  - Add profiling section to user guide
  - Document `--profile` flag usage
  - Document how to analyze profile files
  - Add examples of using pstats and snakeviz
  - Document FPS output format
  - _Requirements: All_

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Create demo script
  - Create `demo/demo_profiling.py` to demonstrate profiling features
  - Show FPS output
  - Show profile file generation
  - Show how to analyze profile files
  - _Requirements: All_

- [x] 13. Final integration testing
  - Test complete profiling workflow end-to-end
  - Verify profiling works with CoreGraphics backend
  - Verify profiling works with curses backend
  - Test with various workloads (file operations, navigation, etc.)
  - Verify profile files can be analyzed with pstats
  - _Requirements: All_

- [x] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
