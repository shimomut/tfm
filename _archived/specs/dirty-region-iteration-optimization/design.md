# Design Document

## Overview

The CoreGraphics backend's drawRect_() method contains a critical performance bottleneck in the dirty region iteration phase. Profiling reveals that iterating through cells and accumulating them into batches takes approximately 0.2 seconds for a full-screen update (24x80 = 1920 cells). This design document analyzes the root causes and proposes optimizations to reduce this time to under 0.05 seconds.

## Architecture

The current rendering pipeline in drawRect_() consists of five phases:

1. **Calculate dirty region** (t1-t0): Determine which cells need redrawing
2. **Iterate and batch backgrounds** (t2-t1): Loop through cells, accumulate into batches ⚠️ BOTTLENECK
3. **Draw batched backgrounds** (t3-t2): Render all background rectangles
4. **Draw characters** (t4-t3): Render all non-space characters
5. **Draw cursor** (t5-t4): Render cursor if visible

The bottleneck occurs in phase 2, where we iterate through every cell in the dirty region performing multiple operations per cell.

## Components and Interfaces

### Current Implementation Analysis

The problematic code (lines 1910-1945) performs these operations for each cell:

```python
for row in range(start_row, end_row):
    for col in range(start_col, end_col):
        # 1. Grid access (dictionary-like access)
        char, color_pair, attributes = self.backend.grid[row][col]
        
        # 2. Pixel position calculation (2 multiplications)
        x = col * self.backend.char_width
        y = (self.backend.rows - row - 1) * self.backend.char_height
        
        # 3. Color pair lookup (dictionary access)
        if color_pair in self.backend.color_pairs:
            fg_rgb, bg_rgb = self.backend.color_pairs[color_pair]
        else:
            fg_rgb, bg_rgb = self.backend.color_pairs[0]
        
        # 4. Reverse video handling (conditional swap)
        if attributes & TextAttribute.REVERSE:
            fg_rgb, bg_rgb = bg_rgb, fg_rgb
        
        # 5. Add to batcher (method call with 5 parameters)
        batcher.add_cell(x, y, self.backend.char_width, 
                       self.backend.char_height, bg_rgb)
    
    batcher.finish_row()
```

### Performance Analysis

For a 24x80 grid (1920 cells), this code performs:
- **1920 grid accesses**: `self.backend.grid[row][col]`
- **3840 multiplications**: 2 per cell for x and y calculations
- **1920 dictionary lookups**: `color_pair in self.backend.color_pairs`
- **1920 conditional checks**: reverse video attribute check
- **1920 method calls**: `batcher.add_cell()` with 5 parameters
- **24 method calls**: `batcher.finish_row()`

The primary bottlenecks are:
1. **Repeated attribute access**: `self.backend.char_width`, `self.backend.char_height`, `self.backend.rows` accessed in every iteration
2. **Redundant calculations**: `(self.backend.rows - row - 1) * self.backend.char_height` recalculated for every cell in the same row
3. **Dictionary lookups**: Color pair dictionary accessed for every cell
4. **Method call overhead**: `add_cell()` called 1920 times with 5 parameters

## Data Models

No changes to data models are required. The optimization focuses on algorithmic improvements and caching.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After reviewing the prework analysis, I identified the following testable properties:

1. Performance property (1.1): Iteration completes in under 0.05 seconds
2. Correctness property (3.5, 4.1): Optimized code produces identical batches
3. Performance improvement property (4.2, 4.4): Optimized version is measurably faster

Properties 3.5 and 4.1 are redundant - they both test that the optimized code produces identical output. We can combine these into a single comprehensive property.

Properties 4.2 and 4.4 are also redundant - they both test performance improvement. We can combine these into a single property.

After eliminating redundancy, we have three unique properties:
1. Performance target property
2. Correctness property (identical output)
3. Performance improvement property

### Correctness Properties

Property 1: Iteration performance target
*For any* grid state with a 24x80 dirty region, the iteration phase should complete in under 0.05 seconds
**Validates: Requirements 1.1**

Property 2: Batch output equivalence
*For any* grid state and dirty region, the optimized implementation should produce identical batches to the original implementation
**Validates: Requirements 3.5, 4.1**

Property 3: Performance improvement
*For any* grid state with a full-screen dirty region, the optimized implementation should be measurably faster than the original implementation (at least 50% faster)
**Validates: Requirements 4.2, 4.4**

## Proposed Optimizations

### Optimization 1: Cache Frequently Accessed Attributes

**Problem**: `self.backend.char_width`, `self.backend.char_height`, and `self.backend.rows` are accessed in every iteration.

**Solution**: Cache these values in local variables before the loop:

```python
char_width = self.backend.char_width
char_height = self.backend.char_height
rows = self.backend.rows
grid = self.backend.grid
color_pairs = self.backend.color_pairs
```

**Expected Impact**: Reduces attribute access overhead by ~1920 accesses per frame.

### Optimization 2: Pre-calculate Row Y-Coordinates

**Problem**: `(self.backend.rows - row - 1) * self.backend.char_height` is recalculated for every cell in the same row.

**Solution**: Calculate y-coordinate once per row:

```python
for row in range(start_row, end_row):
    y = (rows - row - 1) * char_height  # Calculate once per row
    for col in range(start_col, end_col):
        x = col * char_width
        # ... rest of loop
```

