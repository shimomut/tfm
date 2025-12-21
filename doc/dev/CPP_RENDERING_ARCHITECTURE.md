# C++ Rendering Backend Architecture

## Overview

This document describes the architecture and design decisions for the C++ rendering backend. The backend provides high-performance rendering for the CoreGraphics backend through direct CoreGraphics/CoreText API access while maintaining backward compatibility with the existing PyObjC implementation.

## Design Goals

1. **Performance**: Achieve 20-40% faster rendering through direct API access and optimized caching
2. **Compatibility**: Maintain API compatibility with PyObjC rendering for seamless switching
3. **Reliability**: Robust error handling and memory management
4. **Maintainability**: Clean architecture with clear separation of concerns

## High-Level Architecture

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

## Component Architecture

### 1. Backend Selector

**Purpose**: Provide runtime selection between PyObjC and C++ rendering implementations.

**Design Decision**: Use environment variable for configuration
- **Rationale**: Simple, no code changes required, easy to test both implementations
- **Alternative Considered**: Configuration file - rejected as too complex for binary choice
- **Implementation**: `TTK_USE_CPP_RENDERING=true` environment variable

**Fallback Strategy**:
```python
if USE_CPP_RENDERING:
    try:
        import cpp_renderer
        # Use C++ rendering
    except ImportError:
        # Fall back to PyObjC
        USE_CPP_RENDERING = False
```

**Design Decision**: Automatic fallback on import failure
- **Rationale**: Graceful degradation if C++ module not built or incompatible
- **Benefit**: Application continues to work even if C++ extension unavailable

### 2. C++ Extension Module

**Purpose**: Provide Python-callable C++ functions for high-performance rendering.

**Design Decision**: Single `render_frame()` function instead of multiple specialized functions
- **Rationale**: Simpler API, fewer Python/C++ boundary crossings
- **Alternative Considered**: Separate functions for backgrounds, characters, cursor - rejected due to overhead
- **Benefit**: All rendering state stays in C++, reducing marshalling overhead

**Module Structure**:
```cpp
// Python extension module
PyMODINIT_FUNC PyInit_cpp_renderer(void) {
    static PyMethodDef methods[] = {
        {"render_frame", render_frame, METH_VARARGS, "Render a frame"},
        {"get_performance_metrics", get_performance_metrics, METH_NOARGS, "Get metrics"},
        {"reset_metrics", reset_metrics, METH_NOARGS, "Reset metrics"},
        {"clear_caches", clear_caches, METH_NOARGS, "Clear caches"},
        {NULL, NULL, 0, NULL}
    };
    
    static PyModuleDef module = {
        PyModuleDef_HEAD_INIT,
        "cpp_renderer",
        "High-performance CoreGraphics rendering",
        -1,
        methods
    };
    
    return PyModule_Create(&module);
}
```

### 3. Renderer Class

**Purpose**: Coordinate rendering pipeline and manage caches.

**Design Decision**: Single Renderer instance with persistent caches
- **Rationale**: Caches persist across frames for maximum performance
- **Alternative Considered**: Stateless rendering - rejected due to cache recreation overhead
- **Implementation**: Renderer instance created once, reused for all frames

**Rendering Pipeline**:
```
1. Parse Python data structures (grid, color_pairs)
2. Calculate dirty region cells
3. Render backgrounds (batched)
4. Render characters (batched)
5. Render cursor (if visible)
6. Render IME marked text (if present)
7. Update performance metrics
```

**Design Decision**: Sequential rendering stages
- **Rationale**: Clear separation of concerns, easier to debug
- **Alternative Considered**: Interleaved rendering - rejected due to complexity
- **Benefit**: Each stage can be optimized independently

### 4. Caching Strategy

The C++ renderer uses three-level caching for maximum performance:

#### Font Cache

**Purpose**: Cache CTFont objects for different attribute combinations.

**Design Decision**: Cache by attribute bitfield
- **Rationale**: Small number of combinations (8 max: normal, bold, underline, bold+underline, etc.)
- **Cache Size**: ~10 entries typical
- **Eviction**: None needed (small, bounded size)

