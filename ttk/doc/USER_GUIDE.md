# TTK User Guide

This guide will help you get started with TTK (TUI Toolkit) and build character-grid-based applications that work across multiple platforms.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Building Your First Application](#building-your-first-application)
- [Working with Colors](#working-with-colors)
- [Handling Input](#handling-input)
- [Drawing Operations](#drawing-operations)
- [Backend Selection](#backend-selection)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Introduction

TTK is a rendering library that provides a unified API for building character-grid-based applications. Write your application once, and it can run:

- In a terminal using the curses backend
- As a native macOS desktop application using the CoreGraphics backend

TTK handles all the platform-specific details, so you can focus on your application logic.

## Installation

### Basic Installation

```bash
pip install ttk
```

This installs TTK with the curses backend, which works on all Unix-like systems (Linux, macOS, BSD).

### macOS Desktop Support

For native macOS desktop applications, install PyObjC:

```bash
pip install pyobjc-framework-Cocoa
```

The CoreGraphics backend provides:
- Simple, lightweight implementation
- Native macOS text rendering quality
- Full Unicode and emoji support
- Automatic font fallback
- Smooth rendering performance

### Development Installation

If you're contributing to TTK or want to run tests:

```bash
pip install ttk[dev]
```

## Quick Start

Here's a minimal TTK application:

```python
from ttk.backends.curses_backend import CursesBackend
from ttk import KeyCode

# Create and initialize renderer
renderer = CursesBackend()
renderer.initialize()

try:
    # Draw some text
    renderer.draw_text(0, 0, "Hello, TTK!")
    renderer.draw_text(1, 0, "Press ESC to quit")
    renderer.refresh()
    
    # Wait for ESC key
    while True:
        event = renderer.get_input()
        if event.key_code == KeyCode.ESCAPE:
            break

finally:
    # Always clean up
    renderer.shutdown()
```

Save this as `hello_ttk.py` and run it:

```bash
python hello_ttk.py
```

## Core Concepts

### The Renderer

The `Renderer` is the main interface for all drawing and input operations. You never use the `Renderer` class directly—instead, you use a specific backend implementation like `CursesBackend` or `CoreGraphicsBackend`.

### Character Grid

TTK uses a character-based coordinate system:
- Positions are specified in rows and columns (not pixels)
- (0, 0) is the top-left corner
- Rows increase downward, columns increase rightward

```
     Col 0   Col 1   Col 2   ...
Row 0  (0,0)  (0,1)  (0,2)  ...
Row 1  (1,0)  (1,1)  (1,2)  ...
Row 2  (2,0)  (2,1)  (2,2)  ...
...
```

### Monospace Fonts

TTK requires monospace (fixed-width) fonts where all characters have the same width. This ensures perfect alignment in the character grid.

### Color Pairs

Colors are managed through color pairs—combinations of foreground and background colors. You initialize color pairs with RGB values, then reference them by ID when drawing.

## Building Your First Application

Let's build a simple text viewer application:

```python
from ttk.backends.curses_backend import CursesBackend
from ttk import KeyCode, TextAttribute

class TextViewer:
    def __init__(self, filename):
        self.filename = filename
        self.lines = []
        self.scroll_offset = 0
        self.renderer = CursesBackend()
        
    def load_file(self):
        """Load file contents."""
        with open(self.filename, 'r') as f:
            self.lines = f.readlines()
    
    def draw(self):
        """Draw the current view."""
        rows, cols = self.renderer.get_dimensions()
        
        # Clear screen
        self.renderer.clear()
        
        # Draw title bar
        title = f" {self.filename} "
        self.renderer.draw_text(0, 0, title.center(cols), 
                               color_pair=1, 
                               attributes=TextAttribute.BOLD)
        
        # Draw file contents
        visible_rows = rows - 2  # Leave room for title and status
        for i in range(visible_rows):
            line_num = self.scroll_offset + i
            if line_num < len(self.lines):
                line = self.lines[line_num].rstrip('\n')
                # Truncate if too long
                if len(line) > cols:
                    line = line[:cols]
                self.renderer.draw_text(i + 1, 0, line)
        
        # Draw status bar
        status = f" Line {self.scroll_offset + 1}/{len(self.lines)} "
        self.renderer.draw_text(rows - 1, 0, status.ljust(cols),
                               color_pair=2)
        
        self.renderer.refresh()
    
    def handle_input(self, event):
        """Handle keyboard input."""
        rows, cols = self.renderer.get_dimensions()
        visible_rows = rows - 2
        
        if event.key_code == KeyCode.UP:
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif event.key_code == KeyCode.DOWN:
            max_offset = max(0, len(self.lines) - visible_rows)
            self.scroll_offset = min(max_offset, self.scroll_offset + 1)
        elif event.key_code == KeyCode.PAGE_UP:
            self.scroll_offset = max(0, self.scroll_offset - visible_rows)
        elif event.key_code == KeyCode.PAGE_DOWN:
            max_offset = max(0, len(self.lines) - visible_rows)
            self.scroll_offset = min(max_offset, 
                                    self.scroll_offset + visible_rows)
        elif event.key_code == KeyCode.HOME:
            self.scroll_offset = 0
        elif event.key_code == KeyCode.END:
            max_offset = max(0, len(self.lines) - visible_rows)
            self.scroll_offset = max_offset
        elif event.key_code == KeyCode.ESCAPE or event.char == 'q':
            return False  # Quit
        
        return True  # Continue
    
    def run(self):
        """Main application loop."""
        self.renderer.initialize()
        
        try:
            # Initialize colors
            self.renderer.init_color_pair(1, (255, 255, 255), (0, 0, 128))
            self.renderer.init_color_pair(2, (0, 0, 0), (200, 200, 200))
            
            # Load file
            self.load_file()
            
            # Main loop
            running = True
            while running:
                self.draw()
                event = self.renderer.get_input()
                running = self.handle_input(event)
        
        finally:
            self.renderer.shutdown()

# Usage
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python text_viewer.py <filename>")
        sys.exit(1)
    
    viewer = TextViewer(sys.argv[1])
    viewer.run()
```

## Working with Colors

### Initializing Color Pairs

Color pairs are initialized with RGB values (0-255 for each component):

```python
# White text on blue background
renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))

# Yellow text on black background
renderer.init_color_pair(2, (255, 255, 0), (0, 0, 0))

# Green text on dark green background
renderer.init_color_pair(3, (0, 255, 0), (0, 64, 0))
```

### Using Color Pairs

Reference color pairs by their ID when drawing:

```python
renderer.draw_text(0, 0, "White on blue", color_pair=1)
renderer.draw_text(1, 0, "Yellow on black", color_pair=2)
renderer.draw_text(2, 0, "Green on dark green", color_pair=3)
```

### Color Pair 0

Color pair 0 is reserved for the default terminal colors and doesn't need initialization:

```python
# Use default colors
renderer.draw_text(0, 0, "Default colors", color_pair=0)
```

### Color Limitations

- You can define up to 255 color pairs (IDs 1-255)
- Color pair 0 is reserved for defaults
- The curses backend approximates RGB colors to terminal colors
- The CoreGraphics backend supports full RGB colors

## Handling Input

### Basic Input

Get input events with `get_input()`:

```python
# Blocking - wait forever for input
event = renderer.get_input()

# Non-blocking - return immediately
event = renderer.get_input(timeout_ms=0)
if event is None:
    print("No input available")

# Timeout - wait up to 1 second
event = renderer.get_input(timeout_ms=1000)
```

### Checking Key Types

```python
event = renderer.get_input()

if event.is_printable():
    print(f"Printable character: {event.char}")
elif event.is_special_key():
    print(f"Special key: {event.key_code}")
```

### Handling Specific Keys

```python
from ttk import KeyCode

event = renderer.get_input()

if event.key_code == KeyCode.ENTER:
    print("Enter pressed")
elif event.key_code == KeyCode.ESCAPE:
    print("Escape pressed")
elif event.key_code == KeyCode.UP:
    print("Up arrow pressed")
elif event.key_code == KeyCode.F1:
    print("F1 pressed")
elif event.char == 'q':
    print("Q key pressed")
```

### Modifier Keys

Check for modifier keys like Ctrl, Shift, Alt:

```python
from ttk import ModifierKey

event = renderer.get_input()

# Check for Ctrl+C
if event.char == 'c' and event.has_modifier(ModifierKey.CONTROL):
    print("Ctrl+C pressed")

# Check for Shift+Arrow
if event.key_code == KeyCode.UP and event.has_modifier(ModifierKey.SHIFT):
    print("Shift+Up pressed")

# Check for multiple modifiers
if event.has_modifier(ModifierKey.CONTROL) and \
   event.has_modifier(ModifierKey.ALT):
    print("Ctrl+Alt pressed")
```

### Window Resize Events

Handle terminal/window resizing:

```python
event = renderer.get_input()

if event.key_code == KeyCode.RESIZE:
    # Window was resized
    rows, cols = renderer.get_dimensions()
    print(f"New size: {rows}x{cols}")
    # Redraw your UI with new dimensions
    redraw_ui()
```

## Drawing Operations

### Drawing Text

```python
# Simple text
renderer.draw_text(0, 0, "Hello, World!")

# Text with color
renderer.draw_text(1, 0, "Colored text", color_pair=1)

# Bold text
from ttk import TextAttribute
renderer.draw_text(2, 0, "Bold text", 
                   attributes=TextAttribute.BOLD)

# Multiple attributes
renderer.draw_text(3, 0, "Bold + Underline",
                   attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE)
```

### Drawing Lines

```python
# Horizontal line using box-drawing character (recommended)
renderer.draw_hline(5, 0, '─', 40)

# Vertical line using box-drawing character (recommended)
renderer.draw_vline(0, 10, '│', 20)

# Colored lines with box-drawing characters
renderer.draw_hline(10, 0, '─', 40, color_pair=1)
renderer.draw_vline(0, 20, '│', 20, color_pair=2)

# ASCII alternatives (for compatibility)
renderer.draw_hline(15, 0, '-', 40)
renderer.draw_vline(0, 30, '|', 20)
```

### Drawing Rectangles

```python
# Outlined rectangle
renderer.draw_rect(2, 2, 10, 30, filled=False)

# Filled rectangle
renderer.draw_rect(15, 5, 5, 20, filled=True)

# Colored rectangle
renderer.draw_rect(5, 40, 8, 25, color_pair=1, filled=False)
```

### Clearing Regions

```python
# Clear entire screen
renderer.clear()

# Clear a specific region
renderer.clear_region(5, 10, 10, 20)
```

### Refreshing the Display

Always call `refresh()` after drawing to make changes visible:

```python
renderer.draw_text(0, 0, "Line 1")
renderer.draw_text(1, 0, "Line 2")
renderer.draw_text(2, 0, "Line 3")
renderer.refresh()  # Now all three lines appear
```

For efficiency, you can refresh only a specific region:

```python
renderer.draw_text(5, 10, "Updated")
renderer.refresh_region(5, 10, 1, 7)
```

## Backend Selection

### Choosing a Backend

Select the appropriate backend for your platform:

```python
# Terminal application (works everywhere)
from ttk.backends.curses_backend import CursesBackend
renderer = CursesBackend()

# macOS desktop application - CoreGraphics (recommended)
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
renderer = CoreGraphicsBackend(
    window_title="My App",
    font_name="Menlo",
    font_size=14
)

# macOS desktop application - CoreGraphics (native rendering)
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
renderer = CoreGraphicsBackend(
    window_title="My App",
    font_name="Menlo",
    font_size=14
)
```

**Which macOS backend should I use?**

- **CoreGraphics**: Best for macOS desktop applications. Simple, lightweight, excellent text quality.

### Automatic Backend Selection

Use the utility function to automatically select the best backend:

```python
from ttk.utils.platform_utils import get_recommended_backend

backend_name = get_recommended_backend()

if backend_name == 'coregraphics':
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    renderer = CoreGraphicsBackend()
else:
    from ttk.backends.curses_backend import CursesBackend
    renderer = CursesBackend()
```

### Command-Line Backend Selection

Allow users to choose the backend:

```python
import argparse
from ttk.backends.curses_backend import CursesBackend
from ttk.backends.coregraphics_backend import CoreGraphicsBackend

parser = argparse.ArgumentParser()
parser.add_argument('--backend', 
                   choices=['curses', 'coregraphics'],
                   default='curses', 
                   help='Rendering backend')
args = parser.parse_args()

if args.backend == 'coregraphics':
    renderer = CoreGraphicsBackend()
else:
    renderer = CursesBackend()
```

## Common Patterns

### Application Template

```python
from ttk.backends.curses_backend import CursesBackend
from ttk import KeyCode

class MyApplication:
    def __init__(self):
        self.renderer = CursesBackend()
        self.running = False
    
    def initialize(self):
        """Initialize the application."""
        self.renderer.initialize()
        # Initialize colors
        self.renderer.init_color_pair(1, (255, 255, 255), (0, 0, 128))
    
    def shutdown(self):
        """Clean up resources."""
        self.renderer.shutdown()
    
    def draw(self):
        """Draw the UI."""
        self.renderer.clear()
        # Draw your UI here
        self.renderer.draw_text(0, 0, "My Application")
        self.renderer.refresh()
    
    def handle_input(self, event):
        """Handle input events."""
        if event.key_code == KeyCode.ESCAPE:
            self.running = False
        # Handle other input
    
    def run(self):
        """Main application loop."""
        self.initialize()
        
        try:
            self.running = True
            while self.running:
                self.draw()
                event = self.renderer.get_input()
                self.handle_input(event)
        finally:
            self.shutdown()

if __name__ == '__main__':
    app = MyApplication()
    app.run()
```

### Animation Loop

For smooth animations, use non-blocking input:

```python
import time

def animation_loop():
    renderer.initialize()
    
    try:
        frame = 0
        last_time = time.time()
        
        while True:
            # Calculate delta time
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Update animation
            frame += 1
            
            # Draw frame
            renderer.clear()
            renderer.draw_text(0, 0, f"Frame: {frame}")
            renderer.refresh()
            
            # Check for input without blocking
            event = renderer.get_input(timeout_ms=0)
            if event and event.key_code == KeyCode.ESCAPE:
                break
            
            # Target 60 FPS
            time.sleep(max(0, 1/60 - dt))
    
    finally:
        renderer.shutdown()
```

### Status Bar

```python
def draw_status_bar(renderer, message):
    """Draw a status bar at the bottom of the screen."""
    rows, cols = renderer.get_dimensions()
    status_row = rows - 1
    
    # Clear the status bar
    renderer.clear_region(status_row, 0, 1, cols)
    
    # Draw status message
    renderer.draw_text(status_row, 0, message.ljust(cols), color_pair=1)
```

### Menu System

```python
def draw_menu(renderer, items, selected_index):
    """Draw a simple menu."""
    for i, item in enumerate(items):
        if i == selected_index:
            # Highlight selected item
            renderer.draw_text(i, 0, f"> {item}", 
                             attributes=TextAttribute.REVERSE)
        else:
            renderer.draw_text(i, 0, f"  {item}")

def handle_menu_input(event, selected_index, num_items):
    """Handle menu navigation."""
    if event.key_code == KeyCode.UP:
        return max(0, selected_index - 1)
    elif event.key_code == KeyCode.DOWN:
        return min(num_items - 1, selected_index + 1)
    return selected_index
```

## Troubleshooting

### "Module not found" Error

Make sure TTK is installed:
```bash
pip install ttk
```

### Terminal Colors Look Wrong

The curses backend approximates RGB colors to terminal colors. For accurate colors, use the CoreGraphics backend on macOS.

### Application Doesn't Respond to Input

Make sure you're calling `get_input()` in your main loop:

```python
while running:
    draw()
    event = renderer.get_input()  # Don't forget this!
    handle_input(event)
```

### Screen Doesn't Update

Always call `refresh()` after drawing:

```python
renderer.draw_text(0, 0, "Hello")
renderer.refresh()  # Required to display changes
```

### Terminal State Corrupted After Crash

If your application crashes and leaves the terminal in a bad state, the `shutdown()` method wasn't called. Always use try-finally:

```python
renderer.initialize()
try:
    # Your code
    pass
finally:
    renderer.shutdown()  # Always called, even on exception
```

To manually fix a corrupted terminal:
```bash
reset
```

### CoreGraphics Backend Not Available

The CoreGraphics backend requires macOS and PyObjC. Install with:
```bash
pip install pyobjc-framework-Cocoa
```

### Font Validation Error

The CoreGraphics backend only supports monospace fonts. Use fonts like:
- Menlo (default)
- Monaco
- Courier New
- SF Mono

Avoid proportional fonts like:
- Helvetica
- Arial
- Times New Roman

## Next Steps

- Read the [API Reference](API_REFERENCE.md) for detailed API documentation
- Check out the [Backend Implementation Guide](BACKEND_IMPLEMENTATION_GUIDE.md) to create custom backends
- Explore the demo applications in the `demo/` directory
- Review example applications for common use cases

## Getting Help

- Check the documentation in the `doc/` directory
- Review the demo applications for examples
- Report issues on the project repository
- Consult the API reference for detailed method documentation
