# TTK API Reference

This document provides a complete reference for the TTK (TUI Toolkit) library API.

## Table of Contents

- [Core Classes](#core-classes)
  - [Renderer](#renderer)
  - [KeyEvent](#KeyEvent)
  - [KeyCode](#keycode)
  - [ModifierKey](#modifierkey)
  - [TextAttribute](#textattribute)
- [Backend Implementations](#backend-implementations)
  - [CursesBackend](#cursesbackend)
  - [CoreGraphicsBackend](#coregraphicsbackend)
- [Serialization](#serialization)
- [Utilities](#utilities)

## Core Classes

### Renderer

The `Renderer` class is the abstract base class for all rendering backends. Applications interact with this interface without needing to know which backend is being used.

```python
from abc import ABC, abstractmethod
from typing import Tuple, Optional

class Renderer(ABC):
    """Abstract base class for text grid rendering backends."""
```

#### Initialization and Cleanup

##### `initialize() -> None`

Initialize the rendering backend and create the window.

**Example:**
```python
renderer = CursesBackend()
renderer.initialize()
```

##### `shutdown() -> None`

Clean up resources and close the window. Always call this method when done with the renderer.

**Example:**
```python
try:
    renderer.initialize()
    # ... use renderer ...
finally:
    renderer.shutdown()
```

#### Window Management

##### `get_dimensions() -> Tuple[int, int]`

Get window dimensions in character cells.

**Returns:** Tuple of `(rows, columns)` representing the character grid size.

**Example:**
```python
rows, cols = renderer.get_dimensions()
print(f"Window size: {rows} rows x {cols} columns")
```

##### `clear() -> None`

Clear the entire window.

**Example:**
```python
renderer.clear()
renderer.refresh()
```

##### `clear_region(row: int, col: int, height: int, width: int) -> None`

Clear a rectangular region.

**Parameters:**
- `row`: Starting row (0-based)
- `col`: Starting column (0-based)
- `height`: Height in character rows
- `width`: Width in character columns

**Example:**
```python
# Clear a 10x20 region starting at row 5, column 10
renderer.clear_region(5, 10, 10, 20)
```

#### Drawing Operations

##### `draw_text(row: int, col: int, text: str, color_pair: int = 0, attributes: int = 0) -> None`

Draw text at the specified position.

**Parameters:**
- `row`: Row position (0-based, 0 is top)
- `col`: Column position (0-based, 0 is left)
- `text`: Text string to draw
- `color_pair`: Color pair index (0-255)
- `attributes`: Bitwise OR of TextAttribute values

**Example:**
```python
from ttk import TextAttribute

# Draw normal text
renderer.draw_text(0, 0, "Hello, World!")

# Draw bold text with color
renderer.draw_text(1, 0, "Bold Text", color_pair=1, 
                   attributes=TextAttribute.BOLD)

# Draw text with multiple attributes
renderer.draw_text(2, 0, "Bold + Underline", color_pair=2,
                   attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE)
```

##### `draw_hline(row: int, col: int, char: str, length: int, color_pair: int = 0) -> None`

Draw a horizontal line.

**Parameters:**
- `row`: Row position
- `col`: Starting column position
- `char`: Character to use for the line
- `length`: Length in characters
- `color_pair`: Color pair index

**Example:**
```python
# Draw a horizontal line using box-drawing character (recommended)
renderer.draw_hline(5, 0, '─', 40, color_pair=1)

# Draw a horizontal line of equals signs
renderer.draw_hline(10, 5, '=', 30)

# ASCII alternative (for compatibility)
renderer.draw_hline(15, 0, '-', 40)
```

##### `draw_vline(row: int, col: int, char: str, length: int, color_pair: int = 0) -> None`

Draw a vertical line.

**Parameters:**
- `row`: Starting row position
- `col`: Column position
- `char`: Character to use for the line
- `length`: Length in characters
- `color_pair`: Color pair index

**Example:**
```python
# Draw a vertical line using box-drawing character (recommended)
renderer.draw_vline(0, 10, '│', 20, color_pair=1)

# ASCII alternative (for compatibility)
renderer.draw_vline(0, 15, '|', 20)
```

##### `draw_rect(row: int, col: int, height: int, width: int, color_pair: int = 0, filled: bool = False) -> None`

Draw a rectangle.

**Parameters:**
- `row`: Top-left row position
- `col`: Top-left column position
- `height`: Height in character rows
- `width`: Width in character columns
- `color_pair`: Color pair index
- `filled`: If True, fill the rectangle; if False, draw outline only

**Example:**
```python
# Draw an outlined rectangle
renderer.draw_rect(2, 2, 10, 30, color_pair=1, filled=False)

# Draw a filled rectangle
renderer.draw_rect(15, 5, 5, 20, color_pair=2, filled=True)
```

#### Display Updates

##### `refresh() -> None`

Refresh the entire window to display all pending changes.

**Example:**
```python
renderer.draw_text(0, 0, "Hello")
renderer.draw_text(1, 0, "World")
renderer.refresh()  # Display both lines
```

##### `refresh_region(row: int, col: int, height: int, width: int) -> None`

Refresh a specific region of the window. This can be more efficient than refreshing the entire window.

**Parameters:**
- `row`: Starting row
- `col`: Starting column
- `height`: Height in rows
- `width`: Width in columns

**Example:**
```python
# Update only a specific region
renderer.draw_text(5, 10, "Updated")
renderer.refresh_region(5, 10, 1, 7)
```

#### Color Management

##### `init_color_pair(pair_id: int, fg_color: Tuple[int, int, int], bg_color: Tuple[int, int, int]) -> None`

Initialize a color pair with RGB values.

**Parameters:**
- `pair_id`: Color pair index (1-255, 0 is reserved for default)
- `fg_color`: Foreground color as (R, G, B) tuple (0-255 each)
- `bg_color`: Background color as (R, G, B) tuple (0-255 each)

**Example:**
```python
# Initialize color pair 1: white on blue
renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))

# Initialize color pair 2: yellow on black
renderer.init_color_pair(2, (255, 255, 0), (0, 0, 0))

# Use the color pairs
renderer.draw_text(0, 0, "White on blue", color_pair=1)
renderer.draw_text(1, 0, "Yellow on black", color_pair=2)
```

#### Input Handling

##### `get_input(timeout_ms: int = -1) -> Optional[KeyEvent]`

Get the next input event.

**Parameters:**
- `timeout_ms`: Timeout in milliseconds. -1 for blocking, 0 for non-blocking.

**Returns:** `KeyEvent` if input is available, `None` if timeout expires.

**Example:**
```python
# Blocking input (wait forever)
event = renderer.get_input()

# Non-blocking input (return immediately)
event = renderer.get_input(timeout_ms=0)
if event is None:
    print("No input available")

# Timeout after 1 second
event = renderer.get_input(timeout_ms=1000)
```

#### Cursor Control

##### `set_cursor_visibility(visible: bool) -> None`

Set cursor visibility.

**Parameters:**
- `visible`: True to show cursor, False to hide it.

**Example:**
```python
# Hide cursor
renderer.set_cursor_visibility(False)

# Show cursor
renderer.set_cursor_visibility(True)
```

##### `move_cursor(row: int, col: int) -> None`

Move the cursor to the specified position.

**Parameters:**
- `row`: Row position
- `col`: Column position

**Example:**
```python
renderer.move_cursor(10, 20)
renderer.set_cursor_visibility(True)
```

### KeyEvent

Represents a user input event with a unified interface across backends.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class KeyEvent:
    """Represents a user input event."""
    key_code: int  # KeyCode value or Unicode code point
    modifiers: int  # Bitwise OR of ModifierKey values
    char: Optional[str] = None  # Character for printable keys
    mouse_row: Optional[int] = None  # For mouse events
    mouse_col: Optional[int] = None  # For mouse events
    mouse_button: Optional[int] = None  # 1=left, 2=middle, 3=right
```

#### Methods

##### `is_printable() -> bool`

Check if this is a printable character.

**Example:**
```python
event = renderer.get_input()
if event.is_printable():
    print(f"Printable character: {event.char}")
```

##### `is_special_key() -> bool`

Check if this is a special key (arrow, function, etc.).

**Example:**
```python
event = renderer.get_input()
if event.is_special_key():
    print(f"Special key code: {event.key_code}")
```

##### `has_modifier(modifier: ModifierKey) -> bool`

Check if a specific modifier key is pressed.

**Example:**
```python
from ttk import ModifierKey

event = renderer.get_input()
if event.has_modifier(ModifierKey.CONTROL):
    print("Control key is pressed")
if event.has_modifier(ModifierKey.SHIFT):
    print("Shift key is pressed")
```

### KeyCode

Standard key codes for special keys.

```python
from enum import IntEnum

class KeyCode(IntEnum):
    """Standard key codes for special keys."""
    # Printable characters use their Unicode code points
    
    # Special keys
    ENTER = 10
    ESCAPE = 27
    BACKSPACE = 127
    TAB = 9
    
    # Arrow keys
    UP = 1000
    DOWN = 1001
    LEFT = 1002
    RIGHT = 1003
    
    # Function keys
    F1 = 1100
    F2 = 1101
    F3 = 1102
    F4 = 1103
    F5 = 1104
    F6 = 1105
    F7 = 1106
    F8 = 1107
    F9 = 1108
    F10 = 1109
    F11 = 1110
    F12 = 1111
    
    # Editing keys
    INSERT = 1200
    DELETE = 1201
    HOME = 1202
    END = 1203
    PAGE_UP = 1204
    PAGE_DOWN = 1205
    
    # Mouse event marker
    MOUSE = 2000
    
    # Window events
    RESIZE = 3000
```

**Example:**
```python
from ttk import KeyCode

event = renderer.get_input()
if event.key_code == KeyCode.ENTER:
    print("Enter key pressed")
elif event.key_code == KeyCode.UP:
    print("Up arrow pressed")
elif event.key_code == KeyCode.F1:
    print("F1 pressed")
```

### ModifierKey

Modifier key flags (can be combined with bitwise OR).

```python
from enum import IntEnum

class ModifierKey(IntEnum):
    """Modifier key flags (can be combined with bitwise OR)."""
    NONE = 0
    SHIFT = 1
    CONTROL = 2
    ALT = 4
    COMMAND = 8  # macOS Command key
```

**Example:**
```python
from ttk import ModifierKey

event = renderer.get_input()

# Check for Ctrl+C
if event.char == 'c' and event.has_modifier(ModifierKey.CONTROL):
    print("Ctrl+C pressed")

# Check for Shift+Alt combination
if event.modifiers & (ModifierKey.SHIFT | ModifierKey.ALT):
    print("Shift and/or Alt pressed")
```

### TextAttribute

Text rendering attributes.

```python
from enum import IntEnum

class TextAttribute(IntEnum):
    """Text rendering attributes."""
    NORMAL = 0
    BOLD = 1
    UNDERLINE = 2
    REVERSE = 4
    # Attributes can be combined with bitwise OR
```

**Example:**
```python
from ttk import TextAttribute

# Normal text
renderer.draw_text(0, 0, "Normal")

# Bold text
renderer.draw_text(1, 0, "Bold", attributes=TextAttribute.BOLD)

# Underlined text
renderer.draw_text(2, 0, "Underline", attributes=TextAttribute.UNDERLINE)

# Reverse video
renderer.draw_text(3, 0, "Reverse", attributes=TextAttribute.REVERSE)

# Combined attributes
renderer.draw_text(4, 0, "Bold + Underline",
                   attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE)
```

## Backend Implementations

### CursesBackend

Terminal-based rendering backend using Python's curses library.

```python
from ttk.backends.curses_backend import CursesBackend

renderer = CursesBackend()
```

**Platform Support:** Unix-like systems (Linux, macOS, BSD)

**Features:**
- Full terminal color support
- All text attributes (bold, underline, reverse)
- Keyboard and special key input
- Terminal resize handling

**Example:**
```python
from ttk.backends.curses_backend import CursesBackend

renderer = CursesBackend()
renderer.initialize()

try:
    # Initialize colors
    renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))
    
    # Draw text
    renderer.draw_text(0, 0, "Terminal Application", color_pair=1)
    renderer.refresh()
    
    # Wait for input
    event = renderer.get_input()
    
finally:
    renderer.shutdown()
```

### CoreGraphicsBackend

Native macOS desktop application backend using Apple's CoreGraphics (Quartz 2D) framework.

```python
from ttk.backends.coregraphics_backend import CoreGraphicsBackend

renderer = CoreGraphicsBackend(
    window_title="My Application",
    font_name="Menlo",
    font_size=14
)
```

**Platform Support:** macOS only

**Requirements:**
- macOS 10.13 or later
- PyObjC framework: `pip install pyobjc-framework-Cocoa`

**Parameters:**
- `window_title`: Title for the native window (default: "TextGrid Application")
- `font_name`: Monospace font name (default: "Menlo")
- `font_size`: Font size in points (default: 14)

**Features:**
- Native macOS text rendering with NSAttributedString
- High-quality font rendering with automatic font fallback
- Full RGB color support (256 color pairs)
- Unicode and emoji support
- All text attributes (bold, underline, reverse)
- Native window controls (close, minimize, resize)
- Simple implementation (~300 lines of code)

**Example:**
```python
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk import KeyCode

renderer = CoreGraphicsBackend(
    window_title="Desktop File Manager",
    font_name="Monaco",
    font_size=12
)
renderer.initialize()

try:
    # Initialize colors
    renderer.init_color_pair(1, (255, 255, 255), (30, 30, 30))
    
    # Draw text
    renderer.draw_text(0, 0, "Desktop Application", color_pair=1)
    renderer.refresh()
    
    # Event loop
    while True:
        event = renderer.get_input()
        if event and event.key_code == KeyCode.ESCAPE:
            break
    
finally:
    renderer.shutdown()
```

### CoreGraphicsBackend

Native macOS desktop application backend using Apple's CoreGraphics framework.

```python
from ttk.backends.coregraphics_backend import CoreGraphicsBackend

renderer = CoreGraphicsBackend(
    window_title="My Application",
    font_name="Menlo",
    font_size=14
)
```

**Platform Support:** macOS only

**Parameters:**
- `window_title`: Title for the native window (default: "TextGrid Application")
- `font_name`: Monospace font name (default: "Menlo")
- `font_size`: Font size in points (default: 14)

**Features:**
- Native macOS text rendering
- Native macOS window
- Full RGB color support
- High performance (< 10ms for 80x24 grid)
- Monospace font validation

**Example:**
```python
from ttk.backends.coregraphics_backend import CoreGraphicsBackend

renderer = CoreGraphicsBackend(
    window_title="Desktop File Manager",
    font_name="Monaco",
    font_size=12
)
renderer.initialize()

try:
    # Initialize colors
    renderer.init_color_pair(1, (255, 255, 255), (30, 30, 30))
    
    # Draw text
    renderer.draw_text(0, 0, "Desktop Application", color_pair=1)
    renderer.refresh()
    
    # Event loop
    while True:
        event = renderer.get_input(timeout_ms=16)  # ~60 FPS
        if event and event.key_code == KeyCode.ESCAPE:
            break
    
finally:
    renderer.shutdown()
```

## Serialization

The serialization module provides functions for serializing, parsing, and pretty-printing rendering commands.

```python
from ttk.serialization.command_serializer import (
    serialize_command,
    parse_command,
    pretty_print_command
)
```

### `serialize_command(command_type: str, **kwargs) -> dict`

Serialize a rendering command to a dictionary format.

**Example:**
```python
# Serialize a draw_text command
cmd = serialize_command('draw_text', row=0, col=0, text="Hello", 
                       color_pair=1, attributes=0)
# Returns: {'type': 'draw_text', 'row': 0, 'col': 0, ...}
```

### `parse_command(command_dict: dict) -> dict`

Parse a serialized command dictionary.

**Example:**
```python
cmd_dict = {'type': 'draw_text', 'row': 0, 'col': 0, 'text': 'Hello'}
parsed = parse_command(cmd_dict)
```

### `pretty_print_command(command_dict: dict) -> str`

Format a command as a human-readable string.

**Example:**
```python
cmd = serialize_command('draw_rect', row=2, col=2, height=10, 
                       width=20, color_pair=1, filled=False)
print(pretty_print_command(cmd))
# Output:
# draw_rect(
#   row=2,
#   col=2,
#   height=10,
#   width=20,
#   color_pair=1,
#   filled=False
# )
```

## Utilities

### Platform Detection

```python
from ttk.utils.platform_utils import get_recommended_backend

backend_name = get_recommended_backend()
# Returns: 'coregraphics' on macOS, 'curses' on other platforms
```

### Color Utilities

```python
from ttk.utils.color_utils import rgb_to_hex, hex_to_rgb

# Convert RGB to hex
hex_color = rgb_to_hex(255, 128, 0)  # Returns: '#FF8000'

# Convert hex to RGB
r, g, b = hex_to_rgb('#FF8000')  # Returns: (255, 128, 0)
```

### Validation

```python
from ttk.utils.validation import (
    validate_color_pair_id,
    validate_rgb_color,
    validate_coordinates
)

# Validate color pair ID (1-255)
validate_color_pair_id(1)  # OK
validate_color_pair_id(256)  # Raises ValueError

# Validate RGB color (0-255 for each component)
validate_rgb_color((255, 128, 0))  # OK
validate_rgb_color((256, 0, 0))  # Raises ValueError

# Validate coordinates
validate_coordinates(10, 20)  # OK
validate_coordinates(-1, 20)  # Raises ValueError
```

## Coordinate System

TTK uses a character-based coordinate system:

- **Origin:** (0, 0) is at the top-left corner
- **Rows:** Increase downward (0 is top)
- **Columns:** Increase rightward (0 is left)
- **Units:** All positions and dimensions are in character cells

```
(0,0)  (0,1)  (0,2)  ...  (0,cols-1)
(1,0)  (1,1)  (1,2)  ...  (1,cols-1)
(2,0)  (2,1)  (2,2)  ...  (2,cols-1)
  ...    ...    ...   ...     ...
(rows-1,0)           ...  (rows-1,cols-1)
```

## Error Handling

### Common Exceptions

- **ValueError:** Invalid parameters (negative dimensions, invalid RGB values, etc.)
- **TypeError:** Incomplete backend implementation
- **RuntimeError:** Backend initialization or operation failures

### Out-of-Bounds Handling

Drawing operations with coordinates outside the window bounds are handled gracefully:
- Curses backend: Ignores out-of-bounds drawing
- CoreGraphics backend: Clips to window boundaries

**Example:**
```python
rows, cols = renderer.get_dimensions()

# This won't crash, but won't draw anything visible
renderer.draw_text(rows + 10, cols + 10, "Out of bounds")
```

## Best Practices

1. **Always use try-finally for cleanup:**
   ```python
   renderer = CursesBackend()
   renderer.initialize()
   try:
       # Your application code
       pass
   finally:
       renderer.shutdown()
   ```

2. **Initialize color pairs before use:**
   ```python
   renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))
   renderer.draw_text(0, 0, "Text", color_pair=1)
   ```

3. **Call refresh() after drawing:**
   ```python
   renderer.draw_text(0, 0, "Hello")
   renderer.draw_text(1, 0, "World")
   renderer.refresh()  # Display both lines
   ```

4. **Use non-blocking input for animations:**
   ```python
   while running:
       # Update display
       renderer.refresh()
       
       # Check for input without blocking
       event = renderer.get_input(timeout_ms=0)
       if event:
           handle_input(event)
   ```

5. **Handle window resize events:**
   ```python
   event = renderer.get_input()
   if event.key_code == KeyCode.RESIZE:
       rows, cols = renderer.get_dimensions()
       # Redraw UI with new dimensions
   ```