**Expected Impact**: Reduces multiplications from 3840 to 1920 (50% reduction).

### Optimization 3: Optimize Color Pair Lookup

**Problem**: Dictionary lookup `color_pair in self.backend.color_pairs` happens for every cell, even though most cells use the same few color pairs.

**Solution**: Use `dict.get()` with default value instead of conditional check:

```python
# Before
if color_pair in self.backend.color_pairs:
    fg_rgb, bg_rgb = self.backend.color_pairs[color_pair]
else:
    fg_rgb, bg_rgb = self.backend.color_pairs[0]

# After
fg_rgb, bg_rgb = color_pairs.get(color_pair, color_pairs[0])
```

**Expected Impact**: Reduces dictionary operations from 2 lookups to 1 per cell (50% reduction).

### Optimization 4: Inline Simple Operations

**Problem**: Method call overhead for `batcher.add_cell()` with 5 parameters.

**Solution**: Consider inlining the batching logic directly in the loop to avoid method call overhead. However, this trades code clarity for performance, so we should measure the impact first.

**Expected Impact**: Potentially significant reduction in method call overhead, but may reduce code maintainability.

### Optimization 5: Use Tuple Unpacking Efficiently

**Problem**: Unpacking `char, color_pair, attributes = self.backend.grid[row][col]` creates temporary tuple.

**Solution**: Only unpack the values we need. Since we don't use `char` in this phase, we can skip it:

```python
# Before
char, color_pair, attributes = grid[row][col]

# After
_, color_pair, attributes = grid[row][col]
# Or even better, use indexing:
color_pair = grid[row][col][1]
attributes = grid[row][col][2]
```

**Expected Impact**: Minor reduction in tuple unpacking overhead.

## Implementation Strategy

We will implement optimizations incrementally and measure the impact of each:

1. **Phase 1**: Implement Optimizations 1-3 (caching, pre-calculation, dict.get)
   - These are low-risk, high-impact optimizations
   - Measure performance improvement
   - Verify correctness with property tests

2. **Phase 2**: Evaluate Optimization 4 (inlining)
   - Measure the actual overhead of method calls
   - Only implement if significant improvement is possible
   - Consider maintainability trade-offs

3. **Phase 3**: Fine-tune with Optimization 5 if needed
   - Only if we haven't reached the 0.05s target
   - Measure actual impact before committing

## Error Handling

The optimization should maintain the same error handling behavior as the original implementation:
- Handle missing color pairs gracefully (fall back to default)
- Handle out-of-bounds grid access (should not occur with correct dirty region calculation)
- Maintain exception handling for any unexpected errors

## Testing Strategy

### Unit Testing

Unit tests will verify:
- Correct caching of attributes
- Correct pre-calculation of y-coordinates
- Correct color pair lookup with dict.get()
- Edge cases (empty dirty region, single cell, full screen)

### Property-Based Testing

Property-based tests will verify the three correctness properties:

1. **Performance Target Property Test**:
   - Generate random grid states (various color pairs, attributes)
   - Measure iteration time for full-screen dirty region
   - Assert time < 0.05 seconds
   - Run 100 iterations to account for variance

2. **Batch Output Equivalence Property Test**:
   - Generate random grid states
   - Run both original and optimized implementations
   - Compare the batches produced (same positions, sizes, colors)
   - Run 100 iterations with different grid states

3. **Performance Improvement Property Test**:
   - Generate random grid states
   - Measure time for both implementations
   - Assert optimized is at least 50% faster
   - Run 100 iterations to account for variance

### Integration Testing

Integration tests will:
- Run the full drawRect_() method with optimized iteration
- Verify visual output matches original implementation
- Use existing visual correctness tests
- Measure end-to-end rendering performance

## Performance Targets

Based on the analysis, we expect the following improvements:

| Optimization | Expected Time Reduction |
|-------------|------------------------|
| Baseline (current) | 0.200s |
| After Opt 1 (caching) | 0.150s (-25%) |
| After Opt 2 (pre-calc) | 0.100s (-33%) |
| After Opt 3 (dict.get) | 0.070s (-30%) |
| After Opt 4 (inlining) | 0.045s (-36%) |
| **Target** | **< 0.050s** |

These are estimates based on the analysis. Actual results will be measured during implementation.

## Risks and Mitigation

### Risk 1: Optimizations Don't Achieve Target

**Mitigation**: If optimizations 1-3 don't reach the target, we have optimization 4 (inlining) as a fallback. If that's still insufficient, we may need to consider more aggressive optimizations like:
- Using NumPy arrays instead of Python lists for the grid
- Implementing the iteration in Cython or C extension
- Caching batch results between frames (if grid hasn't changed)

### Risk 2: Correctness Regression

**Mitigation**: Comprehensive property-based testing will catch any correctness issues. We'll run 100+ iterations with random grid states to ensure the optimized code produces identical results.

### Risk 3: Code Maintainability

**Mitigation**: We'll prioritize optimizations that maintain code clarity. Optimization 4 (inlining) will only be implemented if necessary, and we'll document the trade-offs clearly.

## Future Enhancements

After achieving the performance target, we can consider:
1. **Incremental dirty region tracking**: Only redraw cells that actually changed
2. **Batch caching**: Cache batches between frames if grid hasn't changed
3. **Parallel processing**: Use multiple threads for large dirty regions
4. **GPU acceleration**: Investigate using Metal for rendering (future spec)
