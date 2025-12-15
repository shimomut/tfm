# Design Document

## Overview

This document describes the design for implementing a macOS CoreGraphics (Quartz 2D) rendering backend for TTK. The CoreGraphics backend will enable TTK applications to run as native macOS desktop applications while maintaining full compatibility with the existing abstract Renderer API.

The design leverages Apple's CoreGraphics and Cocoa frameworks through PyObjC to provide high-quality text rendering with minimal code complexity. The implementation consists of approximately 300 lines of Python code, making it significantly simpler than alternative approaches like Metal (~1000+ lines) while providing equivalent functionality for TTK's character-grid-based use case.

Key design principles:
- **Simplicity**: Use native macOS APIs directly without complex GPU programming
- **Quality**: Leverage NSAttributedString for native text rendering quality
- **Compatibility**: Implement the exact same Renderer interface as the curses backend
- **Performance**: Achieve sub-10ms rendering for typical 80x24 grids
- **Maintainability**: Keep code simple and well-documented

## Architecture

### Component Overview

The CoreGraphics backend consists of two main classes:

1. **CoreGraphicsBackend**: Implements the Renderer interface and manages the window, font, character grid, and color pairs
2. **TTKView**: A custom NSView subclass that handles the actual drawing operations

```
┌─────────────────────────────────────────────────────────┐
│                    TTK Application                       │
│                  (Uses Renderer API)                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Renderer Interface
                     │
┌────────────────────▼────────────────────────────────────┐
│              CoreGraphicsBackend                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  - Window management (NSWindow)                  │  │
│  │  - Font management (NSFont)                      │  │
│  │  - Character grid (2D array)                     │  │
│  │  - Color pairs (dict)                            │  │
│  │  - Input event translation                       │  │
│  └──────────────────────────────────────────────────┘  │
│                     │                                    │
│                     │ Creates and manages                │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │              TTKView (NSView)                    │   │
│  │  - Implements drawRect_ for rendering           │   │
│  │  - Iterates character grid                      │   │
│  │  - Draws backgrounds and text                   │   │
│  │  - Handles keyboard focus                       │   │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                     │
                     │ PyObjC Bridge
                     │
┌────────────────────▼────────────────────────────────────┐
│              macOS Frameworks                            │
│  - Cocoa (NSWindow, NSView, NSFont, NSColor)           │
│  - CoreGraphics (CGContext, drawing operations)         │
│  - CoreText (text layout and rendering)                 │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

#### Initialization Flow
```
Application calls initialize()
    ↓
Create NSFont and calculate character dimensions
    ↓
Calculate grid dimensions (cols, rows)
    ↓
Create NSWindow with calculated size
    ↓
Create TTKView and set as window content view
    ↓
Initialize character grid (2D array)
    ↓
Initialize default color pair (0)
    ↓
Show window
```

#### Drawing Flow
```
Application calls draw_text(row, col, text, color, attrs)
    ↓
Update character grid cells at specified positions
    ↓
Application calls refresh()
    ↓
Call view.setNeedsDisplay_(True)
    ↓
Cocoa event loop triggers drawRect_
    ↓
Iterate through character grid
    ↓
For each non-empty cell:
    - Calculate pixel position
    - Draw background rectangle
    - Create NSAttributedString with font, color, attributes
    - Draw character
```

#### Input Flow
```
Application calls get_input(timeout_ms)
    ↓
Call NSApp.nextEventMatchingMask_untilDate_inMode_dequeue_
    ↓
Wait for event (blocking, non-blocking, or with timeout)
    ↓
Receive NSEvent
    ↓
Dispatch event with NSApp.sendEvent_
    ↓
Translate NSEvent to KeyEvent
    - Extract key code
    - Extract character
    - Extract modifier flags
    ↓
