# C++ Rendering Backend API Documentation

## Overview

The C++ rendering backend provides high-performance rendering for the CoreGraphics backend through direct CoreGraphics/CoreText API access. This document describes the public API exposed by the `cpp_renderer` Python extension module.

## Module: cpp_renderer

The `cpp_renderer` module is a Python extension written in C++ that provides optimized rendering functions for the TTK CoreGraphics backend.

### Importing the Module

```python
import cpp_renderer

# Check if module is available
try:
    import cpp_renderer
    print("C++ renderer available")
except ImportError:
    print("C++ renderer not available, using PyObjC fallback")
```

## Public Functions

### render_frame()

Main rendering function that draws a complete frame to a CoreGraphics context.

**Signature:**
```python
def render_frame(
    context: int,           # CGContextRef as integer pointer
    grid: List[List[Tuple[str, int, int]]],  # Character grid
    color_pairs: Dict[int, Tuple[Tuple[int, int, int], Tuple[int, int, int]]],
    dirty_rect: Tuple[float, float, float, float],  # (x, y, width, height)
    char_width: float,
    char_height: float,
    rows: int,
    cols: int,
    offset_x: float,
    offset_y: float,
    cursor_visible: bool,
    cursor_row: int,
    cursor_col: int,
    marked_text: str = ""
) -> None
```

**Parameters:**

- `context` (int): CGContextRef cast to integer pointer. Obtain from `NSGraphicsContext.currentContext().CGContext()`
- `grid` (List[List[Tuple[str, int, int]]]): 2D array of cells, where each cell is a tuple of:
  - `char` (str): Single character or empty string for wide character placeholders
  - `color_pair` (int): Index into color_pairs dictionary
  - `attributes` (int): Bitfield of text attributes (BOLD=1, UNDERLINE=2, REVERSE=4)
- `color_pairs` (Dict[int, Tuple[Tuple[int, int, int], Tuple[int, int, int]]]): Mapping of color pair IDs to (foreground_rgb, background_rgb) tuples, where each RGB is (r, g, b) with values 0-255
- `dirty_rect` (Tuple[float, float, float, float]): Rectangle to redraw in CoreGraphics coordinates (x, y, width, height)
- `char_width` (float): Width of a single character cell in pixels
- `char_height` (float): Height of a single character cell in pixels
- `rows` (int): Number of rows in the grid
- `cols` (int): Number of columns in the grid
- `offset_x` (float): Horizontal offset for centering the grid in the view
- `offset_y` (float): Vertical offset for centering the grid in the view
- `cursor_visible` (bool): Whether to draw the cursor
- `cursor_row` (int): Row position of the cursor (0-based)
- `cursor_col` (int): Column position of the cursor (0-based)
- `marked_text` (str, optional): IME composition text to render at cursor position

**Returns:** None

**Raises:**
- `ValueError`: If parameters are invalid (null context, invalid dimensions, out-of-bounds indices)
- `TypeError`: If parameter types are incorrect
- `RuntimeError`: If rendering fails due to CoreGraphics API errors
- `MemoryError`: If memory allocation fails

**Example:**
```python
import cpp_renderer
import Cocoa

# In TTKView.drawRect_()
graphics_context = Cocoa.NSGraphicsContext.currentContext()
context = graphics_context.CGContext()

cpp_renderer.render_frame(
    context=context,
    grid=self.backend.grid,
    color_pairs=self.backend.color_pairs,
    dirty_rect=(rect.origin.x, rect.origin.y, rect.size.width, rect.size.height),
    char_width=self.backend.char_width,
    char_height=self.backend.char_height,
    rows=self.backend.rows,
    cols=self.backend.cols,
    offset_x=offset_x,
    offset_y=offset_y,
    cursor_visible=self.backend.cursor_visible,
    cursor_row=self.backend.cursor_row,
    cursor_col=self.backend.cursor_col,
    marked_text=getattr(self, 'marked_text', '')
)
```

### get_performance_metrics()

Retrieves performance metrics collected during rendering.

**Signature:**
```python
def get_performance_metrics() -> Dict[str, float]
```

**Parameters:** None

**Returns:** Dictionary with the following keys:
- `frames_rendered` (int): Total number of frames rendered
- `total_render_time_ms` (float): Total rendering time in milliseconds
- `avg_render_time_ms` (float): Average rendering time per frame in milliseconds
- `total_batches` (int): Total number of batches drawn (backgrounds + characters)
- `avg_batches_per_frame` (float): Average number of batches per frame
- `attr_dict_cache_hits` (int): Number of attribute dictionary cache hits
- `attr_dict_cache_misses` (int): Number of attribute dictionary cache misses
- `attr_dict_cache_hit_rate` (float): Cache hit rate as percentage (0-100)

**Example:**
```python
import cpp_renderer

# After rendering some frames
metrics = cpp_renderer.get_performance_metrics()
print(f"Average render time: {metrics['avg_render_time_ms']:.2f}ms")
print(f"Cache hit rate: {metrics['attr_dict_cache_hit_rate']:.1f}%")
print(f"Batches per frame: {metrics['avg_batches_per_frame']:.1f}")
```

### reset_metrics()

Resets all performance metrics counters to zero.

**Signature:**
```python
def reset_metrics() -> None
```

**Parameters:** None

**Returns:** None

**Example:**
```python
import cpp_renderer

# Reset metrics before benchmarking
cpp_renderer.reset_metrics()

# Render frames...

# Get fresh metrics
metrics = cpp_renderer.get_performance_metrics()
```

### clear_caches()