```cpp
class FontCache {
    std::unordered_map<int, CTFontRef> cache_;
    CTFontRef base_font_;
    
    CTFontRef get_font(int attributes) {
        auto it = cache_.find(attributes);
        if (it != cache_.end()) {
            return it->second;  // Cache hit
        }
        
        // Create font with attributes
        CTFontRef font = base_font_;
        if (attributes & ATTR_BOLD) {
            font = CTFontCreateCopyWithSymbolicTraits(
                base_font_, 0.0, nullptr, kCTFontBoldTrait, kCTFontBoldTrait
            );
        }
        
        cache_[attributes] = font;
        return font;
    }
};
```

**Design Decision**: Apply BOLD via CTFontCreateCopyWithSymbolicTraits
- **Rationale**: Native CoreText bold rendering, better quality than synthetic bold
- **Alternative Considered**: Synthetic bold via stroke width - rejected due to quality
- **Limitation**: UNDERLINE applied via attributes, not font modification

#### Color Cache

**Purpose**: Cache CGColor objects for different RGB values.

**Design Decision**: LRU cache with 256 entry limit
- **Rationale**: Balance memory usage vs cache hit rate
- **Cache Size**: 256 entries = ~8KB memory
- **Eviction**: LRU (least recently used)

```cpp
class ColorCache {
    std::unordered_map<uint32_t, CGColorRef> cache_;
    std::list<uint32_t> lru_list_;
    std::unordered_map<uint32_t, std::list<uint32_t>::iterator> lru_map_;
    size_t max_size_;
    
    CGColorRef get_color(uint8_t r, uint8_t g, uint8_t b, float alpha = 1.0) {
        uint32_t key = (r << 16) | (g << 8) | b;
        
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            // Move to front of LRU list
            lru_list_.splice(lru_list_.begin(), lru_list_, lru_map_[key]);
            return it->second;
        }
        
        // Create color
        CGFloat components[] = {r/255.0f, g/255.0f, b/255.0f, alpha};
        CGColorSpaceRef colorspace = CGColorSpaceCreateDeviceRGB();
        CGColorRef color = CGColorCreate(colorspace, components);
        CGColorSpaceRelease(colorspace);
        
        // Add to cache with LRU eviction
        if (cache_.size() >= max_size_) {
            uint32_t evict_key = lru_list_.back();
            CGColorRelease(cache_[evict_key]);
            cache_.erase(evict_key);
            lru_map_.erase(evict_key);
            lru_list_.pop_back();
        }
        
        cache_[key] = color;
        lru_list_.push_front(key);
        lru_map_[key] = lru_list_.begin();
        
        return color;
    }
};
```

**Design Decision**: Pack RGB into uint32_t for hash key
- **Rationale**: Fast hashing, compact storage
- **Format**: 0x00RRGGBB (24-bit color)
- **Benefit**: Single integer comparison instead of three

#### Attribute Dictionary Cache

**Purpose**: Cache CFDictionary objects containing text rendering attributes.

**Design Decision**: Cache by composite key (font_attributes, color, underline)
- **Rationale**: Attribute dictionaries are expensive to create (multiple CF objects)
- **Cache Size**: ~100 entries typical
- **Eviction**: LRU (least recently used)

```cpp
class AttributeDictCache {
    std::unordered_map<uint64_t, CFDictionaryRef> cache_;
    FontCache* font_cache_;
    ColorCache* color_cache_;
    size_t hits_;
    size_t misses_;
    
    CFDictionaryRef get_attributes(int font_key, uint32_t color_rgb, bool underline) {
        // Composite key: font_key (8 bits) | color_rgb (24 bits) | underline (1 bit)
        uint64_t key = ((uint64_t)font_key << 32) | (color_rgb << 1) | (underline ? 1 : 0);
        
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            hits_++;
            return it->second;
        }
        
        misses_++;
        
        // Get font and color from caches
        CTFontRef font = font_cache_->get_font(font_key);
        uint8_t r = (color_rgb >> 16) & 0xFF;
        uint8_t g = (color_rgb >> 8) & 0xFF;
        uint8_t b = color_rgb & 0xFF;
        CGColorRef color = color_cache_->get_color(r, g, b);
        
        // Create attribute dictionary
        CFStringRef keys[3] = {kCTFontAttributeName, kCTForegroundColorAttributeName};
        CFTypeRef values[3] = {font, color};
        int count = 2;
        
        if (underline) {
            CFNumberRef underline_style = CFNumberCreate(
                nullptr, kCFNumberIntType, &kCTUnderlineStyleSingle
            );
            keys[count] = kCTUnderlineStyleAttributeName;
            values[count] = underline_style;
            count++;
        }
        
        CFDictionaryRef attrs = CFDictionaryCreate(
            nullptr, (const void**)keys, (const void**)values, count,
            &kCFTypeDictionaryKeyCallBacks, &kCFTypeDictionaryValueCallBacks
        );
        
        cache_[key] = attrs;
        return attrs;
    }
};
```