Return KeyEvent to application
```

## Components and Interfaces

### CoreGraphicsBackend Class

The main backend class that implements the Renderer interface.

**Responsibilities:**
- Window lifecycle management (create, show, close)
- Font initialization and character dimension calculation
- Character grid management (2D array of cells)
- Color pair storage and management
- Input event retrieval and translation
- Coordinate system transformation

**Key Attributes:**
```python
window: NSWindow              # The native macOS window
view: TTKView                 # Custom view for rendering
font: NSFont                  # Monospace font for text
char_width: int               # Width of one character in pixels
char_height: int              # Height of one character in pixels
rows: int                     # Grid height in characters
cols: int                     # Grid width in characters
grid: List[List[Tuple]]       # Character grid: (char, color_pair, attrs)
color_pairs: Dict[int, Tuple] # Color pair storage: {id: (fg_rgb, bg_rgb)}
```

**Key Methods:**
- `initialize()`: Create window, font, and grid
- `shutdown()`: Close window and cleanup
- `get_dimensions()`: Return (rows, cols)
- `clear()`: Reset all grid cells to spaces
- `draw_text()`: Update grid cells with text
- `refresh()`: Trigger view redraw
- `init_color_pair()`: Store color pair
- `get_input()`: Retrieve and translate input events

### TTKView Class

A custom NSView subclass that handles rendering.

**Responsibilities:**
- Implement drawRect_ to render the character grid
- Iterate through grid and draw each cell
- Handle coordinate system transformation (flip y-axis)
- Accept keyboard focus for input handling

**Key Attributes:**
```python
backend: CoreGraphicsBackend  # Reference to backend for grid access
```

**Key Methods:**
- `initWithFrame_backend_()`: Initialize with backend reference
- `drawRect_()`: Render the character grid
- `acceptsFirstResponder()`: Return True to receive keyboard input

### Character Grid Structure

The character grid is a 2D list where each cell contains a tuple:
```python
(char: str, color_pair: int, attributes: int)
```

- `char`: Single character to display (or space for empty)
- `color_pair`: Index into color_pairs dict (0-255)
- `attributes`: Bitwise OR of TextAttribute values

Example grid cell:
```python
('A', 1, TextAttribute.BOLD | TextAttribute.UNDERLINE)
```

### Color Pair Storage

Color pairs are stored in a dictionary:
```python
color_pairs: Dict[int, Tuple[Tuple[int, int, int], Tuple[int, int, int]]]
```

Key: Color pair ID (0-255)
Value: Tuple of (fg_rgb, bg_rgb) where each RGB is (r, g, b) with values 0-255

Example:
```python
color_pairs[1] = ((255, 255, 255), (0, 0, 255))  # White on blue
```

## Data Models

### KeyEvent Translation

NSEvent key codes must be translated to TTK KeyEvent objects:

```python
# NSEvent provides:
- keyCode: int           # macOS virtual key code
- characters: str        # Character representation
- modifierFlags: int     # Modifier key flags

# Translate to KeyEvent:
KeyEvent(
    key_code=keyCode,
    char=characters if characters else None,
    modifiers=modifier_mask  # Translated from modifierFlags
)
```

Modifier flag translation:
```python
NSEventModifierFlagShift   → ModifierKey.SHIFT
NSEventModifierFlagControl → ModifierKey.CONTROL
NSEventModifierFlagOption  → ModifierKey.ALT
NSEventModifierFlagCommand → ModifierKey.COMMAND
```

### Coordinate System Transformation

TTK uses top-left origin (0,0), but CoreGraphics uses bottom-left origin.

**Transformation formulas:**
```python
# TTK coordinates (row, col) to pixel coordinates (x, y):
x = col * char_width
y = (rows - row - 1) * char_height

# This flips the y-axis so row 0 appears at the top
```

Example for 24-row grid:
```
TTK row 0  → pixel y = (24 - 0 - 1) * char_height = 23 * char_height (top)
TTK row 23 → pixel y = (24 - 23 - 1) * char_height = 0 * char_height (bottom)
```

### Font Metrics Calculation

Character dimensions are calculated from the font:

```python
# Create test string with font
test_string = NSAttributedString.alloc().initWithString_attributes_(
    "M", {NSFontAttributeName: font}
)

