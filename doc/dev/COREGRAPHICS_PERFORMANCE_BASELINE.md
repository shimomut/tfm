# CoreGraphics Performance Baseline Documentation

## Overview

This document describes the process for establishing a performance baseline for the CoreGraphics backend's `drawRect_` method. The baseline measurements are essential for evaluating the effectiveness of optimization efforts.

## Purpose

The performance baseline provides:
- **Current FPS measurements** - Frames per second during typical usage
- **drawRect_ execution time** - Time spent in the rendering method
- **API call counts** - Number of CoreGraphics API calls per frame
- **Bottleneck identification** - Which operations are most expensive

## Baseline Measurement Tools

### 1. Manual Benchmark Script (Recommended)

The manual benchmark script provides the most realistic performance data because it captures actual user interaction patterns.

**Location**: `tools/manual_baseline_benchmark.sh`

**Usage**:
```bash
./tools/manual_baseline_benchmark.sh [duration_seconds]
```

**Process**:
1. Script launches TFM with CoreGraphics backend and profiling enabled
2. You interact with TFM normally (navigate, scroll, switch panes, etc.)
3. After the specified duration, quit TFM by pressing 'q'
4. Script automatically analyzes the profiling data and generates a report

**Advantages**:
- Captures realistic usage patterns
- Easy to run and understand
- Provides immediate analysis
- No complex setup required

**Example**:
```bash
# Run 30-second benchmark (default)
./tools/manual_baseline_benchmark.sh

# Run 60-second benchmark for more data
./tools/manual_baseline_benchmark.sh 60
```

### 2. Automated Benchmark Script (Advanced)

The automated benchmark script runs TFM with simulated input for consistent, repeatable measurements.

**Location**: `tools/benchmark_coregraphics_performance.py`

**Usage**:
```bash
python3 tools/benchmark_coregraphics_performance.py --duration 30 --output-dir profiling_output/baseline
```

**Options**:
- `--duration SECONDS` - How long to run the benchmark (default: 30)
- `--output-dir DIR` - Where to save results (default: profiling_output/baseline)
- `--help` - Show help message

**Advantages**:
- Consistent, repeatable measurements
- Automated data collection and analysis
- Generates comprehensive reports
- Good for comparing before/after optimization

**Disadvantages**:
- May not capture realistic usage patterns
- Requires more complex setup
- Simulated input may not trigger all rendering paths

## Baseline Metrics

### Key Performance Indicators

1. **Frames Per Second (FPS)**
   - **Target**: 60 FPS (smooth rendering)
   - **Minimum acceptable**: 30 FPS
   - **Current baseline**: To be measured
   - **Measurement**: Average FPS over benchmark duration

2. **drawRect_ Execution Time**
   - **Metric**: Cumulative time spent in drawRect_ method
   - **Per-call time**: Average time per drawRect_ invocation
   - **Measurement**: From cProfile data

3. **CoreGraphics API Call Count**
   - **Current**: ~3,840+ calls per frame (24×80 grid)
   - **Target**: 75-85% reduction through batching
   - **Measurement**: Count of NSRectFill, NSColor, NSAttributedString calls

4. **Time Per Frame**
   - **Calculation**: 1000ms / FPS
   - **Target**: <16.67ms (for 60 FPS)
   - **Acceptable**: <33.33ms (for 30 FPS)

### Expected Baseline Values

Based on profiling data analysis, we expect:

**Before Optimization**:
- FPS: 15-25 FPS (poor performance)
- drawRect_ time: 40-60ms per call
- API calls per frame: 3,000-4,000
- Time per frame: 40-67ms

**After Optimization** (Target):
- FPS: 60+ FPS (smooth performance)
- drawRect_ time: 10-15ms per call
- API calls per frame: 500-900 (75-85% reduction)
- Time per frame: <16.67ms

## Running the Baseline Benchmark

### Step-by-Step Process

#### Using Manual Benchmark (Recommended for Initial Baseline)

1. **Prepare the environment**:
   ```bash
   # Ensure you're in the TFM project directory
   cd /path/to/tfm
   
   # Make sure the script is executable
   chmod +x tools/manual_baseline_benchmark.sh
   ```

2. **Run the benchmark**:
   ```bash
   ./tools/manual_baseline_benchmark.sh 30
   ```

3. **Interact with TFM**:
   - Navigate through directories (j, k, arrow keys)
   - Scroll through file lists
   - Switch between panes (Tab)
   - View file details (i)
   - Perform typical file manager operations
   - Try to use TFM as you normally would

4. **Quit TFM**:
   - After 30 seconds (or your specified duration), press 'q' to quit
   - The script will automatically analyze the profiling data

5. **Review the results**:
   - The script prints a detailed analysis to the console
   - Profile data is saved to `profiling_output/baseline/`
   - Note the FPS values that were printed during execution

#### Using Automated Benchmark

1. **Run the automated benchmark**:
   ```bash
   python3 tools/benchmark_coregraphics_performance.py --duration 30
   ```

