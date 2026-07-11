# CoreGraphics Performance Analysis Guide

## Overview

This comprehensive guide explains how to measure, analyze, and compare the performance of the CoreGraphics backend. It covers establishing performance baselines, measuring optimized performance, and validating improvement targets.

## Quick Start

### Complete Measurement Workflow

```bash
# Step 1: Establish baseline (before optimization)
./tools/manual_baseline_benchmark.sh 30

# Step 2: Review baseline results
cat profiling_output/baseline/baseline_report.txt

# Step 3: Implement optimizations
# ... implement ColorCache, FontCache, RectangleBatcher, etc.

# Step 4: Measure optimized performance
./tools/measure_optimized_manual.sh 30

# Step 5: Review comparison results
cat profiling_output/optimized/optimized_report.txt
```

## Part 1: Establishing Performance Baseline

### Purpose of Baseline

The performance baseline provides:
- **Current FPS measurements** - Frames per second during typical usage
- **drawRect_ execution time** - Time spent in the rendering method
- **API call counts** - Number of CoreGraphics API calls per frame
- **Bottleneck identification** - Which operations are most expensive

### Baseline Measurement Tools

#### 1. Manual Baseline Benchmark (Recommended)

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

#### 2. Automated Baseline Benchmark (Advanced)

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

### Running the Baseline Benchmark

#### Step-by-Step Process (Manual Benchmark)

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

## Part 2: Measuring Optimized Performance

### Optimized Measurement Tools

#### Manual Optimized Measurement (Recommended)

**Script**: `tools/measure_optimized_manual.sh`

**Purpose**: Measure optimized performance and compare with baseline

**Usage**:
```bash
./tools/measure_optimized_manual.sh [duration_seconds]
```

**Features**:
- Interactive measurement with real user input
- Automatic baseline comparison
- Improvement percentage calculation
- Target validation (20% FPS, 75-85% API reduction)
- Comprehensive comparison report

**Output**:
- `profiling_output/optimized/optimized_report.txt` - Comparison report
- `profiling_output/optimized/*_profile_*.prof` - cProfile data

#### Automated Measurement (Python)

**Script**: `tools/measure_optimized_performance.py`

**Purpose**: Automated performance measurement for consistent testing

**Usage**:
```bash
python3 tools/measure_optimized_performance.py \
  --duration 30 \
  --output-dir profiling_output/optimized \
  --baseline-dir profiling_output/baseline
```

**Options**:
- `--duration SECONDS` - Measurement duration (default: 30)
- `--output-dir DIR` - Output directory (default: profiling_output/optimized)
- `--baseline-dir DIR` - Baseline directory (default: profiling_output/baseline)

**Features**:
- Automated execution (no manual interaction)
- Consistent test scenarios
- Comprehensive data collection
- Automatic baseline comparison
- CSV export of FPS data

## Part 3: Performance Metrics

### Key Performance Indicators

#### 1. Frames Per Second (FPS)

**Average FPS**: Mean frames per second over measurement period
- **Target**: 60+ FPS (excellent)
- **Acceptable**: 30-60 FPS
- **Poor**: 20-30 FPS
- **Critical**: <20 FPS

**Min/Max/Median FPS**: Statistical distribution of FPS samples

#### 2. drawRect_ Execution Time

**Metric**: Cumulative time spent in drawRect_ method
**Per-call time**: Average time per drawRect_ invocation
- **Target**: <16.67ms (60 FPS)
- **Acceptable**: <33.33ms (30 FPS)

**Calls per second**: Rendering frequency

#### 3. CoreGraphics API Call Count

**Current**: ~3,840+ calls per frame (24×80 grid)
**Target**: 75-85% reduction through batching
**Measurement**: Count of NSRectFill, NSColor, NSAttributedString calls

**API calls per second**: Rate of API usage
**API calls per frame**: Average API calls per drawRect_ call

#### 4. Time Per Frame

