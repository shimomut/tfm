# Requirements Document

## Introduction

This document specifies the requirements for implementing a macOS CoreGraphics (Quartz 2D) rendering backend for TTK (Terminal Toolkit). TTK currently supports terminal-based rendering through a curses backend. The goal is to add a CoreGraphics backend that enables TTK applications to run as native macOS desktop applications with high-quality text rendering, while maintaining the same abstract rendering API. CoreGraphics was chosen over Metal because it provides native macOS text rendering quality, requires significantly less code (~300 lines vs ~1000+ lines), and is proven by applications like Terminal.app and iTerm2.

## Glossary

- **TTK**: Terminal Toolkit - A generic, reusable library providing an abstract rendering API for text-based applications
- **CoreGraphics**: Apple's Quartz 2D drawing API for macOS, providing high-quality 2D rendering capabilities
- **Quartz 2D**: Another name for CoreGraphics, Apple's 2D graphics rendering engine
- **Rendering Backend**: An implementation of TTK's abstract Renderer interface for a specific platform
- **CoreGraphics Backend**: A rendering backend implementation using Apple's CoreGraphics/Quartz 2D API
- **Curses Backend**: The existing terminal-based rendering backend using Python's curses library
- **Character Grid**: A coordinate system where positions are specified in character rows and columns
- **Monospace Font**: A fixed-width font where all characters have identical width, required for character grid alignment
- **NSView**: A Cocoa class representing a view that can draw content in a window
- **NSWindow**: A Cocoa class representing a window on macOS
- **NSAttributedString**: A Cocoa class for styled text with attributes like font, color, and underline
- **CGContext**: A CoreGraphics drawing context that receives drawing commands
- **Color Pair**: A combination of foreground and background RGB colors used for text rendering
- **Text Attribute**: Visual styling applied to text such as bold, underline, or reverse video
- **PyObjC**: Python bridge to Objective-C frameworks, enabling access to Cocoa and CoreGraphics APIs

## Requirements

### Requirement 1

**User Story:** As a developer, I want to implement a CoreGraphics rendering backend, so that TTK applications can run as native macOS desktop applications with high-quality text rendering.

#### Acceptance Criteria

1. WHEN the CoreGraphics backend is initialized THEN the system SHALL create a native macOS window using NSWindow
2. WHEN the CoreGraphics backend renders text THEN the system SHALL use NSAttributedString for native macOS text rendering quality
3. WHEN the CoreGraphics backend draws characters THEN the system SHALL render them on a character grid with monospace font
4. WHEN the CoreGraphics backend is used THEN the system SHALL implement all methods defined in the abstract Renderer interface
5. WHEN the CoreGraphics backend is initialized THEN the system SHALL require PyObjC framework for Cocoa and CoreGraphics access

### Requirement 2

**User Story:** As a developer, I want the CoreGraphics backend to maintain a character grid, so that text positioning works identically to the curses backend.

#### Acceptance Criteria

1. WHEN the character grid is initialized THEN the system SHALL create a 2D array storing character, color pair, and attributes for each cell
2. WHEN text is drawn THEN the system SHALL update the character grid at the specified row and column positions
3. WHEN the display is refreshed THEN the system SHALL render all characters from the grid to the screen
4. WHEN the window is resized THEN the system SHALL recalculate grid dimensions based on character size
5. WHEN coordinates are out of bounds THEN the system SHALL ignore the operation without crashing

### Requirement 3

**User Story:** As a developer, I want the CoreGraphics backend to support monospace fonts, so that character alignment is guaranteed and grid positioning is accurate.

#### Acceptance Criteria

1. WHEN a font is specified THEN the system SHALL only accept monospace font families
2. WHEN the backend initializes THEN the system SHALL calculate fixed character width and height from the font
3. WHEN characters are positioned THEN the system SHALL use the fixed character dimensions for all grid calculations
4. WHEN a proportional font is requested THEN the system SHALL reject it with a clear error message
5. WHEN the default font is used THEN the system SHALL use "Menlo" at 14 points as the default monospace font

### Requirement 4

**User Story:** As a developer, I want the CoreGraphics backend to support color pairs, so that text can be rendered with foreground and background colors matching the curses backend.

#### Acceptance Criteria

1. WHEN color pairs are initialized THEN the system SHALL store RGB values for foreground and background colors
2. WHEN color pairs are used THEN the system SHALL support at least 256 color pairs to match curses capabilities
3. WHEN text is rendered THEN the system SHALL draw the background color as a filled rectangle before drawing the character
4. WHEN text is rendered THEN the system SHALL apply the foreground color to the character using NSForegroundColorAttributeName
5. WHEN color pair 0 is used THEN the system SHALL default to white text on black background

### Requirement 5

