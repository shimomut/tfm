# Design Document

## Overview

The CoreGraphics backend's drawRect_() method contains a performance bottleneck in the character drawing phase (Phase 2). Profiling reveals that drawing characters takes approximately 0.03 seconds (30ms) for a full-screen update. This design document analyzes the root causes and proposes optimizations to reduce this time to under 0.01 seconds (10ms).

## Architecture

The current rendering pipeline in drawRect_() consists of five phases:

1. **Calculate dirty region** (t1-t0): Determine which cells need redrawing
2. **Iterate and batch backgrounds** (t2-t1): Loop through cells, accumulate into batches ✅ OPTIMIZED (0.65ms)
3. **Draw batched backgrounds** (t3-t2): Render all background rectangles
4. **Draw characters** (t4-t3): Render all non-space characters ⚠️ BOTTLENECK (30ms)
5. **Draw cursor** (t5-t4): Render cursor if visible

The bottleneck occurs in phase 4, where we iterate through every cell in the dirty region and create NSAttributedString objects for non-space characters.

## Components and Interfaces

### Current Implementation Analysis

The character drawing code (lines 2015-2070) performs these operations for each non-space cell:

```python
for row in range(start_row, end_row):
    for col in range(start_col, end_col):
        # 1. Grid access
        char, color_pair, attributes = grid[row][col]
        
        # 2. Skip spaces
        if char == ' ':
            continue
        
        # 3. Calculate position (2 multiplications)
        x = col * char_width
        y = (rows - row - 1) * char_height
        
        # 4. Color pair lookup
        fg_rgb, bg_rgb = color_pairs.get(color_pair, color_pairs[0])
        
        # 5. Handle reverse video
        if attributes & TextAttribute.REVERSE:
            fg_rgb, bg_rgb = bg_rgb, fg_rgb
        
        # 6. Get cached color
        fg_color = self.backend._color_cache.get_color(*fg_rgb)
        
        # 7. Get cached font
        font = self.backend._font_cache.get_font(attributes)
        
        # 8. Build attributes dictionary (3-4 key-value pairs)
        text_attributes = {
            Cocoa.NSFontAttributeName: font,
            Cocoa.NSForegroundColorAttributeName: fg_color
        }
        if attributes & TextAttribute.UNDERLINE:
            text_attributes[Cocoa.NSUnderlineStyleAttributeName] = (
                Cocoa.NSUnderlineStyleSingle
            )
        
        # 9. Create NSAttributedString (object allocation)
        attr_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
            char,
            text_attributes
        )
        
        # 10. Draw character (CoreGraphics API call)
        attr_string.drawAtPoint_(Cocoa.NSMakePoint(x, y))
```

### Performance Analysis

For a 24x80 grid (1920 cells), assuming ~50% are non-space characters (960 characters):
- **960 grid accesses**: `grid[row][col]`
- **1920 multiplications**: 2 per cell for x and y calculations
- **960 dictionary lookups**: `color_pairs.get()`
- **960 conditional checks**: reverse video and underline
- **960 cache lookups**: font and color cache
- **960 dictionary allocations**: `text_attributes` dictionary
- **960 NSAttributedString creations**: Object allocation and initialization
- **960 CoreGraphics API calls**: `drawAtPoint_()`

The primary bottlenecks are:
1. **NSAttributedString creation overhead**: Creating 960 objects per frame is expensive
2. **Dictionary allocations**: Creating 960 `text_attributes` dictionaries
3. **Repeated calculations**: Y-coordinate calculated for every cell (same as Phase 1)
4. **Attribute access overhead**: Repeated access to `self.backend` attributes

## Data Models

No changes to data models are required. The optimization focuses on algorithmic improvements and reducing object creation overhead.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After reviewing the acceptance criteria, I identified the following testable properties:

1. Performance property (1.1): Character drawing completes in under 10ms
2. Correctness property (3.5, 4.1): Optimized code produces identical visual output
3. Performance improvement property (4.2, 4.4): Optimized version is measurably faster

Properties 3.5 and 4.1 are redundant - they both test that the optimized code produces identical output. We can combine these into a single comprehensive property.

