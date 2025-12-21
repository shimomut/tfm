# Design Document

## Overview

This document describes the design for a C++ rendering backend that provides direct CoreGraphics/CoreText API access while maintaining compatibility with the existing PyObjC implementation. The design focuses on performance optimization through native API calls, efficient caching, and batching strategies, while allowing seamless switching between PyObjC and C++ implementations.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Python Application Layer                  │
│                  (TTK/TFM Application Code)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              CoreGraphicsBackend (Python)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Backend Selector (USE_CPP_RENDERING flag)           │  │
│  └──────────────┬───────────────────────┬────────────────┘  │
│                 │                       │                    │
│                 ▼                       ▼                    │
│  ┌──────────────────────┐  ┌──────────────────────────┐    │
│  │  PyObjC Rendering    │  │  C++ Rendering Module    │    │
│  │  (drawRect_ method)  │  │  (cpp_renderer.so)       │    │
│  └──────────────────────┘  └──────────┬───────────────┘    │
└─────────────────────────────────────────┼──────────────────┘
                                          │
                                          ▼
                           ┌──────────────────────────────┐
                           │  CoreGraphics/CoreText APIs  │
                           │  (Native macOS Frameworks)   │
                           └──────────────────────────────┘
```

### Component Breakdown

1. **Backend Selector**: Configuration mechanism in Python that chooses between PyObjC and C++ rendering
2. **PyObjC Rendering**: Existing implementation using PyObjC bridge (preserved for compatibility)
3. **C++ Rendering Module**: New Python extension module written in C++ with direct API access
4. **Cache Layer**: Font, color, and attribute caching implemented in C++ for performance
5. **Batch Processor**: Background and character batching logic in C++ for reduced API calls

## Components and Interfaces

### 1. Backend Selector (Python)

**Purpose**: Provide a simple mechanism to switch between PyObjC and C++ rendering implementations.

**Interface**:
```python
class CoreGraphicsBackend(Renderer):
    # Configuration flag (can be set via environment variable or code)
    USE_CPP_RENDERING = os.environ.get('TTK_USE_CPP_RENDERING', 'false').lower() == 'true'
    
    def __init__(self, ...):
        # Try to import C++ module if enabled
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

**Design Decisions**:
- Use environment variable `TTK_USE_CPP_RENDERING=true` for easy switching
- Fall back to PyObjC if C++ module is not available
- Log which implementation is being used for debugging

### 2. C++ Rendering Module (cpp_renderer)

**Purpose**: Provide high-performance rendering through direct CoreGraphics/CoreText API access.

**Module Structure**:
```cpp
// cpp_renderer.cpp - Python extension module

// Main rendering function exposed to Python
PyObject* render_frame(PyObject* self, PyObject* args) {
    // Parameters:
    // - CGContextRef context
    // - grid data (list of lists)
    // - color_pairs (dict)
    // - dirty_rect (NSRect)
    // - char_width, char_height
    // - rows, cols
    // - cursor_visible, cursor_row, cursor_col
    // - marked_text (optional)
    
    // Returns: None or raises exception on error
}

// Cache management functions
PyObject* clear_caches(PyObject* self, PyObject* args);
PyObject* get_performance_metrics(PyObject* self, PyObject* args);
PyObject* reset_metrics(PyObject* self, PyObject* args);

// Module initialization
PyMODINIT_FUNC PyInit_cpp_renderer(void) {
    // Register functions and initialize module
}
```

**Key Classes**:

```cpp
// Font cache for CTFont objects
class FontCache {
private:
    std::unordered_map<int, CTFontRef> cache_;
    CTFontRef base_font_;
    
public:
    FontCache(CTFontRef base_font);
    ~FontCache();
    
    CTFontRef get_font(int attributes);
    void clear();
};

// Color cache for CGColor objects
class ColorCache {
private:
    std::unordered_map<uint32_t, CGColorRef> cache_;
    size_t max_size_;
    
public:
    ColorCache(size_t max_size = 256);
    ~ColorCache();
    
    CGColorRef get_color(uint8_t r, uint8_t g, uint8_t b, float alpha = 1.0);
    void clear();
};

// Attribute dictionary cache for text attributes
class AttributeDictCache {
private:
    std::unordered_map<uint64_t, CFDictionaryRef> cache_;
    FontCache* font_cache_;
    ColorCache* color_cache_;
    size_t hits_;
    size_t misses_;
    
public:
    AttributeDictCache(FontCache* font_cache, ColorCache* color_cache);
    ~AttributeDictCache();
    
    CFDictionaryRef get_attributes(int font_key, uint32_t color_rgb, bool underline);
    void clear();
    size_t get_hit_count() const { return hits_; }
    size_t get_miss_count() const { return misses_; }
    void reset_metrics();
};

// Rectangle batcher for background rendering
class RectangleBatcher {
private:
    struct RectBatch {
        CGFloat x, y, width, height;
        uint32_t bg_rgb;
    };
    
    std::vector<RectBatch> batches_;
    std::optional<RectBatch> current_batch_;
    
public:
    void add_cell(CGFloat x, CGFloat y, CGFloat width, CGFloat height, uint32_t bg_rgb);
    void finish_row();
    const std::vector<RectBatch>& get_batches();
    void clear();
};

// Main renderer class
class Renderer {
private:
    FontCache font_cache_;
    ColorCache color_cache_;
    AttributeDictCache attr_dict_cache_;
    RectangleBatcher batcher_;
    
    // Performance metrics
    size_t frames_rendered_;
    double total_render_time_;
    size_t total_batches_;
    
public:
    Renderer(CTFontRef base_font);
    ~Renderer();
    
    void render_frame(
        CGContextRef context,
        PyObject* grid,
        PyObject* color_pairs,
        CGRect dirty_rect,
        CGFloat char_width,
        CGFloat char_height,
        int rows,
        int cols,
        CGFloat offset_x,
        CGFloat offset_y,
        bool cursor_visible,
        int cursor_row,
        int cursor_col,
        const char* marked_text
    );
    
    void clear_caches();
    PyObject* get_performance_metrics();
    void reset_metrics();
};
```

### 3. TTKView Integration (Python)

**Purpose**: Integrate C++ rendering into the existing TTKView drawRect_ method.

**Modified drawRect_ Method**:
```python
def drawRect_(self, rect):
    """Render using C++ or PyObjC based on configuration."""
    
    # Get graphics context
    graphics_context = Cocoa.NSGraphicsContext.currentContext()
    if graphics_context is None:
        return
    
    # Calculate offsets (same for both implementations)
    view_frame = self.frame()
    view_width = view_frame.size.width
    view_height = view_frame.size.height
    grid_width = self.backend.cols * self.backend.char_width
    grid_height = self.backend.rows * self.backend.char_height
    offset_x = (view_width - grid_width) / 2.0
    offset_y = (view_height - grid_height) / 2.0
    
    # Choose rendering implementation
    if self.backend.USE_CPP_RENDERING and self.backend._cpp_renderer:
        # Use C++ rendering
        context = graphics_context.CGContext()
        
        try:
            self.backend._cpp_renderer.render_frame(
                context,
                self.backend.grid,
                self.backend.color_pairs,
                rect,
                self.backend.char_width,
                self.backend.char_height,
                self.backend.rows,
                self.backend.cols,
                offset_x,
                offset_y,
                self.backend.cursor_visible,
                self.backend.cursor_row,
                self.backend.cursor_col,
                getattr(self, 'marked_text', None)
            )
        except Exception as e:
            print(f"C++ rendering failed: {e}")
            # Fall back to PyObjC rendering
            self._render_with_pyobjc(rect, offset_x, offset_y)
    else:
        # Use PyObjC rendering
        self._render_with_pyobjc(rect, offset_x, offset_y)

def _render_with_pyobjc(self, rect, offset_x, offset_y):
    """Original PyObjC rendering implementation."""
    # ... existing drawRect_ code ...
```

## Data Models

### Grid Data Structure

The character grid is passed from Python to C++ as a list of lists:

```python
# Python side
grid = [
    [(' ', 0, 0), ('H', 1, 0), ('e', 1, 0), ...],  # Row 0
    [(' ', 0, 0), ('W', 1, 2), ('o', 1, 2), ...],  # Row 1
    ...
]
# Each cell: (char: str, color_pair: int, attributes: int)
```

```cpp
// C++ side - extract from PyObject*
struct Cell {
    std::string character;  // UTF-8 encoded
    int color_pair;
    int attributes;
};

std::vector<std::vector<Cell>> parse_grid(PyObject* grid_obj);
```

### Color Pair Structure