**User Story:** As a developer, I want the CoreGraphics backend to support text attributes, so that bold, underline, and reverse video styling work identically to the curses backend.

#### Acceptance Criteria

1. WHEN bold attribute is applied THEN the system SHALL use NSFontManager to convert the font to its bold variant
2. WHEN underline attribute is applied THEN the system SHALL use NSUnderlineStyleAttributeName with NSUnderlineStyleSingle
3. WHEN reverse video attribute is applied THEN the system SHALL swap foreground and background colors before rendering
4. WHEN multiple attributes are combined THEN the system SHALL apply all attributes simultaneously to the same character
5. WHEN attributes are rendered THEN the system SHALL produce visually equivalent output to the curses backend

### Requirement 6

**User Story:** As a developer, I want the CoreGraphics backend to handle keyboard input, so that applications can respond to user key presses.

#### Acceptance Criteria

1. WHEN keyboard events occur THEN the system SHALL translate NSEvent key codes to TTK KeyEvent objects
2. WHEN modifier keys are pressed THEN the system SHALL detect and report Shift, Control, Alt, and Command states
3. WHEN special keys are pressed THEN the system SHALL provide consistent codes for arrow keys, function keys, Enter, Escape, Backspace, and Delete
4. WHEN input is requested with timeout THEN the system SHALL support blocking, non-blocking, and timed input modes
5. WHEN the view receives keyboard focus THEN the system SHALL implement acceptsFirstResponder to return True

### Requirement 7

**User Story:** As a developer, I want the CoreGraphics backend to handle window management, so that applications can control window size, title, and lifecycle.

#### Acceptance Criteria

1. WHEN the window is created THEN the system SHALL set the window title from the initialization parameter
2. WHEN the window is created THEN the system SHALL support standard macOS window controls including close, minimize, and resize
3. WHEN window dimensions are queried THEN the system SHALL return the current grid size in rows and columns
4. WHEN the window is resized THEN the system SHALL recalculate grid dimensions and trigger a redraw
5. WHEN the backend shuts down THEN the system SHALL close the window and release all resources

### Requirement 8

**User Story:** As a developer, I want the CoreGraphics backend to use a custom NSView for rendering, so that drawing operations are properly integrated with the Cocoa event loop.

#### Acceptance Criteria

1. WHEN the custom view is created THEN the system SHALL subclass NSView and store a reference to the backend
2. WHEN the view needs to draw THEN the system SHALL implement drawRect_ to render the character grid
3. WHEN drawing occurs THEN the system SHALL iterate through the character grid and render each non-empty cell
4. WHEN the display needs updating THEN the system SHALL call setNeedsDisplay_ to trigger a redraw
5. WHEN the view is initialized THEN the system SHALL use initWithFrame_backend_ to pass the backend reference

### Requirement 9

**User Story:** As a developer, I want the CoreGraphics backend to handle coordinate system differences, so that the character grid origin matches the curses backend convention.

#### Acceptance Criteria

1. WHEN positioning characters THEN the system SHALL place row 0 at the top of the window
2. WHEN positioning characters THEN the system SHALL place column 0 at the left of the window
3. WHEN calculating pixel positions THEN the system SHALL invert the y-axis to match CoreGraphics bottom-left origin
4. WHEN drawing at row R and column C THEN the system SHALL calculate y position as (rows - R - 1) * char_height
5. WHEN drawing at row R and column C THEN the system SHALL calculate x position as C * char_width

### Requirement 10

**User Story:** As a developer, I want the CoreGraphics backend to optimize rendering performance, so that only changed cells are redrawn when possible.

#### Acceptance Criteria

1. WHEN the grid is cleared THEN the system SHALL reset all cells to space character with default color pair
2. WHEN text is drawn THEN the system SHALL only update the affected cells in the character grid
3. WHEN the display is refreshed THEN the system SHALL mark the entire view as needing display
4. WHEN drawing empty cells THEN the system SHALL skip rendering space characters with default colors to improve performance
5. WHEN rendering the grid THEN the system SHALL complete a full 80x24 grid redraw in under 10 milliseconds

### Requirement 11

**User Story:** As a developer, I want to verify the CoreGraphics backend works correctly, so that I can ensure it produces equivalent output to the curses backend before integration.

#### Acceptance Criteria

1. WHEN running demo applications THEN the system SHALL support command-line selection between curses and CoreGraphics backends
2. WHEN running with CoreGraphics backend THEN the system SHALL display the same visual output as the curses backend
3. WHEN testing text rendering THEN the system SHALL correctly display all printable ASCII characters
4. WHEN testing colors THEN the system SHALL correctly display all initialized color pairs
5. WHEN testing attributes THEN the system SHALL correctly display bold, underline, and reverse video text