Properties 4.2 and 4.4 are also redundant - they both test performance improvement. We can combine these into a single property.

After eliminating redundancy, we have three unique properties:
1. Performance target property
2. Correctness property (identical output)
3. Performance improvement property

### Correctness Properties

Property 1: Character drawing performance target
*For any* grid state with a 24x80 dirty region containing non-space characters, the character drawing phase should complete in under 0.01 seconds (10ms)
**Validates: Requirements 1.1**

Property 2: Visual output equivalence
*For any* grid state and dirty region, the optimized implementation should produce identical visual output to the original implementation
**Validates: Requirements 3.5, 4.1**

Property 3: Performance improvement
*For any* grid state with a full-screen dirty region, the optimized implementation should be measurably faster than the original implementation (at least 50% faster)
**Validates: Requirements 4.2, 4.4**

## Proposed Optimizations

### Optimization 1: Cache Frequently Accessed Attributes (Similar to Phase 1)

**Problem**: `self.backend.char_width`, `self.backend.char_height`, `self.backend.rows`, etc. are accessed in every iteration.

**Solution**: Reuse the cached values from Phase 1 or cache them again at the start of Phase 2:

```python
# Already cached in Phase 1, reuse them
char_width = self.backend.char_width
char_height = self.backend.char_height
rows = self.backend.rows
grid = self.backend.grid
color_pairs = self.backend.color_pairs
```

**Expected Impact**: Reduces attribute access overhead by ~960 accesses per frame.

### Optimization 2: Pre-calculate Row Y-Coordinates (Similar to Phase 1)

**Problem**: `(rows - row - 1) * char_height` is recalculated for every cell in the same row.

**Solution**: Calculate y-coordinate once per row:

```python
for row in range(start_row, end_row):
    y = (rows - row - 1) * char_height  # Calculate once per row
    for col in range(start_col, end_col):
        # ... rest of loop
```

**Expected Impact**: Reduces multiplications from 1920 to 24 (98% reduction).

### Optimization 3: Cache Attribute Dictionaries

**Problem**: Creating a new dictionary for every character is expensive. Most characters use the same font and color combinations.

**Solution**: Create a cache of attribute dictionaries keyed by (font, color, underline):

```python
# At class level
self._attr_dict_cache = {}

# In drawing loop
cache_key = (font, fg_color, bool(attributes & TextAttribute.UNDERLINE))
if cache_key not in self._attr_dict_cache:
    text_attributes = {
        Cocoa.NSFontAttributeName: font,
        Cocoa.NSForegroundColorAttributeName: fg_color
    }
    if attributes & TextAttribute.UNDERLINE:
        text_attributes[Cocoa.NSUnderlineStyleAttributeName] = (
            Cocoa.NSUnderlineStyleSingle
        )
    self._attr_dict_cache[cache_key] = text_attributes
else:
    text_attributes = self._attr_dict_cache[cache_key]
```

**Expected Impact**: Reduces dictionary allocations from 960 to ~10-20 per frame (95-98% reduction).

### Optimization 4: Batch Character Drawing

**Problem**: Creating 960 NSAttributedString objects and making 960 drawAtPoint_() calls is expensive.

**Solution**: Investigate batching characters with the same attributes into a single NSAttributedString:

```python
# Accumulate characters with same attributes
char_batch = []
for col in range(start_col, end_col):
    if same_attributes:
        char_batch.append(char)
    else:
        # Draw accumulated batch
        draw_batch(char_batch)
        char_batch = [char]
```

**Expected Impact**: Potentially significant reduction in NSAttributedString creations and API calls.

**Trade-off**: More complex code, may not work well with variable-width fonts or complex layouts.

### Optimization 5: Use NSString drawAtPoint:withAttributes: Directly

**Problem**: Creating NSAttributedString objects adds overhead.

**Solution**: Use NSString's drawAtPoint:withAttributes: method directly:

```python
# Instead of creating NSAttributedString
ns_string = Cocoa.NSString.stringWithString_(char)
ns_string.drawAtPoint_withAttributes_(
    Cocoa.NSMakePoint(x, y),
    text_attributes
)
```