2. **Wait for completion**:
   - The script will launch TFM automatically
   - It will simulate user input for the specified duration
   - TFM will close automatically when complete

3. **Review the generated report**:
   ```bash
   cat profiling_output/baseline/baseline_report.txt
   ```

## Analyzing Baseline Results

### Understanding the Profile Data

The profiling data includes:

1. **Function call statistics**:
   - Number of calls to each function
   - Time spent in each function
   - Cumulative time (including called functions)

2. **drawRect_ method metrics**:
   - Total calls during benchmark
   - Total time spent in the method
   - Average time per call

3. **CoreGraphics API call counts**:
   - NSRectFill calls (background rectangles)
   - NSColor creation calls
   - NSAttributedString creation calls
   - drawAtPoint calls (character rendering)

### Using pstats for Detailed Analysis

For detailed analysis of the profile data:

```bash
# Interactive analysis
python3 -m pstats profiling_output/baseline/loop_profile_*.prof

# In the pstats prompt:
sort cumulative    # Sort by cumulative time
stats 20          # Show top 20 functions
callers drawRect_ # Show what calls drawRect_
```

### Using snakeviz for Visual Analysis

For visual analysis (requires installation):

```bash
# Install snakeviz
pip install snakeviz

# Open visual profiler
snakeviz profiling_output/baseline/loop_profile_*.prof
```

This opens a web browser with an interactive visualization of the profiling data.

## Interpreting Results

### Performance Assessment

Based on the FPS measurements:

- **60+ FPS**: Excellent - No optimization needed
- **30-60 FPS**: Acceptable - Optimization recommended
- **20-30 FPS**: Poor - Optimization required
- **<20 FPS**: Critical - Significant optimization required

### Bottleneck Identification

Look for:

1. **High call counts** in drawRect_:
   - Each cell in the grid triggers multiple API calls
   - Expected: rows × cols × 2-3 calls per frame

2. **Expensive operations**:
   - NSColor creation (should be cached)
   - NSFont operations (should be cached)
   - NSRectFill calls (should be batched)

3. **Redundant work**:
   - Creating the same color multiple times
   - Drawing cells that haven't changed
   - Processing cells outside the dirty region

## Baseline Documentation Template

After running the baseline benchmark, document the results:

```markdown
## Performance Baseline - [Date]

### Environment
- macOS version: [version]
- Python version: [version]
- PyObjC version: [version]
- Grid size: 24 rows × 80 columns

### Measurements
- Average FPS: [value]
- Minimum FPS: [value]
- Maximum FPS: [value]
- Median FPS: [value]

### drawRect_ Performance
- Total calls: [value]
- Cumulative time: [value] seconds
- Average time per call: [value] ms
- Calls per second: [value]

### API Call Counts
- Total CoreGraphics API calls: [value]
- NSRectFill calls: [value]
- NSColor creation calls: [value]
- NSAttributedString calls: [value]
- drawAtPoint calls: [value]

### Assessment
[EXCELLENT/ACCEPTABLE/POOR/CRITICAL]

### Bottlenecks Identified
1. [bottleneck description]
2. [bottleneck description]
3. [bottleneck description]

### Optimization Priorities
1. [optimization strategy]
2. [optimization strategy]
3. [optimization strategy]
```

## Next Steps

After establishing the baseline:

1. **Document the baseline metrics** in the optimization spec
2. **Identify specific bottlenecks** from the profiling data
3. **Prioritize optimizations** based on expected impact
4. **Implement optimizations** according to the design document
5. **Re-run benchmark** to measure improvement
6. **Compare results** to validate optimization effectiveness

## Troubleshooting

### Common Issues

**Issue**: No profile data generated
- **Cause**: Profiling not enabled or TFM quit too quickly
- **Solution**: Ensure TFM_PROFILING=1 is set and run for at least 10 seconds

**Issue**: FPS not printed during execution
- **Cause**: Profiling not enabled or FPS tracking disabled
- **Solution**: Check that TFM_PROFILING=1 environment variable is set

**Issue**: drawRect_ not found in profile data
- **Cause**: Method wasn't called or profiling started too late
- **Solution**: Ensure you interact with TFM to trigger rendering

**Issue**: Profile file not found
- **Cause**: Profiling output directory not writable
- **Solution**: Check permissions on profiling_output directory

### Getting Help

If you encounter issues:
1. Check the profiling output directory for error messages
2. Review the TFM console output for warnings
3. Verify PyObjC is installed correctly
4. Ensure you're running on macOS (CoreGraphics backend requirement)

## References

- [TFM Profiling System](PROFILING_SYSTEM_IMPLEMENTATION.md)
- [CoreGraphics Backend Implementation](../../ttk/backends/coregraphics_backend.py)
- [Performance Optimization Design](../../.kiro/specs/coregraphics-performance-optimization/design.md)
- [Python cProfile Documentation](https://docs.python.org/3/library/profile.html)
