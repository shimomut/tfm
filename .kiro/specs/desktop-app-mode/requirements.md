# Requirements Document

## Introduction

This document specifies the requirements for adding desktop application mode support to TFM (TUI File Manager). Currently, TFM runs exclusively as a terminal-based application using Python's curses library. The goal is to create an abstract rendering API that allows TFM to support multiple rendering backends, starting with the existing curses backend for terminals and a new Metal backend for native macOS desktop applications. This architectural change will enable TFM to run both as a terminal application and as a native desktop application without duplicating core logic.

## Glossary

- **Rendering Backend**: An implementation of the abstract rendering API that handles drawing operations for a specific platform or environment (e.g., curses for terminals, Metal for macOS)
- **Abstract Rendering API**: A platform-agnostic interface defining all drawing, input, and window management operations needed by text-based applications
- **Curses Backend**: A rendering backend implementation using Python's curses library for terminal-based display
- **Metal Backend**: A rendering backend implementation using Apple's Metal framework for native macOS desktop applications
- **Renderer**: An instance of a rendering backend that applications use to perform all display operations
- **Drawing Primitive**: A basic rendering operation such as drawing text, rectangles, or handling colors
- **Input Event**: User input such as keyboard presses, mouse clicks, or window resize events
- **Color Pair**: A combination of foreground and background colors used for text rendering
- **Window Context**: The rendering surface provided by a backend (terminal window for curses, native window for Metal)
- **Backend-agnostic Code**: Application code that works with any rendering backend without checking which backend is active
- **Monospace Font**: A fixed-pitch font where all characters have the same width, required for character-grid-based rendering
- **Character Grid**: A coordinate system where positions are specified in character rows and columns rather than pixels

## Requirements

### Requirement 1

**User Story:** As a developer, I want to define an abstract rendering API, so that TFM can support multiple rendering backends without modifying core application logic.

#### Acceptance Criteria

1. WHEN the abstract rendering API is defined THEN the system SHALL provide interfaces for all drawing operations including text rendering, rectangle drawing, line drawing, and color management
2. WHEN the abstract rendering API is defined THEN the system SHALL provide interfaces for input handling including keyboard events, mouse events, and special key detection
3. WHEN the abstract rendering API is defined THEN the system SHALL provide interfaces for window management including dimensions, clearing, refreshing, and coordinate systems
4. WHEN the abstract rendering API is defined THEN the system SHALL use abstract base classes with clearly documented method signatures and return types
5. WHEN a rendering backend is implemented THEN the system SHALL enforce implementation of all required abstract methods through Python's ABC mechanism

### Requirement 2

**User Story:** As a developer, I want to implement a curses rendering backend, so that TFM maintains its existing terminal-based functionality through the new abstract API.

#### Acceptance Criteria

1. WHEN the curses backend is implemented THEN the system SHALL provide all drawing operations using curses library functions
2. WHEN the curses backend handles text rendering THEN the system SHALL support all existing curses attributes including colors, bold, underline, and reverse video
3. WHEN the curses backend handles input THEN the system SHALL translate curses key codes to the abstract API's key representation
4. WHEN the curses backend manages windows THEN the system SHALL handle terminal resizing and coordinate transformations correctly
5. WHEN the curses backend is used THEN the system SHALL maintain backward compatibility with all existing TFM terminal functionality

### Requirement 3

**User Story:** As a developer, I want to implement a Metal rendering backend, so that TFM can run as a native macOS desktop application with GPU-accelerated rendering.

#### Acceptance Criteria

1. WHEN the Metal backend is implemented THEN the system SHALL create a native macOS window using Metal framework
2. WHEN the Metal backend renders text THEN the system SHALL use GPU-accelerated text rendering with support for monospace fonts
3. WHEN the Metal backend handles colors THEN the system SHALL support the same color pairs and attributes as the curses backend
4. WHEN the Metal backend handles input THEN the system SHALL translate macOS keyboard events to the abstract API's key representation
5. WHEN the Metal backend manages the window THEN the system SHALL handle window resizing, focus events, and coordinate transformations correctly
6. WHEN the Metal backend renders THEN the system SHALL achieve smooth 60 FPS rendering performance for typical TFM operations

### Requirement 4

**User Story:** As a developer, I want the abstract rendering API to support all TFM drawing operations, so that no functionality is lost when switching between backends.

#### Acceptance Criteria

1. WHEN drawing text THEN the system SHALL support positioning at any row and column with specified color attributes
2. WHEN drawing rectangles THEN the system SHALL support filled and outlined rectangles with specified colors
3. WHEN drawing lines THEN the system SHALL support horizontal and vertical lines with specified characters and colors
4. WHEN handling colors THEN the system SHALL support initialization of color pairs with foreground and background colors
5. WHEN clearing regions THEN the system SHALL support clearing the entire window or specific rectangular regions
6. WHEN refreshing display THEN the system SHALL support both full window refresh and partial region updates

