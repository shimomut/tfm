# Character Drawing Optimization Design

## Overview

This design addresses the performance bottleneck in the CoreGraphics backend's character drawing phase. Current profiling shows the "Draw characters" section (t4-t3) takes approximately 30ms for a full-screen update, which is unacceptable for responsive UI rendering. The goal is to reduce this to under 10ms through systematic optimization of NSAttributedString creation, attribute dictionary management, and character iteration patterns.

The optimization will focus on minimizing object allocations, reducing dictionary operations, and implementing strategic caching while maintaining pixel-perfect visual compatibility with the current implementation.

## Architecture

### Current Implementation Analysis

The character drawing phase currently follows this pattern:

1. **Iterate through dirty region cells** - Loop over rows and columns in the dirty rectangle
2. **Skip space characters** - Optimization to avoid drawing spaces
3. **Build attribute dictionary** - Create a new dictionary for each character with NSFont, NSForegroundColor, and optional NSUnderlineStyle
4. **Create NSAttributedString** - Instantiate a new attributed string for each character
5. **Draw to context** - Render the attributed string at the calculated position

**Identified Bottlenecks:**
- Dictionary allocation for every non-space character
- NSAttributedString object creation for every character
- Repeated font and color object lookups from caches
- Python dictionary operations for attribute building

### Proposed Architecture

The optimized architecture will implement a multi-level caching and batching strategy:

```
┌─────────────────────────────────────────────────────────────┐
│            Character Drawing Phase (Phase 2)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │   Attribute Dictionary Cache                          │ │
│  │   Key: (font_key, color_rgb, underline)              │ │
│  │   Value: Pre-built NSDictionary                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                           ↓                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │   NSAttributedString Cache                            │ │
│  │   Key: (string, font_key, color_rgb, underline)      │ │
│  │   Value: Pre-built NSAttributedString                 │ │
│  └───────────────────────────────────────────────────────┘ │
│                           ↓                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │   Character Drawing Loop with Batching                │ │
│  │   - Iterate dirty region row by row                   │ │
│  │   - Identify runs of characters with same attributes  │ │
│  │   - Batch continuous characters into single string    │ │
│  │   - Lookup/create cached NSAttributedString           │ │
│  │   - Single drawAtPoint_ call per batch                │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Architectural Changes:**

1. **Character Batching:** Instead of drawing each character individually, identify continuous runs of characters with identical attributes and draw them as a single string
2. **NSAttributedString Caching:** Cache pre-built NSAttributedString objects to eliminate repeated instantiation overhead
3. **Dual-Level Caching:** Attribute dictionaries cached for building new strings, NSAttributedString objects cached for reuse

## Components and Interfaces

### 1. Attribute Dictionary Cache

**Purpose:** Eliminate repeated dictionary allocations by caching pre-built attribute dictionaries.

**Interface:**
```python
class AttributeDictCache:
    def __init__(self, font_cache: FontCache, color_cache: ColorCache):
        self._cache: Dict[Tuple[str, Tuple[int, int, int], bool], NSDictionary] = {}
        self._font_cache = font_cache
        self._color_cache = color_cache
    
    def get_attributes(self, font_key: str, color_rgb: Tuple[int, int, int], 
                      underline: bool) -> NSDictionary:
        """Get or create cached attribute dictionary."""
        pass
    
    def clear(self):
        """Clear the cache when needed."""
        pass
```

**Key Design Decisions:**
- Cache key uses tuple of (font_key, color_rgb, underline) for fast lookup
- Pre-builds NSDictionary objects to avoid Python dict → NSDictionary conversion overhead
- Integrates with existing FontCache and ColorCache
- Cache clearing strategy: clear on terminal resize or color scheme change

### 2. NSAttributedString Cache

**Purpose:** Eliminate repeated NSAttributedString instantiation by caching pre-built attributed strings.

**Interface:**
```python
class AttributedStringCache:
    def __init__(self, attr_dict_cache: AttributeDictCache):
        self._cache: Dict[Tuple[str, str, Tuple[int, int, int], bool], NSAttributedString] = {}
        self._attr_dict_cache = attr_dict_cache
        self._max_cache_size = 1000  # Limit cache growth
    
    def get_attributed_string(self, text: str, font_key: str, 
                             color_rgb: Tuple[int, int, int], 
                             underline: bool) -> NSAttributedString:
        """Get or create cached NSAttributedString."""
        pass
    
    def clear(self):
        """Clear the cache when needed."""
        pass
