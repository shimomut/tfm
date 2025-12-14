# Visual Correctness Verification

## Overview

This document describes the visual correctness verification system for the CoreGraphics backend optimization. The verification ensures that performance optimizations do not introduce visual regressions or rendering artifacts.

## Purpose

The visual correctness verification validates that the optimized CoreGraphics backend produces visually identical output to the baseline implementation, satisfying Requirements 7.1-7.5:

- **7.1**: All existing visual tests pass
- **7.2**: Optimized and original output are visually identical
- **7.3**: Edge cases are handled correctly
- **7.4**: Different color combinations render correctly
- **7.5**: Various rectangle sizes appear correctly

## Verification Tools

### 1. Automated Visual Verification (`tools/verify_visual_correctness.py`)

Automated tool that captures and compares visual output data.

**Features:**
- Creates comprehensive test scenarios
- Captures rendering data for baseline and optimized implementations
- Performs pixel-by-pixel comparison
- Generates detailed comparison reports

**Usage:**

```bash
# Step 1: Capture baseline (before optimization)
python tools/verify_visual_correctness.py --mode baseline --output profiling_output/baseline_visual.dat

# Step 2: Apply optimizations to CoreGraphics backend

# Step 3: Capture optimized output
python tools/verify_visual_correctness.py --mode optimized --output profiling_output/optimized_visual.dat

# Step 4: Compare baseline and optimized
python tools/verify_visual_correctness.py --mode compare \
    --baseline profiling_output/baseline_visual.dat \
    --optimized profiling_output/optimized_visual.dat
```

**Test Scenarios:**

1. **Solid Color Blocks**: Large blocks of solid colors to test batching
2. **Checkerboard Pattern**: Alternating colors to test batching boundaries
3. **Colored Text**: Text in different colors to test font and color caching
4. **Gradient Pattern**: Gradual color changes to test color cache
5. **Edge Cases**: Single-cell color changes to test batching edge cases
6. **Complex UI**: Simulated file manager UI with mixed content

### 2. Manual Visual Verification (`tools/verify_visual_manual.sh`)

Interactive script for manual visual inspection.

**Features:**
- Guides user through visual verification tests
- Launches TFM with various test scenarios
- Collects user feedback on visual correctness
- Generates pass/fail report

**Usage:**

```bash
./tools/verify_visual_manual.sh
```

**Test Scenarios:**

1. **Basic File Listing**: Default colors and layout
2. **Large Directory**: Performance with many files
3. **Nested Directories**: Navigation and rendering
4. **File Selection**: Selection highlighting
5. **Dual Pane Mode**: Active pane indication
6. **Text Viewer**: Syntax highlighting
7. **Search Functionality**: Search result highlighting
8. **Long Filenames**: Truncation and display

### 3. Unit Tests (`ttk/test/test_visual_correctness.py`)

Automated unit tests for visual correctness components.

**Features:**
- Tests color cache consistency
- Tests font cache consistency
- Tests rectangle batching coverage
- Tests dirty region calculation
- Tests edge cases

**Usage:**

```bash
python ttk/test/test_visual_correctness.py
```

## Verification Workflow

### Complete Verification Process

1. **Establish Baseline**
   ```bash
   # Capture baseline visual data
   python tools/verify_visual_correctness.py --mode baseline --output profiling_output/baseline_visual.dat
   ```

2. **Apply Optimizations**
   - Implement ColorCache
   - Implement FontCache
   - Implement RectangleBatcher
   - Refactor drawRect_ method

3. **Capture Optimized Output**
   ```bash
   # Capture optimized visual data
   python tools/verify_visual_correctness.py --mode optimized --output profiling_output/optimized_visual.dat
   ```

4. **Compare Outputs**
   ```bash
   # Compare baseline and optimized
   python tools/verify_visual_correctness.py --mode compare \
       --baseline profiling_output/baseline_visual.dat \
       --optimized profiling_output/optimized_visual.dat
   ```

5. **Manual Verification**
   ```bash
   # Run manual visual tests
   ./tools/verify_visual_manual.sh
   ```

6. **Run Unit Tests**
   ```bash
   # Run automated unit tests
   python ttk/test/test_visual_correctness.py
   ```

## Verification Criteria

### Visual Equivalence

The optimized implementation must produce **pixel-perfect** output matching the baseline:

- **Colors**: RGB values must match exactly
- **Positions**: Character positions must be identical
- **Attributes**: Font attributes (bold, underline) must be preserved
- **Backgrounds**: Background colors must match exactly
- **Coverage**: All cells must be rendered (no gaps or overlaps)

