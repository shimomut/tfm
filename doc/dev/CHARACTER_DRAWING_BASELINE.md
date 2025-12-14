# Character Drawing Performance Baseline

## Overview

This document records the baseline performance measurements for the character drawing phase (t4-t3) in the CoreGraphics backend's `drawRect_` method. These measurements establish the starting point for the character drawing optimization effort.

## Test Environment

- **System**: macOS
- **Backend**: CoreGraphics (ttk/backends/coregraphics_backend.py)
- **Font**: Menlo, 12pt
- **Grid Size**: 24 rows × 80 columns (1,920 cells)
- **Test Date**: December 14, 2025

## Test Methodology

The baseline test creates a maximum workload scenario for character drawing:

1. **Full Grid Coverage**: All 1,920 cells contain non-space characters
2. **Character Variety**: Uses 79 different characters (letters, numbers, symbols)
3. **Color Pairs**: 5 different color pairs applied across rows
4. **Text Attributes**: Mixed bold, underline, and reverse attributes
5. **Measurement**: Captures t4-t3 time delta from `drawRect_` method

### Test Script

Location: `test/test_character_drawing_performance.py`

The test script:
- Creates a CoreGraphics backend with 24×80 grid
- Initializes 5 color pairs
- Fills all cells with non-space characters
- Applies various attributes (bold, underline, reverse)
- Triggers 5 redraws and captures timing data

### Demo Script

Location: `demo/demo_character_drawing_optimization.py`

The demo script provides interactive visual verification:
- Multiple test patterns (full grid, colors, attributes, mixed)
- Real-time timing information in console
- Interactive pattern switching
- Visual correctness verification

## Baseline Results

### Character Drawing Phase (t4-t3)

Five samples were collected:

| Sample | t4-t3 Time (seconds) | t4-t3 Time (ms) |
|--------|---------------------|-----------------|
| 1      | 0.0440              | 44.0 ms         |
| 2      | 0.0405              | 40.5 ms         |
| 3      | 0.0456              | 45.6 ms         |
| 4      | 0.0404              | 40.4 ms         |
| 5      | 0.0598              | 59.8 ms         |

**Average**: 46.1 ms  
**Minimum**: 40.4 ms  
**Maximum**: 59.8 ms  
**Standard Deviation**: 7.5 ms

### Other Phase Timings

For context, here are the other phase timings from Sample 1:

| Phase | Time (ms) | Description |
|-------|-----------|-------------|
| t1-t0 | 0.4 ms    | Setup and dirty region calculation |
| t2-t1 | 0.6 ms    | Background batching iteration |
| t3-t2 | 0.6 ms    | Background drawing |
| t4-t3 | 44.0 ms   | **Character drawing (optimization target)** |
| t5-t4 | 0.0 ms    | Cursor drawing |

**Total rendering time**: ~46 ms per frame

## Analysis

### Current Performance

The character drawing phase (t4-t3) accounts for **95.7%** of the total rendering time:
- Character drawing: 44.0 ms (95.7%)
- All other phases: 2.0 ms (4.3%)

This confirms that character drawing is the primary bottleneck in the rendering pipeline.

### Performance Characteristics

1. **Consistency**: Most samples cluster around 40-46ms, with one outlier at 59.8ms
2. **Workload**: Processing 1,920 characters takes ~46ms average
3. **Per-Character Cost**: ~0.024ms per character (46ms / 1,920 characters)

### Bottleneck Identification

The character drawing phase involves:
1. **Dictionary operations**: Building attribute dictionaries for each character
2. **NSAttributedString creation**: Allocating and initializing attributed strings
3. **CoreGraphics calls**: Individual `drawAtPoint_` calls for each character

Expected bottlenecks:
- Python dictionary creation overhead (~1,920 dictionaries per frame)
- NSAttributedString allocation overhead (~1,920 objects per frame)
- Repeated font and color cache lookups

## Optimization Target

### Requirements

From the design document:
- **Target**: Character drawing phase (t4-t3) < 10ms
- **Improvement**: 70-85% reduction from baseline

### Baseline vs. Target

| Metric | Baseline | Target | Required Improvement |
|--------|----------|--------|---------------------|
| Average | 46.1 ms  | <10 ms | 78.3% reduction     |
| Best case | 40.4 ms | <10 ms | 75.2% reduction     |

### Expected Optimizations

Based on the design document, the following optimizations should achieve the target:

1. **Character Batching** (50-70% reduction)
   - Batch continuous characters with same attributes
   - Reduce `drawAtPoint_` calls from ~1,920 to ~50-200
   - Expected gain: 23-32ms

2. **NSAttributedString Caching** (20-30% additional reduction)
   - Cache pre-built attributed strings
   - Eliminate repeated instantiation overhead
   - Expected gain: 9-14ms

3. **Attribute Dictionary Caching** (10-15% additional reduction)
   - Cache pre-built attribute dictionaries
   - Eliminate dictionary operations
   - Expected gain: 5-7ms

**Combined expected result**: 5-9ms (78-85% reduction)

## Verification

### Running the Baseline Test

```bash
python3 test/test_character_drawing_performance.py
```

Expected output:
- 5 samples of timing data
- t4-t3 values around 40-60ms
- Visual window for 3 seconds

### Running the Demo

```bash
python3 demo/demo_character_drawing_optimization.py
```

Interactive controls:
- `1`: Full grid pattern (maximum workload)
- `2`: Color pairs demonstration
- `3`: Text attributes demonstration
- `4`: Mixed pattern (checkerboard)
- `H`: Help screen
- `Q`: Quit

## Next Steps

1. **Task 2**: Implement AttributeDictCache class
2. **Task 3**: Implement AttributedStringCache class
3. **Task 4**: Implement character batching logic
4. **Task 5**: Integrate caches into character drawing loop
5. **Task 8**: Verify performance improvement (target: <10ms)

## References

- Design Document: `.kiro/specs/character-drawing-optimization/design.md`
- Requirements: `.kiro/specs/character-drawing-optimization/requirements.md`
- Tasks: `.kiro/specs/character-drawing-optimization/tasks.md`
- CoreGraphics Backend: `ttk/backends/coregraphics_backend.py`