```

**Key Design Decisions:**
- Cache key includes the actual text string plus all attributes
- Implements LRU eviction when cache exceeds max_cache_size
- Particularly effective for repeated strings (common in file listings: "..", ".", common extensions)
- Integrates with AttributeDictCache for building new strings
- Cache clearing strategy: clear on terminal resize or color scheme change

**Performance Impact:**
- Eliminates NSAttributedString.alloc().initWithString_attributes_() overhead for repeated strings
- Most effective for common patterns: directory names, file extensions, repeated UI elements
- Batched strings also benefit from caching when patterns repeat

### 3. Optimized Character Drawing Loop with Batching

**Current Pattern (One drawAtPoint_ per character):**
```python
for row in range(dirty_top, dirty_bottom):
    for col in range(dirty_left, dirty_right):
        char = grid[row][col]['char']
        if char == ' ':
            continue
        
        # Build attributes dict (SLOW)
        attrs = {
            NSFontAttributeName: font_cache.get_font(...),
            NSForegroundColorAttributeName: color_cache.get_color(...),
        }
        if underline:
            attrs[NSUnderlineStyleAttributeName] = NSUnderlineStyleSingle
        
        # Create attributed string (SLOW)
        attr_str = NSAttributedString.alloc().initWithString_attributes_(char, attrs)
        attr_str.drawAtPoint_(NSPoint(x, y))  # One call per character
```

**Optimized Pattern (Batching + Caching):**
```python
for row in range(dirty_top, dirty_bottom):
    col = dirty_left
    while col < dirty_right:
        # Skip leading spaces
        while col < dirty_right and grid[row][col]['char'] == ' ':
            col += 1
        
        if col >= dirty_right:
            break
        
        # Start of a run - get attributes for first character
        start_col = col
        start_attrs = (font_key, color_rgb, underline)
        batch_chars = []
        
        # Collect continuous characters with same attributes
        while col < dirty_right:
            char = grid[row][col]['char']
            if char == ' ':
                break
            
            current_attrs = (font_key, color_rgb, underline)
            if current_attrs != start_attrs:
                break
            
            batch_chars.append(char)
            col += 1
        
        # Draw the batched string with cached NSAttributedString
        if batch_chars:
            batch_text = ''.join(batch_chars)
            attr_str = attributed_string_cache.get_attributed_string(
                batch_text, *start_attrs
            )
            attr_str.drawAtPoint_(NSPoint(x_start, y))  # One call per batch
```

**Key Optimizations:**
1. **Batching:** Multiple characters drawn with single drawAtPoint_() call
2. **NSAttributedString Caching:** Reuse pre-built attributed strings
3. **Attribute Dictionary Caching:** Fast attribute lookup for new strings
4. **Space Skipping:** Skip entire runs of spaces efficiently

**Performance Impact:**
- Reduces drawAtPoint_() calls from ~1920 (24x80) to ~50-200 (depending on attribute changes)
- Eliminates most NSAttributedString instantiations through caching
- Particularly effective for file listings with repeated patterns

### 4. Integration with Existing Caches

The new caching layers will integrate with:

- **FontCache** - Provides NSFont objects for different text attributes
- **ColorCache** - Provides NSColor objects for RGB values
- **Existing drawRect_() structure** - Changes to character drawing loop, but maintains overall flow

**Cache Hierarchy:**
```
FontCache ──┐
            ├──> AttributeDictCache ──> AttributedStringCache ──> Drawing Loop
ColorCache ─┘
```

**Cache Lifecycle:**
- All caches cleared on terminal resize
- All caches cleared on color scheme change
- AttributedStringCache implements LRU eviction for memory management

## Data Models

### Attribute Dictionary Cache Entry

```python
AttrDictCacheKey = Tuple[str, Tuple[int, int, int], bool]
# (font_key, (r, g, b), underline)

AttrDictCacheValue = NSDictionary
# Pre-built dictionary with NSFont, NSForegroundColor, optional NSUnderlineStyle
```

**Cache Key Components:**
- `font_key`: String identifying font attributes (e.g., "normal", "bold", "bold_underline")
- `color_rgb`: Tuple of (red, green, blue) values (0-255)
- `underline`: Boolean indicating if underline style should be applied

**Cache Value:**
- Immutable NSDictionary containing all required text attributes
- Created once and reused for all characters with same attributes

### NSAttributedString Cache Entry

```python
AttrStringCacheKey = Tuple[str, str, Tuple[int, int, int], bool]
# (text, font_key, (r, g, b), underline)