### Requirement 5

**User Story:** As a developer, I want the abstract rendering API to handle input consistently, so that keyboard and mouse interactions work identically across all backends.

#### Acceptance Criteria

1. WHEN processing keyboard input THEN the system SHALL provide a unified key code representation for all printable characters
2. WHEN processing special keys THEN the system SHALL provide consistent codes for arrow keys, function keys, Enter, Escape, Backspace, and Delete
3. WHEN processing modifier keys THEN the system SHALL detect and report Shift, Control, Alt, and Command key states
4. WHEN handling mouse input THEN the system SHALL provide mouse position and button state information
5. WHEN input is unavailable THEN the system SHALL support non-blocking input checks with timeout support

### Requirement 6

**User Story:** As a developer, I want to create a demo application, so that I can verify both rendering backends work correctly before integrating them into TFM.

#### Acceptance Criteria

1. WHEN the demo application runs THEN the system SHALL allow selection between curses and Metal backends via command-line argument
2. WHEN the demo application runs THEN the system SHALL display a test interface showing text rendering, colors, rectangles, and lines
3. WHEN the demo application runs THEN the system SHALL respond to keyboard input and display the pressed keys
4. WHEN the demo application runs THEN the system SHALL demonstrate window resizing and coordinate handling
5. WHEN the demo application runs THEN the system SHALL verify that both backends produce visually equivalent output
6. WHEN the demo application runs THEN the system SHALL include performance metrics showing frame rate and rendering time

### Requirement 7

**User Story:** As a developer, I want the rendering API to support TFM's color scheme system, so that all existing color schemes work with both backends.

#### Acceptance Criteria

1. WHEN initializing colors THEN the system SHALL support defining color pairs with RGB values or terminal color codes
2. WHEN using color pairs THEN the system SHALL support at least 256 color pairs to match curses capabilities
3. WHEN rendering with colors THEN the system SHALL support combining colors with text attributes like bold and underline
4. WHEN the Metal backend renders colors THEN the system SHALL accurately reproduce the same colors as the curses backend
5. WHEN color schemes are applied THEN the system SHALL work identically across both backends

### Requirement 8

**User Story:** As a developer, I want the rendering API to handle coordinate systems consistently, so that positioning logic works the same way across backends.

#### Acceptance Criteria

1. WHEN positioning elements THEN the system SHALL use a character-based coordinate system with row and column indices
2. WHEN the coordinate origin is defined THEN the system SHALL place (0, 0) at the top-left corner
3. WHEN querying window dimensions THEN the system SHALL return dimensions in character rows and columns
4. WHEN the window is resized THEN the system SHALL provide updated dimensions through a resize event
5. WHEN coordinates exceed window bounds THEN the system SHALL handle out-of-bounds drawing gracefully without crashing

### Requirement 9

**User Story:** As a developer, I want the rendering API to support text attributes, so that TFM's visual styling works across all backends.

#### Acceptance Criteria

1. WHEN rendering text THEN the system SHALL support bold attribute for emphasized text
2. WHEN rendering text THEN the system SHALL support underline attribute for highlighted text
3. WHEN rendering text THEN the system SHALL support reverse video attribute for inverted colors
4. WHEN rendering text THEN the system SHALL support combining multiple attributes simultaneously
5. WHEN the Metal backend renders attributes THEN the system SHALL produce visually equivalent output to the curses backend

### Requirement 10

**User Story:** As a developer, I want the rendering API to be well-documented, so that implementing new backends is straightforward and all required behaviors are clear.

#### Acceptance Criteria

1. WHEN abstract methods are defined THEN the system SHALL include comprehensive docstrings explaining purpose, parameters, return values, and expected behavior
2. WHEN coordinate systems are used THEN the system SHALL document the origin, axis directions, and unit of measurement
3. WHEN color systems are used THEN the system SHALL document color representation, initialization, and usage patterns
4. WHEN input handling is implemented THEN the system SHALL document key code mappings and event structures
5. WHEN implementing a new backend THEN the system SHALL provide example code and implementation guidelines

### Requirement 11

**User Story:** As a user, I want to run TFM as a desktop application on macOS, so that I can use TFM without opening a terminal.

#### Acceptance Criteria

1. WHEN launching TFM with the Metal backend THEN the system SHALL open a native macOS window
2. WHEN using TFM as a desktop app THEN the system SHALL provide all the same functionality as the terminal version
3. WHEN using TFM as a desktop app THEN the system SHALL support standard macOS window operations including minimize, maximize, and close
4. WHEN using TFM as a desktop app THEN the system SHALL integrate with macOS keyboard shortcuts and conventions
5. WHEN using TFM as a desktop app THEN the system SHALL maintain responsive performance with smooth rendering