# Get size
size = test_string.size()
char_width = int(size.width)
char_height = int(size.height * 1.2)  # Add 20% for line spacing
```

The character 'M' is used because it's typically the widest character in monospace fonts.

### Text Attribute Application

Text attributes are applied through NSAttributedString attributes:

**Bold:**
```python
font_manager = NSFontManager.sharedFontManager()
bold_font = font_manager.convertFont_toHaveTrait_(font, NSBoldFontMask)
attributes[NSFontAttributeName] = bold_font
```

**Underline:**
```python
attributes[NSUnderlineStyleAttributeName] = NSUnderlineStyleSingle
```

**Reverse Video:**
```python
# Swap foreground and background colors before creating attributed string
if attrs & TextAttribute.REVERSE:
    fg_rgb, bg_rgb = bg_rgb, fg_rgb
```

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the requirements analysis, the following correctness properties must hold for the CoreGraphics backend implementation:

### Property 1: Character Grid Positioning Consistency

*For any* valid row and column position within the grid bounds, drawing a character at that position should update exactly that cell in the character grid without affecting other cells.

**Validates: Requirements 1.3, 2.2**

### Property 2: Out-of-Bounds Safety

*For any* coordinates that are outside the valid grid bounds (negative or >= dimensions), drawing operations should complete without crashing or raising exceptions.

**Validates: Requirements 2.5**

### Property 3: Fixed Character Dimension Consistency

*For any* character position in the grid, the pixel position calculation should use the same fixed character width and height values throughout the backend's lifetime.

**Validates: Requirements 3.3**

### Property 4: Color Pair Storage Integrity

*For any* valid color pair ID (1-255) with valid RGB values (0-255 for each component), initializing the color pair should store the exact RGB values such that they can be retrieved unchanged.

**Validates: Requirements 4.1**

### Property 5: Attribute Combination Support

*For any* combination of text attributes (bold, underline, reverse), applying multiple attributes simultaneously to a character should preserve all attributes in the character grid cell.

**Validates: Requirements 5.4**

### Property 6: Input Event Translation Completeness

*For any* keyboard event received from macOS, the translation to KeyEvent should produce a valid KeyEvent object with appropriate key code, character, and modifier fields.

**Validates: Requirements 6.1**

### Property 7: Modifier Key Detection

*For any* combination of modifier keys (Shift, Control, Alt, Command), the input event translation should correctly detect and report all pressed modifiers in the modifier mask.

**Validates: Requirements 6.2**

### Property 8: Window Title Preservation

*For any* valid window title string provided during initialization, the created window should display exactly that title.

**Validates: Requirements 7.1**

### Property 9: Dimension Query Consistency

*For any* point in time after initialization, querying window dimensions should return positive integer values for rows and columns that match the current grid size.

**Validates: Requirements 7.3**

### Property 10: Y-Axis Coordinate Transformation

*For any* valid row R in the grid, the pixel y-coordinate should be calculated as (rows - R - 1) * char_height, correctly inverting the y-axis.

**Validates: Requirements 9.3, 9.4**

### Property 11: X-Axis Coordinate Transformation

*For any* valid column C in the grid, the pixel x-coordinate should be calculated as C * char_width.

**Validates: Requirements 9.5**

### Property 12: Selective Grid Updates

*For any* text drawing operation at a specific position, only the cells covered by the text should be modified in the character grid, leaving all other cells unchanged.

**Validates: Requirements 10.2**

### Property 13: ASCII Character Rendering

*For any* printable ASCII character (32-126), drawing that character to the grid should store it correctly and allow it to be rendered.

**Validates: Requirements 11.3**

### Property 14: Color Pair Range Support

*For any* color pair ID in the valid range (0-255), the backend should accept and store the color pair without raising exceptions.

**Validates: Requirements 11.4**

### Property 15: Color Pair Range Validation

*For any* color pair ID outside the valid range (< 0 or > 255), attempting to initialize that color pair should raise a ValueError with range information.

**Validates: Requirements 12.3**

### Property 16: Unicode Character Support

*For any* valid Unicode character, drawing that character to the grid should store it correctly without requiring special handling or manual glyph positioning.

**Validates: Requirements 15.1**

### Property 17: Key Code Consistency

*For any* keyboard input, the key codes produced by the CoreGraphics backend should match the key codes produced by the curses backend for the same logical key.

**Validates: Requirements 16.4**

### Property 18: Exception Type Consistency

*For any* error condition that raises an exception, the exception type should match the exception types used by other backends (curses) for equivalent error conditions.

**Validates: Requirements 17.4**

## Error Handling

The CoreGraphics backend implements comprehensive error handling at multiple levels:

### Initialization Errors

**Missing Dependencies:**
```python
if not COCOA_AVAILABLE:
    raise RuntimeError(
        "PyObjC is required for CoreGraphics backend. "
        "Install with: pip install pyobjc-framework-Cocoa"
    )