AttrStringCacheValue = NSAttributedString
# Pre-built NSAttributedString ready for drawing
```

**Cache Key Components:**
- `text`: The actual string content (single character or batched string)
- `font_key`: String identifying font attributes
- `color_rgb`: Tuple of (red, green, blue) values (0-255)
- `underline`: Boolean indicating if underline style should be applied

**Cache Value:**
- Immutable NSAttributedString object ready for drawAtPoint_()
- Eliminates alloc().initWithString_attributes_() overhead

**Cache Size Management:**
- Maximum 1000 entries (configurable)
- LRU eviction when limit reached
- Common strings cached: "..", ".", file extensions, repeated directory names

### Performance Metrics Data Model

```python
@dataclass
class CharacterDrawingMetrics:
    total_time: float                    # Total time for character drawing phase (t4-t3)
    characters_drawn: int                # Number of non-space characters drawn
    batches_drawn: int                   # Number of drawAtPoint_() calls made
    avg_batch_size: float                # Average characters per batch
    attr_dict_cache_hits: int           # Attribute dict cache hits
    attr_dict_cache_misses: int         # Attribute dict cache misses
    attr_string_cache_hits: int         # NSAttributedString cache hits
    attr_string_cache_misses: int       # NSAttributedString cache misses
    avg_time_per_char: float            # Average time per character (microseconds)
    avg_time_per_batch: float           # Average time per batch (microseconds)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Visual Output Equivalence
*For any* grid state and dirty region, the optimized character drawing implementation SHALL produce pixel-identical output to the original implementation.

**Validates: Requirements 3.5**

**Testing Strategy:** Capture screenshots before and after optimization, compare pixel-by-pixel.

### Property 2: Performance Improvement
*For any* full-screen character drawing operation, the optimized implementation SHALL complete in under 10ms (compared to baseline ~30ms).

**Validates: Requirements 1.1**

**Testing Strategy:** Run performance test with maximum character workload, measure t4-t3 delta.

### Property 3: Attribute Dictionary Cache Correctness
*For any* sequence of character drawing operations with identical attributes, the attribute dictionary cache SHALL return the same NSDictionary object on subsequent lookups.

**Validates: Requirements 3.4**

**Testing Strategy:** Verify cache returns same object reference for identical keys.

### Property 5: NSAttributedString Cache Correctness
*For any* sequence of character drawing operations with identical text and attributes, the NSAttributedString cache SHALL return the same NSAttributedString object on subsequent lookups.

**Validates: Requirements 3.4**

**Testing Strategy:** Verify cache returns same object reference for identical (text, attributes) keys.

### Property 6: Batching Correctness
*For any* row of characters, batching continuous characters with identical attributes SHALL produce the same visual output as drawing each character individually.

**Validates: Requirements 3.5**

**Testing Strategy:** Compare output of batched vs. individual character drawing.

### Property 4: Attribute Dictionary Completeness
*For any* cached attribute dictionary, it SHALL contain all required keys (NSFont, NSForegroundColor, and NSUnderlineStyle when applicable).

**Validates: Requirements 3.1, 3.5**

**Testing Strategy:** Inspect cached dictionaries to verify all required attributes are present.

## Error Handling

### Cache Management Errors

**Scenario:** Cache grows too large in memory
- **Detection:** Monitor cache size during operation
- **Response:** Implement LRU eviction or clear cache on memory pressure
- **Recovery:** Cache will rebuild entries as needed

**Scenario:** Font or color cache returns None
- **Detection:** Check return values from font_cache.get_font() and color_cache.get_color()
- **Response:** Log warning and skip character drawing for that cell
- **Recovery:** Character will be drawn on next frame when cache is populated

### Drawing Errors

**Scenario:** NSAttributedString creation fails
- **Detection:** Catch exceptions during initWithString_attributes_()
- **Response:** Log error with character and attributes, continue with next character
- **Recovery:** Skip problematic character, maintain rendering stability

**Scenario:** Drawing outside bounds
- **Detection:** Validate x, y coordinates before drawAtPoint_()
- **Response:** Skip drawing for out-of-bounds characters
- **Recovery:** Continue with remaining characters in dirty region

## Testing Strategy

### Unit Testing

**Test Coverage:**
1. **Attribute Dictionary Cache Tests**
   - Test cache hit/miss behavior
   - Verify correct attribute dictionary construction
   - Test cache clearing functionality
   - Verify integration with font and color caches

2. **NSAttributedString Cache Tests**
   - Test cache hit/miss behavior for repeated strings
   - Verify LRU eviction when cache limit reached
   - Test cache clearing functionality
   - Verify correct attributed string construction

3. **Character Batching Tests**
   - Test identification of continuous character runs
   - Verify correct batch boundary detection (attribute changes)
   - Test space skipping within batching logic
   - Verify correct coordinate calculations for batches

4. **Character Drawing Loop Tests**
   - Test batching with various attribute patterns
   - Verify correct attribute lookup
   - Test dirty region iteration
   - Verify coordinate calculations

5. **Edge Cases**
   - Empty dirty region
   - Single character dirty region
   - Full-screen dirty region
   - Row with all same attributes (maximum batching)
   - Row with all different attributes (no batching benefit)
   - Alternating attributes (worst case for batching)
   - Rows with leading/trailing spaces

### Property-Based Testing