Clears all internal caches (font cache, color cache, attribute dictionary cache).

**Signature:**
```python
def clear_caches() -> None
```

**Parameters:** None

**Returns:** None

**Notes:**
- Call this when changing fonts or when memory usage is a concern
- Caches will be repopulated automatically on next render
- Performance may be temporarily reduced after clearing until caches warm up

**Example:**
```python
import cpp_renderer

# Clear caches when font changes
cpp_renderer.clear_caches()
```

## Python Interface Integration

### CoreGraphicsBackend Integration

The C++ renderer integrates with the CoreGraphicsBackend class through a backend selector mechanism:

```python
class CoreGraphicsBackend(Renderer):
    # Enable C++ rendering via environment variable
    USE_CPP_RENDERING = os.environ.get('TTK_USE_CPP_RENDERING', 'false').lower() == 'true'
    
    def __init__(self, ...):
        self._cpp_renderer = None
        if self.USE_CPP_RENDERING:
            try:
                import cpp_renderer
                self._cpp_renderer = cpp_renderer
                print("Using C++ rendering backend")
            except ImportError:
                print("C++ renderer not available, falling back to PyObjC")
                self.USE_CPP_RENDERING = False
```

### TTKView Integration

The TTKView class uses the backend selector to choose between PyObjC and C++ rendering:

```python
def drawRect_(self, rect):
    """Render using C++ or PyObjC based on configuration."""
    if self.backend.USE_CPP_RENDERING and self.backend._cpp_renderer:
        # Use C++ rendering
        try:
            self.backend._cpp_renderer.render_frame(...)
        except Exception as e:
            print(f"C++ rendering failed: {e}")
            # Fall back to PyObjC
            self._render_with_pyobjc(rect, offset_x, offset_y)
    else:
        # Use PyObjC rendering
        self._render_with_pyobjc(rect, offset_x, offset_y)
```

## Data Structures

### Grid Format

The grid is a 2D list where each cell is a tuple:

```python
grid = [
    [(' ', 0, 0), ('H', 1, 0), ('e', 1, 0), ('l', 1, 0), ('l', 1, 0), ('o', 1, 0)],  # Row 0
    [(' ', 0, 0), ('W', 2, 1), ('o', 2, 1), ('r', 2, 1), ('l', 2, 1), ('d', 2, 1)],  # Row 1
]

# Cell format: (character, color_pair_id, attributes)
# - character: Single UTF-8 character or empty string for wide char placeholders
# - color_pair_id: Index into color_pairs dictionary
# - attributes: Bitfield (BOLD=1, UNDERLINE=2, REVERSE=4)
```

### Color Pairs Format

Color pairs map IDs to foreground and background RGB tuples:

```python
color_pairs = {
    0: ((255, 255, 255), (0, 0, 0)),      # White on black
    1: ((0, 255, 0), (0, 0, 0)),          # Green on black
    2: ((255, 0, 0), (255, 255, 255)),    # Red on white
}

# Format: {id: ((fg_r, fg_g, fg_b), (bg_r, bg_g, bg_b))}
# RGB values: 0-255
```

### Text Attributes

Text attributes are stored as a bitfield:

```python
ATTR_BOLD = 1      # 0b001
ATTR_UNDERLINE = 2 # 0b010
ATTR_REVERSE = 4   # 0b100

# Combine attributes with bitwise OR
attributes = ATTR_BOLD | ATTR_UNDERLINE  # Bold and underlined
```

## Error Handling

The C++ renderer raises Python exceptions for error conditions:

### ValueError
Raised when parameters are invalid:
- Null CGContext pointer
- Invalid grid dimensions (rows/cols <= 0)
- Out-of-bounds cursor position
- Invalid color values (not in 0-255 range)

### TypeError
Raised when parameter types are incorrect:
- Grid is not a list of lists
- Color pairs is not a dictionary
- Numeric parameters are not numbers

### RuntimeError
Raised when CoreGraphics API calls fail:
- Font loading failures
- Color creation failures
- Context drawing errors

### MemoryError
Raised when memory allocation fails:
- Cache allocation failures
- Large grid allocations

## Performance Considerations

### Cache Warming

For best performance, allow caches to warm up:

```python
# First frame may be slower as caches populate
cpp_renderer.render_frame(...)  # ~5ms (cold caches)
cpp_renderer.render_frame(...)  # ~2ms (warm caches)
```

### Batch Optimization

The renderer automatically batches adjacent cells with the same attributes:

- Background batching: Adjacent cells with same background color
- Character batching: Consecutive characters with same font/color/attributes

Typical batch counts:
- Small grids (24x80): 50-100 batches per frame
- Large grids (50x200): 200-400 batches per frame

### Memory Usage

Cache sizes are tuned for typical usage:
- Font cache: ~10 entries (one per attribute combination)
- Color cache: 256 entries (LRU eviction)
- Attribute dictionary cache: ~100 entries (LRU eviction)

Total memory overhead: ~50-100 KB

## Thread Safety

The C++ renderer is **not thread-safe**. All rendering must occur on the main thread (AppKit requirement).

## Compatibility

- **macOS Version**: 10.13+ (High Sierra or later)
- **Python Version**: 3.7+
- **Architecture**: x86_64, arm64 (Apple Silicon)

## See Also

- [Architecture Documentation](CPP_RENDERING_ARCHITECTURE.md)
- [Build and Installation Guide](CPP_RENDERING_BUILD.md)
- [Troubleshooting Guide](CPP_RENDERING_TROUBLESHOOTING.md)
- [Performance Guide](CPP_RENDERING_PERFORMANCE.md)