```

**Invalid Font:**
```python
self.font = NSFont.fontWithName_size_(self.font_name, self.font_size)
if not self.font:
    raise ValueError(f"Font '{self.font_name}' not found. Use a valid monospace font.")
```

**Window Creation Failure:**
```python
if not self.window:
    raise RuntimeError(
        "Failed to create window. Check system resources and permissions."
    )
```

### Runtime Errors

**Invalid Color Pair ID:**
```python
if pair_id < 1 or pair_id > 255:
    raise ValueError(
        f"Color pair ID must be 1-255, got {pair_id}. "
        f"Color pair 0 is reserved for default colors."
    )
```

**Invalid RGB Values:**
```python
for component in fg_color + bg_color:
    if component < 0 or component > 255:
        raise ValueError(
            f"RGB components must be 0-255, got {component}"
        )
```

**Out-of-Bounds Coordinates:**
```python
# Silently ignore out-of-bounds drawing operations
if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
    return  # No error, just skip the operation
```

### Drawing Errors

Drawing operations that fail should log warnings but not crash:

```python
try:
    # Drawing operation
    attr_string.drawAtPoint_(NSMakePoint(x, y))
except Exception as e:
    # Log warning but continue
    print(f"Warning: Failed to draw character at ({row}, {col}): {e}")
    # Don't re-raise, allow rendering to continue
```

### Resource Cleanup

Shutdown should handle cleanup gracefully even if errors occur:

```python
def shutdown(self) -> None:
    """Clean up resources."""
    try:
        if self.window:
            self.window.close()
    except Exception as e:
        print(f"Warning: Error during shutdown: {e}")
    finally:
        self.window = None
        self.view = None