**Property Tests:**
1. **Visual Equivalence Property Test**
   - Generate random grid states with various attributes
   - Render with both original and optimized implementations
   - Compare output pixel-by-pixel
   - **Validates: Property 1**

2. **Performance Property Test**
   - Generate maximum workload scenarios (full grid, all non-space)
   - Measure character drawing phase time
   - Verify time is consistently under 10ms threshold
   - **Validates: Property 2**

3. **Attribute Dictionary Cache Consistency Property Test**
   - Generate random sequences of attribute lookups
   - Verify cache returns consistent results for same keys
   - Verify cache hit rate improves with repeated patterns
   - **Validates: Property 3**

4. **NSAttributedString Cache Consistency Property Test**
   - Generate random sequences of (text, attributes) lookups
   - Verify cache returns consistent results for same keys
   - Verify LRU eviction maintains most-used entries
   - **Validates: Property 5**

5. **Batching Correctness Property Test**
   - Generate random rows with various attribute patterns
   - Compare batched drawing output to individual character drawing
   - Verify pixel-identical results
   - **Validates: Property 6**

### Performance Testing

**Baseline Measurement:**
- Create test scenario with 24x80 grid filled with non-space characters
- Apply various color pairs, bold, underline, and reverse attributes
- Measure t4-t3 time delta (expected: ~30ms)
- Record as baseline for comparison

**Optimization Measurement:**
- Run same test scenario with optimized implementation
- Measure t4-t3 time delta (target: <10ms)
- Calculate improvement percentage
- Verify visual output matches baseline

**Test Script:** `test/test_character_drawing_performance.py`
**Demo Script:** `demo/demo_character_drawing_optimization.py`

### Integration Testing

**Full Rendering Pipeline:**
1. Test character drawing optimization within complete drawRect_() flow
2. Verify all rendering phases work correctly together
3. Test with real TFM usage scenarios (file browsing, text viewing)
4. Verify no visual regressions in actual application use

**Cache Integration:**
1. Test attribute dict cache with existing font cache
2. Test attribute dict cache with existing color cache
3. Test NSAttributedString cache with attribute dict cache
4. Verify all caches clear on terminal resize
5. Verify all caches clear on color scheme change
6. Test LRU eviction in NSAttributedString cache under memory pressure

## Implementation Notes

### Optimization Priorities

1. **Highest Impact:** Character batching (reduces drawAtPoint_() calls by 10-40x)
2. **High Impact:** NSAttributedString caching (eliminates repeated instantiation)
3. **High Impact:** Attribute dictionary caching (eliminates dictionary operations)
4. **Medium Impact:** Efficient space skipping in batching logic
5. **Low Impact:** Loop micro-optimizations (already efficient)

**Expected Performance Gains:**
- Batching: 50-70% reduction in drawing time (fewer CoreGraphics calls)
- NSAttributedString caching: 20-30% additional reduction (for repeated patterns)
- Attribute dictionary caching: 10-15% additional reduction (faster string creation)
- Combined: 70-85% total reduction (30ms → 5-9ms)

### Compatibility Considerations

- Maintain compatibility with existing FontCache and ColorCache interfaces
- No changes required to grid data structure
- Minimal changes to drawRect_() method signature
- Cache clearing hooks into existing resize and color scheme change events

### Performance Monitoring

Add instrumentation to track:
- Attribute dictionary cache hit/miss rates
- NSAttributedString cache hit/miss rates
- Average batch size (characters per drawAtPoint_() call)
- Number of batches per frame
- Average time per character
- Average time per batch
- Total characters drawn per frame
- Cache sizes and memory usage
- Batching efficiency (actual vs. theoretical maximum)

### Future Enhancements

Potential further optimizations (out of scope for this feature):
- GPU-accelerated text rendering using Metal
- Pre-rendered glyph atlas for common characters
- Incremental dirty region tracking to minimize redraws
- Multi-threaded batch preparation (prepare batches while drawing previous frame)
- Adaptive cache sizing based on available memory

## Dependencies

- **Existing Components:**
  - FontCache (src/tfm_backend_coregraphics.py)
  - ColorCache (src/tfm_backend_coregraphics.py)
  - CoreGraphicsBackend.drawRect_() method
  
- **External Libraries:**
  - PyObjC (Cocoa, AppKit, Foundation)
  - CoreGraphics framework

- **Testing Dependencies:**
  - pytest for unit tests
  - Hypothesis for property-based tests
  - Performance profiling tools (cProfile, time module)

## Success Criteria

1. **Performance:** Character drawing phase (t4-t3) completes in <10ms for full-screen updates
2. **Correctness:** Pixel-identical visual output compared to original implementation
3. **Stability:** No crashes or visual artifacts during normal operation
4. **Maintainability:** Code remains clean and well-documented
5. **Test Coverage:** All properties verified through automated tests