```python
# Python side
color_pairs = {
    0: ((255, 255, 255), (0, 0, 0)),      # White on black
    1: ((0, 255, 0), (0, 0, 0)),          # Green on black
    2: ((255, 0, 0), (255, 255, 255)),    # Red on white
    ...
}
```

```cpp
// C++ side
struct ColorPair {
    uint32_t fg_rgb;  // Packed RGB: 0x00RRGGBB
    uint32_t bg_rgb;
};

std::unordered_map<int, ColorPair> parse_color_pairs(PyObject* pairs_obj);
```

### Performance Metrics Structure

```cpp
struct PerformanceMetrics {
    size_t frames_rendered;
    double total_render_time_ms;
    double avg_render_time_ms;
    size_t total_batches;
    double avg_batches_per_frame;
    size_t attr_dict_cache_hits;
    size_t attr_dict_cache_misses;
    double attr_dict_cache_hit_rate;
};
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Visual Output Equivalence

*For any* valid grid state, color pairs, and rendering parameters, the C++ rendering output SHALL be visually identical to the PyObjC rendering output.

**Validates: Requirements 8.2**

### Property 2: Coordinate Transformation Consistency

*For any* cell position (row, col) in the grid, the pixel coordinates calculated by C++ rendering SHALL match the coordinates calculated by PyObjC rendering.

**Validates: Requirements 1.4, 8.3**

### Property 3: Batch Correctness

*For any* sequence of adjacent cells with the same background color, the C++ batcher SHALL produce a single batch covering all cells.

**Validates: Requirements 2.1**

### Property 4: Cache Hit Consistency

*For any* repeated rendering of the same text with the same attributes, the attribute dictionary cache SHALL return the same cached object on subsequent calls.

**Validates: Requirements 4.3**

### Property 5: Memory Leak Freedom

*For any* sequence of render operations followed by cache clearing, all CoreFoundation objects SHALL be properly released with no memory leaks.

**Validates: Requirements 12.1, 12.2**

### Property 6: Error Handling Robustness

*For any* invalid input parameters (null pointers, out-of-bounds indices, invalid color values), the C++ renderer SHALL raise appropriate Python exceptions without crashing.

**Validates: Requirements 11.2, 11.5**

### Property 7: Backend Switching Transparency

*For any* application code using the CoreGraphicsBackend, switching between PyObjC and C++ rendering SHALL require only changing the USE_CPP_RENDERING flag.

**Validates: Requirements 7.1, 7.2**

### Property 8: Wide Character Handling

*For any* wide character (zenkaku) in the grid, the C++ renderer SHALL draw it with double width and skip the placeholder cell.

**Validates: Requirements 3.4**

### Property 9: Attribute Application Correctness

*For any* text with BOLD, UNDERLINE, or REVERSE attributes, the C++ renderer SHALL apply the attributes identically to PyObjC rendering.

**Validates: Requirements 1.5, 3.5**

### Property 10: Dirty Region Optimization

*For any* dirty rectangle that covers only a subset of the grid, the C++ renderer SHALL process only the cells within that rectangle.

**Validates: Requirements 2.4, 2.5**

## Error Handling

### Error Categories

1. **Python API Errors**:
   - Invalid parameter types (not a list, not a dict, etc.)
   - Out-of-bounds indices
   - Missing required parameters
   - **Handling**: Raise Python TypeError or ValueError with descriptive message

2. **CoreGraphics API Errors**:
   - Null CGContext
   - Font loading failures
   - Color creation failures
   - **Handling**: Log error and fall back to PyObjC rendering

3. **Memory Allocation Errors**:
   - Failed malloc/new
   - Cache size exceeded
   - **Handling**: Throw std::bad_alloc, caught and converted to Python MemoryError

4. **Resource Cleanup Errors**:
   - CFRelease on null pointer
   - Double-free attempts
   - **Handling**: Use RAII patterns to prevent, log warnings if detected

### Error Handling Strategy

```cpp
PyObject* render_frame(PyObject* self, PyObject* args) {
    try {
        // Validate parameters
        if (!validate_parameters(args)) {
            PyErr_SetString(PyExc_ValueError, "Invalid parameters");
            return nullptr;
        }
        
        // Parse Python objects
        auto grid = parse_grid(grid_obj);
        auto color_pairs = parse_color_pairs(pairs_obj);
        
        // Perform rendering
        renderer.render_frame(context, grid, color_pairs, ...);
        
        Py_RETURN_NONE;
        
    } catch (const std::bad_alloc& e) {
        PyErr_SetString(PyExc_MemoryError, "Memory allocation failed");
        return nullptr;
        
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
        
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "Unknown error in C++ renderer");
        return nullptr;
    }
}
```

## Testing Strategy

### Unit Testing

**Objective**: Verify individual C++ components work correctly in isolation.

**Approach**:
- Use Google Test framework for C++ unit tests
- Test each cache class independently
- Test coordinate transformation functions
- Test batch accumulation logic
- Test error handling paths

**Example Tests**:
```cpp
TEST(FontCacheTest, CachesAndReturnsSameFont) {
    CTFontRef base_font = create_test_font();
    FontCache cache(base_font);
    
    CTFontRef font1 = cache.get_font(TextAttribute::BOLD);
    CTFontRef font2 = cache.get_font(TextAttribute::BOLD);
    
    EXPECT_EQ(font1, font2);  // Same object returned
}

