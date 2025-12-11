# TTK (TUI Toolkit / Traditional app Toolkit)

A generic, reusable rendering library that supports multiple backends for character-grid-based applications.

## Overview

TTK provides an abstract rendering API that allows text-based applications to run on different platforms without modification. The library focuses on character-grid-based rendering with monospace fonts, supporting text, rectangles, lines, and future image rendering.

Write your application once using TTK's simple API, and it can run:
- In a terminal using the curses backend
- As a native macOS desktop application using the Metal backend
- On any platform with a custom backend implementation

## Features

- **Backend Agnostic**: Write your application once, run on multiple platforms
- **Multiple Backends**: 
  - Curses backend for terminal applications (Linux, macOS, BSD)
  - Metal backend for native macOS desktop applications
- **Simple API**: Clean, well-documented interface for rendering operations
- **Input Handling**: Unified input event system across all backends
- **Color Support**: Full RGB color support with 256 color pairs
- **Text Attributes**: Bold, underline, and reverse video support
- **Performance**: Efficient rendering with support for partial updates
- **Extensible**: Easy to implement custom backends for new platforms

## Installation

### Basic Installation (Terminal Support)

```bash
pip install ttk
```

This installs TTK with the curses backend, which works on all Unix-like systems.

### macOS Desktop Support

For native macOS desktop applications with the Metal backend:

```bash
pip install ttk[metal]
```

### Development Installation

For development and testing:

```bash
pip install ttk[dev]
```

## Quick Start

### Simple Terminal Application

```python
from ttk.backends.curses_backend import CursesBackend
from ttk import KeyCode

# Create and initialize renderer
renderer = CursesBackend()
renderer.initialize()

try:
    # Initialize colors
    renderer.init_color_pair(1, (255, 255, 255), (0, 0, 128))
    
    # Draw text
    renderer.draw_text(0, 0, "Hello, TTK!", color_pair=1)
    renderer.draw_text(1, 0, "Press ESC to quit")
    
    # Draw a rectangle
    renderer.draw_rect(3, 2, 5, 30, filled=False)
    
    # Refresh to display
    renderer.refresh()
    
    # Wait for ESC key
    while True:
        event = renderer.get_input()
        if event.key_code == KeyCode.ESCAPE:
            break
    
finally:
    renderer.shutdown()
```

### macOS Desktop Application

```python
from ttk.backends.metal_backend import MetalBackend
from ttk import KeyCode

# Create Metal backend with custom window
renderer = MetalBackend(
    window_title="My Desktop App",
    font_name="Menlo",
    font_size=14
)
renderer.initialize()

try:
    # Same drawing code works with Metal backend!
    renderer.init_color_pair(1, (255, 255, 255), (30, 30, 30))
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

### Automatic Backend Selection

```python
from ttk.utils.platform_utils import get_recommended_backend

backend_name = get_recommended_backend()

if backend_name == 'metal':
    from ttk.backends.metal_backend import MetalBackend
    renderer = MetalBackend()
else:
    from ttk.backends.curses_backend import CursesBackend
    renderer = CursesBackend()

renderer.initialize()
# ... use renderer ...
renderer.shutdown()
```

## Core Concepts

### Character Grid Coordinate System

TTK uses a character-based coordinate system:
- **(0, 0)** is at the top-left corner
- **Rows** increase downward (0 is top)
- **Columns** increase rightward (0 is left)
- All positions and dimensions are in **character cells**, not pixels

### Monospace Fonts

TTK requires monospace (fixed-width) fonts where all characters have the same width. This ensures perfect alignment in the character grid.

### Color Pairs

Colors are managed through color pairs—combinations of foreground and background colors:

```python
# Initialize color pair 1: white text on blue background
renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))

# Use the color pair
renderer.draw_text(0, 0, "Colored text", color_pair=1)
```

### Text Attributes

Combine text attributes for styling:

```python
from ttk import TextAttribute

# Bold text
renderer.draw_text(0, 0, "Bold", attributes=TextAttribute.BOLD)

# Bold + Underline
renderer.draw_text(1, 0, "Bold + Underline",
                   attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE)
```

## Documentation

Comprehensive documentation is available in the `doc/` directory:

- **[User Guide](doc/USER_GUIDE.md)** - Getting started, tutorials, and common patterns
- **[API Reference](doc/API_REFERENCE.md)** - Complete API documentation with examples
- **[Backend Implementation Guide](doc/BACKEND_IMPLEMENTATION_GUIDE.md)** - How to create custom backends

## Examples

Example applications are available in the `demo/` directory:

- `demo/demo_ttk.py` - Main demo application with backend selection
- `demo/test_interface.py` - Test interface showing all features
- `demo/performance.py` - Performance monitoring and metrics

Run the demo:

```bash
# Terminal version
python -m ttk.demo.demo_ttk --backend curses