**Expected Impact**: Eliminates NSAttributedString allocation overhead, potentially 20-30% faster.

## Implementation Strategy

We will implement optimizations incrementally and measure the impact of each:

1. **Phase 1**: Implement Optimizations 1-2 (caching, pre-calculation)
   - Low-risk, proven optimizations from Phase 1
   - Measure performance improvement
   - Verify correctness

2. **Phase 2**: Implement Optimization 3 (attribute dictionary caching)
   - Medium complexity, high potential impact
   - Measure performance improvement
   - Verify correctness

3. **Phase 3**: Evaluate Optimization 5 (NSString direct drawing)
   - Test if it provides significant improvement
   - Simpler than batching (Optimization 4)
   - Measure actual impact

4. **Phase 4**: Consider Optimization 4 (batching) if needed
   - Only if we haven't reached the 10ms target
   - Most complex, evaluate trade-offs carefully

## Error Handling

The optimization should maintain the same error handling behavior as the original implementation:
- Handle missing color pairs gracefully (fall back to default)
- Handle missing fonts gracefully (fall back to default)
- Maintain exception handling for any unexpected errors

## Testing Strategy

### Unit Testing

Unit tests will verify:
- Correct caching of attributes
- Correct pre-calculation of y-coordinates
- Correct attribute dictionary caching
- Edge cases (empty dirty region, single character, full screen)

### Property-Based Testing

Property-based tests will verify the three correctness properties:

1. **Performance Target Property Test**:
   - Generate random grid states with various characters
   - Measure character drawing time for full-screen dirty region
   - Assert time < 0.01 seconds (10ms)
   - Run 100 iterations to account for variance

2. **Visual Output Equivalence Property Test**:
   - Generate random grid states
   - Run both original and optimized implementations
   - Compare the visual output (same characters, positions, colors, attributes)
   - Run 100 iterations with different grid states

3. **Performance Improvement Property Test**:
   - Generate random grid states
   - Measure time for both implementations
   - Assert optimized is at least 50% faster
   - Run 100 iterations to account for variance

### Integration Testing

Integration tests will:
- Run the full drawRect_() method with optimized character drawing
- Verify visual output matches original implementation
- Use existing visual correctness tests
- Measure end-to-end rendering performance

## Performance Targets

Based on the analysis, we expect the following improvements:

| Optimization | Expected Time Reduction |
|-------------|------------------------|
| Baseline (current) | 30.0ms |
| After Opt 1-2 (caching + pre-calc) | 25.0ms (-17%) |
| After Opt 3 (attr dict cache) | 15.0ms (-40%) |
| After Opt 5 (NSString direct) | 8.0ms (-47%) |
| **Target** | **< 10.0ms** |

These are estimates based on the analysis. Actual results will be measured during implementation.

## Risks and Mitigation

### Risk 1: Optimizations Don't Achieve Target

**Mitigation**: If optimizations 1-3 and 5 don't reach the target, we have optimization 4 (batching) as a fallback. If that's still insufficient, we may need to consider:
- Using Core Text API directly (lower-level than NSAttributedString)
- Implementing character drawing in Objective-C or Swift
- Caching rendered character glyphs as images

### Risk 2: Correctness Regression

**Mitigation**: Comprehensive property-based testing will catch any correctness issues. We'll run 100+ iterations with random grid states to ensure the optimized code produces identical results.

### Risk 3: Code Maintainability

**Mitigation**: We'll prioritize optimizations that maintain code clarity. Optimization 4 (batching) will only be implemented if necessary, and we'll document the trade-offs clearly.

### Risk 4: Cache Memory Overhead

**Mitigation**: The attribute dictionary cache will be bounded in size (limited by the number of unique font/color/underline combinations). We'll monitor memory usage and implement cache eviction if needed.

## Future Enhancements

After achieving the performance target, we can consider:
1. **Glyph caching**: Cache rendered character glyphs as images
2. **Core Text API**: Use lower-level Core Text for more control
3. **Parallel processing**: Use multiple threads for large dirty regions
4. **GPU acceleration**: Investigate using Metal for text rendering (future spec)
