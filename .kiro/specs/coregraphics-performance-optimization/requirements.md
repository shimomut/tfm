# Requirements Document

## Introduction

This document specifies the requirements for optimizing the performance of the CoreGraphics backend's `drawRect_` method in TFM. Profiling data has identified `drawRect_` as a significant performance bottleneck, causing slow rendering and reduced FPS. This optimization project will analyze the bottleneck, implement targeted improvements, and verify performance gains through measurement.

## Glossary

- **TFM**: TUI File Manager - the terminal-based file manager application
- **CoreGraphics Backend**: The macOS-native rendering backend that uses CoreGraphics/Metal for display
- **drawRect_**: The method in the CoreGraphics backend responsible for drawing filled rectangles
- **FPS**: Frames Per Second - a measure of rendering performance
- **Profiling Data**: Performance measurements collected using cProfile showing function call times
- **Rendering Loop**: The main loop that draws the UI to the screen
- **CoreGraphics API**: Apple's 2D drawing API (part of Quartz) used for rendering
- **Batch Rendering**: Combining multiple drawing operations into fewer API calls
- **Draw Call**: A single request to the CoreGraphics API to render something
- **Native Implementation**: Code written in Objective-C or Swift that can directly interface with CoreGraphics
- **Python-C Bridge**: The interface layer between Python code and native Objective-C/Swift code

## Requirements

### Requirement 1

**User Story:** As a developer, I want to analyze the current `drawRect_` implementation, so that I can identify specific performance bottlenecks.

#### Acceptance Criteria

1. WHEN analyzing the `drawRect_` method THEN the system SHALL identify all operations that contribute to execution time
2. WHEN profiling data is examined THEN the analysis SHALL determine which sub-operations are most expensive
3. WHEN the implementation is reviewed THEN the analysis SHALL identify redundant operations or inefficient patterns
4. WHEN the analysis is complete THEN it SHALL document specific optimization opportunities
5. WHEN optimization opportunities are identified THEN they SHALL be prioritized by expected performance impact

### Requirement 2

**User Story:** As a developer, I want to reduce redundant CoreGraphics API calls in `drawRect_`, so that rendering performance improves.

#### Acceptance Criteria

1. WHEN multiple rectangles with the same color are drawn THEN the system SHALL batch them into a single draw call
2. WHEN drawing operations are batched THEN the system SHALL maintain correct visual output
3. WHEN batching is implemented THEN it SHALL reduce the total number of CoreGraphics API calls
4. WHEN the same rectangle is drawn multiple times THEN the system SHALL eliminate duplicate operations
5. WHEN batching logic is added THEN it SHALL not increase memory usage significantly

### Requirement 3

**User Story:** As a developer, I want to optimize color conversion operations, so that color processing overhead is minimized.

#### Acceptance Criteria

1. WHEN colors are converted THEN the system SHALL cache frequently used color values
2. WHEN the same color is requested multiple times THEN the system SHALL return the cached value
3. WHEN color caching is implemented THEN it SHALL reduce redundant color conversion calculations
4. WHEN the color cache is used THEN it SHALL maintain color accuracy
5. WHEN the cache size is managed THEN it SHALL not grow unbounded

### Requirement 4

**User Story:** As a developer, I want to minimize coordinate transformation overhead, so that position calculations are efficient.

#### Acceptance Criteria

1. WHEN coordinate transformations are performed THEN the system SHALL use efficient calculation methods
2. WHEN transformations are repeated THEN the system SHALL cache transformation results where possible
3. WHEN transformation logic is optimized THEN it SHALL maintain correct positioning
4. WHEN integer coordinates are sufficient THEN the system SHALL avoid floating-point operations
5. WHEN transformation overhead is reduced THEN it SHALL be measurable in profiling data

### Requirement 5

**User Story:** As a developer, I want to implement lazy evaluation for drawing operations, so that unnecessary draws are avoided.

#### Acceptance Criteria

1. WHEN a rectangle is outside the visible area THEN the system SHALL skip drawing it
2. WHEN rectangles overlap completely THEN the system SHALL only draw the topmost rectangle
3. WHEN culling is implemented THEN it SHALL reduce the number of draw operations
4. WHEN culling logic is added THEN it SHALL maintain correct visual output
5. WHEN culling is active THEN the performance improvement SHALL be measurable

### Requirement 6

**User Story:** As a developer, I want to measure the performance improvement from optimizations, so that I can verify the changes are effective.

#### Acceptance Criteria

1. WHEN optimizations are implemented THEN the system SHALL measure FPS before and after changes
2. WHEN performance is measured THEN the system SHALL use the existing profiling infrastructure
3. WHEN measurements are taken THEN they SHALL be conducted under identical conditions
4. WHEN FPS improvements are measured THEN they SHALL show at least 20% improvement
5. WHEN profiling data is compared THEN it SHALL show reduced time spent in `drawRect_`

### Requirement 7

**User Story:** As a developer, I want to ensure optimizations don't break existing functionality, so that visual correctness is maintained.

#### Acceptance Criteria

1. WHEN optimizations are applied THEN all existing visual tests SHALL pass
2. WHEN rendering output is compared THEN optimized and original output SHALL be visually identical
3. WHEN edge cases are tested THEN the system SHALL handle them correctly
4. WHEN different color combinations are used THEN they SHALL render correctly
5. WHEN various rectangle sizes are drawn THEN they SHALL appear correctly

### Requirement 8

**User Story:** As a developer, I want to evaluate native language implementation options, so that I can determine if rewriting critical sections in Objective-C or Swift would improve performance.

#### Acceptance Criteria

1. WHEN evaluating native implementation THEN the analysis SHALL identify which portions of `drawRect_` are most expensive
2. WHEN considering Objective-C or Swift THEN the evaluation SHALL estimate the performance improvement potential
3. WHEN native code is considered THEN the analysis SHALL assess the complexity of the Python-C bridge
4. WHEN implementation options are compared THEN the evaluation SHALL consider maintainability trade-offs
5. WHEN a decision is made THEN it SHALL be documented with performance data and rationale

### Requirement 9

**User Story:** As a developer, I want to document the optimization techniques used, so that future developers understand the implementation.

#### Acceptance Criteria

1. WHEN optimizations are implemented THEN the code SHALL include comments explaining the techniques
2. WHEN optimization decisions are made THEN they SHALL be documented with rationale
3. WHEN performance characteristics change THEN the documentation SHALL explain the improvements
4. WHEN the optimization is complete THEN a summary document SHALL describe the changes
5. WHEN future maintenance is needed THEN the documentation SHALL provide sufficient context