**Calculation**: 1000ms / FPS
**Target**: <16.67ms (for 60 FPS)
**Acceptable**: <33.33ms (for 30 FPS)

### Performance Assessment Criteria

| Average FPS | Assessment | Description |
|-------------|------------|-------------|
| 60+ FPS | EXCELLENT | Smooth rendering, target achieved |
| 30-60 FPS | ACCEPTABLE | Usable, optimization successful |
| 20-30 FPS | POOR | Noticeable lag, further optimization needed |
| <20 FPS | CRITICAL | Significant lag, major issues remain |

## Part 4: Improvement Targets

### Primary Target: FPS Improvement

**Requirement**: ≥20% improvement in average FPS

**Calculation**:
```
FPS Improvement % = ((Optimized FPS - Baseline FPS) / Baseline FPS) × 100
```

**Example**:
- Baseline: 20 FPS
- Optimized: 50 FPS
- Improvement: ((50 - 20) / 20) × 100 = 150%
- Result: ✓ Target met (150% > 20%)

### Secondary Target: API Call Reduction

**Requirement**: 75-85% reduction in CoreGraphics API calls

**Calculation**:
```
API Reduction % = ((Baseline API - Optimized API) / Baseline API) × 100
```

**Example**:
- Baseline: 3,840 API calls per frame
- Optimized: 600 API calls per frame
- Reduction: ((3,840 - 600) / 3,840) × 100 = 84.4%
- Result: ✓ Target met (84.4% in 75-85% range)

## Part 5: Analyzing Results

### Understanding Profile Data

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
callees drawRect_ # Show what drawRect_ calls
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

### Key Functions to Analyze

**drawRect_**: Main rendering method
- Look for cumulative time
- Check calls per second
- Identify time-consuming operations

**NSRectFill**: Background rectangle drawing
- Count total calls
- Should be significantly reduced after batching

**NSColor creation**: Color object instantiation
- Should be minimal after caching
- Look for colorWithRed_green_blue_alpha_ calls

**NSAttributedString**: Text rendering
- Count should match non-space characters
- Check for font-related operations

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

## Part 6: Report Interpretation

### Sample Report Analysis

```
OPTIMIZED PERFORMANCE METRICS
Average FPS: 55.23
drawRect_ avg time: 12.45 ms
Total API calls: 45,678
API calls per frame: 623.45

COMPARISON WITH BASELINE
Baseline Average FPS: 18.45
Improvements:
  FPS improvement: +199.35%
  API call reduction: +82.15%

Assessment:
✓ Target achieved: FPS improved by 20% or more
✓ Excellent API call reduction: 82.15%

Overall: ACCEPTABLE - 30-60 FPS range
```

**Interpretation**:
- FPS improved from 18.45 to 55.23 (3x improvement)
- API calls reduced by 82.15% (within 75-85% target)
- Both primary targets met
- Performance is acceptable (near excellent threshold)
- Consider minor tweaks to reach 60+ FPS

## Part 7: Iterative Optimization

### If Targets Not Met

```bash
# 1. Identify bottlenecks from profile data
python3 -m pstats profiling_output/optimized/*_profile_*.prof

# 2. Implement additional optimizations
# ... refine batching, caching, etc.

# 3. Re-measure
./tools/measure_optimized_manual.sh 30

# 4. Compare improvements
# Review new report and check progress toward targets
```

### If Targets Met

1. **Document results**
2. **Visual verification**
3. **Evaluate native implementation need**
4. **Create end-user documentation**

### If Performance Excellent (60+ FPS)

1. **Document success**
2. **Skip native implementation** (not needed)
3. **Focus on visual verification**
4. **Complete documentation**

## Part 8: Best Practices

### Measurement Duration

**Minimum**: 10 seconds (for basic data)
**Recommended**: 30 seconds (for reliable statistics)
**Extended**: 60+ seconds (for detailed analysis)

### User Interaction

During manual measurements:
- Navigate through directories
- Scroll through file lists
- Switch between panes
- Use various TFM features
- Simulate realistic usage patterns

