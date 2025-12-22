# Requirements Document

## Introduction

This document specifies the requirements for rewriting the rendering portion of the CoreGraphics backend in C++ while maintaining the existing PyObjC implementation as a switchable alternative. The goal is to provide direct CoreGraphics/CoreText API access for improved performance while preserving backward compatibility and allowing easy switching between implementations.

## Glossary

- **CoreGraphics**: Apple's 2D graphics rendering framework (also known as Quartz 2D)
- **CoreText**: Apple's text layout and rendering framework
- **PyObjC**: Python-Objective-C bridge that allows Python code to call macOS APIs
- **TTK**: Terminal Toolkit - the application framework using this backend
- **Renderer**: Abstract interface that backends must implement
- **Character_Grid**: 2D array storing (char, color_pair, attributes) tuples
- **Color_Pair**: Mapping of pair ID to (foreground_rgb, background_rgb) tuples
- **Dirty_Region**: Rectangular area of the screen that needs to be redrawn
- **Batch**: Group of adjacent cells with the same background color drawn in a single API call
- **CTLine**: CoreText object representing a line of text with attributes
- **CGContext**: CoreGraphics drawing context
- **NSAttributedString**: Cocoa object representing styled text
- **C++_Extension**: Python extension module written in C++ that can be imported from Python
- **Backend_Selector**: Configuration mechanism to choose between PyObjC and C++ rendering

## Requirements

### Requirement 1: C++ Rendering Module

**User Story:** As a developer, I want a C++ extension module that handles rendering, so that I can achieve better performance through direct CoreGraphics/CoreText API access.

#### Acceptance Criteria

1. THE C++_Extension SHALL provide a Python-importable module for rendering operations
2. THE C++_Extension SHALL expose a render function that accepts grid data and rendering parameters
3. THE C++_Extension SHALL use CoreGraphics and CoreText APIs directly without PyObjC overhead
4. THE C++_Extension SHALL handle coordinate system transformation from TTK (top-left origin) to CoreGraphics (bottom-left origin)
5. THE C++_Extension SHALL support all text attributes (BOLD, UNDERLINE, REVERSE)

### Requirement 2: Background Rendering

**User Story:** As a developer, I want efficient background rendering, so that the application can quickly fill cell backgrounds.

#### Acceptance Criteria

1. WHEN rendering backgrounds, THE C++_Extension SHALL batch adjacent cells with the same background color
2. WHEN drawing batched backgrounds, THE C++_Extension SHALL use CGContextFillRect for each batch
3. THE C++_Extension SHALL handle edge cell extension to fill window padding areas
4. THE C++_Extension SHALL support dirty region optimization to redraw only changed areas
5. THE C++_Extension SHALL calculate dirty cells from NSRect parameters

### Requirement 3: Character Rendering

**User Story:** As a developer, I want efficient character rendering, so that text displays quickly with proper attributes.

#### Acceptance Criteria

1. WHEN rendering characters, THE C++_Extension SHALL batch consecutive characters with the same attributes
2. WHEN drawing batched characters, THE C++_Extension SHALL use CTLineDraw for each batch
3. THE C++_Extension SHALL skip space characters (backgrounds already rendered)
4. THE C++_Extension SHALL handle wide characters (zenkaku) that occupy 2 grid cells
5. THE C++_Extension SHALL apply text attributes (BOLD, UNDERLINE, REVERSE) correctly

### Requirement 4: Font and Color Management

**User Story:** As a developer, I want efficient font and color management, so that rendering minimizes object creation overhead.

#### Acceptance Criteria

1. THE C++_Extension SHALL cache CTFont objects for different attribute combinations
2. THE C++_Extension SHALL cache CGColor objects for different RGB values
3. THE C++_Extension SHALL cache CFDictionary objects for text attributes
4. THE C++_Extension SHALL implement LRU eviction when caches reach maximum size
5. THE C++_Extension SHALL provide cache clearing functionality

### Requirement 5: Cursor Rendering

**User Story:** As a developer, I want cursor rendering support, so that users can see the current input position.

#### Acceptance Criteria

1. WHEN cursor is visible, THE C++_Extension SHALL draw a filled rectangle at cursor position
2. THE C++_Extension SHALL use semi-transparent white color for cursor visibility
3. THE C++_Extension SHALL accept cursor position (row, col) as parameters
4. THE C++_Extension SHALL handle cursor visibility flag
5. THE C++_Extension SHALL draw cursor after all other rendering is complete

### Requirement 6: IME Marked Text Rendering

**User Story:** As a developer, I want IME composition text rendering, so that users can see text being composed in Japanese/Chinese input methods.

#### Acceptance Criteria