```

## Testing Strategy

The CoreGraphics backend requires both unit testing and property-based testing to ensure correctness and compatibility with the Renderer interface.

### Unit Testing Approach

Unit tests verify specific examples, edge cases, and integration points:

**Initialization Tests:**
- Verify window is created with correct title
- Verify font is loaded and character dimensions calculated
- Verify grid is initialized with correct dimensions
- Verify default color pair (0) is set up
- Verify PyObjC dependency check works

**Drawing Tests:**
- Verify draw_text updates grid cells correctly
- Verify clear() resets all cells
- Verify clear_region() resets specified cells
- Verify draw_hline() and draw_vline() work correctly
- Verify draw_rect() works for filled and outlined rectangles

**Color Tests:**
- Verify init_color_pair() stores colors correctly
- Verify color pair 0 defaults to white on black
- Verify 256 color pairs can be initialized
- Verify invalid color pair IDs raise ValueError

**Input Tests:**
- Verify get_input() with timeout=0 returns immediately
- Verify get_input() with timeout=-1 blocks
- Verify keyboard events are translated to KeyEvent
- Verify modifier keys are detected correctly

**Coordinate Tests:**
- Verify coordinate transformation formulas
- Verify row 0 appears at top
- Verify column 0 appears at left

**Error Handling Tests:**
- Verify missing PyObjC raises RuntimeError
- Verify invalid font raises ValueError
- Verify out-of-bounds drawing doesn't crash
- Verify invalid color pair IDs raise ValueError

### Property-Based Testing Approach

Property-based tests verify universal properties across many randomly generated inputs:

**Property Test 1: Character Grid Positioning Consistency**
- Generate random valid (row, col) positions
- Generate random characters
- Draw character at position
- Verify grid cell at that position contains the character
- Verify other cells are unchanged
- **Validates: Property 1**

**Property Test 2: Out-of-Bounds Safety**
- Generate random out-of-bounds coordinates (negative, >= dimensions)
- Attempt to draw at those positions
- Verify no exceptions are raised
- Verify grid remains valid
- **Validates: Property 2**

**Property Test 3: Fixed Character Dimension Consistency**
- Generate random positions
- Calculate pixel coordinates for each
- Verify all calculations use the same char_width and char_height
- **Validates: Property 3**

**Property Test 4: Color Pair Storage Integrity**
- Generate random valid color pair IDs (1-255)
- Generate random RGB values (0-255 for each component)
- Initialize color pair
- Retrieve color pair
- Verify stored values match initialized values exactly
- **Validates: Property 4**

**Property Test 5: Attribute Combination Support**
- Generate random combinations of TextAttribute values
- Draw character with combined attributes
- Verify grid cell stores all attributes
- **Validates: Property 5**

**Property Test 6: Input Event Translation Completeness**
- Generate various keyboard events (simulated)
- Translate to KeyEvent
- Verify KeyEvent has valid key_code, char, and modifiers
- **Validates: Property 6**

**Property Test 7: Modifier Key Detection**
- Generate random combinations of modifier flags
- Translate to KeyEvent
- Verify all pressed modifiers are detected
- **Validates: Property 7**

**Property Test 8: Window Title Preservation**
- Generate random window title strings
- Initialize backend with title
- Verify window displays exact title
- **Validates: Property 8**

**Property Test 9: Dimension Query Consistency**
- Query dimensions multiple times
- Verify dimensions are always positive integers
- Verify dimensions match grid size
- **Validates: Property 9**

**Property Test 10: Y-Axis Coordinate Transformation**
- Generate random valid row values
- Calculate pixel y-coordinate
- Verify formula: y = (rows - row - 1) * char_height
- **Validates: Property 10**

**Property Test 11: X-Axis Coordinate Transformation**
- Generate random valid column values
- Calculate pixel x-coordinate
- Verify formula: x = col * char_width
- **Validates: Property 11**

**Property Test 12: Selective Grid Updates**
- Initialize grid with known state
- Generate random text and position
- Draw text
- Verify only affected cells changed
- Verify other cells unchanged
- **Validates: Property 12**

**Property Test 13: ASCII Character Rendering**
- Generate all printable ASCII characters (32-126)
- Draw each character
- Verify each is stored correctly in grid
- **Validates: Property 13**

**Property Test 14: Color Pair Range Support**
- Generate random valid color pair IDs (0-255)
- Initialize with random RGB values
- Verify no exceptions raised
- **Validates: Property 14**

**Property Test 15: Color Pair Range Validation**
- Generate random invalid color pair IDs (< 0 or > 255)
- Attempt to initialize
- Verify ValueError is raised
- Verify error message contains range information
- **Validates: Property 15**

**Property Test 16: Unicode Character Support**
- Generate random Unicode characters
- Draw each character
- Verify stored correctly without special handling
- **Validates: Property 16**

**Property Test 17: Key Code Consistency**
- Generate various keyboard inputs
- Compare key codes between CoreGraphics and curses backends
- Verify key codes match for same logical keys
- **Validates: Property 17**

**Property Test 18: Exception Type Consistency**
- Generate various error conditions
- Verify exception types match curses backend
- **Validates: Property 18**

### Integration Testing

Integration tests verify the backend works with real TTK applications:

**Demo Application Tests:**
- Run existing TTK demo applications with CoreGraphics backend
- Verify visual output matches curses backend
- Verify keyboard input works correctly
- Verify window management works correctly

**Backend Switching Tests:**
- Create application that works with both backends
- Switch between backends
- Verify identical behavior
- Verify no application code changes needed

**Performance Tests:**
- Measure rendering time for 80x24 grid
- Verify < 10ms rendering time
- Measure rendering time for 200x60 grid
- Verify acceptable performance

## Implementation Notes

### PyObjC Bridge Considerations

The implementation relies on PyObjC to bridge Python and Objective-C:

**Import Pattern:**
```python
try:
    import Cocoa
    import Quartz
    import objc
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False
```

**Method Name Translation:**
PyObjC translates Objective-C method names to Python:
- `initWithFrame:` becomes `initWithFrame_()`
- `setNeedsDisplay:` becomes `setNeedsDisplay_()`
- `drawAtPoint:` becomes `drawAtPoint_()`

**Custom Method Signatures:**
For custom methods with multiple parameters:
```python
def initWithFrame_backend_(self, frame, backend):
    # Custom initializer with two parameters
    pass
