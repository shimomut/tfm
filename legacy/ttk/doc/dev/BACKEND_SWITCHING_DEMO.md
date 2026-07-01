# Backend Switching Demo Implementation

## Overview

The Backend Switching Demo (`ttk/demo/backend_switching.py`) demonstrates that TTK applications can switch between different rendering backends without any changes to the application code. This validates Requirements 11.1 and 16.2 from the CoreGraphics backend specification.

## Purpose

This demo proves that:
1. The same application code works identically with both curses and CoreGraphics backends
2. No application code changes are needed to switch backends
3. Only the backend instantiation needs to change
4. All rendering features work equivalently across backends

## Implementation

### Demo Application Structure

The demo consists of a single `BackendSwitchingDemo` class that:
- Accepts any `Renderer` instance in its constructor
- Uses only the abstract `Renderer` interface methods
- Never checks which backend is being used
- Produces identical output regardless of backend

### Key Features Demonstrated

The demo displays:
1. **Text Rendering**: Various colors (red, green, blue, yellow, cyan)
2. **Text Attributes**: Normal, bold, underline, reverse, and combinations
3. **Shape Drawing**: Rectangles and horizontal lines
4. **Window Information**: Dimensions and coordinate system
5. **Input Handling**: Keyboard events and quit commands
6. **Frame Counter**: Shows continuous rendering

### Backend Selection

Backend selection happens only in the `create_backend()` function:

```python
def create_backend(backend_name: str) -> Renderer:
    if backend_name == 'curses':
        return CursesBackend()
    elif backend_name == 'coregraphics':
        return CoreGraphicsBackend(
            window_title="Backend Switching Demo - CoreGraphics",
            font_name="Menlo",
            font_size=14
        )
```

Once the backend is created, the demo application code is completely backend-agnostic.

## Usage

### Running with Curses Backend

```bash
python ttk/demo/backend_switching.py --backend curses
```

This runs the demo in the terminal using the curses backend.

### Running with CoreGraphics Backend

```bash
python ttk/demo/backend_switching.py --backend coregraphics
```

This runs the demo in a native macOS window using the CoreGraphics backend.

### Expected Behavior

Both backends should display:
- Identical text layout and content
- Same colors (within color space limitations)
- Same text attributes (bold, underline, reverse)
- Same shapes (rectangles, lines)
- Same input handling behavior
- Same quit commands ('q' or ESC)

## Testing

The demo includes comprehensive tests in `ttk/test/test_backend_switching_demo.py`:

### Test Coverage

1. **Initialization Tests**: Verify demo initializes correctly
2. **Color Tests**: Verify color pairs are initialized
3. **Drawing Tests**: Verify screen drawing works
4. **Input Tests**: Verify input handling for quit, ESC, resize, and regular keys
5. **Backend Creation Tests**: Verify both backends can be created
6. **Backend Independence Tests**: Verify identical behavior with both backends

### Running Tests

```bash
python -m pytest ttk/test/test_backend_switching_demo.py -v
```

All 21 tests should pass, confirming:
- Demo works correctly with mock renderers
- Backend creation works for both curses and CoreGraphics
- Input handling is identical for both backends
- Drawing operations are identical for both backends

## Requirements Validation

### Requirement 11.1: Command-Line Backend Selection

✅ **Validated**: The demo accepts `--backend` argument with choices:
- `curses`: Terminal-based rendering
- `coregraphics`: Native macOS rendering

### Requirement 16.2: No Application Code Changes

✅ **Validated**: The `BackendSwitchingDemo` class:
- Uses only abstract `Renderer` interface methods
- Never checks which backend is being used
- Works identically with both backends
- Requires no code changes to switch backends

## Code Structure

### Main Components

1. **BackendSwitchingDemo Class**
   - `__init__(renderer)`: Initialize with any renderer
   - `initialize_colors()`: Set up color pairs
   - `draw_screen()`: Draw the demo interface
   - `handle_input(event)`: Handle keyboard input
   - `run()`: Main event loop

2. **Backend Creation**
   - `create_backend(name)`: Factory function for backends
   - Platform validation for CoreGraphics
   - Error handling for invalid backends

3. **Argument Parsing**
   - `parse_arguments()`: Parse command-line arguments
   - Required `--backend` argument
   - Help text with usage examples

4. **Main Entry Point**
   - `main()`: Initialize, run, and cleanup
   - Error handling and reporting
   - Graceful shutdown

## Design Principles

### Backend Agnostic Code

The demo follows these principles:
1. **Interface-Based**: Uses only `Renderer` interface methods
2. **No Backend Checks**: Never checks `isinstance()` or backend type
3. **Consistent API**: Same method calls work with all backends
4. **Portable**: Works on any platform that supports the backend

### Minimal Backend-Specific Code

Backend-specific code is isolated to:
1. Backend instantiation (different constructors)
2. Platform validation (macOS check for CoreGraphics)
3. Window configuration (title, font for CoreGraphics)

Everything else is completely backend-independent.

## Comparison with demo_ttk.py

The project has two demo applications:

### demo_ttk.py (Comprehensive Demo)
- Full-featured test interface
- Performance monitoring
- More extensive testing
- Supports CoreGraphics backend too
- Auto-detection of best backend

### backend_switching.py (Focused Demo)
- Simpler, more focused
- Specifically demonstrates backend switching
- Only curses and CoreGraphics
- Required `--backend` argument
- Clearer demonstration of backend independence

Both demos validate the same requirements but `backend_switching.py` provides a clearer, more focused demonstration of backend independence.

## Future Enhancements

Potential improvements:
1. Add side-by-side comparison mode
2. Add more complex rendering examples
3. Add animation to show continuous rendering
4. Add performance metrics comparison
5. Add Unicode and emoji examples

## Conclusion

The Backend Switching Demo successfully demonstrates that:
1. TTK applications can switch backends via command-line argument
2. The same application code works identically with both backends
3. No application code changes are needed to switch backends
4. All rendering features work equivalently across backends

This validates the core design principle of TTK: applications written against the abstract `Renderer` interface work with any backend implementation.
