# Performance Testing Guide

## Quick Start - Establishing Performance Baseline

This guide shows you how to measure the current performance of TFM's CoreGraphics backend before optimization.

### Prerequisites

- macOS operating system
- TFM installed with CoreGraphics backend support
- PyObjC installed (`pip install pyobjc-framework-Cocoa`)

### Running the Baseline Benchmark

#### Option 1: Manual Benchmark (Recommended)

The easiest way to establish a baseline:

```bash
# Run from the TFM project directory
./tools/manual_baseline_benchmark.sh
```

**What happens**:
1. TFM launches with profiling enabled
2. You use TFM normally for 30 seconds
3. Press 'q' to quit when done
4. Script automatically analyzes performance and shows results

**Tips for accurate measurements**:
- Navigate through directories
- Scroll through file lists
- Switch between panes
- Use TFM as you normally would
- Don't just let it sit idle

#### Option 2: Automated Benchmark

For consistent, repeatable measurements:

```bash
python3 tools/benchmark_coregraphics_performance.py --duration 30
```

This runs TFM with simulated input for exactly 30 seconds.

### Understanding the Results

After the benchmark completes, you'll see:

**FPS (Frames Per Second)**:
- 60+ FPS = Excellent (smooth)
- 30-60 FPS = Acceptable
- 20-30 FPS = Poor (needs optimization)
- <20 FPS = Critical (significant optimization needed)

**drawRect_ Performance**:
- Shows how much time is spent rendering
- Lower time per call = better performance

**API Call Counts**:
- Shows how many CoreGraphics calls per frame
- Current: ~3,000-4,000 calls per frame
- Target: ~500-900 calls per frame (75-85% reduction)

### Example Output

```
========================================================================
CoreGraphics Performance Baseline Report
========================================================================
Generated: 2024-01-15 14:30:00
Duration: 30.00 seconds

FPS Measurements:
----------------------------------------------------------------------
Average FPS: 18.50
Minimum FPS: 15.20
Maximum FPS: 22.30
Median FPS: 18.00
Total samples: 6

drawRect_ Method Performance:
----------------------------------------------------------------------
Total calls: 555
Cumulative time: 29.4000 seconds
Average time per call: 52.9730 ms
Calls per second: 18.50

CoreGraphics API Calls:
----------------------------------------------------------------------
Total API calls: 2109600
API calls per second: 70320.00

Performance Assessment:
----------------------------------------------------------------------
Overall: POOR - Below 30 FPS, optimization needed
```

### What to Do Next

1. **Document your baseline** - Save the results for comparison
2. **Identify bottlenecks** - Look at which operations are slowest
3. **Implement optimizations** - Follow the optimization spec
4. **Re-run benchmark** - Measure improvement after optimization
5. **Compare results** - Verify the optimization worked

### Viewing Detailed Profile Data

For deeper analysis:

```bash
# Interactive command-line analysis
python3 -m pstats profiling_output/baseline/loop_profile_*.prof

# Visual analysis (requires snakeviz)
pip install snakeviz
snakeviz profiling_output/baseline/loop_profile_*.prof
```

### Troubleshooting

**No profile data generated?**
- Make sure you ran TFM for at least 10 seconds
- Check that profiling_output directory exists and is writable

**FPS not showing during execution?**
- Profiling should print FPS every 5 seconds
- If not, check that TFM_PROFILING=1 is set

**TFM won't launch?**
- Verify PyObjC is installed: `python3 -c "import Cocoa"`
- Make sure you're on macOS
- Try running TFM directly: `python3 tfm.py --backend coregraphics`

### Advanced Usage

**Custom benchmark duration**:
```bash
./tools/manual_baseline_benchmark.sh 60  # 60-second benchmark
```

**Custom output directory**:
```bash
python3 tools/benchmark_coregraphics_performance.py \
  --duration 30 \
  --output-dir profiling_output/my_baseline
```

**Comparing before/after optimization**:
```bash
# Before optimization
./tools/manual_baseline_benchmark.sh 30
mv profiling_output/baseline profiling_output/before

# After optimization
./tools/manual_baseline_benchmark.sh 30
mv profiling_output/baseline profiling_output/after

# Compare results
diff profiling_output/before/baseline_report.txt \
     profiling_output/after/baseline_report.txt
```

## Performance Profiling Features

TFM includes built-in performance profiling that can be enabled anytime:

### Enabling Profiling

```bash
# Set environment variable before running TFM
export TFM_PROFILING=1
python3 tfm.py --backend coregraphics
```

### What Gets Profiled

When profiling is enabled:
- **FPS tracking** - Prints FPS every 5 seconds
- **Automatic profiling** - Triggers when FPS drops below 30 for 1+ seconds
- **Profile files** - Saved to `profiling_output/` directory
- **Low FPS detection** - Automatically captures performance issues

### Profile File Naming

Profile files are timestamped for easy identification:
```
loop_profile_20240115_143000_123456.prof
key_profile_20240115_143005_789012.prof
render_profile_20240115_143010_345678.prof
```

### Analyzing Profile Files

```bash
# List all profile files
ls -lh profiling_output/

# Analyze a specific profile
python3 -m pstats profiling_output/loop_profile_*.prof

# In pstats prompt:
sort cumulative  # Sort by cumulative time
stats 20        # Show top 20 functions
callers func    # Show what calls a function
```

## Best Practices

### For Accurate Measurements

1. **Close other applications** - Reduce system load
2. **Use consistent test scenarios** - Same navigation patterns
3. **Run multiple times** - Average results for reliability
4. **Document environment** - Note macOS version, hardware, etc.
5. **Test realistic usage** - Don't just idle or spam keys

### For Optimization Work

1. **Establish baseline first** - Always measure before optimizing
2. **Change one thing at a time** - Isolate the impact of each change
3. **Measure after each change** - Verify improvement
4. **Document results** - Keep track of what worked
5. **Compare profiles** - Use diff to see what changed

### For Reporting Issues

If you encounter performance problems:

1. **Run the baseline benchmark** - Capture current performance
2. **Save the profile data** - Include in bug reports
3. **Note your environment** - macOS version, hardware specs
4. **Describe usage pattern** - What were you doing when slow?
5. **Include FPS measurements** - From the benchmark output

## Additional Resources

- [Developer Documentation](dev/COREGRAPHICS_PERFORMANCE_BASELINE.md) - Detailed technical guide
- [Profiling System](dev/PROFILING_SYSTEM_IMPLEMENTATION.md) - How profiling works
- [Optimization Design](../.kiro/specs/coregraphics-performance-optimization/design.md) - Planned optimizations
- [Python cProfile](https://docs.python.org/3/library/profile.html) - Official documentation
