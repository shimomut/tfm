# Requirements Document

## Introduction

The CoreGraphics backend's drawRect_() method contains a performance bottleneck in the character drawing phase (Phase 2). Profiling shows that the section "Draw characters" (t4-t3) takes approximately 0.03 seconds (30ms), which represents a significant portion of the total rendering time. This feature aims to investigate and optimize this critical rendering path to achieve sub-10ms performance.

## Glossary

- **Character Drawing Phase**: The phase where non-space characters are rendered to the screen using NSAttributedString
- **NSAttributedString**: A Cocoa class that manages styled text with attributes like font, color, and underline
- **Font Cache**: A cache that stores pre-created NSFont objects with different text attributes
- **Color Cache**: A cache that stores pre-created NSColor objects for different RGB values
- **Text Attributes Dictionary**: A dictionary containing NSFont, NSForegroundColor, and optional NSUnderlineStyle
- **Grid**: The 2D array storing all character cells (rows x cols)
- **Dirty Region**: The rectangular area of the screen that needs to be redrawn
- **CoreGraphics**: Apple's 2D graphics rendering framework
- **PyObjC**: Python-Objective-C bridge used to call Cocoa APIs

## Requirements

### Requirement 1

**User Story:** As a TFM user, I want the file manager to render text quickly, so that I can see updates without noticeable lag.

#### Acceptance Criteria

1. WHEN the character drawing phase executes THEN the system SHALL complete in under 0.01 seconds (10ms) for a full-screen update
2. WHEN drawing characters THEN the system SHALL minimize object creation overhead
3. WHEN accessing character data THEN the system SHALL use efficient data access patterns
4. WHEN creating NSAttributedString objects THEN the system SHALL minimize redundant operations
5. WHEN applying text attributes THEN the system SHALL reduce dictionary operations

### Requirement 2

**User Story:** As a developer, I want to understand the character drawing bottleneck, so that I can make informed optimization decisions.

#### Acceptance Criteria

1. WHEN analyzing the current implementation THEN the system SHALL identify which specific operations consume the most time
2. WHEN profiling the code THEN the system SHALL measure time spent in NSAttributedString creation, attribute dictionary building, and drawing separately
3. WHEN comparing alternatives THEN the system SHALL provide quantitative performance measurements
4. WHEN documenting findings THEN the system SHALL explain the root causes of the performance issues

### Requirement 3

**User Story:** As a developer, I want to optimize the character drawing phase, so that rendering performance improves significantly.

#### Acceptance Criteria

1. WHEN optimizing attribute dictionary creation THEN the system SHALL minimize dictionary allocations
2. WHEN optimizing NSAttributedString creation THEN the system SHALL reduce object creation overhead
3. WHEN optimizing character iteration THEN the system SHALL use efficient loop patterns
4. WHEN caching is beneficial THEN the system SHALL implement appropriate caching strategies
5. WHEN implementing optimizations THEN the system SHALL maintain identical visual output to the current implementation

### Requirement 4

**User Story:** As a developer, I want a reproducible test case that demonstrates the performance bottleneck, so that I can measure the impact of optimizations.

#### Acceptance Criteria

1. WHEN running the performance test THEN the system SHALL create a scenario with maximum character drawing workload
2. WHEN the test fills the grid THEN the system SHALL use non-space characters across the entire 24x80 grid
3. WHEN the test applies attributes THEN the system SHALL use various color pairs, bold, underline, and reverse attributes
4. WHEN measuring the baseline THEN the system SHALL demonstrate t4-t3 time of approximately 0.03 seconds (30ms)
5. WHEN the test executes THEN the system SHALL provide clear timing output for the character drawing phase

### Requirement 5

**User Story:** As a developer, I want to verify that optimizations work correctly, so that I can ensure no regressions are introduced.

#### Acceptance Criteria

1. WHEN testing optimized code THEN the system SHALL produce identical visual output to the original implementation
2. WHEN measuring performance THEN the system SHALL show measurable improvement in the t4-t3 time delta
3. WHEN running existing tests THEN the system SHALL pass all visual correctness tests
4. WHEN profiling the optimized code THEN the system SHALL demonstrate reduced time in the character drawing phase
