# Performance Profiling Feature

## Overview

TFM includes a built-in performance profiling system that helps developers investigate and optimize rendering and input handling performance. The profiling system provides real-time FPS (frames per second) measurements and detailed profiling data for key event handling and rendering operations.

This feature is particularly useful when investigating performance issues with the CoreGraphics backend or when optimizing TFM's performance on different systems.

## Quick Start

### Enable Profiling Mode

Launch TFM with the `--profile` flag to enable profiling:

```bash
python3 tfm.py --profile
```

You'll see a message confirming profiling mode is active:
```
Profiling mode enabled - performance data will be collected
```

### What You'll See

When profiling is enabled:
- **FPS measurements** are printed to stdout every 5 seconds
- **Profile files** are automatically generated for key events and rendering operations
- **Profile data** is saved to the `profiling_output/` directory

## FPS Monitoring

### Real-Time FPS Output

While TFM is running in profiling mode, you'll see FPS measurements printed every 5 seconds:

```
[2024-12-13 14:30:22] FPS: 58.3
[2024-12-13 14:30:27] FPS: 59.1
[2024-12-13 14:30:32] FPS: 60.0
```

### Understanding FPS Values

- **60 FPS**: Optimal performance (desktop mode target)
- **30-60 FPS**: Good performance
- **15-30 FPS**: Acceptable but may feel sluggish
- **< 15 FPS**: Poor performance, investigation needed

### FPS Output Format

Each FPS line includes:
- **Timestamp**: When the measurement was taken (ISO 8601 format)
- **FPS Value**: Frames per second, calculated from recent frame times

## Profile Files

### Automatic Profile Generation

TFM automatically generates profile files for:
- **Key event handling**: When you press keys
- **Rendering operations**: When the interface is drawn

### Profile File Location

All profile files are saved to the `profiling_output/` directory in your current working directory:

```
profiling_output/
├── key_profile_20241213_143022_123456.prof
├── key_profile_20241213_143025_789012.prof
├── render_profile_20241213_143022_234567.prof
├── render_profile_20241213_143025_890123.prof
└── README.txt
```

### Profile File Naming

Profile files use descriptive names with timestamps:
- **Format**: `{operation_type}_profile_{timestamp}.prof`
- **Operation types**: `key` (key handling) or `render` (rendering)
- **Timestamp**: `YYYYMMDD_HHMMSS_microseconds` for uniqueness

### README File

The `profiling_output/` directory includes a `README.txt` file with instructions on how to analyze the profile files.

## Analyzing Profile Files

### Using Python's pstats Module

The simplest way to analyze profile files is with Python's built-in `pstats` module:

```bash
# Analyze a specific profile file
python3 -m pstats profiling_output/key_profile_20241213_143022_123456.prof
```

This opens an interactive prompt where you can use commands like:

```
# Sort by cumulative time and show top 20 functions
sort cumulative
stats 20

# Show callers of a specific function
callers handle_key_input

# Show callees of a specific function
callees draw_interface

# Print statistics for functions matching a pattern
stats tfm_

# Get help on available commands
help
```

### Common pstats Commands

| Command | Description |
|---------|-------------|
| `sort cumulative` | Sort by cumulative time (time including subcalls) |
| `sort time` | Sort by internal time (time excluding subcalls) |
| `stats 20` | Show top 20 functions |
| `stats pattern` | Show functions matching pattern |
| `callers func` | Show what calls this function |
| `callees func` | Show what this function calls |
| `help` | Show all available commands |

### Using snakeviz for Visual Analysis

For a more visual analysis, install and use snakeviz:

```bash
# Install snakeviz
pip install snakeviz

# Visualize a profile file
snakeviz profiling_output/key_profile_20241213_143022_123456.prof
```

This opens a web browser with an interactive visualization showing:
- **Icicle chart**: Visual representation of function call hierarchy
- **Sunburst chart**: Alternative circular visualization
- **Function statistics**: Detailed timing information
- **Call graph**: Function call relationships

### Comparing Profiles

To compare performance before and after optimizations:

```bash
# Generate baseline profile
python3 tfm.py --profile
# Use TFM, then quit

# Make optimizations to code

# Generate new profile
python3 tfm.py --profile
# Use TFM with same operations, then quit

# Compare the profiles
python3 -m pstats profiling_output/key_profile_baseline.prof
# Note the cumulative times for key functions

python3 -m pstats profiling_output/key_profile_optimized.prof
# Compare cumulative times to see improvements
```

## Use Cases

### Investigating Slow Rendering

If TFM feels sluggish when drawing the interface:

1. **Enable profiling**: `python3 tfm.py --profile`
2. **Navigate and interact**: Perform actions that feel slow
3. **Check FPS output**: Look for FPS drops below 30
4. **Analyze render profiles**: Find which rendering functions are slow
5. **Optimize**: Focus on functions with high cumulative time

### Investigating Slow Key Response

If key presses feel delayed:

1. **Enable profiling**: `python3 tfm.py --profile`
2. **Press keys**: Perform the slow operations
3. **Analyze key profiles**: Find bottlenecks in key handling
4. **Optimize**: Focus on functions called during key handling