### Requirement 12

**User Story:** As a developer, I want the rendering backends to be isolated from TFM core logic, so that backend implementation details don't leak into application code.

#### Acceptance Criteria

1. WHEN TFM application code performs rendering THEN the system SHALL only use abstract rendering API methods
2. WHEN TFM application code is examined THEN the system SHALL contain zero backend-specific conditionals or imports
3. WHEN a new backend is added THEN the system SHALL require zero modifications to TFM application code
4. WHEN backend-specific initialization is needed THEN the system SHALL encapsulate it within the backend implementation
5. WHEN backend-specific resources are used THEN the system SHALL manage them entirely within the backend class

### Requirement 13

**User Story:** As a developer, I want to parse and pretty-print rendering commands, so that I can test the rendering API independently of any backend implementation.

#### Acceptance Criteria

1. WHEN rendering commands are issued THEN the system SHALL support serializing them to a text format
2. WHEN rendering commands are serialized THEN the system SHALL include all parameters needed to reproduce the command
3. WHEN serialized commands are parsed THEN the system SHALL reconstruct the original rendering operations
4. WHEN pretty-printing commands THEN the system SHALL format them in a human-readable way for debugging
5. WHEN testing the rendering API THEN the system SHALL allow recording and replaying command sequences

### Requirement 14

**User Story:** As a developer, I want the Metal backend to handle text rendering efficiently, so that TFM remains responsive even with large file listings.

#### Acceptance Criteria

1. WHEN rendering large amounts of text THEN the system SHALL use GPU-accelerated text rendering
2. WHEN text content changes THEN the system SHALL only re-render changed regions
3. WHEN scrolling through content THEN the system SHALL maintain 60 FPS frame rate
4. WHEN rendering monospace text THEN the system SHALL ensure perfect character alignment
5. WHEN measuring text THEN the system SHALL provide accurate character width and height metrics

### Requirement 15

**User Story:** As a developer, I want the demo application to serve as a test suite, so that I can verify rendering backend correctness before TFM integration.

#### Acceptance Criteria

1. WHEN running the demo THEN the system SHALL test all drawing primitives including text, rectangles, and lines
2. WHEN running the demo THEN the system SHALL test all color pairs and text attributes
3. WHEN running the demo THEN the system SHALL test input handling for keyboard and special keys
4. WHEN running the demo THEN the system SHALL test window resizing and coordinate transformations
5. WHEN running the demo THEN the system SHALL provide visual confirmation that both backends produce equivalent output
6. WHEN running the demo THEN the system SHALL report any discrepancies between backend behaviors

### Requirement 16

**User Story:** As a developer of other applications, I want the rendering library to be reusable and generic, so that I can use it for any text-based application without TFM-specific dependencies.

#### Acceptance Criteria

1. WHEN the library is named THEN the system SHALL use a generic name that does not reference TFM
2. WHEN API methods are named THEN the system SHALL use generic terminology applicable to any text-based application
3. WHEN the library is packaged THEN the system SHALL be distributable as a standalone Python package
4. WHEN the library is documented THEN the system SHALL include examples that are not TFM-specific
5. WHEN the library is used THEN the system SHALL have zero dependencies on TFM code or TFM-specific concepts

### Requirement 17

**User Story:** As a developer, I want the rendering library to support only monospace fonts, so that character grid alignment is guaranteed and implementation is simplified.

#### Acceptance Criteria

1. WHEN text is rendered THEN the system SHALL assume all characters have identical width
2. WHEN the Metal backend initializes fonts THEN the system SHALL only accept monospace font families
3. WHEN calculating text positions THEN the system SHALL use fixed character width and height values
4. WHEN documenting the library THEN the system SHALL explicitly state the monospace font requirement
5. WHEN proportional fonts are requested THEN the system SHALL reject them with a clear error message

### Requirement 18

**User Story:** As a developer planning future enhancements, I want the rendering API to be designed with image support in mind, so that adding image rendering later does not require breaking API changes.

#### Acceptance Criteria

1. WHEN the abstract rendering API is designed THEN the system SHALL reserve method names and patterns for future image rendering operations
2. WHEN coordinate systems are defined THEN the system SHALL support both character-based and pixel-based positioning for future compatibility
3. WHEN the API is documented THEN the system SHALL note that image rendering is planned for future versions
4. WHEN backend implementations are created THEN the system SHALL structure code to allow adding image rendering without major refactoring
5. WHEN the API version is specified THEN the system SHALL use semantic versioning to indicate when image support is added