1. WHEN marked text exists, THE C++_Extension SHALL render it at cursor position
2. THE C++_Extension SHALL use underline style for marked text
3. THE C++_Extension SHALL accept marked text string and attributes as parameters
4. THE C++_Extension SHALL handle empty marked text (no rendering)
5. THE C++_Extension SHALL draw marked text after cursor rendering

### Requirement 7: Backend Switching

**User Story:** As a developer, I want to switch between PyObjC and C++ rendering implementations, so that I can compare performance and debug issues.

#### Acceptance Criteria

1. THE Backend_Selector SHALL allow switching between PyObjC and C++ rendering with a single line of code
2. THE Backend_Selector SHALL default to PyObjC rendering for backward compatibility
3. THE Backend_Selector SHALL provide a configuration flag or environment variable for selection
4. WHEN C++_Extension is not available, THE Backend_Selector SHALL fall back to PyObjC rendering
5. THE Backend_Selector SHALL log which rendering implementation is being used

### Requirement 8: API Compatibility

**User Story:** As a developer, I want the C++ rendering to be API-compatible with PyObjC rendering, so that existing code continues to work without modification.

#### Acceptance Criteria

1. THE C++_Extension SHALL accept the same parameters as the PyObjC drawRect_ method
2. THE C++_Extension SHALL produce visually identical output to PyObjC rendering
3. THE C++_Extension SHALL handle all edge cases that PyObjC rendering handles
4. THE C++_Extension SHALL raise appropriate exceptions for invalid parameters
5. THE C++_Extension SHALL maintain the same coordinate system conventions

### Requirement 9: Build System Integration

**User Story:** As a developer, I want the C++ extension to build automatically, so that I can easily install and use it.

#### Acceptance Criteria

1. THE Build_System SHALL compile the C++ extension using setup.py or CMake
2. THE Build_System SHALL link against CoreGraphics and CoreText frameworks
3. THE Build_System SHALL support macOS 10.13+ (High Sierra and later)
4. THE Build_System SHALL produce a .so file that Python can import
5. WHEN build fails, THE Build_System SHALL provide clear error messages

### Requirement 10: Performance Metrics

**User Story:** As a developer, I want performance metrics, so that I can measure the improvement from C++ rendering.

#### Acceptance Criteria

1. THE C++_Extension SHALL track rendering time for each frame
2. THE C++_Extension SHALL track cache hit/miss rates
3. THE C++_Extension SHALL track number of batches drawn
4. THE C++_Extension SHALL provide a method to retrieve performance metrics
5. THE C++_Extension SHALL allow resetting metrics counters

### Requirement 11: Error Handling

**User Story:** As a developer, I want robust error handling, so that rendering failures don't crash the application.

#### Acceptance Criteria

1. WHEN CoreGraphics API calls fail, THE C++_Extension SHALL log error messages
2. WHEN invalid parameters are provided, THE C++_Extension SHALL raise Python exceptions
3. WHEN memory allocation fails, THE C++_Extension SHALL handle gracefully
4. WHEN font loading fails, THE C++_Extension SHALL fall back to system font
5. THE C++_Extension SHALL validate all input parameters before use

### Requirement 12: Memory Management

**User Story:** As a developer, I want proper memory management, so that the application doesn't leak memory.

#### Acceptance Criteria

1. THE C++_Extension SHALL release all CoreFoundation objects using CFRelease
2. THE C++_Extension SHALL use RAII patterns for automatic resource cleanup
3. THE C++_Extension SHALL avoid memory leaks in cache implementations
4. THE C++_Extension SHALL handle Python reference counting correctly
5. THE C++_Extension SHALL provide cleanup methods for releasing resources

### Requirement 13: Testing Support

**User Story:** As a developer, I want comprehensive testing support, so that I can verify correctness of the C++ implementation.

#### Acceptance Criteria

1. THE C++_Extension SHALL provide a test mode that captures rendering output
2. THE C++_Extension SHALL allow comparing C++ output with PyObjC output
3. THE C++_Extension SHALL support rendering to offscreen buffers for testing
4. THE C++_Extension SHALL provide methods to query internal state for testing
5. THE C++_Extension SHALL include unit tests for all major functions

### Requirement 14: Documentation

**User Story:** As a developer, I want comprehensive documentation, so that I can understand and maintain the C++ implementation.

#### Acceptance Criteria

1. THE C++_Extension SHALL include API documentation for all public functions
2. THE C++_Extension SHALL include architecture documentation explaining design decisions
3. THE C++_Extension SHALL include build instructions for different platforms
4. THE C++_Extension SHALL include performance comparison data
5. THE C++_Extension SHALL include troubleshooting guide for common issues
