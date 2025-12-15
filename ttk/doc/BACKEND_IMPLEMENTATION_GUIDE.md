# Backend Implementation Guide

This guide explains how to implement a new rendering backend for TTK. By following this guide, you can add support for new platforms or rendering systems.

## Table of Contents

- [Overview](#overview)
- [Backend Requirements](#backend-requirements)
- [Implementation Steps](#implementation-steps)
- [Abstract Methods Reference](#abstract-methods-reference)
- [Testing Your Backend](#testing-your-backend)
- [Best Practices](#best-practices)
- [Example: Minimal Backend](#example-minimal-backend)

## Overview

A TTK backend is a class that inherits from the `Renderer` abstract base class and implements all required methods. The backend handles:

1. **Window Management**: Creating and managing the rendering surface
2. **Drawing Operations**: Rendering text, shapes, and colors
3. **Input Handling**: Translating platform-specific input to KeyEvent objects
4. **Resource Management**: Initializing and cleaning up platform resources

## Backend Requirements

### Must Implement All Abstract Methods

Your backend must implement every abstract method defined in the `Renderer` class. Python's ABC mechanism will raise `TypeError` if any methods are missing.

### Must Use Character Grid Coordinates

All positioning must use character-based coordinates:
- (0, 0) is the top-left corner
- Rows increase downward
- Columns increase rightward
- All dimensions are in character cells, not pixels

### Must Support Monospace Fonts

TTK assumes all characters have the same width and height. Your backend must:
- Use monospace fonts only
- Validate fonts at initialization
- Reject proportional fonts with clear error messages

### Must Handle Errors Gracefully

- Out-of-bounds drawing should be clipped or ignored (not crash)
- Invalid parameters should raise appropriate exceptions
- Resource cleanup must happen even if errors occur

## Implementation Steps

### Step 1: Create Backend Class

Create a new file in `ttk/backends/` for your backend:

```python
# ttk/backends/my_backend.py

from ttk.renderer import Renderer
from ttk.input_event import KeyEvent
from typing import Tuple, Optional

class MyBackend(Renderer):
    """My custom rendering backend."""
    
    def __init__(self, **kwargs):
        """Initialize backend with configuration."""
        # Store configuration
        self.config = kwargs
        
        # Initialize instance variables
        self.initialized = False
        self.window = None
        self.rows = 0
        self.cols = 0
        self.color_pairs = {}
```

### Step 2: Implement Initialization

Implement `initialize()` to set up your rendering system:

```python
def initialize(self) -> None:
    """Initialize the rendering backend."""
    if self.initialized:
        return
    
    # Create window/surface
    self.window = self._create_window()
    
    # Calculate dimensions
    self.rows, self.cols = self._calculate_dimensions()
    
    # Set up rendering resources
    self._setup_rendering()
    
    # Initialize default color pair
    self.init_color_pair(0, (255, 255, 255), (0, 0, 0))
    
    self.initialized = True

def _create_window(self):
    """Create the rendering window (platform-specific)."""
    # Your platform-specific window creation code
    pass

def _calculate_dimensions(self) -> Tuple[int, int]:
    """Calculate window dimensions in character cells."""
    # Calculate based on window size and character dimensions
    pass

def _setup_rendering(self):
    """Set up rendering resources."""
    # Initialize rendering pipeline, buffers, etc.
    pass
```

### Step 3: Implement Shutdown

Implement `shutdown()` to clean up resources:

```python
def shutdown(self) -> None:
    """Clean up resources and close window."""
    if not self.initialized:
        return
    
    # Close window
    if self.window:
        self._close_window()
        self.window = None
    
    # Release rendering resources
    self._cleanup_rendering()
    
    # Clear state
    self.color_pairs.clear()
    self.initialized = False

def _close_window(self):
    """Close the rendering window (platform-specific)."""
    pass

def _cleanup_rendering(self):
    """Clean up rendering resources."""
    pass
```

### Step 4: Implement Window Management

```python
def get_dimensions(self) -> Tuple[int, int]:
    """Get window dimensions in character cells."""
    return (self.rows, self.cols)

def clear(self) -> None:
    """Clear the entire window."""
    self.clear_region(0, 0, self.rows, self.cols)

def clear_region(self, row: int, col: int, height: int, width: int) -> None:
    """Clear a rectangular region."""
    # Validate bounds
    if row < 0 or col < 0:
        return
    
    # Clip to window bounds
    end_row = min(row + height, self.rows)
    end_col = min(col + width, self.cols)
    
    # Clear the region (platform-specific)
    for r in range(row, end_row):
        for c in range(col, end_col):
            self._clear_cell(r, c)

def _clear_cell(self, row: int, col: int):
    """Clear a single cell (platform-specific)."""
    pass
```

### Step 5: Implement Drawing Operations

```python
def draw_text(self, row: int, col: int, text: str,
              color_pair: int = 0, attributes: int = 0) -> None:
    """Draw text at the specified position."""
    # Validate bounds
    if row < 0 or row >= self.rows or col < 0:
        return
    
    # Draw each character
    for i, char in enumerate(text):
        c = col + i
        if c >= self.cols:
            break
        
        # Get colors
        fg, bg = self.color_pairs.get(color_pair, ((255, 255, 255), (0, 0, 0)))
        
        # Draw character (platform-specific)
        self._draw_character(row, c, char, fg, bg, attributes)

def _draw_character(self, row: int, col: int, char: str,
                   fg_color: Tuple[int, int, int],
                   bg_color: Tuple[int, int, int],
                   attributes: int):
    """Draw a single character (platform-specific)."""
    pass

def draw_hline(self, row: int, col: int, char: str,
               length: int, color_pair: int = 0) -> None:
    """Draw a horizontal line."""
    self.draw_text(row, col, char[0] * length, color_pair)

def draw_vline(self, row: int, col: int, char: str,
               length: int, color_pair: int = 0) -> None:
    """Draw a vertical line."""
    for i in range(length):
        if row + i < self.rows:
            self.draw_text(row + i, col, char[0], color_pair)

def draw_rect(self, row: int, col: int, height: int, width: int,
              color_pair: int = 0, filled: bool = False) -> None:
    """Draw a rectangle."""
    if filled:
        # Fill rectangle
        for r in range(row, min(row + height, self.rows)):
            self.draw_text(r, col, ' ' * width, color_pair)
    else:
        # Draw outline
        self.draw_hline(row, col, '-', width, color_pair)
        self.draw_hline(row + height - 1, col, '-', width, color_pair)
        self.draw_vline(row, col, '|', height, color_pair)
        self.draw_vline(row, col + width - 1, '|', height, color_pair)
```

### Step 6: Implement Display Updates

```python
def refresh(self) -> None:
    """Refresh the entire window."""
    self.refresh_region(0, 0, self.rows, self.cols)

def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
    """Refresh a specific region."""
    # Validate bounds
    if row < 0 or col < 0:
        return
    
    # Clip to window bounds
    end_row = min(row + height, self.rows)
    end_col = min(col + width, self.cols)
    
    # Render the region (platform-specific)
    self._render_region(row, col, end_row - row, end_col - col)

def _render_region(self, row: int, col: int, height: int, width: int):
    """Render a region to the screen (platform-specific)."""
    pass
```

### Step 7: Implement Color Management

```python
def init_color_pair(self, pair_id: int, fg_color: Tuple[int, int, int],
                   bg_color: Tuple[int, int, int]) -> None:
    """Initialize a color pair."""
    # Validate pair ID
    if pair_id < 0 or pair_id > 255:
        raise ValueError(f"Color pair ID must be 0-255, got {pair_id}")
    
    # Validate RGB values
    for component in fg_color + bg_color:
        if component < 0 or component > 255:
            raise ValueError(f"RGB values must be 0-255, got {component}")
    
    # Store color pair
    self.color_pairs[pair_id] = (fg_color, bg_color)
    
    # Initialize in rendering system (platform-specific)
    self._init_platform_color_pair(pair_id, fg_color, bg_color)

def _init_platform_color_pair(self, pair_id: int,
                              fg_color: Tuple[int, int, int],
                              bg_color: Tuple[int, int, int]):
    """Initialize color pair in platform rendering system."""
    pass
```

### Step 8: Implement Input Handling

```python
def get_input(self, timeout_ms: int = -1) -> Optional[KeyEvent]:
    """Get the next input event."""
    # Poll platform event system
    platform_event = self._poll_platform_event(timeout_ms)
    
    if platform_event is None:
        return None
    
    # Translate to KeyEvent
    return self._translate_platform_event(platform_event)

def _poll_platform_event(self, timeout_ms: int):
    """Poll platform event system (platform-specific)."""
    # Your platform-specific event polling code
    pass

def _translate_platform_event(self, platform_event) -> KeyEvent:
    """Translate platform event to KeyEvent."""
    from ttk.input_event import KeyCode, ModifierKey
    
    # Extract event data
    key_code = self._get_key_code(platform_event)
    modifiers = self._get_modifiers(platform_event)
    char = self._get_char(platform_event)
    
    # Create KeyEvent
    return KeyEvent(
        key_code=key_code,
        modifiers=modifiers,
        char=char
    )

def _get_key_code(self, platform_event) -> int:
    """Extract key code from platform event."""
    # Map platform key codes to KeyCode values
    pass

def _get_modifiers(self, platform_event) -> int:
    """Extract modifier keys from platform event."""
    # Map platform modifiers to ModifierKey flags
    pass

def _get_char(self, platform_event) -> Optional[str]:
    """Extract character from platform event."""
    # Return character for printable keys, None otherwise
    pass
```

### Step 9: Implement Cursor Control

```python
def set_cursor_visibility(self, visible: bool) -> None:
    """Set cursor visibility."""
    self._set_platform_cursor_visibility(visible)

def move_cursor(self, row: int, col: int) -> None:
    """Move cursor to specified position."""
    # Validate bounds
    if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
        return
    
    self._move_platform_cursor(row, col)

def _set_platform_cursor_visibility(self, visible: bool):
    """Set cursor visibility in platform (platform-specific)."""
    pass

def _move_platform_cursor(self, row: int, col: int):
    """Move cursor in platform (platform-specific)."""
    pass
```

## Abstract Methods Reference

Here's a complete list of methods you must implement:

### Required Methods

1. `initialize() -> None` - Initialize backend
2. `shutdown() -> None` - Clean up resources
3. `get_dimensions() -> Tuple[int, int]` - Get window size
4. `clear() -> None` - Clear entire window
5. `clear_region(row, col, height, width) -> None` - Clear region
6. `draw_text(row, col, text, color_pair, attributes) -> None` - Draw text
7. `draw_hline(row, col, char, length, color_pair) -> None` - Draw horizontal line
8. `draw_vline(row, col, char, length, color_pair) -> None` - Draw vertical line
9. `draw_rect(row, col, height, width, color_pair, filled) -> None` - Draw rectangle
10. `refresh() -> None` - Refresh entire window
11. `refresh_region(row, col, height, width) -> None` - Refresh region
12. `init_color_pair(pair_id, fg_color, bg_color) -> None` - Initialize color pair
13. `get_input(timeout_ms) -> Optional[KeyEvent]` - Get input event
14. `set_cursor_visibility(visible) -> None` - Set cursor visibility
15. `move_cursor(row, col) -> None` - Move cursor

## Testing Your Backend

### Unit Tests

Create unit tests for your backend:

```python
# ttk/test/test_my_backend.py

import pytest
from ttk.backends.my_backend import MyBackend
from ttk import KeyCode, TextAttribute

def test_initialization():
    """Test backend initialization."""
    backend = MyBackend()
    backend.initialize()
    
    try:
        # Verify dimensions are positive
        rows, cols = backend.get_dimensions()
        assert rows > 0
        assert cols > 0
    finally:
        backend.shutdown()

def test_drawing_operations():
    """Test drawing operations don't crash."""
    backend = MyBackend()
    backend.initialize()
    
    try:
        # Test text drawing
        backend.draw_text(0, 0, "Hello")
        
        # Test line drawing
        backend.draw_hline(1, 0, '-', 10)
        backend.draw_vline(0, 5, '|', 5)
        
        # Test rectangle drawing
        backend.draw_rect(2, 2, 5, 10, filled=False)
        backend.draw_rect(8, 2, 5, 10, filled=True)
        
        # Test refresh
        backend.refresh()
    finally:
        backend.shutdown()

def test_color_pairs():
    """Test color pair initialization."""
    backend = MyBackend()
    backend.initialize()
    
    try:
        # Initialize color pairs
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 255))
        backend.init_color_pair(2, (255, 255, 0), (0, 0, 0))
        
        # Use color pairs
        backend.draw_text(0, 0, "White on blue", color_pair=1)
        backend.draw_text(1, 0, "Yellow on black", color_pair=2)
        backend.refresh()
    finally:
        backend.shutdown()

def test_out_of_bounds():
    """Test out-of-bounds drawing doesn't crash."""
    backend = MyBackend()
    backend.initialize()
    
    try:
        rows, cols = backend.get_dimensions()
        
        # Draw outside bounds (should not crash)
        backend.draw_text(rows + 10, cols + 10, "Out of bounds")
        backend.draw_text(-5, -5, "Negative coords")
        backend.refresh()
    finally:
        backend.shutdown()
```

### Integration Tests

Test your backend with a real application:

```python
# ttk/test/test_my_backend_integration.py

from ttk.backends.my_backend import MyBackend
from ttk import KeyCode, TextAttribute

def test_simple_application():
    """Test a simple application using the backend."""
    backend = MyBackend()
    backend.initialize()
    
    try:
        # Initialize colors
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 128))
        
        # Draw UI
        backend.clear()
        backend.draw_text(0, 0, "Test Application", color_pair=1,
                         attributes=TextAttribute.BOLD)
        backend.draw_rect(2, 2, 10, 30, filled=False)
        backend.draw_text(3, 3, "Press any key...")
        backend.refresh()
        
        # Test input (with timeout to avoid blocking)
        event = backend.get_input(timeout_ms=100)
        # Event may be None if no input within timeout
        
    finally:
        backend.shutdown()
```

## Best Practices

### 1. Validate Parameters

Always validate parameters before using them:

```python
def draw_text(self, row: int, col: int, text: str,
              color_pair: int = 0, attributes: int = 0) -> None:
    # Validate bounds
    if row < 0 or row >= self.rows:
        return
    if col < 0 or col >= self.cols:
        return
    
    # Validate color pair
    if color_pair < 0 or color_pair > 255:
        raise ValueError(f"Invalid color pair: {color_pair}")
    
    # Continue with drawing...
```

### 2. Handle Errors Gracefully

Don't let platform errors crash the application:

```python
def _render_region(self, row: int, col: int, height: int, width: int):
    try:
        # Platform-specific rendering
        self._platform_render(row, col, height, width)
    except PlatformError as e:
        # Log error but don't crash
        print(f"Warning: Rendering error: {e}")
```

### 3. Clean Up Resources

Always clean up in `shutdown()`, even if errors occur:

```python
def shutdown(self) -> None:
    try:
        if self.window:
            self._close_window()
    except Exception as e:
        print(f"Warning: Error closing window: {e}")
    finally:
        self.window = None
        self.initialized = False
```

### 4. Document Platform Requirements

Document what platforms your backend supports:

```python
class MyBackend(Renderer):
    """
    My custom rendering backend.
    
    Platform Support:
        - Linux (X11)
        - macOS (Cocoa)
        - Windows (Win32)
    
    Requirements:
        - Python 3.8+
        - platform-specific-library >= 1.0
    
    Example:
        >>> backend = MyBackend()
        >>> backend.initialize()
        >>> backend.draw_text(0, 0, "Hello")
        >>> backend.refresh()
        >>> backend.shutdown()
    """
```

### 5. Optimize Performance

- Batch drawing operations when possible
- Use partial updates (refresh_region) instead of full refreshes
- Cache frequently used resources
- Minimize platform API calls

### 6. Test on Target Platforms

Test your backend on all platforms it claims to support:
- Different operating systems
- Different screen sizes
- Different font configurations
- Different color depths

## Example: Minimal Backend

Here's a complete minimal backend implementation:

```python
# ttk/backends/minimal_backend.py

from ttk.renderer import Renderer
from ttk.input_event import KeyEvent, KeyCode, ModifierKey
from typing import Tuple, Optional

class MinimalBackend(Renderer):
    """Minimal backend that stores drawing commands without rendering."""
    
    def __init__(self, rows: int = 24, cols: int = 80):
        self.rows = rows
        self.cols = cols
        self.grid = []
        self.color_pairs = {}
        self.commands = []  # Store all commands for testing
    
    def initialize(self) -> None:
        # Create empty grid
        self.grid = [
            [(' ', 0, 0) for _ in range(self.cols)]
            for _ in range(self.rows)
        ]
        self.init_color_pair(0, (255, 255, 255), (0, 0, 0))
    
    def shutdown(self) -> None:
        self.grid = []
        self.color_pairs.clear()
        self.commands.clear()
    
    def get_dimensions(self) -> Tuple[int, int]:
        return (self.rows, self.cols)
    
    def clear(self) -> None:
        self.commands.append(('clear',))
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col] = (' ', 0, 0)
    
    def clear_region(self, row: int, col: int, height: int, width: int) -> None:
        self.commands.append(('clear_region', row, col, height, width))
        for r in range(row, min(row + height, self.rows)):
            for c in range(col, min(col + width, self.cols)):
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    self.grid[r][c] = (' ', 0, 0)
    
    def draw_text(self, row: int, col: int, text: str,
                  color_pair: int = 0, attributes: int = 0) -> None:
        self.commands.append(('draw_text', row, col, text, color_pair, attributes))
        if 0 <= row < self.rows:
            for i, char in enumerate(text):
                c = col + i
                if 0 <= c < self.cols:
                    self.grid[row][c] = (char, color_pair, attributes)
    
    def draw_hline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        self.commands.append(('draw_hline', row, col, char, length, color_pair))
        self.draw_text(row, col, char[0] * length, color_pair)
    
    def draw_vline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        self.commands.append(('draw_vline', row, col, char, length, color_pair))
        for i in range(length):
            if row + i < self.rows:
                self.draw_text(row + i, col, char[0], color_pair)
    
    def draw_rect(self, row: int, col: int, height: int, width: int,
                  color_pair: int = 0, filled: bool = False) -> None:
        self.commands.append(('draw_rect', row, col, height, width, color_pair, filled))
        if filled:
            for r in range(row, min(row + height, self.rows)):
                self.draw_text(r, col, ' ' * width, color_pair)
        else:
            self.draw_hline(row, col, '-', width, color_pair)
            self.draw_hline(row + height - 1, col, '-', width, color_pair)
            self.draw_vline(row, col, '|', height, color_pair)
            self.draw_vline(row, col + width - 1, '|', height, color_pair)
    
    def refresh(self) -> None:
        self.commands.append(('refresh',))
    
    def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
        self.commands.append(('refresh_region', row, col, height, width))
    
    def init_color_pair(self, pair_id: int, fg_color: Tuple[int, int, int],
                       bg_color: Tuple[int, int, int]) -> None:
        if pair_id < 0 or pair_id > 255:
            raise ValueError(f"Color pair ID must be 0-255, got {pair_id}")
        self.commands.append(('init_color_pair', pair_id, fg_color, bg_color))
        self.color_pairs[pair_id] = (fg_color, bg_color)
    
    def get_input(self, timeout_ms: int = -1) -> Optional[KeyEvent]:
        # Return None (no input available)
        return None
    
    def set_cursor_visibility(self, visible: bool) -> None:
        self.commands.append(('set_cursor_visibility', visible))
    
    def move_cursor(self, row: int, col: int) -> None:
        self.commands.append(('move_cursor', row, col))
```

This minimal backend can be used for testing without requiring a real display.

## Next Steps

1. Implement your backend following this guide
2. Write comprehensive unit tests
3. Test with real applications
4. Document platform-specific requirements
5. Submit your backend to the TTK project (if open source)

## Example Backends

TTK includes several backend implementations you can study:

### CursesBackend (`ttk/backends/curses_backend.py`)
- Terminal-based rendering using Python's curses library
- Works on all Unix-like systems
- Good example of handling terminal-specific features

### CoreGraphicsBackend (`ttk/backends/coregraphics_backend.py`)
- Native macOS rendering using CoreGraphics/Quartz 2D
- Simple implementation (~300 lines)
- Excellent example of native platform integration
- Shows how to use NSAttributedString for text rendering
- Demonstrates coordinate system transformation

### CoreGraphicsBackend (`ttk/backends/coregraphics_backend.py`)
- Native macOS rendering using Apple's CoreGraphics framework
- Moderate complexity implementation (~800+ lines)
- Shows native text rendering and window management
- Good example of shader-based rendering

## Resources

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [User Guide](USER_GUIDE.md) - Usage examples and patterns
- Existing backends in `ttk/backends/` - Reference implementations
- Demo applications in `ttk/demo/` - Integration examples