TEST(RectangleBatcherTest, BatchesAdjacentCells) {
    RectangleBatcher batcher;
    
    batcher.add_cell(0.0, 0.0, 10.0, 20.0, 0xFF0000);  // Red
    batcher.add_cell(10.0, 0.0, 10.0, 20.0, 0xFF0000); // Adjacent red
    batcher.finish_row();
    
    auto batches = batcher.get_batches();
    EXPECT_EQ(batches.size(), 1);  // Single batch
    EXPECT_EQ(batches[0].width, 20.0);  // Combined width
}
```

### Integration Testing

**Objective**: Verify C++ rendering produces correct output when integrated with Python.

**Approach**:
- Create Python test scripts that render known patterns
- Compare C++ output with PyObjC output pixel-by-pixel
- Test with various grid sizes, fonts, and color schemes
- Test edge cases (empty grid, single cell, full screen)

**Example Tests**:
```python
def test_cpp_rendering_matches_pyobjc():
    """Verify C++ and PyObjC produce identical output."""
    backend_cpp = create_backend(use_cpp=True)
    backend_pyobjc = create_backend(use_cpp=False)
    
    # Render same content with both backends
    test_grid = create_test_grid()
    
    image_cpp = render_to_image(backend_cpp, test_grid)
    image_pyobjc = render_to_image(backend_pyobjc, test_grid)
    
    # Compare pixel-by-pixel
    assert images_equal(image_cpp, image_pyobjc)
```

### Property-Based Testing

**Objective**: Verify correctness properties hold across many generated inputs.

**Approach**:
- Use Hypothesis for Python property tests
- Generate random grids, color pairs, and dirty regions
- Verify properties like visual equivalence, batch correctness, memory safety

**Example Tests**:
```python
from hypothesis import given, strategies as st

@given(
    grid=st.lists(st.lists(st.tuples(
        st.text(min_size=1, max_size=1),  # char
        st.integers(min_value=0, max_value=255),  # color_pair
        st.integers(min_value=0, max_value=7)  # attributes
    )), min_size=1, max_size=100),
    color_pairs=st.dictionaries(
        st.integers(min_value=0, max_value=255),
        st.tuples(
            st.tuples(st.integers(0, 255), st.integers(0, 255), st.integers(0, 255)),
            st.tuples(st.integers(0, 255), st.integers(0, 255), st.integers(0, 255))
        )
    )
)
def test_cpp_rendering_never_crashes(grid, color_pairs):
    """Property: C++ rendering never crashes on valid input."""
    backend = create_backend(use_cpp=True)
    
    try:
        render_grid(backend, grid, color_pairs)
        # Should complete without exception
    except Exception as e:
        pytest.fail(f"C++ rendering crashed: {e}")
```

### Performance Testing

**Objective**: Measure and compare performance of C++ vs PyObjC rendering.

**Approach**:
- Benchmark rendering time for various grid sizes
- Measure cache hit rates
- Compare batch counts
- Profile with Instruments on macOS

**Example Tests**:
```python
def test_cpp_rendering_performance():
    """Measure C++ rendering performance."""
    backend = create_backend(use_cpp=True)
    grid = create_large_grid(rows=50, cols=200)
    
    times = []
    for _ in range(100):
        start = time.time()
        backend.refresh()
        times.append(time.time() - start)
    
    avg_time = sum(times) / len(times)
    print(f"Average render time: {avg_time*1000:.2f}ms")
    
    # Get metrics
    metrics = backend._cpp_renderer.get_performance_metrics()
    print(f"Cache hit rate: {metrics['cache_hit_rate']:.1f}%")
    print(f"Avg batches per frame: {metrics['avg_batches_per_frame']:.1f}")
