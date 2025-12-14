# CoreGraphics Performance Measurement Guide

## Overview

This guide explains how to measure and compare the performance of the CoreGraphics backend before and after optimizations. The measurement framework provides comprehensive tools for establishing baselines, measuring optimized performance, and validating improvement targets.

## Quick Start

### 1. Establish Baseline (Before Optimization)

```bash
# Run 30-second manual baseline benchmark
./tools/manual_baseline_benchmark.sh 30

# Results saved to: profiling_output/baseline/
```

### 2. Implement Optimizations

Implement the optimization tasks (2-9):
- ColorCache
- FontCache
- RectangleBatcher
- DirtyRegionCalculator
- Cache integration
- drawRect_ refactoring

### 3. Measure Optimized Performance

```bash
# Run 30-second optimized measurement
./tools/measure_optimized_manual.sh 30

# Results saved to: profiling_output/optimized/
# Automatic comparison with baseline
```

### 4. Review Results

Check the generated report for:
- FPS improvement (target: ≥20%)
- API call reduction (target: 75-85%)
- Overall performance assessment

## Measurement Tools

### Manual Baseline Benchmark

**Script**: `tools/manual_baseline_benchmark.sh`

**Purpose**: Establish performance baseline before optimization

**Usage**:
```bash
./tools/manual_baseline_benchmark.sh [duration_seconds]
```

**Features**:
- Interactive measurement with real user input
- FPS tracking throughout measurement
- cProfile data collection
- Automatic analysis and reporting
- Profile file generation for detailed analysis

**Output**:
- `profiling_output/baseline/baseline_report.txt` - Performance summary
- `profiling_output/baseline/*_profile_*.prof` - cProfile data

### Manual Optimized Measurement

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

### Automated Measurement (Python)

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

## Performance Metrics

### FPS Measurements

**Average FPS**: Mean frames per second over measurement period
- Target: 60+ FPS (excellent)
- Acceptable: 30-60 FPS
- Poor: 20-30 FPS
- Critical: <20 FPS

**Min/Max/Median FPS**: Statistical distribution of FPS samples

### drawRect_ Performance

**Total calls**: Number of times drawRect_ was invoked
**Cumulative time**: Total time spent in drawRect_
**Average time per call**: Mean execution time per call
- Target: <16.67ms (60 FPS)
- Acceptable: <33.33ms (30 FPS)

**Calls per second**: Rendering frequency

### CoreGraphics API Calls

**Total API calls**: Sum of all CoreGraphics API invocations
- Baseline: 3,000-4,000 per frame
- Target: 500-900 per frame (75-85% reduction)

**API calls per second**: Rate of API usage
**API calls per frame**: Average API calls per drawRect_ call

## Improvement Targets

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

### Performance Assessment Criteria

| Average FPS | Assessment | Description |
|-------------|------------|-------------|
| 60+ FPS | EXCELLENT | Smooth rendering, target achieved |
| 30-60 FPS | ACCEPTABLE | Usable, optimization successful |
| 20-30 FPS | POOR | Noticeable lag, further optimization needed |
| <20 FPS | CRITICAL | Significant lag, major issues remain |

## Measurement Workflow

### Complete Measurement Process

```bash
# Step 1: Establish baseline (before optimization)
./tools/manual_baseline_benchmark.sh 30

# Step 2: Review baseline results
cat profiling_output/baseline/baseline_report.txt

# Step 3: Implement optimizations (tasks 2-9)
# ... implement ColorCache, FontCache, RectangleBatcher, etc.

# Step 4: Measure optimized performance
./tools/measure_optimized_manual.sh 30

# Step 5: Review comparison results
cat profiling_output/optimized/optimized_report.txt

# Step 6: Validate targets
# - Check FPS improvement ≥ 20%
# - Check API call reduction 75-85%
# - Assess overall performance level
```

### Iterative Optimization

If targets are not met, iterate:

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

## Analyzing Profile Data

### Using pstats (Built-in)

```bash
# Interactive analysis
python3 -m pstats profiling_output/optimized/*_profile_*.prof

# Common commands:
# sort cumulative  - Sort by cumulative time
# stats 20         - Show top 20 functions
# callers drawRect_ - Show what calls drawRect_
# callees drawRect_ - Show what drawRect_ calls
```

### Using snakeviz (Visual)

```bash
# Install snakeviz
pip install snakeviz

# Open visual profile viewer
snakeviz profiling_output/optimized/*_profile_*.prof

# Opens in web browser with interactive visualization
```

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

## Troubleshooting

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
- Consider native implementation (Task 13)

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

## Best Practices

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

## Integration with Development Workflow

### During Development

```bash
# Quick check after implementing optimization
./tools/measure_optimized_manual.sh 15

# Review immediate impact
# Iterate if needed
```

### Before Committing

```bash
# Full measurement before commit
./tools/measure_optimized_manual.sh 30

# Verify targets are met
# Document results
```

### Continuous Monitoring

```bash
# Periodic performance checks
./tools/measure_optimized_manual.sh 30

# Track performance over time
# Detect regressions early
```

## Report Interpretation

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

## Next Steps After Measurement

### If Targets Met (FPS ≥20%, API reduction 75-85%)

1. **Document results** (Task 14)
2. **Visual verification** (Task 12)
3. **Evaluate native implementation need** (Task 13)
4. **Create end-user documentation** (Task 15)

### If Targets Not Met

1. **Analyze profile data** for bottlenecks
2. **Review optimization implementation**
3. **Identify additional optimization opportunities**
4. **Iterate on optimizations**
5. **Re-measure and compare**

### If Performance Excellent (60+ FPS)

1. **Document success**
2. **Skip native implementation** (not needed)
3. **Focus on visual verification**
4. **Complete documentation**

## References

### Related Documentation

- **Baseline Establishment**: `doc/dev/COREGRAPHICS_PERFORMANCE_BASELINE.md`
- **Performance Testing Guide**: `doc/PERFORMANCE_TESTING_GUIDE.md`
- **Optimization Design**: `.kiro/specs/coregraphics-performance-optimization/design.md`

### Related Scripts

- **Baseline Benchmark**: `tools/manual_baseline_benchmark.sh`
- **Optimized Measurement**: `tools/measure_optimized_manual.sh`
- **Automated Measurement**: `tools/measure_optimized_performance.py`
- **Profiling Infrastructure**: `src/tfm_profiling.py`

## Conclusion

The performance measurement framework provides comprehensive tools for:
- Establishing performance baselines
- Measuring optimized performance
- Comparing before/after results
- Validating improvement targets
- Identifying remaining bottlenecks

Use these tools throughout the optimization process to:
- Track progress toward targets
- Validate optimization effectiveness
- Make data-driven decisions
- Document performance improvements