```

### Memory Management

PyObjC handles memory management automatically through reference counting. However, we should:

1. Set references to None in shutdown()
2. Avoid circular references between backend and view
3. Let PyObjC handle Cocoa object lifecycle

### Thread Safety

CoreGraphics and Cocoa are not thread-safe. All operations must occur on the main thread:

- Window creation: main thread
- Drawing operations: main thread (via drawRect_)
- Event processing: main thread

The backend assumes single-threaded usage, which is appropriate for TTK's event-driven model.

### Performance Optimization

**Skip Empty Cells:**
```python
if char == ' ' and color_pair == 0:
    continue  # Skip rendering default empty cells
```

**Batch Drawing:**
All drawing operations update the grid, then a single refresh() triggers one drawRect_ call.

**Efficient Grid Storage:**
Use simple list of lists rather than complex data structures.

### Coordinate System Gotchas

The y-axis inversion is the most error-prone aspect:

**Correct:**
```python
y = (self.rows - row - 1) * self.char_height
```

**Incorrect:**
```python
y = row * self.char_height  # Would draw upside-down
```

Always remember: CoreGraphics origin is bottom-left, TTK origin is top-left.

## Future Enhancements

While not part of the initial implementation, the design supports future enhancements:

### Image Rendering Support

The architecture can be extended to support image rendering:

1. Add image drawing methods to Renderer interface
2. Implement using NSImage in CoreGraphics backend
3. Support both character-grid and pixel-based positioning

### Window Resizing

Currently, window resizing recalculates grid dimensions. Future enhancements could:

1. Support dynamic grid resizing
2. Emit resize events to applications
3. Allow applications to handle resize gracefully

### Multiple Windows

The design could support multiple windows:

1. Create multiple CoreGraphicsBackend instances
2. Each manages its own window and grid
3. Share font and color pair definitions

### Retina Display Support

For high-DPI displays:

1. Use NSWindow's backingScaleFactor
2. Adjust character dimensions accordingly
3. Ensure crisp text rendering on Retina displays

### Custom Fonts

Allow runtime font changes:

1. Add set_font() method to Renderer interface
2. Recalculate character dimensions
3. Recalculate grid dimensions
4. Trigger full redraw

These enhancements maintain backward compatibility with the current design.