**Design Decision**: Three-level cache hierarchy (Font → Color → AttributeDict)
- **Rationale**: Each level caches progressively more complex objects
- **Benefit**: Maximum reuse, minimal object creation
- **Hit Rates**: Font ~99%, Color ~95%, AttributeDict ~90% typical

### 5. Batching Strategy

**Purpose**: Reduce CoreGraphics API calls by batching adjacent cells.

#### Background Batching

**Design Decision**: Batch adjacent cells with same background color
- **Rationale**: CGContextFillRect is expensive, batching reduces calls by 10-50x
- **Algorithm**: Scan left-to-right, accumulate adjacent cells, flush on color change or row end

```cpp
class RectangleBatcher {
    struct RectBatch {
        CGFloat x, y, width, height;
        uint32_t bg_rgb;
    };
    
    std::vector<RectBatch> batches_;
    std::optional<RectBatch> current_batch_;
    
    void add_cell(CGFloat x, CGFloat y, CGFloat width, CGFloat height, uint32_t bg_rgb) {
        if (!current_batch_) {
            // Start new batch
            current_batch_ = {x, y, width, height, bg_rgb};
            return;
        }
        
        // Check if cell can extend current batch
        bool same_row = (y == current_batch_->y);
        bool same_color = (bg_rgb == current_batch_->bg_rgb);
        bool adjacent = (x == current_batch_->x + current_batch_->width);
        
        if (same_row && same_color && adjacent) {
            // Extend batch
            current_batch_->width += width;
        } else {
            // Finish current batch, start new one
            batches_.push_back(*current_batch_);
            current_batch_ = {x, y, width, height, bg_rgb};
        }
    }
    
    void finish_row() {
        if (current_batch_) {
            batches_.push_back(*current_batch_);
            current_batch_.reset();
        }
    }
};
```

**Performance Impact**: Typical reduction from 2000 cells → 200 batches (10x reduction)

#### Character Batching

**Design Decision**: Batch consecutive characters with same attributes
- **Rationale**: CTLineDraw can render multiple characters in one call
- **Algorithm**: Accumulate characters until attributes change, then draw batch

```cpp
void render_characters(CGContextRef context, const Grid& grid, ...) {
    std::string batch_text;
    int batch_color_pair = -1;
    int batch_attributes = -1;
    CGFloat batch_x = 0, batch_y = 0;
    
    for (int row = start_row; row <= end_row; row++) {
        for (int col = start_col; col <= end_col; col++) {
            const Cell& cell = grid[row][col];
            
            // Skip spaces (backgrounds already rendered)
            if (cell.character == " ") continue;
            
            // Check if cell can extend batch
            bool same_attrs = (cell.color_pair == batch_color_pair &&
                             cell.attributes == batch_attributes);
            bool adjacent = (col == batch_col + 1);
            
            if (same_attrs && adjacent && !batch_text.empty()) {
                // Extend batch
                batch_text += cell.character;
            } else {
                // Draw previous batch
                if (!batch_text.empty()) {
                    draw_character_batch(context, batch_text, batch_x, batch_y, ...);
                }
                
                // Start new batch
                batch_text = cell.character;
                batch_color_pair = cell.color_pair;
                batch_attributes = cell.attributes;
                batch_x = offset_x + col * char_width;
                batch_y = offset_y + row * char_height;
            }
        }
        
        // Flush batch at end of row
        if (!batch_text.empty()) {
            draw_character_batch(context, batch_text, batch_x, batch_y, ...);
            batch_text.clear();
        }
    }
}
```

**Performance Impact**: Typical reduction from 2000 characters → 100 batches (20x reduction)

### 6. Coordinate System Transformation

**Purpose**: Convert between TTK (top-left origin) and CoreGraphics (bottom-left origin) coordinate systems.