```

### Visual Regression Testing

**Objective**: Ensure C++ rendering produces visually correct output.

**Approach**:
- Capture screenshots of known UI states
- Compare with reference images
- Flag any pixel differences for manual review

**Example Tests**:
```python
def test_visual_regression():
    """Verify C++ rendering matches reference images."""
    backend = create_backend(use_cpp=True)
    
    test_cases = [
        "file_listing",
        "text_editor",
        "dialog_box",
        "menu_bar",
        "japanese_text"
    ]
    
    for test_case in test_cases:
        grid = load_test_case(test_case)
        image = render_to_image(backend, grid)
        reference = load_reference_image(test_case)
        
        diff = compare_images(image, reference)
        assert diff < 0.01, f"{test_case} differs from reference"
```

## Build System

### Setup.py Configuration

```python
from setuptools import setup, Extension
import os

# Define C++ extension module
cpp_renderer = Extension(
    'cpp_renderer',
    sources=['src/cpp_renderer.cpp'],
    include_dirs=['/usr/include'],
    extra_compile_args=[
        '-std=c++17',
        '-O3',
        '-Wall',
        '-Wextra'
    ],
    extra_link_args=[
        '-framework', 'CoreGraphics',
        '-framework', 'CoreText',
        '-framework', 'CoreFoundation'
    ],
    language='c++'
)

setup(
    name='ttk',
    version='1.0.0',
    ext_modules=[cpp_renderer],
    # ... other setup parameters ...
)
```

### Build Instructions

```bash
# Build the C++ extension
python setup.py build_ext --inplace

# Install with C++ extension
python setup.py install

# Run tests
python -m pytest test/

# Enable C++ rendering
export TTK_USE_CPP_RENDERING=true
python tfm.py
```

### Platform Requirements

- macOS 10.13+ (High Sierra or later)
- Xcode Command Line Tools
- Python 3.7+
- C++17 compatible compiler (clang++)

## Performance Considerations

### Expected Performance Improvements

Based on the current PyObjC implementation analysis:

1. **Reduced Python/Objective-C Bridge Overhead**:
   - PyObjC adds ~10-20% overhead for each API call
   - Direct C++ calls eliminate this overhead
   - Expected improvement: 10-20% faster

2. **More Efficient Caching**:
   - C++ std::unordered_map is faster than Python dict
   - No Python object creation overhead
   - Expected improvement: 5-10% faster

3. **Optimized Memory Layout**:
   - C++ structs have better cache locality than Python objects
   - Reduced memory allocations
   - Expected improvement: 5-10% faster

4. **Combined Expected Improvement**: 20-40% faster rendering

### Optimization Strategies

1. **Cache Warming**: Pre-populate caches with common fonts and colors
2. **Batch Size Tuning**: Adjust batch accumulation thresholds
3. **SIMD Operations**: Use vector instructions for color conversions
4. **Memory Pooling**: Reuse allocated memory across frames

## Migration Path

### Phase 1: Basic C++ Rendering (Weeks 1-2)

- Implement core rendering functions
- Background batching
- Character drawing with CTLineDraw
- Basic caching (fonts, colors)

### Phase 2: Feature Parity (Weeks 3-4)

- Cursor rendering
- IME marked text
- All text attributes (BOLD, UNDERLINE, REVERSE)
- Wide character support

### Phase 3: Integration & Testing (Weeks 5-6)

- Backend selector implementation
- Comprehensive testing
- Performance benchmarking
- Bug fixes

### Phase 4: Optimization & Documentation (Weeks 7-8)

- Performance tuning
- Advanced caching strategies
- Documentation
- User guide

## Deployment Strategy

### Backward Compatibility

- PyObjC rendering remains the default
- C++ rendering is opt-in via environment variable
- Automatic fallback if C++ module unavailable
- No changes required to existing application code

### Rollout Plan

1. **Alpha Release**: Internal testing with C++ rendering enabled
2. **Beta Release**: Opt-in for early adopters
3. **Stable Release**: C++ rendering available, PyObjC still default
4. **Future**: Consider making C++ rendering the default after extensive testing