### Edge Cases

The verification must handle edge cases correctly:

- Empty screens (all spaces)
- Single characters in corners
- Very long lines exceeding screen width
- Unicode and special characters
- Maximum and minimum color values
- Various rectangle sizes (1x1 to full screen)

### Performance Considerations

While verifying visual correctness, also monitor:

- **Rendering time**: Should not increase significantly
- **Memory usage**: Should not increase significantly
- **API calls**: Should decrease (optimization goal)

## Test Scenarios Explained

### Solid Color Blocks

Tests batching of adjacent cells with the same color.

**Expected Behavior:**
- Multiple adjacent cells should batch into single rectangles
- Reduces API calls significantly
- Visual output identical to drawing each cell individually

### Checkerboard Pattern

Tests batching boundaries with alternating colors.

**Expected Behavior:**
- No batching possible (each cell different color)
- Each cell drawn individually
- Visual output identical to baseline

### Colored Text

Tests font and color caching with various text colors.

**Expected Behavior:**
- Fonts cached and reused
- Colors cached and reused
- Text rendering identical to baseline
- Font attributes preserved

### Gradient Pattern

Tests color cache with many similar colors.

**Expected Behavior:**
- Color cache handles many unique colors
- Cache eviction works correctly
- Visual output shows smooth gradient
- No color banding or artifacts

### Edge Cases

Tests single-cell differences in large uniform areas.

**Expected Behavior:**
- Batching correctly splits at color boundaries
- Single different cells rendered correctly
- No visual artifacts at boundaries

### Complex UI

Tests realistic file manager UI with mixed content.

**Expected Behavior:**
- Headers, file lists, and status bars render correctly
- Alternating row backgrounds work correctly
- Text and backgrounds combine correctly
- Overall layout matches baseline

## Troubleshooting

### Visual Differences Detected

If visual differences are detected:

1. **Review the comparison report** to identify specific differences
2. **Check batching logic** for boundary conditions
3. **Verify color cache** returns correct RGB values
4. **Verify font cache** preserves attributes
5. **Check coordinate transformations** for off-by-one errors

### Common Issues

**Issue**: Colors appear slightly different
- **Cause**: Color cache returning wrong RGB values
- **Fix**: Verify ColorCache.get_color() implementation

**Issue**: Text appears in wrong position
- **Cause**: Coordinate transformation error
- **Fix**: Verify DirtyRegionCalculator coordinate conversion

**Issue**: Missing or duplicate cells
- **Cause**: Batching logic error
- **Fix**: Verify RectangleBatcher coverage

**Issue**: Font attributes not preserved
- **Cause**: Font cache not handling attributes correctly
- **Fix**: Verify FontCache.get_font() implementation

## Integration with Performance Testing

Visual correctness verification should be performed alongside performance testing:

1. **Measure baseline performance** (Task 1)
2. **Implement optimizations** (Tasks 2-9)
3. **Verify visual correctness** (Task 12) ← You are here
4. **Measure optimized performance** (Task 11)
5. **Compare results** (Task 13)

This ensures optimizations improve performance without sacrificing visual quality.

## Success Criteria

Visual correctness verification is successful when:

- ✓ All automated comparison tests pass
- ✓ All manual verification tests pass
- ✓ All unit tests pass
- ✓ No visual artifacts or glitches observed
- ✓ Edge cases handled correctly
- ✓ All color combinations render correctly
- ✓ All rectangle sizes render correctly

## Future Enhancements

Potential improvements to the verification system:

1. **Screenshot Capture**: Capture actual screenshots for pixel-perfect comparison
2. **Automated UI Testing**: Automated interaction with TFM for testing
3. **Regression Testing**: Continuous verification in CI/CD pipeline
4. **Performance Profiling**: Integrated performance and visual testing
5. **Visual Diff Tool**: Side-by-side comparison of baseline and optimized output

## References

- **Requirements Document**: `.kiro/specs/coregraphics-performance-optimization/requirements.md`
- **Implementation Plan**: `.kiro/specs/coregraphics-performance-optimization/tasks.md`
- **Performance Measurement**: `doc/dev/COREGRAPHICS_PERFORMANCE_MEASUREMENT.md`
- **CoreGraphics Backend**: `ttk/backends/coregraphics_backend.py`

## Related Documentation

- **User Documentation**: None (visual correctness is transparent to users)
- **Developer Documentation**: This document
- **Test Documentation**: `ttk/test/test_visual_correctness.py`