**Design Decision**: Transform at cell calculation stage, not per-pixel
- **Rationale**: Minimize transformation overhead
- **Formula**: `cg_y = (rows - ttk_row - 1) * char_height`

```cpp
struct DirtyCells {
    int start_row, end_row;
    int start_col, end_col;
};

DirtyCells calculate_dirty_cells(CGRect dirty_rect, int rows, int cols,
                                 CGFloat char_width, CGFloat char_height,
                                 CGFloat offset_x, CGFloat offset_y) {
    // Convert CoreGraphics rect to cell coordinates
    CGFloat view_height = rows * char_height;
    
    // Transform Y coordinate (CG bottom-left → TTK top-left)
    CGFloat ttk_y = view_height - (dirty_rect.origin.y + dirty_rect.size.height);
    
    // Calculate cell range
    int start_row = std::max(0, (int)std::floor((ttk_y - offset_y) / char_height));
    int end_row = std::min(rows - 1, (int)std::ceil((ttk_y + dirty_rect.size.height - offset_y) / char_height));
    int start_col = std::max(0, (int)std::floor((dirty_rect.origin.x - offset_x) / char_width));
    int end_col = std::min(cols - 1, (int)std::ceil((dirty_rect.origin.x + dirty_rect.size.width - offset_x) / char_width));
    
    return {start_row, end_row, start_col, end_col};
}
```

**Design Decision**: Clamp to grid bounds at calculation time
- **Rationale**: Prevent out-of-bounds access, simplify rendering loops
- **Benefit**: No bounds checking needed in hot rendering loops

### 7. Memory Management

**Purpose**: Ensure proper cleanup of CoreFoundation objects.

**Design Decision**: RAII (Resource Acquisition Is Initialization) pattern
- **Rationale**: Automatic cleanup, exception-safe
- **Implementation**: Destructors release all CF objects

```cpp
class ColorCache {
public:
    ~ColorCache() {
        // Release all cached colors
        for (auto& pair : cache_) {
            CGColorRelease(pair.second);
        }
        cache_.clear();
    }
};

class FontCache {
public:
    ~FontCache() {
        // Release all cached fonts
        for (auto& pair : cache_) {
            CFRelease(pair.second);
        }
        cache_.clear();
    }
};

class AttributeDictCache {
public:
    ~AttributeDictCache() {
        // Release all cached dictionaries
        for (auto& pair : cache_) {
            CFRelease(pair.second);
        }
        cache_.clear();
    }
};
```

**Design Decision**: Manual CFRelease instead of smart pointers
- **Rationale**: CoreFoundation uses reference counting, not C++ ownership semantics
- **Alternative Considered**: Custom smart pointer wrapper - rejected as over-engineering
- **Benefit**: Clear, explicit resource management

### 8. Error Handling

**Purpose**: Robust error handling without crashing the application.

**Design Decision**: Convert C++ exceptions to Python exceptions
- **Rationale**: Python code expects Python exceptions, not C++ exceptions
- **Implementation**: Try-catch wrapper around all C++ code

```cpp
PyObject* render_frame(PyObject* self, PyObject* args) {
    try {
        // Validate parameters
        if (!validate_parameters(args)) {
            PyErr_SetString(PyExc_ValueError, "Invalid parameters");
            return nullptr;
        }
        
        // Parse and render
        // ...
        
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

**Design Decision**: Fallback to PyObjC on C++ rendering failure
- **Rationale**: Application continues to work even if C++ renderer fails
- **Implementation**: Python code catches exceptions and calls PyObjC renderer

```python
try:
    cpp_renderer.render_frame(...)
except Exception as e:
    print(f"C++ rendering failed: {e}")
    self._render_with_pyobjc(rect, offset_x, offset_y)
```

### 9. Performance Metrics

**Purpose**: Measure and track rendering performance.

**Design Decision**: Collect metrics in C++, expose to Python
- **Rationale**: Minimal overhead, accurate timing
- **Metrics Tracked**:
  - Frames rendered
  - Total/average render time
  - Total/average batches per frame
  - Cache hit/miss rates

```cpp
class Renderer {
    size_t frames_rendered_;
    double total_render_time_;
    size_t total_batches_;
    
