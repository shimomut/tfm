# TTK (TUI Toolkit / Traditional app Toolkit)

A generic, reusable rendering library that supports multiple backends for character-grid-based applications.

## Overview

TTK provides an abstract rendering API that allows text-based applications to run on different platforms without modification. The library focuses on character-grid-based rendering with monospace fonts, supporting text, rectangles, lines, and future image rendering.

## Features

- **Backend Agnostic**: Write your application once, run on multiple platforms
- **Multiple Backends**: 
  - Curses backend for terminal applications
  - Metal backend for native macOS desktop applications (planned)
- **Simple API**: Clean, well-documented interface for rendering operations
- **Input Handling**: Unified input event system across all backends
- **Color Support**: Full RGB color support with 256 color pairs
- **Text Attributes**: Bold, underline, and reverse video support
- **Performance**: Efficient rendering with support for partial updates

## Installation

```bash
pip install ttk
```

For Metal backend support on macOS:
```bash
pip install ttk[metal]
```

For development:
```bash
pip install ttk[dev]
```

## Quick Start

```python
from ttk import Renderer
from ttk.backends.curses_backend import CursesBackend

# Create a renderer
renderer = CursesBackend()
renderer.initialize()

try:
    # Get window dimensions
    rows, cols = renderer.get_dimensions()
    
    # Draw some text
    renderer.draw_text(0, 0, "Hello, TTK!", color_pair=1)
    
    # Draw a rectangle
    renderer.draw_rect(2, 2, 5, 20, color_pair=2, filled=False)
    
    # Refresh to display
    renderer.refresh()
    
    # Wait for input
    event = renderer.get_input(timeout_ms=-1)
    
finally:
    renderer.shutdown()
```

## Requirements

- Python 3.8 or higher
- curses library (built-in on Unix-like systems)
- PyObjC (for Metal backend on macOS, optional)

## Project Structure

```
ttk/
├── __init__.py           # Main package initialization
├── renderer.py           # Abstract Renderer base class
├── input_event.py        # Input event system
├── backends/             # Backend implementations
│   ├── curses_backend.py
│   └── metal_backend.py
├── serialization/        # Command serialization
│   └── command_serializer.py
└── utils/                # Utility functions
    ├── platform_utils.py
    ├── color_utils.py
    └── validation.py
```

## Documentation

Full documentation will be available as the library is developed. For now, refer to:
- API documentation in source code docstrings
- Design document in the project repository
- Demo applications in the `demo/` directory

## Development Status

TTK is currently in alpha development. The API may change as the library evolves.

## License

MIT License

## Contributing

Contributions are welcome! Please refer to the project repository for contribution guidelines.