### Comparing Backend Performance

To compare terminal mode vs desktop mode performance:

```bash
# Profile terminal mode
python3 tfm.py --backend curses --profile
# Note FPS and profile data

# Profile desktop mode (macOS only)
python3 tfm.py --backend coregraphics --profile
# Compare FPS and profile data
```

### Testing Optimizations

When making performance improvements:

1. **Generate baseline**: Profile before changes
2. **Make changes**: Implement optimizations
3. **Generate new profile**: Profile after changes
4. **Compare**: Verify improvements in FPS and function times

## Performance Impact

### Profiling Overhead

The profiling system is designed to have minimal impact:
- **Disabled profiling**: Zero overhead (no profiling code runs)
- **Enabled profiling**: Less than 10% overhead
- **FPS tracking**: Lightweight timing with minimal impact
- **Profile generation**: File I/O doesn't block the main loop

### When to Use Profiling

Use profiling mode when:
- Investigating performance issues
- Testing optimizations
- Comparing different backends
- Benchmarking on different systems

Don't use profiling mode for:
- Normal daily usage
- Production environments
- When maximum performance is needed

## Tips and Best Practices

### Getting Accurate Measurements

1. **Warm up**: Let TFM run for a few seconds before measuring
2. **Consistent operations**: Perform the same actions when comparing
3. **Multiple runs**: Take several measurements and average
4. **Minimize background load**: Close other applications during profiling

### Interpreting Results

1. **Focus on cumulative time**: This shows total time including subcalls
2. **Look for patterns**: Repeated slow operations compound
3. **Check call counts**: Functions called many times add up
4. **Consider context**: Some operations are naturally slower

### Optimizing Based on Profiles

1. **Start with biggest impact**: Optimize functions with highest cumulative time
2. **Reduce call counts**: Avoid unnecessary function calls
3. **Cache results**: Store expensive computations
4. **Profile again**: Verify optimizations actually help

## Troubleshooting

### Profiling Mode Not Starting

**Problem**: `--profile` flag doesn't enable profiling

**Solutions**:
- Verify you're using the correct flag: `--profile` (not `--profiling`)
- Check for error messages in the output
- Ensure TFM starts successfully without the flag first

### No Profile Files Generated

**Problem**: `profiling_output/` directory is empty

**Solutions**:
- Interact with TFM (press keys, navigate) to trigger profiling
- Check file permissions in the current directory
- Look for error messages about file I/O
- Verify the directory was created

### FPS Not Printing

**Problem**: No FPS measurements appear

**Solutions**:
- Wait at least 5 seconds (FPS prints every 5 seconds)
- Check that profiling mode is enabled (look for startup message)
- Ensure stdout is not redirected or buffered
- Try interacting with TFM to generate frames

### Profile Files Too Large

**Problem**: Profile files are very large

**Solutions**:
- This is normal for complex operations
- Use `stats 20` to see only top functions
- Focus on specific patterns with `stats pattern`
- Consider profiling shorter sessions

### Can't Analyze Profile Files

**Problem**: pstats or snakeviz doesn't work

**Solutions**:
- Verify Python 3 is installed: `python3 --version`
- Install snakeviz if needed: `pip install snakeviz`
- Check profile file exists and is readable
- Try a different profile file to rule out corruption

## Advanced Usage

### Custom Profiling Sessions

For targeted profiling of specific operations:

```bash
# Start TFM with profiling
python3 tfm.py --profile

# Perform ONLY the operation you want to profile
# For example: navigate to a large directory

# Quit immediately after
# This keeps profile files focused on that operation
```

### Automated Performance Testing

For regression testing:

```bash
#!/bin/bash
# performance_test.sh

# Run TFM with profiling
python3 tfm.py --profile &
TFM_PID=$!

# Wait for startup
sleep 2

# Send test inputs (requires automation tools)
# ... send key sequences ...

# Wait for operations
sleep 5

# Kill TFM
kill $TFM_PID

# Analyze results
python3 -m pstats profiling_output/render_profile_*.prof << EOF
sort cumulative
stats 10
quit
EOF
```

### Profiling Specific Code Paths

To profile specific operations, modify the code temporarily:

```python
# In your test code
from tfm_profiling import ProfilingManager

profiler = ProfilingManager(enabled=True)

# Profile a specific function
result = profiler.profile_key_handling(my_function, arg1, arg2)

# Or profile rendering
profiler.profile_rendering(my_render_function)
```

## Related Features

- **Color Debugging**: Use `--color-test` to diagnose color performance issues
- **Remote Log Monitoring**: Use `--remote-log-port` to monitor logs during profiling
- **Desktop Mode**: Desktop mode (macOS) provides better baseline performance

## See Also

- [Performance Testing Guide](PERFORMANCE_TESTING_GUIDE.md) - Comprehensive performance testing
- [Desktop Mode Guide](DESKTOP_MODE_GUIDE.md) - High-performance desktop mode
- Developer documentation: `doc/dev/PROFILING_SYSTEM_IMPLEMENTATION.md`

---

For technical implementation details and API documentation, see the developer documentation in `doc/dev/PROFILING_SYSTEM_IMPLEMENTATION.md`.