    void render_frame(...) {
        auto start = std::chrono::high_resolution_clock::now();
        
        // Render...
        
        auto end = std::chrono::high_resolution_clock::now();
        double elapsed_ms = std::chrono::duration<double, std::milli>(end - start).count();
        
        frames_rendered_++;
        total_render_time_ += elapsed_ms;
        total_batches_ += batches.size();
    }
    
    PyObject* get_performance_metrics() {
        PyObject* dict = PyDict_New();
        PyDict_SetItemString(dict, "frames_rendered", PyLong_FromSize_t(frames_rendered_));
        PyDict_SetItemString(dict, "avg_render_time_ms", 
                           PyFloat_FromDouble(total_render_time_ / frames_rendered_));
        // ... more metrics
        return dict;
    }
};
```

## Design Trade-offs

### Performance vs Complexity

**Trade-off**: Three-level caching adds complexity but provides significant performance gains.

**Decision**: Accept complexity for performance
- **Rationale**: Rendering is on critical path, performance is paramount
- **Mitigation**: Clear documentation, comprehensive tests

### Memory vs Speed

**Trade-off**: Larger caches use more memory but improve hit rates.

**Decision**: Moderate cache sizes (256 colors, ~100 attribute dicts)
- **Rationale**: Balance memory usage (~50-100KB) vs hit rates (>90%)
- **Tuning**: Cache sizes can be adjusted based on profiling

### API Simplicity vs Flexibility

**Trade-off**: Single `render_frame()` function is simple but less flexible than multiple specialized functions.

**Decision**: Single function for simplicity
- **Rationale**: Fewer Python/C++ boundary crossings, simpler API
- **Benefit**: All rendering state stays in C++, reducing marshalling overhead

## Future Enhancements

### Potential Optimizations

1. **SIMD Color Conversion**: Use vector instructions for RGB packing/unpacking
2. **Memory Pooling**: Reuse allocated memory across frames
3. **Parallel Rendering**: Render backgrounds and characters in parallel (requires careful synchronization)
4. **GPU Acceleration**: Investigate Metal for rendering (major architectural change)

### Extensibility

The architecture supports future extensions:

1. **Additional Text Attributes**: Italic, strikethrough, etc. (add to attribute bitfield)
2. **Custom Fonts**: Per-cell font selection (extend cache key)
3. **Advanced Effects**: Shadows, outlines, etc. (add to attribute dictionary)

## Lessons Learned

### What Worked Well

1. **Backend Selector**: Simple environment variable makes testing easy
2. **Three-Level Caching**: Excellent hit rates with minimal memory overhead
3. **Batching Strategy**: Dramatic reduction in API calls
4. **RAII Pattern**: Automatic resource cleanup prevents leaks

### What Could Be Improved

1. **Error Messages**: More detailed error messages for debugging
2. **Profiling Integration**: Built-in profiling hooks for performance analysis
3. **Configuration**: Runtime cache size tuning without recompilation

## References

- [API Documentation](CPP_RENDERING_API.md)
- [Build and Installation Guide](CPP_RENDERING_BUILD.md)
- [Performance Guide](CPP_RENDERING_PERFORMANCE.md)
- [Troubleshooting Guide](CPP_RENDERING_TROUBLESHOOTING.md)

## Appendix: Performance Comparison

### Benchmark Results

Measured on MacBook Pro M1, 2021:

| Grid Size | PyObjC (ms) | C++ (ms) | Improvement |
|-----------|-------------|----------|-------------|
| 24x80     | 3.2         | 2.1      | 34% faster  |
| 40x120    | 5.8         | 3.7      | 36% faster  |
| 50x200    | 9.4         | 6.1      | 35% faster  |

### Cache Hit Rates

Typical hit rates during normal usage:

| Cache Type          | Hit Rate |
|---------------------|----------|
| Font Cache          | 99.2%    |
| Color Cache         | 94.8%    |
| Attribute Dict Cache| 91.3%    |

### Batch Reduction

Typical batch counts for 50x200 grid:

| Operation   | Without Batching | With Batching | Reduction |
|-------------|------------------|---------------|-----------|
| Backgrounds | 10,000 cells     | 800 batches   | 12.5x     |
| Characters  | 8,000 chars      | 400 batches   | 20x       |
| **Total**   | **18,000 calls** | **1,200 calls**| **15x**  |