# macOS desktop version
python -m ttk.demo.demo_ttk --backend metal
```

## Requirements

- **Python**: 3.8 or higher
- **Curses backend**: Built-in on Unix-like systems (Linux, macOS, BSD)
- **Metal backend**: macOS only, requires PyObjC

## Project Structure

```
ttk/
├── __init__.py              # Main package initialization
├── renderer.py              # Abstract Renderer base class
├── input_event.py           # Input event system (KeyCode, ModifierKey, InputEvent)
├── backends/                # Backend implementations
│   ├── __init__.py
│   ├── curses_backend.py    # Terminal backend
│   └── metal_backend.py     # macOS desktop backend
├── serialization/           # Command serialization
│   └── command_serializer.py
├── utils/                   # Utility functions
│   ├── platform_utils.py    # Platform detection
│   ├── color_utils.py       # Color conversion utilities
│   └── validation.py        # Parameter validation
├── demo/                    # Demo applications
│   ├── demo_ttk.py          # Main demo
│   ├── test_interface.py    # Test interface
│   └── performance.py       # Performance monitoring
├── test/                    # Test suite
└── doc/                     # Documentation
    ├── USER_GUIDE.md
    ├── API_REFERENCE.md
    └── BACKEND_IMPLEMENTATION_GUIDE.md
```

## Key Features

### Drawing Operations

```python
# Text
renderer.draw_text(row, col, "Hello", color_pair=1)

# Horizontal line
renderer.draw_hline(row, col, '-', length=40)

# Vertical line
renderer.draw_vline(row, col, '|', length=20)

# Rectangle (outlined or filled)
renderer.draw_rect(row, col, height=10, width=30, filled=False)
```

### Input Handling

```python
from ttk import KeyCode, ModifierKey

event = renderer.get_input()

# Check key type
if event.is_printable():
    print(f"Character: {event.char}")
elif event.key_code == KeyCode.UP:
    print("Up arrow pressed")

# Check modifiers
if event.has_modifier(ModifierKey.CONTROL):
    print("Control key held")
```

### Window Management

```python
# Get dimensions
rows, cols = renderer.get_dimensions()

# Clear screen
renderer.clear()

# Clear region
renderer.clear_region(row=5, col=10, height=10, width=20)

# Refresh display
renderer.refresh()

# Refresh region (more efficient)
renderer.refresh_region(row=5, col=10, height=10, width=20)
```

## Platform Support

| Backend | Platform | Status |
|---------|----------|--------|
| Curses  | Linux    | ✅ Stable |
| Curses  | macOS    | ✅ Stable |
| Curses  | BSD      | ✅ Stable |
| Metal   | macOS    | ✅ Stable |

## Performance

- **Curses backend**: Optimized for terminal rendering
- **Metal backend**: GPU-accelerated, 60 FPS performance
- **Partial updates**: Both backends support efficient region updates
- **Minimal overhead**: Thin abstraction layer over platform APIs

## Development Status

TTK is currently in active development. The core API is stable, but new features may be added in future versions.

### Current Version: 0.1.0 (Alpha)

- ✅ Core rendering API
- ✅ Curses backend (stable)
- ✅ Metal backend (stable)
- ✅ Input event system
- ✅ Color management
- ✅ Text attributes
- ✅ Command serialization
- 🚧 Image rendering (planned)
- 🚧 Additional backends (planned)

## Contributing

Contributions are welcome! Areas where you can help:

- Implement backends for new platforms (Windows, Web, etc.)
- Add new features to existing backends
- Improve documentation and examples
- Report bugs and suggest improvements
- Write tests and improve test coverage

Please refer to the project repository for contribution guidelines.

## License

MIT License - see LICENSE file for details

## Credits

TTK was created as part of the TFM (TUI File Manager) project to enable cross-platform rendering support.

## Getting Help

- **Documentation**: Check the `doc/` directory for comprehensive guides
- **Examples**: Review demo applications in the `demo/` directory
- **Issues**: Report bugs and request features on the project repository
- **API Reference**: See [API_REFERENCE.md](doc/API_REFERENCE.md) for detailed API documentation

## Quick Links

- [User Guide](doc/USER_GUIDE.md) - Learn how to use TTK
- [API Reference](doc/API_REFERENCE.md) - Complete API documentation
- [Backend Guide](doc/BACKEND_IMPLEMENTATION_GUIDE.md) - Implement custom backends
- [Demo Applications](demo/) - Example code and usage patterns
