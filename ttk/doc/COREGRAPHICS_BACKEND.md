# CoreGraphics Backend

The CoreGraphics backend enables TTK applications to run as native macOS desktop applications using Apple's CoreGraphics (Quartz 2D) framework.

## Overview

The CoreGraphics backend provides:
- **Native macOS text rendering** using NSAttributedString
- **High-quality font rendering** with automatic font fallback
- **Full Unicode and emoji support** without special handling
- **Simple implementation** (~300 lines of code)
- **Native window controls** (close, minimize, resize)
- **Full RGB color support** (256 color pairs)

## Platform Requirements

- **Operating System**: macOS 10.13 (High Sierra) or later
- **Python**: Python 3.8 or later
- **Dependencies**: PyObjC framework

## Installation

Install the PyObjC framework:

```bash
pip install pyobjc-framework-Cocoa
```

This is the only additional dependency needed for the CoreGraphics backend.

## Basic Usage

### Simple Example

```python
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk import KeyCode

# Create backend with default settings
renderer = CoreGraphicsBackend()
renderer.initialize()

try:
    # Set up event callback
    class SimpleCallback(EventCallback):
        def __init__(self):
            self.should_quit = False
        
        def on_key_event(self, event):
            if event.key_code == KeyCode.ESCAPE:
                self.should_quit = True
                return True
            return False
        
        def on_char_event(self, event):
            return False
        
        def should_close(self):
            return self.should_quit
    
    callback = SimpleCallback()
    renderer.set_event_callback(callback)
    
    # Draw text
    renderer.draw_text(0, 0, "Hello, macOS!")
    renderer.refresh()
    
    # Event loop
    while not callback.should_quit:
        renderer.run_event_loop_iteration(timeout_ms=16)

finally:
    renderer.shutdown()
```

### Custom Configuration

```python
from ttk.backends.coregraphics_backend import CoreGraphicsBackend

# Create backend with custom settings
renderer = CoreGraphicsBackend(
    window_title="My Application",
    font_name="Monaco",
    font_size=12
)
renderer.initialize()
```

## Configuration Options

### Window Title

Set the title displayed in the window's title bar:

```python
renderer = CoreGraphicsBackend(window_title="File Manager")
```

### Font Selection

Choose a monospace font and size:

```python
renderer = CoreGraphicsBackend(
    font_name="Menlo",  # Font name
    font_size=14        # Font size in points
)
```

**Supported Fonts** (monospace only):
- Menlo (default)
- Monaco
- Courier New
- SF Mono
- Any other monospace font installed on the system

**Note**: Proportional fonts (like Helvetica or Arial) will be rejected with a clear error message.

## Features

### Native Text Rendering

The CoreGraphics backend uses NSAttributedString for text rendering, providing:
- Native macOS text quality
- Automatic font smoothing
- Proper character spacing
- Subpixel rendering

### Unicode and Emoji Support

Full Unicode support is built-in:

```python
# Unicode characters work automatically
renderer.draw_text(0, 0, "Hello 世界 🌍")
renderer.draw_text(1, 0, "Emoji: 😀 🎉 ✨")
renderer.draw_text(2, 0, "Arabic: مرحبا")
renderer.draw_text(3, 0, "Thai: สวัสดี")
```

The backend automatically:
- Handles complex scripts (Arabic, Thai, etc.)
- Renders emoji using the system's native emoji font
- Falls back to alternative fonts for missing glyphs

### Color Support

Full RGB color support with 256 color pairs:

```python
# Initialize color pairs with RGB values (0-255)
renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))    # White on blue
renderer.init_color_pair(2, (255, 255, 0), (0, 0, 0))        # Yellow on black
renderer.init_color_pair(3, (0, 255, 0), (0, 64, 0))         # Green on dark green

# Use color pairs when drawing
renderer.draw_text(0, 0, "White on blue", color_pair=1)
renderer.draw_text(1, 0, "Yellow on black", color_pair=2)
renderer.draw_text(2, 0, "Green on dark green", color_pair=3)
```

### Text Attributes

All standard text attributes are supported:

```python
from ttk import TextAttribute

# Bold text
renderer.draw_text(0, 0, "Bold", attributes=TextAttribute.BOLD)

# Underlined text
renderer.draw_text(1, 0, "Underline", attributes=TextAttribute.UNDERLINE)

# Reverse video
renderer.draw_text(2, 0, "Reverse", attributes=TextAttribute.REVERSE)

# Combined attributes
renderer.draw_text(3, 0, "Bold + Underline",
                   attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE)
```

### Window Management

The backend creates a native macOS window with standard controls:
- **Close button**: Closes the window
- **Minimize button**: Minimizes to dock
- **Resize button**: Allows window resizing

Window resize events are reported through the input system:

```python
from ttk import KeyCode

event = renderer.get_input()
if event.key_code == KeyCode.RESIZE:
    rows, cols = renderer.get_dimensions()
    print(f"Window resized to {rows}x{cols}")
    # Redraw UI with new dimensions
```

### Keyboard Input

Full keyboard support including:
- All printable characters
- Special keys (arrows, function keys, etc.)
- Modifier keys (Shift, Control, Alt, Command)

```python
from ttk import KeyCode, ModifierKey

event = renderer.get_input()

# Check for specific keys
if event.key_code == KeyCode.ENTER:
    print("Enter pressed")
elif event.key_code == KeyCode.UP:
    print("Up arrow pressed")

# Check for modifiers
if event.has_modifier(ModifierKey.COMMAND):
    print("Command key held")
if event.char == 'c' and event.has_modifier(ModifierKey.CONTROL):
    print("Ctrl+C pressed")
```

## Performance