### Consistent Conditions

For accurate comparisons:
- Use same duration for baseline and optimized
- Perform similar actions in both measurements
- Use same directory structure
- Avoid background processes
- Close other applications

### Multiple Measurements

For statistical validity:
- Run multiple measurements (3-5 times)
- Calculate average improvements
- Check for consistency
- Identify outliers

## Part 9: Troubleshooting

### No Baseline Data

**Problem**: "No baseline data found" warning

**Solution**:
```bash
# Run baseline benchmark first
./tools/manual_baseline_benchmark.sh 30
```

### Low FPS After Optimization

**Problem**: FPS still below 30 after optimization

**Diagnosis**:
1. Check if all optimizations are implemented
2. Review profile data for new bottlenecks
3. Verify caches are being used

**Solutions**:
- Review optimization implementation
- Check for bugs in batching logic
- Verify cache hit rates
- Consider native implementation

### API Calls Not Reduced

**Problem**: API call reduction less than expected

**Diagnosis**:
1. Check if batching is working correctly
2. Verify RectangleBatcher is being used
3. Look for unbatched API calls

**Solutions**:
- Review batching logic
- Check batch size distribution
- Verify adjacent cell detection
- Ensure finish_row() is called

### Profile Files Not Generated

**Problem**: "No profile files found" error

**Diagnosis**:
1. Check if profiling is enabled
2. Verify output directory permissions
3. Ensure TFM ran for sufficient duration

**Solutions**:
```bash
# Verify profiling environment variable
export TFM_PROFILING=1

# Check output directory
ls -la profiling_output/optimized/

# Ensure sufficient duration (minimum 10 seconds)
./tools/measure_optimized_manual.sh 30
```

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

## Part 10: Documentation Template

After running measurements, document the results:

```markdown
## Performance Analysis - [Date]

### Environment
- macOS version: [version]
- Python version: [version]
- PyObjC version: [version]
- Grid size: 24 rows × 80 columns

### Baseline Measurements
- Average FPS: [value]
- Minimum FPS: [value]
- Maximum FPS: [value]
- Median FPS: [value]
- drawRect_ avg time: [value] ms
- API calls per frame: [value]

### Optimized Measurements
- Average FPS: [value]
- Minimum FPS: [value]
- Maximum FPS: [value]
- Median FPS: [value]
- drawRect_ avg time: [value] ms
- API calls per frame: [value]

### Improvements
- FPS improvement: [value]%
- API call reduction: [value]%

### Assessment
[EXCELLENT/ACCEPTABLE/POOR/CRITICAL]

### Targets Met
- [ ] FPS improvement ≥20%
- [ ] API call reduction 75-85%

### Bottlenecks Identified
1. [bottleneck description]
2. [bottleneck description]

### Optimization Priorities
1. [optimization strategy]
2. [optimization strategy]
```

## References

### Related Documentation

- **Optimization Design**: `.kiro/specs/coregraphics-performance-optimization/design.md`
- **Profiling System**: `doc/dev/PROFILING_SYSTEM_IMPLEMENTATION.md`
- **CoreGraphics Backend**: `ttk/backends/coregraphics_backend.py`

### Related Scripts

- **Baseline Benchmark**: `tools/manual_baseline_benchmark.sh`
- **Optimized Measurement**: `tools/measure_optimized_manual.sh`
- **Automated Measurement**: `tools/measure_optimized_performance.py`
- **Profiling Infrastructure**: `src/tfm_profiling.py`

### External Resources

- [Python cProfile Documentation](https://docs.python.org/3/library/profile.html)
- [snakeviz Profiler](https://jiffyclub.github.io/snakeviz/)

## Conclusion

This comprehensive guide provides all the tools and knowledge needed to:
- Establish accurate performance baselines
- Measure optimized performance
- Compare before/after results
- Validate improvement targets
- Identify and resolve bottlenecks
- Make data-driven optimization decisions

Use this guide throughout the optimization process to track progress, validate effectiveness, and document improvements.
