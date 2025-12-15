# Design Document

## Overview

This design document describes the architecture for a generic, reusable rendering library that supports multiple backends. The library, named **TTK (TUI Toolkit / Traditional app Toolkit)**, provides an abstract rendering API that allows character-grid-based applications to run on different platforms without modification. The initial implementation includes two backends: a curses backend for terminal applications and a Metal backend for native macOS desktop applications.

TTK is designed as a standalone library independent of TFM, making it reusable for any character-grid-based application. The library focuses on character-grid-based rendering with monospace fonts, supporting text, rectangles, lines, and future image rendering, providing a simple yet powerful abstraction over platform-specific rendering systems.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│              (TFM or other applications)                 │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ Uses abstract API
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  TTK Abstract API                        │
│  (Renderer, KeyEvent, ColorPair, WindowInfo, etc.)   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ Implements
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐         ┌────────▼────────┐
│ Curses Backend │         │  Metal Backend  │
│   (Terminal)   │         │    (macOS)      │
└────────────────┘         └─────────────────┘
```

### Component Layers

1. **Abstract API Layer**: Defines interfaces for rendering, input, and window management
2. **Backend Implementation Layer**: Provides platform-specific implementations
3. **Application Layer**: Uses the abstract API without backend knowledge

### Design Principles

1. **Backend Agnosticism**: Applications use only abstract interfaces
2. **Minimal Dependencies**: Core library has minimal external dependencies
3. **Performance**: Efficient rendering with support for partial updates
4. **Extensibility**: Designed to support future features like image rendering
5. **Simplicity**: Focus on monospace character grids for clarity

## Components and Interfaces

### 1. Renderer (Abstract Base Class)

The `Renderer` class is the main interface for all rendering operations.

```python
from abc import ABC, abstractmethod
from typing import Tuple, Optional, List
from enum import IntEnum

class TextAttribute(IntEnum):
    """Text rendering attributes."""
    NORMAL = 0
    BOLD = 1
    UNDERLINE = 2
    REVERSE = 4
    # Attributes can be combined with bitwise OR