The CoreGraphics backend is optimized for typical TTK use cases:

- **Full screen refresh**: < 10ms for 80x24 grid
- **Partial updates**: Supported via `refresh_region()`
- **Empty cell optimization**: Skips rendering space characters with default colors

For most text-based applications, performance is excellent without any special optimization.

## Comparison with Other Backends

### CoreGraphics vs Curses

| Feature | CoreGraphics | Curses |
|---------|-------------|--------|
| Platform | macOS only | Unix-like systems |
| Window Type | Native desktop | Terminal |
| Text Quality | Native macOS | Terminal-dependent |
| Colors | Full RGB | Approximated |
| Unicode | Full support | Limited |
| Emoji | Native rendering | Limited/none |
| Implementation | ~300 lines | ~400 lines |

### CoreGraphics vs Metal

| Feature | CoreGraphics | Metal |
|---------|-------------|-------|
| Platform | macOS only | macOS only |
| Rendering | CPU (CoreGraphics) | GPU (Metal) |
| Text Quality | Native (NSAttributedString) | Shader-based |
| Implementation | ~300 lines | ~1000+ lines |
| Complexity | Simple | Complex |
| Performance | Excellent for text | Optimized for 60 FPS |
| Best For | Most applications | GPU-intensive apps |

**When to use CoreGraphics:**
- You want native macOS text rendering quality
- You prefer a simple, maintainable implementation
- Your application is primarily text-based
- You don't need GPU acceleration

**When to use Metal:**
- You need GPU acceleration
- You want 60 FPS rendering
- You're building a graphics-intensive application

## Error Handling

### Missing PyObjC

If PyObjC is not installed:

```
RuntimeError: PyObjC is required for CoreGraphics backend.
Install with: pip install pyobjc-framework-Cocoa
```

**Solution**: Install PyObjC as shown in the error message.

### Invalid Font

If you specify a font that doesn't exist:

```
ValueError: Font 'InvalidFont' not found. Use a valid monospace font.
```

**Solution**: Use a valid monospace font like Menlo, Monaco, or Courier New.

### Proportional Font

If you try to use a proportional font:

```
ValueError: Font 'Helvetica' is not monospace. TTK requires fixed-width fonts.
```

**Solution**: Use a monospace font instead.

## Advanced Usage

### Custom Window Size

The window size is calculated automatically based on the character grid dimensions (default 80x24). To change the grid size, you would need to modify the backend initialization (this is typically not needed for most applications).

### Coordinate System

The CoreGraphics backend handles coordinate system transformation automatically:
- TTK uses top-left origin (0,0)
- CoreGraphics uses bottom-left origin
- The backend transforms coordinates so you don't have to worry about it

### Character Dimensions

Character dimensions are calculated automatically from the font:
- Width: Based on the 'M' character (typically widest in monospace fonts)
- Height: Font height + 20% line spacing

## Troubleshooting

### Window Doesn't Appear

Make sure you call `initialize()` before drawing:

```python
renderer = CoreGraphicsBackend()
renderer.initialize()  # Required!
renderer.draw_text(0, 0, "Hello")
renderer.refresh()
```

### Text Doesn't Display

Always call `refresh()` after drawing:

```python
renderer.draw_text(0, 0, "Hello")
renderer.refresh()  # Required to display changes!
```

### Application Hangs

Make sure you're calling `get_input()` in your event loop:

```python
while running:
    renderer.draw_text(0, 0, "Hello")
    renderer.refresh()
    event = renderer.get_input()  # Don't forget this!
    # Handle event...
```

### Colors Look Wrong

Make sure you initialize color pairs before using them:

```python
# Initialize first
renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))

# Then use
renderer.draw_text(0, 0, "Text", color_pair=1)
```

## Example Application

Here's a complete example application:

```python
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk import KeyCode, TextAttribute

class SimpleApp:
    def __init__(self):
        self.renderer = CoreGraphicsBackend(
            window_title="Simple Application",
            font_name="Menlo",
            font_size=14
        )
        self.running = False
    
    def initialize(self):
        self.renderer.initialize()
        
        # Initialize colors
        self.renderer.init_color_pair(1, (255, 255, 255), (0, 0, 128))
        self.renderer.init_color_pair(2, (0, 0, 0), (200, 200, 200))
    
    def draw(self):
        self.renderer.clear()
        
        # Draw title
        self.renderer.draw_text(0, 0, " Simple Application ",
                               color_pair=1,
                               attributes=TextAttribute.BOLD)
        
        # Draw content
        self.renderer.draw_text(2, 2, "Hello, macOS!")
        self.renderer.draw_text(3, 2, "Unicode: 世界 🌍")
        self.renderer.draw_text(4, 2, "Emoji: 😀 🎉 ✨")
        
        # Draw status bar
        rows, cols = self.renderer.get_dimensions()
        self.renderer.draw_text(rows - 1, 0,
                               " Press ESC to quit ".ljust(cols),
                               color_pair=2)
        
        self.renderer.refresh()
    
    def handle_input(self, event):
        if event.key_code == KeyCode.ESCAPE:
            self.running = False
    
    def run(self):
        self.initialize()
        
        try:
            self.running = True
            while self.running:
                self.draw()
                event = self.renderer.get_input()
                if event:
                    self.handle_input(event)
        finally:
            self.renderer.shutdown()

if __name__ == '__main__':
    app = SimpleApp()
    app.run()
```

## See Also

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [User Guide](USER_GUIDE.md) - General TTK usage guide
- [Backend Implementation Guide](BACKEND_IMPLEMENTATION_GUIDE.md) - Creating custom backends
- [Examples](EXAMPLES.md) - More example applications
