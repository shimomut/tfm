# C++ Rendering Backend Profiling Guide

This guide explains how to profile the C++ rendering backend using macOS Instruments to identify performance bottlenecks and verify cache effectiveness.

## Requirements

- macOS with Xcode Command Line Tools installed
- Instruments app (included with Xcode)
- C++ rendering backend built and installed

## Profiling Methods

### Method 1: Profile with Instruments GUI

#### Step 1: Build with Debug Symbols

Build the C++ extension with debug symbols for better profiling:

```bash
# Build with debug symbols
CFLAGS="-g -O2" python setup.py build_ext --inplace
```

#### Step 2: Run Benchmark Under Instruments

1. Open Instruments app:
   ```bash
   open -a Instruments
   ```

2. Choose a profiling template:
   - **Time Profiler**: Identify CPU hotspots
   - **Allocations**: Track memory usage and leaks
   - **Leaks**: Detect memory leaks
   - **System Trace**: Overall system performance

3. Configure the target:
   - Click "Choose Target" → "Choose Existing Process"
   - Or configure to launch Python with the benchmark script

4. Start profiling and run the benchmark:
   ```bash
   python ttk/test/benchmark_rendering.py
   ```

5. Stop profiling after the benchmark completes

#### Step 3: Analyze Results

**Time Profiler Analysis:**
- Look for hot functions in the call tree
- Check if rendering functions dominate CPU time
- Identify any unexpected bottlenecks

**Allocations Analysis:**
- Verify cache objects are reused (not recreated each frame)
- Check for memory growth over time
- Look for temporary allocations that could be avoided

**Leaks Analysis:**
- Verify no CGColorRef, CTFontRef, or CFDictionaryRef leaks
- Check that all CoreFoundation objects are properly released

### Method 2: Profile with Command Line

Use `instruments` command-line tool for automated profiling:

```bash
# Time profiling
instruments -t "Time Profiler" -D profile_time.trace python ttk/test/benchmark_rendering.py

# Memory profiling
instruments -t "Allocations" -D profile_alloc.trace python ttk/test/benchmark_rendering.py

# Leak detection
instruments -t "Leaks" -D profile_leaks.trace python ttk/test/benchmark_rendering.py
```

View results:
```bash
# Open trace file in Instruments GUI
open profile_time.trace
```

### Method 3: Use Built-in Performance Metrics

The C++ renderer includes built-in performance metrics:

```python
import cpp_renderer

# Run some rendering...

# Get metrics
metrics = cpp_renderer.get_performance_metrics()
print(f"Frames rendered: {metrics['frames_rendered']}")
print(f"Total render time: {metrics['total_render_time_ms']:.2f} ms")
print(f"Avg render time: {metrics['avg_render_time_ms']:.2f} ms")
print(f"Avg batches per frame: {metrics['avg_batches_per_frame']:.1f}")
print(f"Cache hit rate: {metrics['attr_dict_cache_hit_rate']:.1f}%")
```

## Key Performance Indicators

### Expected Performance Characteristics

1. **Rendering Time**:
   - Small grid (25x80): < 3ms per frame
   - Medium grid (40x120): < 7ms per frame
   - Large grid (50x200): < 10ms per frame

2. **Cache Hit Rate**:
   - Attribute dictionary cache: > 95% hit rate
   - Color cache: > 90% hit rate
   - Font cache: > 90% hit rate

3. **Batch Count**:
   - Should be significantly less than total cell count
   - Typical: 50-300 batches for a full screen

4. **Memory Usage**:
   - Should remain stable over time (no leaks)
   - Cache sizes should stabilize after warm-up

### Performance Bottlenecks to Look For

1. **Excessive Object Creation**:
   - CGColorRef, CTFontRef, CFDictionaryRef should be cached
   - Look for repeated creation of same objects

2. **Cache Misses**:
   - High cache miss rate indicates poor cache effectiveness
   - May need to increase cache size or improve key generation

3. **Batch Inefficiency**:
   - Too many small batches indicate poor batching
   - Should batch adjacent cells with same attributes

4. **Memory Leaks**:
   - Growing memory usage over time
   - CoreFoundation objects not being released

## Profiling Workflow

### 1. Baseline Profiling

Run initial profiling to establish baseline:

```bash
# Run benchmark and capture metrics
python ttk/test/benchmark_rendering.py > baseline_results.txt

# Profile with Instruments
instruments -t "Time Profiler" -D baseline_time.trace python ttk/test/benchmark_rendering.py
```

### 2. Identify Bottlenecks

Analyze profiling data:
- Which functions consume most CPU time?
- Are there unexpected allocations?
- Is cache hit rate acceptable?

### 3. Optimize

Make targeted optimizations based on profiling data:
- Increase cache sizes if hit rate is low
- Improve batching logic if too many batches
- Reduce allocations in hot paths

### 4. Verify Improvements

Re-run profiling after optimizations:

```bash
# Run benchmark again
python ttk/test/benchmark_rendering.py > optimized_results.txt

# Compare results
diff baseline_results.txt optimized_results.txt
```

## Common Issues and Solutions

### Issue: Low Cache Hit Rate

**Symptoms:**
- Cache hit rate < 90%
- Many cache misses in metrics

**Solutions:**
- Increase cache size (max_size parameter)
- Verify cache key generation is correct
- Check if attributes are changing unnecessarily

### Issue: Memory Leaks

**Symptoms:**
- Memory usage grows over time
- Instruments shows leaked objects

**Solutions:**
- Verify all CGColorRef calls have matching CFRelease
- Check cache clear() methods release all objects
- Use RAII patterns for automatic cleanup

### Issue: Poor Batching

**Symptoms:**
- Batch count close to cell count
- Many small batches

**Solutions:**
- Verify batching logic groups adjacent cells
- Check if attributes are preventing batching
- Review batch accumulation algorithm

### Issue: Slow Rendering

**Symptoms:**
- Render time exceeds expected values
- Low FPS

**Solutions:**
- Profile to identify hot functions
- Check for unnecessary work in render loop
- Verify dirty region optimization is working

## Profiling Checklist

Before profiling:
- [ ] Build with debug symbols
- [ ] Ensure C++ renderer is being used (not PyObjC fallback)
- [ ] Close other applications to reduce noise
- [ ] Run benchmark multiple times for consistency

During profiling:
- [ ] Use appropriate Instruments template
- [ ] Let benchmark complete fully
- [ ] Capture multiple runs for comparison

After profiling:
- [ ] Analyze call tree for hot functions
- [ ] Check memory allocations and leaks
- [ ] Verify cache effectiveness
- [ ] Document findings and optimizations

## References

- [Instruments User Guide](https://help.apple.com/instruments/mac/current/)
- [Time Profiler](https://developer.apple.com/documentation/xcode/improving-your-app-s-performance)
- [Memory Management](https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFMemoryMgmt/CFMemoryMgmt.html)
- [CoreGraphics Performance](https://developer.apple.com/library/archive/documentation/GraphicsImaging/Conceptual/drawingwithquartz2d/dq_performance/dq_performance.html)
