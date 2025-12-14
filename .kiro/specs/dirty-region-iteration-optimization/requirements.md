# Requirements Document

## Introduction

The CoreGraphics backend's drawRect_() method contains a performance bottleneck in the dirty region iteration phase. Profiling shows that the section "Iterate through dirty region cells and accumulate into batches" (t2-t1) takes approximately 0.2 seconds, which is unacceptable for smooth rendering. This feature aims to investigate and optimize this critical rendering path.

## Glossary

- **Dirty Region**: The rectangular area of the screen that needs to be redrawn, provided by Cocoa's drawRect_ method
- **Cell**: A single character position in the grid, containing (char, color_pair, attributes)
- **Batching**: The process of combining adjacent cells with the same background color into a single rectangle for efficient rendering
- **RectangleBatcher**: A class that accumulates adjacent cells with the same background color into batches
- **Color Pair**: A tuple of (foreground_rgb, background_rgb) colors associated with an ID
- **Grid**: The 2D array storing all character cells (rows x cols)
- **CoreGraphics**: Apple's 2D graphics rendering framework
- **NSRect**: A rectangle structure in CoreGraphics coordinate system

## Requirements

### Requirement 1

**User Story:** As a TFM user, I want the file manager to render updates quickly, so that I can navigate and work efficiently without lag.

#### Acceptance Criteria

1. WHEN the dirty region iteration executes THEN the system SHALL complete in under 0.05 seconds for a full-screen update (24x80 grid)
2. WHEN iterating through cells THEN the system SHALL minimize redundant calculations and lookups
3. WHEN accessing grid data THEN the system SHALL use the most efficient data access patterns
4. WHEN calculating pixel positions THEN the system SHALL avoid repeated arithmetic operations where possible
5. WHEN looking up color pairs THEN the system SHALL minimize dictionary access overhead

### Requirement 2

**User Story:** As a developer, I want to understand the performance bottleneck, so that I can make informed optimization decisions.

#### Acceptance Criteria

1. WHEN analyzing the current implementation THEN the system SHALL identify which specific operations consume the most time
2. WHEN profiling the code THEN the system SHALL measure the time spent in grid access, color pair lookups, and pixel calculations separately
3. WHEN comparing alternatives THEN the system SHALL provide quantitative performance measurements
4. WHEN documenting findings THEN the system SHALL explain the root causes of the performance issues

### Requirement 3

**User Story:** As a developer, I want to optimize the dirty region iteration, so that rendering performance improves significantly.

#### Acceptance Criteria

1. WHEN optimizing grid access THEN the system SHALL use local variable caching where beneficial
2. WHEN optimizing color pair lookups THEN the system SHALL minimize dictionary access frequency
3. WHEN optimizing pixel calculations THEN the system SHALL pre-calculate or cache repeated values
4. WHEN optimizing the batching process THEN the system SHALL reduce the overhead of add_cell() calls
5. WHEN implementing optimizations THEN the system SHALL maintain identical visual output to the current implementation

### Requirement 4

**User Story:** As a developer, I want to verify that optimizations work correctly, so that I can ensure no regressions are introduced.

#### Acceptance Criteria

1. WHEN testing optimized code THEN the system SHALL produce identical visual output to the original implementation
2. WHEN measuring performance THEN the system SHALL show measurable improvement in the t2-t1 time delta
3. WHEN running existing tests THEN the system SHALL pass all visual correctness tests
4. WHEN profiling the optimized code THEN the system SHALL demonstrate reduced time in the iteration phase