### Requirement 12

**User Story:** As a developer, I want the CoreGraphics backend to handle errors gracefully, so that missing dependencies or invalid configurations provide clear error messages.

#### Acceptance Criteria

1. WHEN PyObjC is not installed THEN the system SHALL raise RuntimeError with installation instructions
2. WHEN an invalid font name is specified THEN the system SHALL raise ValueError with the font name
3. WHEN color pair IDs are out of range THEN the system SHALL raise ValueError with valid range information
4. WHEN drawing operations fail THEN the system SHALL log warnings but continue execution without crashing
5. WHEN the window cannot be created THEN the system SHALL raise RuntimeError with diagnostic information

### Requirement 13

**User Story:** As a developer, I want the CoreGraphics backend to integrate with the Cocoa event loop, so that the application remains responsive and handles events properly.

#### Acceptance Criteria

1. WHEN processing events THEN the system SHALL use NSApp.nextEventMatchingMask_untilDate_inMode_dequeue_ to retrieve events
2. WHEN events are retrieved THEN the system SHALL dispatch them using NSApp.sendEvent_ for proper handling
3. WHEN waiting for input THEN the system SHALL support NSDate.distantFuture for blocking indefinitely
4. WHEN waiting for input with timeout THEN the system SHALL use NSDate.dateWithTimeIntervalSinceNow_ for timed waits
5. WHEN no events are available THEN the system SHALL return None from get_input without blocking if timeout is 0

### Requirement 14

**User Story:** As a developer, I want the CoreGraphics backend implementation to be simple and maintainable, so that it can be easily understood, debugged, and extended.

#### Acceptance Criteria

1. WHEN the backend is implemented THEN the system SHALL require approximately 300 lines of code total
2. WHEN the code is reviewed THEN the system SHALL have no shader code, texture atlases, or GPU state management
3. WHEN the code is reviewed THEN the system SHALL use direct NSAttributedString rendering without intermediate buffers
4. WHEN the implementation is compared to Metal THEN the system SHALL be at least 3 times simpler in lines of code
5. WHEN the code is documented THEN the system SHALL include clear docstrings explaining the CoreGraphics approach

### Requirement 15

**User Story:** As a developer, I want the CoreGraphics backend to support Unicode and emoji, so that applications can display international text and symbols.

#### Acceptance Criteria

1. WHEN Unicode characters are rendered THEN the system SHALL use NSAttributedString's automatic Unicode support
2. WHEN emoji are rendered THEN the system SHALL display them using the system's native emoji rendering
3. WHEN complex scripts are rendered THEN the system SHALL rely on CoreText's automatic handling of Arabic, Thai, etc.
4. WHEN characters are missing from the font THEN the system SHALL use macOS's automatic font fallback mechanism
5. WHEN rendering Unicode THEN the system SHALL require no manual glyph positioning or special handling

### Requirement 16

**User Story:** As a developer, I want to run existing TTK demo applications with the CoreGraphics backend, so that I can verify compatibility without modifying application code.

#### Acceptance Criteria

1. WHEN demo applications are run THEN the system SHALL work with the existing demo code without modifications
2. WHEN switching backends THEN the system SHALL only require changing the backend instantiation line
3. WHEN running demos THEN the system SHALL produce visually equivalent output between curses and CoreGraphics
4. WHEN testing keyboard input THEN the system SHALL respond to the same key codes as the curses backend
5. WHEN testing all demos THEN the system SHALL verify that no demo-specific code changes are needed

### Requirement 17

**User Story:** As a developer, I want the CoreGraphics backend to follow TTK's architecture, so that it integrates seamlessly with the existing abstract rendering API.

#### Acceptance Criteria

1. WHEN the backend is implemented THEN the system SHALL inherit from the abstract Renderer base class
2. WHEN methods are implemented THEN the system SHALL match the exact signatures defined in the Renderer interface
3. WHEN the backend is used THEN the system SHALL work with any application written against the Renderer interface
4. WHEN exceptions occur THEN the system SHALL use the same exception types as other backends for consistency
5. WHEN the backend is initialized THEN the system SHALL accept the same initialization parameters as documented in the API

### Requirement 18

**User Story:** As a developer, I want comprehensive tests for the CoreGraphics backend, so that I can verify correctness and prevent regressions.

#### Acceptance Criteria

1. WHEN tests are run THEN the system SHALL verify window creation and initialization
2. WHEN tests are run THEN the system SHALL verify character grid management and updates
3. WHEN tests are run THEN the system SHALL verify color pair initialization and usage
4. WHEN tests are run THEN the system SHALL verify text attribute rendering (bold, underline, reverse)
5. WHEN tests are run THEN the system SHALL verify keyboard input translation and event handling
