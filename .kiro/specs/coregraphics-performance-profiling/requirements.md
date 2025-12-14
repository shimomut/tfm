# Requirements Document

## Introduction

This document specifies the requirements for a performance profiling system to investigate and optimize the CoreGraphics backend rendering and key event handling performance in TFM. Users have reported slow rendering and key response times when running with the CoreGraphics endpoint, and this feature will provide the tools needed to identify bottlenecks and measure improvements.

## Glossary

- **TFM**: TUI File Manager - the terminal-based file manager application
- **CoreGraphics Backend**: The macOS-native rendering backend that uses CoreGraphics/Metal for display
- **FPS**: Frames Per Second - a measure of rendering performance
- **Profiling Mode**: An operational mode that collects performance metrics and generates profiling data
- **cProfile**: Python's built-in deterministic profiling module
- **Key Event Handling**: The process of receiving, processing, and responding to keyboard input
- **Rendering Loop**: The main loop that draws the UI to the screen

## Requirements

### Requirement 1

**User Story:** As a developer, I want to enable profiling mode via a command-line flag, so that I can collect performance data without modifying code.

#### Acceptance Criteria

1. WHEN the user launches TFM with the `--profile` flag THEN the system SHALL enter profiling mode
2. WHEN profiling mode is enabled THEN the system SHALL display a message indicating profiling is active
3. WHEN the `--profile` flag is not provided THEN the system SHALL run in normal mode without profiling overhead
4. WHEN profiling mode is active THEN the system SHALL function normally while collecting performance data

### Requirement 2

**User Story:** As a developer, I want to see real-time FPS measurements, so that I can understand rendering performance during actual usage.

#### Acceptance Criteria

1. WHEN profiling mode is enabled THEN the system SHALL measure frames per second continuously
2. WHEN 5 seconds have elapsed THEN the system SHALL print the current FPS to stdout
3. WHEN FPS is printed THEN the output SHALL include a timestamp and the measured FPS value
4. WHEN the application is running THEN FPS measurements SHALL not significantly impact performance
5. WHEN FPS is calculated THEN the system SHALL use the actual frame rendering times from the main loop

### Requirement 3

**User Story:** As a developer, I want detailed profiling data for key event handling, so that I can identify bottlenecks in input processing.

#### Acceptance Criteria

1. WHEN a key event is processed in profiling mode THEN the system SHALL profile the event handling code path
2. WHEN profiling key event handling THEN the system SHALL use cProfile to collect function call statistics
3. WHEN key event profiling completes THEN the system SHALL write profiling data to a file
4. WHEN the profiling file is created THEN the filename SHALL include a timestamp for uniqueness
5. WHEN the profiling file is created THEN it SHALL be placed in a designated profiling output directory

### Requirement 4

**User Story:** As a developer, I want detailed profiling data for rendering operations, so that I can identify bottlenecks in the drawing code.

#### Acceptance Criteria

1. WHEN a frame is rendered in profiling mode THEN the system SHALL profile the rendering code path
2. WHEN profiling rendering THEN the system SHALL use cProfile to collect function call statistics
3. WHEN rendering profiling completes THEN the system SHALL write profiling data to a file
4. WHEN the profiling file is created THEN the filename SHALL include a timestamp for uniqueness
5. WHEN the profiling file is created THEN it SHALL be placed in a designated profiling output directory

### Requirement 5

**User Story:** As a developer, I want profiling to focus on the FileManager.run() main loop, so that I can analyze the most performance-critical code paths.

#### Acceptance Criteria

1. WHEN profiling is enabled THEN the system SHALL profile the latter half of FileManager.run() method
2. WHEN profiling the main loop THEN the system SHALL capture both key event handling and rendering operations
3. WHEN profiling data is collected THEN it SHALL include function call counts, cumulative time, and per-call time
4. WHEN profiling is active THEN the system SHALL maintain separate profiles for key handling and rendering

### Requirement 6

**User Story:** As a developer, I want profiling output files organized and easily accessible, so that I can analyze performance data efficiently.

#### Acceptance Criteria

1. WHEN profiling mode is enabled THEN the system SHALL create a profiling output directory if it does not exist
2. WHEN profiling files are written THEN they SHALL use descriptive names indicating the operation type
3. WHEN multiple profiling sessions occur THEN each SHALL generate uniquely named files
4. WHEN profiling completes THEN the system SHALL print the location of generated profiling files
5. WHEN the profiling directory is created THEN it SHALL be named "profiling_output" or similar

### Requirement 7

**User Story:** As a developer, I want minimal performance impact from profiling infrastructure, so that measurements reflect actual performance characteristics.

#### Acceptance Criteria

1. WHEN profiling mode is disabled THEN the system SHALL have zero profiling overhead
2. WHEN FPS measurement is active THEN it SHALL use lightweight timing mechanisms
3. WHEN profiling data is written THEN file I/O SHALL not block the main rendering loop
4. WHEN profiling is enabled THEN the system SHALL only profile targeted code sections
5. WHEN profiling overhead is measured THEN it SHALL be less than 10% of total execution time