class Renderer(ABC):
    """Abstract base class for text grid rendering backends."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the rendering backend and create the window."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Clean up resources and close the window."""
        pass
    
    @abstractmethod
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get window dimensions in character cells.
        
        Returns:
            Tuple of (rows, columns) representing the character grid size.
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the entire window."""
        pass
    
    @abstractmethod
    def clear_region(self, row: int, col: int, height: int, width: int) -> None:
        """
        Clear a rectangular region.
        
        Args:
            row: Starting row (0-based)
            col: Starting column (0-based)
            height: Height in character rows
            width: Width in character columns
        """
        pass
    
    @abstractmethod
    def draw_text(self, row: int, col: int, text: str, 
                  color_pair: int = 0, attributes: int = 0) -> None:
        """
        Draw text at the specified position.
        
        Args:
            row: Row position (0-based, 0 is top)
            col: Column position (0-based, 0 is left)
            text: Text string to draw
            color_pair: Color pair index (0-255)
            attributes: Bitwise OR of TextAttribute values
        """
        pass
    
    @abstractmethod
    def draw_hline(self, row: int, col: int, char: str, 
                   length: int, color_pair: int = 0) -> None:
        """
        Draw a horizontal line.
        
        Args:
            row: Row position
            col: Starting column position
            char: Character to use for the line
            length: Length in characters
            color_pair: Color pair index
        """
        pass
    
    @abstractmethod
    def draw_vline(self, row: int, col: int, char: str, 
                   length: int, color_pair: int = 0) -> None:
        """
        Draw a vertical line.
        
        Args:
            row: Starting row position
            col: Column position
            char: Character to use for the line
            length: Length in characters
            color_pair: Color pair index
        """
        pass
    
    @abstractmethod
    def draw_rect(self, row: int, col: int, height: int, width: int,
                  color_pair: int = 0, filled: bool = False) -> None:
        """
        Draw a rectangle.
        
        Args:
            row: Top-left row position
            col: Top-left column position
            height: Height in character rows
            width: Width in character columns
            color_pair: Color pair index
            filled: If True, fill the rectangle; if False, draw outline only
        """
        pass
    
    @abstractmethod
    def refresh(self) -> None:
        """Refresh the entire window to display all pending changes."""
        pass
    
    @abstractmethod
    def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
        """
        Refresh a specific region of the window.
        
        Args:
            row: Starting row
            col: Starting column
            height: Height in rows
            width: Width in columns
        """
        pass
    
    @abstractmethod
    def init_color_pair(self, pair_id: int, fg_color: Tuple[int, int, int],
                       bg_color: Tuple[int, int, int]) -> None:
        """
        Initialize a color pair with RGB values.
        
        Args:
            pair_id: Color pair index (1-255, 0 is reserved for default)
            fg_color: Foreground color as (R, G, B) tuple (0-255 each)
            bg_color: Background color as (R, G, B) tuple (0-255 each)
        """
        pass
    
    @abstractmethod
    def get_input(self, timeout_ms: int = -1) -> Optional['KeyEvent']:
        """
        Get the next input event.
        
        Args:
            timeout_ms: Timeout in milliseconds. -1 for blocking, 0 for non-blocking.
        
        Returns:
            KeyEvent if input is available, None if timeout expires.
        """
        pass
    
    @abstractmethod
    def set_cursor_visibility(self, visible: bool) -> None:
        """
        Set cursor visibility.
        
        Args:
            visible: True to show cursor, False to hide it.
        """
        pass
    
    @abstractmethod
    def move_cursor(self, row: int, col: int) -> None:
        """
        Move the cursor to the specified position.
        
        Args:
            row: Row position
            col: Column position
        """
        pass
```

### 2. KeyEvent

Represents user input events with a unified interface across backends.

```python
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional

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

class ModifierKey(IntEnum):
    """Modifier key flags (can be combined with bitwise OR)."""
    NONE = 0
    SHIFT = 1
    CONTROL = 2
    ALT = 4
    COMMAND = 8  # macOS Command key

@dataclass
class KeyEvent:
    """Represents a user input event."""
    key_code: int  # KeyCode value or Unicode code point
    modifiers: int  # Bitwise OR of ModifierKey values
    char: Optional[str] = None  # Character for printable keys
    mouse_row: Optional[int] = None  # For mouse events
    mouse_col: Optional[int] = None  # For mouse events
    mouse_button: Optional[int] = None  # 1=left, 2=middle, 3=right
    
    def is_printable(self) -> bool:
        """Check if this is a printable character."""
        return self.char is not None and len(self.char) == 1
    
    def is_special_key(self) -> bool:
        """Check if this is a special key (arrow, function, etc.)."""
        return self.key_code >= 1000
    
    def has_modifier(self, modifier: ModifierKey) -> bool:
        """Check if a specific modifier key is pressed."""
        return (self.modifiers & modifier) != 0
```

### 3. CursesBackend

Implementation of the Renderer interface using Python's curses library.

```python
import curses
from typing import Tuple, Optional

class CursesBackend(Renderer):
    """Curses-based rendering backend for terminal applications."""
    
    def __init__(self):
        self.stdscr = None
        self.color_pairs_initialized = set()
    
    def initialize(self) -> None:
        """Initialize curses and set up the terminal."""
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        curses.curs_set(0)  # Hide cursor by default
        
        # Initialize default color pair (0)
        curses.init_pair(0, -1, -1)
    
    def shutdown(self) -> None:
        """Clean up curses and restore terminal."""
        if self.stdscr:
            self.stdscr.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Get terminal dimensions."""
        height, width = self.stdscr.getmaxyx()
        return (height, width)
    
    def clear(self) -> None:
        """Clear the terminal."""
        self.stdscr.clear()
    
    def clear_region(self, row: int, col: int, height: int, width: int) -> None:
        """Clear a rectangular region."""
        for r in range(row, min(row + height, self.get_dimensions()[0])):
            try:
                self.stdscr.move(r, col)
                self.stdscr.clrtoeol()
            except curses.error:
                pass
    
    def draw_text(self, row: int, col: int, text: str,
                  color_pair: int = 0, attributes: int = 0) -> None:
        """Draw text using curses."""
        try:
            attr = curses.color_pair(color_pair)
            if attributes & TextAttribute.BOLD:
                attr |= curses.A_BOLD
            if attributes & TextAttribute.UNDERLINE:
                attr |= curses.A_UNDERLINE
            if attributes & TextAttribute.REVERSE:
                attr |= curses.A_REVERSE
            
            self.stdscr.addstr(row, col, text, attr)
        except curses.error:
            pass  # Ignore out-of-bounds errors
    
    def draw_hline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        """Draw horizontal line."""
        try:
            self.stdscr.hline(row, col, ord(char[0]), length,
                            curses.color_pair(color_pair))
        except curses.error:
            pass
    
    def draw_vline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        """Draw vertical line."""
        try:
            self.stdscr.vline(row, col, ord(char[0]), length,
                            curses.color_pair(color_pair))
        except curses.error:
            pass
    
    def draw_rect(self, row: int, col: int, height: int, width: int,
                  color_pair: int = 0, filled: bool = False) -> None:
        """Draw rectangle."""
        if filled:
            for r in range(row, row + height):
                self.draw_text(r, col, ' ' * width, color_pair)
        else:
            # Draw outline
            self.draw_hline(row, col, '-', width, color_pair)
            self.draw_hline(row + height - 1, col, '-', width, color_pair)
            self.draw_vline(row, col, '|', height, color_pair)
            self.draw_vline(row, col + width - 1, '|', height, color_pair)
    
    def refresh(self) -> None:
        """Refresh the terminal."""
        self.stdscr.refresh()
    
    def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
        """Refresh a region (curses refreshes entire window)."""
        self.stdscr.refresh()
    
    def init_color_pair(self, pair_id: int, fg_color: Tuple[int, int, int],
                       bg_color: Tuple[int, int, int]) -> None:
        """Initialize color pair."""
        if pair_id in self.color_pairs_initialized:
            return
        
        # Convert RGB to curses color (simplified - use closest terminal color)
        fg = self._rgb_to_curses_color(fg_color)
        bg = self._rgb_to_curses_color(bg_color)
        
        curses.init_pair(pair_id, fg, bg)
        self.color_pairs_initialized.add(pair_id)
    
    def _rgb_to_curses_color(self, rgb: Tuple[int, int, int]) -> int:
        """Convert RGB to curses color code."""
        # Simplified mapping to 8 basic colors
        r, g, b = rgb
        if r < 128 and g < 128 and b < 128:
            return curses.COLOR_BLACK
        elif r > 200 and g > 200 and b > 200:
            return curses.COLOR_WHITE
        elif r > g and r > b:
            return curses.COLOR_RED
        elif g > r and g > b:
            return curses.COLOR_GREEN
        elif b > r and b > g:
            return curses.COLOR_BLUE
        elif r > 128 and g > 128:
            return curses.COLOR_YELLOW
        elif r > 128 and b > 128:
            return curses.COLOR_MAGENTA
        elif g > 128 and b > 128:
            return curses.COLOR_CYAN
        return curses.COLOR_WHITE
    
    def get_input(self, timeout_ms: int = -1) -> Optional[KeyEvent]:
        """Get input from terminal."""
        if timeout_ms >= 0:
            self.stdscr.timeout(timeout_ms)
        else:
            self.stdscr.timeout(-1)
        
        try:
            key = self.stdscr.getch()
            if key == -1:
                return None
            
            return self._translate_curses_key(key)
        except curses.error:
            return None
    
    def _translate_curses_key(self, key: int) -> KeyEvent:
        """Translate curses key code to KeyEvent."""
        modifiers = ModifierKey.NONE
        
        # Map curses keys to KeyCode
        key_map = {
            curses.KEY_UP: KeyCode.UP,
            curses.KEY_DOWN: KeyCode.DOWN,
            curses.KEY_LEFT: KeyCode.LEFT,
            curses.KEY_RIGHT: KeyCode.RIGHT,
            curses.KEY_HOME: KeyCode.HOME,
            curses.KEY_END: KeyCode.END,
            curses.KEY_PPAGE: KeyCode.PAGE_UP,
            curses.KEY_NPAGE: KeyCode.PAGE_DOWN,
            curses.KEY_DC: KeyCode.DELETE,
            curses.KEY_IC: KeyCode.INSERT,
            curses.KEY_BACKSPACE: KeyCode.BACKSPACE,
            curses.KEY_RESIZE: KeyCode.RESIZE,
        }
        
        # Function keys
        for i in range(12):
            key_map[curses.KEY_F1 + i] = KeyCode.F1 + i
        
        if key in key_map:
            return KeyEvent(key_code=key_map[key], modifiers=modifiers)
        
        # Printable character
        if 32 <= key <= 126:
            return KeyEvent(key_code=key, modifiers=modifiers, char=chr(key))
        
        # Special characters
        if key == 10 or key == 13:
            return KeyEvent(key_code=KeyCode.ENTER, modifiers=modifiers)
        elif key == 27:
            return KeyEvent(key_code=KeyCode.ESCAPE, modifiers=modifiers)
        elif key == 9:
            return KeyEvent(key_code=KeyCode.TAB, modifiers=modifiers)
        
        # Default
        return KeyEvent(key_code=key, modifiers=modifiers)
    
    def set_cursor_visibility(self, visible: bool) -> None:
        """Set cursor visibility."""
        curses.curs_set(1 if visible else 0)
    
    def move_cursor(self, row: int, col: int) -> None:
        """Move cursor position."""
        try:
            self.stdscr.move(row, col)
        except curses.error:
            pass
```

### 4. MetalBackend

Implementation using Apple's Metal framework for native macOS rendering.

```python
# Note: This is a conceptual design. Actual implementation would use
# PyObjC or similar to interface with Metal framework.

class MetalBackend(Renderer):
    """Metal-based rendering backend for macOS desktop applications."""
    
    def __init__(self, window_title: str = "TextGrid Application",
                 font_name: str = "Menlo", font_size: int = 14):
        """
        Initialize Metal backend.
        
        Args:
            window_title: Title for the native window
            font_name: Monospace font name (must be monospace)
            font_size: Font size in points
        """
        self.window_title = window_title
        self.font_name = font_name
        self.font_size = font_size
        
        # Will be initialized in initialize()
        self.window = None
        self.metal_device = None
        self.command_queue = None
        self.render_pipeline = None
        self.char_width = 0
        self.char_height = 0
        self.rows = 0
        self.cols = 0
        
        # Character grid buffer
        self.grid = []
        self.color_pairs = {}
    
    def initialize(self) -> None:
        """Initialize Metal and create native window."""
        # Create Metal device
        self.metal_device = self._create_metal_device()
        self.command_queue = self.metal_device.newCommandQueue()
        
        # Load and compile shaders
        self.render_pipeline = self._create_render_pipeline()
        
        # Create native window
        self.window = self._create_native_window()
        
        # Calculate character dimensions
        self._calculate_char_dimensions()
        
        # Initialize character grid
        self._initialize_grid()
    
    def _create_metal_device(self):
        """Create Metal device (platform-specific)."""
        # Use PyObjC to create MTLDevice
        pass
    
    def _create_render_pipeline(self):
        """Create Metal rendering pipeline with text shaders."""
        # Load vertex and fragment shaders for text rendering
        # Shaders handle character positioning and coloring
        pass
    
    def _create_native_window(self):
        """Create native macOS window."""
        # Use PyObjC to create NSWindow with Metal view
        pass
    
    def _calculate_char_dimensions(self):
        """Calculate character cell dimensions for the font."""
        # Measure monospace font to get exact character width/height
        # This ensures perfect grid alignment
        pass
    
    def _initialize_grid(self):
        """Initialize the character grid buffer."""
        self.rows = self.window.height // self.char_height
        self.cols = self.window.width // self.char_width
        
        # Create grid: list of rows, each row is list of (char, color_pair, attrs)
        self.grid = [
            [('' ' ', 0, 0) for _ in range(self.cols)]
            for _ in range(self.rows)
        ]
    
    def shutdown(self) -> None:
        """Clean up Metal resources and close window."""
        if self.window:
            self.window.close()
        # Release Metal resources
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Get window dimensions in character cells."""
        return (self.rows, self.cols)
    
    def clear(self) -> None:
        """Clear the entire grid."""
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col] = (' ', 0, 0)
    
    def clear_region(self, row: int, col: int, height: int, width: int) -> None:
        """Clear a rectangular region."""
        for r in range(row, min(row + height, self.rows)):
            for c in range(col, min(col + width, self.cols)):
                self.grid[r][c] = (' ', 0, 0)
    
    def draw_text(self, row: int, col: int, text: str,
                  color_pair: int = 0, attributes: int = 0) -> None:
        """Draw text to the grid buffer."""
        if row < 0 or row >= self.rows:
            return
        
        for i, char in enumerate(text):
            c = col + i
            if c >= self.cols:
                break
            self.grid[row][c] = (char, color_pair, attributes)
    
    def draw_hline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        """Draw horizontal line."""
        self.draw_text(row, col, char[0] * length, color_pair)
    
    def draw_vline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        """Draw vertical line."""
        for i in range(length):
            if row + i < self.rows:
                self.grid[row + i][col] = (char[0], color_pair, 0)
    
    def draw_rect(self, row: int, col: int, height: int, width: int,
                  color_pair: int = 0, filled: bool = False) -> None:
        """Draw rectangle."""
        if filled:
            for r in range(row, min(row + height, self.rows)):
                self.draw_text(r, col, ' ' * width, color_pair)
        else:
            self.draw_hline(row, col, '-', width, color_pair)
            self.draw_hline(row + height - 1, col, '-', width, color_pair)
            self.draw_vline(row, col, '|', height, color_pair)
            self.draw_vline(row, col + width - 1, '|', height, color_pair)
    
    def refresh(self) -> None:
        """Render the entire grid using Metal."""
        self._render_grid()
    
    def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
        """Render a specific region (Metal can optimize this)."""
        self._render_grid_region(row, col, height, width)
    
    def _render_grid(self):
        """Render the character grid using Metal."""
        # Create Metal command buffer
        command_buffer = self.command_queue.commandBuffer()
        
        # Create render pass
        render_pass = self._create_render_pass(command_buffer)
        
        # For each character in grid, create a quad with texture
        for row in range(self.rows):
            for col in range(self.cols):
                char, color_pair, attrs = self.grid[row][col]
                if char != ' ':
                    self._render_character(render_pass, row, col, char,
                                         color_pair, attrs)
        
        # Commit and present
        render_pass.endEncoding()
        command_buffer.present(self.window.drawable)
        command_buffer.commit()
    
    def _render_grid_region(self, row: int, col: int, height: int, width: int):
        """Optimized rendering for a specific region."""
        # Similar to _render_grid but only for specified region
        pass
    
    def _render_character(self, render_pass, row: int, col: int,
                         char: str, color_pair: int, attrs: int):
        """Render a single character using Metal."""
        # Calculate screen position
        x = col * self.char_width
        y = row * self.char_height
        
        # Get colors from color pair
        fg_color, bg_color = self.color_pairs.get(color_pair, ((255, 255, 255), (0, 0, 0)))
        
        # Apply attributes (bold, underline, etc.)
        # Render background quad
        # Render character glyph with foreground color
        pass
    
    def init_color_pair(self, pair_id: int, fg_color: Tuple[int, int, int],
                       bg_color: Tuple[int, int, int]) -> None:
        """Initialize color pair."""
        self.color_pairs[pair_id] = (fg_color, bg_color)
    
    def get_input(self, timeout_ms: int = -1) -> Optional[KeyEvent]:
        """Get input from macOS event system."""
        # Poll macOS event queue
        event = self._poll_macos_event(timeout_ms)
        if event:
            return self._translate_macos_event(event)
        return None
    
    def _poll_macos_event(self, timeout_ms: int):
        """Poll macOS event queue."""
        # Use NSEvent polling
        pass
    
    def _translate_macos_event(self, event) -> KeyEvent:
        """Translate macOS event to KeyEvent."""
        # Map NSEvent to KeyEvent
        # Handle keyboard events, mouse events, window events
        pass
    
    def set_cursor_visibility(self, visible: bool) -> None:
        """Set cursor visibility."""
        # Control cursor rendering in Metal
        pass
    
    def move_cursor(self, row: int, col: int) -> None:
        """Move cursor position."""
        # Update cursor position for rendering
        pass
```

## Data Models

### Color Pair Structure

```python
@dataclass
class ColorPair:
    """Represents a foreground/background color combination."""
    pair_id: int
    foreground: Tuple[int, int, int]  # RGB (0-255)
    background: Tuple[int, int, int]  # RGB (0-255)
```

### Window Information

```python
@dataclass
class WindowInfo:
    """Information about the rendering window."""
    rows: int  # Height in character cells
    cols: int  # Width in character cells
    char_width_pixels: int  # Width of one character in pixels (Metal only)
    char_height_pixels: int  # Height of one character in pixels (Metal only)
    backend_name: str  # "curses" or "metal"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified the following testable properties. Some properties are redundant or can be combined:

**Redundancies identified:**
- Properties 2.2, 7.3, and 9.1-9.4 all test attribute handling - these can be combined into comprehensive attribute properties
- Properties 4.1-4.6 all test drawing operations - these can be grouped by operation type
- Properties 5.1-5.4 all test input handling - these can be grouped by input type
- Properties 13.1-13.3 all test serialization - these form a single round-trip property

**Consolidated property list:**
1. Drawing operations complete without error for valid parameters
2. Text attributes are handled correctly
3. Input events are translated correctly
4. Backend equivalence for colors and attributes
5. Coordinate system behaves correctly
6. Serialization round-trip preserves commands
7. Error handling for invalid inputs

### Correctness Properties

Property 1: Drawing operations robustness
*For any* valid drawing parameters (position, size, color, text, attributes), all drawing operations (draw_text, draw_rect, draw_hline, draw_vline, clear, clear_region) should complete without raising exceptions.
**Validates: Requirements 4.1, 4.2, 4.3, 4.5**

Property 2: Color pair initialization robustness
*For any* valid color pair ID (1-255) and RGB color values (0-255 for each component), init_color_pair should complete without raising exceptions.
**Validates: Requirements 4.4, 7.1**

Property 3: Refresh operations robustness
*For any* valid window state, both refresh() and refresh_region() with valid parameters should complete without raising exceptions.
**Validates: Requirements 4.6**

Property 4: Text attribute support
*For any* combination of text attributes (BOLD, UNDERLINE, REVERSE, or combinations via bitwise OR), draw_text should handle them without raising exceptions.
**Validates: Requirements 2.2, 7.3, 9.1, 9.2, 9.3, 9.4**

Property 5: Printable character input translation
*For any* printable character input event, get_input should return an KeyEvent with the correct character in the char field and a valid key_code.
**Validates: Requirements 5.1**

Property 6: Special key input translation
*For any* special key input (arrow keys, function keys, Enter, Escape, Backspace, Delete), get_input should return an KeyEvent with the correct KeyCode value.
**Validates: Requirements 5.2**

Property 7: Modifier key detection
*For any* key input with modifier keys pressed, get_input should return an KeyEvent with the correct modifier flags set.
**Validates: Requirements 5.3**

Property 8: Mouse input handling
*For any* mouse event, get_input should return an KeyEvent with valid mouse position (row, col) and button state.
**Validates: Requirements 5.4**

Property 9: Dimension query consistency
*For any* renderer state, get_dimensions() should return a tuple of two positive integers representing (rows, columns).
**Validates: Requirements 8.3**

Property 10: Command serialization round-trip
*For any* rendering command (draw_text, draw_rect, etc. with their parameters), serializing then parsing the command should reconstruct an equivalent command with the same parameters.
**Validates: Requirements 13.1, 13.2, 13.3**

Property 11: Pretty-print completeness
*For any* rendering command, pretty-printing should produce a non-empty string representation without raising exceptions.
**Validates: Requirements 13.4**

Property 12: Backend color equivalence
*For any* color pair and text attributes, rendering the same content with both curses and Metal backends should use equivalent color values (allowing for terminal color approximation in curses).
**Validates: Requirements 3.3**

Property 13: Backend input equivalence
*For any* input event type, both curses and Metal backends should translate platform-specific events to equivalent KeyEvent objects with the same key_code and modifiers.
**Validates: Requirements 2.3, 3.4**

## Error Handling

### Invalid Parameter Handling

The library should handle invalid parameters gracefully:

1. **Out-of-bounds coordinates**: Drawing operations with coordinates outside the window bounds should be clipped or ignored without crashing
2. **Invalid color pair IDs**: Using color pair IDs outside the valid range (0-255) should raise ValueError
3. **Invalid RGB values**: RGB values outside 0-255 range should raise ValueError
4. **Negative dimensions**: Negative width/height parameters should raise ValueError
5. **Invalid font names**: Metal backend should raise ValueError for non-monospace fonts

### Backend-Specific Error Handling

1. **Curses backend**: Handle curses.error exceptions gracefully, typically by ignoring out-of-bounds drawing
2. **Metal backend**: Handle Metal framework errors and provide meaningful error messages
3. **Initialization failures**: If backend initialization fails, raise a descriptive exception

### Resource Cleanup

Both backends must properly clean up resources in shutdown():
- Curses: Restore terminal state
- Metal: Release Metal resources and close window
- Ensure cleanup happens even if exceptions occur

## Testing Strategy

### Unit Testing

Unit tests will verify specific behaviors and edge cases:

1. **API completeness**: Verify all abstract methods are defined
2. **Parameter validation**: Test error handling for invalid parameters
3. **Coordinate system**: Verify (0,0) is top-left, dimensions are correct
4. **Color pair limits**: Test initialization of 256 color pairs
5. **Attribute combinations**: Test all combinations of text attributes
6. **Input timeout**: Test non-blocking input with timeout=0
7. **Window resize**: Test dimension updates after resize events
8. **Out-of-bounds drawing**: Test graceful handling of invalid coordinates
9. **Font validation**: Test Metal backend rejects proportional fonts
10. **ABC enforcement**: Test that incomplete backend implementations raise TypeError

### Property-Based Testing

Property-based tests will verify universal properties across many inputs:

**Testing Framework**: Use Python's `hypothesis` library for property-based testing.

**Property Test 1: Drawing operations robustness**
- Generate random valid drawing parameters
- Call all drawing operations
- Verify no exceptions are raised
- **Feature: desktop-app-mode, Property 1: Drawing operations robustness**
- **Validates: Requirements 4.1, 4.2, 4.3, 4.5**

**Property Test 2: Color pair initialization robustness**
- Generate random color pair IDs (1-255) and RGB values (0-255)
- Call init_color_pair
- Verify no exceptions are raised
- **Feature: desktop-app-mode, Property 2: Color pair initialization robustness**
- **Validates: Requirements 4.4, 7.1**

**Property Test 3: Refresh operations robustness**
- Generate random window states
- Call refresh() and refresh_region() with valid parameters
- Verify no exceptions are raised
- **Feature: desktop-app-mode, Property 3: Refresh operations robustness**
- **Validates: Requirements 4.6**

**Property Test 4: Text attribute support**
- Generate random combinations of text attributes
- Call draw_text with these attributes
- Verify no exceptions are raised
- **Feature: desktop-app-mode, Property 4: Text attribute support**
- **Validates: Requirements 2.2, 7.3, 9.1, 9.2, 9.3, 9.4**

**Property Test 5: Printable character input translation**
- Generate random printable characters
- Simulate input events
- Verify KeyEvent has correct char and key_code
- **Feature: desktop-app-mode, Property 5: Printable character input translation**
- **Validates: Requirements 5.1**

**Property Test 6: Special key input translation**
- Generate random special key events
- Verify KeyEvent has correct KeyCode
- **Feature: desktop-app-mode, Property 6: Special key input translation**
- **Validates: Requirements 5.2**

**Property Test 7: Modifier key detection**
- Generate random key events with random modifier combinations
- Verify KeyEvent has correct modifier flags
- **Feature: desktop-app-mode, Property 7: Modifier key detection**
- **Validates: Requirements 5.3**

**Property Test 8: Mouse input handling**
- Generate random mouse events
- Verify KeyEvent has valid mouse data
- **Feature: desktop-app-mode, Property 8: Mouse input handling**
- **Validates: Requirements 5.4**

**Property Test 9: Dimension query consistency**
- For any renderer state, verify get_dimensions() returns valid tuple
- **Feature: desktop-app-mode, Property 9: Dimension query consistency**
- **Validates: Requirements 8.3**

**Property Test 10: Command serialization round-trip**
- Generate random rendering commands
- Serialize, then parse
- Verify reconstructed command equals original
- **Feature: desktop-app-mode, Property 10: Command serialization round-trip**
- **Validates: Requirements 13.1, 13.2, 13.3**

**Property Test 11: Pretty-print completeness**
- Generate random rendering commands
- Pretty-print each command
- Verify non-empty string output
- **Feature: desktop-app-mode, Property 11: Pretty-print completeness**
- **Validates: Requirements 13.4**

**Property Test 12: Backend color equivalence**
- Generate random color pairs and attributes
- Render with both backends
- Verify equivalent color usage (accounting for terminal limitations)
- **Feature: desktop-app-mode, Property 12: Backend color equivalence**
- **Validates: Requirements 3.3**

**Property Test 13: Backend input equivalence**
- Generate random input events
- Translate with both backends
- Verify equivalent KeyEvent objects
- **Feature: desktop-app-mode, Property 13: Backend input equivalence**
- **Validates: Requirements 2.3, 3.4**

### Integration Testing

Integration tests will verify the complete system:

1. **Demo application**: Verify demo runs with both backends
2. **Backend switching**: Verify application can switch backends
3. **Cross-backend consistency**: Verify same application code works with both backends
4. **Performance**: Verify Metal backend achieves 60 FPS for typical operations

### Testing Configuration

- Run property-based tests with minimum 100 iterations per property
- Use hypothesis strategies to generate valid test data
- Mock platform-specific components (curses, Metal) for unit tests
- Use real backends for integration tests on appropriate platforms

## Implementation Notes

### Library Name and Structure

The library will be named **TTK (TUI Toolkit / Traditional app Toolkit)** to reflect its support for text, rectangles, lines, and future graphics primitives:

```
ttk/
├── __init__.py
├── renderer.py          # Abstract Renderer class
├── input_event.py       # KeyEvent, KeyCode, ModifierKey
├── backends/
│   ├── __init__.py
│   ├── curses_backend.py
│   └── metal_backend.py
├── serialization.py     # Command serialization/parsing
└── utils.py            # Utility functions
```

### Monospace Font Enforcement

The Metal backend will validate fonts at initialization:

```python
def _validate_font(self, font_name: str) -> None:
    """Validate that font is monospace."""
    # Use Core Text to check font metrics
    # Verify all characters have same width
    # Raise ValueError if proportional
```

### Future Image Support

The API reserves space for future image rendering:

```python
# Reserved for future use
def draw_image(self, row: int, col: int, image_data, 
               width: int, height: int) -> None:
    """Draw image at specified position (future feature)."""
    raise NotImplementedError("Image rendering not yet supported")
```

### Performance Considerations

1. **Metal backend**: Use GPU instancing for character rendering
2. **Curses backend**: Minimize curses calls by batching operations
3. **Partial updates**: Both backends support refresh_region for efficiency
4. **Double buffering**: Metal backend uses double buffering for smooth rendering

### Platform Detection

The library will provide a helper for backend selection:

```python
def get_recommended_backend() -> str:
    """Get recommended backend for current platform."""
    import platform
    if platform.system() == 'Darwin':
        return 'metal'
    return 'curses'
```

## Demo Application Design

The demo application will:

1. Accept `--backend` argument (curses or metal)
2. Display a test interface with:
   - Text in various colors and attributes
   - Rectangles (filled and outlined)
   - Horizontal and vertical lines
   - Input echo area showing pressed keys
3. Respond to keyboard input
4. Handle window resizing
5. Display performance metrics (FPS, render time)
6. Provide visual confirmation of backend functionality

Demo structure:
```
demo/
├── demo_ttk.py          # Main demo application
├── test_interface.py    # Test UI implementation
└── performance.py       # Performance monitoring
```

The demo will serve as both a verification tool and an example of library usage.
